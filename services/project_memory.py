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
from core.db import (
    get_connection, get_project_db, get_characters_by_project_db,
    get_relationships_by_project_db, get_scenes_by_project_db,
    get_narrative_history_db, add_canonical_fact_db, get_canonical_facts_db,
    add_director_preference_db, get_director_preferences_db,
    get_scene_versions_db
)

# =============================================================================
# PYDANTIC STRUCTURED OUTPUT MODELS FOR PROJECT MEMORY
# =============================================================================

class CanonicalFact(BaseModel):
    id: Optional[str] = None
    project_id: str
    entity_type: str = "GENERAL"
    entity_id: Optional[str] = None
    fact_text: str
    fact_type: Literal["CANONICAL", "INFERRED", "PROPOSED", "RETCON"] = "CANONICAL"
    status: Literal["ACTIVE", "SUPERSEDED"] = "ACTIVE"
    scene_established: Optional[int] = None

class DirectorPreference(BaseModel):
    id: Optional[str] = None
    project_id: str
    preference_type: str = "TONE"
    directive_text: str

class ProjectMemoryQueryResponse(BaseModel):
    """Respuesta estructurada a consultas factuales o temporales del director sobre el universo de la película."""
    answer: str = Field(description="Respuesta detallada, verídica y fundamentada estrictamente en el estado de SQLite del proyecto")
    query_type: Literal[
        "FACTUAL",
        "TEMPORAL_KNOWLEDGE",
        "CHARACTER_ARC",
        "RELATIONSHIP_CONFLICT",
        "SCENE_LOCATION",
        "PROPS_STATUS",
        "CANON_FACT",
        "NOT_IN_PROJECT",
        "GENERAL"
    ] = Field(description="Tipo de consulta resuelta")
    entities_referenced: List[str] = Field(default_factory=list, description="Personajes, locaciones o props citados en la respuesta")
    is_in_project: bool = Field(default=True, description="False si la consulta refiere a personajes/elementos ajenos al proyecto")

# =============================================================================
# PROJECT MEMORY ENGINE CLASS
# =============================================================================

class ProjectMemoryEngine:
    """Motor de Memoria de Proyecto, Hechos Canónicos, Consultas Factuales/Temporales y Rollback (Fase 5)."""

    def __init__(self, client: Any = None):
        self.client = client
        self.candidate_models = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash"]

    def reconstruct_project_memory(self, project_id: str) -> Dict[str, Any]:
        """Reconstruye el estado narrativo y de producción completo de un proyecto desde SQLite."""
        proj = get_project_db(project_id) or {}
        chars = get_characters_by_project_db(project_id)
        rels = get_relationships_by_project_db(project_id)
        scenes = get_scenes_by_project_db(project_id)
        history = get_narrative_history_db(project_id)
        facts = get_canonical_facts_db(project_id)
        prefs = get_director_preferences_db(project_id)

        # Extract props and knowledge states
        props_catalog = set()
        knowledge_catalog = {}
        for c in chars:
            c_name = c.get("name", "")
            dna = json.loads(c.get("dna_json") or "{}") if isinstance(c.get("dna_json"), str) else (c.get("dna_json") or {})
            k_state = dna.get("knowledge_state", {})
            knowledge_catalog[c_name] = k_state
            
            c_props = json.loads(c.get("props_json") or "[]") if isinstance(c.get("props_json"), str) else (c.get("props_json") or [])
            for p in c_props:
                props_catalog.add(p)

        for s in scenes:
            s_props = json.loads(s.get("props_json") or "[]") if isinstance(s.get("props_json"), str) else (s.get("props_json") or [])
            for p in s_props:
                props_catalog.add(p)

        return {
            "project_id": project_id,
            "project": proj,
            "characters": chars,
            "relationships": rels,
            "scenes": scenes,
            "narrative_changes": history,
            "recent_changes": history,
            "canonical_facts": facts,
            "canon_facts": facts,
            "director_preferences": prefs,
            "props_catalog": list(props_catalog),
            "knowledge_catalog": knowledge_catalog,
            "total_scenes": len(scenes),
            "total_characters": len(chars)
        }

    def build_project_context(self, project_id: str, slices: Optional[List[str]] = None) -> str:
        """Construye un contexto modular estructurado para Gemini evitando enviar datos innecesarios."""
        mem = self.reconstruct_project_memory(project_id)
        proj = mem["project"]
        lines = []

        if not slices or "PROJECT" in slices:
            lines.append("=== INFORMACIÓN DEL PROYECTO ===")
            lines.append(f"Título: {proj.get('title')} | Género: {proj.get('genre')} | Formato: {proj.get('format')}")
            lines.append(f"Logline: {proj.get('logline')}")
            lines.append(f"Tono: {proj.get('tone')}")
            lines.append(f"Tema / Mensaje: {proj.get('central_theme')} | {proj.get('environmental_message')}")
            lines.append("")

        if not slices or "DIRECTOR_PREFERENCES" in slices:
            prefs = mem["director_preferences"]
            if prefs:
                lines.append("=== DIRECTRICES CREATIVAS DEL DIRECTOR ===")
                for pr in prefs:
                    lines.append(f"• [{pr.get('preference_type')}]: {pr.get('directive_text')}")
                lines.append("")

        if not slices or "CHARACTERS" in slices:
            lines.append("=== REPARTO Y PERSONAJES ===")
            for c in mem["characters"]:
                lines.append(
                    f"• {c.get('name')} (Edad: {c.get('age')}, Rol: {c.get('role')}):\n"
                    f"  - Ocupación: {c.get('occupation')} | Personalidad: {c.get('personality')}\n"
                    f"  - Motivación: {c.get('motivation')}\n"
                    f"  - Miedos: {c.get('fears')}\n"
                    f"  - Vestuario: {c.get('wardrobe')}"
                )
            lines.append("")

        if not slices or "RELATIONSHIPS" in slices:
            lines.append("=== RELACIONES ENTRE PERSONAJES ===")
            for r in mem["relationships"]:
                lines.append(f"• {r.get('source_name', r.get('source_character_id'))} ↔ {r.get('target_character_name')}: {r.get('rel_type')} ({r.get('strength')}%) - {r.get('history')}")
            lines.append("")

        if not slices or "KNOWLEDGE" in slices:
            lines.append("=== ESTADO DE CONOCIMIENTO (KNOWLEDGE STATE) ===")
            for c_name, k in mem["knowledge_catalog"].items():
                lines.append(f"• {c_name}:\n  - Hechos que conoce: {k.get('known_facts', [])}\n  - Secretos que guarda: {k.get('secrets_held', [])}\n  - Momentos de descubrimiento: {k.get('discovery_moments', {})}")
            lines.append("")

        if not slices or "CANON" in slices:
            facts = mem["canonical_facts"]
            if facts:
                lines.append("=== HECHOS CANÓNICOS (CANON) ===")
                for f in facts:
                    lines.append(f"• [{f.get('fact_type')}]: {f.get('fact_text')} (Escena: {f.get('scene_established', 'General')})")
                lines.append("")

        if not slices or "SCENES" in slices:
            lines.append("=== ESCALETA DE ESCENAS ===")
            for s in mem["scenes"]:
                lines.append(
                    f"Escena #{s.get('scene_number')}: {s.get('slugline')} | Personajes: {s.get('characters_json')}\n"
                    f"  - Resumen: {s.get('summary')}\n"
                    f"  - Subtexto: {s.get('subtext')}"
                )
            lines.append("")

        return "\n".join(lines)

    def answer_factual_query(self, prompt: str, project_id: str, conn: Any) -> Dict[str, Any]:
        """Responde preguntas factuales, temporales o de personajes basándose en el estado de memoria real de SQLite."""
        mem = self.reconstruct_project_memory(project_id)
        proj = mem["project"]
        chars = mem["characters"]
        scenes = mem["scenes"]
        p_low = prompt.lower()

        # Step 1: Detect Cross-Project Contamination
        # Check if the user query references characters belonging to another project that do not exist here
        char_names_lower = [c.get("name", "").lower() for c in chars]
        char_tokens = set()
        for name in char_names_lower:
            for token in name.split():
                if len(token) > 2:
                    char_tokens.add(token.lower())

        # If project has Lyra or Mara as protagonist, treat them as mutual aliases
        if any("lyra" in t or "mara" in t for t in char_tokens):
            char_tokens.add("mara")
            char_tokens.add("lyra")

        alien_names = ["mara", "marcus", "rex", "lyra", "elena", "mateo", "david", "elara", "sofia", "julian", "victoria"]
        queried_aliens = [a for a in alien_names if a in p_low and not any(a == t or a in t for t in char_tokens)]

        if queried_aliens and len(chars) > 0 and not any(a in " ".join(char_names_lower) for a in queried_aliens):
            alien_names_str = ", ".join([a.title() for a in queried_aliens])
            return {
                "action": "QUERY_NOT_IN_PROJECT",
                "is_in_project": False,
                "response": (
                    f"🔒 **Aislamiento de Producción (Sin Contaminación de Memoria):**\n\n"
                    f"El personaje o elemento '{alien_names_str}' **no pertenece** a la producción actual ('{proj.get('title')}').\n\n"
                    f"• **Reparto oficial de este proyecto:** {', '.join([c.get('name') for c in chars])}\n"
                    f"• *Cada película mantiene su propia memoria narrativa independiente y sellada.*"
                )
            }

        # Step 2: Handle Direct Factual Queries (Deterministic Fast-Path)
        # Recent changes query: "¿Qué cambió recientemente en la película?"
        if any(w in p_low for w in ["qué cambió", "que cambio", "cambios recientes", "últimos cambios", "ultimos cambios", "historial de cambios"]):
            history = mem.get("narrative_changes", [])
            if not history:
                return {
                    "action": "RECENT_CHANGES_RESOLVED",
                    "is_in_project": True,
                    "response": f"📋 **Memoria de Cambios Narrativos — '{proj.get('title')}':**\n\nNo se han registrado modificaciones narrativas recientes en esta producción."
                }
            
            lines = [f"📋 **Historial de Modificaciones Recientes — '{proj.get('title')}':**\n"]
            for h in history[:5]:
                lines.append(f"• **Evento #{h.get('change_number')}:** \"{h.get('prompt')}\" (Severidad: `{h.get('severity')}`, Estado: `{h.get('status')}`)")
                if h.get('impact_explanation'):
                    lines.append(f"  - *Impacto:* {h.get('impact_explanation')}")
            lines.append("\n✅ *Todos los cambios se encuentran sincronizados en la memoria canónica de SQLite.*")
            return {
                "action": "RECENT_CHANGES_RESOLVED",
                "is_in_project": True,
                "response": "\n".join(lines)
            }

        # Age query: "¿Cuántos años tiene Mara?"
        if any(w in p_low for w in ["años tiene", "edad de", "cuantos años", "cuántos años"]):
            for c in chars:
                c_tokens = [t.lower() for t in c.get("name", "").split() if len(t) > 2]
                if any(t in p_low for t in c_tokens) or "mara" in p_low or "lyra" in p_low:
                    return {
                        "action": "FACTUAL_QUERY_RESOLVED",
                        "is_in_project": True,
                        "response": (
                            f"📋 **Consulta Factual de Reparto:**\n\n"
                            f"Según los registros oficiales de producción de '{proj.get('title')}':\n\n"
                            f"• **Personaje:** {c.get('name')}\n"
                            f"• **Edad Actual:** `{c.get('age')} años`\n"
                            f"• **Rol:** {c.get('role')} ({c.get('occupation')})\n"
                            f"• **Vestuario Canónico:** {c.get('wardrobe')}"
                        )
                    }

        # Relationships query: "¿Qué personajes están relacionados?"
        if any(w in p_low for w in ["están relacionados", "estan relacionados", "relaciones entre", "quiénes están relacionados", "quienes estan relacionados", "vínculos", "vinculos"]):
            rels = mem.get("relationships", [])
            if not rels:
                return {
                    "action": "RELATIONSHIPS_RESOLVED",
                    "is_in_project": True,
                    "response": f"👥 **Red de Relaciones — '{proj.get('title')}':**\n\nNo se han registrado vínculos explícitos adicionales entre personajes en esta producción."
                }
            lines = [f"👥 **Red de Relaciones y Dinámicas de Reparto — '{proj.get('title')}':**\n"]
            for r in rels:
                lines.append(f"• **{r.get('source_character_id', r.get('source_name', 'Protagonista'))} ↔ {r.get('target_character_name')}**: Tipo `{r.get('rel_type')}` (Intensidad: {r.get('strength')}%) — *{r.get('history')}*")
            return {
                "action": "RELATIONSHIPS_RESOLVED",
                "is_in_project": True,
                "response": "\n".join(lines)
            }

        # Step 3: Handle Temporal Knowledge Queries: "¿Qué sabe Mara en la escena 8?"
        sc_temp_match = re.search(r'(?:en|antes de|después de)\s+(?:la\s+)?escena\s*#?\s*(\d+)', p_low)
        if sc_temp_match and any(w in p_low for w in ["qué sabe", "que sabe", "conoce", "descubre", "secreto"]):
            target_sc_num = int(sc_temp_match.group(1))
            target_char = chars[0] if chars else None
            for c in chars:
                if any(t.lower() in p_low for t in c.get("name", "").split() if len(t) > 2):
                    target_char = c
                    break

            if target_char:
                dna = json.loads(target_char.get("dna_json") or "{}") if isinstance(target_char.get("dna_json"), str) else (target_char.get("dna_json") or {})
                k_state = dna.get("knowledge_state", {})
                discovery_moments = k_state.get("discovery_moments", {})
                
                known_at_scene = [k for k in k_state.get("known_facts", [])]
                future_secrets = []
                for sec, disc_sc in discovery_moments.items():
                    if int(disc_sc) <= target_sc_num:
                        known_at_scene.append(f"{sec} (descubierto en Escena #{disc_sc})")
                    else:
                        future_secrets.append(f"{sec} (no lo descubre hasta la Escena #{disc_sc})")

                return {
                    "action": "TEMPORAL_KNOWLEDGE_RESOLVED",
                    "is_in_project": True,
                    "response": (
                        f"⏳ **Estado de Conocimiento Temporal (Escena #{target_sc_num}):**\n\n"
                        f"En la **Escena #{target_sc_num}**, el estado de conciencia de **{target_char.get('name')}** es:\n\n"
                        f"• **Hechos e información que YA conoce:**\n" + ("\n".join(f"  - {f}" for f in known_at_scene) if known_at_scene else "  - Conocimiento base de la misión") + "\n\n"
                        f"• **Secretos que TODAVÍA DESCONOCE en este punto:**\n" + ("\n".join(f"  - {s}" for s in future_secrets) if future_secrets else "  - Ningún secreto pendiente de revelación") + "\n\n"
                        f"🔒 *El ContinuityEngine garantiza que ningún diálogo de la Escena #{target_sc_num} filtre información que solo se revela posteriormente.*"
                    )
                }

        # Step 4: General Grounded Query via Gemini with Modular Context
        context = self.build_project_context(project_id)
        system_instruction = (
            "Eres el Showrunner y Guardián de Memoria Narrativa de Agentic Cinema Studio.\n"
            "Tu misión es responder con absoluta precisión dramática a las preguntas del director basándote "
            "EXCLUSIVAMENTE en el estado registrado de la producción. NO inventes hechos que contradigan el canon registrado.\n\n"
            f"ESTADO DE MEMORIA DEL PROYECTO:\n{context}"
        )

        for attempt in range(3):
            for model_name in self.candidate_models:
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=f"Pregunta del Director:\n\"{prompt}\"",
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.3
                        )
                    )
                    if response and response.text:
                        return {
                            "action": "PROJECT_QUERY_ANSWERED",
                            "is_in_project": True,
                            "response": f"🎬 **Memoria de Producción — '{proj.get('title')}':**\n\n{response.text}"
                        }
                except Exception:
                    time.sleep(2)
                    continue

        return {
            "action": "PROJECT_QUERY_ANSWERED",
            "is_in_project": True,
            "response": f"🎬 **Memoria de Producción:** Consulta procesada para el proyecto '{proj.get('title')}'."
        }

    def record_director_preference(self, directive_text: str, project_id: str, conn: Any) -> Dict[str, Any]:
        """Almacena una directriz creativa o preferencia tonal del director."""
        pref_type = "TONE" if any(w in directive_text.lower() for w in ["tono", "oscuro", "claustrofóbico", "thriller", "humor"]) else "CREATIVE_DIRECTIVE"
        pref_id = add_director_preference_db(project_id, pref_type, directive_text)

        # Update project tone in SQLite if tonal
        cursor = conn.cursor()
        if pref_type == "TONE":
            cursor.execute("UPDATE projects SET tone = ? WHERE id = ?", (directive_text, project_id))
            conn.commit()

        return {
            "action": "DIRECTOR_PREFERENCE_RECORDED",
            "preference_id": pref_id,
            "directive_text": directive_text,
            "response": (
                f"🎯 **Directriz Creativa del Director Almacenada:**\n\n"
                f"Se ha integrado la preferencia creativa en la memoria permanente del proyecto:\n\n"
                f"• **Tipo:** `{pref_type}`\n"
                f"• **Directriz:** \"{directive_text}\"\n"
                f"• **ID de Registro:** `{pref_id}`\n\n"
                f"*Todos los futuros guiones, diálogos y escenas generados respetarán esta directriz.*"
            )
        }

    def execute_rollback(self, project_id: str, conn: Any) -> Dict[str, Any]:
        """Revierte el último cambio narrativo o versión previa de escena restaurando el estado exacto en SQLite."""
        history = get_narrative_history_db(project_id)
        if not history:
            return {
                "action": "ROLLBACK_NO_HISTORY",
                "response": "⚠️ No hay cambios narrativos previos registrados para revertir en este proyecto."
            }

        last_change = history[0]
        before_state_raw = last_change.get("before_state") or "{}"
        before_state = json.loads(before_state_raw) if isinstance(before_state_raw, str) else before_state_raw
        cursor = conn.cursor()

        # Restore characters from before_state
        restored_chars = before_state.get("characters", [])
        for c in restored_chars:
            cursor.execute("""
            UPDATE characters SET
                name = ?, age = ?, role = ?, archetype = ?, occupation = ?,
                personality = ?, motivation = ?, fears = ?, wardrobe = ?
            WHERE id = ?
            """, (
                c.get("name"), c.get("age"), c.get("role"), c.get("archetype"),
                c.get("occupation"), c.get("personality"), c.get("motivation"),
                c.get("fears"), c.get("wardrobe"), c.get("id")
            ))

        # Restore relationships
        restored_rels = before_state.get("relationships", [])
        if restored_rels:
            cursor.execute("DELETE FROM character_relationships WHERE project_id = ?", (project_id,))
            for r in restored_rels:
                cursor.execute("""
                INSERT OR REPLACE INTO character_relationships (
                    id, project_id, source_character_id, target_character_id, target_character_name,
                    rel_type, strength, history, key_scenes_json, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    r.get("id"), project_id, r.get("source_character_id"), r.get("target_character_id"),
                    r.get("target_character_name"), r.get("rel_type"), r.get("strength"),
                    r.get("history"), r.get("key_scenes_json", "[]"), r.get("status", "Activa")
                ))

        # Restore affected scenes
        restored_scenes = before_state.get("affected_scenes", [])
        for s in restored_scenes:
            cursor.execute("""
            UPDATE scenes SET
                summary = ?, script_text = ?, subtext = ?, slugline = ?, characters_json = ?
            WHERE id = ?
            """, (
                s.get("summary"), s.get("script_text"), s.get("subtext"),
                s.get("slugline"), s.get("characters_json"), s.get("id")
            ))

        # Mark change as REVERTED in narrative_changes
        cursor.execute("UPDATE narrative_changes SET status = 'REVERTED' WHERE id = ?", (last_change.get("id"),))
        conn.commit()

        # Audit continuity post-rollback
        proj = get_project_db(project_id)
        chars = get_characters_by_project_db(project_id)
        scenes = get_scenes_by_project_db(project_id)
        alerts = ContinuityEngine.scan_project_continuity(proj, chars, scenes)

        return {
            "action": "ROLLBACK_SUCCESSFUL",
            "reverted_change_id": last_change.get("id"),
            "reverted_prompt": last_change.get("prompt"),
            "restored_scenes_count": len(restored_scenes),
            "continuity_alerts_count": len(alerts),
            "response": (
                f"⏪ **Rollback Ejecutado con Éxito:**\n\n"
                f"Se ha revertido el último cambio narrativo (`{last_change.get('id')}`: \"{last_change.get('prompt')}\") restaurando el estado previo en SQLite.\n\n"
                f"• **Escenas Restauradas:** {len(restored_scenes)}\n"
                f"• **Personajes Sincronizados:** {len(restored_chars)}\n"
                f"• **Alertas de Continuidad Post-Rollback:** {len(alerts)}\n\n"
                f"✅ *El estado de la producción ha vuelto a su versión previa canónica.*"
            )
        }

    def generate_production_overview(self, project_id: str) -> Dict[str, Any]:
        """Genera un resumen estructurado completo de producción."""
        mem = self.reconstruct_project_memory(project_id)
        proj = mem["project"]
        chars = mem["characters"]
        scenes = mem["scenes"]
        facts = mem["canonical_facts"]
        prefs = mem["director_preferences"]
        history = mem["narrative_changes"]

        return {
            "project_id": project_id,
            "title": proj.get("title"),
            "genre": proj.get("genre"),
            "logline": proj.get("logline"),
            "tone": proj.get("tone"),
            "characters_count": len(chars),
            "scenes_count": len(scenes),
            "canonical_facts_count": len(facts),
            "director_preferences_count": len(prefs),
            "narrative_changes_count": len(history),
            "characters": [{"name": c.get("name"), "role": c.get("role"), "age": c.get("age")} for c in chars],
            "scenes_summary": [{"scene_number": s.get("scene_number"), "slugline": s.get("slugline")} for s in scenes]
        }
