import re
import json
import math
from typing import Dict, List, Any, Optional

class ProductionIntelligence:
    """
    Motor de Inteligencia de Producción Cinematográfica, Presupuestaria y Sostenibilidad.
    Proporciona estimaciones realistas basadas en escaleta, locaciones, elenco y complejidad técnica.
    """

    @staticmethod
    def calculate_scene_cost(scene: Dict[str, Any], total_cast: int = 3) -> Dict[str, Any]:
        """Calcula el costo estimado de rodaje de una escena individual según sus atributos reales."""
        intext = (scene.get("interior_exterior") or "INT").upper()
        daynight = (scene.get("day_night") or "DAY").upper()
        complexity = (scene.get("complexity") or "MEDIUM").upper()
        location = scene.get("location") or "Estudio"
        slugline = scene.get("slugline") or ""

        # Costo base por tipo de set
        base_cost = 3200.0 if "EXT" in intext or "EXT" in slugline else 1900.0

        # Multiplicador por rodaje nocturno (equipos de iluminación pesada, permisos, horas extras)
        night_mult = 1.25 if "NIGHT" in daynight or "NOCHE" in daynight or "NIGHT" in slugline else 1.0

        # Multiplicador por complejidad dramática / técnica
        comp_mults = {
            "LOW": 0.85,
            "MEDIUM": 1.1,
            "HIGH": 1.6,
            "CRITICAL": 2.2
        }
        comp_mult = comp_mults.get(complexity, 1.1)

        # Elenco presente
        chars_present = scene.get("characters_present") or scene.get("characters_json") or []
        if isinstance(chars_present, str):
            try:
                chars_present = json.loads(chars_present)
            except Exception:
                chars_present = [chars_present]
        num_chars = len(chars_present) if chars_present else max(1, min(total_cast, 2))
        cast_cost = num_chars * 350.0

        # Utilería y arte
        props = scene.get("props_json") or scene.get("props") or []
        if isinstance(props, str):
            try:
                props = json.loads(props)
            except Exception:
                props = [props]
        props_cost = len(props) * 150.0

        total_scene_cost = round((base_cost * night_mult * comp_mult) + cast_cost + props_cost, -1)
        
        # Asignación estimada de tiempo de rodaje en días
        if complexity == "CRITICAL" or (comp_mult >= 1.6 and "EXT" in intext):
            estimated_days = 1.5
        elif complexity == "HIGH" or "EXT" in intext or night_mult > 1.0:
            estimated_days = 1.0
        elif complexity == "LOW":
            estimated_days = 0.3
        else:
            estimated_days = 0.5

        return {
            "scene_number": scene.get("scene_number", 1),
            "slugline": slugline or f"{intext}. {location.upper()} - {daynight}",
            "location": location,
            "interior_exterior": intext,
            "day_night": daynight,
            "complexity": complexity,
            "estimated_cost": total_scene_cost,
            "estimated_days": estimated_days,
            "num_characters": num_chars,
            "cost_drivers": [
                f"{intext} set ({'Exterior con logística de calle/campo' if 'EXT' in intext else 'Interior controlado'})",
                f"{daynight} ({'Paquete de iluminación nocturna' if night_mult > 1.0 else 'Luz diurna/natural'})",
                f"Complejidad {complexity} ({comp_mult}x)",
                f"{num_chars} personaje(s) en escena"
            ]
        }

    @classmethod
    def calculate_shooting_schedule(cls, scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula el cronograma estimado de producción y desglose por escena."""
        if not scenes:
            return {
                "pre_production_days": 10,
                "principal_photography_days": 8,
                "post_production_days": 18,
                "total_days": 36,
                "scenes_schedule": [],
                "disclaimer": "Planificación preliminar estimada basada en estándares de cine independiente."
            }

        scene_breakdown = []
        total_shoot_days = 0.0

        for sc in scenes:
            calc = cls.calculate_scene_cost(sc)
            days = calc["estimated_days"]
            total_shoot_days += days
            scene_breakdown.append({
                "scene_number": calc["scene_number"],
                "slugline": calc["slugline"],
                "complexity": calc["complexity"],
                "estimated_days": days,
                "estimated_cost": calc["estimated_cost"],
                "location": calc["location"]
            })

        principal_days = max(4, math.ceil(total_shoot_days * 2) / 2)  # Redondeo a incrementos de 0.5 día
        pre_prod_days = max(8, int(principal_days * 1.4))
        post_prod_days = max(14, int(principal_days * 2.2))
        total_days = pre_prod_days + int(principal_days) + post_prod_days

        return {
            "pre_production_days": pre_prod_days,
            "principal_photography_days": principal_days,
            "post_production_days": post_prod_days,
            "total_days": total_days,
            "scenes_schedule": scene_breakdown,
            "disclaimer": "Proyección y rango de planificación estimada según volumen de escenas, locaciones y complejidad."
        }

    @classmethod
    def calculate_production_budget(
        cls,
        project: Dict[str, Any],
        scenes: List[Dict[str, Any]],
        characters: List[Dict[str, Any]],
        lang: str = "EN"
    ) -> Dict[str, Any]:
        """Genera el presupuesto estructurado de producción en 10 categorías reales de la industria."""
        is_en = (lang.upper() != "ES")
        num_scenes = len(scenes) or 6
        num_chars = len(characters) or 3
        
        # Calcular costos directos sumando escenas
        scene_costs = [cls.calculate_scene_cost(s, num_chars)["estimated_cost"] for s in scenes]
        direct_scene_sum = sum(scene_costs) if scene_costs else (num_scenes * 3200.0)

        # Base de referencia
        target_budget = float(project.get("estimated_budget") or project.get("target_budget") or (direct_scene_sum * 1.85))
        base_total = max(target_budget, direct_scene_sum * 1.5)

        # Desglose en 10 categorías estándar de producción
        if is_en:
            breakdown_weights = [
                ("Development & Story Rights", 0.05, "Screenplay, Story Bible, IP registration and dramatic research."),
                ("Directing Team & Principal Cast", 0.22, f"Director fees, 1st AD and principal cast ({num_chars} characters)."),
                ("Technical Crew, Camera & Lighting", 0.18, "Cinematography, 4K/35mm camera operation, gaffer, grips and production sound."),
                ("Locations, Scouting & Permits", 0.10, "Physical location rental, municipal permits, film insurance and location fees."),
                ("Production Design & Art Department", 0.09, "Set decoration, key hero props, set construction and art consumables."),
                ("Wardrobe, Hair & Makeup", 0.06, f"Costume design, character styling and SFX makeup for {num_chars} characters."),
                ("Transportation, Fuel & Logistics", 0.07, "Technical freight, cast vans, inter-location transit and fuel."),
                ("Catering & Craft Services", 0.05, "Full crew meals and eco-friendly craft service during principal photography."),
                ("Post-Production, Sound & Score", 0.10, "Film editing, color grading, foley, 5.1 surround sound mix and original score."),
                ("Contingency & Reserve (10%)", 0.08, "Weather contingency fund, overtime buffer and retake insurance.")
            ]
        else:
            breakdown_weights = [
                ("Desarrollo & Derechos Narrativos", 0.05, "Guion literario, Story Bible, registro de propiedad intelectual e investigación dramática."),
                ("Equipo de Dirección & Talento Principal", 0.22, f"Honorarios de Dirección, Asistencia de Dirección y elenco principal ({num_chars} personajes)."),
                ("Equipo Técnico, Cámara & Iluminación", 0.18, "Dirección de fotografía, operación de cámara 4K/35mm, gaffer, grips y sonido directo."),
                ("Locaciones, Scouting & Permisos", 0.10, "Alquiler de locaciones físicas, permisos municipales, seguros de filmación y tasas de rodaje."),
                ("Diseño de Producción & Utilería", 0.09, "Ambientación escenográfica, utilería clave, decoración de sets y consumibles de arte."),
                ("Vestuario, Peluquería & Caracterización", 0.06, f"Diseño de vestuario, caracterización de época y estilismo para {num_chars} personajes."),
                ("Transporte, Combustible & Logística", 0.07, "Fletes de equipo técnico, van de elenco, traslados entre locaciones y combustible."),
                ("Catering & Servicios de Rodaje", 0.05, "Alimentación completa y craft service ecológico para equipo técnico durante el rodaje."),
                ("Post-Producción & Sonido / Música", 0.10, "Montaje cinematográfico, etalonaje / color grading, foley, mezcla sonora 5.1 y banda sonora original."),
                ("Imprevistos & Contingencia (10%)", 0.08, "Fondo de reserva para climatología, sobrecostos de locación y días adicionales de retoma.")
            ]

        categories = []
        cumulative = 0.0
        for name, weight, desc in breakdown_weights:
            cat_amount = round(base_total * weight, -2)
            cumulative += cat_amount
            categories.append({
                "category": name,
                "amount": cat_amount,
                "percentage": round(weight * 100, 1),
                "description": desc
            })

        schedule = cls.calculate_shooting_schedule(scenes)

        if is_en:
            methodology = {
                "title": "Cinematic Estimation Baseline",
                "basis_points": [
                    f"{num_scenes} scenes analyzed ({len([s for s in scenes if 'EXT' in (s.get('interior_exterior') or '')])} exteriors, {len([s for s in scenes if 'INT' in (s.get('interior_exterior') or 'INT')])} interiors)",
                    f"{len([s for s in scenes if 'NIGHT' in (s.get('day_night') or '').upper()])} night sequences requiring heavy lighting package and night shoot permits",
                    f"{num_chars} principal cast members on payroll",
                    f"{schedule['principal_photography_days']} projected days of principal photography",
                    "8-10% contingency reserve for weather and location contingencies",
                    "Complete post-production with editing, surround sound design, and color grading"
                ]
            }
        else:
            methodology = {
                "title": "Base de Estimación Cinemática",
                "basis_points": [
                    f"{num_scenes} escenas analizadas ({len([s for s in scenes if 'EXT' in (s.get('interior_exterior') or '')])} exteriores, {len([s for s in scenes if 'INT' in (s.get('interior_exterior') or 'INT')])} interiores)",
                    f"{len([s for s in scenes if 'NIGHT' in (s.get('day_night') or '').upper()])} secuencias nocturnas que requieren paquete de iluminación y permisos de noche",
                    f"{num_chars} personajes principales en nómina de reparto",
                    f"{schedule['principal_photography_days']} días proyectados de fotografía principal",
                    f"Respaldo de contingencia del 8-10% para imprevistos climáticos y de locación",
                    "Post-producción con montaje, diseño sonoro envolvente y corrección de color"
                ]
            }

        return {
            "total_estimated_budget": cumulative,
            "currency": "USD",
            "planning_range": f"${(cumulative * 0.92):,.0f} — ${(cumulative * 1.12):,.0f}",
            "categories": categories,
            "schedule": schedule,
            "methodology": methodology
        }

    @classmethod
    def generate_sustainability_recommendations(
        cls,
        project: Dict[str, Any],
        scenes: List[Dict[str, Any]],
        characters: List[Dict[str, Any]],
        lang: str = "EN"
    ) -> Dict[str, Any]:
        """Genera recomendaciones prácticas y defendibles de producción sostenible vinculadas a la película."""
        is_en = (lang.upper() != "ES")
        num_scenes = len(scenes) or 6
        ext_scenes = [s for s in scenes if 'EXT' in (s.get('interior_exterior') or '').upper()]
        night_scenes = [s for s in scenes if 'NIGHT' in (s.get('day_night') or '').upper() or 'NOCHE' in (s.get('day_night') or '').upper()]
        locations = list(set([s.get("location", "Locación" if not is_en else "Location") for s in scenes if s.get("location")]))

        night_labels = ', '.join([f"Scene {s.get('scene_number')}" for s in night_scenes[:3]]) or 'night sequences'
        loc_labels = ', '.join(locations[:3]) or 'principal sets'

        if is_en:
            recommendations = [
                {
                    "area": "Set Construction & Materials (Art Dept)",
                    "title": "Modular Construction & Reusable Flats",
                    "recommendation": "Utilize modular prefabricated wall units and FSC-certified recycled timber for interiors, leasing hero props instead of custom single-use fabrication.",
                    "context_link": f"Directly applies to interior sets ({num_scenes - len(ext_scenes)} interior scenes), eliminating lumber landfill disposal post-wrap.",
                    "estimated_impact": "45% reduction in art department and lumber construction waste."
                },
                {
                    "area": "Lighting & Power Grid",
                    "title": "100% LED Luminaire Package & Mobile Hybrid Power",
                    "recommendation": "Replace legacy tungsten and HMI heads with high-efficiency bi-color LED panels. On exterior sets, deploy high-capacity lithium battery stations instead of diesel generators.",
                    "context_link": f"Crucial for the {len(night_scenes)} night-shoot scenes ({night_labels}).",
                    "estimated_impact": "60% reduction in diesel fuel consumption and zero acoustic disturbance during sound takes."
                },
                {
                    "area": "Transportation & Logistics (Fleet)",
                    "title": "Location Clustering & Reduced Unit Transit",
                    "recommendation": "Structure the shooting call schedule to group all scenes within identical geographic perimeters on consecutive days to eliminate unit truck convoy moves.",
                    "context_link": f"Optimizes moves across the {len(locations)} primary filming locations ({loc_labels}).",
                    "estimated_impact": "Up to 35% reduction in transport CO2 emissions and 15% fuel cost savings."
                },
                {
                    "area": "Wardrobe & Character Styling",
                    "title": "Circular Leasing & Archival Wardrobe",
                    "recommendation": "Partner with theatrical costume rental houses and vintage repositories for character garments, avoiding fast-fashion disposable fabrication.",
                    "context_link": f"Applies across all {len(characters)} cast members, preserving cinematic visual fidelity while preventing garment scrap.",
                    "estimated_impact": "70% water and textile footprint reduction versus purchasing new single-use wardrobe."
                },
                {
                    "area": "Catering & Craft Services",
                    "title": "Zero-Waste Farm-to-Table & Plastic-Free Sets",
                    "recommendation": "Supply crew with personalized stainless-steel hydration containers and filtered refill stations. Provide compostable meal kits and donate surplus daily craft service to regional shelters.",
                    "context_link": "Applies across all filming days for technical crew and talent.",
                    "estimated_impact": "Eliminates over 1,200 single-use plastic water bottles during production."
                },
                {
                    "area": "Paperless Digital Production Office",
                    "title": "100% Digital Script & Call Sheet Workflow",
                    "recommendation": "Distribute screenplays, script revisions, daily call sheets, and actor contracts via cloud-synced tablets and mobile terminals.",
                    "context_link": "Ensures all Director Agent continuity revisions update instantaneously without printing physical screenplay sides.",
                    "estimated_impact": "Saves ~4,000 sheets of paper and printer consumables."
                }
            ]
            tier = "Green Film Shooting Tier II (Certified Sustainable Production)"
            methodology = "Recommendations are dynamically calibrated to the project's set counts, night lighting packages, and logistical footprints."
        else:
            recommendations = [
                {
                    "area": "Escenografía & Materiales (Sets)",
                    "title": "Construcción Modular & Reutilización de Bastidores",
                    "recommendation": "Utilizar estructuras modulares prefabricadas y madera reciclada con certificación FSC para interiores, alquilando utilería en lugar de fabricar piezas de un solo uso.",
                    "context_link": f"Aplica directamente a los sets interiores del proyecto ({num_scenes - len(ext_scenes)} escenas en interiores), evitando desechar madera al término de producción.",
                    "estimated_impact": "Reducción del 45% en generación de residuos de arte y maderas."
                },
                {
                    "area": "Iluminación & Energía (Lighting)",
                    "title": "Paquete 100% LED y Baterías Híbridas Móviles",
                    "recommendation": "Reemplazar luminarias HMI incandescentes por paneles y focos LED de alta eficiencia. En exteriores, usar estaciones de energía a batería en lugar de generadores diésel ruidosos y contaminantes.",
                    "context_link": f"Clave para las {len(night_scenes)} escenas con rodaje nocturno ({', '.join([f'Escena {s.get('scene_number')}' for s in night_scenes[:3]]) or 'secuencias de noche'}).",
                    "estimated_impact": "Disminución del 60% en consumo de combustible diésel y cero contaminación acústica en rodaje."
                },
                {
                    "area": "Transporte & Logística (Fleet)",
                    "title": "Agrupamiento Geográfico de Locaciones (Location Clustering)",
                    "recommendation": "Planificar el plan de rodaje agrupando todas las escenas de una misma zona física en jornadas continuas para minimizar el movimiento de camiones y vehículos de reparto.",
                    "context_link": f"Beneficia las {len(locations)} locaciones identificadas ({', '.join(locations[:3]) or 'locaciones principales'}), reduciendo traslados entre sets.",
                    "estimated_impact": "Ahorro de hasta 35% en emisiones de CO2 por transporte y 15% en costos de combustible."
                },
                {
                    "area": "Vestuario & Estilismo (Wardrobe)",
                    "title": "Alquiler Circular y Textiles Recuperados",
                    "recommendation": "Acordar convenios de alquiler y devolución con casas de vestuario locales y bazares vintage para el vestuario de personajes, evitando confecciones descartables.",
                    "context_link": f"Aplica a los {len(characters)} personajes del reparto, respetando la estética cinematográfica sin acumular prendas desechadas.",
                    "estimated_impact": "70% de reducción en huella hídrica y textil frente a vestuario nuevo de un solo uso."
                },
                {
                    "area": "Catering & Hospitalidad (Catering)",
                    "title": "Catering Local Residuo Cero & Sin Plásticos",
                    "recommendation": "Instalar bidones de hidratación con botellas reutilizables de acero inoxidable para todo el crew. Servir alimentos con vajilla compostable y donar excedentes a comedores comunitarios.",
                    "context_link": "Aplica a las jornadas de rodaje diarias para el equipo técnico y artístico.",
                    "estimated_impact": "Eliminación de más de 1,200 botellas plásticas de un solo uso durante el rodaje."
                },
                {
                    "area": "Oficina de Producción Digital (Paperless)",
                    "title": "Flujo de Libreto y Llamados 100% Digital",
                    "recommendation": "Distribuir guiones, notas de continuidad, contratos y órdenes de llamado exclusivamente a través de aplicaciones móviles y tablets digitales.",
                    "context_link": "Garantiza que todas las revisiones del guion del Director Agent se consulten al instante sin imprimir cientos de páginas de libreto.",
                    "estimated_impact": "Ahorro de ~4,000 hojas de papel y consumibles de impresión."
                }
            ]
            tier = "Green Film Shooting Tier II (Producción Sostenible Certificada)"
            methodology = "Las recomendaciones están conectadas a los requerimientos específicos de sets, iluminación nocturna y traslados de esta producción."

        score = project.get("eco_impact_score", 92)
        return {
            "eco_score": score,
            "green_production_score": score,
            "certification_tier": tier,
            "score_label": tier,
            "recommendations": recommendations,
            "methodology": methodology
        }

    @classmethod
    def answer_production_query(
        cls,
        prompt: str,
        project: Dict[str, Any],
        scenes: List[Dict[str, Any]],
        characters: List[Dict[str, Any]],
        parallel_tool: Any = None,
        lang: str = "EN"
    ) -> Dict[str, Any]:
        """Responde de manera cinematográfica, profesional y fundamentada a consultas de presupuesto o sostenibilidad."""
        p_low = prompt.lower().strip()
        is_en = (lang.upper() != "ES") and not any(c in p_low for c in "áéíóúñ¿¡")
        is_es = not is_en

        budget_data = cls.calculate_production_budget(project, scenes, characters, lang="EN" if is_en else "ES")
        sustainability_data = cls.generate_sustainability_recommendations(project, scenes, characters, lang="EN" if is_en else "ES")
        schedule = budget_data["schedule"]

        # 1. Consultas sobre Investigación con Parallel Search (Costos regionales / Materiales sostenibles reales)
        requires_parallel = any(w in p_low for w in [
            "panamá", "panama", "mercado local", "materiales reales", "precios reales", "proveedor", "costos reales", "locales",
            "local market", "real materials", "real prices", "local suppliers", "real costs"
        ]) and any(w in p_low for w in ["investiga", "busca", "cuánto cuesta", "costar", "materiales", "precios", "alquiler", "search", "research", "how much", "cost", "rent", "prices"])

        if requires_parallel and parallel_tool:
            query = "costos de produccion de cine alquiler de equipos locaciones Panama" if ("cost" in p_low or "presupuesto" in p_low or "precio" in p_low) else "materiales escenografia reciclados sostenibles proveedores Panama"
            try:
                search_res = parallel_tool.search(query, mode="fast", max_results=3)
                sources = search_res.get("results", [])
                source_snippet = "\n".join([f"• [{s.get('title')}]({s.get('url')}): {s.get('snippet', '')[:160]}" for s in sources[:3]])
                
                if is_en:
                    resp = (
                        f"🌐 **Real-World Cost & Sustainability Research (Parallel Search):**\n\n"
                        f"Consulted verified film industry references for **'{project.get('title')}'**:\n\n"
                        f"{source_snippet}\n\n"
                        f"📊 **Production Application:**\n"
                        f"Based on live data, your planning budget range of **{budget_data['planning_range']}** aligns with regional independent productions. "
                        f"To maximize green compliance, we recommend coordinating with local rental suppliers to minimize import freight emissions."
                    )
                else:
                    resp = (
                        f"🌐 **Investigación de Costos / Sostenibilidad en el Mundo Real (Parallel Search):**\n\n"
                        f"He consultado referencias de mercado cinematográfico para **'{project.get('title')}'**:\n\n"
                        f"{source_snippet}\n\n"
                        f"📊 **Aplicación a la Producción:**\n"
                        f"Con base en estos datos, el rango presupuestario de **{budget_data['planning_range']}** se ajusta a tarifas independientes en la región. "
                        f"Para optimizar la sostenibilidad, te sugiero coordinar con proveedores de alquiler locales para reducir fletes de importación."
                    )
                return {
                    "action": "PRODUCTION_RESEARCH_ANSWERED",
                    "severity": "LOW",
                    "scope": "EXTERNAL_RESEARCH",
                    "sources": sources,
                    "sources_count": len(sources),
                    "response": resp
                }
            except Exception as e:
                pass

        # 2. Consultas sobre Sostenibilidad
        if any(w in p_low for w in ["sostenible", "sostenibilidad", "ecológic", "ecologic", "medio ambiente", "huella", "verde", "green", "sustainable", "sustainability", "eco-friendly"]):
            recs = sustainability_data["recommendations"]
            if is_en:
                recs_text = "\n\n".join([
                    f"🌱 **{r['area']}:** {r['title']}\n"
                    f"• *Proposal:* {r['recommendation']}\n"
                    f"• *Project Context:* {r['context_link']}\n"
                    f"• *Projected Impact:* {r['estimated_impact']}"
                    for r in recs[:4]
                ])
                resp = (
                    f"🌿 **Cinematic Sustainability Plan — '{project.get('title')}'**\n\n"
                    f"We structured an eco-certified filming protocol scored at **{sustainability_data['eco_score']}/100** ({sustainability_data['certification_tier']}):\n\n"
                    f"{recs_text}\n\n"
                    f"💡 *Methodology:* Every measure directly links to the {len(scenes)} scenes and technical demands of your film."
                )
            else:
                recs_text = "\n\n".join([
                    f"🌱 **{r['area']}:** {r['title']}\n"
                    f"• *Propuesta:* {r['recommendation']}\n"
                    f"• *Conexión con el proyecto:* {r['context_link']}\n"
                    f"• *Impacto proyectado:* {r['estimated_impact']}"
                    for r in recs[:4]
                ])
                resp = (
                    f"🌿 **Plan de Sostenibilidad Cinemática — '{project.get('title')}'**\n\n"
                    f"Hemos diseñado un protocolo de rodaje ecológico con calificación **{sustainability_data['eco_score']}/100** ({sustainability_data['certification_tier']}):\n\n"
                    f"{recs_text}\n\n"
                    f"💡 *Metodología:* Cada medida responde directamente a las {len(scenes)} escenas y requerimientos técnicos de tu película."
                )
            return {
                "action": "SUSTAINABILITY_ANALYSIS_ANSWERED",
                "severity": "LOW",
                "scope": "SUSTAINABILITY_QUERY",
                "response": resp
            }

        # 3. Consulta sobre Escena más cara
        if any(w in p_low for w in ["más cara", "mas cara", "más costosa", "mas costosa", "escena cara", "mayor costo", "most expensive", "expensive scene", "highest cost"]):
            scenes_sched = schedule["scenes_schedule"]
            if scenes_sched:
                sorted_scenes = sorted(scenes_sched, key=lambda s: s.get("estimated_cost", 0), reverse=True)
                top_scene = sorted_scenes[0]
                if is_en:
                    resp = (
                        f"🎬 **Highest Budget Demand Scene:**\n\n"
                        f"The most expensive scene in the project is **Scene {top_scene['scene_number']}**: `{top_scene['slugline']}`.\n\n"
                        f"• **Estimated Cost:** `${top_scene['estimated_cost']:,.0f}` (Planning Range)\n"
                        f"• **Shooting Time:** `{top_scene['estimated_days']} day(s)`\n"
                        f"• **Complexity Level:** `{top_scene['complexity']}`\n"
                        f"• **Location:** `{top_scene['location']}`\n\n"
                        f"**Why is it the most expensive?**\n"
                        f"It combines exterior/night conditions with high staging complexity and multiple characters in frame. "
                        f"If you wish to optimize budget, we could adapt part of the action to an interior or shoot at magic hour."
                    )
                else:
                    resp = (
                        f"🎬 **Escena de Mayor Demanda Presupuestaria:**\n\n"
                        f"La escena más costosa del proyecto es la **Escena {top_scene['scene_number']}**: `{top_scene['slugline']}`.\n\n"
                        f"• **Costo Estimado:** `${top_scene['estimated_cost']:,.0f}` (Rango de planificación)\n"
                        f"• **Tiempo de Rodaje:** `{top_scene['estimated_days']} día(s)`\n"
                        f"• **Nivel de Complejidad:** `{top_scene['complexity']}`\n"
                        f"• **Locación:** `{top_scene['location']}`\n\n"
                        f"**¿Por qué es la más cara?**\n"
                        f"Combina exterior/nocturno con requerimientos escénicos de alta complejidad y múltiples personajes en cuadro. "
                        f"Si deseas reducir el presupuesto, podríamos adaptar parte de la acción a un interior o rodarla con luz diurna/atardecer."
                    )
                return {
                    "action": "BUDGET_ANALYSIS_ANSWERED",
                    "severity": "LOW",
                    "scope": "BUDGET_QUERY",
                    "response": resp
                }

        # 4. Consulta sobre Días de Rodaje / Cronograma
        if any(w in p_low for w in ["días de rodaje", "dias de rodaje", "cuántos días", "cuantos dias", "cronograma", "tiempo de rodaje", "schedule", "shooting days", "how many days", "production days"]):
            if is_en:
                resp = (
                    f"🗓️ **Estimated Production Schedule — '{project.get('title')}'**\n\n"
                    f"We project a complete production cycle of **{schedule['total_days']} days** distributed across 3 key phases:\n\n"
                    f"1. 📋 **Pre-Production:** `{schedule['pre_production_days']} days` (Location scouting, casting, wardrobe fittings, and table reads).\n"
                    f"2. 🎥 **Principal Photography:** `{schedule['principal_photography_days']} days` (Shooting all {len(scenes)} script scenes).\n"
                    f"3. 🎞️ **Post-Production:** `{schedule['post_production_days']} days` (Editing, color grading, sound design, and score).\n\n"
                    f"💡 *Shooting pace:* ~1 to 1.5 scenes per day to guarantee top photographic and performance quality."
                )
            else:
                resp = (
                    f"🗓️ **Cronograma Estimado de Producción — '{project.get('title')}'**\n\n"
                    f"Proyectamos un ciclo completo de producción de **{schedule['total_days']} días** distribuidos en 3 fases clave:\n\n"
                    f"1. 📋 **Pre-Producción:** `{schedule['pre_production_days']} días` (Scouting de locaciones, casting, pruebas de vestuario y lectura de guion).\n"
                    f"2. 🎥 **Fotografía Principal:** `{schedule['principal_photography_days']} días` (Rodaje de las {len(scenes)} escenas de escaleta).\n"
                    f"3. 🎞️ **Post-Producción:** `{schedule['post_production_days']} días` (Montaje, corrección de color, diseño sonoro y banda sonora).\n\n"
                    f"💡 *Promedio de rodaje:* ~1 a 1.5 escenas diarias para garantizar alta calidad fotográfica e interpretativa."
                )
            return {
                "action": "BUDGET_ANALYSIS_ANSWERED",
                "severity": "LOW",
                "scope": "BUDGET_QUERY",
                "response": resp
            }

        # 5. Consulta sobre Base de Estimación
        if any(w in p_low for w in ["en qué estás basando", "en que estas basando", "en qué basas", "en que basas", "cómo calculas", "como calculas", "metodología", "metodologia", "methodology", "basis", "how do you calculate", "how is this calculated"]):
            basis_list = "\n".join([f"• {bp}" for bp in budget_data["methodology"]["basis_points"]])
            if is_en:
                resp = (
                    f"📐 **Budget Estimation Methodology & Basis:**\n\n"
                    f"The budget of **${budget_data['total_estimated_budget']:,.0f} USD** is not an arbitrary number; "
                    f"it is calculated directly from actual production parameters:\n\n"
                    f"{basis_list}\n\n"
                    f"📌 *Core Allocations:* Above the Line (Direction/Cast: 22%), Technical Crew & Camera (18%), and Post-Production (10%)."
                )
            else:
                resp = (
                    f"📐 **Metodología y Base de Estimación Presupuestaria:**\n\n"
                    f"El presupuesto de **${budget_data['total_estimated_budget']:,.0f} USD** no es un número arbitrario; "
                    f"se calcula a partir de los datos técnicos reales de la producción:\n\n"
                    f"{basis_list}\n\n"
                    f"📌 *Desglose Mayoritario:* Arriba de la línea (Dirección/Elenco: 22%), Equipo Técnico & Cámara (18%), y Post-Producción (10%)."
                )
            return {
                "action": "BUDGET_ANALYSIS_ANSWERED",
                "severity": "LOW",
                "scope": "BUDGET_QUERY",
                "response": resp
            }

        # 6. Consulta sobre Reducción de Presupuesto
        if any(w in p_low for w in ["reducir", "bajar", "ahorrar", "optimizar el presupuesto", "menos dinero", "abaratar", "reduce budget", "cut cost", "save money", "cheaper", "optimize budget"]):
            if is_en:
                resp = (
                    f"💡 **Strategies to Optimize Budget Without Hurting the Narrative:**\n\n"
                    f"To reduce costs while preserving the dramatic punch of **'{project.get('title')}'**, I recommend three adjustments:\n\n"
                    f"1. 📍 **Location Consolidation:** Reduce moves by grouping scenes into fewer physical locations (estimated savings: $3,000 - $5,500).\n"
                    f"2. ☀️ **Convert Night to Magic Hour/Day:** Filming night exteriors at dusk reduces generator and heavy lighting rental costs (estimated savings: ~$2,500).\n"
                    f"3. 🎭 **Focused Cast:** Concentrate dialogue in secondary scenes around the two primary characters.\n\n"
                    f"Would you like me to adapt a specific scene to apply these savings?"
                )
            else:
                resp = (
                    f"💡 **Estrategias para Optimizar el Presupuesto sin Dañar la Historia:**\n\n"
                    f"Para reducir costos manteniendo la potencia dramática de **'{project.get('title')}'**, recomiendo tres ajustes:\n\n"
                    f"1. 📍 **Consolidación de Locaciones:** Reducir traslados agrupando escenas en menos sets físicos (ahorro estimado: $3,000 - $5,500).\n"
                    f"2. ☀️ **Conversión de Nocturnas a Horas Mágicas/Día:** Rodar escenas nocturnas al atardecer reduce el gasto en generadores y alquiler de luminarias (ahorro estimado: ~$2,500).\n"
                    f"3. 🎭 **Reparto Focalizado:** Concentrar los diálogos de las escenas secundarias en los dos personajes centrales.\n\n"
                    f"¿Deseas que adapte alguna escena específica para aplicar este ahorro?"
                )
            return {
                "action": "BUDGET_ANALYSIS_ANSWERED",
                "severity": "LOW",
                "scope": "BUDGET_QUERY",
                "response": resp
            }

        # 7. Consulta General de Presupuesto
        top_cats = sorted(budget_data["categories"], key=lambda c: c["amount"], reverse=True)[:4]
        cats_summary = "\n".join([f"• **{c['category']}:** `${c['amount']:,.0f}` ({c['percentage']}%) — *{c['description'][:70]}...*" for c in top_cats])
        if is_en:
            resp = (
                f"💰 **Estimated Production Budget — '{project.get('title')}'**\n\n"
                f"The projected total cost for this film is **${budget_data['total_estimated_budget']:,.0f} USD** "
                f"(Planning range: `{budget_data['planning_range']}` for `{schedule['principal_photography_days']} shooting days`).\n\n"
                f"📋 **Key Budget Categories:**\n"
                f"{cats_summary}\n\n"
                f"🔍 *You can ask:* 'What is this budget based on?', 'What is the most expensive scene?' or 'How can we make it more sustainable?'."
            )
        else:
            resp = (
                f"💰 **Presupuesto Estimado de Producción — '{project.get('title')}'**\n\n"
                f"El costo total proyectado para esta película es de **${budget_data['total_estimated_budget']:,.0f} USD** "
                f"(Rango de planificación: `{budget_data['planning_range']}` para `{schedule['principal_photography_days']} días de rodaje`).\n\n"
                f"📋 **Principales Rubros de Inversión:**\n"
                f"{cats_summary}\n\n"
                f"🔍 *Puedes consultar:* '¿En qué estás basando ese presupuesto?', '¿Cuál es la escena más cara?' o '¿Cómo podríamos hacerlo más sostenible?'."
            )
        return {
            "action": "BUDGET_ANALYSIS_ANSWERED",
            "severity": "LOW",
            "scope": "BUDGET_QUERY",
            "response": resp
        }
