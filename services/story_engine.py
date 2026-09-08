from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import json

class CharacterDraft(BaseModel):
    name: str = Field(description="Nombre completo o identificador del personaje")
    age: int = Field(description="Edad en años (o equivalente biológico si no es humano)")
    species: str = Field(default="Humano", description="Especie: Humano, Canino, Androide, etc.")
    role: str = Field(description="Rol narrativo: Protagonista, Aliado Principal, Antagonista, Mentor, etc.")
    archetype: str = Field(description="Arquetipo dramático (ej. The Explorer, The Visionary, The Skeptic, etc.)")
    occupation: str = Field(description="Ocupación o función en la historia")
    personality: str = Field(description="Rasgos psicológicos y de personalidad")
    motivation: str = Field(description="Deseo o motivación central en la película")
    fears: str = Field(description="Miedos y vulnerabilidades")
    strengths: str = Field(description="Habilidades y fortalezas clave")
    weaknesses: str = Field(description="Defectos y debilidades dramáticas")
    wardrobe: str = Field(description="Vestuario adaptado a la época, locación y ambientación")
    avatar_url: Optional[str] = Field(default=None, description="URL de referencia o avatar")

class SceneDraft(BaseModel):
    scene_number: int = Field(description="Número correlativo de escena")
    title: str = Field(description="Título breve de la escena")
    slugline: str = Field(description="Encabezado estándar de Hollywood: INT./EXT. LOCACIÓN - DÍA/NOCHE/HORA")
    location: str = Field(description="Locación física donde transcurre")
    interior_exterior: str = Field(description="INT o EXT")
    day_night: str = Field(description="DAY, NIGHT, DUSK, DAWN, u horario específico")
    summary: str = Field(description="Resumen conciso del acontecimiento dramático")
    purpose: str = Field(description="Propósito dramático y avance de la trama")
    objective: str = Field(description="Objetivo inmediato del personaje en la escena")
    conflict: str = Field(description="Obstáculo o conflicto presente")
    stakes: str = Field(description="Lo que está en juego en esta escena")
    emotional_change: str = Field(description="Cambio emocional experimentado por los personajes")
    outcome: str = Field(description="Resultado o consecuencia al finalizar la escena")
    characters_present: List[str] = Field(description="Lista exacta de nombres de los personajes presentes")
    props: List[str] = Field(default_factory=list, description="Objetos y utilería clave")
    environmental_details: str = Field(description="Detalles atmosféricos, climatológicos e iluminación")
    complexity: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH o CRITICAL")
    estimated_cost: float = Field(default=2500.0, description="Costo estimado de producción de la escena")
    script_text: Optional[str] = Field(default=None, description="Libreto cinematográfico formateado en estándar Hollywood con acotaciones, personajes en MAYÚSCULAS y diálogos dramáticos")

class RelationshipDraft(BaseModel):
    source_character_name: str = Field(description="Nombre del personaje de origen")
    target_character_name: str = Field(description="Nombre del personaje con quien se relaciona")
    rel_type: str = Field(description="Tipo de relación: ALLIANCE, CONFLICT, FAMILY, SIBLINGS, MENTORSHIP, ROMANCE, RIVALRY, etc.")
    history: str = Field(description="Historia o trasfondo de su dinámica y relación")
    strength: int = Field(default=80, description="Intensidad de la relación (0-100)")

class StoryBible(BaseModel):
    title: str = Field(description="Título original cinematográfico generado para la película")
    tagline: str = Field(description="Lema o frase promocional impactante")
    logline: str = Field(description="Resumen de una sola frase que resume protagonista, conflicto central y stakes")
    genre: str = Field(description="Género principal y subgéneros (ej. Ciencia Ficción / Drama Ecológico / Misterio)")
    subgenres: List[str] = Field(default_factory=list, description="Lista de subgéneros aplicables")
    tone: str = Field(description="Tono y atmósfera de la obra")
    target_audience: str = Field(description="Público objetivo y demografía recomendada")
    runtime_minutes: int = Field(default=118, description="Duración estimada del largometraje en minutos")
    synopsis: str = Field(description="Sinopsis argumental completa estructurada en 3 Actos")
    visual_aesthetic: str = Field(description="Dirección de arte, fotografía, lentes, paleta de color e iluminación")
    central_theme: str = Field(description="Tema central filosófico o existencial")
    environmental_message: str = Field(description="Mensaje ecológico o reflexión sobre la preservación planetaria")
    act_1_summary: str = Field(description="Resumen detallado del Acto I (Planteamiento, detonante y primer punto de giro)")
    act_2_summary: str = Field(description="Resumen detallado del Acto II (Desarrollo, punto medio, crisis y clímax de acto)")
    act_3_summary: str = Field(description="Resumen detallado del Acto III (Clímax final, resolución y mensaje final)")
    main_conflict: str = Field(description="Conflicto central irresoluble que mueve toda la narrativa")
    stakes: str = Field(description="Lo que la humanidad y los protagonistas perderán si fracasan")
    ending_direction: str = Field(description="Dirección y naturaleza del desenlace final")
    characters: List[CharacterDraft] = Field(description="Elenco de MÍNIMO 3 personajes: Protagonista, Antagonista y Aliado/Secundario diseñados con profundidad psicológica")
    scenes: List[SceneDraft] = Field(description="Lista completa de MÍNIMO 3 a 4 escenas secuenciales estructuradas para la historia")
    relationships: List[RelationshipDraft] = Field(default_factory=list, description="Relaciones y dinámicas dramáticas entre los personajes del elenco")
    canonical_facts: List[str] = Field(default_factory=list, description="Mínimo 3 hechos canónicos clave que fijan la verdad inviolable de la historia")

class StoryEngine:
    """Motor especializado en interpretar premisas libres y generar Story Bibles mediante Gemini API con Structured Outputs."""

    def __init__(self, client: Any = None):
        self.client = client
        if not self.client:
            try:
                import os
                from dotenv import load_dotenv
                load_dotenv()
                api_key = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
                if not api_key:
                    import config
                    api_key = getattr(config, "GEMINI_API_KEY", "")
                if api_key:
                    from google import genai
                    self.client = genai.Client(api_key=api_key)
            except Exception:
                pass
        self.candidate_models = [
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3.6-flash"
        ]

    def generate_story_bible(self, prompt: str) -> StoryBible:
        if not self.client:
            raise ValueError(
                "Gemini API Client no está inicializado. "
                "Verifique que GEMINI_API_KEY esté configurada en su archivo .env o en las variables de entorno."
            )

        from google.genai import types

        system_instruction = (
            "Eres el Director Creativo Principal y Arquitecto Narrativo de Agentic Cinema Studio.\n"
            "Tu misión es interpretar la solicitud del usuario y crear una Story Bible cinematográfica completa, "
            "100% original, profunda y adaptada con precisión a la premisa indicada.\n\n"
            "REGLAS CRÍTICAS DE ESCALABILIDAD DINÁMICA Y PRODUCCIÓN:\n"
            "1. TÍTULO CINEMATOGRÁFICO DE ALTO IMPACTO: Genera un título original, sonoro y memorable adaptado a la premisa (ej. 'Ecos de Neón', 'Frecuencia 1995', 'La Sombra del Faro', 'Código Abisal').\n"
            "2. ELENCO COMPLETO OBLIGATORIO: Debes generar como MÍNIMO 3 personajes: Protagonista, Antagonista y Aliado/Secundario, con perfiles psicológicos, arquetipos y motivaciones contrastantes.\n"
            "3. ESCENARIOS Y ESCALETA: Genera como MÍNIMO 3 a 4 escenas secuenciales completas (habitualmente entre 4 y 8 escenas para formatos estándar o hasta 14-20 si se pide extensa) con sluglines estándar de Hollywood (INT./EXT. LOCACIÓN - DÍA/NOCHE).\n"
            "4. GUION COMPLETO (script_text): Cada escena DEBE incluir en el campo 'script_text' un libreto técnico de Hollywood con acotaciones y diálogos reales entre los personajes presentes. Formato: encabezado de escena, FADE IN:, descripción de acción, NOMBRE DEL PERSONAJE EN MAYÚSCULAS, (acotación actoral entre paréntesis) y líneas de diálogo auténticas, finalizando con CUT TO:.\n"
            "5. RED DE REPARTO: Define en 'relationships' las conexiones entre los personajes (alianzas, rivalidades, conflictos, lealtades) con etiquetas explícitas (ALLIANCE, CONFLICT, MENTORSHIP, etc.).\n"
            "6. HECHOS CANÓNICOS (canonical_facts): Genera al menos 3 hechos canónicos clave que fijen la verdad inviolable del universo de la película.\n"
            "7. RESTRICCIONES NUMÉRICAS EXPLÍCITAS (HARD CONSTRAINTS): Si la instrucción del director especifica una cantidad exacta de escenas (ej. 'exactamente 6 escenas', '8 escenas', '12 escenas') o personajes (ej. '3 personajes', '5 personajes'), DEBES RESPETAR EXACTAMENTE esa cantidad en los arrays correspondientes sin omitir ni añadir elementos arbitrarios.\n"
            "8. Devuelve exclusivamente la estructura JSON requerida conforme al response_schema de StoryBible."
        )

        import time
        last_error = None
        for attempt in range(5):
            for model_name in self.candidate_models:
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=f"Premisa y requerimientos del Director:\n{prompt}",
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json",
                            response_schema=StoryBible,
                            temperature=0.75,
                        )
                    )

                    if response and response.text:
                        story_bible = StoryBible.model_validate_json(response.text)
                        return story_bible

                except Exception as e:
                    last_error = e
                    err_msg = str(e)
                    if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                        time.sleep(12 * (attempt + 1))
                    else:
                        time.sleep(2 * (attempt + 1))
                    continue

        raise RuntimeError(f"Error al generar Story Bible con Gemini: {last_error}")
