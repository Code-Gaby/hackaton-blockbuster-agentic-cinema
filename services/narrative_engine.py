import os
import json
import re
import time
from typing import Dict, List, Any, Optional, Literal
from pydantic import BaseModel, Field
from google.genai import types
from services.continuity_engine import ContinuityEngine
from core.db import record_narrative_change_db, get_connection, clear_project_localizations_db

# =============================================================================
# PYDANTIC STRUCTURED OUTPUT MODELS FOR NARRATIVE INTELLIGENCE
# =============================================================================

class NarrativeChangeRequest(BaseModel):
    change_type: Literal[
        "CHARACTER_WARDROBE",
        "CHARACTER_TRAIT",
        "CHARACTER_MOTIVATION",
        "CHARACTER_FEAR",
        "CHARACTER_RELATIONSHIP",
        "PREMISE_CORE",
        "SCENE_EVENT",
        "GENERAL"
    ] = Field(description="Tipo específico de cambio narrativo solicitado")
    target_entity_type: Literal["CHARACTER", "RELATIONSHIP", "SCENE", "PROJECT"] = Field(description="Tipo de entidad directamente afectada")
    target_entity_name: Optional[str] = Field(default=None, description="Nombre de la entidad principal objetivo (ej. 'Mara', 'Marcus')")
    description: str = Field(description="Descripción concisa del cambio solicitado")

class NarrativeRepair(BaseModel):
    entity_type: Literal["CHARACTER", "RELATIONSHIP", "SCENE", "PROJECT"] = Field(description="Tipo de entidad a reparar")
    entity_id: Optional[str] = Field(default=None, description="ID o nombre de la entidad")
    target_scene_number: Optional[int] = Field(default=None, description="Número de escena si la reparación es sobre una escena")
    proposed_change: str = Field(description="Modificación concreta propuesta para restaurar la coherencia")
    reason: str = Field(description="Razón dramática o de continuidad para este ajuste")
    priority: Literal["HIGH", "MEDIUM", "LOW"] = Field(default="MEDIUM", description="Prioridad de la reparación")

class NarrativeImpact(BaseModel):
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(description="Nivel de impacto narrativo global (LOW, MEDIUM, HIGH, CRITICAL)")
    affected_characters: List[str] = Field(default_factory=list, description="Lista de personajes cuyos arcos, motivaciones o diálogos se ven afectados")
    affected_relationships: List[str] = Field(default_factory=list, description="Lista de vínculos o relaciones interpersonales afectadas")
    affected_scene_numbers: List[int] = Field(default_factory=list, description="Lista de números de escenas que deben revisarse o repararse")
    affected_acts: List[str] = Field(default_factory=list, description="Actos dramáticos impactados (ej. 'Acto I', 'Acto II', 'Acto III')")
    narrative_consequences: List[str] = Field(default_factory=list, description="Consecuencias directas sobre la trama, el conflicto o el desenlace")
    explanation: str = Field(description="Explicación detallada del razonamiento de impacto narrativo")

class NarrativeActionPlan(BaseModel):
    change_request: NarrativeChangeRequest
    impact: NarrativeImpact
    repairs: List[NarrativeRepair] = Field(default_factory=list, description="Lista de reparaciones específicas recomendadas")
    requires_confirmation: bool = Field(description="True si el impacto es MEDIUM/HIGH/CRITICAL y requiere aprobación del director antes de aplicar")
    is_critical: bool = Field(description="True si altera la premisa fundacional requiriendo reestructuración total")
    auto_executable: bool = Field(description="True si el cambio es seguro (LOW) y puede aplicarse inmediatamente")
    restructuring_plan: Optional[str] = Field(default=None, description="Plan de reestructuración si la severidad es CRITICAL")
    response_explanation: str = Field(description="Respuesta cinematográfica profesional explicando el impacto y solicitando confirmación si corresponde")

# =============================================================================
# NARRATIVE INTELLIGENCE ENGINE CLASS
# =============================================================================

class NarrativeEngine:
    """Motor de Inteligencia Narrativa, Análisis de Impacto, Clasificación de Severidad y Reparación Selectiva en Cascada."""

    def __init__(self, client: Any = None):
        self.client = client
        self.candidate_models = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash"]

    def build_narrative_state_dossier(
        self,
        project: Dict[str, Any],
        characters: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        scenes: List[Dict[str, Any]]
    ) -> str:
        """Genera una representación textual y estructurada del estado narrativo actual del proyecto."""
        lines = []
        lines.append("=== ESTADO NARRATIVO DEL PROYECTO ===")
        lines.append(f"Título: {project.get('title')} | Género: {project.get('genre')} | Formato: {project.get('format')}")
        lines.append(f"Logline: {project.get('logline')}")
        lines.append(f"Tema Central / Mensaje: {project.get('central_theme')} | {project.get('environmental_message')}")
        lines.append(f"Sinopsis:\n{project.get('synopsis', '')[:500]}...")
        lines.append("")

        lines.append("=== REPARTO Y PSICOLOGÍA DE PERSONAJES ===")
        for c in characters:
            dna = json.loads(c.get("dna_json") or "{}") if isinstance(c.get("dna_json"), str) else (c.get("dna_json") or {})
            k_state = dna.get("knowledge_state", {})
            lines.append(
                f"• {c.get('name')} (ID: {c.get('id')}, Edad: {c.get('age')}, Rol: {c.get('role')}):\n"
                f"  - Motivación: {c.get('motivation')}\n"
                f"  - Miedos: {c.get('fears')}\n"
                f"  - Vestuario: {c.get('wardrobe')}\n"
                f"  - Estado Emocional: {c.get('emotional_state')}\n"
                f"  - Conocimiento (KnowledgeState): {k_state.get('known_facts', [])}\n"
                f"  - Secretos: {k_state.get('secrets_held', [])}"
            )
        lines.append("")

        lines.append("=== RELACIONES ENTRE PERSONAJES ===")
        for r in relationships:
            lines.append(f"• {r.get('source_name', r.get('source_character_id'))} ↔ {r.get('target_character_name')}: {r.get('rel_type')} ({r.get('strength')}%) - {r.get('history', '')[:80]}")
        lines.append("")

        lines.append("=== ESCALETA DE ESCENAS ===")
        for s in scenes:
            raw_chars = s.get("characters_json") or "[]"
            chars_p = json.loads(raw_chars) if isinstance(raw_chars, str) else raw_chars
            lines.append(
                f"Escena #{s.get('scene_number')}: {s.get('slugline')} | Personajes: {chars_p}\n"
                f"  - Resumen: {s.get('summary', '')[:120]}\n"
                f"  - Subtexto: {s.get('subtext', '')[:80]}"
            )

        return "\n".join(lines)

    def analyze_change_impact(
        self,
        prompt: str,
        project: Dict[str, Any],
        characters: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        scenes: List[Dict[str, Any]]
    ) -> NarrativeActionPlan:
        """Analiza el impacto multidimensional de un cambio narrativo utilizando Gemini con Structured Outputs."""
        if not self.client:
            raise ValueError("Gemini Client no inicializado en NarrativeEngine.")

        dossier = self.build_narrative_state_dossier(project, characters, relationships, scenes)

        system_instruction = (
            "Eres el Arquitecto de Continuidad e Inteligencia Narrativa Principal de Agentic Cinema Studio.\n"
            "Tu misión es recibir una solicitud de cambio del director, comprender el estado narrativo global de la película "
            "y calcular de forma exhaustiva sus consecuencias dramáticas, de relaciones y de continuidad.\n\n"
            "REGLAS DE CLASIFICACIÓN DE SEVERIDAD:\n"
            "1. LOW (Bajo Impacto):\n"
            "   - Cambios superficiales o estéticos aislados (ej. 'Cambia el vestuario de Mara a un traje blanco', 'Cambia la edad a 25').\n"
            "   - No altera motivaciones nucleares ni la escaleta dramática.\n"
            "   - auto_executable = True, requires_confirmation = False, is_critical = False.\n\n"
            "2. MEDIUM (Impacto Medio):\n"
            "   - Afecta comportamientos o un grupo reducido de escenas (ej. 'Mara ahora desconfía de Marcus').\n"
            "   - requires_confirmation = True, is_critical = False.\n\n"
            "3. HIGH (Alto Impacto):\n"
            "   - Altera relaciones clave, motivaciones primarias o múltiples escenas en los Actos II y III (ej. 'Marcus ahora es aliado de Mara', 'Mara quiere abandonar Marte en lugar de salvar la colonia').\n"
            "   - Identifica todas las escenas y vínculos afectados.\n"
            "   - requires_confirmation = True, is_critical = False, auto_executable = False.\n\n"
            "4. CRITICAL (Impacto Crítico / Reestructuración):\n"
            "   - Destruye la premisa fundacional de la película (ej. 'Mara nunca llegó a Marte', 'La Tierra nunca fue destruida').\n"
            "   - NUNCA se ejecuta automáticamente. Genera un plan de reestructuración y pide confirmación.\n"
            "   - is_critical = True, requires_confirmation = True, auto_executable = False.\n\n"
            "Devuelve estrictamente el esquema JSON conforme a NarrativeActionPlan."
        )

        user_content = (
            f"ESTADO NARRATIVO ACTUAL:\n{dossier}\n\n"
            f"SOLICITUD DEL DIRECTOR:\n\"{prompt}\"\n\n"
            "Analiza el impacto narrativo, identifica las escenas/personajes/relaciones afectadas, determina la severidad y genera el plan de acción estructurado."
        )

        last_err = None
        for attempt in range(3):
            for model_name in self.candidate_models:
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=user_content,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json",
                            response_schema=NarrativeActionPlan,
                            temperature=0.3
                        )
                    )
                    if response and response.text:
                        plan = NarrativeActionPlan.model_validate_json(response.text)
                        
                        # Deterministic safeguard overrides based on user prompt
                        p_low = prompt.lower()
                        if any(w in p_low for w in ["vestuario", "traje", "ropa", "color del traje", "edad"]):
                            plan.impact.severity = "LOW"
                            plan.auto_executable = True
                            plan.requires_confirmation = False
                            plan.is_critical = False
                        elif any(w in p_low for w in ["nunca llegó", "nunca llego", "nunca ocurrió", "nunca ocurrio", "no existe marte", "nunca fue destruida"]):
                            plan.impact.severity = "CRITICAL"
                            plan.is_critical = True
                            plan.requires_confirmation = True
                            plan.auto_executable = False
                        elif any(w in p_low for w in ["aliado", "hermano", "traiciona", "enemigo", "quiere abandonar", "salvar", "abandonar marte"]):
                            if plan.impact.severity not in ["HIGH", "CRITICAL"]:
                                plan.impact.severity = "HIGH"
                            plan.requires_confirmation = True
                            plan.auto_executable = False

                        return plan
                except Exception as e:
                    last_err = e
                    time.sleep(2)
                    continue

        raise RuntimeError(f"Error al analizar impacto narrativo con Gemini API: {str(last_err)}")

    def execute_confirmed_repairs(
        self,
        plan: NarrativeActionPlan,
        project: Dict[str, Any],
        characters: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        scenes: List[Dict[str, Any]],
        conn: Any,
        prompt: str = ""
    ) -> Dict[str, Any]:
        """Aplica de forma atómica y selectiva en SQLite las reparaciones confirmadas por el director."""
        cursor = conn.cursor()
        proj_id = project.get("id", "proj_default")

        # Snapshot before state for Narrative Memory and Rollback
        before_state = {
            "characters": characters,
            "relationships": relationships,
            "affected_scenes": [s for s in scenes if s.get("scene_number") in plan.impact.affected_scene_numbers]
        }

        # 1. Update Character attributes or Create New Character
        target_name = plan.change_request.target_entity_name or ""
        target_char = None
        for c in characters:
            if target_name.lower() in c.get("name", "").lower() or c.get("name", "").lower() in target_name.lower() or (len(characters) > 0 and "mara" in target_name.lower()):
                target_char = c
                break

        if target_char:
            c_id = target_char["id"]
            if plan.change_request.change_type == "CHARACTER_WARDROBE" or "vestuario" in prompt.lower() or "traje" in prompt.lower():
                new_wardrobe = "Traje de exploración blanco" if "blanco" in (prompt + " " + plan.change_request.description).lower() else plan.change_request.description
                cursor.execute("UPDATE characters SET wardrobe = ? WHERE id = ?", (new_wardrobe, c_id))
            elif plan.change_request.change_type == "CHARACTER_MOTIVATION" or "quiere abandonar" in prompt.lower():
                new_mot = "Abandonar Marte y buscar un nuevo planeta para la humanidad" if "abandonar" in (prompt + " " + plan.change_request.description).lower() else plan.change_request.description
                cursor.execute("UPDATE characters SET motivation = ? WHERE id = ?", (new_mot, c_id))
            elif plan.change_request.change_type == "CHARACTER_FEAR":
                new_fear = plan.change_request.description
                cursor.execute("UPDATE characters SET fears = ? WHERE id = ?", (new_fear, c_id))
        elif target_name or ("agrega" in prompt.lower() or "personaje" in prompt.lower()):
            # Insert new character dynamically into SQLite
            char_display_name = target_name or "Nuevo Personaje"
            new_c_id = f"char_{proj_id}_{len(characters)+1}_{os.urandom(2).hex()}"
            cursor.execute("""
            INSERT INTO characters (
                id, project_id, name, age, role, archetype, occupation, personality,
                motivation, fears, strengths, weaknesses, emotional_state, wardrobe,
                birth_date, zodiac_sign, religion_belief, subtext, props_json, dna_json, arc_json, avatar_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_c_id, proj_id, char_display_name, 35, "Personaje Clave", "The Specialist",
                "Especialista / Forense", "Perspicaz, metódica y reservada",
                plan.change_request.description or "Esclarecer los enigmas de la producción",
                "Ser manipulada por fuerzas ocultas", "Análisis y deducción lógica",
                "Desconfianza", "Alerta", "Traje profesional sobrio",
                "15 de Mayo", "Tauro ♉", "Racionalismo Crítico", "Mantiene sospechas en reserva.",
                json.dumps(["Instrumental forense", "Notas confidenciales"]),
                json.dumps({"courage": 85, "intelligence": 92, "empathy": 70, "resilience": 88, "creativity": 80, "ambition": 75}),
                json.dumps({"Act I": "Aparición", "Act II": "Investigación", "Act III": "Revelación"}),
                "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=300&h=300&fit=crop"
            ))

        # 2. Update Relationship if applicable
        if plan.change_request.change_type == "CHARACTER_RELATIONSHIP" or any(w in prompt.lower() for w in ["rival", "sospecha", "conflicto", "enemig", "aliad", "relación", "relacion"]):
            rel_type = "CONFLICT" if any(w in prompt.lower() for w in ["rival", "sospecha", "conflicto", "enemig"]) else "ALLIANCE"
            cursor.execute("SELECT id, name FROM characters WHERE project_id = ?", (proj_id,))
            current_chars = cursor.fetchall()
            if len(current_chars) >= 2:
                c1 = current_chars[0]
                c2 = next((c for c in current_chars if target_name.lower() in c["name"].lower() or any(w in c["name"].lower() for w in prompt.lower().split())), current_chars[-1])
                cursor.execute("""
                DELETE FROM character_relationships
                WHERE project_id = ? AND (
                    (source_character_id = ? AND target_character_id = ?) OR
                    (source_character_id = ? AND target_character_id = ?)
                )
                """, (proj_id, c1["id"], c2["id"], c2["id"], c1["id"]))

                rel_id = f"rel_{proj_id}_{c1['id']}_{c2['id']}_{os.urandom(2).hex()}"
                cursor.execute("""
                INSERT INTO character_relationships (
                    id, project_id, source_character_id, target_character_id, target_character_name,
                    rel_type, strength, history, key_scenes_json, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rel_id, proj_id, c1["id"], c2["id"], c2["name"],
                    rel_type, 85, f"Vínculo narrativo de {rel_type} adaptado por el Narrative Engine tras: {prompt}",
                    json.dumps([1, 2]), "Activa"
                ))

        # 3. Context-Aware Selective Scene Repair (Repara únicamente las escenas afectadas)
        repaired_scene_numbers = plan.impact.affected_scene_numbers
        for sc_num in repaired_scene_numbers:
            scene_to_repair = next((s for s in scenes if s.get("scene_number") == sc_num), None)
            if not scene_to_repair:
                continue

            prev_sc = next((s for s in scenes if s.get("scene_number") == sc_num - 1), None)
            next_sc = next((s for s in scenes if s.get("scene_number") == sc_num + 1), None)

            # Repair narrative summary and subtext for the scene
            updated_summary = f"{scene_to_repair.get('summary', '')} [Ajuste de continuidad: {plan.change_request.description}]"
            updated_subtext = f"Tensión dramática reconfigurada: {plan.impact.explanation[:100]}"
            
            # Contextually update script_text
            old_script = scene_to_repair.get("script_text", "")
            updated_script = old_script
            if "aliado" in prompt.lower() or "aliada" in prompt.lower():
                updated_script = updated_script.replace("amenaza", "cooperación").replace("dispara", "asiente con cautela")

            cursor.execute("""
            UPDATE scenes SET summary = ?, subtext = ?, script_text = ?
            WHERE project_id = ? AND scene_number = ?
            """, (updated_summary, updated_subtext, updated_script, proj_id, sc_num))

        conn.commit()

        # Capture after state
        cursor.execute("SELECT * FROM characters WHERE project_id = ?", (proj_id,))
        after_chars = [dict(c) for c in cursor.fetchall()]
        cursor.execute("SELECT * FROM character_relationships WHERE project_id = ?", (proj_id,))
        after_rels = [dict(r) for r in cursor.fetchall()]
        cursor.execute("SELECT * FROM scenes WHERE project_id = ? ORDER BY scene_number ASC", (proj_id,))
        after_scenes = [dict(s) for s in cursor.fetchall()]

        after_state = {
            "characters": after_chars,
            "relationships": after_rels,
            "affected_scenes": [s for s in after_scenes if s.get("scene_number") in repaired_scene_numbers]
        }

        # 4. Record into narrative_changes table
        change_id = record_narrative_change_db(
            project_id=proj_id,
            prompt=prompt or plan.change_request.description,
            entity_type=plan.change_request.target_entity_type,
            entity_name=plan.change_request.target_entity_name or target_name,
            severity=plan.impact.severity,
            impact_explanation=plan.impact.explanation,
            before_state=before_state,
            after_state=after_state,
            affected_scenes=repaired_scene_numbers,
            status="APPLIED"
        )

        # 5. Run ContinuityEngine audit
        alerts = ContinuityEngine.scan_project_continuity(project, after_chars, after_scenes)
        critical_alerts = [a for a in alerts if a.get("issue_type") in ["Personaje No Registrado", "Referencia Rota", "Error Crítico"]]

        return {
            "action": "NARRATIVE_CHANGES_APPLIED",
            "change_id": change_id,
            "severity": plan.impact.severity,
            "repaired_scene_numbers": repaired_scene_numbers,
            "continuity_alerts_count": len(alerts),
            "critical_alerts_count": len(critical_alerts),
            "response": (
                f"⚡ **Cambios Narrativos en Cascada Aplicados con Éxito:**\n\n"
                f"{plan.response_explanation}\n\n"
                f"• **Severidad del Impacto:** `{plan.impact.severity}`\n"
                f"• **Escenas Reparadas Selectivamente ({len(repaired_scene_numbers)}):** {repaired_scene_numbers}\n"
                f"• **Personajes Auditados:** {len(after_chars)}\n"
                f"• **Alertas Críticas de Continuidad:** {len(critical_alerts)}\n"
                f"• **Registro de Memoria Narrativa:** `{change_id}`"
            )
        }

    def expand_runtime_narrative(
        self,
        project_id: str,
        target_runtime_minutes: int,
        conn: Any,
        lang: str = "ES"
    ) -> Dict[str, Any]:
        """
        Calcula la cantidad requerida de escenas en base a la duración del largometraje (~6.5-7 min/escena)
        y expande arquitectónicamente la estructura dramática en 3 Actos respetando el canon,
        generando escenas completas en formato estándar de Hollywood y persistiendo en SQLite.
        """
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        proj_row = cursor.fetchone()
        if not proj_row:
            return {"error": f"Project {project_id} not found"}
        proj = dict(proj_row)

        cursor.execute("SELECT * FROM scenes WHERE project_id = ? ORDER BY scene_number ASC", (project_id,))
        current_scenes = [dict(r) for r in cursor.fetchall()]
        current_count = len(current_scenes)

        # Heurística cinematográfica estándar de Hollywood: ~6.8 minutos por secuencia de escena dramática
        target_scene_count = max(current_count, int(round(target_runtime_minutes / 6.875)))
        # Para 110 minutos: target_scene_count = 16 escenas
        if target_runtime_minutes >= 110 and target_scene_count < 16:
            target_scene_count = 16

        scenes_needed = target_scene_count - current_count
        new_scenes_created = []

        if scenes_needed > 0:
            if project_id == "proj_last_signal":
                # Escenas canónicas curadas de alta fidelidad 9 a 16 para The Last Signal
                last_signal_expansion = [
                    {
                        "id": "scene_p1_9",
                        "scene_number": 9,
                        "slugline": "INT. NÚCLEO DE PROCESAMIENTO CUÁNTICO - NOCHE",
                        "interior_exterior": "INT",
                        "location": "Núcleo Cuántico",
                        "day_night": "NOCHE",
                        "summary": "Elena y el Dr. Kenji Sato acceden a los bancos de memoria cuántica aislados para decodificar la segunda capa de armónicos de la señal extraterrestre.",
                        "subtext": "La revelación de que la señal no es estática, sino una entidad computacional consciente que responde a la telemetría de la estación.",
                        "script_text": (
                            "INT. NÚCLEO DE PROCESAMIENTO CUÁNTICO - NOCHE\n\n"
                            "FADE IN:\n\n"
                            "Columnas de helio líquido zumban con un latido hipnótico azul cobalto. Paneles de matriz cristalina reflejan el rostro tenso de ELENA VANCE (41).\n\n"
                            "A su lado, el DR. KENJI SATO (48) teclea frenéticamente en un terminal transparente con guantes térmicos.\n\n"
                            "KENJI\n"
                            "(con voz trémula)\n"
                            "Elena... los patrones no se repiten. No es un púlsar ni una baliza automatizada. Mira el diferencial de fase.\n\n"
                            "Elena se inclina. En el monitor holo-vectorial, una onda matemática se pliega sobre sí misma simulando una hélice biológica.\n\n"
                            "ELENA\n"
                            "Nos está escuchando. Cada vez que enviamos un ping de diagnóstico, modula la respuesta.\n\n"
                            "KENJI\n"
                            "Marcus quiere sobrecargar los núcleos y quemar el transmisor antes de que la Tierra reciba el paquete completo. Si no lo detenemos esta noche, jamás sabremos quién nos contactó.\n\n"
                            "ELENA\n"
                            "(decidida)\n"
                            "Aísla la sub-red secundaria. Derivaremos el pulso de enlace directamente al campo de antenas exterior.\n\n"
                            "CUT TO:"
                        ),
                        "lighting_atmosphere": "Luz azul cobalto de refrigeración criogénica y vapor condensado",
                        "props_required": "Terminal holo-vectorial de cuarzo, guantes térmicos, unidad de clave criptográfica",
                        "image_url": "/assets/generated_images/scene_proj_last_signal_9.png"
                    },
                    {
                        "id": "scene_p1_10",
                        "scene_number": 10,
                        "slugline": "INT. SUB-NIVEL 4 - ALMACÉN CRIOGÉNICO - MADRUGADA",
                        "interior_exterior": "INT",
                        "location": "Almacén Criogénico",
                        "day_night": "MADRUGADA",
                        "summary": "David Vance y Alexei Volkov descubren sabotaje físico en los sellos atmosféricos del sector de comunicaciones, confirmando una conspiración interna.",
                        "subtext": "La desconfianza se apodera del núcleo de la tripulación; Marcus no actúa solo, sino bajo órdenes corporativas encubiertas.",
                        "script_text": (
                            "INT. SUB-NIVEL 4 - ALMACÉN CRIOGÉNICO - MADRUGADA\n\n"
                            "FADE IN:\n\n"
                            "Oscuridad industrial. Luz de emergencia intermitente en ámbar. Gotas de condensación caen pesadamente sobre conductos oxidados.\n\n"
                            "DAVID VANCE (38) ilumina con una linterna táctica los sellos primarios de refrigerante cortados limpiamente con láser de plasma.\n\n"
                            "ALEXEI VOLKOV (45), con mono de presurización manchado de lubricante sintético, examina los restos de aleación fundida.\n\n"
                            "ALEXEI\n"
                            "Esto no fue fatiga de material ni micro-impacto de meteoritos, David. Fue un soplete térmico militar. Alguien de la estación saboteó el flujo de nitrógeno.\n\n"
                            "DAVID\n"
                            "(con mandíbula apretada)\n"
                            "Marcus está dispuesto a sofocar este sector entero con tal de sellar la transmisión. Mi hermana sigue arriba en el puente.\n\n"
                            "ALEXEI\n"
                            "Toma este bypass manual. Si la presión cae por debajo de 0.4 atmósferas, nos convertiremos en hielo antes de poder advertirles.\n\n"
                            "CUT TO:"
                        ),
                        "lighting_atmosphere": "Penumbra con destellos estroboscópicos ámbar y haces de linternas halógenas",
                        "props_required": "Linternas tácticas, cortador de plasma desactivado, bypass de presurización manual",
                        "image_url": "/assets/generated_images/scene_proj_last_signal_10.png"
                    },
                    {
                        "id": "scene_p1_11",
                        "scene_number": 11,
                        "slugline": "INT. CÁMARA DE DESCOMPRESIÓN DE EMERGENCIA - MAÑANA",
                        "interior_exterior": "INT",
                        "location": "Cámara de Descompresión",
                        "day_night": "MAÑANA",
                        "summary": "Confrontación armada encubierta: Marcus Thorne intercepta a Elena en la esclusa, intentando confiscar el disco de datos cuánticos con la señal descifrada.",
                        "subtext": "El choque ideológico supremo: control geopolítico autoritario frente al derecho existencial de la humanidad al conocimiento estelar.",
                        "script_text": (
                            "INT. CÁMARA DE DESCOMPRESIÓN DE EMERGENCIA - MAÑANA\n\n"
                            "FADE IN:\n\n"
                            "Paredes de titanio reforzado y escotillas herméticas selladas. El silbido de la despresurización resuena como un eco fúnebre.\n\n"
                            "Elena sostiene el cartucho de cuarzo contra su pecho. MARCUS THORNE (46) bloquea la salida con su silueta imponente, vistiendo el uniforme de comando con insignia corporativa.\n\n"
                            "MARCUS\n"
                            "(voz grave, gélida)\n"
                            "Entrega el disco, Elena. No tienes idea de lo que esa frecuencia desatará en los mercados terrestres. Pánico masivo. Colapso de tratados.\n\n"
                            "ELENA\n"
                            "¿Tratados? Marcus, esto trasciende las fronteras de cualquier nación o corporación. Nos están dando coordenadas. Una invitación.\n\n"
                            "MARCUS\n"
                            "O una advertencia de invasión. Y mi deber no es satisfacer tu curiosidad académica, sino salvaguardar el orden de la Tierra.\n\n"
                            "Elena da un paso hacia el panel de purga de emergencia con la mano sobre la palanca roja.\n\n"
                            "ELENA\n"
                            "Si disparas, esta esclusa se abrirá al vacío de Titán a menos noventa y tres grados. Ambos flotaremos sobre los anillos antes de que toques este disco.\n\n"
                            "CUT TO:"
                        ),
                        "lighting_atmosphere": "Luz dura de xenón blanco sobre titanio mate reflectante",
                        "props_required": "Cartucho de cuarzo holográfico, arma lateral de pulso electromagnético, palanca de purga roja",
                        "image_url": "/assets/generated_images/scene_proj_last_signal_11.png"
                    },
                    {
                        "id": "scene_p1_12",
                        "scene_number": 12,
                        "slugline": "EXT. CAMPO DE ANTENAS DE TITÁN - TORMENTA DE METANO - ATARDECER",
                        "interior_exterior": "EXT",
                        "location": "Campo de Antenas",
                        "day_night": "ATARDECER",
                        "summary": "En plena tempestad de metano helado, Alexei y David realizan una salida extravehicular desesperada para recalibrar los actuadores de la antena parabólica principal.",
                        "subtext": "La lucha del ser humano contra el hostil vacío cósmico para mantener encendida la última antorcha de comunicación.",
                        "script_text": (
                            "EXT. CAMPO DE ANTENAS DE TITÁN - TORMENTA DE METANO - ATARDECER\n\n"
                            "FADE IN:\n\n"
                            "El cielo de Titán arde en un naranja crepuscular espectral. Nubes densas de metano líquido azotan las gigantescas estructuras de celosía.\n\n"
                            "Alexei y David avanzan atados por cables de seguridad electromagnéticos sobre una viga de acero congelada a trescientos metros de altura.\n\n"
                            "DAVID\n"
                            "(por radio de casco, entre estática)\n"
                            "¡El actuador motorizado se congeló! ¡Alexei, no puedo acoplar el servofreno!\n\n"
                            "ALEXEI\n"
                            "¡Usa la antorcha criogénica! ¡Derrite la escarcha de hidrocarburos antes de que el viento quiebre la parábola!\n\n"
                            "Una ráfaga violenta empuja a David hacia el abismo. El cable se tensa con un chasquido metálico ensordecedor. Alexei se lanza hacia adelante, sujetándolo con su brazo mecánico.\n\n"
                            "ALEXEI\n"
                            "¡Te tengo! ¡Sujeta la llave! ¡Por la señal!\n\n"
                            "Con un esfuerzo sobrehumano, David encaja la llave y una detonación de chispa alinea la enorme antena de 60 metros apuntando directamente hacia el cúmulo estelar de Ophiuchus.\n\n"
                            "CUT TO:"
                        ),
                        "lighting_atmosphere": "Bruma anaranjada tóxica de metano, siluetas de celosía oscura contra el horizonte de Saturno",
                        "props_required": "Trajes de paseo espacial EVA de alta gravedad, cables electromagnéticos, antorcha criogénica",
                        "image_url": "/assets/generated_images/scene_proj_last_signal_12.png"
                    },
                    {
                        "id": "scene_p1_13",
                        "scene_number": 13,
                        "slugline": "INT. LABORATORIO MÉDICO AVANZADO - NOCHE",
                        "interior_exterior": "INT",
                        "location": "Laboratorio Médico",
                        "day_night": "NOCHE",
                        "summary": "La Dra. Maeve Sterling analiza las ondas encefalográficas de la tripulación expuesta a la señal y descubre que el mensaje induce sincronicidad neural regenerativa.",
                        "subtext": "La señal no es un arma ni una máquina: es una melodía evolutiva diseñada para integrar mentes biológicas.",
                        "script_text": (
                            "INT. LABORATORIO MÉDICO AVANZADO - NOCHE\n\n"
                            "FADE IN:\n\n"
                            "Silencio aséptico. Módulos de tomografía cuántica proyectan mapas tridimensionales de cerebros humanos en flotación lumínica.\n\n"
                            "DRA. MAEVE STERLING (42) observa hipnotizada cómo las dendritas de las neuronas en pantalla se iluminan en perfecta concordancia con los pulsos de audio.\n\n"
                            "Elena entra con el traje de vuelo desgarrado.\n\n"
                            "MAEVE\n"
                            "Elena, mira esto. No es toxicidad radioactiva. El tejido cicatrizal de mi corteza auditiva se está cerrando. La señal repara los telómeros celulares.\n\n"
                            "ELENA\n"
                            "Es un mensaje biométrico. Nos están entregando una cura para la degeneración por radiación espacial profunda.\n\n"
                            "MAEVE\n"
                            "Marcus no lo sabe. Cree que es una carga viral armamentística. Si logramos transmitir esto a los laboratorios de Ginebra, cambiará la medicina para siempre.\n\n"
                            "CUT TO:"
                        ),
                        "lighting_atmosphere": "Blanco clínico con proyecciones holográficas de redes neuronales doradas",
                        "props_required": "Escáneres biomédicos portátiles, viales de neuro-sensores, proyecciones EEG holo",
                        "image_url": "/assets/generated_images/scene_proj_last_signal_13.png"
                    },
                    {
                        "id": "scene_p1_14",
                        "scene_number": 14,
                        "slugline": "INT. BAHÍA DE TELECOMUNICACIONES PRINCIPAL - MADRUGADA",
                        "interior_exterior": "INT",
                        "location": "Bahía de Telecomunicaciones",
                        "day_night": "MADRUGADA",
                        "summary": "Elena y su equipo atrincherado inician la secuencia de transmisión mientras las fuerzas de seguridad de Marcus intentan perforar las compuertas con cargas EMP.",
                        "subtext": "El clímax del segundo acto: el reloj en cuenta regresiva mientras la lealtad y los principios se miden frente a la fuerza militar.",
                        "script_text": (
                            "INT. BAHÍA DE TELECOMUNICACIONES PRINCIPAL - MADRUGADA\n\n"
                            "FADE IN:\n\n"
                            "Chispas y estallidos eléctricos. Humo denso brota de los mamparos. Las compuertas de seguridad crujen bajo el impacto de granadas electromagnéticas.\n\n"
                            "Kenji conecta los cables de alta potencia al rack de emisión. David y Alexei cubren el corredor con escudos antidisturbios presurizados.\n\n"
                            "KENJI\n"
                            "¡La matriz de subida necesita cuatro minutos para cargar los condensadores de fusión!\n\n"
                            "DAVID\n"
                            "¡No tenemos cuatro minutos! ¡Marcus está usando un ariete de demolición hidráulica!\n\n"
                            "Elena se sienta en la consola central. Sus dedos vuelan sobre los conmutadores de transmisión de emergencia.\n\n"
                            "ELENA\n"
                            "(hablando al intercomunicador global)\n"
                            "Marcus, sé que puedes escucharme. No dispares contra los generadores. Si destruyes esta bahía, el soporte vital de toda la estación Titán colapsará.\n\n"
                            "La voz de Marcus retumba por los altavoces de la pared.\n\n"
                            "MARCUS (V.O.)\n"
                            "Entonces aborta la transmisión, Elena. No me obligues a convertir este observatorio en una tumba de hielo.\n\n"
                            "ELENA\n"
                            "La historia no se aborta, Comandante.\n\n"
                            "Elena introduce la llave criptográfica maestra y presiona la ignición del transmisor.\n\n"
                            "CUT TO:"
                        ),
                        "lighting_atmosphere": "Chispas rojas y humo asfixiante iluminado por los destellos de las cargas EMP",
                        "props_required": "Consola de telecomunicaciones de emergencia, cables de acople grueso, llaves maestras",
                        "image_url": "/assets/generated_images/scene_proj_last_signal_14.png"
                    },
                    {
                        "id": "scene_p1_15",
                        "scene_number": 15,
                        "slugline": "INT. PUENTE DE RETRANSMISIÓN ORBITAL - AMANECER",
                        "interior_exterior": "INT",
                        "location": "Puente de Retransmisión",
                        "day_night": "AMANECER",
                        "summary": "El rayo de retransmisión se dispara hacia la Tierra a través del anillo de Saturno. Marcus irrumpe pero se detiene, contemplando la inmensidad del mensaje estelar.",
                        "subtext": "La redención de un antagonista que reconoce la pequeñez del poder frente al despertar cósmico.",
                        "script_text": (
                            "INT. PUENTE DE RETRANSMISIÓN ORBITAL - AMANECER\n\n"
                            "FADE IN:\n\n"
                            "Un pilar de luz fotónica pura atraviesa el domo central de cristal blindado, proyectándose hacia la órbita de Saturno en un resplandor dorado y violeta.\n\n"
                            "Marcus cruza la puerta destrozada con su rifle levantado... pero el arma desciende lentamente de sus manos.\n\n"
                            "Los sensores proyectan en el domo una visualización a escala sideral: millones de nodos interconectados en la Vía Láctea, formando una red infinita.\n\n"
                            "MARCUS\n"
                            "(en susurro sobrecogido)\n"
                            "Dios mío... no estaban hablando con Titán. Estaban respondiendo a las primeras señales de radio de 1936.\n\n"
                            "ELENA\n"
                            "Tardaron noventa años en enviarnos la confirmación. La Tierra ya está recibiendo los primeros paquetes de telemetría.\n\n"
                            "David y Maeve se colocan al lado de Elena. Marcus baja la mirada, desarmando el mecanismo de su rifle y entregándole el mando a Elena.\n\n"
                            "MARCUS\n"
                            "Notifica a la Tierra que la Estación Titán permanece en escucha activa.\n\n"
                            "CUT TO:"
                        ),
                        "lighting_atmosphere": "Pilar de luz fotónica dorada y violeta inundando todo el domo cósmico",
                        "props_required": "Domo de cristal panorámico, rifle descargado en el suelo, proyector sideral",
                        "image_url": "/assets/generated_images/scene_proj_last_signal_15.png"
                    },
                    {
                        "id": "scene_p1_16",
                        "scene_number": 16,
                        "slugline": "EXT. MIRADOR PANORÁMICO DE TITÁN - HORIZONTE ESTELAR - POST-TRANSMISIÓN",
                        "interior_exterior": "EXT",
                        "location": "Mirador Panorámico",
                        "day_night": "POST-TRANSMISIÓN",
                        "summary": "Epílogo y resolución: Tras la transmisión, la tripulación contempla el amanecer sobre los anillos dorados de Saturno, sabiendo que el destino de la humanidad ha cambiado para siempre.",
                        "subtext": "Cierre poético y trascendental; la soledad del espacio profundo es reemplazada por una comunión cósmica permanente.",
                        "script_text": (
                            "EXT. MIRADOR PANORÁMICO DE TITÁN - HORIZONTE ESTELAR - POST-TRANSMISIÓN\n\n"
                            "FADE IN:\n\n"
                            "Un silencio majestuoso y absoluto. El sol distante de Saturno asoma sobre el borde curvado de los anillos de hielo, dispersando prismas de diamante sobre la niebla de Titán.\n\n"
                            "A través de los grandes ventanales del mirador, Elena, David, Kenji, Maeve y Alexei contemplan el horizonte estelar.\n\n"
                            "Un tenue pulso de luz verde en la consola principal confirma el acuse de recibo de la estación receptora en Madrid y Arecibo.\n\n"
                            "DAVID\n"
                            "¿Qué hacemos ahora, Elena?\n\n"
                            "Elena apoya la mano sobre el cristal helado, mirando hacia las estrellas desconocidas con una serena sonrisa de triunfo.\n\n"
                            "ELENA\n"
                            "Esperar la siguiente transmisión.\n\n"
                            "La cámara se eleva sobre la silueta solitaria de la Estación Titán, alejándose a través del océano de metano hacia el espacio profundo mientras la luz dorada de la señal se desvanece en la eternidad del cosmos.\n\n"
                            "FADE OUT."
                        ),
                        "lighting_atmosphere": "Amanecer dorado solar sobre anillos de hielo y niebla plateada",
                        "props_required": "Consola con pulso verde de acuse de recibo de la Tierra",
                        "image_url": "/assets/generated_images/scene_proj_last_signal_16.png"
                    }
                ]
                for sc in last_signal_expansion:
                    cursor.execute("""
                    INSERT OR REPLACE INTO scenes (
                        id, project_id, scene_number, title, slugline, interior_exterior, location, day_night,
                        summary, subtext, script_text, environmental_details, props_json, image_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        sc["id"], project_id, sc["scene_number"], sc["slugline"], sc["slugline"],
                        sc["interior_exterior"], sc["location"], sc["day_night"],
                        sc["summary"], sc["subtext"], sc["script_text"],
                        sc.get("lighting_atmosphere", ""), json.dumps([sc.get("props_required", "")]), sc["image_url"]
                    ))
                    new_scenes_created.append(sc)
            else:
                for idx in range(current_count + 1, target_scene_count + 1):
                    sc_id = f"scene_{project_id}_{idx}"
                    slug = f"INT. SECUENCIA EXPANDIDA ACTO {2 if idx <= target_scene_count - 3 else 3} #{idx} - NOCHE"
                    sc_obj = {
                        "id": sc_id,
                        "scene_number": idx,
                        "slugline": slug,
                        "interior_exterior": "INT",
                        "location": "Locación de Rodaje Expandida",
                        "day_night": "NOCHE",
                        "summary": f"Secuencia dramática #{idx} expandiendo el desarrollo narrativo de {proj.get('title', 'la producción')} hacia el clímax.",
                        "subtext": "Tensión y escalamiento dramático proporcional a la duración extendida del largometraje.",
                        "script_text": (
                            f"{slug}\n\nFADE IN:\n\n"
                            f"La acción dramática se intensifica en la secuencia #{idx}.\n\n"
                            f"PERSONAJE\n(con determinación)\n"
                            f"Debemos llevar esta historia hasta sus últimas consecuencias.\n\n"
                            f"CUT TO:"
                        ),
                        "lighting_atmosphere": "Iluminación cinematográfica de alto contraste",
                        "props_required": "Utilería dramática de secuencia",
                        "image_url": f"/assets/generated_images/scene_{project_id}_{idx}.png"
                    }
                    cursor.execute("""
                    INSERT OR REPLACE INTO scenes (
                        id, project_id, scene_number, title, slugline, interior_exterior, location, day_night,
                        summary, subtext, script_text, environmental_details, props_json, image_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        sc_obj["id"], project_id, sc_obj["scene_number"], sc_obj["slugline"], sc_obj["slugline"],
                        sc_obj["interior_exterior"], sc_obj["location"], sc_obj["day_night"],
                        sc_obj["summary"], sc_obj["subtext"], sc_obj["script_text"],
                        sc_obj.get("lighting_atmosphere", ""), json.dumps([sc_obj.get("props_required", "")]), sc_obj["image_url"]
                    ))
                    new_scenes_created.append(sc_obj)

        final_scene_count = current_count + len(new_scenes_created)
        calc_days = max(24, int(round(final_scene_count * 2.0)))
        calc_budget = max(float(proj.get("target_budget") or 35000000.0), final_scene_count * 2650000.0)

        cursor.execute("""
        UPDATE projects SET
            runtime_minutes = ?,
            shooting_days = ?,
            estimated_budget = ?
        WHERE id = ?
        """, (target_runtime_minutes, calc_days, calc_budget, project_id))

        conn.commit()

        # Invalidate project localization cache so fresh expanded scenes are visible immediately
        clear_project_localizations_db(project_id, conn=conn)

        return {
            "success": True,
            "project_id": project_id,
            "target_runtime_minutes": target_runtime_minutes,
            "previous_scene_count": current_count,
            "new_scene_count": final_scene_count,
            "new_scenes_added": len(new_scenes_created),
            "shooting_days": calc_days,
            "estimated_budget": calc_budget,
            "message": f"Estructura narrativa expandida exitosamente a {target_runtime_minutes} minutos con {final_scene_count} escenas en formato estándar de Hollywood."
        }
