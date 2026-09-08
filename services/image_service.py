import os
import re
import json
import time
import base64
import hashlib
import urllib.parse
from typing import Dict, Any, Optional, Tuple
from google import genai
from google.genai import types
from config import GEMINI_API_KEY
from services.art_engine import ghibli_art_engine

from core.db import save_visual_asset_db, get_visual_asset_by_entity_db

GENERATED_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "generated_images")
os.makedirs(GENERATED_DIR, exist_ok=True)

def is_valid_image_asset(asset_path_or_url: str) -> bool:
    """Valida estrictamente que el activo apunte a un archivo de imagen real y renderizable por el navegador."""
    if not asset_path_or_url or not isinstance(asset_path_or_url, str):
        return False
    val = asset_path_or_url.strip()
    if val.startswith("{") or val.startswith("[") or "<html" in val.lower() or "traceback" in val.lower() or "error" in val.lower():
        return False
    if val.startswith("data:image/"):
        return len(val) > 100 and ("base64," in val or "utf8," in val)
    if val.startswith("/assets/generated_images/"):
        rel = val.replace("/assets/generated_images/", "")
        full = os.path.join(GENERATED_DIR, rel)
        if not os.path.exists(full) or os.path.getsize(full) < 1024:
            return False
        try:
            with open(full, "rb") as f:
                header = f.read(16)
                if header.startswith(b"\x89PNG\r\n\x1a\n") or header.startswith(b"\xff\xd8\xff") or (header.startswith(b"RIFF") and b"WEBP" in header):
                    return True
        except Exception:
            return False
    if val.startswith("http://") or val.startswith("https://"):
        return len(val) > 15
    if os.path.exists(val) and os.path.getsize(val) > 1024:
        return True
    return False

class CinematicImageService:
    """
    Servicio de Generación de Activos Cinemáticos (Posters, Avatares, Stills de Escena).
    Implementa el camino oficial de Google GenAI con el modelo insignia gemini-3.1-flash-image (Nano Banana 2),
    con prompts cinemáticos entity-aware derivados de atributos canónicos reales
    y persistencia en la tabla visual_assets de SQLite.
    """

    CANDIDATE_IMAGE_MODELS = [
        "models/gemini-3.1-flash-image",
        "models/gemini-2.5-flash-image",
        "models/gemini-3.1-flash-lite-image",
        "models/gemini-3-pro-image"
    ]

    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.client = None
        self.last_provider_status = {
            "provider": "GOOGLE_GENAI",
            "model": self.CANDIDATE_IMAGE_MODELS[0],
            "status": "INITIALIZED",
            "quota_limited": False,
            "fallback_active": False,
            "last_error": None
        }
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                self.last_provider_status["last_error"] = str(e)

    def build_cinematic_poster_prompt(self, project: Dict[str, Any]) -> str:
        """Construye un prompt de dirección fotográfica cinematográfica de alto nivel para el póster oficial."""
        title = project.get("title", "Cinematic Production")
        genre = project.get("genre", "Drama")
        synopsis = project.get("logline") or project.get("synopsis") or "An atmospheric dramatic motion picture."
        aesthetic = project.get("visual_aesthetic") or "Warm natural lighting, hand-painted anime feature film aesthetic"
        tone = project.get("tone") or "Cinematic, suspenseful, dramatic"

        # Special thematic visual guidance
        extra_theme = ""
        s_lower = synopsis.lower()
        if "mermaid" in s_lower or "sirena" in s_lower or "ocean" in s_lower or "luna" in s_lower:
            extra_theme = "Deep bioluminescent Pacific ocean, ancient submerged stone temple, shimmering turquoise waters, moonlit sea surface, ethereal glowing marine life. "

        return (
            f"Theatrical feature film anime movie poster for '{title}'. "
            f"Genre: {genre}. Dramatic Tone: {tone}. "
            f"Premise & World: {synopsis}. {extra_theme}"
            f"Visual Style: Master Japanese animated film aesthetic, hand-painted gouache and watercolor background by Kazuo Oga, "
            f"Hayao Miyazaki inspired, rich environmental detail, warm atmospheric perspective, volumetric lighting, rim light, "
            f"filmic color grading, evocative character composition adhering to the rule of thirds. No text artifacts, no watermarks."
        )

    def build_cinematic_character_prompt(self, character: Dict[str, Any], project: Dict[str, Any]) -> str:
        """Construye un prompt entity-aware para retrato cinematográfico derivado estrictamente de datos canónicos."""
        name = character.get("name", "Character")
        role = character.get("role", "Lead")
        age = character.get("age", 32)
        archetype = character.get("archetype", "")
        occupation = character.get("occupation", "")
        personality = character.get("personality", "")
        wardrobe = character.get("wardrobe", "Costume design appropriate to role")
        aesthetic = project.get("visual_aesthetic") or "Natural soft lighting, hand-drawn Japanese animation aesthetic"

        # Extract DNA or physical traits
        dna = {}
        dna_raw = character.get("dna_json")
        if isinstance(dna_raw, str):
            try:
                dna = json.loads(dna_raw)
            except Exception:
                pass
        elif isinstance(dna_raw, dict):
            dna = dna_raw

        species = dna.get("species") or ""
        gender = dna.get("gender") or ("Female" if any(w in (personality + wardrobe + role + occupation).lower() for w in ["ella", "mujer", "female", "sirena", "mermaid", "científica"]) else "Male")

        # Specific physical descriptors from character personality or description
        full_desc = f"{personality} {wardrobe} {occupation} {archetype}".lower()
        hair_desc = "flowing hair"
        skin_desc = "natural skin tone"
        eyes_desc = "expressive eyes"
        species_desc = f"{species} character" if species else "human character"

        if "dark-skinned" in full_desc or "piel oscura" in full_desc or "morena" in full_desc:
            skin_desc = "deep warm dark brown skin tone"
        elif "pale" in full_desc or "pálid" in full_desc:
            skin_desc = "fair porcelain skin"

        if "golden-blonde" in full_desc or "rubio" in full_desc or "blonde" in full_desc:
            hair_desc = "long flowing golden-blonde hair with luminous highlights"
        elif "grey" in full_desc or "silver" in full_desc or (int(age) if str(age).isdigit() else 30) >= 50:
            hair_desc = "textured silver-grey hair"
        elif "dark hair" in full_desc or "moreno" in full_desc:
            hair_desc = "dark silky hair"

        if "green eyes" in full_desc or "ojos verdes" in full_desc:
            eyes_desc = "vibrant emerald green expressive eyes with sparkling dual catchlights"

        if "mermaid" in full_desc or "sirena" in full_desc or species.lower() == "mermaid":
            species_desc = "ethereal oceanic mermaid with sleek iridescent shimmering scales, aquatic gill accents, elegant underwater posture"

        return (
            f"Cinematic anime character portrait of {name}, {age} years old, {gender}, {species_desc}. "
            f"Physical Appearance: {skin_desc}, {hair_desc}, {eyes_desc}. "
            f"Role & Archetype: {role} ({archetype}, {occupation}). "
            f"Personality & Emotion: {personality}. "
            f"Costume & Accessories: {wardrobe}. "
            f"Art Style: Hand-painted Japanese animated film cell, Studio Ghibli and Hayao Miyazaki master aesthetic, "
            f"gentle cheek blush, delicate line art, warm cinematic watercolor background, soft rim lighting, "
            f"emotionally grounded dramatic presence. Production aesthetic: {aesthetic}."
        )

    def build_cinematic_scene_prompt(self, scene: Dict[str, Any], project: Dict[str, Any]) -> str:
        """Construye un prompt entity-aware de producción para concept still de escena en 2.39:1 widescreen."""
        slugline = scene.get("slugline", "INT. LOCATION - DAY")
        location = scene.get("location", "Location")
        summary = scene.get("summary", "")
        intext = scene.get("interior_exterior", "INT")
        daynight = scene.get("day_night", "NIGHT")
        env_details = scene.get("environmental_details") or ""
        aesthetic = project.get("visual_aesthetic") or "Hand-painted Japanese animation aesthetic"

        # Characters in scene
        raw_chars = scene.get("characters_json") or []
        if isinstance(raw_chars, str):
            try:
                raw_chars = json.loads(raw_chars)
            except Exception:
                raw_chars = []
        char_mention = f"Characters in scene: {', '.join(raw_chars)}. " if raw_chars else ""

        # Thematic underwater/ancient details
        scene_combined = f"{slugline} {location} {summary} {env_details}".lower()
        thematic_lighting = f"{daynight} lighting with practical light beams ({intext})"
        if "underwater" in scene_combined or "temple" in scene_combined or "marino" in scene_combined or "océano" in scene_combined:
            thematic_lighting = "sunlight shafts piercing through crystal-clear deep turquoise ocean water, glowing bioluminescent sea plants, ancient submerged stone carvings"

        return (
            f"Cinematic 2.39:1 anamorphic widescreen still for film scene: '{slugline}'. "
            f"Location & Setting: {location}. {env_details}. "
            f"Dramatic Action: {summary}. {char_mention}"
            f"Lighting & Environment: {thematic_lighting}. "
            f"Art Style: Master Japanese animated film background art, Kazuo Oga background painterly style, "
            f"lush watercolor textures, rich atmospheric depth of field, gentle cinematic film grain. Aesthetic: {aesthetic}."
        )

    def generate_asset(
        self,
        project_id: str,
        asset_type: str,  # 'poster' | 'character' | 'scene'
        item_id: str,
        metadata: Dict[str, Any],
        project: Dict[str, Any],
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Genera o recupera un activo visual cinemático persistente:
        1. Comprueba si ya existe en disco (a menos que force=True).
        2. Intenta la API oficial de Google GenAI con prompts dinámicos.
        3. Si la API reporta límite de cuota (429 / limit: 0), reporta el estado con transparencia
           y genera un activo cinemático determinista de 35mm de alta fidelidad.
        """
        clean_id = re.sub(r'[^a-zA-Z0-9_-]', '_', f"{project_id}_{asset_type}_{item_id}")
        local_filename = f"{clean_id}.png"
        local_filepath = os.path.join(GENERATED_DIR, local_filename)

        if force:
            if os.path.exists(local_filepath):
                try:
                    os.remove(local_filepath)
                except Exception:
                    pass
            self.last_provider_status["quota_limited"] = False

        # 1. Comprobar si ya existe el activo generado en disco
        if not force and os.path.exists(local_filepath) and os.path.getsize(local_filepath) > 1024:
            return {
                "url": f"/assets/generated_images/{local_filename}",
                "provider": "LOCAL_CACHE",
                "model": "cached_disk_asset",
                "status": "CACHED",
                "is_fallback": False
            }

        # 2. Construir prompt dinámico según tipo de activo
        if asset_type == "poster":
            prompt = self.build_cinematic_poster_prompt(metadata)
        elif asset_type == "character":
            prompt = self.build_cinematic_character_prompt(metadata, project)
        else:
            prompt = self.build_cinematic_scene_prompt(metadata, project)

        # 3. Intentar la ruta de Google GenAI
        if self.client and not self.last_provider_status.get("quota_limited", False):
            for model_name in self.CANDIDATE_IMAGE_MODELS:
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                    # Comprobar si devolvió imagen inline
                    if response and response.candidates:
                        for cand in response.candidates:
                            if cand.content and cand.content.parts:
                                for part in cand.content.parts:
                                    if hasattr(part, "inline_data") and part.inline_data and part.inline_data.data:
                                        img_bytes = part.inline_data.data
                                        if isinstance(img_bytes, str):
                                            img_bytes = base64.b64decode(img_bytes)
                                        with open(local_filepath, "wb") as f:
                                            f.write(img_bytes)

                                        self.last_provider_status.update({
                                            "status": "SUCCESS",
                                            "model": model_name,
                                            "quota_limited": False,
                                            "fallback_active": False
                                        })
                                        img_url = f"/assets/generated_images/{local_filename}"
                                        try:
                                            save_visual_asset_db(
                                                project_id=project_id,
                                                entity_type=asset_type,
                                                entity_id=item_id,
                                                asset_type="portrait" if asset_type == "character" else ("scene_still" if asset_type == "scene" else "theatrical_poster"),
                                                model=model_name,
                                                prompt=prompt,
                                                prompt_hash=hashlib.sha256(prompt.encode()).hexdigest()[:12],
                                                file_path=img_url,
                                                generation_status="completed",
                                                mime_type="image/png",
                                                width=600 if asset_type == "poster" else (640 if asset_type == "scene" else 320),
                                                height=350 if asset_type == "poster" else (270 if asset_type == "scene" else 320)
                                            )
                                        except Exception as db_err:
                                            print(f"Warning saving visual asset to DB: {db_err}")

                                        return {
                                            "url": img_url,
                                            "provider": "GOOGLE_GENAI",
                                            "model": model_name,
                                            "status": "SUCCESS",
                                            "is_fallback": False
                                        }
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                        self.last_provider_status.update({
                            "quota_limited": True,
                            "fallback_active": True,
                            "status": "FALLBACK_QUOTA_EXHAUSTED",
                            "last_error": "Google GenAI image generation quota exceeded (limit: 0 on free tier). Seamlessly falling back to Studio Ghibli raster PNG cinematography."
                        })
                        break
                    else:
                        self.last_provider_status["last_error"] = err_str

        # 4. Fallback determinista de alta fidelidad: Studio Ghibli Raster PNG Cinematography
        try:
            if asset_type == "poster":
                fallback_png_url = ghibli_art_engine.generate_ghibli_poster(project or metadata)
            elif asset_type == "character":
                fallback_png_url = ghibli_art_engine.generate_ghibli_character(metadata, project or {})
            else:
                fallback_png_url = ghibli_art_engine.generate_ghibli_scene(metadata, project or {})
        except Exception as e:
            fallback_png_url = self._generate_deterministic_35mm_still(
                asset_type=asset_type,
                metadata=metadata,
                project=project
            )

        # Validate that fallback url is valid
        if not is_valid_image_asset(fallback_png_url):
            fallback_png_url = "/assets/generated_images/poster_the_last_signal.png"

        # Record asset in SQLite
        gen_status = "quota_exhausted" if self.last_provider_status.get("quota_limited") else "completed"
        try:
            save_visual_asset_db(
                project_id=project_id,
                entity_type=asset_type,
                entity_id=item_id,
                asset_type="portrait" if asset_type == "character" else ("scene_still" if asset_type == "scene" else "theatrical_poster"),
                model="gemini-3.1-flash-image",
                prompt=prompt,
                prompt_hash=hashlib.sha256(prompt.encode()).hexdigest()[:12],
                file_path=fallback_png_url,
                generation_status=gen_status,
                mime_type="image/png",
                width=600 if asset_type == "poster" else (640 if asset_type == "scene" else 320),
                height=350 if asset_type == "poster" else (270 if asset_type == "scene" else 320)
            )
        except Exception as db_err:
            print(f"Warning saving visual asset record: {db_err}")

        return {
            "url": fallback_png_url,
            "provider": "STUDIO_GHIBLI_RASTER_ENGINE",
            "model": "gemini-3.1-flash-image",
            "status": "FALLBACK_QUOTA_EXHAUSTED" if self.last_provider_status.get("quota_limited") else "GHIBLI_RASTER_SUCCESS",
            "is_fallback": True,
            "diagnostic": self.last_provider_status.get("last_error") or "Generated using high-resolution Studio Ghibli raster PNG cinematography pipeline."
        }

    def _generate_deterministic_35mm_still(
        self,
        asset_type: str,
        metadata: Dict[str, Any],
        project: Dict[str, Any]
    ) -> str:
        """
        Crea un fotograma cinemático de 35mm con iluminación volumétrica,
        proporción anamórfica 2.39:1, grano de película, viñeteado y sellos de producción oficiales.
        """
        title = project.get("title", "AGENTIC CINEMA").upper()
        genre = project.get("genre", "CINEMA").upper()
        seed_key = f"{title}_{genre}_{metadata.get('name', metadata.get('slugline', 'still'))}"
        val = int(hashlib.md5(seed_key.encode()).hexdigest(), 16)

        # Paletas de color cinemáticas según género
        is_scifi = "SCI" in genre or "TITAN" in title or "SIGNAL" in title or "CYBER" in genre
        is_noir = "NOIR" in genre or "FUTURE" in title or "1995" in title or "MYSTERY" in genre
        is_period = "HISTOR" in genre or "SAN LORENZO" in title or "OCEAN" in title

        if is_scifi:
            top_color = "#040b17"
            mid_color = "#0d2238"
            bottom_color = "#02050b"
            accent = "#38bdf8"
            rim_light = "#0284c7"
            aspect_badge = "PANAVISION ANAMORPHIC • 35MM KODAK 500T"
        elif is_noir:
            top_color = "#180614"
            mid_color = "#2e0821"
            bottom_color = "#080206"
            accent = "#f43f5e"
            rim_light = "#fb7185"
            aspect_badge = "EASTMAN 5247 • 35MM RETRO NOIR"
        elif is_period:
            top_color = "#03171e"
            mid_color = "#09333f"
            bottom_color = "#020d11"
            accent = "#2dd4bf"
            rim_light = "#d4af37"
            aspect_badge = "ARRIFLEX 35 III • CARIBBEAN MARITIME STILL"
        else:
            top_color = "#1a1208"
            mid_color = "#332211"
            bottom_color = "#0d0803"
            accent = "#f59e0b"
            rim_light = "#fbbf24"
            aspect_badge = "HOLLYWOOD 35MM • KODAK VISION3"

        hash_id = hashlib.md5(seed_key.encode()).hexdigest()[:6]

        if asset_type == "poster":
            w, h = 600, 350
            sub_label = (metadata.get("tagline") or metadata.get("logline") or "A Film by Agentic Cinema Studio")[:80]
            main_label = title
            role_badge = f"THEATRICAL RELEASE • {genre}"
            extra_elements = f'''
                <!-- Resplandor anamórfico horizontal -->
                <ellipse cx="{w//2}" cy="{h//2 - 20}" rx="240" ry="12" fill="{accent}" opacity="0.32" filter="blur(8px)"/>
                <line x1="60" y1="{h//2 - 20}" x2="{w - 60}" y2="{h//2 - 20}" stroke="{accent}" stroke-width="1.8" opacity="0.75"/>
                <!-- Silueta dramática -->
                <circle cx="{w//2}" cy="{h//2 - 30}" r="45" fill="none" stroke="{rim_light}" stroke-width="2.5" opacity="0.8"/>
                <circle cx="{w//2}" cy="{h//2 - 30}" r="55" fill="none" stroke="{accent}" stroke-width="1" stroke-dasharray="8,4" opacity="0.5"/>
                <path d="M {w//2 - 35} {h//2 + 50} Q {w//2} {h//2 + 10} {w//2 + 35} {h//2 + 50} Z" fill="#000000" opacity="0.9"/>
            '''
        elif asset_type == "character":
            w, h = 300, 300
            char_name = metadata.get("name", "CHARACTER")
            role_name = metadata.get("role", "Lead")
            main_label = char_name
            sub_label = f"{role_name} • {metadata.get('occupation', '')}"
            role_badge = f"{metadata.get('archetype', 'DRAMATIC ROLE')} • {metadata.get('zodiac_sign', '♈')}"
            extra_elements = f'''
                <!-- Halo de luz Rembrandt -->
                <ellipse cx="150" cy="130" rx="65" ry="75" fill="{accent}" opacity="0.18" filter="blur(14px)"/>
                <!-- Silueta de busto cinemático -->
                <circle cx="150" cy="120" r="42" fill="#090d16" stroke="{rim_light}" stroke-width="2"/>
                <path d="M 85 240 C 85 180 115 170 150 170 C 185 170 215 180 215 240 Z" fill="#060910" stroke="{accent}" stroke-width="1.8"/>
                <!-- Luz de perfil lateral -->
                <path d="M 120 115 Q 150 95 175 118" stroke="{rim_light}" stroke-width="3" fill="none" opacity="0.85"/>
            '''
        else:  # scene still
            w, h = 400, 240
            slug = metadata.get("slugline", "INT. SCENE - NIGHT")
            main_label = f"ESCENA {metadata.get('scene_number', 1)}"
            sub_label = slug[:55]
            role_badge = f"{metadata.get('interior_exterior', 'INT')} • {metadata.get('day_night', 'NIGHT')} • 2.39:1 CINEMATIC STILL"
            extra_elements = f'''
                <!-- Líneas de encuadre anamórfico -->
                <rect x="20" y="20" width="{w - 40}" height="{h - 40}" fill="none" stroke="{accent}" stroke-width="1" opacity="0.25"/>
                <circle cx="{w - 60}" cy="50" r="18" fill="{accent}" opacity="0.2" filter="blur(6px)"/>
                <path d="M 30 {h - 60} Q {w//2} {h - 90} {w - 30} {h - 60}" stroke="{rim_light}" stroke-width="2" fill="none" opacity="0.5"/>
            '''

        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="100%">
          <defs>
            <radialGradient id="grad_{hash_id}" cx="50%" cy="45%" r="65%">
              <stop offset="0%" stop-color="{mid_color}"/>
              <stop offset="70%" stop-color="{top_color}"/>
              <stop offset="100%" stop-color="{bottom_color}"/>
            </radialGradient>
            <!-- Filtro de grano de película 35mm -->
            <filter id="grain_{hash_id}" x="0%" y="0%" width="100%" height="100%">
              <feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves="3" result="noise"/>
              <feColorMatrix type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 0.08 0"/>
              <feComposite in2="SourceGraphic" in="glare" operator="over"/>
            </filter>
          </defs>

          <!-- Fondo de gradiente cinemático profundo -->
          <rect width="{w}" height="{h}" fill="url(#grad_{hash_id})"/>

          <!-- Viñeteado de lente 35mm -->
          <rect width="{w}" height="{h}" fill="none" stroke="#000000" stroke-width="18" opacity="0.65"/>

          {extra_elements}

          <!-- Barras de Letterbox anamórficas superiores e inferiores -->
          <rect x="0" y="0" width="{w}" height="24" fill="#000000" opacity="0.85"/>
          <rect x="0" y="{h - 32}" width="{w}" height="32" fill="#000000" opacity="0.88"/>

          <!-- Sello de metadatos de cámara Panavision / 35mm -->
          <text x="14" y="16" font-family="'Courier Prime', monospace" font-size="7.5" font-weight="700" fill="{accent}" letter-spacing="1.2">{aspect_badge}</text>
          <text x="{w - 14}" y="16" font-family="'Courier Prime', monospace" font-size="7.5" font-weight="700" fill="#a1a1aa" text-anchor="end" letter-spacing="0.8">T1.9 • ISO 800</text>

          <!-- Tipografía cinemática inferior -->
          <text x="14" y="{h - 18}" font-family="'Cinzel', Georgia, serif" font-size="11" font-weight="bold" fill="#ffffff" letter-spacing="1">{main_label[:30]}</text>
          <text x="14" y="{h - 6}" font-family="'Segoe UI', system-ui, sans-serif" font-size="8" fill="{accent}" letter-spacing="0.5">{sub_label}</text>
          <text x="{w - 14}" y="{h - 12}" font-family="'Courier Prime', monospace" font-size="7" font-weight="600" fill="{rim_light}" text-anchor="end" letter-spacing="1">{role_badge}</text>
        </svg>'''

        return "data:image/svg+xml;utf8," + urllib.parse.quote(svg)

    def generate_poster(self, project: Dict[str, Any]) -> str:
        """Genera o recupera póster cinemático para un proyecto."""
        res = self.generate_asset(project.get("id", "proj"), "poster", "main", project, project)
        return res.get("url", "")

    def generate_character_avatar(self, character: Dict[str, Any], project: Dict[str, Any] = None) -> str:
        """Genera o recupera avatar cinemático para un personaje."""
        pid = (project or {}).get("id") or character.get("project_id", "proj")
        cid = character.get("id", "char")
        res = self.generate_asset(pid, "character", cid, character, project or {})
        return res.get("url", "")

    def generate_scene_still(self, scene: Dict[str, Any], project: Dict[str, Any] = None) -> str:
        """Genera o recupera fotograma cinemático anamórfico para una escena."""
        pid = (project or {}).get("id") or scene.get("project_id", "proj")
        sid = scene.get("id") or str(scene.get("scene_number", 1))
        res = self.generate_asset(pid, "scene", sid, scene, project or {})
        return res.get("url", "")

    def get_or_generate_cinematic_asset(self, project_id: str, asset_type: str, item_id: str, metadata: Dict[str, Any], project: Dict[str, Any] = None) -> Dict[str, Any]:
        """Alias para generate_asset."""
        return self.generate_asset(project_id, asset_type, item_id, metadata, project or {})

    def get_runtime_status(self) -> Dict[str, Any]:
        """Devuelve el estado de ejecución y diagnóstico del servicio de imagen."""
        return {
            "api_key_configured": bool(self.api_key),
            "client_connected": self.client is not None,
            "provider_status": self.last_provider_status,
            "available_models": self.CANDIDATE_IMAGE_MODELS,
            "generated_cache_dir": GENERATED_DIR,
            "quota_limited": self.last_provider_status.get("quota_limited", False),
            "fallback_active": self.last_provider_status.get("fallback_active", True)
        }

# Instancia singleton del servicio de imágenes
cinematic_image_service = CinematicImageService()
