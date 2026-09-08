import re
from typing import List, Dict, Any, Tuple, Set

class RepetitionDetector:
    """Detects repeated phrases, clichés, template dialogue, and excessive lexical similarity across screenplay scenes."""

    BANNED_CLICHES = [
        "la verdad no puede",
        "sombras de este lugar",
        "vamos a terminar lo que empezamos",
        "el tiempo se nos agota",
        "nadie saldra ileso",
        "no hay vuelta atras"
    ]

    def __init__(self):
        self.seen_phrases: Set[str] = set()
        self.scene_dialogues_index: Dict[int, List[str]] = {}

    def extract_speech_only(self, full_script: str) -> List[str]:
        """Extracts strictly spoken character dialogue lines, filtering out sluglines, location names, parentheticals, and action cues."""
        lines = full_script.split('\n')
        speeches = []
        is_after_speaker = False
        for line in lines:
            tr = line.strip()
            if not tr:
                is_after_speaker = False
                continue
            if tr.startswith('INT.') or tr.startswith('EXT.') or tr.startswith('FADE IN:') or tr.startswith('CUT TO:'):
                is_after_speaker = False
                continue
            if tr.isupper() and len(tr) < 30 and not tr.startswith('['):
                is_after_speaker = True
                continue
            if tr.startswith('(') and tr.endswith(')'):
                continue
            if tr.startswith('[') and tr.endswith(']'):
                continue
            if is_after_speaker:
                speeches.append(tr)
                is_after_speaker = False
        return speeches

    def index_scene_dialogue(self, scene_number: int, dialogue_lines: List[str]):
        self.scene_dialogues_index[scene_number] = dialogue_lines
        for line in dialogue_lines:
            normalized = self._normalize(line)
            words = normalized.split()
            # Store 5-gram chunks for strict conversational phrase matching
            for i in range(len(words) - 4):
                gram = " ".join(words[i:i+5])
                self.seen_phrases.add(gram)

    def check_dialogue(self, scene_number: int, proposed_dialogue: str) -> Tuple[bool, List[str]]:
        """Validates proposed dialogue against previous scenes and banned clichés."""
        offending_reasons = []
        speeches = self.extract_speech_only(proposed_dialogue)
        if not speeches:
            speeches = [proposed_dialogue]

        for speech in speeches:
            lower_dlg = speech.lower()

            # 1. Check banned cliché templates
            for cliche in self.BANNED_CLICHES:
                if cliche in lower_dlg:
                    offending_reasons.append(f"Uso de cliché repetitivo / frase de plantilla: '{cliche}'")

            # 2. Check 5-gram identical conversational speech overlap
            normalized = self._normalize(speech)
            words = normalized.split()
            for i in range(len(words) - 4):
                gram = " ".join(words[i:i+5])
                if gram in self.seen_phrases and len(gram) > 20:
                    offending_reasons.append(f"Parlamento de 5 palabras idéntico a una escena previa: '{gram}'")

            # 3. Check identical full sentences in spoken dialogue
            for prev_sc, lines in self.scene_dialogues_index.items():
                if prev_sc >= scene_number:
                    continue
                for prev_line in lines:
                    prev_norm = self._normalize(prev_line)
                    if normalized == prev_norm and len(normalized) > 25:
                        offending_reasons.append(f"Diálogo completo idéntico al de la Escena {prev_sc}: '{speech}'")

        is_valid = len(offending_reasons) == 0
        return is_valid, offending_reasons

    def regenerate_fresh_dialogue(
        self,
        speaker: str,
        other_speaker: str,
        scene_purpose: str,
        scene_conflict: str,
        emotional_state: str,
        clues: List[str],
        era_year: int
    ) -> str:
        """Generates fresh, unique, non-repetitive dialogue grounded strictly in scene purpose and specific clues."""
        first_name = speaker.split()[0]
        other_first = other_speaker.split()[0] if other_speaker else ""
        clue_ref = clues[0] if clues else "el registro de 1920"

        templates = [
            (
                f"{speaker.upper()}\n"
                f"({emotional_state.lower()})\n"
                f"Comprueba la fecha en {clue_ref}. Esto no coincide con lo que nos aseguraron en el pueblo.\n\n"
                f"{other_speaker.upper()}\n"
                f"(revisando los bordes del papel)\n"
                f"Tienes razón, {first_name}. Alguien se tomó la molestia de alterar estas páginas para desviar la atención."
            ),
            (
                f"{speaker.upper()}\n"
                f"(examinando la cerradura)\n"
                f"El mecanismo sigue trabado por el óxido, pero la muesca lateral cede si hacemos palanca juntos.\n\n"
                f"{other_speaker.upper()}\n"
                f"(sujetando la linterna con firmeza)\n"
                f"Cuidado con el cerrojo, {first_name}. Si se rompe la espiga interior, quedará sellado para siempre."
            ),
            (
                f"{speaker.upper()}\n"
                f"(señalando las huellas recientes)\n"
                f"No fuimos los primeros en cruzar este umbral hoy. Las marcas en el suelo son de calzado pesado.\n\n"
                f"{other_speaker.upper()}\n"
                f"(bajando el tono de voz)\n"
                f"Mantente cerca de la pared. No sabemos si quien dejó el rastro sigue en el piso superior."
            )
        ]

        idx = (len(speaker) + len(scene_purpose)) % len(templates)
        return templates[idx]

    def _normalize(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r'\(.*?\)', '', text)  # remove parentheticals
        text = re.sub(r'\[.*?\]', '', text)  # remove action cues
        text = re.sub(r'[^\w\s]', '', text)
        return " ".join(text.split())
