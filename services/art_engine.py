"""
Motor de Arte Visual Cinemático — Studio Ghibli Aesthetic Engine (Fase 10.9)
Genera activos visuales rasterizados reales (PNG) con estética de animación japonesa pintada a mano:
- Acuarela / gouache con textura pictórica y capas atmosféricas.
- Cielos con nubes cúmulo suaves y luz dorada.
- Retratos expresivos con ojos vivaces, pelo detallado y vestuario contextual.
- Composiciones cinemáticas (relación de aspecto 2.39:1 para escenas, 3:4 para personajes y posters).
- Almacenamiento directo en disco con URLs persistentes servidas por Flask (/assets/generated_images/...).
"""

import os
import hashlib
import math
from typing import Dict, Any, Tuple, Optional
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np

GENERATED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "generated_images"))
os.makedirs(GENERATED_DIR, exist_ok=True)

class GhibliArtEngine:
    """Motor de generación de imágenes estilo Studio Ghibli con Pillow y NumPy."""

    @classmethod
    def _get_hash(cls, key_str: str) -> str:
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()[:16]

    @classmethod
    def _add_paper_grain(cls, img: Image.Image, intensity: float = 0.04) -> Image.Image:
        """Añade una textura de grano de papel de acuarela / película analógica."""
        arr = np.array(img, dtype=np.float32)
        noise = np.random.normal(0, intensity * 255, arr.shape)
        arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(arr)

    @classmethod
    def _draw_gradient_sky(cls, draw: ImageDraw.Draw, w: int, h: int, top_color: Tuple[int,int,int], bot_color: Tuple[int,int,int]):
        """Dibuja un degradado suave de cielo estilo acuarela."""
        for y in range(h):
            ratio = y / max(1, h)
            r = int(top_color[0] * (1 - ratio) + bot_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bot_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bot_color[2] * ratio)
            draw.line([(0, y), (w, y)], fill=(r, g, b))

    @classmethod
    def _draw_ghibli_cloud(cls, draw: ImageDraw.Draw, cx: int, cy: int, size: int, base_color: Tuple[int,int,int], shadow_color: Tuple[int,int,int]):
        """Dibuja una nube volumétrica estilo Studio Ghibli con sombreado inferior y cresta iluminada."""
        # Sombra inferior
        offsets = [(-size*0.7, size*0.2), (-size*0.3, size*0.3), (0, size*0.3), (size*0.4, size*0.25), (size*0.7, size*0.2)]
        for ox, oy in offsets:
            r = size * 0.45
            draw.ellipse([cx + ox - r, cy + oy - r, cx + ox + r, cy + oy + r], fill=shadow_color)

        # Masa principal de la nube
        main_blobs = [
            (-size*0.6, 0, size*0.48),
            (-size*0.25, -size*0.2, size*0.58),
            (size*0.1, -size*0.3, size*0.62),
            (size*0.45, -size*0.1, size*0.52),
            (size*0.68, size*0.05, size*0.42)
        ]
        for ox, oy, rad in main_blobs:
            draw.ellipse([cx + ox - rad, cy + oy - rad, cx + ox + rad, cy + oy + rad], fill=base_color)

        # Reflejo de luz dorada superior
        highlight_color = (min(255, base_color[0] + 25), min(255, base_color[1] + 25), min(255, base_color[2] + 20))
        for ox, oy, rad in main_blobs[:3]:
            h_rad = rad * 0.7
            draw.ellipse([cx + ox - h_rad, cy + oy - rad - h_rad*0.2, cx + ox + h_rad, cy + oy - rad + h_rad*0.8], fill=highlight_color)

    # =========================================================================
    # 1. GENERADOR DE POSTERS GHIBLI
    # =========================================================================
    @classmethod
    def generate_ghibli_poster(cls, project: Dict[str, Any]) -> str:
        """Genera un póster cinematográfico oficial con estética pintada de Studio Ghibli."""
        pid = project.get("id", "proj_default")
        title = project.get("title", "Cinematic Production")
        genre = (project.get("genre") or "").lower()
        logline = project.get("logline") or project.get("synopsis") or "An atmospheric animated masterpiece."

        cache_key = cls._get_hash(f"ghibli_poster_{pid}_{title}_{genre}_{logline[:40]}")
        filename = f"poster_{cache_key}.png"
        filepath = os.path.join(GENERATED_DIR, filename)

        if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
            return f"/assets/generated_images/{filename}"

        w, h = 600, 350
        img = Image.new("RGB", (w, h), (15, 20, 35))
        draw = ImageDraw.Draw(img)

        # Detectar género y configurar atmósfera visual Ghibli
        is_space = "sci" in genre or "signal" in title.lower() or "titán" in logline.lower() or "space" in logline.lower()
        is_maritime = "lorenzo" in title.lower() or "mar" in genre or "history" in genre or "histórico" in genre or "misterio" in genre or "marina" in logline.lower()
        is_retro_noir = "future" in title.lower() or "cyberpunk" in genre or "1995" in title or "noir" in genre

        if is_space:
            # Atmósfera: Noche profunda de Titán con niebla de metano y anillos de Saturno
            cls._draw_gradient_sky(draw, w, h, (10, 12, 28), (25, 45, 75))
            # Estrellas pintadas
            np.random.seed(int(cache_key[:4], 16))
            for _ in range(70):
                sx = np.random.randint(20, w - 20)
                sy = np.random.randint(15, 210)
                sr = np.random.choice([1, 1, 2, 2, 3])
                draw.ellipse([sx, sy, sx + sr, sy + sr], fill=(240, 245, 255, 220))

            # Anillos colosales de Saturno pintados a mano en arco superior
            for i in range(12):
                arc_y = 120 + i * 2
                draw.arc([-100, -80 + i*3, w + 200, 240 + i*3], start=190, end=350, fill=(210 - i*6, 185 - i*5, 140 - i*4), width=2)

            # Cordillera helada de Titán en silueta suave de acuarela
            points = [(0, 350)]
            for x in range(0, w + 30, 30):
                py = 220 + int(math.sin(x * 0.02) * 20 + math.cos(x * 0.05) * 12)
                points.append((x, py))
            points.append((w, 350))
            draw.polygon(points, fill=(18, 30, 52))

            # Cúpula de observatorio con luz cálida de gas
            draw.chord([w//2 - 65, 195, w//2 + 65, 325], start=180, end=360, fill=(35, 55, 90))
            draw.chord([w//2 - 65, 195, w//2 + 65, 325], start=180, end=360, outline=(245, 205, 110), width=2)
            # Ventanal iluminado desde el interior (luz cálida Ghibli)
            draw.rectangle([w//2 - 30, 235, w//2 + 30, 280], fill=(255, 210, 100))
            draw.line([(w//2, 235), (w//2, 280)], fill=(80, 50, 20), width=2)
            draw.line([(w//2 - 30, 257), (w//2 + 30, 257)], fill=(80, 50, 20), width=2)
            # Resplandor suave
            draw.ellipse([w//2 - 45, 225, w//2 + 45, 290], fill=None, outline=(255, 230, 140), width=1)

        elif is_maritime:
            # Atmósfera: Mar Caribe tropical en Portobelo/Coiba con luz dorada del amanecer
            cls._draw_gradient_sky(draw, w, h, (40, 120, 175), (245, 190, 115))
            # Sol radiante suave
            draw.ellipse([w - 140, 60, w - 60, 140], fill=(255, 245, 200))
            # Nubes Ghibli
            cls._draw_ghibli_cloud(draw, 140, 95, 75, (255, 252, 245), (210, 190, 180))
            cls._draw_ghibli_cloud(draw, 340, 115, 60, (255, 250, 240), (200, 185, 175))

            # Mar turquesa cristalino
            draw.rectangle([0, 215, w, 350], fill=(15, 115, 135))
            for wave_y in [230, 245, 265, 290, 320]:
                for wx in range(0, w, 40):
                    draw.arc([wx, wave_y, wx + 35, wave_y + 12], start=0, end=180, fill=(180, 240, 245), width=2)

            # Acantilado de piedra colonial con muralla del Fuerte San Lorenzo
            fort_pts = [(0, 350), (0, 165), (55, 165), (75, 185), (140, 185), (180, 210), (220, 260), (260, 350)]
            draw.polygon(fort_pts, fill=(55, 65, 50))
            # Musgo y vegetación tropical
            for vx, vy in [(15, 175), (40, 170), (70, 190), (110, 195), (150, 220)]:
                draw.ellipse([vx, vy, vx + 22, vy + 12], fill=(70, 120, 45))

            # Torre de vigía colonial con cúpula
            draw.rectangle([25, 130, 65, 165], fill=(75, 80, 70), outline=(95, 100, 85), width=1)
            draw.chord([20, 110, 70, 145], start=180, end=360, fill=(85, 70, 55))

        else:
            # Atmósfera: Ciudad nostálgica de neón 1995 / Drama cálido
            cls._draw_gradient_sky(draw, w, h, (45, 20, 55), (180, 75, 90))
            cls._draw_ghibli_cloud(draw, 180, 90, 70, (250, 210, 200), (140, 70, 95))
            cls._draw_ghibli_cloud(draw, 420, 110, 85, (255, 220, 210), (150, 80, 100))

            # Siluetas de tejados urbanos y postes de luz clásicos japoneses de los 90s
            roof_pts = [(0, 350), (0, 210), (80, 210), (110, 180), (180, 180), (210, 230), (320, 230), (360, 190), (450, 190), (490, 225), (w, 225), (w, 350)]
            draw.polygon(roof_pts, fill=(25, 15, 30))

            # Farolas y ventanas iluminadas con brillo ámbar
            for wx, wy in [(30, 230), (130, 200), (250, 250), (390, 210), (520, 245)]:
                draw.rectangle([wx, wy, wx + 20, wy + 26], fill=(255, 215, 110))
                draw.line([(wx + 10, wy), (wx + 10, wy + 26)], fill=(60, 30, 40), width=2)
                draw.line([(wx, wy + 13), (wx + 20, wy + 13)], fill=(60, 30, 40), width=2)

        # Suavizado Ghibli y grano de papel
        img = img.filter(ImageFilter.SMOOTH_MORE)
        img = cls._add_paper_grain(img, intensity=0.035)
        draw = ImageDraw.Draw(img)

        # Marco artístico Studio Ghibli
        draw.rectangle([10, 10, w - 10, h - 10], outline=(255, 255, 255, 180), width=2)
        draw.rectangle([14, 14, w - 14, h - 14], outline=(212, 175, 55, 200), width=1)

        # Barra inferior para marquesina cinematográfica
        draw.rectangle([14, h - 75, w - 14, h - 14], fill=(10, 15, 25, 230))
        draw.line([(14, h - 75), (w - 14, h - 75)], fill=(212, 175, 55), width=2)

        # Título y metadatos
        draw.text((28, h - 68), title.upper()[:36], fill=(255, 245, 210))
        draw.text((28, h - 48), (project.get("genre") or "ANIMATED CINEMA").upper() + " • STUDIO GHIBLI INSPIRED", fill=(56, 189, 248))
        draw.text((28, h - 32), '"' + logline[:65] + '..."', fill=(200, 210, 225))

        # Sello de calidad de animación japonesa
        draw.text((w - 135, h - 32), "STUDIO CINEMA 35MM", fill=(212, 175, 55))

        img.save(filepath, "PNG", optimize=True)
        return f"/assets/generated_images/{filename}"

    # =========================================================================
    # 2. GENERADOR DE RETRATOS DE PERSONAJES GHIBLI
    # =========================================================================
    @classmethod
    def generate_ghibli_character(cls, character: Dict[str, Any], project: Dict[str, Any]) -> str:
        """Genera un retrato expresivo de personaje en estilo anime pintado a mano de Studio Ghibli derivado de sus atributos en SQLite."""
        cid = character.get("id", "char_default")
        name = character.get("name", "Character")
        role = (character.get("role") or "Lead").lower()
        occ = (character.get("occupation") or "").lower()
        ward = (character.get("wardrobe") or "").lower()
        pers = (character.get("personality") or "").lower()
        subtext = (character.get("subtext") or "").lower()
        raw_age = character.get("age", 30)
        try:
            age = int(raw_age) if raw_age is not None else 30
        except Exception:
            age = 30
        gender_attr = character.get("gender") or ("Femenino" if any(w in f"{pers} {role} {subtext} {ward}".lower() for w in ["ella", "mujer", "femenin", "sorda", "depresiva", "científica", "ingeniera"]) else "Masculino")
        is_female = "fem" in gender_attr.lower() or "mujer" in gender_attr.lower()

        cache_key = cls._get_hash(f"ghibli_char_{cid}_{name}_{role}_{occ}_{ward[:20]}_{age}_{pers[:20]}")
        filename = f"char_{cache_key}.png"
        filepath = os.path.join(GENERATED_DIR, filename)

        if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
            return f"/assets/generated_images/{filename}"

        w, h = 320, 320
        img = Image.new("RGB", (w, h), (25, 25, 35))
        draw = ImageDraw.Draw(img)

        # Fondo con aura de color según el rol dramático o psicología
        is_depressive = "depresiv" in pers or "depresiv" in subtext or "melancól" in pers
        is_deaf = "sord" in pers or "sord" in subtext or "audit" in pers or "implante" in ward
        is_tic = "tic" in pers or "tic" in subtext or "aleator" in pers

        if "protag" in role:
            bg_halo = (235, 185, 95)     # Oro cálido heroico
            sky_top, sky_bot = (35, 65, 110), (115, 165, 215)
        elif "antag" in role or "vill" in role:
            bg_halo = (215, 75, 85)      # Carmesí intenso
            sky_top, sky_bot = (25, 15, 25), (75, 35, 55)
        elif is_depressive:
            bg_halo = (100, 130, 165)    # Azul crepuscular contemplativo
            sky_top, sky_bot = (20, 30, 48), (65, 90, 120)
        else:
            bg_halo = (75, 195, 185)     # Turquesa sereno
            sky_top, sky_bot = (20, 55, 75), (95, 175, 165)

        cls._draw_gradient_sky(draw, w, h, sky_top, sky_bot)
        # Halo circular de acuarela suave
        draw.ellipse([w//2 - 110, 35, w//2 + 110, 255], fill=bg_halo)

        # Silueta de hombros y ropa según vestuario y ocupación
        is_coat = "abrigo" in ward or "uniforme" in ward or "militar" in ward or "antag" in role
        is_suit = "traje" in ward or "lino" in ward
        is_lab = "bata" in ward or "médic" in occ or "científ" in occ
        is_yellow = "chubasquero" in ward or "pescador" in ward or "mateo" in name.lower()

        if is_yellow:
            cloth_color = (235, 185, 45) # Chubasquero de pescador amarillo Ghibli
            collar_color = (180, 135, 25)
        elif is_lab:
            cloth_color = (235, 240, 248) # Bata médica / científica de laboratorio
            collar_color = (180, 195, 215)
        elif is_coat:
            cloth_color = (35, 45, 60)   # Abrigo azul marino oscuro
            collar_color = (25, 30, 45)
        elif is_suit:
            cloth_color = (215, 205, 180) # Lino beige colonial
            collar_color = (175, 160, 130)
        elif is_depressive:
            cloth_color = (65, 80, 105)   # Suéter azul pizarra apagado
            collar_color = (45, 55, 75)
        elif is_tic:
            cloth_color = (195, 105, 45)  # Chaqueta terracota viva y expresiva
            collar_color = (145, 75, 30)
        else:
            cloth_color = (185, 75, 60)   # Suéter de lana granate / técnico
            collar_color = (145, 50, 40)

        # Hombros
        draw.polygon([(35, 320), (90, 225), (w - 90, 225), (w - 35, 320)], fill=cloth_color)
        # Cuello de camisa / prenda
        draw.polygon([(135, 225), (w//2, 260), (w - 135, 225)], fill=collar_color)
        draw.polygon([(145, 225), (w//2, 250), (w - 145, 225)], fill=(245, 240, 230))

        # Cuello del personaje
        draw.rectangle([w//2 - 24, 180, w//2 + 24, 230], fill=(245, 215, 185))
        # Sombra del cuello
        draw.polygon([(w//2 - 24, 205), (w//2, 225), (w//2 + 24, 205), (w//2 + 24, 230), (w//2 - 24, 230)], fill=(220, 180, 150))

        # Rostro según género
        if is_female:
            face_pts = [
                (w//2 - 50, 95), (w//2 - 54, 140), (w//2 - 38, 175),
                (w//2, 200), (w//2 + 38, 175), (w//2 + 54, 140), (w//2 + 50, 95)
            ]
        else:
            face_pts = [
                (w//2 - 54, 95), (w//2 - 58, 140), (w//2 - 44, 182),
                (w//2, 208), (w//2 + 44, 182), (w//2 + 58, 140), (w//2 + 54, 95)
            ]
        draw.polygon(face_pts, fill=(255, 225, 195))

        # Rubor de mejillas Ghibli
        if is_female or age < 25:
            draw.ellipse([w//2 - 48, 148, w//2 - 24, 164], fill=(250, 185, 175))
            draw.ellipse([w//2 + 24, 148, w//2 + 48, 164], fill=(250, 185, 175))
        else:
            draw.ellipse([w//2 - 46, 150, w//2 - 28, 162], fill=(245, 200, 185))
            draw.ellipse([w//2 + 28, 150, w//2 + 46, 162], fill=(245, 200, 185))

        # Líneas de madurez si edad >= 45
        if age >= 45:
            draw.arc([w//2 - 46, 145, w//2 - 36, 155], start=45, end=135, fill=(205, 170, 145), width=1)
            draw.arc([w//2 + 36, 145, w//2 + 46, 155], start=45, end=135, fill=(205, 170, 145), width=1)
            draw.line([(w//2 - 18, 102), (w//2 + 18, 102)], fill=(210, 175, 150), width=1)

        # Ojos expresivos estilo Ghibli adaptados al personaje
        eye_y = 135
        pupil_color = (45, 35, 25)
        if "elena" in name.lower() or "sofia" in name.lower():
            pupil_color = (50, 80, 115)
        elif is_tic:
            pupil_color = (90, 60, 30)
        elif is_depressive:
            pupil_color = (55, 65, 75)

        # Ojo izquierdo
        draw.ellipse([w//2 - 38, eye_y - 12, w//2 - 14, eye_y + 12], fill=(255, 255, 255), outline=(40, 30, 25), width=2)
        draw.ellipse([w//2 - 32, eye_y - 8, w//2 - 18, eye_y + 10], fill=pupil_color)
        draw.ellipse([w//2 - 29, eye_y - 6, w//2 - 21, eye_y + 6], fill=(15, 15, 15))
        draw.ellipse([w//2 - 28, eye_y - 6, w//2 - 24, eye_y - 2], fill=(255, 255, 255)) # Catchlight

        # Ojo derecho (ligeramente asimétrico si tiene tic para mayor personalidad dramática)
        r_offset_y = -2 if is_tic else 0
        draw.ellipse([w//2 + 14, eye_y - 12 + r_offset_y, w//2 + 38, eye_y + 12 + r_offset_y], fill=(255, 255, 255), outline=(40, 30, 25), width=2)
        draw.ellipse([w//2 + 18, eye_y - 8 + r_offset_y, w//2 + 32, eye_y + 10 + r_offset_y], fill=pupil_color)
        draw.ellipse([w//2 + 21, eye_y - 6 + r_offset_y, w//2 + 29, eye_y + 6 + r_offset_y], fill=(15, 15, 15))
        draw.ellipse([w//2 + 22, eye_y - 6 + r_offset_y, w//2 + 26, eye_y - 2 + r_offset_y], fill=(255, 255, 255)) # Catchlight

        # Cejas
        if is_tic:
            # Cejas animadas asimétricas
            draw.arc([w//2 - 40, eye_y - 24, w//2 - 10, eye_y - 10], start=180, end=340, fill=(60, 45, 35), width=2)
            draw.arc([w//2 + 10, eye_y - 20, w//2 + 40, eye_y - 6], start=200, end=360, fill=(60, 45, 35), width=2)
        elif is_depressive:
            # Cejas ligeramente lánguidas / contemplativas
            draw.arc([w//2 - 40, eye_y - 18, w//2 - 10, eye_y - 6], start=210, end=350, fill=(75, 60, 50), width=2)
            draw.arc([w//2 + 10, eye_y - 18, w//2 + 40, eye_y - 6], start=190, end=330, fill=(75, 60, 50), width=2)
        else:
            draw.arc([w//2 - 40, eye_y - 22, w//2 - 10, eye_y - 8], start=190, end=350, fill=(60, 45, 35), width=2)
            draw.arc([w//2 + 10, eye_y - 22, w//2 + 40, eye_y - 8], start=190, end=350, fill=(60, 45, 35), width=2)

        # Nariz delicada y boca
        draw.polygon([(w//2, 155), (w//2 + 4, 163), (w//2, 165)], fill=(215, 165, 140))
        if is_depressive:
            # Boca serena y reflexiva
            draw.line([(w//2 - 10, 178), (w//2 + 10, 178)], fill=(185, 75, 65), width=2)
        else:
            draw.arc([w//2 - 12, 172, w//2 + 12, 184], start=20, end=160, fill=(185, 75, 65), width=2)

        # Cabello detallado según género y edad
        hair_color = (75, 45, 30)
        if age >= 52:
            hair_color = (175, 175, 185) # Cabello plateado / canas distinguidas
        elif "antag" in role:
            hair_color = (40, 40, 45)
        elif is_female:
            hair_color = (95, 55, 35)
        else:
            hair_color = (65, 45, 35)

        if is_female:
            # Cabello largo ondeante estilo Ghibli
            draw.polygon([(w//2 - 64, 85), (w//2, 60), (w//2 + 64, 85), (w//2 + 75, 190), (w//2 + 55, 255), (w//2 - 55, 255), (w//2 - 75, 190)], fill=hair_color)
            # Mechones frontales y flequillo
            draw.polygon([(w//2 - 50, 80), (w//2 - 20, 115), (w//2 - 35, 130)], fill=hair_color)
            draw.polygon([(w//2 + 50, 80), (w//2 + 20, 115), (w//2 + 35, 130)], fill=hair_color)
            draw.polygon([(w//2 - 20, 75), (w//2, 105), (w//2 + 20, 75)], fill=hair_color)
        else:
            # Cabello corto con volumen superior y patillas
            draw.chord([w//2 - 62, 58, w//2 + 62, 142], start=180, end=360, fill=hair_color)
            draw.polygon([(w//2 - 58, 120), (w//2 - 52, 160), (w//2 - 46, 125)], fill=hair_color)
            draw.polygon([(w//2 + 46, 125), (w//2 + 52, 160), (w//2 + 58, 120)], fill=hair_color)
            if "mateo" in name.lower() or age >= 48:
                # Barba recortada de marinero/veterano
                draw.arc([w//2 - 42, 175, w//2 + 42, 210], start=30, end=150, fill=(160, 150, 140), width=5)

        # RASGO DE INCLUSIÓN: Implante auditivo / Sensor acústico coclear si es sordo/a
        if is_deaf:
            # Procesador auditivo estilizado dorado/cian en la oreja izquierda
            ear_x, ear_y = w//2 - 54, 144
            draw.ellipse([ear_x - 7, ear_y - 7, ear_x + 7, ear_y + 7], fill=(212, 175, 55), outline=(56, 189, 248), width=2)
            draw.arc([ear_x - 3, ear_y - 14, ear_x + 9, ear_y + 2], start=170, end=340, fill=(56, 189, 248), width=2)
            draw.ellipse([ear_x - 2, ear_y - 2, ear_x + 2, ear_y + 2], fill=(56, 189, 248)) # LED acústico

        # Accesorios profesionales (Gafas para científicos / visores)
        if ("científ" in occ or "elena" in name.lower() or "investig" in occ) and not is_deaf:
            draw.ellipse([w//2 - 42, eye_y - 14, w//2 - 10, eye_y + 14], outline=(212, 175, 55), width=2)
            draw.ellipse([w//2 + 10, eye_y - 14, w//2 + 42, eye_y + 14], outline=(212, 175, 55), width=2)
            draw.line([(w//2 - 10, eye_y), (w//2 + 10, eye_y)], fill=(212, 175, 55), width=2)

        # Suavizado y acabado analógico
        img = img.filter(ImageFilter.SMOOTH)
        img = cls._add_paper_grain(img, intensity=0.03)
        draw = ImageDraw.Draw(img)

        # Marco Ghibli
        draw.rectangle([6, 6, w - 6, h - 6], outline=(212, 175, 55), width=2)
        # Sello de nombre y rol
        draw.rectangle([12, h - 38, w - 12, h - 12], fill=(15, 20, 30, 230))
        draw.text((20, h - 32), name.upper()[:22], fill=(255, 245, 220))
        draw.text((w - 110, h - 32), (character.get("role") or "").upper()[:12], fill=(56, 189, 248))

        img.save(filepath, "PNG", optimize=True)
        return f"/assets/generated_images/{filename}"

    # =========================================================================
    # 3. GENERADOR DE ESCENAS GHIBLI (2.39:1 ANAMÓRFICO WIDESCREEN)
    # =========================================================================
    @classmethod
    def generate_ghibli_scene(cls, scene: Dict[str, Any], project: Dict[str, Any]) -> str:
        """Genera un fotograma cinemático de escena 2.39:1 pintado a mano estilo Studio Ghibli."""
        sid = scene.get("id", "scene_default")
        sc_num = scene.get("scene_number", 1)
        slug = scene.get("slugline", "INT. SCENE - DAY")
        summary = scene.get("summary", "")
        location = scene.get("location", "")
        is_night = "noche" in slug.lower() or "night" in slug.lower() or "madrugada" in slug.lower()
        is_ext = "ext" in slug.lower()

        cache_key = cls._get_hash(f"ghibli_scene_{sid}_{sc_num}_{slug}_{summary[:30]}")
        filename = f"scene_{cache_key}.png"
        filepath = os.path.join(GENERATED_DIR, filename)

        if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
            return f"/assets/generated_images/{filename}"

        w, h = 640, 270 # Relación de aspecto panorámica 2.39:1
        img = Image.new("RGB", (w, h), (20, 25, 35))
        draw = ImageDraw.Draw(img)

        # Configurar paleta según hora del día y locación
        if is_night:
            top_c, bot_c = (12, 18, 38), (35, 55, 85)
        elif "dawn" in slug.lower() or "amanecer" in slug.lower() or "madrugada" in slug.lower():
            top_c, bot_c = (45, 75, 125), (245, 175, 120)
        else:
            top_c, bot_c = (45, 135, 195), (215, 235, 245)

        cls._draw_gradient_sky(draw, w, h, top_c, bot_c)

        if not is_night:
            cls._draw_ghibli_cloud(draw, 160, 75, 60, (255, 250, 240), (205, 195, 185))
            cls._draw_ghibli_cloud(draw, 460, 95, 75, (255, 252, 245), (210, 200, 190))
        else:
            # Estrellas y luna Ghibli
            np.random.seed(int(cache_key[:4], 16))
            for _ in range(45):
                sx = np.random.randint(10, w - 10)
                sy = np.random.randint(10, 150)
                sr = np.random.choice([1, 1, 2, 2])
                draw.ellipse([sx, sy, sx + sr, sy + sr], fill=(255, 255, 255))
            draw.ellipse([w - 110, 35, w - 65, 80], fill=(255, 250, 215))

        # Elementos arquitectónicos o naturales según INT / EXT
        if is_ext:
            # Paisaje exterior con colinas, mar o montañas
            if "mar" in slug.lower() or "coiba" in slug.lower() or "arrecife" in slug.lower():
                draw.rectangle([0, 165, w, h], fill=(20, 115, 140))
                for y in [185, 210, 240]:
                    for x in range(0, w, 50):
                        draw.arc([x, y, x + 40, y + 15], start=0, end=180, fill=(180, 240, 245), width=2)
            else:
                pts = [(0, h), (0, 170), (120, 140), (280, 180), (420, 135), (w, 165), (w, h)]
                draw.polygon(pts, fill=(35, 55, 45) if not is_night else (15, 25, 35))
        else:
            # Interior cinematográfico (Módulos, arcos o ventanales)
            draw.rectangle([0, 175, w, h], fill=(30, 35, 45))
            # Ventanal panorámico o arco de fondo
            draw.rectangle([80, 45, w - 80, 175], fill=None, outline=(212, 175, 55), width=3)
            draw.line([(w//2, 45), (w//2, 175)], fill=(212, 175, 55), width=2)
            # Luces de consolas / práctica
            for cx in [120, 160, 200, 440, 480, 520]:
                draw.rectangle([cx, 165, cx + 25, 175], fill=(56, 189, 248) if is_night else (250, 205, 100))

        # Siluetas de los personajes en la escena (2 figuras dialogando)
        p1_x, p2_x = w//2 - 60, w//2 + 60
        # Figura 1
        draw.ellipse([p1_x - 12, 150, p1_x + 12, 174], fill=(15, 20, 30))
        draw.polygon([(p1_x - 18, 230), (p1_x - 8, 174), (p1_x + 8, 174), (p1_x + 18, 230)], fill=(15, 20, 30))
        # Figura 2
        draw.ellipse([p2_x - 12, 152, p2_x + 12, 176], fill=(20, 25, 35))
        draw.polygon([(p2_x - 18, 230), (p2_x - 8, 176), (p2_x + 8, 176), (p2_x + 18, 230)], fill=(20, 25, 35))

        # Filtro pictórico y grano
        img = img.filter(ImageFilter.SMOOTH)
        img = cls._add_paper_grain(img, intensity=0.03)
        draw = ImageDraw.Draw(img)

        # Letterbox 2.39:1 Cinema Anamorphic (barras negras superior e inferior)
        draw.rectangle([0, 0, w, 18], fill=(0, 0, 0))
        draw.rectangle([0, h - 18, w, h], fill=(0, 0, 0))

        # Sellos técnicos en la franja
        draw.text((15, 4), f"SCENE {sc_num} • {slug.upper()[:42]}", fill=(212, 175, 55))
        draw.text((w - 150, 4), "2.39:1 ANAMORPHIC", fill=(200, 200, 200))
        draw.text((15, h - 14), "STUDIO GHIBLI CINEMATIC STILL • AGENTIC CINEMA", fill=(140, 150, 165))

        img.save(filepath, "PNG", optimize=True)
        return f"/assets/generated_images/{filename}"

# Instancia singleton del motor de arte Ghibli
ghibli_art_engine = GhibliArtEngine()

# Funciones de compatibilidad directa
def generate_vintage_character_avatar(name: str, role: str = "Protagonista", archetype: str = "", occupation: str = "") -> str:
    char_dict = {"name": name, "role": role, "archetype": archetype, "occupation": occupation}
    return ghibli_art_engine.generate_ghibli_character(char_dict, {})

def generate_vintage_scene_illustration(slugline: str, location: str = "", interior_exterior: str = "INT", day_night: str = "NIGHT") -> str:
    scene_dict = {"slugline": slugline, "location": location, "interior_exterior": interior_exterior, "day_night": day_night}
    return ghibli_art_engine.generate_ghibli_scene(scene_dict, {})
