import json
import re
from typing import List, Dict, Any, Optional
from services.repetition_detector import RepetitionDetector

class ContinuityEngine:
    """Persistent Project Memory Scanner, Narrative Knowledge Auditor & Conflict Detector."""

    @staticmethod
    def scan_project_continuity(
        project_data: Dict[str, Any],
        characters: List[Dict[str, Any]],
        scenes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Deeply scans all scenes against characters, knowledge boundaries, timeline integrity, dialogue and visual consistency."""
        alerts = []
        rep_detector = RepetitionDetector()

        char_names = set()
        char_map = {}
        for c in characters:
            name = c.get("name", "").strip()
            if name:
                char_names.add(name)
                char_map[name] = c

        # 1. Check scene characters and knowledge states
        for s in scenes:
            sc_num = s.get("scene_number", 1)
            raw_chars = s.get("characters_json") or s.get("characters_present") or s.get("characters") or []
            if isinstance(raw_chars, str):
                try:
                    raw_chars = json.loads(raw_chars)
                except Exception:
                    raw_chars = [raw_chars]

            # Helper to check if a character name matches any official character in the cast
            def matches_cast(query: str) -> bool:
                if not query:
                    return True
                q_clean = query.strip().lower()
                for c in characters:
                    c_name = c.get("name", "").strip().lower()
                    if not c_name:
                        continue
                    if q_clean == c_name or q_clean in c_name or c_name in q_clean:
                        return True
                    # Token overlap (e.g., "Lyra" matching "Dra. Lyra Thorne")
                    q_tokens = set(re.findall(r'\w+', q_clean))
                    c_tokens = set(re.findall(r'\w+', c_name))
                    titles = {"dra", "dr", "comandante", "ingeniero", "capitan", "don", "dona", "mr", "mrs"}
                    q_sig = q_tokens - titles
                    c_sig = c_tokens - titles
                    if q_sig and c_sig and (q_sig & c_sig):
                        return True
                return False

            # Check unknown character references
            for c_name in raw_chars:
                if c_name and not matches_cast(c_name):
                    alerts.append({
                        "id": f"cont_char_unknown_{sc_num}_{c_name[:10]}",
                        "scene_number": sc_num,
                        "character_name": c_name,
                        "issue_type": "Personaje No Registrado",
                        "description": f"En la escena {sc_num} aparece '{c_name}', pero no se encuentra en el reparto oficial.",
                        "suggested_fix": f"Añadir a '{c_name}' al reparto o reemplazar por un personaje existente."
                    })

        # 2. Check timeline numbering
        prev_num = 0
        for s in scenes:
            sc_num = s.get("scene_number", 1)
            if sc_num != prev_num + 1 and prev_num != 0:
                alerts.append({
                    "id": f"cont_seq_{sc_num}",
                    "scene_number": sc_num,
                    "character_name": "Narrativa General",
                    "issue_type": "Secuencia Temporal",
                    "description": f"Discontinuidad en la numeración: Salto de escena {prev_num} a {sc_num}.",
                    "suggested_fix": "Reordenar numeración de escenas consecutivamente."
                })
            prev_num = sc_num

        # 3. Check dialogue speakers vs characters present
        for s in scenes:
            sc_num = s.get("scene_number", 1)
            script_text = s.get("script_text", "")
            raw_chars = s.get("characters_json") or s.get("characters_present") or s.get("characters") or []
            if isinstance(raw_chars, str):
                try:
                    raw_chars = json.loads(raw_chars)
                except Exception:
                    raw_chars = [raw_chars]

            # Extract character names speaking in dialogue
            speaking_names = re.findall(r'\n([A-ZÁÉÍÓÚÑ\s]{3,25})\n(?:\([^\)]+\)\n)?', script_text)
            clean_speaking = set()
            for sp in speaking_names:
                sp_clean = sp.strip().title()
                if sp_clean not in ["Fade In:", "Cut To:", "Dissolve To:", "Ext.", "Int.", "Escena"]:
                    clean_speaking.add(sp_clean)

            # Check if speaking characters are in characters_present
            for sp in clean_speaking:
                is_present = any(sp.lower() in cp.lower() or cp.lower() in sp.lower() for cp in raw_chars)
                if not is_present and len(raw_chars) > 0:
                    alerts.append({
                        "id": f"cont_dialogue_{sc_num}_{sp[:10]}",
                        "scene_number": sc_num,
                        "character_name": sp,
                        "issue_type": "Diálogo Inconsistente",
                        "description": f"'{sp}' tiene líneas de diálogo en la escena {sc_num}, pero no figura en la lista de personajes presentes.",
                        "suggested_fix": f"Añadir '{sp}' a los personajes presentes de la escena {sc_num}."
                    })

        # 4. Check spoken dialogue repetition and clichés (ignoring sluglines & action paragraphs)
        for s in scenes:
            sc_num = s.get("scene_number", 1)
            script_text = s.get("script_text", "")
            is_valid, reasons = rep_detector.check_dialogue(sc_num, script_text)
            if not is_valid:
                alerts.append({
                    "id": f"cont_rep_{sc_num}",
                    "scene_number": sc_num,
                    "character_name": "Co-Director Script Auditor",
                    "issue_type": "Repetición de Diálogo / Cliché",
                    "description": f"En la escena {sc_num} se detectaron patrones repetitivos: {'; '.join(reasons)}",
                    "suggested_fix": "Regenerar el diálogo con lenguaje contextual y subtexto específico."
                })
            # Index spoken dialogue lines for progressive checking
            speeches = rep_detector.extract_speech_only(script_text)
            rep_detector.index_scene_dialogue(sc_num, speeches)

        # 5. Check Day/Night slugline vs metadata consistency
        for s in scenes:
            sc_num = s.get("scene_number", 1)
            slug = (s.get("slugline") or "").upper()
            dn = (s.get("day_night") or "").upper()
            if "NIGHT" in dn or "NOCHE" in dn:
                if " - DÍA" in slug or " - DAY" in slug:
                    alerts.append({
                        "id": f"cont_lighting_{sc_num}",
                        "scene_number": sc_num,
                        "character_name": "Dirección de Fotografía",
                        "issue_type": "Inconsistencia de Iluminación",
                        "description": f"La escena {sc_num} está clasificada como '{dn}', pero su slugline dice '{slug}'.",
                        "suggested_fix": "Sincronizar el slugline y la hora del día en la base de datos."
                    })

        # 6. Knowledge State & Secret Leak Audit
        for c in characters:
            c_name = c.get("name", "")
            raw_dna = c.get("dna_json")
            if isinstance(raw_dna, str):
                try:
                    dna = json.loads(raw_dna) if raw_dna.strip() else {}
                except Exception:
                    dna = {}
            else:
                dna = raw_dna or {}
            k_state = dna.get("knowledge_state", {}) if isinstance(dna, dict) else {}
            discovery_moments = k_state.get("discovery_moments", {}) if isinstance(k_state, dict) else {}

            for secret, disc_scene in discovery_moments.items():
                secret_keywords = [w.lower() for w in secret.split() if len(w) > 3]
                if not secret_keywords:
                    continue
                for s in scenes:
                    sc_num = s.get("scene_number", 1)
                    if sc_num < int(disc_scene):
                        sc_text = (s.get("summary", "") + " " + s.get("script_text", "")).lower()
                        raw_c_json = s.get("characters_json")
                        if isinstance(raw_c_json, str):
                            try:
                                scene_chars = json.loads(raw_c_json) if raw_c_json.strip() else []
                            except Exception:
                                scene_chars = []
                        else:
                            scene_chars = raw_c_json or []
                        c_in_scene = any(c_name.lower() in str(cp).lower() or str(cp).lower() in c_name.lower() for cp in scene_chars)
                        if c_in_scene and any(kw in sc_text for kw in secret_keywords):
                            alerts.append({
                                "id": f"cont_knowledge_leak_{sc_num}_{c_name[:10]}",
                                "scene_number": sc_num,
                                "character_name": c_name,
                                "issue_type": "Fuga de Conocimiento (Knowledge Leak)",
                                "description": f"En la escena {sc_num}, '{c_name}' actúa sobre o menciona '{secret}', pero según su KnowledgeState no descubre esta información hasta la escena {disc_scene}.",
                                "suggested_fix": f"Eliminar la revelación anticipada de la escena {sc_num} o adelantar el descubrimiento."
                            })

        # 7. Temporal & Physical Item Continuity
        lost_items_timeline = {}
        for s in scenes:
            sc_num = s.get("scene_number", 1)
            sc_text = (s.get("summary", "") + " " + s.get("script_text", "")).lower()
            loss_matches = re.findall(r'(?:pierde|destruye|se rompe|extravía|abandona)\s+(?:el|la|su)\s+([a-záéíóúñ\s]{3,20})', sc_text)
            for item in loss_matches:
                clean_item = item.strip().lower()
                if clean_item not in lost_items_timeline:
                    lost_items_timeline[clean_item] = sc_num

            props_raw = s.get("props_json") or "[]"
            props_list = json.loads(props_raw) if isinstance(props_raw, str) else props_raw
            for prop in props_list:
                prop_clean = prop.strip().lower()
                for lost_item, lost_scene in lost_items_timeline.items():
                    if sc_num > lost_scene and (lost_item in prop_clean or prop_clean in lost_item):
                        if "recupera" not in sc_text and "encuentra" not in sc_text:
                            alerts.append({
                                "id": f"cont_temporal_item_{sc_num}_{prop_clean[:10]}",
                                "scene_number": sc_num,
                                "character_name": "Continuidad Temporal y Objetos",
                                "issue_type": "Inconsistencia Temporal de Objeto",
                                "description": f"El objeto '{prop}' aparece en la utilería de la escena {sc_num}, pero fue destruido/perdido en la escena {lost_scene} sin que se justifique su recuperación.",
                                "suggested_fix": f"Eliminar '{prop}' de la escena {sc_num} o añadir una justificación dramática de recuperación."
                            })

        return alerts
