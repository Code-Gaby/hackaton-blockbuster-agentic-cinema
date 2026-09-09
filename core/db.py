import sqlite3
import json
import os
from typing import Dict, List, Any, Optional

DB_FILE = os.path.join(os.path.dirname(__file__), "..", "studio_cinema.db")

def get_connection():
    conn = sqlite3.connect(DB_FILE, timeout=60.0)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 60000;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Creates all relational tables with strict foreign key constraints and seeds sample productions."""
    conn = get_connection()
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
    except Exception:
        pass
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        tagline TEXT,
        genre TEXT,
        format TEXT,
        runtime_minutes INTEGER,
        tone TEXT,
        target_audience TEXT,
        status TEXT,
        progress_percentage INTEGER,
        target_budget REAL,
        estimated_budget REAL,
        shooting_days INTEGER,
        crew_count INTEGER,
        available_locations INTEGER,
        synopsis TEXT,
        logline TEXT,
        visual_aesthetic TEXT,
        eco_impact_score INTEGER,
        age_rating TEXT,
        poster_url TEXT,
        is_demo INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS characters (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        name TEXT NOT NULL,
        age INTEGER,
        role TEXT,
        archetype TEXT,
        occupation TEXT,
        personality TEXT,
        motivation TEXT,
        fears TEXT,
        strengths TEXT,
        weaknesses TEXT,
        emotional_state TEXT,
        wardrobe TEXT,
        birth_date TEXT,
        zodiac_sign TEXT,
        religion_belief TEXT,
        subtext TEXT,
        props_json TEXT,
        dna_json TEXT,
        arc_json TEXT,
        avatar_url TEXT,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS character_relationships (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        source_character_id TEXT NOT NULL,
        target_character_id TEXT NOT NULL,
        target_character_name TEXT,
        rel_type TEXT,
        strength INTEGER,
        history TEXT,
        key_scenes_json TEXT,
        status TEXT,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (source_character_id) REFERENCES characters(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scenes (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        scene_number INTEGER NOT NULL,
        title TEXT,
        slugline TEXT,
        location TEXT,
        interior_exterior TEXT,
        day_night TEXT,
        summary TEXT,
        script_text TEXT,
        subtext TEXT,
        environmental_details TEXT,
        characters_json TEXT,
        props_json TEXT,
        wardrobe_json TEXT,
        vfx_json TEXT,
        sfx_json TEXT,
        complexity TEXT,
        risk_score INTEGER,
        estimated_cost REAL,
        image_url TEXT,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("PRAGMA table_info(scenes)")
    scene_cols = [r[1] for r in cursor.fetchall()]
    if "image_url" not in scene_cols:
        try:
            cursor.execute("ALTER TABLE scenes ADD COLUMN image_url TEXT")
        except Exception:
            pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS budget_options (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        title TEXT,
        description TEXT,
        estimated_savings REAL,
        impact_level TEXT,
        affected_scenes_json TEXT,
        status TEXT,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS project_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT NOT NULL,
        timestamp TEXT,
        event TEXT,
        agent TEXT,
        details TEXT,
        entity_type TEXT,
        entity_id TEXT,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS narrative_changes (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        change_number INTEGER,
        prompt TEXT NOT NULL,
        entity_type TEXT,
        entity_name TEXT,
        severity TEXT,
        impact_explanation TEXT,
        before_state TEXT,
        after_state TEXT,
        affected_scenes_json TEXT,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS project_facts (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        entity_type TEXT,
        entity_id TEXT,
        fact_text TEXT NOT NULL,
        fact_type TEXT DEFAULT 'CANONICAL',
        status TEXT DEFAULT 'ACTIVE',
        scene_established INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scene_versions (
        id TEXT PRIMARY KEY,
        scene_id TEXT NOT NULL,
        project_id TEXT NOT NULL,
        version_number INTEGER NOT NULL,
        scene_snapshot_json TEXT NOT NULL,
        reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS director_preferences (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        preference_type TEXT NOT NULL,
        directive_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS project_research (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        objective TEXT NOT NULL,
        search_queries_json TEXT,
        research_summary TEXT NOT NULL,
        sources_json TEXT,
        target_scope TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS project_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT NOT NULL,
        role TEXT NOT NULL,
        text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS project_localizations (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        lang TEXT NOT NULL,
        section TEXT NOT NULL,
        data_json TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        UNIQUE(project_id, lang, section)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS visual_assets (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        asset_type TEXT NOT NULL,
        model TEXT NOT NULL,
        prompt TEXT NOT NULL,
        prompt_hash TEXT NOT NULL,
        file_path TEXT NOT NULL,
        mime_type TEXT DEFAULT 'image/png',
        width INTEGER DEFAULT 320,
        height INTEGER DEFAULT 320,
        generation_status TEXT DEFAULT 'completed',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
    );
    """)

    # Migration: Add missing columns if database already exists
    for col_query in [
        "ALTER TABLE projects ADD COLUMN is_demo INTEGER DEFAULT 0;",
        "ALTER TABLE projects ADD COLUMN poster_url TEXT;",
        "ALTER TABLE characters ADD COLUMN birth_date TEXT;",
        "ALTER TABLE characters ADD COLUMN zodiac_sign TEXT;",
        "ALTER TABLE characters ADD COLUMN religion_belief TEXT;",
        "ALTER TABLE characters ADD COLUMN subtext TEXT;",
        "ALTER TABLE scenes ADD COLUMN subtext TEXT;",
        "ALTER TABLE scenes ADD COLUMN environmental_details TEXT;"
    ]:
        try:
            cursor.execute(col_query)
            conn.commit()
        except sqlite3.OperationalError:
            pass

    # Ensure all character columns are correctly aligned
    repair_misaligned_character_columns(conn)

    # Seed demo projects if DB has fewer than 3 sample demo projects or incomplete cast
    cursor.execute("SELECT COUNT(*) FROM projects WHERE is_demo = 1")
    demo_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM characters WHERE project_id IN (SELECT id FROM projects WHERE is_demo = 1)")
    demo_chars = cursor.fetchone()[0]
    if demo_count < 3 or demo_chars < 9:
        seed_demo_projects(conn)

    conn.close()

def repair_misaligned_character_columns(conn):
    """Repairs any historical column shifts in characters table."""
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, props_json, dna_json, arc_json, avatar_url, birth_date, zodiac_sign, religion_belief, subtext FROM characters")
    rows = cursor.fetchall()
    for r in rows:
        cid = r[0]
        name = r[1]
        props = r[2]
        dna = r[3]
        arc = r[4]
        avatar = r[5]
        birth = r[6]
        zodiac = r[7]
        religion = r[8]
        subtext = r[9]

        is_shifted = False
        if subtext and (str(subtext).startswith("/assets/") or str(subtext).startswith("http://") or str(subtext).startswith("https://")):
            is_shifted = True
        elif zodiac and (str(zodiac).strip().startswith("{") or str(zodiac).strip().startswith("[")):
            is_shifted = True
        elif avatar and not (str(avatar).startswith("/assets/") or str(avatar).startswith("http://") or str(avatar).startswith("https://") or str(avatar).startswith("data:image")):
            is_shifted = True

        if is_shifted:
            cursor.execute("""
            UPDATE characters SET
                props_json = ?,
                dna_json = ?,
                arc_json = ?,
                avatar_url = ?,
                birth_date = ?,
                zodiac_sign = ?,
                religion_belief = ?,
                subtext = ?
            WHERE id = ?
            """, (birth, zodiac, religion, subtext, props, dna, arc, avatar, cid))
    conn.commit()

def seed_demo_projects(conn):
    """Populates relational database with 3 complete, deep cinematic productions."""
    cursor = conn.cursor()

    # --- PROJECT 1: The Last Signal (DEMO) ---
    p1 = "proj_last_signal"
    cursor.execute("""
    INSERT OR REPLACE INTO projects (
        id, title, tagline, genre, format, runtime_minutes, tone, target_audience,
        status, progress_percentage, target_budget, estimated_budget, shooting_days,
        crew_count, available_locations, synopsis, logline, visual_aesthetic,
        eco_impact_score, age_rating, poster_url, is_demo
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        p1, "The Last Signal (DEMO)",
        "En el silencio del espacio profundo, la primera respuesta es una cuenta regresiva.",
        "Sci-Fi Thriller", "FILM", 110,
        "Suspenso cerebral, atmósfera densa y tensión tecnológica constante",
        "Amantes de la ciencia ficción dura y dramas de supervivencia",
        "PRE-PRODUCCIÓN", 80, 50000.0, 68400.0, 24, 18, 6,
        "Acto I: En la estación de investigación Titán, la astrofísica Elena Vance intercepta una extraña señal matemática de origen no humano. El comandante militar Thorne oculta una directiva clasificada para incinerar el complejo. Acto II: Elena y su hermano David descubren que la señal es una advertencia de colapso atmosférico mientras Thorne desconecta los transmisores de emergencia. Acto III: En una peligrosa caminata espacial sobre los anillos de Saturno, Elena reorienta la antena principal para transmitir la respuesta antes de que la estación sea destruida.",
        "Una astrofísica aislada en una estación de Titán debe burlar a su comandante militar para transmitir la respuesta de la humanidad a una señal extraterrestre antes de que un ataque orbital los destruya a todos.",
        "Iluminación azul neón contra acero mate oscuro, polvo de partículas volumétricas y destellos anamórficos",
        88, "PG-13",
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600&h=350&fit=crop", 1
    ))

    chars_p1 = [
        ("char_elena", p1, "Elena Vance", 34, "Protagonista", "The Visionary", "Astrofísica Principal",
         "Tenaz, analítica, reservada", "Decodificar la señal y salvar a la tripulación", "Perder a su hermano David",
         "Decodificación cuántica y astrofísica", "Dificultad para confiar en la autoridad", "Determinada",
         "Traje térmico de vuelo y visor de análisis espectral",
         "14 de Julio de 1990", "Cáncer ♋", "Racionalismo Empírico",
         "Siente la carga de salvar a su hermano por encima de cualquier orden militar.",
         json.dumps(["Receptor Cuántico", "Data Pad", "Reloj analógico"]),
         json.dumps({"courage": 94, "intelligence": 96, "empathy": 85, "resilience": 90, "creativity": 92, "ambition": 88}),
         json.dumps({"Act I": "Aislamiento en Titán", "Act II": "Descubre la traición de Thorne", "Act III": "Transmisión final sobre los anillos"}),
         "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=300&h=300&fit=crop"),
        ("char_marcus", p1, "Marcus Thorne", 48, "Antagonista", "The Ruler", "Comandante Militar de la Estación",
         "Pragmático, autoritario, implacable", "Cumplir la Directiva 99 de exterminio de datos", "El caos civil en la Tierra",
         "Estrategia táctica y combate militar", "Paranoia de seguridad", "Tensión constante",
         "Uniforme de gala militar gris con funda táctica de plasma",
         "3 de Noviembre de 1976", "Escorpio ♏", "Doctrina Militar y Orden Absoluto",
         "Teme perder el control de la estación ante una inteligencia incomprensible.",
         json.dumps(["Tarjeta Maestra", "Pistola de plasma"]),
         json.dumps({"courage": 86, "intelligence": 84, "empathy": 40, "resilience": 88, "creativity": 65, "ambition": 95}),
         json.dumps({"Act I": "Bloqueo de investigación", "Act II": "Purga de servidores", "Act III": "Confrontación en el puente"}),
         "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300&h=300&fit=crop"),
        ("char_david", p1, "David Vance", 29, "Aliado Clave", "The Heroic Sibling", "Ingeniero en Jefe",
         "Empático, creativo, protector", "Proteger a Elena y sostener los sistemas de vida", "Fallo del reactor central",
         "Ingeniería de reactores y soldadura de plasma", "Vulnerabilidad física", "Alerta",
         "Mono de trabajo de mecánico espacial con cinturón de herramientas",
         "28 de Febrero de 1995", "Piscis ♓", "Humanismo Tecnológico",
         "Desea regresar a la Tierra para ver los océanos una vez más.",
         json.dumps(["Escáner de diagnóstico", "Antorcha de plasma"]),
         json.dumps({"courage": 80, "intelligence": 86, "empathy": 94, "resilience": 82, "creativity": 88, "ambition": 60}),
         json.dumps({"Act I": "Alerta sobre el reactor", "Act II": "Desvío de energía a la antena", "Act III": "Reparación crítica en el exterior"}),
         "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=300&h=300&fit=crop")
    ]
    for c in chars_p1:
        cursor.execute("""
        INSERT OR REPLACE INTO characters (
            id, project_id, name, age, role, archetype, occupation, personality,
            motivation, fears, strengths, weaknesses, emotional_state, wardrobe,
            birth_date, zodiac_sign, religion_belief, subtext,
            props_json, dna_json, arc_json, avatar_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, c)

    rels_p1 = [
        ("rel_1", p1, "char_elena", "char_marcus", "Marcus Thorne", "CONFLICT", 95, "Fricción irreconciliable por la censura de la señal de espacio profundo.", json.dumps([2, 6, 12]), "Crítica"),
        ("rel_2", p1, "char_elena", "char_david", "David Vance", "ALLIANCE", 98, "Hermanos unidos por un instinto protector y lealtad absoluta.", json.dumps([1, 4, 10]), "Inquebrantable")
    ]
    for r in rels_p1:
        cursor.execute("INSERT OR REPLACE INTO character_relationships VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", r)

    scenes_p1 = [
        ("INT. CÚPULA DE OBSERVACIÓN DE TITÁN - NOCHE", "Elena detecta un pulso armónico proveniente del sector Kepler.", "Elena sospecha que el pulso no es natural.", "Luces de instrumentos parpadeando en la oscuridad."),
        ("INT. SALA DE REACTORES SUB-NIVEL 3 - NOCHE", "David repara sobrecargas producidas por la frecuencia anómala.", "David teme que el núcleo colapse si continúan recibiendo datos.", "Zumbido sordo de alta frecuencia."),
        ("INT. DESPACHO DEL COMANDANTE - MADRUGADA", "Thorne recibe la Directiva 99 ordenando la purga inmediata de la estación.", "Thorne se convence de que ocultar la señal es por el bien común.", "Monitores holográficos en rojo."),
        ("INT. LABORATORIO DE ASTROFÍSICA - DÍA", "Elena decodifica los números primos inscritos en la transmisión.", "La maravilla científica supera el miedo inicial.", "Haz de luz dorada cruzando la sala."),
        ("EXT. PASARELA EXTERIOR DE TITÁN - ESPACIO", "David y Elena inspeccionan el nodo emisor en medio de tormentas de metano.", "Conciencia extrema de la fragilidad humana en el vacío.", "Anillos de Saturno brillando en el fondo."),
        ("INT. SALA DE SEGURIDAD - NOCHE", "Thorne confina a los científicos y bloquea el acceso a la antena.", "Tensión de un motín inminente.", "Pasos pesados de guardias blindados."),
        ("INT. CONDUCTOS DE MANTENIMIENTO - NOCHE", "Elena se infiltra hacia el núcleo de comunicaciones.", "Foco mental absoluto en alcanzar el panel.", "Vapor frío saliendo de las juntas."),
        ("INT. PUENTE DE MANDO CENTRAL - AMANECER", "Elena confronta a Thorne y transmite el mensaje a la Tierra.", "El deber cumplido trasciende las consecuencias personales.", "Luz azul de transmisión iluminando el puente.")
    ]
    for i, (slug, sum_text, sub_txt, env_txt) in enumerate(scenes_p1, 1):
        cursor.execute("""
        INSERT OR REPLACE INTO scenes (
            id, project_id, scene_number, title, slugline, location, interior_exterior,
            day_night, summary, script_text, subtext, environmental_details,
            characters_json, props_json, wardrobe_json, vfx_json, sfx_json,
            complexity, risk_score, estimated_cost
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"scene_p1_{i}", p1, i, f"Escena {i}: Sector {i}", slug, "Estación Titán", "INT" if "INT." in slug else "EXT", "NIGHT" if "NOCHE" in slug or "MADRUGADA" in slug else "DAY",
            sum_text, {
                1: f"{slug}\n\nFADE IN:\n\n{sum_text}\n\nELENA\n(ajustando el filtro espectral)\nDavid, no son pulsos aleatorios de magnetosfera. El armónico se repite cada tres segundos en base binaria. No es estática solar.\n\nDAVID\n(acercándose al osciloscopio)\nSi esto proviene de fuera del cinturón, la estación acaba de convertirse en el lugar más peligroso del sistema solar. Thorne no debe enterarse hasta que verifiquemos la paridad.\n\nELENA\n(bloqueando el disco de registro)\nYa es tarde para esconderlo. La antena matriz ya está acoplada al haz.\n\nCUT TO:",
                2: f"{slug}\n\nFADE IN:\n\n{sum_text}\n\nTHORNE\n(cerrando la terminal con frialdad)\nLa Directiva 99 no admite debates científicos, Elena. Titán no es un observatorio universitario; es una instalación clasificada de la Flota.\n\nELENA\n(sin retroceder un paso)\nOcultar este mensaje no protegerá a la colonia, Comandante. Solo garantizará que cuando alcancen nuestra órbita, estemos indefensos y a oscuras.\n\nTHORNE\n(en voz baja, amenazante)\nEl orden se mantiene controlando la verdad. Si vuelve a tocar la antena transmisora, la consideraré insubordinación en tiempo de crisis.\n\nCUT TO:",
                3: f"{slug}\n\nFADE IN:\n\n{sum_text}\n\nELENA\n(con los ojos fijos en la cascada de datos)\nSon números primos entrelazados en doce dimensiones. No buscan amenazarnos, David... están entregando las coordenadas de un punto de encuentro fuera de Saturno.\n\nDAVID\n(comprobando el enfriamiento de los servidores)\nSi Thorne ejecuta el formateo de los bancos de memoria a las seis, perderemos la clave de desencriptación.\n\nELENA\n(copiando los bloques al chip neural)\nNo lo hará. Porque voy a transferir la matriz completa a mi terminal portátil antes de que corten la energía.\n\nCUT TO:",
                4: f"{slug}\n\nFADE IN:\n\n{sum_text}\n\nDAVID\n(a través del comunicador de su casco)\nEl viento criogénico desalineó los servos del reflector doce. Si perdemos la línea visual con la Tierra durante la tormenta, el enlace colapsará.\n\nELENA\n(sujetando el arnés de titanio al riel de guía)\nSostén el calibrador manual, David. Mientras este traje tenga oxígeno, no voy a dejar que Thorne desconecte la señal.\n\nDAVID\n(asegurando la escuadra con esfuerzo)\n¡El servo encajó! Pero los sensores térmicos acaban de detectar actividad en la esclusa tres: Thorne envió a su equipo de asalto.\n\nCUT TO:",
                5: f"{slug}\n\nFADE IN:\n\n{sum_text}\n\nTHORNE\n(bloqueando la consola con su llave biométrica)\nQuedan relevados formalmente de sus cargos de investigación. La estación entra en estado de sitio bajo comando militar directo.\n\nELENA\n(enfrentándolo con serenidad imperturbable)\nPodrá encerrar nuestros cuerpos en este módulo, Marcus, pero el paquete de datos ya cruzó el relé primario. No puede fusilar una señal de radio.\n\nTHORNE\n(acercándose al cristal de contención)\nTal vez no pueda fusilarla, doctora Vance. Pero puedo incinerar el transmisor antes de que la señal salga de la ionosfera.\n\nCUT TO:",
                6: f"{slug}\n\nFADE IN:\n\n{sum_text}\n\nELENA\n(en un susurro entrecortado al comunicador)\nDavid, estoy en el conducto de ventilación del nivel cuatro, justo sobre el puente. El cableado de emergencia todavía tiene tensión.\n\nDAVID (V.O.)\n(estática en el auricular)\nCuidado con los sensores de presión. Los hombres de Thorne están barriendo los pasillos inferiores con rifles sónicos. Te quedan tres minutos.\n\nELENA\n(desatornillando la rejilla de acceso)\nEs tiempo de sobra. Nos vemos del otro lado de la historia.\n\nCUT TO:",
                7: f"{slug}\n\nFADE IN:\n\n{sum_text}\n\nTHORNE\n(con el dedo sobre el gatillo, temblando de rabia)\nSi activa esa emisión, ocho mil millones de personas en la Tierra sabrán que no estamos solos... y la civilización entera entrará en histeria.\n\nELENA\n(con la mano firme sobre el pulsador maestro)\nLa verdad nunca ha destruido a una civilización, Thorne. Lo que nos destruye es vivir arrodillados en el engaño.\n\nCUT TO:",
                8: f"{slug}\n\nFADE IN:\n\n{sum_text}\n\nDAVID\n(observando la cascada de confirmaciones en verde)\nGinebra, la Estación Luna Uno y el observatorio de Marte confirman recepción simultánea. Ya no hay marcha atrás, Elena.\n\nELENA\n(mirando a través del ventanal hacia la inmensidad de Saturno)\nLa frecuencia ya no está atrapada en Titán... Ahora le pertenece al futuro de la humanidad.\n\nFADE OUT."
            }.get(i, f"{slug}\n\nFADE IN:\n\n{sum_text}\n\nCUT TO:"),
            sub_txt, env_txt,
            json.dumps(["Elena Vance", "David Vance"]), json.dumps(["Data Pad"]), json.dumps(["Traje espacial"]),
            json.dumps(["Resplandor azul"]), json.dumps(["Pulso de señal"]), "HIGH" if "EXT" in slug else "MEDIUM", 50, 2400.0
        ))

    # --- PROJECT 2: The Future Woman (1995) ---
    p2 = "proj_future_woman"
    cursor.execute("""
    INSERT OR REPLACE INTO projects (
        id, title, tagline, genre, format, runtime_minutes, tone, target_audience,
        status, progress_percentage, target_budget, estimated_budget, shooting_days,
        crew_count, available_locations, synopsis, logline, visual_aesthetic,
        eco_impact_score, age_rating, poster_url, is_demo
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        p2, "The Future Woman (1995)",
        "El pasado no se recuerda... se rebobina.",
        "Cyberpunk / Neo-Noir", "FILM", 105,
        "Nostálgico, eléctrico, cinematográfico, intrigante",
        "Amantes del cine de culto y ciencia ficción retrofuturista",
        "DESARROLLO DE GUION", 75, 85000.0, 78000.0, 30, 24, 8,
        "Acto I: En un 1995 alternativo de neón y celuloide, Elara Vega es una restauradora de películas que descubre cómo proyectar su conciencia dentro de las cintas de 35mm. Acto II: Al encontrar una cinta clasificada que prueba la conspiración mediática de Marcus Vale, Elara y la sonidista Sofía son perseguidas por las calles lluviosas. Acto III: En la sala de proyección de la torre de transmisión, Elara proyecta la cinta prohibida a toda la ciudad.",
        "Una restauradora de metraje en 1995 descubre que puede viajar a través de las cintas de 35mm y desentrañar una conspiración corporativa antes de que destruyan el archivo.",
        "Grano cálido de 35mm, tonos ámbar y rojo rubí, monitores CRT y luces de neón bajo lluvia urbana",
        92, "PG-13",
        "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=600&h=350&fit=crop", 1
    ))

    chars_p2 = [
        ("char_elara_fw", p2, "Elara Vega", 28, "Protagonista", "The Visionary", "Restauradora de Metraje",
         "Intuitiva, audaz, obsesiva", "Descubrir el origen de la cinta perdida", "El olvido",
         "Salto en celuloide, memoria fotográfica", "Desconfianza", "Inspirada",
         "Chaqueta de cuero granate y pañuelo 90s",
         "19 de Mayo de 1967", "Tauro ♉", "Memoria Histórica y Cine Auténtico",
         "Está convencida de que el celuloide guarda las almas de quienes fueron filmados.",
         json.dumps(["Lente Anamórfico", "Bobina Maestra"]),
         json.dumps({"courage": 94, "intelligence": 92, "empathy": 80, "resilience": 88, "creativity": 96, "ambition": 75}),
         json.dumps({"Act I": "Halla la cinta de 1995", "Act II": "Ingresa al metraje", "Act III": "Proyección final"}),
         "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=300&h=300&fit=crop"),
        ("char_marcus_fw", p2, "Marcus Vale", 52, "Antagonista", "The Shadow", "Magnate de Medios",
         "Implacable, sofisticado, frío", "Controlar la narrativa histórica de la ciudad", "Exposición pública",
         "Influencia mediática y poder legal", "Arrogancia", "Dominante",
         "Traje sastre gris marengo de tres piezas",
         "11 de Agosto de 1943", "Leo ♌", "Poder Mediático Corporativo",
         "Cree que la verdad es un producto que se edita para las masas.",
         json.dumps(["Contrato de Destrucción", "Encendedor de Oro"]),
         json.dumps({"courage": 82, "intelligence": 90, "empathy": 30, "resilience": 85, "creativity": 70, "ambition": 98}),
         json.dumps({"Act I": "Ordena incautar el archivo", "Act II": "Cacería mediática", "Act III": "Derrota en la sala de proyección"}),
         "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=300&h=300&fit=crop"),
        ("char_sofia_fw", p2, "Sofía Ríos", 31, "Aliada", "The Sound Master", "Sonidista de Estudio",
         "Aguda, perspicaz, empática", "Revelar las frecuencias ocultas de la cinta", "Censura total",
         "Aislamiento de audio analógico", "Cautela excesiva", "Concentrada",
         "Auriculares profesionales y chaleco de sonido",
         "5 de Octubre de 1964", "Libra ♎", "Armonía y Pureza Acústica",
         "Protege a Elara como a una hermana menor frente al peligro corporativo.",
         json.dumps(["Grabadora de Cinta", "Micrófono Shotgun"]),
         json.dumps({"courage": 76, "intelligence": 89, "empathy": 92, "resilience": 82, "creativity": 90, "ambition": 65}),
         json.dumps({"Act I": "Filtra la pista de voz", "Act II": "Aísla la pista 4", "Act III": "Emisión radial pública"}),
         "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=300&h=300&fit=crop")
    ]
    for c in chars_p2:
        cursor.execute("""
        INSERT OR REPLACE INTO characters (
            id, project_id, name, age, role, archetype, occupation, personality,
            motivation, fears, strengths, weaknesses, emotional_state, wardrobe,
            birth_date, zodiac_sign, religion_belief, subtext,
            props_json, dna_json, arc_json, avatar_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, c)

    rels_p2 = [
        ("rel_fw_1", p2, "char_elara_fw", "char_marcus_fw", "Marcus Vale", "CONFLICT", 90, "Enemistad mortal por el control del archivo histórico de 35mm.", json.dumps([2, 5, 8]), "Crítica"),
        ("rel_fw_2", p2, "char_elara_fw", "char_sofia_fw", "Sofía Ríos", "ALLIANCE", 92, "Compañeras de estudio y edición con complicidad absoluta.", json.dumps([1, 4, 7]), "Inquebrantable")
    ]
    for r in rels_p2:
        cursor.execute("INSERT OR REPLACE INTO character_relationships VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", r)

    scenes_p2 = [
        ("INT. TALLER DE RESTAURACIÓN DE METRAJE - DÍA", "Elara limpia una vieja cinta de 35mm y ve siluetas moverse solas en el fotograma.", "Fascinación y vértigo temporal.", "Olor a químicos de revelado y polvo."),
        ("INT. SALA DE EDICIÓN DE AUDIO - NOCHE", "Sofía aísla la pista oculta que contiene la voz de Marcus Vale dando órdenes de demolición.", "Tensión de descubrir una conspiración real.", "Cintas magnéticas girando acompasadas."),
        ("EXT. CALLES DE LA CIUDAD BAJO LLUVIA - NOCHE", "Elara y Sofía escapan en un automóvil clásico mientras son seguidas por vehículos negros.", "Pánico y adrenalina pura.", "Luces de neón reflejadas en el asfalto mojado."),
        ("INT. CINE DE BARRIO ABANDONADO - MADRUGADA", "Elara proyecta la cinta en la pantalla gigante y su mente se transporta a 1995.", "Trascendencia dimensional.", "Polvo de celuloide suspendido en el haz ámbar."),
        ("INT. TORRE TRANSMISORA DE VALE MEDIA - AMANECER", "Elara conecta el proyector maestro a la antena matriz para emitir la verdad.", "Determinación victoriosa.", "Viento de gran altura y zumbido de transformadores.")
    ]
    for i, (slug, sum_text, sub_txt, env_txt) in enumerate(scenes_p2, 1):
        cursor.execute("INSERT OR REPLACE INTO scenes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
            f"scene_p2_{i}", p2, i, f"Escena {i}: Celuloide", slug, "Estudio 1995", "INT" if "INT." in slug else "EXT", "NIGHT" if "NOCHE" in slug or "MADRUGADA" in slug else "DAY",
            sum_text, {
                1: f"{slug}\n\nFADE IN:\n\n{sum_text}\n\nELARA\n(con el cuenta-hilos sobre el fotograma 412)\nSofía, mira el margen derecho de este negativo. La silueta que camina junto a la farola no figuraba en la copia de estreno comercial de 1995.\n\nSOFÍA\n(limpiando el cabezal de la moviola)\nDebe ser una mancha de vinagre por descomposición química, Elara. Esa bobina pasó treinta años en una caja fuerte oxidada.\n\nELARA\n(moviendo la manivela despacio)\nNo es vinagre. Respira, Sofía. El celuloide fue cortado y reensamblado para ocultar a un testigo.\n\nCUT TO:",
                2: f"{slug}\n\nFADE IN:\n\n{sum_text}\n\nSOFÍA\n(deteniendo la cinta con el dedo)\nAislé la pista óptica a cuatrocientos hertzios. Debajo de la música ambiental se escucha claramente la orden: Marcus Vale ordenó la demolición deliberada del archivo.\n\nELARA\n(mirando fijamente los altavoces de estudio)\nEsa grabación demuestra que no fue un accidente fortuito. Destruyeron el barrio entero para construir su torre mediática.\n\nSOFÍA\n(guardando el casete maestro en su chaqueta)\nSi Vale descubre que pudimos recomponer este audio, no saldremos vivas de este edificio.\n\nCUT TO:",
                3: f"{slug}\n\nFADE IN:\n\n{sum_text}\n\nELARA\n(abrazando la lata metálica sellada)\nSaben exactamente lo que llevamos. No quieren recuperar el dinero, Sofía... van a quemar el negativo maestro.\n\nSOFÍA\n(pisando el acelerador y doblando bruscamente)\nSujétate bien. Si logramos cruzar el paso bajo nivel antes de que bajen la barrera ferroviaria, los dejamos atrás.\n\nELARA\n(mirando los faros amenazantes acercarse)\n¡Acelera, no frenes por nada!\n\nCUT TO:",
                4: f"{slug}\n\nFADE IN:\n\n{sum_text}\n\nELARA\n(ajustando el foco de la lente anamórfica)\nMira la pantalla... Cuando la luz de carbón atraviesa este grano, el tiempo no se pierde; se revela tal como ocurrió.\n\nSOFÍA\n(conectando el cable coaxial al transmisor pirata)\nLa señal de la moviola está sincronizada con la antena del tejado. En cuanto enciendas el arco, la película saldrá en directo por el canal seis.\n\nELARA\n(con emoción contenida)\nQue toda la ciudad vea lo que quisieron borrar.\n\nCUT TO:",
                5: f"{slug}\n\nFADE IN:\n\n{sum_text}\n\nMARCUS VALE\n(con voz gélida, acomodándose la corbata)\nUn metraje de archivo no es un tribunal de justicia, señorita Vega. La historia la escriben quienes compran las cadenas de televisión.\n\nELARA\n(cerrando la caja de fusibles con candado)\nYa no más, señor Vale. Esta mañana el celuloide habló... y su imperio se acaba de quedar sin señal.\n\nFADE OUT."
            }.get(i, f"{slug}\n\nFADE IN:\n\n{sum_text}\n\nCUT TO:"),
            sub_txt, env_txt,
            json.dumps(["Elara Vega", "Sofía Ríos"]), json.dumps(["Bobina 35mm"]), json.dumps(["Chaqueta granate"]),
            json.dumps(["Grano de película"]), json.dumps(["Zumbido de proyector"]), "MEDIUM", 40, 1800.0
        ))

    # --- PROJECT 3: El Secreto de San Lorenzo ---
    p3 = "proj_san_lorenzo"
    cursor.execute("""
    INSERT OR REPLACE INTO projects (
        id, title, tagline, genre, format, runtime_minutes, tone, target_audience,
        status, progress_percentage, target_budget, estimated_budget, shooting_days,
        crew_count, available_locations, synopsis, logline, visual_aesthetic,
        eco_impact_score, age_rating, poster_url, is_demo
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        p3, "El Secreto de San Lorenzo",
        "En las profundidades del Caribe panameño, la historia que nos contaron fue sumergida a propósito.",
        "Historical Mystery", "FILM", 115,
        "Intriga arqueológica, tensión histórica y atmósfera marina profunda",
        "Amantes del cine de misterio histórico, arqueología y dramas de época",
        "PRE-PRODUCCIÓN", 70, 75000.0, 72000.0, 26, 22, 7,
        "Acto I: La arqueóloga marina Dra. Marina Silva llega a las ruinas del Fuerte San Lorenzo en Portobelo tras descifrar una bitácora naval de 1740 que apunta a un galeón hundido. Acto II: Aliada con el experimentado Capitán Mateo Ruiz, Marina localiza los restos del navío en las aguas protegidas de Isla Coiba, pero el financista privado Dr. Alejandro Vance intenta apropiarse del tesoro cultural por la fuerza. Acto III: Durante una tormenta en altamar, Marina rescata el códice colonial y asegura la preservación del patrimonio para el museo nacional.",
        "Una arqueóloga marina panameña debe arriesgar su vida en las aguas traicioneras de Coiba para recuperar un códice colonial antes de que un coleccionista privado lo saquee para siempre.",
        "Tonos turquesa y ámbar salino, piedra colonial con pátina de musgo, contraluces dorados al amanecer tropical y grano cálido de 35mm.",
        94, "PG-13",
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600&h=350&fit=crop", 1
    ))

    chars_p3 = [
        ("char_marina_sl", p3, "Dra. Marina Silva", 34, "Protagonista", "The Dedicated Scholar", "Arqueóloga Marina e Historiadora",
         "Tenaz, analítica, apasionada por la memoria histórica", "Recuperar el códice de San Lorenzo y proteger el patrimonio de la nación", "La pérdida irreparable de la historia",
         "Arqueología subacuática, paleografía colonial y navegación náutica", "Terquedad obsesiva y desconfianza hacia inversionistas", "Determinada",
         "Traje de neopreno con arnés de buceo, camisa de lino beige y colgante de cuarzo marino",
         "12 de Octubre de 1990", "Libra ♎", "Humanismo Cultural y Respeto a los Océanos",
         "Lleva el peso de reivindicar el legado de su familia de historiadores panameños.",
         json.dumps(["Bitácora Naval de 1740", "Brújula Náutica de Latón", "Cámara Submarina 4K"]),
         json.dumps({"courage": 92, "intelligence": 96, "empathy": 88, "resilience": 90, "creativity": 85, "ambition": 78}),
         json.dumps({"Act I": "Llegada a Portobelo y hallazgo del mapa", "Act II": "Inmersión en Coiba y enfrentamiento con Vance", "Act III": "Rescate del códice en la tormenta"}),
         "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=300&h=300&fit=crop"),

        ("char_mateo_sl", p3, "Capitán Mateo Ruiz", 46, "Aliado Clave", "The Sea Captain", "Capitán de Navío y Navegante",
         "Pragmático, taciturno, leal y observador", "Proteger a Marina y navegar las corrientes de Coiba", "Naufragio en aguas remotas",
         "Navegación en arrecifes, mecánica naval y serenidad bajo presión", "Cansancio acumulado", "Alerta",
         "Chubasquero amarillo de pescador sobre camiseta azul descolorida y gorra gastada",
         "24 de Agosto de 1978", "Virgo ♍", "Código de Honor Marino",
         "Encontró en la expedición de Marina una segunda oportunidad tras perder su antiguo barco.",
         json.dumps(["Cuchillo de Buceo Titán", "Carta Náutica del Pacífico", "Silbato Náutico"]),
         json.dumps({"courage": 90, "intelligence": 82, "empathy": 80, "resilience": 95, "creativity": 72, "ambition": 60}),
         json.dumps({"Act I": "Acepta guiar la expedición a Coiba", "Act II": "Maniobras evasivas frente al barco de Vance", "Act III": "Soporte vital en la inmersión crítica"}),
         "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300&h=300&fit=crop"),

        ("char_alejandro_sl", p3, "Dr. Alejandro Vance", 52, "Antagonista", "The Ruthless Collector", "Magnate de Antigüedades",
         "Sofisticado, elocuente, frío y calculador", "Asegurar el códice para una subasta clandestina en Ginebra", "El descrédito internacional y la confiscación legal",
         "Poder económico, tecnología de sonar militar y manipulación diplomática", "Subestimar a los habitantes locales", "Dominante",
         "Guayabera de lino blanco a medida, reloj náutico suizo y bastón con empuñadura de plata",
         "15 de Marzo de 1972", "Piscis ♓", "El Valor de Mercado Absoluto",
         "Cree que el arte y la historia sólo pertenecen a quienes tienen los recursos para comprarlos.",
         json.dumps(["Contrato de Concesión Falso", "Teléfono Satelital Encriptado"]),
         json.dumps({"courage": 75, "intelligence": 92, "empathy": 20, "resilience": 82, "creativity": 78, "ambition": 98}),
         json.dumps({"Act I": "Intenta sobornar a Marina en la capital", "Act II": "Despliega su yate artillado en Coiba", "Act III": "Derrota legal y captura en el muelle"}),
         "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=300&h=300&fit=crop")
    ]

    for c in chars_p3:
        cursor.execute("""
        INSERT OR REPLACE INTO characters (
            id, project_id, name, age, role, archetype, occupation, personality,
            motivation, fears, strengths, weaknesses, emotional_state, wardrobe,
            birth_date, zodiac_sign, religion_belief, subtext,
            props_json, dna_json, arc_json, avatar_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, c)

    rels_p3 = [
        ("rel_sl_1", p3, "char_marina_sl", "char_mateo_sl", "Capitán Mateo Ruiz", "ALLIANCE", 94, "Confianza y respeto mutuo forjados en las aguas profundas del Pacífico. Mateo es su ancla protectora en el mar.", json.dumps([1, 3, 5]), "Inquebrantable"),
        ("rel_sl_2", p3, "char_marina_sl", "char_alejandro_sl", "Dr. Alejandro Vance", "CONFLICT", 92, "Enconada disputa ética y legal por el destino de las reliquias sumergidas. Conflicto directo e irreconciliable.", json.dumps([2, 4]), "Crítica")
    ]

    for r in rels_p3:
        cursor.execute("INSERT OR REPLACE INTO character_relationships VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", r)

    scenes_p3 = [
        ("EXT. RUINAS DEL FUERTE SAN LORENZO, PORTOBELO - AMANECER", "Marina examina un mapa tallado en una piedra de sillería frente al Mar Caribe.", "Fascinación arqueológica contenida.", "Niebla salina y olas rompiendo contra las murallas."),
        ("INT. ARCHIVO HISTÓRICO DEL CASCO VIEJO - DÍA", "Alejandro Vance confronta a Marina advirtiéndole que abandone la investigación del galeón.", "Tensión cortante entre la academia y el dinero sucio.", "Olor a papel añejo y sombras de celosías coloniales."),
        ("EXT. EMBARCACIÓN 'LA ESPERANZA' EN AGUAS DE COIBA - NOCHE", "Mateo y Marina detectan las señales de sonar del navío sumergido en medio de una mar picada.", "Adrenalina y concentración náutica extrema.", "Luces verdes del sonar reflejadas en los visores mojados."),
        ("EXT. FONDO MARINO DEL ARRECIFE DE SAN LORENZO - DÍA", "Marina realiza una inmersión a 40 metros y localiza el cofre de plomo con el códice intacto.", "Silencio abisal majestuoso y peligro inminente.", "Corales de fuego y haces de sol atravesando el agua cristalina."),
        ("INT. CUBIERTA PRINCIPAL BAJO LA TORMENTA - ATARDECER", "Marina y Mateo aseguran el tesoro y eluden la intercepción del yate de Vance.", "Triunfo moral y heroísmo noble.", "Lluvia torrencial y sirenas de guardacostas al horizonte.")
    ]

    for i, (slug, sum_text, sub_txt, env_txt) in enumerate(scenes_p3, 1):
        cursor.execute("""
        INSERT OR REPLACE INTO scenes (
            id, project_id, scene_number, title, slugline, location, interior_exterior,
            day_night, summary, script_text, subtext, environmental_details,
            characters_json, props_json, wardrobe_json, vfx_json, sfx_json,
            complexity, risk_score, estimated_cost
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"scene_p3_{i}", p3, i, f"Escena {i}: San Lorenzo", slug, "Panamá", "INT" if "INT." in slug else "EXT", "NIGHT" if "NOCHE" in slug else ("DUSK" if "ATARDECER" in slug else "DAY"),
            sum_text, {
                1: f"{slug}\n\nFADE IN:\n\n{sum_text}\n\nDRA. MARINA SILVA\n(soplando el polvo de sillería)\nMira la orientación de esta cruz náutica, Mateo. No apunta hacia la rada de Portobelo... marca directamente los bajos del arrecife en Coiba.\n\nCAPITÁN MATEO RUIZ\n(observando el oleaje con prismáticos gastados)\nEsas aguas tienen corrientes cruzadas y fondos de roca viva, Marina. Muy pocos capitanes se atreven a navegar ese canal con tormenta.\n\nDRA. MARINA SILVA\n(guardando el calco en su portafolios estanco)\nEl galeón San Jerónimo descansó allí trescientos años. Nosotros seremos los primeros en sacarlo a la luz.\n\nCUT TO:",
                2: f"{slug}\n\nFADE IN:\n\n{sum_text}\n\nDR. ALEJANDRO VANCE\n(con tono cordial pero venenoso)\nUn códice del siglo dieciocho pertenece a una colección privada con conservación climatizada, estimada doctora. No a las vitrinas con humedad de un museo público.\n\nDRA. MARINA SILVA\n(cerrando la vitrina de pergaminos con llave)\nEl patrimonio de nuestra gente no es una moneda de cambio para subastas clandestinas en Europa, Vance. Sus ofertas no tienen cabida aquí.\n\nDR. ALEJANDRO VANCE\n(sonriendo con frialdad)\nEl mar es muy profundo y solitario, doctora Silva. Sería una lástima que su expedición sufriera un percance inesperado en Coiba.\n\nCUT TO:",
                3: f"{slug}\n\nFADE IN:\n\n{sum_text}\n\nCAPITÁN MATEO RUIZ\n(marcando las coordenadas en la carta náutica)\nEl sonar confirma el casco a treinta y ocho metros de profundidad, encajado entre dos bancos de coral.\n\nDRA. MARINA SILVA\n(ajustando el arnés del tanque de buceo)\nPrepara el cabestrante y la línea de vida, Mateo. Voy a sumergirme antes de que el yate de Vance entre en este sector.\n\nCAPITÁN MATEO RUIZ\n(revisando el manómetro con firmeza)\nTienes cuarenta minutos de gas de fondo, Marina. Al menor indicio de marejada, abortamos.\n\nCUT TO:",
                4: f"{slug}\n\nFADE IN:\n\n{sum_text}\n\nDRA. MARINA SILVA\n(por el intercomunicador subacuático del casco)\nMateo... lo encontré. El arcón de plomo con el sello virreinal está intacto bajo el sedimento.\n\nCAPITÁN MATEO RUIZ (V.O.)\n(por la radio de superficie)\n¡Engancha las eslingas de sustentación rápido! El radar acaba de marcar una embarcación de alta velocidad aproximándose por el este.\n\nDRA. MARINA SILVA\n(inflando el globo de rescate subacuático)\nEslingas aseguradas. El códice sube a la superficie ahora mismo.\n\nCUT TO:",
                5: f"{slug}\n\nFADE IN:\n\n{sum_text}\n\nDR. ALEJANDRO VANCE\n(a través de un megáfono náutico)\n¡Entreguen el contenedor colonial y les remolcaré hasta tierra firme antes de que el temporal hunda su cascarón!\n\nDRA. MARINA SILVA\n(sosteniendo el cofre sellado junto a la baliza de emergencia)\n¡Llegas tarde, Alejandro! Las patrulleras de la guardia costera acaban de responder a nuestra señal de satélite.\n\nCAPITÁN MATEO RUIZ\n(sonriendo exhausto al timón)\nNuestra historia se queda en casa, Marina.\n\nFADE OUT."
            }.get(i, f"{slug}\n\nFADE IN:\n\n{sum_text}\n\nCUT TO:"),
            sub_txt, env_txt,
            json.dumps(["Dra. Marina Silva", "Capitán Mateo Ruiz"] if i != 2 else ["Dra. Marina Silva", "Dr. Alejandro Vance"]),
            json.dumps(["Bitácora Naval de 1740"]), json.dumps(["Traje de buceo"]),
            json.dumps(["Destello subacuático"]), json.dumps(["Oleaje rompiente"]),
            "HIGH" if "EXT" in slug else "MEDIUM", 45, 2500.0
        ))

    conn.commit()

    conn.commit()

# Database CRUD Helper Functions
def get_all_projects_db() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*,
               (SELECT COUNT(*) FROM characters WHERE project_id = p.id) AS character_count,
               (SELECT COUNT(*) FROM scenes WHERE project_id = p.id) AS scene_count
        FROM projects p
        ORDER BY p.created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_project_db(project_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_project_db(title: str, genre: str, format_type: str, budget: float, logline: str = "", poster_url: str = "") -> str:
    """Creates a 100% EMPTY clean project in SQLite relational database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    import re
    clean_name = re.sub(r'[^a-z0-9]', '_', title.lower())[:12].strip('_') or "project"
    proj_id = f"proj_{clean_name}_{os.urandom(3).hex()}"
    from services.art_engine import generate_vintage_scene_illustration
    default_poster = poster_url if (poster_url and not "unsplash.com" in poster_url) else generate_vintage_scene_illustration(f"CARTEL: {title.upper()}", "PRODUCCION", "EXT", "NIGHT")
    cursor.execute("""
    INSERT INTO projects (
        id, title, tagline, genre, format, runtime_minutes, tone, target_audience,
        status, progress_percentage, target_budget, estimated_budget, shooting_days,
        crew_count, available_locations, synopsis, logline, visual_aesthetic,
        eco_impact_score, age_rating, poster_url, is_demo
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        proj_id, title,
        logline or f"Una producción de {genre.lower()} en formato {format_type.lower()}.",
        genre, format_type, 90 if format_type == "FILM" else 110,
        "Dramático y Cinematográfico", "Audiencia General", "EN DESARROLLO", 0, budget, 0.0,
        0, 0, 0,
        logline or f"Una nueva producción de {genre}.",
        logline or f"Esperando premisa del director en el Visionary Agent.",
        "Estética cinematográfica personalizada",
        90, "PG-13", default_poster, 0
    ))

    cursor.execute("""
    INSERT INTO project_history (project_id, timestamp, event, agent, details, entity_type, entity_id)
    VALUES (?, 'Justo Ahora', 'Proyecto Creado', 'Director', ?, 'PROJECT', ?)
    """, (proj_id, f"Se creó el proyecto limpio '{title}' ({format_type}).", proj_id))

    conn.commit()
    conn.close()
    return proj_id

def update_project_db(project_id: str, conn: Optional[Any] = None, **kwargs) -> bool:
    """Updates scalar fields of a project in SQLite."""
    if not kwargs:
        return False
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    
    allowed_keys = {
        "title", "tagline", "genre", "format", "runtime_minutes", "tone", "target_audience",
        "status", "progress_percentage", "target_budget", "estimated_budget", "shooting_days",
        "crew_count", "available_locations", "synopsis", "logline", "visual_aesthetic",
        "eco_impact_score", "age_rating", "poster_url", "is_demo"
    }
    updates = {k: v for k, v in kwargs.items() if k in allowed_keys}
    if not updates:
        if close_conn:
            conn.close()
        return False

    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [project_id]

    cursor = conn.cursor()
    cursor.execute(f"UPDATE projects SET {set_clause} WHERE id = ?", tuple(values))
    conn.commit()
    if close_conn:
        conn.close()
    return True

def get_characters_by_project_db(project_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM characters WHERE project_id = ?", (project_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_relationships_by_project_db(project_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        cr.*, 
        c.name as source_name,
        COALESCE(c2.name, cr.target_character_name) as target_character_name
    FROM character_relationships cr
    LEFT JOIN characters c ON cr.source_character_id = c.id
    LEFT JOIN characters c2 ON cr.target_character_id = c2.id
    WHERE cr.project_id = ?
    """, (project_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_scenes_by_project_db(project_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scenes WHERE project_id = ? ORDER BY scene_number ASC", (project_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_budget_options_by_project_db(project_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM budget_options WHERE project_id = ?", (project_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_history_by_project_db(project_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM project_history WHERE project_id = ? ORDER BY id DESC", (project_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def record_narrative_change_db(
    project_id: str,
    prompt: str,
    entity_type: str,
    entity_name: str,
    severity: str,
    impact_explanation: str,
    before_state: Dict[str, Any],
    after_state: Dict[str, Any],
    affected_scenes: List[int],
    status: str = "APPLIED"
) -> str:
    """Records a structured narrative change in the project narrative memory."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM narrative_changes WHERE project_id = ?", (project_id,))
    count = cursor.fetchone()[0] + 1
    
    change_id = f"nchange_{project_id}_{count}_{os.urandom(2).hex()}"
    cursor.execute("""
    INSERT INTO narrative_changes (
        id, project_id, change_number, prompt, entity_type, entity_name,
        severity, impact_explanation, before_state, after_state,
        affected_scenes_json, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        change_id, project_id, count, prompt, entity_type, entity_name,
        severity, impact_explanation, json.dumps(before_state, ensure_ascii=False),
        json.dumps(after_state, ensure_ascii=False), json.dumps(affected_scenes),
        status
    ))
    conn.commit()
    conn.close()
    return change_id

def get_narrative_history_db(project_id: str) -> List[Dict[str, Any]]:
    """Fetches all chronological narrative changes for a project."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM narrative_changes WHERE project_id = ? ORDER BY change_number DESC", (project_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# =============================================================================
# PRODUCTION INTELLIGENCE & CANON CRUD HELPERS (FASE 5)
# =============================================================================

def add_canonical_fact_db(
    project_id: str,
    fact_text: str,
    entity_type: str = "GENERAL",
    entity_id: str = "",
    fact_type: str = "CANONICAL",
    scene_established: Optional[int] = None
) -> str:
    """Stores a canonical or inferred fact in the project canon knowledgebase."""
    conn = get_connection()
    cursor = conn.cursor()
    fact_id = f"fact_{project_id}_{os.urandom(3).hex()}"
    cursor.execute("""
    INSERT INTO project_facts (id, project_id, entity_type, entity_id, fact_text, fact_type, status, scene_established)
    VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE', ?)
    """, (fact_id, project_id, entity_type, entity_id, fact_text, fact_type, scene_established))
    conn.commit()
    conn.close()
    return fact_id

def get_canonical_facts_db(project_id: str) -> List[Dict[str, Any]]:
    """Retrieves all active canonical and inferred facts for a project."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM project_facts WHERE project_id = ? ORDER BY created_at ASC", (project_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_scene_version_db(
    scene_id: str,
    project_id: str,
    scene_snapshot: Dict[str, Any],
    reason: str = "Modificación de guion",
    conn: Optional[Any] = None
) -> str:
    """Snapshots a scene state before modification to enable instant rollback."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM scene_versions WHERE scene_id = ?", (scene_id,))
    version_num = cursor.fetchone()[0] + 1
    ver_id = f"ver_{scene_id}_{version_num}_{os.urandom(2).hex()}"
    cursor.execute("""
    INSERT INTO scene_versions (id, scene_id, project_id, version_number, scene_snapshot_json, reason)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (ver_id, scene_id, project_id, version_num, json.dumps(scene_snapshot, ensure_ascii=False), reason))
    conn.commit()
    if close_conn:
        conn.close()
    return ver_id


def get_scene_versions_db(scene_id: str) -> List[Dict[str, Any]]:
    """Fetches all past versions for a scene ordered from newest to oldest."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scene_versions WHERE scene_id = ? ORDER BY version_number DESC", (scene_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_director_preference_db(
    project_id: str,
    preference_type: str,
    directive_text: str
) -> str:
    """Stores a director creative directive or tonal preference."""
    conn = get_connection()
    cursor = conn.cursor()
    pref_id = f"pref_{project_id}_{os.urandom(3).hex()}"
    cursor.execute("""
    INSERT INTO director_preferences (id, project_id, preference_type, directive_text)
    VALUES (?, ?, ?, ?)
    """, (pref_id, project_id, preference_type, directive_text))
    conn.commit()
    conn.close()
    return pref_id

def get_director_preferences_db(project_id: str) -> List[Dict[str, Any]]:
    """Retrieves all stored director creative directives."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM director_preferences WHERE project_id = ? ORDER BY created_at ASC", (project_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_project_research_db(
    project_id: str,
    objective: str,
    search_queries: List[str],
    research_summary: str,
    sources: List[Dict[str, Any]],
    target_scope: str = "GENERAL",
    conn: Optional[Any] = None
) -> str:
    """Stores external web research results (Parallel Search API) associated strictly with a project."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()
    res_id = f"res_{project_id}_{os.urandom(3).hex()}"
    cursor.execute("""
    INSERT INTO project_research (
        id, project_id, objective, search_queries_json, research_summary, sources_json, target_scope
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        res_id,
        project_id,
        objective,
        json.dumps(search_queries, ensure_ascii=False),
        research_summary,
        json.dumps(sources, ensure_ascii=False),
        target_scope
    ))
    conn.commit()
    if close_conn:
        conn.close()
    return res_id

def get_project_research_db(project_id: str, limit: int = 5, conn: Optional[Any] = None) -> List[Dict[str, Any]]:
    """Retrieves stored external research for a specific project, isolated from other projects."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, project_id, objective, search_queries_json, research_summary, sources_json, target_scope, created_at
    FROM project_research
    WHERE project_id = ?
    ORDER BY created_at DESC
    LIMIT ?
    """, (project_id, limit))
    rows = cursor.fetchall()

    results = []
    for r in rows:
        item = dict(r)
        try:
            item["search_queries"] = json.loads(item.get("search_queries_json") or "[]")
        except Exception:
            item["search_queries"] = []
        try:
            item["sources"] = json.loads(item.get("sources_json") or "[]")
        except Exception:
            item["sources"] = []
        results.append(item)

    if close_conn:
        conn.close()
    return results

def save_project_message_db(project_id: str, role: str, text: str, conn: Optional[Any] = None) -> int:
    """Stores a conversational message in SQLite to persist chat history across reloads."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO project_messages (project_id, role, text)
    VALUES (?, ?, ?)
    """, (project_id, role, text))
    msg_id = cursor.lastrowid

    if close_conn:
        conn.commit()
        conn.close()
    return msg_id

def get_project_messages_db(project_id: str, limit: int = 50, conn: Optional[Any] = None) -> List[Dict[str, Any]]:
    """Retrieves chronological chat history for a specific project from SQLite."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()
    cursor.execute("""
    SELECT role, text, created_at
    FROM project_messages
    WHERE project_id = ?
    ORDER BY id ASC
    LIMIT ?
    """, (project_id, limit))
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]

    if close_conn:
        conn.close()
    return results

def save_project_localization_db(project_id: str, lang: str, section: str, data_json: str, conn: Optional[Any] = None) -> None:
    """Saves a non-destructive localized projection for a project and section into SQLite."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()
    loc_id = f"loc_{project_id}_{lang}_{section}"
    cursor.execute("""
    INSERT OR REPLACE INTO project_localizations (id, project_id, lang, section, data_json, updated_at)
    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (loc_id, project_id, lang, section, data_json))

    if close_conn:
        conn.commit()
        conn.close()

def get_project_localization_db(project_id: str, lang: str, section: str, conn: Optional[Any] = None) -> Optional[Dict[str, Any]]:
    """Retrieves a cached localized projection for a project and section from SQLite."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()
    cursor.execute("""
    SELECT data_json FROM project_localizations
    WHERE project_id = ? AND lang = ? AND section = ?
    """, (project_id, lang, section))
    row = cursor.fetchone()

    if close_conn:
        conn.close()

    if row and row["data_json"]:
        try:
            return json.loads(row["data_json"])
        except Exception:
            return None
    return None

def clear_project_localizations_db(project_id: str, conn: Optional[Any] = None) -> None:
    """Clears all cached localized projections for a project from SQLite."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()
    cursor.execute("DELETE FROM project_localizations WHERE project_id = ?", (project_id,))

    if close_conn:
        conn.commit()
        conn.close()

def save_visual_asset_db(
    project_id: str,
    entity_type: str,
    entity_id: str,
    asset_type: str,
    model: str,
    prompt: str,
    prompt_hash: str,
    file_path: str,
    generation_status: str = "completed",
    mime_type: str = "image/png",
    width: int = 320,
    height: int = 320,
    conn: Optional[Any] = None
) -> str:
    """Persists a generated visual asset record in SQLite."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()
    import hashlib
    clean_hash = prompt_hash or hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]
    asset_id = f"va_{project_id}_{entity_type}_{clean_hash}"

    cursor.execute("""
    INSERT OR REPLACE INTO visual_assets (
        id, project_id, entity_type, entity_id, asset_type, model,
        prompt, prompt_hash, file_path, mime_type, width, height,
        generation_status, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        asset_id, project_id, entity_type, entity_id, asset_type, model,
        prompt, clean_hash, file_path, mime_type, width, height,
        generation_status
    ))

    if close_conn:
        conn.commit()
        conn.close()
    return asset_id

def get_visual_assets_by_project_db(project_id: str, conn: Optional[Any] = None) -> List[Dict[str, Any]]:
    """Retrieves all visual assets for a given project."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM visual_assets WHERE project_id = ? ORDER BY created_at DESC", (project_id,))
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]

    if close_conn:
        conn.close()
    return results

def get_visual_asset_by_entity_db(project_id: str, entity_type: str, entity_id: str, conn: Optional[Any] = None) -> Optional[Dict[str, Any]]:
    """Retrieves the visual asset for a specific entity (character, scene, or poster)."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM visual_assets
    WHERE project_id = ? AND entity_type = ? AND entity_id = ?
    ORDER BY updated_at DESC LIMIT 1
    """, (project_id, entity_type, entity_id))
    row = cursor.fetchone()

    if close_conn:
        conn.close()
    return dict(row) if row else None

