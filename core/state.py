import streamlit as st
import json
from typing import Dict, List, Optional, Any
from core.models import Project, Character, CharacterDNA, Relationship, Scene, BudgetDriver, BudgetOptimizationOption, ContinuityAlert, HealthScores
from core.db import (
    init_db, get_all_projects_db, get_project_db, get_characters_by_project_db,
    get_scenes_by_project_db, get_relationships_by_project_db, get_budget_options_by_project_db,
    get_history_by_project_db, create_character_db, delete_character_db, create_project_db
)

def init_session_state():
    """Ensures SQLite relational DB is initialized and loads state."""
    init_db()

    if "language" not in st.session_state:
        st.session_state.language = "ES"

    projects_list = get_all_projects_db()
    if "active_project_id" not in st.session_state or not st.session_state.active_project_id:
        st.session_state.active_project_id = projects_list[0]["id"] if projects_list else "proj_last_signal"
        
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "VISION"

    if "assistant_messages" not in st.session_state:
        st.session_state.assistant_messages = [
            {
                "role": "assistant",
                "content": "¡Hola Director! Soy su Co-Director Digital IA. ¿En qué aspecto de la producción desea trabajar hoy?"
            }
        ]

def get_current_project() -> Project:
    init_session_state()
    pid = st.session_state.get("active_project_id", "proj_last_signal")
    p_data = get_project_db(pid)
    
    if not p_data:
        projects_list = get_all_projects_db()
        p_data = projects_list[0] if projects_list else None

    # Construct Character instances from DB
    db_chars = get_characters_by_project_db(pid)
    characters = []
    for c in db_chars:
        dna_dict = json.loads(c['dna_json']) if c['dna_json'] else {}
        props_list = json.loads(c['props_json']) if c['props_json'] else []
        arc_dict = json.loads(c['arc_json']) if c['arc_json'] else {}
        
        characters.append(Character(
            id=c['id'],
            name=c['name'],
            age=c['age'],
            role=c['role'],
            archetype=c['archetype'],
            occupation=c['occupation'],
            personality=c['personality'],
            motivation=c['motivation'],
            fears=c['fears'],
            strengths=c['strengths'],
            weaknesses=c['weaknesses'],
            arc=arc_dict,
            emotional_state=c['emotional_state'],
            wardrobe=c['wardrobe'],
            props=props_list,
            dna=CharacterDNA(
                courage=dna_dict.get('courage', 80),
                intelligence=dna_dict.get('intelligence', 85),
                empathy=dna_dict.get('empathy', 75),
                trust=dna_dict.get('trust', 65),
                ambition=dna_dict.get('ambition', 80),
                aggression=dna_dict.get('aggression', 35),
                creativity=dna_dict.get('creativity', 85),
                resilience=dna_dict.get('resilience', 80)
            ),
            avatar_url=c['avatar_url']
        ))

    # Construct Scene instances from DB
    db_scenes = get_scenes_by_project_db(pid)
    scenes = []
    for s in db_scenes:
        scenes.append(Scene(
            scene_number=s['scene_number'],
            title=s['title'],
            slugline=s['slugline'],
            location=s['location'],
            interior_exterior=s['interior_exterior'],
            day_night=s['day_night'],
            summary=s['summary'],
            script_text=s['script_text'],
            characters=json.loads(s['characters_json']) if s['characters_json'] else [],
            props=json.loads(s['props_json']) if s['props_json'] else [],
            wardrobe=json.loads(s['wardrobe_json']) if s['wardrobe_json'] else [],
            vfx=json.loads(s['vfx_json']) if s['vfx_json'] else [],
            sfx=json.loads(s['sfx_json']) if s['sfx_json'] else [],
            complexity=s['complexity'],
            risk_score=s['risk_score'],
            estimated_cost=s['estimated_cost']
        ))

    # Construct Budget Options from DB
    db_opts = get_budget_options_by_project_db(pid)
    budget_options = []
    for opt in db_opts:
        budget_options.append(BudgetOptimizationOption(
            id=opt['id'],
            title=opt['title'],
            description=opt['description'],
            estimated_savings=opt['estimated_savings'],
            impact_level=opt['impact_level'],
            affected_scenes=json.loads(opt['affected_scenes_json']) if opt['affected_scenes_json'] else [],
            status=opt['status']
        ))

    # History from DB
    history_logs = get_history_by_project_db(pid)

    return Project(
        id=p_data['id'],
        title=p_data['title'],
        tagline=p_data['tagline'],
        genre=p_data['genre'],
        format=p_data['format'],
        runtime_minutes=p_data['runtime_minutes'],
        tone=p_data['tone'],
        target_audience=p_data['target_audience'],
        status=p_data['status'],
        progress_percentage=p_data['progress_percentage'],
        target_budget=p_data['target_budget'],
        estimated_budget=p_data['estimated_budget'],
        shooting_days=p_data['shooting_days'],
        crew_count=p_data['crew_count'],
        available_locations=p_data['available_locations'],
        synopsis=p_data['synopsis'],
        logline=p_data['logline'],
        visual_aesthetic=p_data['visual_aesthetic'],
        characters=characters,
        scenes=scenes,
        budget_drivers=[
            BudgetDriver("Efectos Visuales (VFX)", 8000.0, "Secuencias complejas de partículas"),
            BudgetDriver("Locaciones Exteriores", 5200.0, "Montaje de pasarelas espaciales"),
            BudgetDriver("Horas Extra de Rodaje Nocturno", 3100.0, "Bloques en observatorio")
        ],
        budget_options=budget_options,
        continuity_alerts=[],
        health_scores=HealthScores(creative_score=92, production_score=78, budget_score=72, continuity_score=88, risk_score=42),
        eco_impact_score=p_data['eco_impact_score'],
        age_rating=p_data['age_rating'],
        content_advisories=["Acción Moderada", "Atmósfera Tensa"],
        history_logs=history_logs
    )

def add_new_character_to_project(project: Project, name: str, age: int, role: str, archetype: str, occupation: str, personality: str, motivation: str, fears: str, strengths: str, weaknesses: str, wardrobe: str, props_str: str) -> str:
    char_data = {
        "name": name, "age": age, "role": role, "archetype": archetype,
        "occupation": occupation, "personality": personality, "motivation": motivation,
        "fears": fears, "strengths": strengths, "weaknesses": weaknesses,
        "wardrobe": wardrobe, "props": [p.strip() for p in props_str.split(",") if p.strip()]
    }
    return create_character_db(project.id, char_data)

def delete_character(project_id: str, char_id: str, char_name: str) -> bool:
    return delete_character_db(project_id, char_id, char_name)

def add_new_project(title: str, genre: str, format_type: str, budget: float, logline: str = "") -> str:
    new_pid = create_project_db(title, genre, format_type, budget, logline)
    st.session_state.active_project_id = new_pid
    return new_pid

def get_all_projects() -> List[Dict[str, Any]]:
    return get_all_projects_db()
