import json
import time
import re
from typing import Dict, List, Any, Optional, Tuple
from google import genai
from google.genai import types
from config import GEMINI_API_KEY
from core.db import (
    get_project_db, get_characters_by_project_db,
    get_scenes_by_project_db, get_relationships_by_project_db,
    save_project_localization_db, get_project_localization_db
)

class LocalizationService:
    """
    Motor de Localización Integral Cinemática (Capa de Proyección No-Destructiva).
    Permite visualizar y exportar producciones en múltiples idiomas (ES, EN, FR, DE, IT, PT)
    sin modificar jamás los datos canónicos en SQLite (garantía de cero drift de traducción).
    """

    CANDIDATE_TRANSLATE_MODELS = [
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-3.6-flash",
        "gemini-flash-latest"
    ]

    # Traducciones curadas de alta calidad para las categorías de presupuesto (10 categorías estándar)
    BUDGET_CATEGORIES_I18N = {
        "EN": {
            "Desarrollo & Derechos Narrativos": ("Story & Literary Rights Development", "Screenplay, Story Bible, intellectual property registration, and dramatic research."),
            "Equipo de Dirección & Talento Principal": ("Director Team & Principal Cast", "Director, Assistant Directors, and principal cast salaries."),
            "Equipo Técnico, Cámara & Iluminación": ("Technical Crew, Camera & Lighting", "Cinematography, 4K/35mm camera operation, gaffer, grips, and production sound."),
            "Locaciones, Scouting & Permisos": ("Locations, Scouting & Permits", "Physical location leases, municipal permits, production insurance, and location fees."),
            "Diseño de Producción & Utilería": ("Production Design & Props", "Scenic dressing, hero props, set decoration, and art consumables."),
            "Vestuario, Peluquería & Caracterización": ("Costumes, Hair & Makeup", "Costume design, period styling, and characterization."),
            "Transporte, Combustible & Logística": ("Transportation, Fuel & Fleet Logistics", "Equipment trucks, cast vans, inter-location moves, and fuel."),
            "Catering & Servicios de Rodaje": ("Catering & Craft Services", "Full catering and eco-friendly craft service for crew during production."),
            "Post-Producción & Sonido / Música": ("Post-Production & Sound / Score", "Picture editorial, color grading, foley, 5.1 surround mix, and original score."),
            "Imprevistos & Contingencia (10%)": ("Contingency & Production Reserve (10%)", "Reserve fund for weather delays, location cost overruns, and reshoots.")
        },
        "FR": {
            "Desarrollo & Derechos Narrativos": ("Développement & Droits Narratifs", "Scénario littéraire, Bible dramatique et recherche narrative."),
            "Equipo de Dirección & Talento Principal": ("Réalisation & Distribution Principale", "Honoraires de réalisation et casting principal."),
            "Equipo Técnico, Cámara & Iluminación": ("Équipe Technique, Caméra & Éclairage", "Direction de la photographie, cadreur 35mm, chef électricien et son direct."),
            "Locaciones, Scouting & Permisos": ("Lieux de Tournage, Repérages & Permis", "Location de décors, autorisations de tournage et assurances."),
            "Diseño de Producción & Utilería": ("Décors, Direction Artistique & Accessoires", "Habillage scénographique et accessoires clés."),
            "Vestuario, Peluquería & Caracterización": ("Costumes, Coiffure & Maquillage", "Création des costumes et coiffure d'époque."),
            "Transporte, Combustible & Logística": ("Transport, Carburant & Logistique", "Camions régie, navettes comédiens et transferts."),
            "Catering & Servicios de Rodaje": ("Restauration & Services de Plateau", "Repas complets et cantine écologique pour l'équipe."),
            "Post-Producción & Sonido / Música": ("Post-Production & Son / Musique", "Montage, étalonnage couleur, mixage 5.1 et musique originale."),
            "Imprevistos & Contingencia (10%)": ("Imprévus & Réserve de Production (10%)", "Fonds de prévoyance pour aléas climatiques et retouches.")
        },
        "DE": {
            "Desarrollo & Derechos Narrativos": ("Stoffentwicklung & Urheberrechte", "Drehbuch, Serienbibel, Recherche und Schutzrechte."),
            "Equipo de Dirección & Talento Principal": ("Regieteam & Hauptbesetzung", "Regiehonorare, Regieassistenz und Hauptdarsteller."),
            "Equipo Técnico, Cámara & Iluminación": ("Kamerateam, Licht & Ton", "Kameraführung, 35mm-Optiken, Oberbeleuchter und Originalton."),
            "Locaciones, Scouting & Permisos": ("Drehorte, Motivsuche & Drehgenehmigungen", "Motivmieten, städtische Genehmigungen und Versicherungen."),
            "Diseño de Producción & Utilería": ("Szenenbild & Requisite", "Szenografie, Schlüsselrequisiten und Setbau."),
            "Vestuario, Peluquería & Caracterización": ("Kostümbild, Maske & Styling", "Kostümgestaltung, historische Garderobe und Maskenbild."),
            "Transporte, Combustible & Logística": ("Fuhrpark, Treibstoff & Logistik", "LKW-Flotte, Shuttleservice und Transporte."),
            "Catering & Servicios de Rodaje": ("Catering & Set-Versorgung", "Ökologische Verpflegung und Trinkwasserstationen für das Team."),
            "Post-Producción & Sonido / Música": ("Postproduktion, Sounddesign & Filmmusik", "Schnitt, Farbkorrektur, 5.1-Mischung und Originalkomposition."),
            "Imprevistos & Contingencia (10%)": ("Unvorhergesehenes & Produktionsreserve (10%)", "Notfallfonds für wetterbedingte Verschiebungen und Nachdrehs.")
        },
        "IT": {
            "Desarrollo & Derechos Narrativos": ("Sviluppo & Diritti Letterari", "Sceneggiatura, bibbia drammatica e ricerca storica."),
            "Equipo de Dirección & Talento Principal": ("Regia & Cast Principale", "Compensi di regia e attori protagonisti."),
            "Equipo Técnico, Cámara & Iluminación": ("Troupe Tecnica, Macchina da Presa & Luci", "Direzione della fotografia, operatore 35mm, capo elettricista e fonico."),
            "Locaciones, Scouting & Permisos": ("Location, Sopralluoghi & Permessi", "Noleggio ambientazioni, permessi comunali e assicurazione."),
            "Diseño de Producción & Utilería": ("Scenografia & Attrezzeria", "Allestimento scenico, arredamento e oggetti di scena."),
            "Vestuario, Peluquería & Caracterización": ("Costumi, Trucco & Acconciatura", "Design dei costumi d'epoca e trucco speciale."),
            "Transporte, Combustible & Logística": ("Trasporti, Carburante & Logistica", "Furgoni di produzione, van per attori e spostamenti."),
            "Catering & Servicios de Rodaje": ("Catering & Servizi di Set", "Mensa biologica sul set e servizi di ristoro sostenibili."),
            "Post-Producción & Sonido / Música": ("Post-Produzione, Suono & Colonna Sonora", "Montaggio video, color grading, missaggio 5.1 e musiche."),
            "Imprevistos & Contingencia (10%)": ("Imprevisti & Riserva di Produzione (10%)", "Fondo di riserva per ritardi meteorologici ed extra.")
        },
        "PT": {
            "Desarrollo & Derechos Narrativos": ("Desenvolvimento & Direitos Narrativos", "Roteiro literário, bíblia de produção e pesquisa temática."),
            "Equipo de Dirección & Talento Principal": ("Equipe de Direção & Elenco Principal", "Cachês de direção e atores protagonistas."),
            "Equipo Técnico, Cámara & Iluminación": ("Equipe Técnica, Câmera & Iluminação", "Direção de fotografia, operação 35mm, maquinária e som direto."),
            "Locaciones, Scouting & Permisos": ("Locações, Prospecção & Autorizações", "Locações de cenários, alvarás e seguros de produção."),
            "Diseño de Producción & Utilería": ("Direção de Arte & Objetos de Cena", "Cenografia, adereços principais e decoração de interiores."),
            "Vestuario, Peluquería & Caracterización": ("Figurino, Maquiagem & Cabelo", "Design de figurinos de época e caracterização."),
            "Transporte, Combustible & Logística": ("Transporte, Combustível & Frota", "Caminhões de apoio, vans e transferências de set."),
            "Catering & Servicios de Rodaje": ("Alimentação & Serviços de Set", "Catering sustentável e estações de hidratação sem plástico."),
            "Post-Producción & Sonido / Música": ("Pós-Produção, Edição de Som & Trilha", "Montagem, correção de cor, mixagem 5.1 e trilha original."),
            "Imprevistos & Contingencia (10%)": ("Imprevistos & Margem de Segurança (10%)", "Fundo de contingência para intempéries e refilmagens.")
        }
    }

    # Traducciones curadas para los 6 sectores de sostenibilidad Green Production
    SUSTAINABILITY_SECTORS_I18N = {
        "EN": {
            "Escenografía & Materiales (Sets)": ("Set Construction & Materials", "Modular Construction & Reusable Flats", "Reduce set wood waste by utilizing prefabricated reusable structures and FSC-certified timber.", "45% reduction in art department lumber waste."),
            "Iluminación & Energía (Lighting)": ("Lighting & Power", "100% LED Lighting & Hybrid Mobile Batteries", "Replace incandescent HMI lamps with high-efficiency LED units and quiet mobile battery generators.", "60% drop in diesel consumption, eliminating acoustic noise."),
            "Transporte & Logística (Fleet)": ("Transport & Logistics", "Geographic Location Clustering", "Group all same-zone scenes into continuous shooting days to eliminate unnecessary crew movements.", "35% reduction in fleet carbon emissions."),
            "Vestuario & Estilismo (Wardrobe)": ("Wardrobe & Styling", "Circular Costume Rental & Upcycled Textiles", "Source cast wardrobe through local rental costume houses and vintage markets instead of single-use purchases.", "70% lower textile water footprint."),
            "Catering & Hospitalidad (Catering)": ("Catering & Hospitality", "Zero-Waste Local Catering & Plastic-Free Sets", "Install multi-gallon water stations with personal reusable canteens and compostable dishware.", "Elimination of 1,200+ single-use plastic bottles."),
            "Oficina de Producción Digital (Paperless)": ("Digital Production Office", "100% Digital Script & Call Sheets", "Distribute script revisions, continuity reports, and call sheets via digital tablets and mobile apps.", "Saving ~4,000 sheets of script paper.")
        },
        "FR": {
            "Escenografía & Materiales (Sets)": ("Décors & Matériaux", "Construction Modulaire & Panneaux Réutilisables", "Réduire les déchets de bois en utilisant des structures préfabriquées certifiées FSC.", "Réduction de 45% des déchets de menuiserie."),
            "Iluminación & Energía (Lighting)": ("Éclairage & Énergie", "Projecteurs 100% LED & Batteries Hybrides", "Remplacer les projecteurs HMI par des projecteurs LED et des générateurs à batterie silencieux.", "Baisse de 60% de la consommation de diesel."),
            "Transporte & Logística (Fleet)": ("Transport & Logistique", "Regroupement Géographique des Décors", "Planifier les journées de tournage par zone géographique pour éviter les trajets inutiles.", "Diminution de 35% de l'empreinte carbone des véhicules."),
            "Vestuario & Estilismo (Wardrobe)": ("Costumes & Styling", "Location Circulaire & Textiles Revalorisés", "Privilégier la location de costumes d'époque et l'upcycling plutôt que l'achat jetable.", "Économie de 70% d'eau textile."),
            "Catering & Hospitalidad (Catering)": ("Restauration & Accueil", "Cantine Locale Zéro Déchet & Zéro Bouteille Plastique", "Fontaines à eau filtrée, gourdes réutilisables et vaisselle compostable sur le plateau.", "Suppression de plus de 1 200 bouteilles plastiques."),
            "Oficina de Producción Digital (Paperless)": ("Bureau de Production Numérique", "Feuilles de Service & Scénarios 100% Numériques", "Distribution électronique des réécritures et feuilles de service sur tablettes.", "Préservation d'environ 4 000 feuilles de papier.")
        },
        "DE": {
            "Escenografía & Materiales (Sets)": ("Kulissenbau & Materialien", "Modularer Setbau & Wiederverwendbare Wände", "Einsatz von FSC-zertifiziertem Holz und modularen Kulissensystemen.", "45% weniger Holzabfälle in der Ausstattung."),
            "Iluminación & Energía (Lighting)": ("Beleuchtung & Energie", "100% LED-Technik & Mobile Batteriespeicher", "Ersatz lauter Dieselgeneratoren durch moderne Speicher und hocheffiziente LED-Scheinwerfer.", "60% geringerer Treibstoffverbrauch und Lärmminderung."),
            "Transporte & Logística (Fleet)": ("Fuhrpark & Logistik", "Geografische Drehplan-Optimierung", "Konzentration aller Drehtage am selben Ort zur Reduzierung von Fahrtstrecken.", "35% Senkung der fahrzeugbedingten CO2-Emissionen."),
            "Vestuario & Estilismo (Wardrobe)": ("Kostümbild & Maske", "Zirkulärer Kostümverleih & Upcycling", "Nutzung von Fundus-Kostümen und Second-Hand-Stoffen anstelle von Neukäufen.", "70% weniger Wasserverbrauch bei Textilien."),
            "Catering & Hospitalidad (Catering)": ("Catering & Set-Betreuung", "Regionale Biokost & Plastikfreies Set", "Trinkwasserstationen und kompostierbares Geschirr für die gesamte Filmcrew.", "Vermeidung von über 1.200 Einweg-Plastikflaschen."),
            "Oficina de Producción Digital (Paperless)": ("Digitales Produktionsbüro", "Papierloses Set & Digitale Dispositionslisten", "Verteilung aller Drehbuchfassungen und Tagesberichte rein digital über Tablets.", "Einsparung von ca. 4.000 Blatt Papier.")
        },
        "IT": {
            "Escenografía & Materiales (Sets)": ("Scenografia & Materiali", "Costruzione Modulare & Pannelli Riusabili", "Riduzione degli scarti di legname grazie a strutture prefabbricate certificate FSC.", "Riduzione del 45% degli scarti di falegnameria."),
            "Iluminación & Energía (Lighting)": ("Illuminazione & Energia", "Illuminazione 100% LED & Batterie Mobili Ibride", "Sostituzione delle lampade a scarica con proiettori LED e generatori a batteria silenziosi.", "Riduzione del 60% del consumo di gasolio."),
            "Transporte & Logística (Fleet)": ("Trasporti & Logistica", "Raggruppamento Geografico dei Set", "Accorpamento dei giorni di ripresa per zona per evitare spostamenti superflui della troupe.", "35% di emissioni di carbonio in meno dalla flotta."),
            "Vestuario & Estilismo (Wardrobe)": ("Costumi & Trucco", "Noleggio Circolare & Tessuti Riciclati", "Noleggio presso sartorie teatrali locali e mercatini vintage anziché acquisti usa e getta.", "Risparmio del 70% sull'impronta idrica tessile."),
            "Catering & Hospitalidad (Catering)": ("Ristorazione & Accoglienza", "Catering a Km Zero & Set Senza Plastica", "Erogatori d'acqua potabile con borracce personali e stoviglie compostabili.", "Eliminazione di oltre 1.200 bottiglie di plastica."),
            "Oficina de Producción Digital (Paperless)": ("Ufficio di Produzione Digitale", "Ordini del Giorno & Sceneggiature Digitali", "Distribuzione digitale di copioni e piani di lavorazione su tablet e smartphone.", "Risparmio di circa 4.000 fogli di carta.")
        },
        "PT": {
            "Escenografía & Materiales (Sets)": ("Cenografia & Materiais", "Construção Modular & Painéis Reutilizáveis", "Redução de resíduos de madeira através de estruturas pré-fabricadas com certificação FSC.", "Redução de 45% nos resíduos de carpintaria."),
            "Iluminación & Energía (Lighting)": ("Iluminação & Energia", "Iluminação 100% LED & Baterias Portáteis Híbridas", "Substituição de refletores incandescentes por painéis LED e geradores silenciosos a bateria.", "Queda de 60% no consumo de diesel."),
            "Transporte & Logística (Fleet)": ("Transporte & Logística", "Planejamento Geográfico de Locações", "Agrupamento de filmagens por polo regional para eliminar deslocamentos desnecessários.", "Redução de 35% nas emissões da frota automotiva."),
            "Vestuario & Estilismo (Wardrobe)": ("Figurino & Caracterização", "Acervo Circular de Figurino & Tecidos Reaproveitados", "Aluguel em brechós e guarda-roupas teatrais ao invés de compras descartáveis.", "Economia de 70% na pegada hídrica têxtil."),
            "Catering & Hospitalidad (Catering)": ("Alimentação & Hospitalidade", "Catering Local Desperdício Zero & Set Sem Plástico", "Instalação de bebedouros com garrafas reutilizáveis individuais e louça compostável.", "Eliminação de mais de 1.200 garrafas plásticas."),
            "Oficina de Producción Digital (Paperless)": ("Produção Digital Integrada", "Roteiros e Ordens do Dia 100% Digitais", "Distribuição eletrônica de revisões de texto e ordens do dia via tablets e celulares.", "Economia de cerca de 4.000 folhas de papel.")
        }
    }

    # Proyecciones curadas completas para producciones demo en los idiomas objetivo
    from services.demo_i18n_catalog import DEMO_PROJECT_I18N

    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception:
                pass

    def get_localized_project_summary(self, project: Dict[str, Any], lang: str = "ES") -> Dict[str, Any]:
        """Devuelve el resumen localizado de un proyecto para la vista de biblioteca/cards."""
        lang = (lang or "ES").upper()
        if not project:
            return {}

        pid = project.get("id", "")
        p_copy = dict(project)

        # Si el proyecto es demo y tenemos traducción curada en el catálogo para este idioma
        demo_i18n = self.DEMO_PROJECT_I18N.get(pid, {}).get(lang)
        if demo_i18n:
            p_copy.update({
                "title": demo_i18n.get("title", p_copy.get("title")),
                "tagline": demo_i18n.get("tagline", p_copy.get("tagline")),
                "genre": demo_i18n.get("genre", p_copy.get("genre")),
                "logline": demo_i18n.get("logline", p_copy.get("logline")),
                "synopsis": demo_i18n.get("synopsis", p_copy.get("synopsis")),
                "visual_aesthetic": demo_i18n.get("visual_aesthetic", p_copy.get("visual_aesthetic")),
                "tone": demo_i18n.get("tone", p_copy.get("tone"))
            })
            return p_copy

        if lang == "ES":
            return p_copy

        # Si no es demo, intentar obtener de caché
        cached = get_project_localization_db(pid, lang, "full_projection")
        if cached and isinstance(cached, dict) and cached.get("project"):
            cached_proj = cached.get("project", {})
            p_copy.update({
                "title": cached_proj.get("title", p_copy.get("title")),
                "tagline": cached_proj.get("tagline", p_copy.get("tagline")),
                "genre": cached_proj.get("genre", p_copy.get("genre")),
                "logline": cached_proj.get("logline", p_copy.get("logline"))
            })
            return p_copy

        return p_copy

    def get_localized_project_details(self, project_id: str, lang: str = "ES") -> Dict[str, Any]:
        """
        Obtiene la proyección completa localizada de un proyecto (metadatos, personajes, escenas, relaciones).
        Si el proyecto tiene catálogo curado en DEMO_PROJECT_I18N para este idioma, genera y cachea la proyección directamente.
        Si lang == 'ES' (y no hay demo catalog especial como en proj_tides_of_luna), devuelve los datos canónicos de SQLite.
        Si lang != 'ES', comprueba la caché de 'project_localizations' en SQLite. Si no existe,
        genera la proyección usando Gemini o plantillas curadas y la almacena en caché.
        """
        lang = (lang or "ES").upper()
        proj = get_project_db(project_id)
        if not proj:
            return {}

        characters = get_characters_by_project_db(project_id) or []
        scenes = get_scenes_by_project_db(project_id) or []
        relationships = get_relationships_by_project_db(project_id) or []

        # 1. Si el proyecto cuenta con catálogo curado para este idioma, proyectar directamente
        demo_i18n = self.DEMO_PROJECT_I18N.get(project_id, {}).get(lang)
        if demo_i18n:
            localized_data = self._generate_localized_projection(proj, characters, scenes, relationships, lang)
            # Sincronizar activos visuales cinemáticos con la verdad viva de SQLite
            if proj.get("poster_url"):
                localized_data["project"]["poster_url"] = proj["poster_url"]
            c_url_map = {c["id"]: c.get("avatar_url") for c in characters}
            for c in localized_data.get("characters", []):
                if c.get("id") in c_url_map and c_url_map[c["id"]]:
                    c["avatar_url"] = c_url_map[c["id"]]
            s_url_map = {s["id"]: s.get("image_url") for s in scenes}
            for s in localized_data.get("scenes", []):
                if s.get("id") in s_url_map and s_url_map[s["id"]]:
                    s["image_url"] = s_url_map[s["id"]]
            try:
                save_project_localization_db(project_id, lang, "full_projection", json.dumps(localized_data, ensure_ascii=False))
            except Exception as e:
                print(f"[LocalizationService] Cache save error: {e}")
            return localized_data

        # 2. Si el idioma solicitado es español y no es demo en inglés, devolver la verdad canónica de SQLite
        if lang == "ES":
            return {
                "project": proj,
                "characters": characters,
                "scenes": scenes,
                "relationships": relationships,
                "lang": "ES",
                "is_projection": False
            }

        # 3. Comprobar si existe la proyección guardada en SQLite (Caché no destructiva)
        cached = get_project_localization_db(project_id, lang, "full_projection")
        if cached and isinstance(cached, dict) and cached.get("project"):
            cached_chars = cached.get("characters", [])
            cached_scenes = cached.get("scenes", [])
            if len(cached_chars) == len(characters) and len(cached_scenes) == len(scenes):
                if proj.get("poster_url"):
                    cached["project"]["poster_url"] = proj["poster_url"]
                c_url_map = {c["id"]: c.get("avatar_url") for c in characters}
                for c in cached.get("characters", []):
                    if c.get("id") in c_url_map and c_url_map[c["id"]]:
                        c["avatar_url"] = c_url_map[c["id"]]
                s_url_map = {s["id"]: s.get("image_url") for s in scenes}
                can_scene_map = {s["id"]: s for s in scenes}
                for s in cached.get("scenes", []):
                    if s.get("id") in s_url_map and s_url_map[s["id"]]:
                        s["image_url"] = s_url_map[s["id"]]
                    # Fallback guard: ensure script_text is never empty if canonical has it
                    if not s.get("script_text") and s.get("id") in can_scene_map:
                        s["script_text"] = can_scene_map[s["id"]].get("script_text")
                    if not s.get("summary") and s.get("id") in can_scene_map:
                        s["summary"] = can_scene_map[s["id"]].get("summary")
                return cached

        # 4. Generar proyección localizada
        localized_data = self._generate_localized_projection(proj, characters, scenes, relationships, lang)

        # Fallback guard on newly generated projection
        can_scene_map = {s["id"]: s for s in scenes}
        for s in localized_data.get("scenes", []):
            if not s.get("script_text") and s.get("id") in can_scene_map:
                s["script_text"] = can_scene_map[s["id"]].get("script_text")
            if not s.get("summary") and s.get("id") in can_scene_map:
                s["summary"] = can_scene_map[s["id"]].get("summary")

        # 5. Guardar en caché no-destructiva en SQLite
        try:
            save_project_localization_db(project_id, lang, "full_projection", json.dumps(localized_data, ensure_ascii=False))
        except Exception as e:
            print(f"[LocalizationService] Warning saving projection cache: {e}")

        return localized_data

    def _generate_localized_projection(
        self,
        project: Dict[str, Any],
        characters: List[Dict[str, Any]],
        scenes: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        lang: str
    ) -> Dict[str, Any]:
        """Construye la proyección traducida garantizando formato y preservando nombres propios."""
        project_id = project.get("id", "")
        proj_copy = dict(project)
        chars_copy = [dict(c) for c in characters]
        scenes_copy = [dict(s) for s in scenes]
        rels_copy = [dict(r) for r in relationships]

        # Comprobar si tenemos traducción curada inmediata para demo
        demo_i18n = self.DEMO_PROJECT_I18N.get(project_id, {}).get(lang)
        if demo_i18n:
            proj_copy.update({
                "title": demo_i18n.get("title", proj_copy.get("title")),
                "tagline": demo_i18n.get("tagline", proj_copy.get("tagline")),
                "genre": demo_i18n.get("genre", proj_copy.get("genre")),
                "logline": demo_i18n.get("logline", proj_copy.get("logline")),
                "synopsis": demo_i18n.get("synopsis", proj_copy.get("synopsis")),
                "visual_aesthetic": demo_i18n.get("visual_aesthetic", proj_copy.get("visual_aesthetic")),
                "tone": demo_i18n.get("tone", proj_copy.get("tone"))
            })
            # Actualizar personajes curados si existen
            curated_char_ids = set()
            if "characters" in demo_i18n:
                for c in chars_copy:
                    cid = c.get("id")
                    if cid in demo_i18n["characters"]:
                        c.update(demo_i18n["characters"][cid])
                        curated_char_ids.add(cid)

            # Actualizar escenas curadas si existen
            loc_map = {
                "EN": {
                    "Estación Titán": "Titan Station", "Ciudad Lumina": "Lumina City",
                    "Golfo San Lorenzo": "Gulf of San Lorenzo", "Arrecife de Coral": "Coral Reef",
                    "Laboratorio Marino": "Marine Laboratory", "Trinchera Abisal": "Abyssal Trench",
                    "Laboratorio de Inteligencia": "Intelligence Lab", "Bahía": "Bay", "Estudio": "Studio"
                },
                "DE": {
                    "Estación Titán": "Titan-Station", "Ciudad Lumina": "Lumina-Stadt",
                    "Golfo San Lorenzo": "Golf von San Lorenzo", "Arrecife de Coral": "Korallenriff",
                    "Laboratorio Marino": "Meereslabor", "Trinchera Abisal": "Tiefseegraben",
                    "Laboratorio de Inteligencia": "KI-Laboratorium", "Bahía": "Bucht", "Estudio": "Studio"
                },
                "FR": {
                    "Estación Titán": "Station Titan", "Ciudad Lumina": "Cité Lumina",
                    "Golfo San Lorenzo": "Golfe de San Lorenzo", "Arrecife de Coral": "Récif de Corail",
                    "Laboratorio Marino": "Laboratoire Marin", "Trinchera Abisal": "Fosse Abyssale",
                    "Laboratorio de Inteligencia": "Laboratoire d'IA", "Bahía": "Baie", "Estudio": "Studio"
                }
            }.get(lang, {})
            if "scenes" in demo_i18n:
                for s in scenes_copy:
                    sid = s.get("id")
                    if sid in demo_i18n["scenes"]:
                        s.update(demo_i18n["scenes"][sid])
                    loc = s.get("location")
                    if loc and loc in loc_map:
                        s["location"] = loc_map[loc]
            else:
                for s in scenes_copy:
                    loc = s.get("location")
                    if loc and loc in loc_map:
                        s["location"] = loc_map[loc]

            # Actualizar relaciones curadas si existen
            curated_rel_ids = set()
            if "relationships" in demo_i18n:
                for r in rels_copy:
                    rid = r.get("id")
                    if rid in demo_i18n["relationships"]:
                        r.update(demo_i18n["relationships"][rid])
                        curated_rel_ids.add(rid)

            # Traducir deterministamente los personajes y relaciones que NO estaban en demo_i18n
            non_curated_chars = [c for c in chars_copy if c.get("id") not in curated_char_ids]
            non_curated_rels = [r for r in rels_copy if r.get("id") not in curated_rel_ids]
            if non_curated_chars or non_curated_rels:
                self._apply_deterministic_translation(proj_copy, non_curated_chars, [], non_curated_rels, lang)

            return {
                "project": proj_copy,
                "characters": chars_copy,
                "scenes": scenes_copy,
                "relationships": rels_copy,
                "lang": lang,
                "is_projection": True
            }

        # Si tenemos Gemini disponible, traducir el contenido dinámico con un único prompt estructurado
        if self.client:
            try:
                translated_bundle = self._translate_with_gemini(proj_copy, chars_copy, scenes_copy, rels_copy, lang)
                if translated_bundle:
                    return translated_bundle
            except Exception as e:
                print(f"[LocalizationService] Gemini translation error: {e}. Using deterministic linguistic rules.")

        # Fallback de reglas lingüísticas y diccionarios para garantizar traducción coherente
        self._apply_deterministic_translation(proj_copy, chars_copy, scenes_copy, rels_copy, lang)

        return {
            "project": proj_copy,
            "characters": chars_copy,
            "scenes": scenes_copy,
            "relationships": rels_copy,
            "lang": lang,
            "is_projection": True
        }

    def _translate_with_gemini(
        self,
        project: Dict[str, Any],
        characters: List[Dict[str, Any]],
        scenes: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        lang: str
    ) -> Optional[Dict[str, Any]]:
        """Traduce de forma unificada y de alta fidelidad vía Gemini."""
        lang_names = {"EN": "English", "FR": "French", "DE": "German", "IT": "Italian", "PT": "Portuguese"}
        target_lang_name = lang_names.get(lang, "English")

        payload_to_translate = {
            "project": {
                "title": project.get("title"),
                "tagline": project.get("tagline"),
                "genre": project.get("genre"),
                "logline": project.get("logline"),
                "synopsis": project.get("synopsis"),
                "visual_aesthetic": project.get("visual_aesthetic"),
                "tone": project.get("tone")
            },
            "characters": [
                {
                    "id": c.get("id"),
                    "name": c.get("name"),  # KEEP NAME INTACT
                    "role": c.get("role"),
                    "archetype": c.get("archetype"),
                    "occupation": c.get("occupation"),
                    "personality": c.get("personality"),
                    "motivation": c.get("motivation"),
                    "wardrobe": c.get("wardrobe")
                }
                for c in characters
            ],
            "scenes": [
                {
                    "id": s.get("id"),
                    "scene_number": s.get("scene_number"),
                    "slugline": s.get("slugline"),
                    "summary": s.get("summary"),
                    "subtext": s.get("subtext"),
                    "script_text": s.get("script_text")
                }
                for s in scenes
            ],
            "relationships": [
                {
                    "id": r.get("id"),
                    "rel_type": r.get("rel_type"),
                    "history": r.get("history"),
                    "status": r.get("status")
                }
                for r in relationships
            ]
        }

        system_instruction = (
            f"You are the Lead Master Translator for Hollywood studio productions.\n"
            f"Translate the provided cinematic production bundle into {target_lang_name}.\n"
            f"CRITICAL RULES:\n"
            f"1. DO NOT translate proper character names (e.g. keep 'Elena Vance', 'Marcus Thorne', 'David Vance', 'Elara Vega', 'Marina Silva' exactly as they are).\n"
            f"2. Maintain standard screenplay sluglines (e.g. INT. / EXT. format, translate location and DAY/NIGHT).\n"
            f"3. In script_text, preserve character cues in all-caps, parentheticals, and FADE IN / CUT TO markers.\n"
            f"4. Output strictly a valid JSON object matching the input structure."
        )

        prompt = f"Translate the following JSON project structure into {target_lang_name}:\n\n{json.dumps(payload_to_translate, ensure_ascii=False)}"

        for model in self.CANDIDATE_TRANSLATE_MODELS:
            try:
                resp = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=0.3
                    )
                )
                if resp and resp.text:
                    parsed = json.loads(resp.text)
                    # Mergear con los campos canónicos
                    p_res = dict(project)
                    p_res.update(parsed.get("project", {}))

                    c_map = {c["id"]: c for c in parsed.get("characters", [])}
                    c_res = []
                    for c in characters:
                        c_copy = dict(c)
                        if c["id"] in c_map:
                            c_copy.update(c_map[c["id"]])
                            c_copy["name"] = c["name"]  # Preservar nombre original
                        c_res.append(c_copy)

                    s_map = {s["id"]: s for s in parsed.get("scenes", [])}
                    s_res = []
                    for s in scenes:
                        s_copy = dict(s)
                        if s["id"] in s_map:
                            trans = s_map[s["id"]]
                            for k, v in trans.items():
                                if k in ["script_text", "summary", "subtext"]:
                                    if v and str(v).strip():
                                        s_copy[k] = v
                                else:
                                    s_copy[k] = v
                        s_res.append(s_copy)

                    r_map = {r["id"]: r for r in parsed.get("relationships", [])}
                    r_res = []
                    for r in relationships:
                        r_copy = dict(r)
                        if r["id"] in r_map:
                            r_copy.update(r_map[r["id"]])
                        r_res.append(r_copy)

                    return {
                        "project": p_res,
                        "characters": c_res,
                        "scenes": s_res,
                        "relationships": r_res,
                        "lang": lang,
                        "is_projection": True
                    }
            except Exception as e:
                continue
        return None

    def _apply_deterministic_translation(
        self,
        project: Dict[str, Any],
        characters: List[Dict[str, Any]],
        scenes: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        lang: str
    ):
        """Aplica reglas deterministas de traducción cuando el modelo LLM no responde."""
        role_dict = {
            "EN": {"Protagonista": "Protagonist", "Antagonista": "Antagonist", "Aliado": "Ally", "Mentor": "Mentor", "Aliada": "Ally", "Aliado Clave": "Key Ally", "Especialista": "Specialist", "Compañero": "Companion", "Tripulación": "Crew Member", "Ingeniero": "Chief Engineer", "Médico": "Medical Officer", "Operador": "Systems Operator", "Científico": "Chief Scientist", "Científica": "Chief Scientist"},
            "FR": {"Protagonista": "Protagoniste", "Antagonista": "Antagoniste", "Aliado": "Allié", "Mentor": "Mentor", "Aliada": "Alliée", "Aliado Clave": "Allié Clé", "Especialista": "Spécialiste", "Compañero": "Compagnon", "Tripulación": "Membre d'Équipage", "Ingeniero": "Ingénieur en Chef", "Médico": "Médecin de Bord", "Operador": "Opérateur Systèmes", "Científico": "Scientifique en Chef", "Científica": "Scientifique en Chef"},
            "DE": {"Protagonista": "Protagonist", "Antagonista": "Antagonist", "Aliado": "Verbündeter", "Mentor": "Mentor", "Aliada": "Verbündete", "Aliado Clave": "Wichtiger Verbündeter", "Especialista": "Spezialist", "Compañero": "Gefährte", "Tripulación": "Besatzungsmitglied", "Ingeniero": "Chefingenieur", "Médico": "Bordarzt", "Operador": "Systemoperator", "Científico": "Leitender Wissenschaftler", "Científica": "Leitende Wissenschaftlerin"},
            "IT": {"Protagonista": "Protagonista", "Antagonista": "Antagonista", "Aliado": "Alleato", "Mentor": "Mentore", "Aliada": "Alleata", "Aliado Clave": "Alleato Chiave", "Especialista": "Specialista", "Compañero": "Compagno", "Tripulación": "Membro dell'Equipaggio", "Ingeniero": "Capo Ingegnere", "Médico": "Ufficiale Medico", "Operador": "Operatore di Sistema", "Científico": "Capo Scienziato", "Científica": "Capo Scienziata"},
            "PT": {"Protagonista": "Protagonista", "Antagonista": "Antagonista", "Aliado": "Aliado", "Mentor": "Mentor", "Aliada": "Aliada", "Aliado Clave": "Aliado Chave", "Especialista": "Especialista", "Compañero": "Companheiro", "Tripulación": "Membro da Tripulação", "Ingeniero": "Engenheiro-Chefe", "Médico": "Oficial Médico", "Operador": "Operador de Sistemas", "Científico": "Cientista-Chefe", "Científica": "Cientista-Chefe"}
        }.get(lang, {})

        for c in characters:
            c["role"] = role_dict.get(c.get("role"), c.get("role"))

        # Sluglines y marcadores de guion
        for s in scenes:
            slug = s.get("slugline", "")
            if lang in ["EN", "DE"]:
                slug = slug.replace("NOCHE", "NIGHT").replace("DÍA", "DAY").replace("DIA", "DAY").replace("MADRUGADA", "DAWN").replace("ATARDECER", "DUSK")
            elif lang == "FR":
                slug = slug.replace("NOCHE", "NUIT").replace("DÍA", "JOUR").replace("DIA", "JOUR").replace("MADRUGADA", "AUBE").replace("ATARDECER", "CRÉPUSCULE")
            elif lang == "IT":
                slug = slug.replace("NOCHE", "NOTTE").replace("DÍA", "GIORNO").replace("DIA", "GIORNO").replace("MADRUGADA", "ALBA").replace("ATARDECER", "TRAMONTO")
            elif lang == "PT":
                slug = slug.replace("NOCHE", "NOITE").replace("DÍA", "DIA").replace("MADRUGADA", "MADRUGADA").replace("ATARDECER", "ENTARDECER")
            s["slugline"] = slug

        # Relaciones interpersonales
        rel_type_dict = {
            "EN": {
                "Tensión profesional": "Professional tension",
                "Aliados": "Allies",
                "Rivalidad": "Rivalry",
                "Confianza": "Trust",
                "Mentoría": "Mentorship",
                "Conflictiva": "Conflicted",
                "Amor / Odio": "Love / Hate",
                "Familiar": "Family",
                "Colegas": "Colleagues"
            },
            "FR": {
                "Tensión profesional": "Tension professionnelle",
                "Aliados": "Alliés",
                "Rivalidad": "Rivalité",
                "Confianza": "Confiance",
                "Mentoría": "Mentorat",
                "Conflictiva": "Conflictuelle",
                "Amor / Odio": "Amour / Haine",
                "Familiar": "Familiale",
                "Colegas": "Collègues"
            },
            "DE": {
                "Tensión profesional": "Berufliche Spannung",
                "Aliados": "Verbündete",
                "Rivalidad": "Rivalität",
                "Confianza": "Vertrauen",
                "Mentoría": "Mentorenschaft",
                "Conflictiva": "Konfliktreich",
                "Amor / Odio": "Hassliebe",
                "Familiar": "Familiär",
                "Colegas": "Kollegen"
            }
        }.get(lang, {})
        for r in relationships:
            r["relationship_type"] = rel_type_dict.get(r.get("relationship_type"), r.get("relationship_type"))

    def get_localized_production_intelligence(
        self,
        project_id: str,
        budget_data: Dict[str, Any],
        sustainability_data: Dict[str, Any],
        lang: str = "ES"
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Traduce las 10 categorías de presupuesto y los 6 sectores de sostenibilidad."""
        lang = (lang or "ES").upper()
        if lang == "ES":
            return budget_data, sustainability_data

        # 1. Comprobar caché
        cached = get_project_localization_db(project_id, lang, "production_intelligence")
        if cached and isinstance(cached, dict) and "budget" in cached and "sustainability" in cached:
            return cached["budget"], cached["sustainability"]

        budget_copy = dict(budget_data)
        sust_copy = dict(sustainability_data)

        # Traducir categorías de presupuesto usando diccionario curado
        cat_dict = self.BUDGET_CATEGORIES_I18N.get(lang, self.BUDGET_CATEGORIES_I18N.get("EN", {}))
        en_to_es = {
            "Development & Story Rights": "Desarrollo & Derechos Narrativos",
            "Directing Team & Principal Cast": "Equipo de Dirección & Talento Principal",
            "Technical Crew, Camera & Lighting": "Equipo Técnico, Cámara & Iluminación",
            "Locations, Scouting & Permits": "Locaciones, Scouting & Permisos",
            "Production Design & Art Department": "Diseño de Producción & Utilería",
            "Wardrobe, Hair & Makeup": "Vestuario, Peluquería & Caracterización",
            "Transportation, Fuel & Logistics": "Transporte, Combustible & Logística",
            "Catering & Craft Services": "Catering & Servicios de Rodaje",
            "Post-Production, Sound & Score": "Post-Producción & Sonido / Música",
            "Contingency & Reserve (10%)": "Imprevistos & Contingencia (10%)"
        }
        if "categories" in budget_copy:
            new_cats = []
            for cat in budget_copy["categories"]:
                cat_c = dict(cat)
                c_name = cat_c.get("category", "")
                lookup_key = c_name if c_name in cat_dict else en_to_es.get(c_name, c_name)
                if lookup_key in cat_dict:
                    cat_c["category"] = cat_dict[lookup_key][0]
                    cat_c["description"] = cat_dict[lookup_key][1]
                new_cats.append(cat_c)
            budget_copy["categories"] = new_cats

        if "schedule" in budget_copy and isinstance(budget_copy["schedule"], dict):
            disclaimer_map = {
                "EN": "Estimated planning projection and schedule range based on scene volume, locations, and technical complexity.",
                "FR": "Projection et calendrier prévisionnel basés sur le volume de scènes, les décors et la complexité technique.",
                "DE": "Geschätzte Drehplanprojektion basierend auf Szenenvolumen, Drehorten und technischer Komplexität.",
                "IT": "Proiezione e pianificazione stimata in base al volume di scene, ambientazioni e complessità tecnica.",
                "PT": "Projeção e cronograma estimado com base no volume de cenas, locações e complexidade técnica."
            }
            if lang in disclaimer_map:
                budget_copy["schedule"]["disclaimer"] = disclaimer_map[lang]

        if "methodology" in budget_copy and isinstance(budget_copy["methodology"], dict):
            if lang == "EN":
                budget_copy["methodology"]["title"] = "Cinematic Estimation Methodology"
            elif lang == "FR":
                budget_copy["methodology"]["title"] = "Méthodologie d'Estimation Cinématographique"
                budget_copy["methodology"]["basis_points"] = [
                    f"{len(budget_copy.get('schedule', {}).get('scenes_schedule', []))} scènes analysées",
                    "Séquences nocturnes nécessitant un équipement d'éclairage lourd",
                    "Rémunération du casting principal et de l'équipe de réalisation",
                    f"{budget_copy.get('schedule', {}).get('principal_photography_days', 8)} jours prévus de tournage principal",
                    "Réserve de contingence de 8 à 10% pour imprévus climatiques et de plateau",
                    "Post-production complète avec montage, design sonore surround et étalonnage"
                ]
            elif lang == "DE":
                budget_copy["methodology"]["title"] = "Methodik der Filmischen Budgetkalkulation"
                budget_copy["methodology"]["basis_points"] = [
                    f"{len(budget_copy.get('schedule', {}).get('scenes_schedule', []))} analysierte Szenen",
                    "Nachtdrehs mit speziellem Beleuchtungspaket und Genehmigungen",
                    "Gagen für Hauptcast und Regieteam",
                    f"{budget_copy.get('schedule', {}).get('principal_photography_days', 8)} geplante Hauptdrehtage",
                    "8-10% Sicherheitsrücklage für Wetter- und Motivrisiken",
                    "Vollständige Postproduktion mit Schnitt, Surround-Sounddesign und Color Grading"
                ]
            elif lang == "IT":
                budget_copy["methodology"]["title"] = "Metodologia di Stima Cinematografica"
            elif lang == "PT":
                budget_copy["methodology"]["title"] = "Metodologia de Estimativa Cinematográfica"

        # Traducir sectores de sostenibilidad
        sust_dict = self.SUSTAINABILITY_SECTORS_I18N.get(lang, self.SUSTAINABILITY_SECTORS_I18N.get("EN", {}))
        en_to_es_sust = {
            "Set Construction & Materials (Art Dept)": "Escenografía & Materiales (Sets)",
            "Lighting & Power Grid": "Iluminación & Energía (Lighting)",
            "Transportation & Logistics (Fleet)": "Transporte & Logística (Fleet)",
            "Wardrobe & Character Styling": "Vestuario & Estilismo (Wardrobe)",
            "Catering & Craft Services": "Catering & Hospitalidad (Catering)",
            "Paperless Digital Production Office": "Oficina de Producción Digital (Paperless)"
        }
        if "recommendations" in sust_copy:
            new_recs = []
            for rec in sust_copy["recommendations"]:
                rec_c = dict(rec)
                area = rec_c.get("area", "")
                lookup_area = area if area in sust_dict else en_to_es_sust.get(area, area)
                if lookup_area in sust_dict:
                    rec_c["area"] = sust_dict[lookup_area][0]
                    rec_c["title"] = sust_dict[lookup_area][1]
                    rec_c["recommendation"] = sust_dict[lookup_area][2]
                    rec_c["estimated_impact"] = sust_dict[lookup_area][3]
                new_recs.append(rec_c)
            sust_copy["recommendations"] = new_recs

        labels_i18n = {
            "EN": ("Green Film Shooting Tier II (Certified Sustainable Production)", "Recommendations are directly linked to the specific set requirements, night shoots, and logistics of this film."),
            "FR": ("Tournage Vert Niveau II (Production Éco-Certifiée)", "Les recommandations sont directement liées aux besoins de décor et à la logistique de ce film."),
            "DE": ("Green Shooting Stufe II (Zertifiziert Nachhaltige Produktion)", "Empfehlungen basieren auf den konkreten Motiv- und Nachtdrehanforderungen dieses Films."),
            "IT": ("Green Film Shooting Livello II (Produzione Certificata Sostenibile)", "Le raccomandazioni sono collegate alle esigenze reali di set e logistica di questo film."),
            "PT": ("Selo Verde de Filmagem Nível II (Produção Sustentável Certificada)", "Recomendações fundamentadas nas necessidades reais de set e logística deste filme.")
        }
        if lang in labels_i18n:
            sust_copy["score_label"] = labels_i18n[lang][0]
            sust_copy["methodology"] = labels_i18n[lang][1]

        # Guardar en caché
        try:
            save_project_localization_db(
                project_id, lang, "production_intelligence",
                json.dumps({"budget": budget_copy, "sustainability": sust_copy}, ensure_ascii=False)
            )
        except Exception:
            pass

        return budget_copy, sust_copy

    def localize_chat_messages(self, messages: List[Dict[str, Any]], lang: str = "ES") -> List[Dict[str, Any]]:
        """Traduce los mensajes del chat del Visionario al idioma activo sin mutar el original."""
        lang = (lang or "ES").upper()
        if lang == "ES" or not messages:
            return messages

        localized = []
        for msg in messages:
            m_copy = dict(msg)
            # Si el mensaje fue guardado con directiva de idioma, limpiar el prefijo de visualización
            content = m_copy.get("message") or m_copy.get("text") or ""
            content = re.sub(r'\[Respond strictly in [A-Za-z]+\]\s*', '', content).strip()
            m_copy["message"] = content
            m_copy["text"] = content
            localized.append(m_copy)

        return localized

localization_service = LocalizationService()
