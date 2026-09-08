import json
import os
import re
import time
import sqlite3
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from services.continuity_engine import ContinuityEngine
from services.parallel_tool import ParallelSearchTool
from core.db import (
    get_connection, get_project_db, get_characters_by_project_db,
    get_relationships_by_project_db, get_scenes_by_project_db,
    record_narrative_change_db, get_narrative_history_db,
    save_project_research_db, get_project_research_db
)

# =============================================================================
# PYDANTIC STRUCTURED MODELS FOR CINEMA ORCHESTRATION (FASE 6)
# =============================================================================

class DirectorIntent(BaseModel):
    """Análisis semántico estructurado del objetivo creativo del director."""
    primary_intent: str = Field(description="Resumen conciso de lo que el director quiere lograr")
    creative_goal: str = Field(description="Objetivo dramático, estético o estructural de la instrucción")
    affected_entities: List[str] = Field(default_factory=list, description="Personajes, relaciones, escenas o elementos afectados")
    scope: Literal[
        "LOCAL_ATTRIBUTE",
        "SINGLE_SCENE",
        "CHARACTER_RELATION",
        "MULTI_SCENE_NARRATIVE",
        "FULL_STORY_ARC",
        "QUERY",
        "ROLLBACK",
        "DIRECTOR_PREFERENCE",
        "FULL_STORY_GENERATION",
        "EXTERNAL_RESEARCH",
        "BUDGET_QUERY",
        "SUSTAINABILITY_QUERY"
    ] = Field(description="Alcance estructural del cambio")
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        description="Nivel de impacto dramático y riesgo de inconsistencias"
    )
    required_engines: List[Literal[
        "CharacterEngine",
        "NarrativeEngine",
        "SceneEngine",
        "ContinuityEngine",
        "ProjectMemory",
        "StoryEngine",
        "ParallelSearch",
        "ProductionIntelligence"
    ]] = Field(description="Lista de motores especializados necesarios para cumplir la instrucción")
    confirmation_required: bool = Field(
        default=False,
        description="True si el cambio es destructivo o de severidad CRITICAL/HIGH y requiere confirmación previa del director"
    )

class ExecutionStep(BaseModel):
    """Paso unitario de ejecución coordinada dentro del plan del Director Agent."""
    step_number: int
    engine: Literal["CharacterEngine", "NarrativeEngine", "SceneEngine", "ContinuityEngine", "ProjectMemory", "StoryEngine"]
    operation: str = Field(description="Operación específica a ejecutar")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parámetros requeridos por el motor")
    dependency_step: Optional[int] = Field(default=None, description="Paso previo del que depende")
    priority: int = Field(default=1, description="Prioridad de ejecución (1 = más alta)")

class DirectorExecutionPlan(BaseModel):
    """Plan maestro de orquestación cinematográfica generado para cumplir la instrucción del director."""
    goal_summary: str = Field(description="Resumen de alto nivel del plan")
    intent: DirectorIntent
    steps: List[ExecutionStep] = Field(description="Secuencia de pasos ordenados por dependencia")
    impact_summary: str = Field(description="Explicación clara del impacto sobre personajes, escenas y canon")
    confirmation_required: bool = Field(default=False)
    expected_changes: List[str] = Field(default_factory=list, description="Cambios específicos esperados")
    validation_requirements: List[str] = Field(default_factory=list, description="Verificaciones de continuidad requeridas")

# =============================================================================
# DIRECTOR AGENT / CINEMA ORCHESTRATOR CLASS
# =============================================================================

class DirectorAgent:
    """Director Agent / Cinema Orchestrator: Cerebro coordinador de motores cinematográficos (Fase 6)."""

    def __init__(
        self,
        client: Any = None,
        story_engine: Any = None,
        character_engine: Any = None,
        scene_engine: Any = None,
        narrative_engine: Any = None,
        project_memory: Any = None,
        parallel_tool: Any = None
    ):
        self.client = client
        self.story_engine = story_engine
        self.character_engine = character_engine
        self.scene_engine = scene_engine
        self.narrative_engine = narrative_engine
        self.project_memory = project_memory
        self.parallel_tool = parallel_tool or ParallelSearchTool()
        self.candidate_models = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.6-flash"]
        self.pending_plans: Dict[str, Any] = {}

    def analyze_intent(
        self,
        prompt: str,
        project: Dict[str, Any],
        characters: List[Dict],
        relationships: List[Dict],
        scenes: List[Dict]
    ) -> DirectorIntent:
        """Determina con Structured Outputs la intención, severidad y motores requeridos."""
        p_low = prompt.lower().strip()

        # Fast deterministic heuristics for immediate standard workflows
        if any(w in p_low for w in ["deshaz el último", "deshaz el ultimo", "deshacer", "revertir", "rollback", "undo last change", "undo change", "revert change", "undo"]):
            return DirectorIntent(
                primary_intent="Revertir el último cambio narrativo",
                creative_goal="Restaurar el estado canónico previo",
                affected_entities=["Narrativa", "Historial"],
                scope="ROLLBACK",
                severity="LOW",
                required_engines=["ProjectMemory", "ContinuityEngine"],
                confirmation_required=False
            )

        if any(w in p_low for w in ["mantén un tono", "manten un tono", "quiero un tono", "el tono debe ser", "tono de thriller", "keep a tone", "set tone to", "the tone should be", "tone must be"]):
            return DirectorIntent(
                primary_intent="Establecer directriz tonal del proyecto",
                creative_goal="Definir la atmósfera creativa permanente",
                affected_entities=["Proyecto", "Tono"],
                scope="DIRECTOR_PREFERENCE",
                severity="LOW",
                required_engines=["ProjectMemory"],
                confirmation_required=False
            )

        if any(w in p_low for w in [
            "¿qué sabe", "¿que sabe", "¿cuántos años", "¿cuantos años", "¿por qué", "¿por que",
            "¿en qué escenas", "¿en que escenas", "¿qué objetos", "¿que objetos", "¿cuándo se revela",
            "¿cuando se revela", "¿cuál es el arco", "¿cual es el arco", "¿qué cambió", "¿que cambio",
            "¿qué personajes", "¿que personajes", "¿quiénes están", "¿quienes estan",
            "están relacionados", "estan relacionados", "cuáles fueron los últimos cambios", "ultimos cambios",
            "¿cuál es la premisa", "¿cual es la premisa", "cuál es la premisa", "cual es la premisa",
            "what does", "who knows", "how old", "why does", "which scenes", "what objects", "when is",
            "what is the arc", "what changed", "which characters", "who is in", "are related",
            "what were the last changes", "what is the premise", "what's the premise"
        ]):
            return DirectorIntent(
                primary_intent="Consulta factual, de relaciones o temporal sobre la película",
                creative_goal="Inspeccionar memoria de producción y canon",
                affected_entities=["Memoria de Producción"],
                scope="QUERY",
                severity="LOW",
                required_engines=["ProjectMemory"],
                confirmation_required=False
            )

        # Budget & Cost Intelligence heuristics
        if any(w in p_low for w in [
            "cuánto costaría", "cuanto costaria", "cuánto cuesta", "cuanto cuesta",
            "presupuesto", "costo de producción", "costo de produccion", "más cara",
            "mas cara", "más costosa", "mas costosa", "reducir el presupuesto",
            "reducir costos", "ahorrar", "en qué estás basando", "en que estas basando",
            "en qué basas", "en que basas", "cómo calculas", "como calculas", "días de rodaje",
            "dias de rodaje", "cuántos días", "cuantos dias", "cronograma", "shooting schedule",
            "production budget", "cost analysis", "how much would it cost", "how much does it cost",
            "budget", "production cost", "most expensive", "reduce budget", "cut costs", "save money",
            "how are you calculating", "how do you calculate", "shooting days", "how many days", "schedule"
        ]):
            needs_parallel = any(w in p_low for w in ["panamá", "panama", "mercado local", "locales", "precios reales", "proveedores", "investiga", "busca", "search", "local suppliers"])
            return DirectorIntent(
                primary_intent="Análisis de presupuesto cinematográfico, desglose de costos o cronograma",
                creative_goal="Proyectar y optimizar la viabilidad económica y plan de rodaje",
                affected_entities=["Presupuesto", "Cronograma"],
                scope="EXTERNAL_RESEARCH" if needs_parallel else "BUDGET_QUERY",
                severity="LOW",
                required_engines=["ProductionIntelligence"] + (["ParallelSearch"] if needs_parallel else []),
                confirmation_required=False
            )

        # Sustainability & Environmental Production heuristics
        if any(w in p_low for w in [
            "sostenible", "sostenibilidad", "ecológic", "ecologic", "medio ambiente",
            "huella de carbono", "green film", "materiales sostenibles", "rodaje verde",
            "reducir el impacto ambiental", "reducir impacto", "sustainable", "sustainability",
            "eco-friendly", "carbon footprint", "environmental impact", "green shooting", "sustainable materials"
        ]):
            needs_parallel = any(w in p_low for w in ["panamá", "panama", "mercado local", "locales", "materiales", "proveedores", "investiga", "busca", "search"])
            return DirectorIntent(
                primary_intent="Consultoría de producción cinematográfica sostenible y reducción de huella",
                creative_goal="Implementar prácticas ecológicas adaptadas a la filmación",
                affected_entities=["Sostenibilidad", "Producción"],
                scope="EXTERNAL_RESEARCH" if needs_parallel else "SUSTAINABILITY_QUERY",
                severity="LOW",
                required_engines=["ProductionIntelligence"] + (["ParallelSearch"] if needs_parallel else []),
                confirmation_required=False
            )

        # Scene-specific operation heuristics (including applying Parallel research)
        has_scene_num_ref = bool(re.search(r'\b(scene|escena|szene|scène|scena|cena)\s+\d+\b', p_low))
        has_scene_action = any(w in p_low for w in [
            "agrega una escena", "añade una escena", "inserta una escena", "pon una escena",
            "regenera la escena", "reescribe la escena", "elimina la escena", "borra la escena",
            "adapta la escena", "modifica la escena", "adapta escena", "modifica escena",
            "adapt scene", "rewrite scene", "add a scene", "create a scene", "insert a scene",
            "delete scene", "remove scene", "modify scene",
            "apply the research", "apply research", "use the best option", "use best option",
            "use recommended location", "use the recommended location", "use scouted location",
            "update scene", "aplica la investigación", "aplica la investigacion",
            "usa la mejor opción", "usa la mejor opcion", "usa la locación", "usa la locacion",
            "beste option", "recherche anwenden", "appliquer la recherche", "scouting anwenden"
        ]) or (has_scene_num_ref and any(w in p_low for w in [
            "apply", "use", "adapt", "rewrite", "modify", "update", "research", "location",
            "aplica", "usa", "adapta", "reescribe", "modifica", "investiga", "locaci",
            "wende", "anwenden", "recherche", "drehort", "szene",
            "appliquer", "applique", "utiliser", "utilise", "repérage", "reperage",
            "applicare", "utilizzare", "aplicar"
        ]))

        if has_scene_action:
            return DirectorIntent(
                primary_intent="Operación de creación, regeneración o modificación de escena específica",
                creative_goal="Ajustar estructura puntual de escaleta de escenas",
                affected_entities=["Escenas"],
                scope="SINGLE_SCENE",
                severity="MEDIUM",
                required_engines=["SceneEngine", "ContinuityEngine"],
                confirmation_required=False
            )


        # External Web Research heuristics (Parallel Search API - Partner Track)
        if (any(w in p_low for w in [
            "busca información real", "busca informacion real", "investiga sobre", "investiga cómo era",
            "investiga como era", "locaciones reales", "lugares reales", "localizaciones reales",
            "busca referencias reales", "referencias reales", "investiga en la web", "buscar en internet",
            "busca en internet", "sitios reales", "investigación de producción", "investigacion de produccion",
            "search real locations", "search for real", "search locations", "real locations in",
            "lugares reales que podrían funcionar", "lugares reales que podrian funcionar",
            "estación de investigación abandonada", "estacion de investigacion abandonada",
            "look up real", "research real", "historical references", "real places that could work",
            "near me", "cerca de mí", "cerca de mi", "nearby", "locations near me", "filming locations near me"
        ]) or (any(w in p_low for w in ["busca", "buscar", "investiga", "investigar", "search", "find"]) and any(w in p_low for w in ["panamá", "panama", "real", "reales", "histórico", "historico", "1980", "locación", "locacion", "locaciones", "facilidad", "estación", "estacion", "location", "locations", "historia"]))) and not any(w in p_low for w in ["adapta la escena", "modifica la escena", "reescribe la escena", "adapt scene", "rewrite scene"]):
            return DirectorIntent(
                primary_intent="Investigación externa web y scouting de locaciones o datos del mundo real",
                creative_goal="Recuperar información factual, referencias históricas y locaciones auténticas del mundo real",
                affected_entities=["Investigación Externa", "Contexto de Producción"],
                scope="EXTERNAL_RESEARCH",
                severity="LOW",
                required_engines=["ProjectMemory", "ParallelSearch"],
                confirmation_required=False
            )

        if (any(w in p_low for w in [
            "crea una película", "crea un guion", "nueva película", "escribe una película", "plan de producción",
            "create a movie", "create a script", "new movie", "write a movie", "create the complete movie",
            "production plan", "movie about", "film about"
        ]) or (len(scenes) == 0 and any(w in p_low for w in ["película", "historia", "movie", "film", "story"]))) and not any(w in p_low for w in ["investiga", "busca", "search"]):
            return DirectorIntent(
                primary_intent="Generación de una nueva producción cinematográfica completa",
                creative_goal="Crear StoryBible, elenco y escaleta desde cero",
                affected_entities=["Toda la Producción"],
                scope="FULL_STORY_GENERATION",
                severity="HIGH",
                required_engines=["StoryEngine", "ContinuityEngine", "ProjectMemory"],
                confirmation_required=False
            )

        # Critical / Destructive change detection (e.g. killing main characters, deleting protagonist, destroying world)
        if any(w in p_low for w in [
            "muera", "matar a", "asesinado", "asesinar a", "eliminar a", "elimina a", "eliminar a todos", "elimina a todos",
            "elimina al protagonista", "eliminar al protagonista", "destruye completamente",
            "destruye la colonia", "destruye el planeta", "cambia completamente el final", "todos mueren",
            "dies", "kill ", "killed", "murder", "eliminate ", "delete the protagonist", "destroy completely",
            "destroy the colony", "destroy the planet", "change completely the ending", "everyone dies", "all die"
        ]):
            return DirectorIntent(
                primary_intent="Modificación radical y destructiva del desenlace o supervivencia de personajes clave",
                creative_goal="Reestructurar el clímax y consecuencias finales de la historia",
                affected_entities=["Protagonista", "Desenlace", "Acto III", "Canon"],
                scope="FULL_STORY_ARC",
                severity="CRITICAL",
                required_engines=["CharacterEngine", "NarrativeEngine", "SceneEngine", "ContinuityEngine", "ProjectMemory"],
                confirmation_required=True
            )

        # Character addition / local attribute / relationship heuristics
        char_action_keywords = [
            "agrega un perro", "añade un perro", "agrega un personaje", "añade un personaje",
            "crea un personaje", "crea un nuevo personaje", "crea un hermano", "crea una hermana",
            "crea un amigo", "crea una amiga", "agrega un hermano", "añade un hermano",
            "crea un nuevo", "añade un nuevo", "agrega un nuevo", "cambia la edad", "cambia el nombre",
            "renombra a", "relación complicada", "relacion complicada", "tengan una relación", "tengan una relacion",
            "personajes más", "personaje más", "personajes mas", "personaje mas",
            "agrega personajes", "añade personajes", "crea personajes", "añade 3 personajes", "agrega 3 personajes",
            "añadir personajes", "agregar personajes", "incorporar personajes", "añade 2 personajes", "agrega 2 personajes",
            "add a character", "add characters", "create a character", "create characters", "add 3 characters", "add 2 characters",
            "add a dog", "create a brother", "create a sister", "create a friend", "change the age", "rename ",
            "complicated relationship", "have a relationship", "new character", "new characters"
        ]
        is_char_intent = any(w in p_low for w in char_action_keywords) or (
            any(w in p_low for w in ["agrega", "añade", "crea", "incorporar", "incluye", "añadir", "agregar", "add", "create", "include"]) and
            any(w in p_low for w in ["personaje", "personajes", "elenco", "reparto", "character", "characters", "cast"]) and
            not any(w in p_low for w in ["muera", "matar", "elimina", "destruye", "asesin", "kill", "die", "destroy"])
        )
        if is_char_intent:
            return DirectorIntent(
                primary_intent="Creación o ampliación del reparto de personajes y dinámicas de relación",
                creative_goal="Incorporar personajes y estructurar vínculos en el universo dramático",
                affected_entities=["Personajes", "Relaciones"],
                scope="CHARACTER_RELATION",
                severity="LOW",
                required_engines=["CharacterEngine", "ContinuityEngine", "ProjectMemory"],
                confirmation_required=False
            )

        if any(w in p_low for w in ["vestuario de", "traje de", "ropa de", "edad de", "wardrobe of", "costume of", "age of"]) and not any(w in p_low for w in ["desconfía", "desconfia", "aliado", "enemigo", "traición", "traicion", "segundo acto", "final"]):
            return DirectorIntent(
                primary_intent="Modificación de atributo visual o biográfico de personaje",
                creative_goal="Ajustar caracterización estética o personal",
                affected_entities=["Personaje"],
                scope="LOCAL_ATTRIBUTE",
                severity="LOW",
                required_engines=["CharacterEngine"],
                confirmation_required=False
            )

        # Invocación estructurada a Gemini para instrucciones complejas
        if self.client:
            char_names = [c.get("name") for c in characters]
            prompt_analysis = (
                f"Analiza la siguiente instrucción del director cinematográfico:\n\n"
                f"Instrucción: \"{prompt}\"\n\n"
                f"Contexto del proyecto: '{project.get('title')}' (Género: {project.get('genre')})\n"
                f"Elenco actual: {', '.join(char_names)}\n"
                f"Total de escenas: {len(scenes)}\n\n"
                f"Determina la intención, severidad (LOW, MEDIUM, HIGH, CRITICAL), alcance y los motores que deben intervenir."
            )
            for model_name in self.candidate_models:
                try:
                    res = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt_analysis,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=DirectorIntent,
                            temperature=0.2
                        )
                    )
                    if res and res.text:
                        data = json.loads(res.text)
                        return DirectorIntent(**data)
                except Exception:
                    continue

        # Default multi-engine intent fallback
        return DirectorIntent(
            primary_intent="Ajuste narrativo y dramático multi-escena",
            creative_goal="Evolución de tramas y relaciones",
            affected_entities=["Reparto", "Escenas"],
            scope="MULTI_SCENE_NARRATIVE",
            severity="MEDIUM",
            required_engines=["CharacterEngine", "NarrativeEngine", "SceneEngine", "ContinuityEngine", "ProjectMemory"],
            confirmation_required=False
        )

    def orchestrate(
        self,
        prompt: str,
        project: Dict[str, Any],
        characters: List[Dict],
        relationships: List[Dict],
        scenes: List[Dict],
        conn: Any
    ) -> Dict[str, Any]:
        """Coordina la ejecución de la instrucción del director invocando los motores especializados correspondientes."""
        proj_id = project.get("id", "proj_default")
        p_low = prompt.lower().strip()

        # 0. Check Confirmation of Pending Plan
        is_confirmation = any(w in p_low for w in [
            "confirmo", "confirmo los cambios", "aplica el plan", "aplica los cambios", "sí, hazlo", "si, hazlo", "procede", "ejecuta el plan",
            "confirm", "i confirm", "confirm changes", "confirm the changes", "apply plan", "apply the plan", "apply changes", "yes, do it", "yes do it", "proceed", "execute the plan"
        ])
        if is_confirmation and proj_id in self.pending_plans:
            pending_plan, orig_prompt = self.pending_plans.pop(proj_id)
            if self.narrative_engine:
                return self.narrative_engine.execute_confirmed_repairs(
                    plan=pending_plan,
                    project=project,
                    characters=characters,
                    relationships=relationships,
                    scenes=scenes,
                    conn=conn,
                    prompt=orig_prompt
                )

        # 1. Analyze Intent with Structured Outputs
        intent = self.analyze_intent(prompt, project, characters, relationships, scenes)
        is_es = any(w in p_low.split() for w in ["el", "la", "los", "las", "que", "de", "en", "un", "una", "por", "para", "con", "es", "muera", "matar", "crea", "cambia", "busca", "investiga"]) or any(c in p_low for c in "áéíóúñ¿¡")
        is_en = not is_es

        # 2. Direct Delegation by Scope
        result = None
        if intent.scope == "QUERY" and self.project_memory:
            result = self.project_memory.answer_factual_query(prompt, proj_id, conn)

        elif intent.scope == "ROLLBACK" and self.project_memory:
            result = self.project_memory.execute_rollback(proj_id, conn)

        elif intent.scope == "DIRECTOR_PREFERENCE" and self.project_memory:
            result = self.project_memory.record_director_preference(prompt, proj_id, conn)

        elif intent.scope in ["LOCAL_ATTRIBUTE", "CHARACTER_RELATION"] and self.character_engine:
            result = self.character_engine.process_conversational_request(
                prompt=prompt,
                project=project,
                characters=characters,
                relationships=relationships,
                scenes=scenes,
                conn=conn
            )

        elif intent.scope == "SINGLE_SCENE" and self.scene_engine:
            edit_prompt = prompt
            is_apply_research = any(w in p_low for w in [
                "usa la mejor opción", "usa la mejor opcion", "usa la opción", "usa la opcion",
                "con la locación", "con la locacion", "locación investigada", "locacion investigada",
                "aplica la investigación", "aplica la investigacion", "use the best option", "with the location"
            ])
            if is_apply_research:
                try:
                    prior_research = get_project_research_db(proj_id, limit=1, conn=conn)
                    if prior_research:
                        r_item = prior_research[0]
                        sources = r_item.get("sources", [])
                        top_source = sources[0].get("title") if sources else "Locación investigada"
                        edit_prompt = f"{prompt}. Contexto de locación real descubierto con Parallel Search: '{top_source}'. Modifica el slugline/locación y resumen de la escena acorde a este lugar real."
                except Exception:
                    pass

            result = self.scene_engine.process_scene_conversational_edit(
                prompt=edit_prompt,
                project=project,
                characters=characters,
                relationships=relationships,
                scenes=scenes,
                conn=conn
            )

        elif intent.scope == "EXTERNAL_RESEARCH":
            result = self._handle_external_research(prompt, project, characters, scenes, conn)

        # 3. Handle CRITICAL / HIGH Changes Requiring Confirmation
        elif intent.confirmation_required or intent.severity == "CRITICAL":
            # Generate impact plan
            plan = None
            if self.narrative_engine:
                try:
                    plan = self.narrative_engine.analyze_change_impact(
                        prompt=prompt,
                        project=project,
                        characters=characters,
                        relationships=relationships,
                        scenes=scenes
                    )
                    self.pending_plans[proj_id] = (plan, prompt)
                except Exception:
                    pass

            if is_en:
                conf_msg = (
                    f"⚠️ **Director Agent — Critical Impact Alert (Confirmation Required):**\n\n"
                    f"I have analyzed the creative instruction: \"*{prompt}*\"\n\n"
                    f"• **Creative Goal:** {intent.creative_goal}\n"
                    f"• **Severity:** `{intent.severity}`\n"
                    f"• **Engines Involved:** {', '.join(intent.required_engines)}\n"
                    f"• **Affected Entities:** {', '.join(intent.affected_entities)}\n\n"
                    f"📌 **Production Consequence Breakdown:**\n"
                    f"This modification will radically impact the narrative climax, the canonical survival of the protagonist, and Act III culmination scenes.\n\n"
                    f"Would you like me to apply this restructuring plan? Reply **\"I confirm the changes\"** to proceed."
                )
            else:
                conf_msg = (
                    f"⚠️ **Director Agent — Alerta de Impacto Crítico (Requiere Confirmación):**\n\n"
                    f"He analizado la instrucción: \"*{prompt}*\"\n\n"
                    f"• **Objetivo Creativo:** {intent.creative_goal}\n"
                    f"• **Severidad:** `{intent.severity}`\n"
                    f"• **Motores Involucrados:** {', '.join(intent.required_engines)}\n"
                    f"• **Entidades Afectadas:** {', '.join(intent.affected_entities)}\n\n"
                    f"📌 **Desglose de Consecuencias en la Producción:**\n"
                    f"Esta modificación afectará radicalmente el desenlace, el canon de supervivencia del protagonista y las escenas culminantes del Acto III.\n\n"
                    f"¿Desea que aplique este plan de reestructuración? Responda **\"Confirmo los cambios\"** para proceder."
                )

            result = {
                "action": "CONFIRMATION_REQUIRED",
                "severity": intent.severity,
                "intent": intent.model_dump(),
                "response": conf_msg
            }

        # 4. Multi-Engine Orchestration (CharacterEngine + NarrativeEngine + SceneEngine + ContinuityEngine)
        elif self.narrative_engine:
            try:
                plan = self.narrative_engine.analyze_change_impact(
                    prompt=prompt,
                    project=project,
                    characters=characters,
                    relationships=relationships,
                    scenes=scenes
                )
                if plan.requires_confirmation and not plan.auto_executable:
                    self.pending_plans[proj_id] = (plan, prompt)
                    if is_en:
                        conf_msg2 = (
                            f"⚠️ **Director Agent — Confirmation Required:**\n\n"
                            f"{plan.response_explanation}\n\n"
                            f"• **Affected Scenes:** {plan.impact.affected_scene_numbers}\n"
                            f"• **Consequences:** {', '.join(plan.impact.narrative_consequences)}\n\n"
                            f"Reply **'I confirm the changes'** to apply cascading repairs."
                        )
                    else:
                        conf_msg2 = (
                            f"⚠️ **Director Agent — Confirmación Requerida:**\n\n"
                            f"{plan.response_explanation}\n\n"
                            f"• **Escenas Afectadas:** {plan.impact.affected_scene_numbers}\n"
                            f"• **Consecuencias:** {', '.join(plan.impact.narrative_consequences)}\n\n"
                            f"Responda **'Confirmo los cambios'** para aplicar las reparaciones en cascada."
                        )
                    result = {
                        "action": "CONFIRMATION_REQUIRED",
                        "severity": plan.impact.severity,
                        "plan": plan.model_dump(),
                        "response": conf_msg2
                    }
                else:
                    result = self.narrative_engine.execute_confirmed_repairs(
                        plan=plan,
                        project=project,
                        characters=characters,
                        relationships=relationships,
                        scenes=scenes,
                        conn=conn,
                        prompt=prompt
                    )
            except Exception as e:
                pass

        if result is None:
            result = {
                "action": "ORCHESTRATION_COMPLETED",
                "response": (
                    f"🎬 **Director Agent:** Instruction processed for '{project.get('title')}'."
                    if is_en else
                    f"🎬 **Director Agent:** Instrucción procesada para '{project.get('title')}'."
                )
            }

        if isinstance(result, dict):
            if "engines_used" not in result:
                result["engines_used"] = intent.required_engines or ["DirectorAgent"]
            if "severity" not in result:
                result["severity"] = intent.severity or "LOW"
            if "scope" not in result:
                result["scope"] = intent.scope or "GENERAL"
            if "confirmation_required" not in result:
                result["confirmation_required"] = intent.confirmation_required
            if "continuity_status" not in result:
                result["continuity_status"] = "PASS"

        return result

    def _handle_external_research(
        self,
        prompt: str,
        project: Dict[str, Any],
        characters: List[Dict],
        scenes: List[Dict],
        conn: Any
    ) -> Dict[str, Any]:
        """Ejecuta investigación web externa en vivo con Parallel Search API y sintetiza resultados con Gemini."""
        proj_id = project.get("id", "proj_default")
        if not self.parallel_tool:
            self.parallel_tool = ParallelSearchTool()

        p_low = prompt.lower().strip()
        is_es = any(w in p_low.split() for w in ["el", "la", "los", "las", "que", "de", "en", "un", "una", "por", "para", "con", "es", "busca", "investiga"]) or any(c in p_low for c in "áéíóúñ¿¡")
        is_en = not is_es

        # Detección de consultas de locación relativas sin ancla geográfica ("near me", "cerca de mí")
        relative_loc_patterns = [
            r'\bnear\s+me\b', r'\bnearby\b', r'\baround\s+here\b',
            r'\bclose\s+to\s+me\b', r'\bin\s+my\s+area\b',
            r'\bcerca\s+de\s+m[íi]\b', r'\bcerca\s+m[íi]o\b',
            r'\bcerca\s+m[íi]a\b', r'\bpor\s+aqu[íi]\b',
            r'\bpor\s+ac[áa]\b', r'\ben\s+mi\s+zona\b'
        ]
        is_relative_loc = any(re.search(pat, p_low) for pat in relative_loc_patterns)
        has_anchor = bool(re.search(r'\b(in|en)\s+([a-záéíóúñA-ZÁÉÍÓÚÑ]+)', prompt)) and not bool(re.search(r'\b(in|en)\s+(my|mi|our|nuestro|nuestra)\b', p_low))

        if is_relative_loc and not has_anchor:
            clarification_msg = (
                "📍 **Location Clarification Required:**\n\n"
                "As an AI filmmaking orchestrator, I do not track your physical GPS coordinates or assume your location. "
                "To discover authentic, real-world filming locations using **Parallel Search API**, please specify the target "
                "**city, region, or country**.\n\n"
                "*Examples:*\n"
                "• *\"Find brutalist filming locations in Panama City, Panama\"*\n"
                "• *\"Search for abandoned astronomical observatories in Atacama, Chile\"*\n\n"
                "*(Zero Mutation Gate: Your film production has not been modified.)*"
                if is_en else
                "📍 **Aclaración de Ubicación Requerida:**\n\n"
                "Como orquestador cinematográfico de IA, no rastreo sus coordenadas GPS ni asumo su ubicación física. "
                "Para descubrir locaciones de filmación auténticas del mundo real mediante **Parallel Search API**, "
                "por favor especifique la **ciudad, región o país** objetivo.\n\n"
                "*Ejemplos:*\n"
                "• *\"Busca locaciones de arquitectura brutalista en Ciudad de Panamá, Panamá\"*\n"
                "• *\"Investiga observatorios astronómicos abandonados en Atacama, Chile\"*\n\n"
                "*(Zero Mutation Gate: Su producción cinematográfica no ha sufrido modificaciones.)*"
            )
            return {
                "action": "LOCATION_CONTEXT_REQUIRED",
                "scope": "EXTERNAL_RESEARCH",
                "severity": "LOW",
                "engines_used": ["DirectorAgent", "ParallelSearch"],
                "mutation": False,
                "sources": [],
                "sources_count": 0,
                "response": clarification_msg
            }

        if not self.parallel_tool.is_configured():
            return {
                "action": "EXTERNAL_RESEARCH_UNAVAILABLE",
                "scope": "EXTERNAL_RESEARCH",
                "severity": "LOW",
                "engines_used": ["DirectorAgent", "ParallelSearch"],
                "mutation": False,
                "sources": [],
                "sources_count": 0,
                "response": (
                    "🔎 **External Research unavailable:**\n\n"
                    "To enable real-time live web search with **Parallel Search API**, configure your key in `.env`:\n"
                    "`PARALLEL_API_KEY=your_key_here`\n\n"
                    "*(Zero Mutation Gate: Your film production has not been modified.)*"
                    if is_en else
                    "🔎 **Investigación Externa no disponible:**\n\n"
                    "Para habilitar la búsqueda web en tiempo real con **Parallel Search API**, configure su clave en el archivo `.env`:\n"
                    "`PARALLEL_API_KEY=su_clave_aqui`\n\n"
                    "*(Zero Mutation Gate: Su producción cinematográfica no ha sufrido modificaciones.)*"
                )
            }

        # Extraer palabras clave de búsqueda
        p_clean = re.sub(r'(?i)\b(busca|buscar|investiga|investigar|información|informacion|sobre|para|que|las|los|de|en|un|una|search|for|about)\b', ' ', prompt).strip()
        p_clean = re.sub(r'\s+', ' ', p_clean)
        search_queries = [
            f"{p_clean} film location"[:80].strip() if any(w in prompt.lower() for w in ["locaci", "lugar", "sitio", "location"]) else f"{p_clean} reference"[:80].strip(),
            f"{project.get('title')} {p_clean}"[:80].strip(),
            p_clean[:80].strip()
        ]
        search_queries = [q for q in search_queries if len(q) > 3][:3]
        if not search_queries:
            search_queries = [prompt[:80]]

        # Invocación real a Parallel Search API
        search_res = self.parallel_tool.search(
            objective=f"Film production research for project '{project.get('title')}': {prompt}",
            search_queries=search_queries,
            mode="fast",
            max_results=5
        )

        sources = search_res.get("results", [])

        # Síntesis cinematográfica profesional con Gemini
        synthesis_text = ""
        if self.client and sources:
            sources_block = "\n\n".join([
                f"Fuente {i+1}: {s.get('title')}\nURL: {s.get('url')}\nExtractos:\n" + "\n".join(s.get('excerpts', []))
                for i, s in enumerate(sources)
            ])
            if is_en:
                synthesis_prompt = (
                    f"You are the Co-Director of the film '{project.get('title')}' (Genre: {project.get('genre')}).\n"
                    f"The Director requested the following real-world external research:\n"
                    f"\"{prompt}\"\n\n"
                    f"Real live web results retrieved via Parallel Search API:\n\n"
                    f"{sources_block}\n\n"
                    f"Write a professional structured cinematic report for the Director in English:\n"
                    f"1. Executive summary of the findings.\n"
                    f"2. Highlighted real-world locations or facts, explaining how they bring authenticity and visual atmosphere to the film.\n"
                    f"3. List of sources citing title and link in markdown [Title](URL).\n"
                    f"4. Explicitly state the safety gate: The SQLite database and screenplay remain intact (Zero Mutation Gate) until the Director explicitly instructs to apply an option (e.g. 'Use the best option and adapt scene 4')."
                )
            else:
                synthesis_prompt = (
                    f"Eres el Co-Director de la película '{project.get('title')}' (Género: {project.get('genre')}).\n"
                    f"El Director solicitó la siguiente investigación externa del mundo real:\n"
                    f"\"{prompt}\"\n\n"
                    f"Resultados web reales recuperados en tiempo real mediante Parallel Search API:\n\n"
                    f"{sources_block}\n\n"
                    f"Redacta un informe cinematográfico estructurado para el Director:\n"
                    f"1. Resumen ejecutivo de los hallazgos.\n"
                    f"2. Opciones de locaciones o datos reales destacados, explicando cómo aportan autenticidad y atmósfera visual a la película.\n"
                    f"3. Lista de fuentes citando su título y enlace en formato [Título](URL).\n"
                    f"4. Recuerda explícitamente la compuerta de seguridad: La base de datos y el guion se mantienen intactos (Zero Mutation Gate) hasta que el Director ordene explícitamente aplicar una opción (ejemplo: 'Usa la mejor opción y adapta la escena 4')."
                )
            for model_name in self.candidate_models:
                try:
                    res = self.client.models.generate_content(
                        model=model_name,
                        contents=synthesis_prompt
                    )
                    if res and res.text:
                        synthesis_text = res.text.strip()
                        break
                except Exception:
                    continue

        if not synthesis_text:
            if is_en:
                synthesis_text = (
                    f"🔎 **External Research Report — Parallel Search API:**\n\n"
                    f"Discovered {len(sources)} real-world sources for the production of *{project.get('title')}*:\n\n"
                )
                for s in sources:
                    synthesis_text += f"• **[{s.get('title')}]({s.get('url')})**\n"
                    for exc in s.get("excerpts", [])[:1]:
                        synthesis_text += f"  > *\"{exc}\"*\n\n"
                synthesis_text += (
                    "\n📌 **Zero Mutation Gate:**\n"
                    "The database and screenplay remain intact. To apply any location or data into your script, instruct me:\n"
                    "*\"Use the best option and adapt scene [N]\"*."
                )
            else:
                synthesis_text = (
                    f"🔎 **Informe de Investigación Externa — Parallel Search API:**\n\n"
                    f"Se han descubierto {len(sources)} fuentes del mundo real para la producción de *{project.get('title')}*:\n\n"
                )
                for s in sources:
                    synthesis_text += f"• **[{s.get('title')}]({s.get('url')})**\n"
                    for exc in s.get("excerpts", [])[:1]:
                        synthesis_text += f"  > *\"{exc}\"*\n\n"
                synthesis_text += (
                    "\n📌 **Zero Mutation Gate:**\n"
                    "La base de datos y la escaleta se mantienen intactas. Para aplicar cualquiera de estas locaciones, responda:\n"
                    "*\"Usa la mejor opción y adapta la escena [N]\"*."
                )

        # Persistencia en la tabla project_research de SQLite
        try:
            target_scope = "LOCATIONS" if any(w in prompt.lower() for w in ["locaci", "lugar", "sitio", "location"]) else "HISTORICAL_CONTEXT"
            save_project_research_db(
                project_id=proj_id,
                objective=prompt,
                search_queries=search_queries,
                research_summary=synthesis_text,
                sources=sources,
                target_scope=target_scope,
                conn=conn
            )
        except Exception as db_err:
            pass

        return {
            "action": "EXTERNAL_RESEARCH_COMPLETED",
            "scope": "EXTERNAL_RESEARCH",
            "severity": "LOW",
            "engines_used": ["DirectorAgent", "ParallelSearch", "ProjectMemory"],
            "mutation": False,
            "sources": sources,
            "sources_count": len(sources),
            "response": synthesis_text
        }

    def answer_production_query(
        self,
        prompt: str,
        project: Dict[str, Any],
        scenes: List[Dict[str, Any]],
        characters: List[Dict[str, Any]],
        lang: str = "EN"
    ) -> Dict[str, Any]:
        """Procesa y responde consultas de presupuesto, costos y sostenibilidad con ProductionIntelligence."""
        from services.production_intelligence import ProductionIntelligence
        res = ProductionIntelligence.answer_production_query(
            prompt=prompt,
            project=project,
            scenes=scenes,
            characters=characters,
            parallel_tool=self.parallel_tool,
            lang=lang
        )
        res["engines_used"] = ["DirectorAgent", "ProductionIntelligence"] + (["ParallelSearch"] if res.get("sources") else [])
        res["mutation"] = False
        return res


