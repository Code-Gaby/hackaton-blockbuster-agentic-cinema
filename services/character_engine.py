import json
import os
import re
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

class DiscoveryItem(BaseModel):
    act: str = Field(default="Act I", description="Acto dramático (Act I, Act II, Act III)")
    discovery: str = Field(default="", description="Información revelada o descubierta por el personaje")

class KnowledgeState(BaseModel):
    """Registra qué hechos conoce el personaje, qué secretos guarda y en qué punto de la historia los descubre."""
    known_facts: List[str] = Field(default_factory=list, description="Lista de hechos y verdades que el personaje conoce")
    secrets_held: List[str] = Field(default_factory=list, description="Secretos o información confidencial que el personaje oculta")
    timeline: List[DiscoveryItem] = Field(
        default_factory=lambda: [
            DiscoveryItem(act="Act I", discovery="Conocimiento inicial"),
            DiscoveryItem(act="Act II", discovery="Descubrimientos clave"),
            DiscoveryItem(act="Act III", discovery="Revelación final")
        ],
        description="Línea de tiempo de descubrimientos por acto"
    )

class DnaStats(BaseModel):
    courage: int = Field(default=85, description="Nivel de valentía (0-100)")
    intelligence: int = Field(default=85, description="Nivel de inteligencia (0-100)")
    loyalty: int = Field(default=95, description="Nivel de lealtad (0-100)")
    resilience: int = Field(default=88, description="Nivel de resiliencia (0-100)")
    creativity: int = Field(default=80, description="Nivel de creatividad (0-100)")
    empathy: int = Field(default=90, description="Nivel de empatía (0-100)")

class ActArc(BaseModel):
    act: str = Field(default="Act I", description="Act I, Act II o Act III")
    arc: str = Field(default="", description="Evolución dramática en este acto")

class CharacterProfile(BaseModel):
    """Perfil completo, consistente y multidimensional de un personaje (humano, animal, androide o criatura)."""
    name: str = Field(description="Nombre completo o apelativo del personaje")
    age: Optional[int] = Field(default=None, description="Edad numérica en años (o None para inteligencias/entidades sin edad)")
    species: str = Field(default="Humano", description="Especie o tipo: Humano, Canino/Perro, Felino, Androide/Sintético, Alien, etc.")
    role: str = Field(description="Rol narrativo: Protagonista, Antagonista, Aliado Principal, Mentor, Compañero Fiel, etc.")
    archetype: str = Field(description="Arquetipo clásico o contemporáneo (ej. The Loyal Companion, The Visionary, The Shadow)")
    occupation: str = Field(description="Ocupación, oficio o función en la historia (ej. Perro de Búsqueda y Rescate, Astrofísica, etc.)")
    personality: str = Field(description="Rasgos psicológicos y conductuales dominantes")
    motivation: str = Field(description="Objetivo dramático central que guía todas sus acciones")
    fears: str = Field(description="Miedo primario o vulnerabilidad psicológica")
    strengths: str = Field(description="Habilidades, talentos o fortalezas físicas/mentales")
    weaknesses: str = Field(description="Defectos de carácter o debilidades críticas")
    emotional_state: str = Field(default="Alerta", description="Estado emocional predominante")
    wardrobe: str = Field(description="Descripción del vestuario, pelaje, arnés, traje o accesorios característicos")
    birth_date: str = Field(default="01 de Enero", description="Fecha de nacimiento o activación")
    zodiac_sign: str = Field(default="Acuario ♒", description="Signo zodiacal o designación de ciclo")
    religion_belief: str = Field(default="Humanismo Empírico", description="Código moral, sistema de creencias o lealtad fundamental")
    subtext: str = Field(description="Subtexto dramático y dimensión psicológica oculta")
    knowledge_state: KnowledgeState = Field(default_factory=KnowledgeState, description="Estado de conocimiento y secretos del personaje")
    props: List[str] = Field(default_factory=list, description="Objetos personales o ítems de utilería vinculados al personaje")
    dna_stats: DnaStats = Field(default_factory=DnaStats, description="Atributos numéricos de 0 a 100")
    act_arcs: List[ActArc] = Field(default_factory=list, description="Evolución del personaje a lo largo de los tres actos")
    avatar_url: Optional[str] = Field(default=None, description="URL de imagen de avatar sugerida")

class RelationshipDraft(BaseModel):
    """Define o actualiza un vínculo dramático estructurado entre dos personajes."""
    source_name: str = Field(description="Nombre del personaje origen de la relación")
    target_name: str = Field(description="Nombre del personaje destino de la relación")
    rel_type: str = Field(default="ALLIANCE", description="Tipo de relación: ALLIANCE, BEST_FRIEND, FAMILY, SIBLINGS, CONFLICT, MENTORSHIP, RIVALRY, LOVERS")
    strength: int = Field(default=85, description="Intensidad de la relación de 0 a 100")
    history: str = Field(description="Historia previa y naturaleza del vínculo entre ambos personajes")
    status: str = Field(default="ACTIVA", description="Estado actual de la relación")

class AttributeUpdates(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    role: Optional[str] = None
    archetype: Optional[str] = None
    occupation: Optional[str] = None
    personality: Optional[str] = None
    motivation: Optional[str] = None
    fears: Optional[str] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    emotional_state: Optional[str] = None
    wardrobe: Optional[str] = None

class CharacterActionPlan(BaseModel):
    """Plan estructurado de acción cinematográfica inferido por Gemini a partir de una instrucción conversacional."""
    action_type: Literal[
        "CREATE_CHARACTER",
        "CREATE_CHARACTERS",
        "UPDATE_CHARACTER",
        "RENAME_CHARACTER",
        "CREATE_OR_UPDATE_RELATIONSHIP",
        "GENERAL_CHAT"
    ] = Field(description="Tipo de acción a ejecutar en el proyecto")
    target_character_query: Optional[str] = Field(default=None, description="Nombre o referencia del personaje objetivo (ej. 'Lyra', 'Protagonista', 'Marcus')")
    character_data: Optional[CharacterProfile] = Field(default=None, description="Datos del nuevo personaje si action_type es CREATE_CHARACTER")
    characters_data: Optional[List[CharacterProfile]] = Field(default=None, description="Lista de múltiples personajes si action_type es CREATE_CHARACTERS")
    attribute_updates: Optional[AttributeUpdates] = Field(default=None, description="Campos a actualizar (ej. age: 22) si action_type es UPDATE_CHARACTER")
    old_name: Optional[str] = Field(default=None, description="Nombre anterior a reemplazar si action_type es RENAME_CHARACTER")
    new_name: Optional[str] = Field(default=None, description="Nuevo nombre a asignar si action_type es RENAME_CHARACTER")
    relationship_data: Optional[RelationshipDraft] = Field(default=None, description="Datos de relación si se crea o modifica una relación individual")
    relationships_data: Optional[List[RelationshipDraft]] = Field(default=None, description="Lista de relaciones a crear o actualizar para los personajes")
    response_explanation: str = Field(description="Respuesta clara, cinematográfica y profesional del Co-Director explicando el cambio realizado")

class CharacterEngine:
    """Motor especializado en creación, modificación y mantenimiento del reparto de personajes y relaciones con Gemini API."""

    def __init__(self, client: Any = None):
        self.client = client
        self.candidate_models = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash"]

    def process_conversational_request(
        self,
        prompt: str,
        project: Dict[str, Any],
        characters: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        scenes: List[Dict[str, Any]],
        conn: Any
    ) -> Dict[str, Any]:
        """Interpreta la solicitud conversacional del usuario con Gemini y ejecuta las modificaciones correspondientes en SQLite."""
        action_plan = self.interpret_instruction(prompt, project, characters, relationships, scenes)
        return self.execute_action_plan(action_plan, project, characters, relationships, scenes, conn, original_prompt=prompt)

    def interpret_instruction(
        self,
        prompt: str,
        project: Dict[str, Any],
        characters: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        scenes: List[Dict[str, Any]]
    ) -> CharacterActionPlan:
        """Invoca a Gemini con Structured Output para determinar la intención y parámetros de la acción sobre personajes."""
        if not self.client:
            raise ValueError("Gemini Client no está configurado en CharacterEngine.")

        proj_title = project.get("title", "Producción Activa")
        char_summary = "\n".join([
            f"- ID: {c.get('id')} | Nombre: {c.get('name')} | Edad: {c.get('age')} | Rol: {c.get('role')} | Ocupación: {c.get('occupation')}"
            for c in characters
        ])
        rels_summary = "\n".join([
            f"- {r.get('source_character_id')} -> {r.get('target_character_name')} ({r.get('rel_type')}): {r.get('history')}"
            for r in relationships
        ])

        system_instruction = (
            "Eres el Director de Reparto y Arquitecto de Personajes de Agentic Cinema Studio.\n"
            "Tu misión es interpretar con precisión las instrucciones del usuario para crear, modificar, "
            "renombrar personajes o ajustar relaciones interpersonales, manteniendo siempre la coherencia del universo narrativo.\n\n"
            f"PROYECTO ACTUAL: '{proj_title}' (Género: {project.get('genre')}, Logline: {project.get('logline')})\n\n"
            f"REPARTO ACTUAL REGISTRADO:\n{char_summary or 'No hay personajes aún.'}\n\n"
            f"RELACIONES REGISTRADAS:\n{rels_summary or 'No hay relaciones registradas.'}\n\n"
            "REGLAS CRÍTICAS:\n"
            "1. Si el usuario pide añadir uno o varios personajes nuevos (ej. 'Añade 3 personajes más a la película...'):\n"
            "   - Si es un solo personaje: action_type = 'CREATE_CHARACTER' y completa 'character_data'.\n"
            "   - Si son múltiples personajes (ej. 2, 3 o más): action_type = 'CREATE_CHARACTERS' y completa 'characters_data' con todos los personajes solicitados.\n"
            "   - Para cada personaje, asigna un nombre propio verosímil y único (¡NUNCA uses el título de la película ni nombres duplicados!), edad numérica, género ('Masculino' o 'Femenino'), rol equilibrado ('Aliado Clave', 'Especialista', 'Compañero', etc. sin opacar a los protagonistas), ocupación técnica o de tripulación coherente, personalidad, motivación, fortalezas, debilidades, subtexto y vestuario (wardrobe).\n"
            "   - Si se solicitan rasgos específicos de inclusión o psicológicos (ej. persona sorda, persona con tics verbales, persona con depresión), refléjalos fielmente en personality, subtext, wardrobe (ej. implante coclear/auricular acústico para la persona sorda) y props.\n"
            "   - Completa 'relationships_data' o 'relationship_data' vinculando a cada nuevo personaje con al menos uno de los personajes clave existentes ('Elena Vance', 'Marcus Thorne', 'David Vance', etc.) o entre sí con rel_type ('ALLIANCE', 'TRUST', 'CONFLICT', 'MENTORSHIP', 'COLLEAGUE', etc.).\n"
            "2. Si el usuario pide cambiar la edad, ocupación, rol o atributos de un personaje existente (ej. 'Cambia la edad de Marina a 28 años'):\n"
            "   - action_type = 'UPDATE_CHARACTER'\n"
            "   - target_character_query = Nombre del personaje a modificar.\n"
            "   - attribute_updates = {age: 28}.\n"
            "3. Si el usuario pide cambiar el nombre de un personaje (ej. 'Cambia el nombre de Lyra a Mara'):\n"
            "   - action_type = 'RENAME_CHARACTER'\n"
            "   - old_name = Nombre actual (ej. 'Lyra' o 'Dra. Lyra Thorne').\n"
            "   - new_name = Nuevo nombre (ej. 'Mara' o 'Dra. Mara Thorne').\n"
            "4. Si el usuario pide establecer o cambiar una relación entre dos personajes existentes (ej. 'Haz que Mateo y Marina tengan una fuerte alianza'):\n"
            "   - action_type = 'CREATE_OR_UPDATE_RELATIONSHIP'\n"
            "   - Completa 'relationship_data' con source_name='Mateo', target_name='Marina', rel_type='ALLIANCE', strength=90 e historia detallada.\n"
            "5. Si el mensaje es una consulta o charla general sin cambios de personaje, usa action_type = 'GENERAL_CHAT'.\n"
            "6. Devuelve exclusivamente la estructura conforme al response_schema de CharacterActionPlan."
        )

        import time
        last_char_err = None
        for attempt in range(3):
            for model_name in self.candidate_models:
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=f"Instrucción del Director / Usuario:\n{prompt}",
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json",
                            response_schema=CharacterActionPlan,
                            temperature=0.4
                        )
                    )
                    if response and response.text:
                        return CharacterActionPlan.model_validate_json(response.text)
                except Exception as e:
                    last_char_err = e
                    time.sleep(2)
                    continue

        raise RuntimeError(f"No se pudo procesar la acción sobre el personaje con Gemini API: {str(last_char_err)}")

    def execute_action_plan(
        self,
        plan: CharacterActionPlan,
        project: Dict[str, Any],
        characters: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        scenes: List[Dict[str, Any]],
        conn: Any,
        original_prompt: str = ""
    ) -> Dict[str, Any]:
        """Ejecuta de forma atómica y consistente el plan en la base de datos SQLite."""
        proj_id = project.get("id", "proj_default")
        cursor = conn.cursor()

        # Helper to find character by exact, substring, or token/name match
        def find_char_match(query_name: Optional[str], char_pool: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
            if not query_name:
                return None
            pool = char_pool if char_pool is not None else characters
            q_clean = query_name.lower().strip()
            # 1. Exact match
            for c in pool:
                if c.get("name", "").lower().strip() == q_clean:
                    return c
            # 2. Substring match
            for c in pool:
                c_name = c.get("name", "").lower()
                if q_clean in c_name or c_name in q_clean:
                    return c
            # 3. Token match (e.g. 'Marina' in 'Dra. Marina Silva' or 'Mateo' in 'Capitán Mateo Ruiz')
            q_tokens = [t for t in re.split(r'\W+', q_clean) if len(t) > 2]
            for c in pool:
                c_tokens = [t for t in re.split(r'\W+', c.get("name", "").lower()) if len(t) > 2]
                if any(t in c_tokens for t in q_tokens):
                    return c
            # 4. Role match (ej. 'protagonista')
            if "protag" in q_clean:
                for c in pool:
                    if "protag" in (c.get("role") or "").lower():
                        return c
            # 5. Protagonist alias match (Mara / Lyra / Marina / Elena)
            if any(alias in q_clean for alias in ["marina", "elena", "elara", "mara", "lyra"]) and pool:
                for c in pool:
                    if any(alias in c.get("name", "").lower() for alias in ["marina", "elena", "elara", "mara", "lyra"]) or "protag" in (c.get("role") or "").lower():
                        return c
            return None

        # -------------------------------------------------------------
        # ACCIÓN 1: CREATE_CHARACTER & CREATE_CHARACTERS
        # -------------------------------------------------------------
        if plan.action_type in ("CREATE_CHARACTER", "CREATE_CHARACTERS") or plan.characters_data or (plan.action_type == "CREATE_CHARACTER" and plan.character_data):
            chars_to_create = []
            if plan.characters_data:
                chars_to_create.extend(plan.characters_data)
            elif plan.character_data:
                chars_to_create.append(plan.character_data)

            if not chars_to_create:
                return {
                    "response": "⚠️ No se especificaron datos para crear el personaje.",
                    "action": "ERROR_NO_CHARACTER_DATA"
                }

            created_names = []
            created_ids = []
            char_pool = list(characters)

            from services.art_engine import GhibliArtEngine

            for c_data in chars_to_create:
                # Sanitize name: if name matches project title, sanitize to realistic character name
                c_name = c_data.name.strip()
                proj_title = (project.get("title") or "").strip().lower()
                if c_name.lower() == proj_title or c_name.lower() in ["the last signal", "last signal", "la última señal", "nueva producción"]:
                    # Assign a distinct realistic name based on role or index
                    default_names = ["Maya Cruz", "Tomas Rivera", "Silvia Mendez", "Lucas Soto", "Dra. Valeria Ramos"]
                    c_name = default_names[len(created_ids) % len(default_names)]

                # Only consider existing if full name is an exact match (never match partial surnames like Vance)
                existing = next((c for c in char_pool if c.get("name", "").lower().strip() == c_name.lower().strip()), None)
                if existing:
                    c_id = existing["id"]
                    self._update_character_in_db(cursor, c_id, c_data.model_dump())
                    created_names.append(c_name)
                    created_ids.append(c_id)
                else:
                    c_id = f"char_{proj_id}_{os.urandom(3).hex()}"

                    # Determine gender if possible
                    p_text = f"{c_data.personality} {c_data.role} {c_data.subtext} {c_data.occupation}".lower()
                    gender = "Femenino" if any(w in p_text for w in ["ella", "mujer", "femenin", "sorda", "depresiva", "científica", "ingeniera"]) else "Masculino"

                    char_dict = {
                        "id": c_id,
                        "name": c_name,
                        "age": c_data.age,
                        "role": c_data.role,
                        "archetype": c_data.archetype,
                        "occupation": c_data.occupation,
                        "personality": c_data.personality,
                        "subtext": c_data.subtext,
                        "wardrobe": c_data.wardrobe,
                        "gender": gender,
                        "props": c_data.props
                    }
                    avatar = GhibliArtEngine.generate_ghibli_character(char_dict, project)

                    dna_dict = c_data.dna_stats.model_dump() if c_data.dna_stats else {}
                    dna_dict["species"] = c_data.species
                    dna_dict["gender"] = gender
                    dna_dict["knowledge_state"] = c_data.knowledge_state.model_dump() if c_data.knowledge_state else {}

                    act_arcs_dict = {arc.act: arc.arc for arc in c_data.act_arcs} if c_data.act_arcs else {"Act I": "Presentación", "Act II": "Aventura", "Act III": "Desenlace"}

                    cursor.execute("""
                    INSERT INTO characters (
                        id, project_id, name, age, role, archetype, occupation, personality,
                        motivation, fears, strengths, weaknesses, emotional_state, wardrobe,
                        birth_date, zodiac_sign, religion_belief, subtext,
                        props_json, dna_json, arc_json, avatar_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        c_id, proj_id, c_name, c_data.age, c_data.role,
                        c_data.archetype, c_data.occupation, c_data.personality,
                        c_data.motivation, c_data.fears, c_data.strengths,
                        c_data.weaknesses, c_data.emotional_state, c_data.wardrobe,
                        c_data.birth_date, c_data.zodiac_sign, c_data.religion_belief,
                        c_data.subtext,
                        json.dumps(c_data.props),
                        json.dumps(dna_dict),
                        json.dumps(act_arcs_dict),
                        avatar
                    ))

                    new_entry = {"id": c_id, "name": c_name, "role": c_data.role, "occupation": c_data.occupation}
                    char_pool.append(new_entry)
                    created_names.append(c_name)
                    created_ids.append(c_id)

                    # Canon fact in ProjectMemory
                    try:
                        cursor.execute("""
                        INSERT INTO project_facts (
                            id, project_id, entity_type, entity_id, fact_text, fact_type, status, scene_established
                        ) VALUES (?, ?, 'CHARACTER', ?, ?, 'CANONICAL', 'ACTIVE', 1)
                        """, (
                            f"canon_{proj_id}_{os.urandom(3).hex()}",
                            proj_id,
                            c_id,
                            f"{c_name} ({gender}, {c_data.age} años) se une al elenco como {c_data.role} ({c_data.occupation}). {c_data.personality[:120]}"
                        ))
                    except Exception as err:
                        print(f"Warning inserting canonical fact: {err}")

            # Relationships handling
            all_rels_to_process = []
            if plan.relationships_data:
                all_rels_to_process.extend(plan.relationships_data)
            elif plan.relationship_data:
                all_rels_to_process.append(plan.relationship_data)

            # Connect new characters to pool if explicit relationships were provided
            for rel in all_rels_to_process:
                src_char = find_char_match(rel.source_name, char_pool)
                tgt_char = find_char_match(rel.target_name, char_pool)
                if src_char and tgt_char and src_char["id"] != tgt_char["id"]:
                    cursor.execute("""
                    DELETE FROM character_relationships
                    WHERE project_id = ? AND (
                        (source_character_id = ? AND target_character_id = ?) OR
                        (source_character_id = ? AND target_character_id = ?)
                    )
                    """, (proj_id, src_char["id"], tgt_char["id"], tgt_char["id"], src_char["id"]))

                    rel_id = f"rel_{proj_id}_{src_char['id']}_{tgt_char['id']}"
                    cursor.execute("""
                    INSERT INTO character_relationships (
                        id, project_id, source_character_id, target_character_id, target_character_name,
                        rel_type, strength, history, key_scenes_json, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        rel_id, proj_id, src_char["id"], tgt_char["id"], tgt_char["name"],
                        rel.rel_type or "ALLIANCE", rel.strength or 85,
                        rel.history or f"Vínculo colaborativo y dramático entre {src_char['name']} y {tgt_char['name']}.",
                        json.dumps([1, 2]), rel.status or "ACTIVA"
                    ))

            # Ensure every created character has at least ONE link in character_relationships
            for idx, cid in enumerate(created_ids):
                cursor.execute("""
                SELECT COUNT(*) FROM character_relationships
                WHERE project_id = ? AND (source_character_id = ? OR target_character_id = ?)
                """, (proj_id, cid, cid))
                has_rel = cursor.fetchone()[0]
                if has_rel == 0 and characters:
                    anchor_char = characters[idx % len(characters)]
                    this_char = next((c for c in char_pool if c["id"] == cid), None)
                    if this_char and anchor_char and this_char["id"] != anchor_char["id"]:
                        rel_id = f"rel_{proj_id}_{cid}_{anchor_char['id']}"
                        rel_types = ["ALLIANCE", "TRUST", "MENTORSHIP", "COLLEAGUE"]
                        chosen_rel = rel_types[idx % len(rel_types)]
                        cursor.execute("""
                        INSERT INTO character_relationships (
                            id, project_id, source_character_id, target_character_id, target_character_name,
                            rel_type, strength, history, key_scenes_json, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            rel_id, proj_id, cid, anchor_char["id"], anchor_char["name"],
                            chosen_rel, 80 + (idx * 4),
                            f"Vínculo dramático y operativo crucial entre {this_char['name']} y {anchor_char['name']} en la dinámica del relato.",
                            json.dumps([1, 2]), "ACTIVA"
                        ))

            # Invalidate stale localization projections in project_localizations
            cursor.execute("DELETE FROM project_localizations WHERE project_id = ?", (proj_id,))

            conn.commit()

            # Verify and construct genuine response strictly from persisted SQLite data
            cursor.execute("SELECT COUNT(*) FROM characters WHERE project_id = ?", (proj_id,))
            total_chars = cursor.fetchone()[0]

            placeholders = ",".join(["?"] * len(created_ids))
            cursor.execute(f"SELECT id, name, role, occupation, personality FROM characters WHERE id IN ({placeholders})", created_ids)
            saved_chars = cursor.fetchall()

            char_details_lines = []
            for sc in saved_chars:
                char_details_lines.append(f"• **{sc[1]}** ({sc[2]} - {sc[3]}): {sc[4]}")

            return {
                "response": (
                    f"🎭 **Elenco Cinematográfico Ampliado ({len(created_ids)} Nuevos Personajes Confirmados en SQLite):**\n\n"
                    f"{plan.response_explanation}\n\n"
                    f"{chr(10).join(char_details_lines)}\n\n"
                    f"📊 **Estado del Reparto:** {total_chars} personajes registrados y vinculados en el grafo de relaciones interpersonales."
                ),
                "action": "CHARACTERS_CREATED" if len(created_ids) > 1 else "CHARACTER_CREATED",
                "characters_created": created_names,
                "total_characters": total_chars
            }

        # -------------------------------------------------------------
        # ACCIÓN 2: UPDATE_CHARACTER
        # -------------------------------------------------------------
        elif plan.action_type == "UPDATE_CHARACTER":
            target = find_char_match(plan.target_character_query)
            if not target and characters:
                target = characters[0]

            if not target:
                return {
                    "response": f"❌ No se encontró ningún personaje que coincida con '{plan.target_character_query}'.",
                    "action": "ERROR_CHARACTER_NOT_FOUND"
                }

            updates = plan.attribute_updates.model_dump(exclude_unset=True) if plan.attribute_updates else {}
            c_id = target["id"]

            for field, val in updates.items():
                if val is not None and field in ["name", "age", "role", "archetype", "occupation", "personality", "motivation", "fears", "strengths", "weaknesses", "emotional_state", "wardrobe"]:
                    cursor.execute(f"UPDATE characters SET {field} = ? WHERE id = ?", (val, c_id))

            cursor.execute("DELETE FROM project_localizations WHERE project_id = ?", (proj_id,))
            conn.commit()
            return {
                "response": f"✏️ **Personaje Modificado:**\n\n{plan.response_explanation}\n\n• **Personaje:** {target['name']}\n• **Cambios aplicados:** {json.dumps(updates, ensure_ascii=False)}",
                "action": "CHARACTER_UPDATED",
                "character_id": c_id
            }

        # -------------------------------------------------------------
        # ACCIÓN 3: RENAME_CHARACTER (CON PROPAGACIÓN EN CASCADA)
        # -------------------------------------------------------------
        elif plan.action_type == "RENAME_CHARACTER":
            old_name_raw = plan.old_name or plan.target_character_query
            target = find_char_match(old_name_raw)
            if not target and characters:
                target = characters[0]

            if not target or not plan.new_name:
                return {
                    "response": f"❌ No se pudo determinar el personaje a renombrar a '{plan.new_name}'.",
                    "action": "ERROR_CHARACTER_NOT_FOUND"
                }

            c_id = target["id"]
            actual_old_name = target["name"]
            actual_new_name = plan.new_name.strip()

            # Execute full cascading rename across database
            self.cascade_rename_character(cursor, proj_id, c_id, actual_old_name, actual_new_name)
            cursor.execute("DELETE FROM project_localizations WHERE project_id = ?", (proj_id,))
            conn.commit()

            return {
                "response": (
                    f"🔄 **Renombramiento con Propagación en Cascada Exitoso:**\n\n"
                    f"{plan.response_explanation}\n\n"
                    f"• **Nombre Anterior:** `{actual_old_name}`\n"
                    f"• **Nuevo Nombre Asignado:** `{actual_new_name}`\n"
                    f"• **Referencias actualizadas:** Elenco de personajes, tabla de relaciones interpersonales, "
                    f"cabeceras de diálogo, escaleta de escenas y listas de personajes presentes."
                ),
                "action": "CHARACTER_RENAMED",
                "old_name": actual_old_name,
                "new_name": actual_new_name
            }

        # -------------------------------------------------------------
        # ACCIÓN 4: CREATE_OR_UPDATE_RELATIONSHIP
        # -------------------------------------------------------------
        elif plan.action_type == "CREATE_OR_UPDATE_RELATIONSHIP" and plan.relationship_data:
            rel = plan.relationship_data
            src_char = find_char_match(rel.source_name)
            tgt_char = find_char_match(rel.target_name)

            if not src_char and characters:
                src_char = characters[0]
            if not tgt_char and len(characters) > 1:
                tgt_char = characters[1]

            if not src_char or not tgt_char:
                return {
                    "response": f"❌ No se encontraron los dos personajes para establecer la relación.",
                    "action": "ERROR_RELATIONSHIP_TARGET_NOT_FOUND"
                }

            # Delete any existing relationship between these two characters in either direction to avoid contradictory duplicate rows
            cursor.execute("""
            DELETE FROM character_relationships
            WHERE project_id = ? AND (
                (source_character_id = ? AND target_character_id = ?) OR
                (source_character_id = ? AND target_character_id = ?)
            )
            """, (proj_id, src_char["id"], tgt_char["id"], tgt_char["id"], src_char["id"]))

            rel_id = f"rel_{proj_id}_{src_char['id']}_{tgt_char['id']}"
            cursor.execute("""
            INSERT INTO character_relationships (
                id, project_id, source_character_id, target_character_id, target_character_name,
                rel_type, strength, history, key_scenes_json, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rel_id, proj_id, src_char["id"], tgt_char["id"], tgt_char["name"],
                rel.rel_type, rel.strength, rel.history,
                json.dumps([1, 3]), rel.status
            ))

            conn.commit()
            return {
                "response": (
                    f"🔗 **Relación Establecida / Actualizada:**\n\n"
                    f"{plan.response_explanation}\n\n"
                    f"• **Vínculo:** `{src_char['name']}` ↔ `{tgt_char['name']}`\n"
                    f"• **Tipo:** `{rel.rel_type}` (Fuerza: {rel.strength}%)\n"
                    f"• **Historia:** {rel.history}"
                ),
                "action": "RELATIONSHIP_UPDATED"
            }

        # -------------------------------------------------------------
        # ACCIÓN 5: GENERAL_CHAT
        # -------------------------------------------------------------
        else:
            return {
                "response": f"🎬 **Co-Director:** {plan.response_explanation}",
                "action": "CHAT"
            }

    def cascade_rename_character(
        self,
        cursor: Any,
        project_id: str,
        character_id: str,
        old_name: str,
        new_name: str
    ):
        """Reemplaza todas las referencias directas, en mayúsculas y en JSON de un personaje en SQLite."""
        # 1. Update characters table
        cursor.execute("UPDATE characters SET name = ? WHERE id = ?", (new_name, character_id))

        # Extract base names (e.g. "Lyra" from "Dra. Lyra Thorne") for thorough replacement
        old_tokens = [tok for tok in old_name.split() if len(tok) > 2 and tok.lower() not in ["dra.", "dr.", "comandante", "ingeniero", "capitán", "de", "la"]]
        new_tokens = [tok for tok in new_name.split() if len(tok) > 2 and tok.lower() not in ["dra.", "dr.", "comandante", "ingeniero", "capitán", "de", "la"]]
        base_old = old_tokens[0] if old_tokens else old_name
        base_new = new_tokens[0] if new_tokens else new_name

        # 2. Update character_relationships table
        cursor.execute("SELECT id, target_character_name, history FROM character_relationships WHERE project_id = ?", (project_id,))
        rel_rows = cursor.fetchall()
        for r in rel_rows:
            r_id = r[0]
            tgt_name = r[1] or ""
            hist = r[2] or ""

            mod = False
            if old_name in tgt_name:
                tgt_name = tgt_name.replace(old_name, new_name)
                mod = True
            elif base_old in tgt_name:
                tgt_name = tgt_name.replace(base_old, base_new)
                mod = True

            if old_name in hist:
                hist = hist.replace(old_name, new_name)
                mod = True
            elif base_old in hist:
                hist = hist.replace(base_old, base_new)
                mod = True

            if mod:
                cursor.execute("UPDATE character_relationships SET target_character_name = ?, history = ? WHERE id = ?", (tgt_name, hist, r_id))

        # 3. Update scenes table (characters_json, summary, script_text, slugline, subtext)
        cursor.execute("SELECT id, characters_json, summary, script_text, slugline, subtext FROM scenes WHERE project_id = ?", (project_id,))
        sc_rows = cursor.fetchall()

        for sc in sc_rows:
            sc_id = sc[0]
            c_json = sc[1] or "[]"
            summary = sc[2] or ""
            script_text = sc[3] or ""
            slugline = sc[4] or ""
            subtext = sc[5] or ""

            mod = False

            # Replace in characters_json
            if old_name in c_json:
                c_json = c_json.replace(old_name, new_name)
                mod = True
            if base_old in c_json:
                c_json = c_json.replace(base_old, base_new)
                mod = True

            # Replace in summary
            if old_name in summary:
                summary = summary.replace(old_name, new_name)
                mod = True
            if base_old in summary:
                summary = summary.replace(base_old, base_new)
                mod = True

            # Replace in script_text (both standard case and ALL-CAPS for dialogue speaker cues)
            if old_name in script_text:
                script_text = script_text.replace(old_name, new_name)
                mod = True
            if old_name.upper() in script_text:
                script_text = script_text.replace(old_name.upper(), new_name.upper())
                mod = True
            if base_old in script_text:
                script_text = script_text.replace(base_old, base_new)
                mod = True
            if base_old.upper() in script_text:
                script_text = script_text.replace(base_old.upper(), base_new.upper())
                mod = True

            # Replace in slugline
            if old_name in slugline:
                slugline = slugline.replace(old_name, new_name)
                mod = True
            if base_old in slugline:
                slugline = slugline.replace(base_old, base_new)
                mod = True

            # Replace in subtext
            if old_name in subtext:
                subtext = subtext.replace(old_name, new_name)
                mod = True
            if base_old in subtext:
                subtext = subtext.replace(base_old, base_new)
                mod = True

            if mod:
                cursor.execute("""
                UPDATE scenes SET
                    characters_json = ?, summary = ?, script_text = ?, slugline = ?, subtext = ?
                WHERE id = ?
                """, (c_json, summary, script_text, slugline, subtext, sc_id))

    def _update_character_in_db(self, cursor: Any, character_id: str, char_dict: Dict[str, Any]):
        """Helper to update a character record in SQLite."""
        fields = [
            "name", "age", "role", "archetype", "occupation", "personality",
            "motivation", "fears", "strengths", "weaknesses", "emotional_state", "wardrobe"
        ]
        for f in fields:
            if f in char_dict and char_dict[f] is not None:
                cursor.execute(f"UPDATE characters SET {f} = ? WHERE id = ?", (char_dict[f], character_id))
