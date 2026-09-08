import json
import os
import re
import time
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from services.continuity_engine import ContinuityEngine
from services.screenplay_auditor import ScreenplayAuditor
from core.db import record_narrative_change_db, get_connection

# =============================================================================
# PYDANTIC STRUCTURED OUTPUT MODELS FOR SCENE INTELLIGENCE
# =============================================================================

class DialogueBeat(BaseModel):
    """Un parlamento cinematográfico individual con subtexto psicológico y acotación actoral."""
    character: str = Field(description="Nombre del personaje que habla (debe coincidir con los personajes presentes)")
    parenthetical: Optional[str] = Field(default=None, description="Acotación actoral o tono de voz, ej. '(susurrando con cautela)' o '(sin mirarlo)'")
    line: str = Field(description="Línea de diálogo hablada, profunda, contextual y libre de clichés o frases genéricas")
    subtext: str = Field(default="", description="Intención dramática, miedo o motivación oculta detrás de lo que dice el personaje")

class ActionParagraph(BaseModel):
    """Bloque de acción física, movimiento de cámara y atmósfera en la escena."""
    visual_beat: str = Field(description="Descripción visual cinematográfica de la acción física o bloqueo de los actores")
    sound_effect: Optional[str] = Field(default=None, description="Efectos de sonido o diseño sonoro diegético en este momento")
    lighting_atmosphere: Optional[str] = Field(default=None, description="Detalles de iluminación o textura visual en este instante")

class SceneScript(BaseModel):
    """Guion cinematográfico completo y detallado para una escena individual conforme al estándar de Hollywood."""
    scene_number: int = Field(description="Número correlativo de la escena")
    title: str = Field(description="Título descriptivo y evocador de la escena")
    slugline: str = Field(description="Encabezado técnico de guion (ej. 'INT. LABORATORIO DE GEOFÍSICA - NOCHE')")
    location: str = Field(description="Locación o set específico de la escena")
    interior_exterior: str = Field(default="INT", description="INT, EXT o INT/EXT")
    day_night: str = Field(default="NIGHT", description="DAY, NIGHT, DAWN, DUSK o CONTINUOUS")
    atmosphere: str = Field(description="Sensación sensorial, temperatura, humedad y atmósfera dramática")
    visual_description: str = Field(description="Estética visual, lentes de cámara, claroscuros y encuadre")
    summary: str = Field(description="Resumen narrativo conciso del beat de la escena")
    characters_present: List[str] = Field(description="Lista exacta de personajes que aparecen físicamente en esta escena")
    props: List[str] = Field(default_factory=list, description="Objetos y utilería clave utilizados o vistos en la escena")
    conflict: str = Field(description="Micro-conflicto central y fricción dramática que impulsa la escena")
    stakes: str = Field(description="Lo que los personajes ganan o pierden en este momento específico")
    subtext: str = Field(description="Tensión subyacente y dimensiones no verbales de la escena")
    dialogues: List[DialogueBeat] = Field(default_factory=list, description="Secuencia ordenada de diálogos entre los personajes presentes")
    action_beats: List[ActionParagraph] = Field(default_factory=list, description="Secuencia de párrafos de acción descriptiva")
    screenplay_text: str = Field(description="Texto completo del guion formateado en formato estándar de guion de Hollywood")
    transition: str = Field(default="CUT TO:", description="Transición de salida de escena (ej. 'CUT TO:', 'DISSOLVE TO:', 'FADE OUT.')")
    continuity_notes: str = Field(default="", description="Notas de continuidad: estado de conocimiento de los personajes y consecuencias directas")
    complexity: str = Field(default="MEDIUM", description="Complejidad de rodaje: LOW, MEDIUM, HIGH, EXTREME")
    estimated_cost: float = Field(default=3500.0, description="Costo estimado de rodaje de esta escena en USD")

class SceneChangeRequest(BaseModel):
    action_type: Literal[
        "CREATE_SCENE",
        "INSERT_SCENE",
        "EDIT_SCENE",
        "REGENERATE_SCENE",
        "DELETE_SCENE",
        "REWRITE_DIALOGUE",
        "CHANGE_LIGHTING_TIME",
        "GENERAL_EDIT"
    ] = Field(description="Tipo específico de operación sobre la escena")
    target_scene_number: int = Field(default=1, description="Número de escena principal objetivo")
    insert_after_scene_number: Optional[int] = Field(default=None, description="Número de escena tras la cual se inserta la nueva escena")
    description: str = Field(description="Descripción concisa de la intención del director")

class SceneImpact(BaseModel):
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(description="Nivel de severidad del cambio en la escena")
    affected_characters: List[str] = Field(default_factory=list, description="Personajes afectados")
    affected_props: List[str] = Field(default_factory=list, description="Objetos o utilería impactados")
    downstream_scenes_affected: List[int] = Field(default_factory=list, description="Escenas posteriores que dependen de este evento")
    consequences: List[str] = Field(default_factory=list, description="Consecuencias sobre la trama o continuidad")
    explanation: str = Field(description="Explicación del impacto y dependencias")

class SceneActionPlan(BaseModel):
    """Plan de acción estructurado para crear, modificar, insertar o regenerar escenas con Gemini."""
    change_request: SceneChangeRequest
    impact: SceneImpact
    updated_scene: Optional[SceneScript] = Field(default=None, description="Guion completo de la escena nueva o actualizada")
    requires_confirmation: bool = Field(default=False, description="True si la severidad es HIGH/CRITICAL y requiere aprobación")
    response_explanation: str = Field(description="Explicación cinematográfica profesional de la modificación realizada")

# =============================================================================
# SCENE & SCREENPLAY INTELLIGENCE ENGINE CLASS
# =============================================================================

class SceneEngine:
    """Motor de Inteligencia de Escenas y Guiones Cinematográficos (Fase 4)."""

    def __init__(self, client: Any = None):
        self.client = client
        self.candidate_models = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash"]

    def _format_screenplay_string(self, sc: SceneScript) -> str:
        """Construye un texto de guion formateado conforme al estándar de Hollywood."""
        lines = []
        lines.append(sc.slugline.upper())
        lines.append("")
        lines.append("FADE IN:")
        lines.append("")
        lines.append(sc.summary)
        lines.append("")

        for d in sc.dialogues:
            lines.append(d.character.upper())
            if d.parenthetical:
                lines.append(f"({d.parenthetical.strip('()')})")
            lines.append(d.line)
            lines.append("")

        lines.append(sc.transition or "CUT TO:")
        return "\n".join(lines)

    def generate_full_scene(
        self,
        scene_meta: Dict[str, Any],
        project: Dict[str, Any],
        characters: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        previous_scene: Optional[Dict[str, Any]] = None
    ) -> SceneScript:
        """Genera un guion cinematográfico completo (diálogo + acción) para una escena a partir de su contexto."""
        if not self.client:
            raise ValueError("Gemini Client no está inicializado en SceneEngine.")

        sc_num = scene_meta.get("scene_number", 1)
        sc_title = scene_meta.get("title", f"Escena {sc_num}")
        sc_slug = scene_meta.get("slugline", "INT. LOCACIÓN - DÍA")
        sc_summ = scene_meta.get("summary", "")
        raw_chars = scene_meta.get("characters_json") or "[]"
        if isinstance(raw_chars, str):
            try:
                present_names = json.loads(raw_chars)
            except Exception:
                present_names = [raw_chars]
        else:
            present_names = raw_chars

        char_dossier = []
        for c in characters:
            c_name = c.get("name", "")
            if any(p.lower() in c_name.lower() or c_name.lower() in p.lower() for p in present_names) or len(present_names) == 0:
                dna = json.loads(c.get("dna_json") or "{}") if isinstance(c.get("dna_json"), str) else (c.get("dna_json") or {})
                k_state = dna.get("knowledge_state", {})
                char_dossier.append(
                    f"• {c_name} ({c.get('role')} • {c.get('occupation')}):\n"
                    f"  - Personalidad: {c.get('personality')}\n"
                    f"  - Motivación actual: {c.get('motivation')}\n"
                    f"  - Miedos: {c.get('fears')}\n"
                    f"  - Conocimiento actual (KnowledgeState): {k_state.get('known_facts', [])}\n"
                    f"  - Secretos que guarda: {k_state.get('secrets_held', [])}"
                )

        rels_dossier = [
            f"• {r.get('source_character_id')} <-> {r.get('target_character_name')} ({r.get('rel_type')}): {r.get('history')}"
            for r in relationships
        ]

        prev_context = (
            f"ESCENA ANTERIOR (#{previous_scene.get('scene_number')} - {previous_scene.get('slugline')}):\n"
            f"Resumen: {previous_scene.get('summary')}\n"
            f"Consecuencia inmediata: {previous_scene.get('subtext', 'Continuidad de la trama')}"
            if previous_scene else "Esta es la escena de apertura del relato."
        )

        system_instruction = (
            "Eres el Guionista Principal y Showrunner de Hollywood en Agentic Cinema Studio.\n"
            "Tu misión es escribir un guion cinematográfico profesional, maduro, de alto calibre dramático "
            "y perfectamente formateado para la escena indicada.\n\n"
            f"PROYECTO: '{project.get('title')}' (Género: {project.get('genre')}, Tono: {project.get('tone')})\n"
            f"TEMA CENTRAL / MENSAJE: {project.get('central_theme', '')} | {project.get('environmental_message', '')}\n\n"
            f"{prev_context}\n\n"
            f"ESCENA A DESARROLLAR: Escena #{sc_num} | {sc_slug}\n"
            f"Resumen argumental previo: {sc_summ}\n\n"
            f"PERSONAJES EN ESTA ESCENA:\n" + ("\n".join(char_dossier) or "Personajes según la escaleta") + "\n\n"
            f"RELACIONES ENTRE ELLOS:\n" + ("\n".join(rels_dossier) or "Relaciones estándar") + "\n\n"
            "REGLAS CRÍTICAS DE ESCRITURA:\n"
            "1. NO uses clichés, ni frases genéricas prefabricadas.\n"
            "2. Los diálogos deben tener subtexto denso, pausas, acotaciones parenthetical oportunas y reflejar el KnowledgeState.\n"
            "3. Respeta el KnowledgeState: un personaje NO puede hablar de un secreto que todavía no ha descubierto.\n"
            "4. CONTROL DE REPETICIÓN: Los diálogos deben ser únicos, progresivos y hacer avanzar el conflicto dramático. NUNCA repitas parlamentos de escenas anteriores.\n"
            "5. Devuelve exclusivamente la estructura JSON requerida conforme al response_schema de SceneScript."
        )

        prompt = f"Escribe el guion completo de la Escena #{sc_num} ({sc_slug}). Incluye los diálogos completos y acciones."

        last_err = None
        for attempt in range(3):
            for model_name in self.candidate_models:
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json",
                            response_schema=SceneScript,
                            temperature=0.75
                        )
                    )
                    if response and response.text:
                        return SceneScript.model_validate_json(response.text)
                except Exception as e:
                    last_err = e
                    time.sleep(2)
                    continue

        raise RuntimeError(f"No se pudo generar el guion de la escena con Gemini API: {str(last_err)}")

    def insert_scene_at_position(
        self,
        prompt: str,
        insert_after: int,
        project: Dict[str, Any],
        characters: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        scenes: List[Dict[str, Any]],
        conn: Any
    ) -> Dict[str, Any]:
        """Inserta una nueva escena tras `insert_after`, renumerando las escenas posteriores en SQLite."""
        proj_id = project.get("id", "proj_default")
        new_scene_num = insert_after + 1
        cursor = conn.cursor()

        # Step 1: Renumber downstream scenes in reverse order to avoid unique constraint collisions
        downstream = [s for s in scenes if s.get("scene_number", 0) >= new_scene_num]
        downstream_sorted = sorted(downstream, key=lambda x: x.get("scene_number", 0), reverse=True)
        for s in downstream_sorted:
            old_num = s["scene_number"]
            cursor.execute("UPDATE scenes SET scene_number = ? WHERE id = ?", (old_num + 1, s["id"]))

        # Step 2: Generate the new inserted scene using Gemini
        scene_meta = {
            "scene_number": new_scene_num,
            "title": f"Escena {new_scene_num}: {prompt[:30]}",
            "slugline": f"INT. SECTOR {new_scene_num} - DÍA",
            "summary": prompt,
            "characters_json": json.dumps([c["name"] for c in characters[:2]])
        }
        prev_sc = next((s for s in scenes if s.get("scene_number") == insert_after), None)
        new_script = self.generate_full_scene(scene_meta, project, characters, relationships, prev_sc)

        new_scene_id = f"scene_{proj_id}_{new_scene_num}_{os.urandom(2).hex()}"
        formatted_script = new_script.screenplay_text or self._format_screenplay_string(new_script)

        cursor.execute("""
        INSERT INTO scenes (
            id, project_id, scene_number, title, slugline, location, interior_exterior,
            day_night, summary, script_text, subtext, environmental_details,
            characters_json, props_json, complexity, risk_score, estimated_cost
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            new_scene_id, proj_id, new_scene_num, new_script.title, new_script.slugline,
            new_script.location, new_script.interior_exterior, new_script.day_night,
            new_script.summary, formatted_script, new_script.subtext, new_script.atmosphere,
            json.dumps(new_script.characters_present), json.dumps(new_script.props),
            new_script.complexity, 30, new_script.estimated_cost
        ))

        conn.commit()

        # Step 3: Audit continuity
        cursor.execute("SELECT * FROM scenes WHERE project_id = ? ORDER BY scene_number ASC", (proj_id,))
        updated_scenes = [dict(s) for s in cursor.fetchall()]
        alerts = ContinuityEngine.scan_project_continuity(project, characters, updated_scenes)

        return {
            "action": "SCENE_INSERTED",
            "scene_number": new_scene_num,
            "scene_id": new_scene_id,
            "total_scenes": len(updated_scenes),
            "continuity_alerts_count": len(alerts),
            "response": (
                f"🎬 **Nueva Escena #{new_scene_num} Insertada con Éxito:**\n\n"
                f"Se ha creado e intercalado la nueva escena en la posición #{new_scene_num} y se han renumerado automáticamente las escenas posteriores (Total: {len(updated_scenes)} escenas).\n\n"
                f"• **Encabezado:** `{new_script.slugline}`\n"
                f"• **Personajes Presentes:** {', '.join(new_script.characters_present)}\n"
                f"• **Resumen:** {new_script.summary}\n"
                f"• **Conflicto / Subtexto:** {new_script.subtext}\n\n"
                f"**Muestra del Guion:**\n```\n" + "\n".join(formatted_script.splitlines()[:12]) + "\n...\n```"
            )
        }

    def delete_scene_by_number(
        self,
        target_scene_number: int,
        project: Dict[str, Any],
        characters: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        scenes: List[Dict[str, Any]],
        conn: Any
    ) -> Dict[str, Any]:
        """Elimina una escena específica y renumera las escenas posteriores hacia abajo."""
        proj_id = project.get("id", "proj_default")
        cursor = conn.cursor()

        target_sc = next((s for s in scenes if s.get("scene_number") == target_scene_number), None)
        if not target_sc:
            return {
                "response": f"❌ No se encontró la Escena #{target_scene_number} para eliminar.",
                "action": "ERROR_SCENE_NOT_FOUND"
            }

        # Step 1: Delete target scene
        cursor.execute("DELETE FROM scenes WHERE id = ?", (target_sc["id"],))

        # Step 2: Renumber downstream scenes
        downstream = [s for s in scenes if s.get("scene_number", 0) > target_scene_number]
        downstream_sorted = sorted(downstream, key=lambda x: x.get("scene_number", 0))
        for s in downstream_sorted:
            old_num = s["scene_number"]
            cursor.execute("UPDATE scenes SET scene_number = ? WHERE id = ?", (old_num - 1, s["id"]))

        conn.commit()

        # Step 3: Fetch updated scenes and audit continuity
        cursor.execute("SELECT * FROM scenes WHERE project_id = ? ORDER BY scene_number ASC", (proj_id,))
        updated_scenes = [dict(s) for s in cursor.fetchall()]
        alerts = ContinuityEngine.scan_project_continuity(project, characters, updated_scenes)

        return {
            "action": "SCENE_DELETED",
            "deleted_scene_number": target_scene_number,
            "total_scenes": len(updated_scenes),
            "continuity_alerts_count": len(alerts),
            "response": (
                f"🗑️ **Escena #{target_scene_number} Eliminada:**\n\n"
                f"La escena ha sido retirada de la producción '{project.get('title')}'. Se han renumerado las escenas posteriores para mantener la secuencia correlativa intacta (Total restante: {len(updated_scenes)} escenas).\n\n"
                f"• **Escena eliminada:** `{target_sc.get('slugline')}`\n"
                f"• **Alertas de Continuidad Post-Eliminación:** {len(alerts)}"
            )
        }

    def process_scene_conversational_edit(
        self,
        prompt: str,
        project: Dict[str, Any],
        characters: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        scenes: List[Dict[str, Any]],
        conn: Any
    ) -> Dict[str, Any]:
        """Interpreta cualquier instrucción conversacional sobre escenas (crear, insertar, editar, regenerar, eliminar)."""
        if not self.client:
            raise ValueError("Gemini Client no está configurado en SceneEngine.")

        p_low = prompt.lower()

        # 1. Detect Scene Insertion: "Añade una escena entre la 4 y la 5...", "Pon una escena entre la 8 y la 9..."
        between_match = re.search(r'(?:entre|después de|despues de)\s+(?:la\s+)?(\d+)(?:\s+y\s+(?:la\s+)?(\d+))?', p_low)
        if between_match and any(w in p_low for w in ["añade", "agrega", "pon", "inserta", "crea una escena"]):
            insert_after = int(between_match.group(1))
            return self.insert_scene_at_position(
                prompt=prompt,
                insert_after=insert_after,
                project=project,
                characters=characters,
                relationships=relationships,
                scenes=scenes,
                conn=conn
            )

        # 2. Detect Scene Deletion: "Elimina la escena 10...", "Borra la escena 4..."
        delete_match = re.search(r'(?:elimina|borra|quita|remover)\s+(?:la\s+)?escena\s*#?\s*(\d+)', p_low)
        if delete_match:
            target_sc_num = int(delete_match.group(1))
            return self.delete_scene_by_number(
                target_scene_number=target_sc_num,
                project=project,
                characters=characters,
                relationships=relationships,
                scenes=scenes,
                conn=conn
            )

        # 3. Detect Scene Identification for Edit or Regeneration
        sc_num_match = re.search(r'escena\s*#?\s*(\d+)', p_low)
        target_sc_num = int(sc_num_match.group(1)) if sc_num_match else None

        current_scene = None
        if target_sc_num:
            current_scene = next((s for s in scenes if s.get("scene_number") == target_sc_num), None)
        if not current_scene and scenes:
            current_scene = scenes[0]

        if not current_scene:
            return {
                "response": "❌ No hay escenas registradas en este proyecto para modificar.",
                "action": "ERROR_NO_SCENES"
            }

        sc_num = current_scene.get("scene_number", 1)
        prev_scene = next((s for s in scenes if s.get("scene_number") == sc_num - 1), None)

        char_summary = "\n".join([f"- {c.get('name')} ({c.get('role')} • {c.get('occupation')})" for c in characters])
        rels_summary = "\n".join([f"- {r.get('source_character_id')} -> {r.get('target_character_name')} ({r.get('rel_type')}): {r.get('history')}" for r in relationships])

        system_instruction = (
            "Eres el Co-Director y Guionista Experto de Agentic Cinema Studio.\n"
            "Tu misión es interpretar la instrucción del usuario para modificar o regenerar una escena cinematográfica específica, "
            "actualizando únicamente los elementos requeridos y manteniendo la coherencia total con el proyecto.\n\n"
            f"PROYECTO: '{project.get('title')}' (Género: {project.get('genre')}, Logline: {project.get('logline')})\n"
            f"REPARTO REGISTRADO:\n{char_summary}\n\n"
            f"RELACIONES REGISTRADAS:\n{rels_summary}\n\n"
            f"ESCENA ACTUAL A MODIFICAR (Escena #{sc_num}):\n"
            f"• Slugline: {current_scene.get('slugline')}\n"
            f"• Resumen actual: {current_scene.get('summary')}\n"
            f"• Personajes presentes actuales: {current_scene.get('characters_json')}\n"
            f"• Props actuales: {current_scene.get('props_json')}\n"
            f"• Subtexto / Conflicto: {current_scene.get('subtext')}\n"
            f"• Guion actual:\n{current_scene.get('script_text')}\n\n"
            "INSTRUCCIONES CLAVE:\n"
            "1. Si el usuario pide regenerar la escena preservando los hechos (ej. 'Regenera la escena 8 pero conserva los eventos'):\n"
            "   - Conserva los personajes, props y resumen central, pero pule y eleva la tensión dramática del guion y los diálogos.\n"
            "2. Si el usuario pide un enfrentamiento o confrontación (ej. 'Haz que Mara confronte a Marcus en la escena 12'):\n"
            "   - Escribe diálogos densos con subtexto, parentheticals y tensión basada en sus secretos y personalidades.\n"
            "3. Si el usuario pide un giro narrativo (ej. 'En la escena 7 Mara descubre que Marcus la estuvo engañando'):\n"
            "   - Integra la revelación dramática en el resumen y los diálogos.\n"
            "4. Devuelve exclusivamente la estructura JSON conforme al response_schema de SceneActionPlan."
        )

        plan = None
        last_edit_err = None
        for attempt in range(3):
            for model_name in self.candidate_models:
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=f"Instrucción del Director:\n{prompt}",
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json",
                            response_schema=SceneActionPlan,
                            temperature=0.7
                        )
                    )
                    if response and response.text:
                        plan = SceneActionPlan.model_validate_json(response.text)
                        break
                except Exception as e:
                    last_edit_err = e
                    time.sleep(2)
                    continue
            if plan and plan.updated_scene:
                break

        if not plan or not plan.updated_scene:
            raise RuntimeError(f"No se pudo procesar la modificación de escena con Gemini API: {str(last_edit_err)}")

        sc_data = plan.updated_scene
        sc_id = current_scene["id"]
        cursor = conn.cursor()

        formatted_script = sc_data.screenplay_text
        if not formatted_script or len(formatted_script) < 30:
            formatted_script = self._format_screenplay_string(sc_data)

        cursor.execute("""
        UPDATE scenes SET
            title = ?, slugline = ?, location = ?, interior_exterior = ?, day_night = ?,
            summary = ?, script_text = ?, subtext = ?, environmental_details = ?,
            characters_json = ?, props_json = ?, complexity = ?, estimated_cost = ?
        WHERE id = ?
        """, (
            sc_data.title, sc_data.slugline, sc_data.location,
            sc_data.interior_exterior, sc_data.day_night,
            sc_data.summary, formatted_script,
            sc_data.subtext or f"Conflicto: {sc_data.conflict}. Stakes: {sc_data.stakes}.",
            sc_data.atmosphere,
            json.dumps(sc_data.characters_present),
            json.dumps(sc_data.props),
            sc_data.complexity,
            sc_data.estimated_cost,
            sc_id
        ))
        conn.commit()

        # Step 4: Audit continuity after modification
        cursor.execute("SELECT * FROM scenes WHERE project_id = ? ORDER BY scene_number ASC", (project.get("id"),))
        updated_scenes = [dict(s) for s in cursor.fetchall()]
        alerts = ContinuityEngine.scan_project_continuity(project, characters, updated_scenes)

        return {
            "response": (
                f"🎬 **Escena #{sc_num} Actualizada con Inteligencia Cinematográfica:**\n\n"
                f"{plan.response_explanation}\n\n"
                f"• **Encabezado:** `{sc_data.slugline}`\n"
                f"• **Personajes Presentes:** {', '.join(sc_data.characters_present)}\n"
                f"• **Resumen:** {sc_data.summary}\n"
                f"• **Conflicto / Subtexto:** {sc_data.subtext}\n"
                f"• **Alertas de Continuidad Post-Edición:** {len(alerts)}\n\n"
                f"**Muestra del Guion:**\n```\n" + "\n".join(formatted_script.splitlines()[:14]) + "\n...\n```"
            ),
            "action": plan.change_request.action_type if hasattr(plan, 'change_request') and plan.change_request else "SCENE_UPDATED",
            "scene_number": sc_num,
            "scene_id": sc_id,
            "continuity_alerts_count": len(alerts)
        }
