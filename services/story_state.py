import json
from typing import Dict, List, Any, Optional, Set

class KnowledgeState:
    """Tracks what each character knows, suspects, wants, and fears at any point in the narrative."""

    def __init__(self, character_name: str, initial_data: Optional[Dict[str, Any]] = None):
        self.character_name = character_name
        data = initial_data or {}
        self.knows: Set[str] = set(data.get("knows", []))
        self.does_not_know: Set[str] = set(data.get("does_not_know", []))
        self.suspects: Set[str] = set(data.get("suspects", []))
        self.wants: str = data.get("wants", "Avanzar en sus objetivos dramáticos")
        self.fears: str = data.get("fears", "Perder el control o fracasar")
        self.emotional_state: str = data.get("emotional_state", "Alerta / Determinado")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "character_name": self.character_name,
            "knows": list(self.knows),
            "does_not_know": list(self.does_not_know),
            "suspects": list(self.suspects),
            "wants": self.wants,
            "fears": self.fears,
            "emotional_state": self.emotional_state
        }

    def learn_fact(self, fact: str):
        self.knows.add(fact)
        self.does_not_know.discard(fact)
        self.suspects.discard(fact)

    def add_suspicion(self, suspicion: str):
        if suspicion not in self.knows:
            self.suspects.add(suspicion)


class DramaticSceneUnit:
    """Defines a scene as a dramatic unit with clear stakes, objectives, and consequences."""

    def __init__(
        self,
        scene_number: int,
        slugline: str,
        purpose: str,
        objective: str,
        conflict: str,
        stakes: str,
        emotional_change: str,
        outcome: str,
        characters_present: List[str],
        discovered_clues: Optional[List[str]] = None,
        key_props: Optional[List[str]] = None
    ):
        self.scene_number = scene_number
        self.slugline = slugline
        self.purpose = purpose
        self.objective = objective
        self.conflict = conflict
        self.stakes = stakes
        self.emotional_change = emotional_change
        self.outcome = outcome
        self.characters_present = characters_present
        self.discovered_clues = discovered_clues or []
        self.key_props = key_props or []

    def to_prompt_context(self) -> str:
        return (
            f"--- UNIDAD DRAMÁTICA DE LA ESCENA {self.scene_number} ---\n"
            f"ENCABEZADO: {self.slugline}\n"
            f"PROPÓSITO (PURPOSE): {self.purpose}\n"
            f"OBJETIVO (OBJECTIVE): {self.objective}\n"
            f"CONFLICTO (CONFLICT): {self.conflict}\n"
            f"EN JUEGO (STAKES): {self.stakes}\n"
            f"CAMBIO EMOCIONAL (EMOTIONAL CHANGE): {self.emotional_change}\n"
            f"RESULTADO / CONSECUENCIA (OUTCOME): {self.outcome}\n"
            f"PERSONAJES PRESENTES: {', '.join(self.characters_present)}\n"
            f"PISTAS O ELEMENTOS EN JUEGO: {', '.join(self.discovered_clues) if self.discovered_clues else 'Ninguna nueva'}\n"
        )


class StoryState:
    """Maintains active narrative memory: timeline of events, discovered secrets, key objects, and character knowledge."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.timeline_events: List[Dict[str, Any]] = []
        self.discovered_clues: Dict[str, Dict[str, Any]] = {}
        self.key_objects_location: Dict[str, str] = {}
        self.characters_knowledge: Dict[str, KnowledgeState] = {}
        self.relationship_tensions: Dict[str, int] = {}  # 0 to 100 tension score

    def register_character(self, name: str, role: str, initial_knows: List[str], initial_unknowns: List[str], wants: str, fears: str):
        self.characters_knowledge[name] = KnowledgeState(name, {
            "knows": initial_knows,
            "does_not_know": initial_unknowns,
            "suspects": [],
            "wants": wants,
            "fears": fears,
            "emotional_state": "Inicial / Expectante"
        })

    def get_character_knowledge(self, name: str) -> Optional[KnowledgeState]:
        return self.characters_knowledge.get(name)

    def record_scene_event(
        self,
        scene_number: int,
        summary: str,
        clues_revealed: List[str],
        characters_present: List[str],
        outcome: str
    ):
        event_record = {
            "scene_number": scene_number,
            "summary": summary,
            "clues_revealed": clues_revealed,
            "characters_present": characters_present,
            "outcome": outcome
        }
        self.timeline_events.append(event_record)

        # Update character knowledge
        for clue in clues_revealed:
            self.discovered_clues[clue] = {
                "discovered_in_scene": scene_number,
                "discovered_by": characters_present
            }
            for char_name in characters_present:
                if char_name in self.characters_knowledge:
                    self.characters_knowledge[char_name].learn_fact(clue)

    def build_scene_context(self, scene_number: int, characters_present: List[str]) -> str:
        """Constructs a concise, relevant narrative context for the given scene and present characters."""
        lines = [f"=== ESTADO NARRATIVO Y MEMORIA DE HISTORIA (ESCENA {scene_number}) ==="]

        # Recent events (last 3 scenes)
        recent_events = [e for e in self.timeline_events if e["scene_number"] < scene_number][-3:]
        if recent_events:
            lines.append("ACONTECIMIENTOS PREVIOS RELEVANTES:")
            for ev in recent_events:
                lines.append(f"  • Escena {ev['scene_number']}: {ev['summary']} (Resultado: {ev['outcome']})")
        else:
            lines.append("ACONTECIMIENTOS PREVIOS: Inicio del viaje dramático (Acto I).")

        # Knowledge state for characters present
        lines.append("ESTADO DE CONOCIMIENTO DE LOS PERSONAJES PRESENTES:")
        for char_name in characters_present:
            k = self.characters_knowledge.get(char_name)
            if k:
                knows_str = ", ".join(list(k.knows)[:5]) if k.knows else "Nada relevante aún"
                unknown_str = ", ".join(list(k.does_not_know)[:4]) if k.does_not_know else "Información no revelada"
                lines.append(f"  [{char_name.upper()}]")
                lines.append(f"    - SABE (KNOWS): {knows_str}")
                lines.append(f"    - IGNORA (DOES NOT KNOW): {unknown_str}")
                lines.append(f"    - SOSPECHA (SUSPECTS): {', '.join(list(k.suspects)[:3]) if k.suspects else 'Observando indicios'}")
                lines.append(f"    - MOTIVACIÓN INMEDIATA (WANTS): {k.wants}")
                lines.append(f"    - MIEDO INMEDIATO (FEARS): {k.fears}")

        return "\n".join(lines)

    def validate_dialogue_knowledge(self, character_name: str, dialogue_line: str, scene_number: int) -> List[str]:
        """Checks if a character references information they should not know yet (impossible knowledge detection)."""
        violations = []
        k = self.characters_knowledge.get(character_name)
        if not k:
            return violations

        for unknown in k.does_not_know:
            keywords = [w.lower() for w in unknown.split() if len(w) > 4]
            # If 2 or more distinct keywords from an unknown secret appear in the character's speech
            matched_kw = [w for w in keywords if w in dialogue_line.lower()]
            if len(matched_kw) >= 2:
                violations.append(
                    f"Violación de Conocimiento: '{character_name}' menciona '{unknown}' en Escena {scene_number} antes de haberlo descubierto."
                )

        return violations
