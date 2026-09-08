import os
import json
import hashlib
from typing import Dict, List, Any, Optional

class CharacterVisualIdentity:
    """Stores consistent visual identity features for a character across the entire film."""

    def __init__(
        self,
        character_name: str,
        species: str = "Humano",
        hair: str = "Castaño oscuro peinado hacia atrás estilo años 50",
        face: str = "Rasgos expresivos, mandíbula definida, mirada inquisitiva",
        eyes: str = "Ojos color ámbar vivaces",
        clothing: str = "Camisa de franela beige, tirantes de cuero marrón y pantalón de pana",
        color_palette: str = "Tonos ocres cálidos, café y crema",
        distinctive_features: str = "Pequeña peca en la mejilla izquierda y reloj de bolsillo vintage",
        silhouette: str = "Complexión delgada y ágil"
    ):
        self.character_name = character_name
        self.species = species
        self.hair = hair
        self.face = face
        self.eyes = eyes
        self.clothing = clothing
        self.color_palette = color_palette
        self.distinctive_features = distinctive_features
        self.silhouette = silhouette

    def to_prompt_fragment(self) -> str:
        return (
            f"{self.character_name} ({self.species}, {self.silhouette}, {self.hair}, {self.face}, {self.eyes}, "
            f"wearing {self.clothing} in {self.color_palette}, distinctive {self.distinctive_features})"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.character_name,
            "species": self.species,
            "hair": self.hair,
            "face": self.face,
            "eyes": self.eyes,
            "clothing": self.clothing,
            "color_palette": self.color_palette,
            "distinctive_features": self.distinctive_features,
            "silhouette": self.silhouette
        }


class VisualBible:
    """Maintains the unified visual philosophy, camera direction, color theory, and lighting rules for a film project."""

    def __init__(
        self,
        project_title: str,
        era_year: int = 1956,
        genre: str = "Misterio / Drama",
        art_style: str = "Golden Era Classic Vintage Animation Cartoon (1930s-1950s)",
        aspect_ratio: str = "1.85:1 Academy Standard",
        lighting_style: str = "Chiaroscuro high-contrast, warm tungsten shafts, dramatic volumetric dust particles",
        camera_lenses: str = "35mm prime lenses, subtle soft-focus vignette, shallow depth of field",
        color_palette: str = "Vintage Technicolor, aged parchment, deep charcoal #08090d, warm gold #d4af37, crimson accent #e50914"
    ):
        self.project_title = project_title
        self.era_year = era_year
        self.genre = genre
        self.art_style = art_style
        self.aspect_ratio = aspect_ratio
        self.lighting_style = lighting_style
        self.camera_lenses = camera_lenses
        self.color_palette = color_palette
        self.character_identities: Dict[str, CharacterVisualIdentity] = {}

    def register_character_identity(self, name: str, identity: CharacterVisualIdentity):
        self.character_identities[name] = identity

    def get_character_identity(self, name: str) -> Optional[CharacterVisualIdentity]:
        return self.character_identities.get(name)

    def generate_character_image_prompt(self, character_name: str, emotion: str = "Determined") -> str:
        ident = self.get_character_identity(character_name)
        char_desc = ident.to_prompt_fragment() if ident else f"{character_name}, {emotion}"

        prompt = (
            f"Official character concept art portrait of {char_desc}. "
            f"Style: {self.art_style}, hand-drawn 2D animation illustration, ink and gouache aesthetic, "
            f"period setting {self.era_year}. Lighting: {self.lighting_style}. "
            f"Color palette: {self.color_palette}. Aspect ratio: 1:1 bust portrait, neutral cinematic textured background. "
            f"NO 3D CGI render, NO hyper-realistic photograph, classic Golden Era animation only."
        )
        return prompt

    def generate_scene_image_prompt(
        self,
        scene_number: int,
        slugline: str,
        location: str,
        interior_exterior: str,
        day_night: str,
        characters_present: List[str],
        action_summary: str,
        environmental_details: str
    ) -> str:
        """Constructs a grounded, non-generic scene visual prompt strictly reflecting location, time of day, weather, and character visual identities."""
        # Character fragments
        chars_desc_list = []
        for c_name in characters_present:
            ident = self.get_character_identity(c_name)
            if ident:
                chars_desc_list.append(ident.to_prompt_fragment())
            else:
                chars_desc_list.append(c_name)

        chars_str = ", ".join(chars_desc_list) if chars_desc_list else "No characters visible, environment shot"

        time_lighting = (
            "Nighttime moonlight streaming through windows, deep dark shadows, high-contrast chiaroscuro, cold blue and warm amber points of light"
            if "NIGHT" in day_night.upper() or "NOCHE" in slugline.upper()
            else (
                "Golden sunset twilight, long orange-gold shadows, rich warm amber horizon"
                if "ATARDECER" in day_night.upper() or "DUSK" in slugline.upper()
                else "Bright 1950s daylight, sunbeams through dust motes, rich warm daytime exposure"
            )
        )

        setting_type = "Interior shot inside" if "INT" in interior_exterior.upper() else "Exterior outdoor wide shot of"

        prompt = (
            f"Cinematic wide film still, Scene {scene_number}: {setting_type} {location} during {day_night} ({self.era_year}). "
            f"Action taking place: {action_summary}. "
            f"Characters present: {chars_str}. "
            f"Atmosphere & Weather: {environmental_details}. Lighting: {time_lighting}. "
            f"Style: {self.art_style}, 2D vintage hand-drawn Disney/Fleischer aesthetic with rich painted gouache backgrounds, "
            f"shot on {self.camera_lenses}, {self.aspect_ratio}, film grain texture. "
            f"Color palette: {self.color_palette}. NO modern CGI, NO photorealism."
        )
        return prompt

    def generate_scene_image_url(
        self,
        scene_number: int,
        location: str,
        interior_exterior: str,
        day_night: str,
        characters_present: List[str]
    ) -> str:
        """Returns a deterministic, high-quality cinematic illustration placeholder or generates via API."""
        is_night = "NIGHT" in day_night.upper() or "NOCHE" in day_night.upper()
        is_int = "INT" in interior_exterior.upper()

        if is_int and is_night:
            # Interior Night
            urls = [
                "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=600&h=350&fit=crop", # dusty vintage room night
                "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600&h=350&fit=crop", # vintage mansion night
                "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=600&h=350&fit=crop"
            ]
        elif is_int and not is_night:
            # Interior Day
            urls = [
                "https://images.unsplash.com/photo-1505664194779-8beaceb93744?w=600&h=350&fit=crop", # vintage library day
                "https://images.unsplash.com/photo-1524758631624-e2822e304c36?w=600&h=350&fit=crop", # sunlit antique room
                "https://images.unsplash.com/photo-1541123437800-1bb1317badc2?w=600&h=350&fit=crop"
            ]
        elif not is_int and is_night:
            # Exterior Night
            urls = [
                "https://images.unsplash.com/photo-1509114397022-ed747cca3f65?w=600&h=350&fit=crop", # dark forest gate night
                "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600&h=350&fit=crop"
            ]
        else:
            # Exterior Day / Sunset
            urls = [
                "https://images.unsplash.com/photo-1448375240586-882707db888b?w=600&h=350&fit=crop", # countryside road day
                "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=600&h=350&fit=crop", # old town square day
                "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?w=600&h=350&fit=crop"
            ]

        idx = scene_number % len(urls)
        return urls[idx]
