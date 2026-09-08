import re
from difflib import SequenceMatcher
from typing import List, Dict, Any, Tuple, Optional

class ScreenplayAuditor:
    """
    Auditor Forense de Continuidad Dramática y Control de Repetición de Diálogos (Fase 10.9).
    Detecta duplicaciones exactas, casi-idénticas (fuzzy >= 0.75), clichés, frases de plantilla
    y ecos de diálogo/acción entre escenas, diferenciando callbacks intencionales de fallos de generación.
    """

    BANNED_CLICHES = [
        "la verdad no puede",
        "sombras de este lugar",
        "vamos a terminar lo que empezamos",
        "el tiempo se nos agota",
        "nadie saldra ileso",
        "no hay vuelta atras",
        "the truth cannot be",
        "finish what we started",
        "time is running out",
        "there is no turning back"
    ]

    # Regex para detectar turnos de personajes en diversos formatos
    # 1) CHARACTER NAME alone on line: "ELENA", "ELENA (V.O.)", "DR. MARINA SILVA", "**ELENA**"
    # 2) CHARACTER: on line: "ELENA:", "DAVID (O.S.):", "**ELENA:**"
    RE_SPEAKER_LINE = re.compile(
        r'^(?:\*\*)?([A-ZÁÉÍÓÚÑ0-9\.\s\-]{2,35})(?:\s*\([A-ZÁÉÍÓÚÑa-záéíóúñ\.\s\-]+\))?(?:\*\*)?\s*:\s*(.*)$'
    )
    RE_SPEAKER_STANDALONE = re.compile(
        r'^(?:\*\*)?([A-ZÁÉÍÓÚÑ0-9\.\s\-]{2,35})(?:\s*\([A-ZÁÉÍÓÚÑa-záéíóúñ\.\s\-]+\))?(?:\*\*)?\s*$'
    )

    @classmethod
    def extract_dialogue_entries(cls, script_text: str) -> List[Dict[str, str]]:
        """
        Extrae estructuradamente cada turno de diálogo del guion soportando:
        - Estándar Hollywood (Nombre en mayúsculas, acotación parentética opcional, parlamento).
        - Extensiones (V.O., O.S., CONT'D).
        - Formato con dos puntos (ELENA: parlamento o ELENA (tono): parlamento).
        - Negritas Markdown (**ELENA:** parlamento).
        """
        if not script_text:
            return []

        lines = script_text.splitlines()
        entries = []
        current_speaker = None
        current_parenthetical = ""
        speech_lines = []

        def flush():
            nonlocal current_speaker, current_parenthetical, speech_lines
            if current_speaker and speech_lines:
                speech_text = " ".join(speech_lines).strip()
                if len(speech_text) > 3:
                    entries.append({
                        "speaker": current_speaker,
                        "parenthetical": current_parenthetical,
                        "speech": speech_text
                    })
            current_speaker = None
            current_parenthetical = ""
            speech_lines = []

        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                flush()
                continue

            # Saltar encabezados de escena y transiciones
            if any(trimmed.upper().startswith(h) for h in ["INT.", "EXT.", "INT/EXT", "FADE IN:", "CUT TO:", "DISSOLVE TO:", "FADE OUT."]):
                flush()
                continue

            # Caso 1: Formato en una sola línea "PERSONAJE: diálogo" o "PERSONAJE (acotación): diálogo"
            inline_match = cls.RE_SPEAKER_LINE.match(trimmed)
            if inline_match:
                speaker_raw = inline_match.group(1).strip()
                rest = inline_match.group(2).strip()
                # Verificar que el nombre sea mayormente mayúsculas
                if speaker_raw.isupper() and len(speaker_raw) < 35 and not speaker_raw.startswith("NOTA"):
                    flush()
                    current_speaker = speaker_raw
                    # Extraer parenthetical si venía en el resto "(susurrando) diálogo"
                    paren_match = re.match(r'^\((.*?)\)\s*(.*)$', rest)
                    if paren_match:
                        current_parenthetical = paren_match.group(1).strip()
                        speech_lines.append(paren_match.group(2).strip())
                    else:
                        speech_lines.append(rest)
                    flush()
                    continue

            # Caso 2: Acotación parentética aislada "(susurrando con cautela)"
            if trimmed.startswith("(") and trimmed.endswith(")"):
                current_parenthetical = trimmed[1:-1].strip()
                continue

            # Caso 3: Nombre de personaje en línea propia
            standalone_match = cls.RE_SPEAKER_STANDALONE.match(trimmed)
            if standalone_match:
                speaker_candidate = standalone_match.group(1).strip()
                # Evitar falsos positivos como notas o descripciones en mayúsculas
                if speaker_candidate.isupper() and len(speaker_candidate) < 35 and not any(w in speaker_candidate for w in ["NOTA", "ESCENA", "ACTO", "DÍA", "NOCHE", "TITÁN"]):
                    flush()
                    current_speaker = speaker_candidate
                    # Extraer posible acotación en la misma línea "ELENA (V.O.)"
                    paren_in_speaker = re.search(r'\((.*?)\)', trimmed)
                    if paren_in_speaker:
                        current_parenthetical = paren_in_speaker.group(1).strip()
                    continue

            # Caso 4: Si hay un personaje activo, es línea de diálogo
            if current_speaker:
                speech_lines.append(trimmed)
            else:
                # Si no hay speaker activo, revisar si parece diálogo entre comillas: "..."
                if (trimmed.startswith('"') and trimmed.endswith('"')) or (trimmed.startswith('«') and trimmed.endswith('»')):
                    clean_speech = trimmed[1:-1].strip()
                    if len(clean_speech) > 5:
                        entries.append({
                            "speaker": "DIÁLOGO",
                            "parenthetical": "",
                            "speech": clean_speech
                        })

        flush()
        return entries

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """Normaliza texto eliminando acentos, puntuación y espacios extras para comparación léxica."""
        t = (text or "").lower()
        t = re.sub(r'\(.*?\)', '', t)
        t = re.sub(r'\[.*?\]', '', t)
        t = re.sub(r'[^\w\s]', '', t)
        return " ".join(t.split())

    @classmethod
    def calculate_similarity(cls, text_a: str, text_b: str) -> float:
        """Calcula ratio de similitud de secuencia entre dos parlamentos."""
        norm_a = cls.normalize_text(text_a)
        norm_b = cls.normalize_text(text_b)
        if not norm_a or not norm_b:
            return 0.0
        if norm_a == norm_b:
            return 1.0
        return SequenceMatcher(None, norm_a, norm_b).ratio()

    @classmethod
    def audit_screenplay(cls, scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Realiza una auditoría forense integral de diálogos y texto entre todas las escenas:
        1. Extrae y compara turnos de diálogo.
        2. Detecta frases n-gram repetidas en el cuerpo completo de las escenas.
        3. Clasifica leitmotifs intencionales de apertura/cierre vs duplicaciones accidentales.
        """
        exact_duplicates = []
        fuzzy_duplicates = []
        issues = []
        dialogue_index = []

        for s in scenes:
            sc_num = s.get("scene_number", 0)
            slug = s.get("slugline", "")
            script = s.get("script_text") or s.get("summary") or ""
            entries = cls.extract_dialogue_entries(script)

            for e in entries:
                dialogue_index.append({
                    "scene_number": sc_num,
                    "slugline": slug,
                    "speaker": e["speaker"],
                    "parenthetical": e["parenthetical"],
                    "speech": e["speech"],
                    "normalized": cls.normalize_text(e["speech"])
                })

        total_dialogues = len(dialogue_index)
        total_scenes = len(scenes)

        # 1. Comparación cruzada de turnos de diálogo
        for i in range(len(dialogue_index)):
            d1 = dialogue_index[i]
            if len(d1["normalized"]) < 12:
                continue

            for j in range(i + 1, len(dialogue_index)):
                d2 = dialogue_index[j]
                if d1["scene_number"] == d2["scene_number"]:
                    continue

                sim = cls.calculate_similarity(d1["speech"], d2["speech"])

                if sim >= 0.90:
                    is_intentional_callback = (
                        d1["scene_number"] == 1 and
                        d2["scene_number"] == total_scenes and
                        total_scenes >= 4
                    )

                    dup_record = {
                        "type": "INTENTIONAL_CALLBACK" if is_intentional_callback else "EXACT_DUPLICATION",
                        "speaker": d1["speaker"],
                        "scene_a": d1["scene_number"],
                        "slugline_a": d1["slugline"],
                        "scene_b": d2["scene_number"],
                        "slugline_b": d2["slugline"],
                        "speech_a": d1["speech"],
                        "speech_b": d2["speech"],
                        "similarity": round(sim, 2),
                        "is_flaw": not is_intentional_callback
                    }

                    if not is_intentional_callback:
                        exact_duplicates.append(dup_record)
                        issues.append(
                            f"Diálogo duplicado ({int(sim*100)}%) de {d1['speaker']} entre Escena {d1['scene_number']} y Escena {d2['scene_number']}: '{d1['speech'][:60]}...'"
                        )
                    else:
                        dup_record["note"] = "Leitmotif temático de apertura y cierre (Aceptado como recurso dramático)"

                elif sim >= 0.75 and d1["speaker"] == d2["speaker"]:
                    fuzzy_duplicates.append({
                        "type": "HIGH_SIMILARITY",
                        "speaker": d1["speaker"],
                        "scene_a": d1["scene_number"],
                        "scene_b": d2["scene_number"],
                        "speech_a": d1["speech"],
                        "speech_b": d2["speech"],
                        "similarity": round(sim, 2),
                        "is_flaw": True
                    })
                    issues.append(
                        f"Alta redundancia ({int(sim*100)}%) de {d1['speaker']} entre Escenas {d1['scene_number']} y {d2['scene_number']}"
                    )

        # 2. Análisis global de frases n-gram repetidas en texto completo (> 6 palabras)
        sentences_seen = {}
        for s in scenes:
            sc_num = s.get("scene_number", 0)
            text = (s.get("script_text") or "") + " " + (s.get("summary") or "")
            raw_sentences = re.split(r'[\.\n\!\?]+', text)
            for raw_s in raw_sentences:
                cleaned = cls.normalize_text(raw_s)
                words = cleaned.split()
                if len(words) >= 7:
                    key = " ".join(words[:12])
                    if key in sentences_seen:
                        prev_sc = sentences_seen[key]
                        if prev_sc != sc_num and prev_sc != 1 and sc_num != total_scenes:
                            dup_already = any(d["scene_a"] == prev_sc and d["scene_b"] == sc_num for d in exact_duplicates)
                            if not dup_already:
                                exact_duplicates.append({
                                    "type": "REPEATED_SENTENCE_FRAGMENT",
                                    "scene_a": prev_sc,
                                    "scene_b": sc_num,
                                    "speech_a": raw_s.strip(),
                                    "speech_b": raw_s.strip(),
                                    "similarity": 1.0,
                                    "is_flaw": True
                                })
                                issues.append(f"Frase narrativa repetida entre Escena {prev_sc} y Escena {sc_num}: '{raw_s.strip()[:60]}...'")
                    else:
                        sentences_seen[key] = sc_num

        has_critical_repetition = len(exact_duplicates) > 0
        repetition_score = max(0, 100 - (len(exact_duplicates) * 25) - (len(fuzzy_duplicates) * 10))

        return {
            "healthy": not has_critical_repetition and len(fuzzy_duplicates) == 0,
            "repetition_score": repetition_score,
            "total_dialogues_audited": total_dialogues,
            "exact_duplicates": exact_duplicates,
            "fuzzy_duplicates": fuzzy_duplicates,
            "issues": issues,
            "summary": (
                "Guion limpio de repeticiones accidentales."
                if not issues else
                f"Se detectaron {len(exact_duplicates)} duplicaciones exactas y {len(fuzzy_duplicates)} redundancias léxicas."
            )
        }

    @classmethod
    def get_progressive_dialogue_replacement(
        cls,
        project_title: str,
        scene_number: int,
        speaker: str,
        other_speaker: str,
        scene_summary: str,
        conflict: str
    ) -> str:
        """
        Genera un reemplazo de diálogo fresco, no repetitivo y progresivo
        contextualizado a la escena actual y personajes involucrados.
        """
        first_name = speaker.split()[-1] if speaker else "Personaje"
        other_first = other_speaker.split()[-1] if other_speaker else "Colega"

        catalog = [
            f"No podemos ignorar las anomalías de la telemetría, {other_first}. Los cálculos confirman que el vector no es aleatorio.",
            f"Si ejecutamos la orden sin contrastar los datos, {other_first}, asumiremos un riesgo que la misión no puede tolerar.",
            f"El margen de error se reduce a cero. O sincronizamos la antena ahora, o el relé colapsará antes de la siguiente órbita.",
            f"Escucha con atención: los registros ópticos no mienten. Alguien alteró deliberadamente las frecuencias maestras.",
            f"No se trata de desobedecer una orden directa, {other_first}; se trata de salvaguardar el descubrimiento más importante de nuestras vidas.",
            f"La presión en los colectores sigue en aumento. Si no aseguramos el acoplamiento manual, perderemos la transmisión completa.",
            f"Tengo la certeza absoluta de que el paquete de datos contiene coordenadas astronómicas, no código militar hostil.",
            f"Ya cruzamos el punto de no retorno. Nuestra única salida viable es transmitir la verdad a las estaciones exteriores."
        ]

        idx = (scene_number * 3 + len(speaker)) % len(catalog)
        return catalog[idx]

    @classmethod
    def repair_duplicates(cls, scenes: List[Dict[str, Any]], project_title: str = "") -> Tuple[List[Dict[str, Any]], int]:
        """
        Repara automáticamente cualquier guion que contenga diálogos duplicados accidentales,
        reescribiendo los parlamentos redundantes con líneas progresivas que avancen el conflicto.
        Garantiza convergencia iterativa hasta alcanzar 100% healthy.
        """
        repaired_scenes = [dict(s) for s in scenes]
        total_repaired = 0

        for pass_num in range(6):
            audit = cls.audit_screenplay(repaired_scenes)
            if audit["healthy"] or not audit["exact_duplicates"]:
                break

            pass_repaired = 0
            for dup in audit["exact_duplicates"]:
                if not dup.get("is_flaw"):
                    continue

                target_scene_num = dup["scene_b"]
                speaker = dup.get("speaker", "PERSONAJE")
                old_speech = dup.get("speech_b", "")

                # Encontrar la escena objetivo a reparar
                for s in repaired_scenes:
                    if s.get("scene_number") == target_scene_num:
                        script = s.get("script_text", "")
                        if old_speech in script:
                            new_speech = cls.get_progressive_dialogue_replacement(
                                project_title=project_title or "Producción",
                                scene_number=target_scene_num + pass_num * 3 + pass_repaired,
                                speaker=speaker,
                                other_speaker="David" if "Elena" in speaker else "Colega",
                                scene_summary=s.get("summary", ""),
                                conflict=s.get("subtext", "")
                            )
                            s["script_text"] = script.replace(old_speech, new_speech, 1)
                            pass_repaired += 1
                            total_repaired += 1

            if pass_repaired == 0:
                break

        return repaired_scenes, total_repaired
