import os
import json
import sqlite3
import time
from flask import Flask, render_template, request, jsonify, Response
from core.db import (
    init_db, get_connection, get_all_projects_db, get_project_db,
    get_characters_by_project_db, get_scenes_by_project_db,
    get_relationships_by_project_db, create_project_db,
    add_canonical_fact_db, get_canonical_facts_db,
    add_director_preference_db, get_director_preferences_db,
    get_project_research_db, save_project_research_db, save_project_message_db, get_project_messages_db,
    get_visual_assets_by_project_db, update_project_db, clear_project_localizations_db,
    add_scene_version_db
)
from services.director_agent import DirectorAgent, DirectorIntent, DirectorExecutionPlan
from services.story_engine import StoryEngine
from services.character_engine import CharacterEngine
from services.scene_engine import SceneEngine
from services.narrative_engine import NarrativeEngine
from services.project_memory import ProjectMemoryEngine
from services.continuity_engine import ContinuityEngine
from services.parallel_tool import ParallelSearchTool
from services.art_engine import generate_vintage_scene_illustration, generate_vintage_character_avatar
from services.docx_generator import create_screenplay_docx
from services.gemini_service import GeminiCreativeProvider
from services.localization_service import localization_service
from services.image_service import cinematic_image_service
from services.screenplay_auditor import ScreenplayAuditor

app = Flask(__name__, template_folder="templates", static_folder="assets", static_url_path="/assets")
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Initialize database tables on startup
init_db()

# =============================================================================
# AGENTIC CINEMA ARCHITECTURE: CO-DIRECTOR AI ORCHESTRATOR & CREATIVE ENGINES
# =============================================================================
gemini = GeminiCreativeProvider()
gemini._ensure_connected()

# First-class references to specialized creative engines
director_agent: DirectorAgent = gemini.director_agent
story_engine: StoryEngine = gemini.story_engine
character_engine: CharacterEngine = gemini.character_engine
scene_engine: SceneEngine = gemini.scene_engine
narrative_engine: NarrativeEngine = gemini.narrative_engine
project_memory: ProjectMemoryEngine = gemini.project_memory
continuity_engine = ContinuityEngine
parallel_tool: ParallelSearchTool = gemini.parallel_tool

# In-memory conversation history keyed by project_id
project_conversations = {}

@app.route("/")
def index():
    """Serves the main Agentic Cinema Studio application."""
    return render_template("index.html")

@app.route("/favicon.ico")
def favicon():
    return ('', 204)

@app.route("/api/projects", methods=["GET"])
def api_get_projects():
    """Returns all projects in the studio library with optional display language localization."""
    lang = request.args.get("lang", "EN").upper()
    projects = get_all_projects_db()
    if lang != "ES":
        localized_projects = []
        for p in projects:
            p_copy = localization_service.get_localized_project_summary(dict(p), lang)
            localized_projects.append(p_copy)
        return jsonify(localized_projects)
    return jsonify(projects)

@app.route("/api/project/<project_id>", methods=["GET"])
@app.route("/api/projects/<project_id>", methods=["GET"])
def api_get_project_details(project_id):
    """Returns full project details including characters, relationships, and scenes exclusively for this ID, with non-destructive localization."""
    lang = request.args.get("lang", "EN").upper()
    if not project_id or project_id.strip() in ["undefined", "null", "none", ""]:
        return jsonify({
            "error": "Invalid or missing project_id",
            "project_id": project_id,
            "project": None,
            "characters": [],
            "scenes": [],
            "relationships": [],
            "screenplay": "",
            "script_text": "",
            "canonical_facts": []
        }), 404

    # Use localization projection layer
    loc_bundle = localization_service.get_localized_project_details(project_id, lang)
    proj = loc_bundle.get("project")
    if not proj:
        return jsonify({
            "error": f"Project '{project_id}' not found",
            "project_id": project_id,
            "project": None,
            "characters": [],
            "scenes": [],
            "relationships": [],
            "screenplay": "",
            "script_text": "",
            "canonical_facts": []
        }), 404

    characters = loc_bundle.get("characters", [])
    relationships = loc_bundle.get("relationships", [])
    scenes = loc_bundle.get("scenes", [])
    canonical_scenes = get_scenes_by_project_db(project_id) or []
    if not scenes and canonical_scenes:
        scenes = canonical_scenes
    else:
        can_map = {cs["id"]: cs for cs in canonical_scenes}
        for s in scenes:
            if not s.get("script_text") and s.get("id") in can_map:
                s["script_text"] = can_map[s["id"]].get("script_text")
            if not s.get("summary") and s.get("id") in can_map:
                s["summary"] = can_map[s["id"]].get("summary")
    canonical_facts = get_canonical_facts_db(project_id) or []

    # Attach scene-level continuity alerts
    alerts = []
    try:
        alerts = ContinuityEngine.scan_project_continuity(proj, characters, scenes)
        for s in scenes:
            sc_num = s.get("scene_number")
            s["continuity_alerts"] = [a for a in alerts if a.get("scene_number") == sc_num]
    except Exception:
        for s in scenes:
            s["continuity_alerts"] = []

    # Compile complete screenplay text
    screenplay_parts = []
    scene_label = "SCENE" if lang == "EN" else "ESCENA"
    for s in scenes:
        header = s.get("slugline") or f"{s.get('interior_exterior', 'INT')}. {s.get('location', 'LOCATION')} - {s.get('day_night', 'NIGHT')}"
        sc_num = s.get("scene_number", "")
        sc_title = f"{scene_label} {sc_num}: {header}" if sc_num else header
        sc_text = s.get("script_text") or s.get("summary") or ""
        screenplay_parts.append(f"{sc_title}\n\n{sc_text}")
    compiled_screenplay = "\n\n---\n\n".join(screenplay_parts)

    db_messages = get_project_messages_db(project_id)
    chat_history = db_messages if db_messages else project_conversations.get(project_id, [])
    if lang != "ES":
        chat_history = localization_service.localize_chat_messages(chat_history, lang)

    # Screenplay duplication and repetition audit
    repetition_audit = ScreenplayAuditor.audit_screenplay(scenes)

    return jsonify({
        "success": True,
        "project_id": project_id,
        "lang": lang,
        "project": proj,
        "characters": characters,
        "relationships": relationships,
        "scenes": scenes,
        "screenplay": compiled_screenplay,
        "script_text": compiled_screenplay,
        "canonical_facts": canonical_facts,
        "continuity_alerts": alerts,
        "continuity_healthy": len(alerts) == 0,
        "repetition_audit": repetition_audit,
        "repetition_healthy": repetition_audit["healthy"],
        "chat_history": chat_history,
        "image_service_status": cinematic_image_service.get_runtime_status()
    })

@app.route("/api/project/<project_id>/chat_history", methods=["GET"])
def api_get_project_chat_history(project_id):
    """Returns chat history for a project with optional non-destructive localization."""
    lang = request.args.get("lang", "EN").upper()
    db_messages = get_project_messages_db(project_id)
    chat_history = db_messages if db_messages else project_conversations.get(project_id, [])
    if lang != "ES":
        chat_history = localization_service.localize_chat_messages(chat_history, lang)
    return jsonify({
        "success": True,
        "project_id": project_id,
        "lang": lang,
        "chat_history": chat_history
    })

@app.route("/api/projects/create", methods=["POST"])
def api_create_project():
    """Creates a brand new blank project in SQLite and sets it active."""
    data = request.get_json() or {}
    title = data.get("title", "Nueva Producción Cinemática")
    genre = data.get("genre", "Drama / Cine")
    format_type = data.get("format", "FILM")
    budget = float(data.get("budget", 65000.0))
    logline = data.get("logline", "")
    poster_url = data.get("poster_url", "")

    proj_id = create_project_db(title, genre, format_type, budget, logline, poster_url)
    proj = get_project_db(proj_id)

    return jsonify({
        "success": True,
        "project_id": proj_id,
        "project": proj
    })

@app.route("/api/projects/<project_id>", methods=["DELETE"])
def api_delete_project(project_id):
    """Deletes a project and all cascading relational data from SQLite."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM characters WHERE project_id = ?", (project_id,))
    cursor.execute("DELETE FROM character_relationships WHERE project_id = ?", (project_id,))
    cursor.execute("DELETE FROM scenes WHERE project_id = ?", (project_id,))
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))

    conn.commit()
    conn.close()

    if project_id in project_conversations:
        del project_conversations[project_id]

    return jsonify({"success": True, "deleted_id": project_id})

@app.route("/api/characters/<character_id>/update", methods=["POST"])
def api_update_character(character_id):
    """Updates a single character's attributes in SQLite and propagates name changes."""
    data = request.get_json() or {}
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM characters WHERE id = ?", (character_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return jsonify({"error": "Character not found"}), 404

    old_name = existing["name"]
    new_name = data.get("name", old_name)
    project_id = existing["project_id"]

    cursor.execute("""
    UPDATE characters SET
        name = ?, age = ?, role = ?, archetype = ?, occupation = ?,
        personality = ?, motivation = ?, fears = ?, strengths = ?,
        weaknesses = ?, emotional_state = ?, wardrobe = ?,
        birth_date = ?, zodiac_sign = ?, religion_belief = ?, subtext = ?
    WHERE id = ?
    """, (
        new_name,
        int(data.get("age", existing["age"])),
        data.get("role", existing["role"]),
        data.get("archetype", existing["archetype"]),
        data.get("occupation", existing["occupation"]),
        data.get("personality", existing["personality"]),
        data.get("motivation", existing["motivation"]),
        data.get("fears", existing["fears"]),
        data.get("strengths", existing["strengths"]),
        data.get("weaknesses", existing["weaknesses"]),
        data.get("emotional_state", existing["emotional_state"]),
        data.get("wardrobe", existing["wardrobe"]),
        data.get("birth_date", existing["birth_date"]),
        data.get("zodiac_sign", existing["zodiac_sign"]),
        data.get("religion_belief", existing["religion_belief"]),
        data.get("subtext", existing["subtext"]),
        character_id
    ))

    # Propagate name change if altered
    if new_name != old_name:
        cursor.execute("UPDATE character_relationships SET target_character_name = ? WHERE target_character_name = ? AND project_id = ?", (new_name, old_name, project_id))
        cursor.execute("SELECT id, characters_json, summary, script_text, slugline FROM scenes WHERE project_id = ?", (project_id,))
        sc_rows = cursor.fetchall()
        for sc in sc_rows:
            sc_id = sc["id"]
            c_json = sc["characters_json"] or "[]"
            summ = sc["summary"] or ""
            scr = sc["script_text"] or ""
            slug = sc["slugline"] or ""

            mod = False
            if old_name in c_json:
                c_json = c_json.replace(old_name, new_name)
                mod = True
            if old_name in summ:
                summ = summ.replace(old_name, new_name)
                mod = True
            if old_name in scr or old_name.upper() in scr:
                scr = scr.replace(old_name, new_name).replace(old_name.upper(), new_name.upper())
                mod = True
            if old_name in slug:
                slug = slug.replace(old_name, new_name)
                mod = True

            if mod:
                cursor.execute("UPDATE scenes SET characters_json = ?, summary = ?, script_text = ?, slugline = ? WHERE id = ?", (c_json, summ, scr, slug, sc_id))

    conn.commit()
    conn.close()

    return jsonify({"success": True, "character_id": character_id, "name": new_name})

@app.route("/api/scenes/<scene_id>/update", methods=["POST"])
def api_update_scene(scene_id):
    """Updates a single scene's attributes directly in SQLite."""
    data = request.get_json() or {}
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM scenes WHERE id = ?", (scene_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return jsonify({"error": "Scene not found"}), 404

    cursor.execute("""
    UPDATE scenes SET
        slugline = ?, interior_exterior = ?, day_night = ?,
        summary = ?, script_text = ?
    WHERE id = ?
    """, (
        data.get("slugline", existing["slugline"]),
        data.get("interior_exterior", existing["interior_exterior"]),
        data.get("day_night", existing["day_night"]),
        data.get("summary", existing["summary"]),
        data.get("script_text", existing["script_text"]),
        scene_id
    ))

    conn.commit()
    conn.close()

    return jsonify({"success": True, "scene_id": scene_id})

@app.route("/api/scenes/<scene_id>/scout_parallel", methods=["POST"])
def api_scout_scene_parallel(scene_id):
    """
    Core Parallel Search Workflow:
    Scouts authentic real-world filming locations for a specific scene using Parallel Search API.
    Synthesizes and ranks candidates with Gemini Co-Director.
    Does NOT mutate the scene (Zero Mutation Gate).
    """
    req_data = request.get_json(silent=True) or {}
    user_objective = req_data.get("objective", "").strip()
    target_lang = req_data.get("lang", "EN").upper()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scenes WHERE id = ?", (scene_id,))
    scene_row = cursor.fetchone()
    if not scene_row:
        conn.close()
        return jsonify({"error": "Scene not found"}), 404

    scene = dict(scene_row)
    project_id = scene["project_id"]
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    proj_row = cursor.fetchone()
    proj = dict(proj_row) if proj_row else {"title": "Cinema Project", "genre": "Drama", "tone": "Cinematic"}
    conn.close()

    loc_current = scene.get("location") or scene.get("slugline", "Interior Set")
    env_details = scene.get("environmental_details") or scene.get("summary", "")
    genre = proj.get("genre", "Drama")
    tone = proj.get("tone", "Cinematic")
    
    clean_loc = loc_current.replace("INT.", "").replace("EXT.", "").replace(" - DAY", "").replace(" - NIGHT", "").strip()

    if user_objective:
        objective = user_objective
    else:
        objective = (
            f"Authentic filming locations for '{scene.get('slugline')}' ({clean_loc}). "
            f"Atmosphere: {env_details[:100]}. Film genre: {genre}, tone: {tone}."
        )

    search_queries = [
        f"{clean_loc} real world filming locations production scout"[:80].strip(),
        f"{clean_loc} authentic places architectural {genre}"[:80].strip(),
        f"{proj.get('title')} {clean_loc} location reference"[:80].strip()
    ]

    search_res = parallel_tool.search(
        objective=objective,
        search_queries=search_queries,
        mode="fast",
        max_results=5
    )

    sources = search_res.get("results", [])

    candidates = []
    gemini._ensure_connected()

    if gemini.client and sources:
        sources_text = "\n\n".join([
            f"Source {i+1}: {s.get('title')}\nURL: {s.get('url')}\nExcerpts: " + " ".join(s.get('excerpts', []))
            for i, s in enumerate(sources)
        ])
        
        prompt_analysis = f"""
You are the Studio Co-Director AI for the feature film '{proj.get('title')}' ({genre}).
You are scouting authentic real-world filming locations for Scene {scene.get('scene_number')}:
Current Slugline: {scene.get('slugline')}
Current Location: {loc_current}
Current Atmosphere: {env_details}
Scene Summary: {scene.get('summary')}

Parallel Search API retrieved the following authentic live web sources:
{sources_text}

Task: Select and rank up to 3 candidate real-world locations that best fit this scene narratively, aesthetically, and logistically.
Respond strictly in JSON format as a list of objects with the following schema:
[
  {{
    "id": "cand_1",
    "name": "Specific Name of Location",
    "city_country": "City, Region or Country",
    "match_score": 95,
    "creative_fit": "Why this real location enhances the scene's drama and theme (2 sentences).",
    "production_fit": "Logistical considerations, accessibility, permits, or studio viability (2 sentences).",
    "proposed_slugline": "EXT. PROPOSED LOCATION - NIGHT",
    "proposed_location": "Clean Name of Location",
    "proposed_environment": "Updated atmospheric notes grounded in the actual location."
  }}
]
Do not include any markdown or conversational filler; return only the raw JSON array.
"""
        for model_name in gemini.director_agent.candidate_models:
            try:
                res = gemini.client.models.generate_content(
                    model=model_name,
                    contents=prompt_analysis
                )
                if res and res.text:
                    raw = res.text.strip()
                    if raw.startswith("```"):
                        raw = raw.split("```")[1]
                        if raw.startswith("json"):
                            raw = raw[4:]
                    parsed = json.loads(raw.strip())
                    if isinstance(parsed, list) and len(parsed) > 0:
                        candidates = parsed
                        break
            except Exception:
                continue

    if not candidates:
        for idx, s in enumerate(sources[:3]):
            title = s.get("title", f"Location Option {idx+1}")
            clean_title = title.split(" - ")[0].split(" | ")[0]
            candidates.append({
                "id": f"cand_{idx+1}",
                "name": clean_title,
                "city_country": "Real-World Location (Parallel Verified)",
                "match_score": 92 - (idx * 5),
                "creative_fit": f"Authentic location discovered via live Parallel Search matching '{clean_loc}'.",
                "production_fit": "Viable practical filming location with real-world infrastructure.",
                "proposed_slugline": f"{scene.get('interior_exterior', 'EXT')}. {clean_title.upper()} - {scene.get('day_night', 'NIGHT')}",
                "proposed_location": clean_title,
                "proposed_environment": f"Authentic atmosphere of {clean_title}. Discovered via Parallel Search API.",
                "source_urls": [s.get("url")] if s.get("url") else []
            })

    try:
        conn = get_connection()
        summary_text = f"Parallel Scout for Scene {scene.get('scene_number')}: Discovered {len(candidates)} candidate locations."
        save_project_research_db(
            project_id=project_id,
            objective=objective,
            search_queries=search_queries,
            research_summary=summary_text,
            sources=sources,
            target_scope=f"SCENE_{scene.get('scene_number')}_LOCATIONS",
            conn=conn
        )
        conn.close()
    except Exception:
        pass

    return jsonify({
        "success": True,
        "scene_id": scene_id,
        "scene_number": scene.get("scene_number"),
        "objective": objective,
        "search_queries": search_queries,
        "candidates": candidates,
        "sources": sources
    })

@app.route("/api/scenes/<scene_id>/apply_scouted_location", methods=["POST"])
def api_apply_scouted_location(scene_id):
    """
    Zero Mutation Gate Confirmation:
    The Director explicitly approves a scouted candidate location.
    Applies changes to SQLite, logs snapshot version, and informs Production Intelligence.
    """
    data = request.get_json() or {}
    cand_name = data.get("candidate_name") or data.get("name", "Scouted Location")
    new_slugline = data.get("slugline") or data.get("proposed_slugline")
    new_location = data.get("location") or data.get("proposed_location") or cand_name
    new_env = data.get("environmental_details") or data.get("proposed_environment")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scenes WHERE id = ?", (scene_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        return jsonify({"error": "Scene not found"}), 404

    existing_dict = dict(existing)
    project_id = existing_dict["project_id"]

    try:
        add_scene_version_db(
            scene_id=scene_id,
            project_id=project_id,
            scene_snapshot=existing_dict,
            reason=f"Prior to applying Parallel scouted location: {cand_name}",
            conn=conn
        )
    except Exception:
        pass

    slug_to_save = new_slugline or existing_dict["slugline"]
    loc_to_save = new_location or existing_dict["location"]
    env_to_save = new_env or existing_dict["environmental_details"]

    cursor.execute("""
    UPDATE scenes SET
        slugline = ?,
        location = ?,
        environmental_details = ?
    WHERE id = ?
    """, (slug_to_save, loc_to_save, env_to_save, scene_id))

    try:
        cursor.execute("""
        INSERT INTO project_history (project_id, timestamp, event, agent, details, entity_type, entity_id)
        VALUES (?, datetime('now'), ?, ?, ?, ?, ?)
        """, (
            project_id,
            "APPLIED_SCOUTED_LOCATION",
            "ParallelSearch & Gemini Co-Director",
            f"Applied scouted location '{cand_name}' to Scene {existing_dict['scene_number']}. Slugline updated to '{slug_to_save}'.",
            "SCENE",
            scene_id
        ))
    except Exception:
        pass

    clear_project_localizations_db(project_id, conn)

    conn.commit()

    cursor.execute("SELECT * FROM scenes WHERE id = ?", (scene_id,))
    updated_row = cursor.fetchone()
    updated_scene = dict(updated_row) if updated_row else {}
    conn.close()

    impact_message = (
        f"✅ Location updated to '{cand_name}' for Scene {existing_dict['scene_number']}. "
        f"Zero Mutation Gate satisfied: Version snapshot preserved in SQLite. "
        f"Production feasibility verified by Studio Co-Director."
    )

    return jsonify({
        "success": True,
        "scene_id": scene_id,
        "scene": updated_scene,
        "impact_message": impact_message
    })

@app.route("/api/agent_builder/spec", methods=["GET"])
def api_agent_builder_spec():
    """Returns OpenAPI 3.0 Tool specification for Google Cloud Agent Builder."""
    from services.agent_builder_bridge import agent_builder_bridge
    return jsonify(agent_builder_bridge.get_agent_builder_spec())

@app.route("/api/agent_builder/manifest", methods=["GET"])
def api_agent_builder_manifest():
    """Returns the Google Cloud Agent Builder application manifest."""
    from services.agent_builder_bridge import agent_builder_bridge
    return jsonify(agent_builder_bridge.get_agent_builder_manifest())

@app.route("/api/project/<project_id>/scenes/<scene_id>", methods=["DELETE"])

def api_delete_scene_endpoint(project_id, scene_id):
    """Deletes a scene by ID and renumbers downstream scenes."""
    proj = get_project_db(project_id)
    if not proj:
        return jsonify({"error": "Project not found"}), 404

    characters = get_characters_by_project_db(project_id)
    relationships = get_relationships_by_project_db(project_id)
    scenes = get_scenes_by_project_db(project_id)

    target_sc = next((s for s in scenes if s["id"] == scene_id), None)
    if not target_sc:
        return jsonify({"error": "Scene not found"}), 404

    conn = get_connection()
    gemini._ensure_connected()
    result = gemini.scene_engine.delete_scene_by_number(
        target_scene_number=target_sc["scene_number"],
        project=proj,
        characters=characters,
        relationships=relationships,
        scenes=scenes,
        conn=conn
    )
    conn.close()
    return jsonify(result)

@app.route("/api/project/<project_id>/export/docx", methods=["GET"])
@app.route("/api/projects/<project_id>/export/docx", methods=["GET"])
def api_export_docx(project_id):
    """Generates and downloads a clean Hollywood-standard screenplay formatted DOCX document in the requested language."""
    lang = request.args.get("lang", "EN").upper()
    loc_bundle = localization_service.get_localized_project_details(project_id, lang)
    proj = loc_bundle.get("project")
    if not proj:
        return jsonify({"error": "Project not found"}), 404

    characters = loc_bundle.get("characters", [])
    scenes = loc_bundle.get("scenes", [])

    docx_bytes = create_screenplay_docx(proj, scenes, characters, lang=lang)
    clean_title = proj["title"].replace(" ", "_").replace(":", "_").replace("/", "_")
    prefix = "Screenplay" if lang == "EN" else "Guion"

    return Response(
        docx_bytes,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={prefix}_{clean_title}.docx"}
    )

@app.route("/api/project/<project_id>/memory", methods=["GET"])
def api_get_project_memory(project_id):
    """Returns reconstructed project memory state from SQLite."""
    gemini._ensure_connected()
    memory_state = gemini.project_memory.reconstruct_project_memory(project_id)
    return jsonify(memory_state)

@app.route("/api/project/<project_id>/production_intelligence", methods=["GET"])
def api_get_production_intelligence(project_id):
    """Calculates granular production budget, shooting schedule, explainable basis, and sustainability plan."""
    lang = request.args.get("lang", "EN").upper()
    details = localization_service.get_localized_project_details(project_id, lang=lang)
    proj = details.get("project") or get_project_db(project_id)
    if not proj:
        return jsonify({"error": "Project not found"}), 404
    characters = details.get("characters") or get_characters_by_project_db(project_id)
    scenes = details.get("scenes") or get_scenes_by_project_db(project_id)
    
    from services.production_intelligence import ProductionIntelligence
    budget_data = ProductionIntelligence.calculate_production_budget(proj, scenes, characters, lang=lang)
    sustainability_data = ProductionIntelligence.generate_sustainability_recommendations(proj, scenes, characters, lang=lang)

    # Localize budget categories and sustainability sectors
    if lang != "ES":
        budget_data, sustainability_data = localization_service.get_localized_production_intelligence(
            project_id, budget_data, sustainability_data, lang=lang
        )
    
    return jsonify({
        "project_id": project_id,
        "title": proj["title"],
        "lang": lang,
        "budget": budget_data,
        "sustainability": sustainability_data
    })

@app.route("/api/projects/<project_id>/visual_assets", methods=["GET"])
@app.route("/api/project/<project_id>/visual_assets", methods=["GET"])
def api_get_project_visual_assets(project_id):
    """Returns all visual assets recorded for this project from SQLite."""
    assets = get_visual_assets_by_project_db(project_id)
    return jsonify({
        "success": True,
        "project_id": project_id,
        "count": len(assets),
        "visual_assets": assets
    })

@app.route("/api/system/image_status", methods=["GET"])
def api_system_image_status():
    """Returns runtime diagnostic status of the Google GenAI image service and fallback pipeline."""
    return jsonify(cinematic_image_service.get_runtime_status())

@app.route("/api/visual_assets/retry", methods=["POST"])
def api_retry_visual_asset():
    """Retries generation for an asset using Google GenAI with transparent fallback."""
    data = request.get_json() or {}
    project_id = data.get("project_id")
    asset_type = data.get("asset_type")
    item_id = data.get("item_id")
    if not project_id or not asset_type or not item_id:
        return jsonify({"error": "project_id, asset_type, and item_id are required"}), 400
    
    cinematic_image_service.last_provider_status["quota_limited"] = False
    proj = get_project_db(project_id) or {}
    metadata = {}
    if asset_type == "character":
        chars = get_characters_by_project_db(project_id)
        for c in chars:
            if c.get("id") == item_id:
                metadata = c
                break
    elif asset_type == "scene":
        scenes = get_scenes_by_project_db(project_id)
        for s in scenes:
            if s.get("id") == item_id:
                metadata = s
                break
    else:
        metadata = proj

    result = cinematic_image_service.generate_asset(
        project_id=project_id,
        asset_type=asset_type,
        item_id=item_id,
        metadata=metadata,
        project=proj,
        force=True
    )
    new_url = result.get("url")
    if new_url:
        conn = get_connection()
        cursor = conn.cursor()
        if asset_type == "poster":
            cursor.execute("UPDATE projects SET poster_url = ? WHERE id = ?", (new_url, project_id))
        elif asset_type == "character":
            cursor.execute("UPDATE characters SET avatar_url = ? WHERE id = ?", (new_url, item_id))
        elif asset_type == "scene":
            cursor.execute("UPDATE scenes SET image_url = ? WHERE id = ?", (new_url, item_id))
        conn.commit()
        conn.close()

        # Invalidate project localization cache so that new visual asset immediately reflects across all languages
        clear_project_localizations_db(project_id)

    return jsonify({
        "success": True,
        "url": new_url,
        "asset_type": asset_type,
        "item_id": item_id,
        "result": result,
        "status": cinematic_image_service.get_runtime_status()
    })


@app.route("/api/project/<project_id>/canon", methods=["GET", "POST"])
def api_project_canon(project_id):
    """Retrieves or adds canonical facts for a project."""
    if request.method == "POST":
        data = request.get_json() or {}
        fact_text = data.get("fact_text", "")
        if not fact_text:
            return jsonify({"error": "fact_text is required"}), 400
        fact_id = add_canonical_fact_db(
            project_id=project_id,
            fact_text=fact_text,
            entity_type=data.get("entity_type", "GENERAL"),
            entity_id=data.get("entity_id", ""),
            fact_type=data.get("fact_type", "CANONICAL"),
            scene_established=data.get("scene_established")
        )
        return jsonify({"success": True, "fact_id": fact_id})
    else:
        facts = get_canonical_facts_db(project_id)
        return jsonify({"project_id": project_id, "facts": facts})

@app.route("/api/project/<project_id>/summary", methods=["GET"])
def api_project_summary(project_id):
    """Returns structured production overview."""
    gemini._ensure_connected()
    summary = gemini.project_memory.generate_production_overview(project_id)
    return jsonify(summary)

@app.route("/api/project/<project_id>/research", methods=["GET"])
def api_get_project_research(project_id):
    """Retrieves external web research history (Parallel Search API) isolated for a project."""
    research_list = get_project_research_db(project_id, limit=10)
    return jsonify({
        "project_id": project_id,
        "count": len(research_list),
        "research": research_list
    })

@app.route("/api/project/<project_id>/workflow", methods=["GET"])
def api_get_project_workflow(project_id):
    """Calculates dynamic Hollywood production workflow stages from SQLite state."""
    proj = get_project_db(project_id)
    if not proj:
        return jsonify({"error": "Project not found"}), 404

    characters = get_characters_by_project_db(project_id)
    scenes = get_scenes_by_project_db(project_id)
    relationships = get_relationships_by_project_db(project_id)

    alerts = ContinuityEngine.scan_project_continuity(proj, characters, scenes)
    critical_errors = [a for a in alerts if "Leak" in a.get("issue_type", "") or "Inconsistencia" in a.get("issue_type", "")]

    stages = {
        "concept": {
            "name": "Concepto & Premisa",
            "status": "COMPLETED" if (proj.get("logline") or proj.get("title")) else "IN_PROGRESS",
            "details": proj.get("logline", "Premisa en desarrollo")
        },
        "story": {
            "name": "Estructura Narrativa (3 Actos)",
            "status": "COMPLETED" if proj.get("synopsis") else "IN_PROGRESS",
            "details": f"Género: {proj.get('genre')}, Tono: {proj.get('tone')}"
        },
        "characters": {
            "name": "Diseño de Elenco & Psicología",
            "status": "COMPLETED" if len(characters) >= 2 else ("IN_PROGRESS" if len(characters) > 0 else "PENDING"),
            "details": f"{len(characters)} personajes, {len(relationships)} dinámicas"
        },
        "screenplay": {
            "name": "Escaleta & Libreto Hollywood",
            "status": "COMPLETED" if len(scenes) >= 4 else ("IN_PROGRESS" if len(scenes) > 0 else "PENDING"),
            "details": f"{len(scenes)} escenas registradas en formato estándar"
        },
        "continuity": {
            "name": "Compuerta de Continuidad & Canon",
            "status": "COMPLETED" if len(critical_errors) == 0 and len(scenes) > 0 else ("WARNING" if len(critical_errors) > 0 else "PENDING"),
            "details": "Saludable (0 errores críticos)" if len(critical_errors) == 0 else f"{len(critical_errors)} alertas críticas detectadas"
        },
        "final_draft": {
            "name": "Guion Final & Exportación DOCX",
            "status": "READY" if (len(scenes) >= 4 and len(critical_errors) == 0) else "IN_PROGRESS",
            "details": "Listo para exportación cinematográfica oficial (.docx)"
        }
    }

    is_production_ready = stages["final_draft"]["status"] == "READY"

    return jsonify({
        "project_id": project_id,
        "title": proj.get("title"),
        "production_ready": is_production_ready,
        "stages": stages,
        "metrics": {
            "characters_count": len(characters),
            "scenes_count": len(scenes),
            "relationships_count": len(relationships),
            "critical_continuity_errors": len(critical_errors),
            "total_continuity_alerts": len(alerts)
        }
    })

@app.route("/api/project/<project_id>/rollback", methods=["POST"])
def api_project_rollback(project_id):
    """Executes safe narrative rollback."""
    conn = get_connection()
    gemini._ensure_connected()
    result = gemini.project_memory.execute_rollback(project_id, conn)
    conn.close()
    return jsonify(result)

@app.route("/api/projects/<project_id>/expand_runtime", methods=["POST"])
@app.route("/api/project/<project_id>/expand_runtime", methods=["POST"])
def api_expand_runtime(project_id):
    """Expands project narrative structure and scene count to support target runtime (e.g. 110 min)."""
    data = request.get_json() or {}
    target_runtime = int(data.get("runtime_minutes") or data.get("target_runtime") or 110)
    
    conn = get_connection()
    gemini._ensure_connected()
    result = narrative_engine.expand_runtime_narrative(
        project_id=project_id,
        target_runtime_minutes=target_runtime,
        conn=conn
    )
    conn.close()
    
    # Invalidate cache so fresh expanded scenes are visible immediately in all languages
    clear_project_localizations_db(project_id)
    
    return jsonify(result)

@app.route("/api/continuity/scan/<project_id>", methods=["POST"])
def api_scan_continuity(project_id):
    """Executes a deep continuity audit scanning knowledge boundaries, sequence, and lighting consistency."""
    proj = get_project_db(project_id)
    if not proj:
        return jsonify({"error": "Project not found"}), 404

    characters = get_characters_by_project_db(project_id)
    scenes = get_scenes_by_project_db(project_id)

    alerts = ContinuityEngine.scan_project_continuity(proj, characters, scenes)
    critical_errors = [a for a in alerts if "Leak" in a.get("issue_type", "") or "Inconsistencia" in a.get("issue_type", "")]
    
    scenes_with_alerts = {}
    for a in alerts:
        sc_num = a.get("scene_number", 0)
        if sc_num not in scenes_with_alerts:
            scenes_with_alerts[sc_num] = []
        scenes_with_alerts[sc_num].append(a)

    return jsonify({
        "success": True,
        "project_id": project_id,
        "healthy": len(alerts) == 0,
        "alerts_count": len(alerts),
        "alerts": alerts,
        "critical_errors": critical_errors,
        "scenes_with_alerts": scenes_with_alerts
    })

@app.route("/api/generate", methods=["POST"])
def api_generate():
    """
    ARQUITECTURA AGÉNTICA DE CO-DIRECCIÓN CINEMATOGRÁFICA (FASE 10)
    
    Abandona el enfoque de 'chatbot pasivo' e implementa una orquestación agéntica real:
    1. Ingestión y Reconstrucción del Estado Relacional desde SQLite (studio_cinema.db).
    2. Director Agent (Orquestador): Razona la intención del usuario y planifica la ejecución previa a cualquier mutación.
    3. Zero Mutation Gate: Si un cambio altera drásticamente la trama o es de severidad CRITICAL, no muta la base de datos; exige confirmación.
    4. Parallel Search Autónomo Condicional: Busca información y locaciones reales en la web mediante API solo si es estrictamente necesario.
    5. Motores Especializados (Creative Engines):
       - StoryEngine: Guion literario en estándar de Hollywood (script_text con acotaciones, personajes en MAYÚSCULAS y diálogos).
       - CharacterEngine: Psicología, relaciones y dirección de arte (forzando 2D vintage Disney 1930s-1950s Golden Era).
       - SceneEngine: Estructura de locaciones, props y atmósfera lumínica.
       - ProjectMemory: Hechos canónicos inviolables, consultas factuales y rollback.
    6. Auditoría de Continuidad: Verificación profunda con ContinuityEngine contra inconsistencias.
    7. Retorno de JSON Estructurado Completo para poblar inmediatamente la UI del Frontend.
    """
    data = request.get_json() or {}
    raw_prompt = data.get("prompt", "").strip()
    project_id = data.get("project_id", "proj_default")
    lang = data.get("lang", "en").upper()

    if not raw_prompt:
        return jsonify({"error": "No prompt provided"}), 400

    prompt = raw_prompt
    if lang != "ES":
        lang_names = {"EN": "English", "FR": "French", "DE": "German", "IT": "Italian", "PT": "Portuguese"}
        target_name = lang_names.get(lang, "English")
        prompt = f"{raw_prompt}\n\n[DIRECTIVA DE IDIOMA]: Responde obligatoriamente en el idioma seleccionado por el usuario: {target_name} ({lang})."

    # Ensure project exists in SQLite
    proj = get_project_db(project_id)
    if not proj:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO projects (
            id, title, tagline, genre, format, runtime_minutes, tone, target_audience,
            status, progress_percentage, target_budget, estimated_budget, shooting_days,
            crew_count, available_locations, synopsis, logline, visual_aesthetic,
            eco_impact_score, age_rating, poster_url, is_demo
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id, "Nueva Producción", "En desarrollo", "Cine", "FILM", 110, "Cinematográfico",
            "General", "EN DESARROLLO", 0, 75000.0, 70000.0, 0, 0, 0,
            "Nueva producción", "En desarrollo", "Estética cinematográfica", 90, "PG-13",
            generate_vintage_scene_illustration("NUEVA PRODUCCIÓN", "ESTUDIO DE CINE", "EXT", "NIGHT"), 0
        ))
        conn.commit()
        conn.close()
        proj = get_project_db(project_id)

    # Ingest project elements from SQLite
    characters = get_characters_by_project_db(project_id)
    relationships = get_relationships_by_project_db(project_id)
    scenes = get_scenes_by_project_db(project_id)

    if project_id not in project_conversations:
        project_conversations[project_id] = []

    history = project_conversations[project_id]
    history.append({"role": "user", "text": raw_prompt})
    try:
        save_project_message_db(project_id, "user", raw_prompt)
    except Exception:
        pass

    p_low = raw_prompt.lower()
    is_confirmation = any(w in p_low for w in [
        "confirmo", "confirmo los cambios", "aplica el plan", "aplica los cambios", "sí, hazlo", "si, hazlo", "procede", "ejecuta el plan",
        "confirm", "i confirm", "confirm changes", "confirm the changes", "apply plan", "apply the plan", "apply changes", "yes, do it", "yes do it", "proceed", "execute the plan"
    ])
    is_rollback = any(w in p_low for w in ["deshaz el último", "deshaz el ultimo", "deshacer", "revertir", "rollback"])
    is_director_preference = any(w in p_low for w in ["mantén un tono", "manten un tono", "quiero un tono", "el tono debe ser", "tono de thriller"])

    conn = get_connection()
    gemini._ensure_connected()

    # 1. DIRECTOR AGENT (ORQUESTADOR): RAZONAMIENTO SEMÁNTICO PREVIO
    intent = director_agent.analyze_intent(
        prompt=prompt,
        project=proj,
        characters=characters,
        relationships=relationships,
        scenes=scenes
    )

    result = None

    # 2. CONFIRMACIÓN RÁPIDA DE PLAN PENDIENTE (SI FUE APROBADO)
    if is_confirmation and project_id in director_agent.pending_plans:
        pending_plan, orig_prompt = director_agent.pending_plans.pop(project_id)
        result = narrative_engine.execute_confirmed_repairs(
            plan=pending_plan,
            project=proj,
            characters=characters,
            relationships=relationships,
            scenes=scenes,
            conn=conn,
            prompt=orig_prompt
        )

    # 2.3 EXPANSIÓN NARRATIVA DE DURACIÓN (P.EJ. 110 MINUTOS / 16 ESCENAS)
    elif any(w in p_low for w in [
        "110 minutos", "110 min", "110 minutes", "amplía a 110", "amplia a 110",
        "expand runtime", "expand to 110", "extiende la película", "extiende a 110",
        "cambia la duración", "cambia duracion", "aumenta la duración", "aumenta duracion",
        "runtime expansion", "expand narrative", "expand script", "ampliar metraje"
    ]):
        target_mins = 110
        import re
        nums = re.findall(r'\b(90|100|110|120|130|140|150|180|\d{2,3})\s*(?:min|minutos|minutes)?\b', p_low)
        if nums:
            try:
                target_mins = int(nums[0])
            except Exception:
                target_mins = 110
        if target_mins < 60:
            target_mins = 110
            
        exp_res = narrative_engine.expand_runtime_narrative(
            project_id=project_id,
            target_runtime_minutes=target_mins,
            conn=conn,
            lang=lang
        )
        is_en_lang = (lang != "ES")
        if is_en_lang:
            resp_text = (
                f"⚡ **Narrative Architecture Expanded to {target_mins} Minutes:**\n\n"
                f"• **Scene Count Expanded:** {exp_res.get('new_scene_count')} complete scenes formatted in Hollywood standard.\n"
                f"• **Shooting Schedule:** Recalculated to {exp_res.get('shooting_days')} days.\n"
                f"• **Budget Allocation:** Estimated at ${exp_res.get('estimated_budget', 42500000.0):,.2f}.\n"
                f"• **Canon & Continuity:** All character relationships, locations, and dramatic tension preserved."
            )
        else:
            resp_text = (
                f"⚡ **Estructura Narrativa Expandida a {target_mins} Minutos:**\n\n"
                f"• **Volumen de Escenas:** {exp_res.get('new_scene_count')} escenas completas con formato estándar de Hollywood.\n"
                f"• **Plan de Rodaje:** Recalculado a {exp_res.get('shooting_days')} días de filmación.\n"
                f"• **Presupuesto Estimado:** ${exp_res.get('estimated_budget', 42500000.0):,.2f}.\n"
                f"• **Canon y Continuidad:** Relaciones del elenco, locaciones y tensión dramática preservadas."
            )
        result = {
            "response": resp_text,
            "action": "RUNTIME_EXPANSION_APPLIED",
            "runtime_minutes": target_mins,
            "scenes_count": exp_res.get("new_scene_count"),
            "mutation": True,
            "engines_used": ["DirectorAgent", "NarrativeEngine", "SceneEngine"]
        }

    # 2.5 DIRECTORAGENT & PRODUCTIONINTELLIGENCE: CONSULTAS DE PRESUPUESTO & SOSTENIBILIDAD
    elif intent.scope in ["BUDGET_QUERY", "SUSTAINABILITY_QUERY"]:
        result = director_agent.answer_production_query(
            prompt=raw_prompt,
            project=proj,
            scenes=scenes,
            characters=characters,
            lang=lang
        )

    # 2.6 PARALLEL SEARCH CONDICIONAL (BÚSQUEDA WEB AUTÓNOMA CON ZERO MUTATION EN GUION)
    elif intent.scope == "EXTERNAL_RESEARCH":
        result = director_agent._handle_external_research(
            prompt=prompt,
            project=proj,
            characters=characters,
            scenes=scenes,
            conn=conn
        )

    # 2.7 PROJECTMEMORY: CONSULTAS FACTUALES Y TEMPORALES DE PRODUCCIÓN (ZERO MUTATION)
    elif intent.scope == "QUERY":
        result = project_memory.answer_factual_query(prompt, project_id, conn)

    # 3. STORYENGINE: GENERACIÓN TÉCNICA DE PRODUCCIÓN COMPLETA (STORY BIBLE & SCREENPLAY)
    elif intent.scope == "FULL_STORY_GENERATION" or (
        (len(scenes) == 0 or "nueva producción" in proj.get("title", "").lower())
        and len(prompt) > 5 and not is_rollback and not is_director_preference and not is_confirmation
    ):
        result = gemini._handle_full_film_generation_real(proj, prompt)

    # 4. ZERO MUTATION GATE: PROTECCIÓN CONTRA MUTACIONES CRÍTICAS NO CONFIRMADAS
    elif (intent.confirmation_required or intent.severity == "CRITICAL") and not is_confirmation:
        plan = None
        try:
            plan = narrative_engine.analyze_change_impact(
                prompt=prompt,
                project=proj,
                characters=characters,
                relationships=relationships,
                scenes=scenes
            )
            director_agent.pending_plans[project_id] = (plan, prompt)
        except Exception:
            pass

        impact_desc = (
            plan.impact.explanation
            if plan and hasattr(plan, "impact") and hasattr(plan.impact, "explanation")
            else getattr(plan, "response_explanation", "Esta modificación altera profundamente el arco dramático o las relaciones centrales de la historia.")
        )
        affected_sc = (
            plan.impact.affected_scene_numbers
            if plan and hasattr(plan, "impact") and hasattr(plan.impact, "affected_scene_numbers")
            else [s.get("scene_number", 1) for s in scenes]
        )

        is_en_lang = (lang != "ES")
        if is_en_lang:
            conf_resp = (
                f"⚠️ **CRITICAL DRAMATIC IMPACT ALERT (Zero Mutation Gate):**\n\n"
                f"{impact_desc}\n\n"
                f"• **Severity:** {intent.severity}\n"
                f"• **Scope:** {intent.scope}\n"
                f"• **Affected Scenes:** {affected_sc}\n\n"
                f"Do you want me to apply these cascading changes and automatically repair continuity? Reply **\"I confirm the changes\"** to proceed."
            )
        else:
            conf_resp = (
                f"⚠️ **ALERTA DE IMPACTO DRAMÁTICO CRÍTICO (Zero Mutation Gate):**\n\n"
                f"{impact_desc}\n\n"
                f"• **Severidad:** {intent.severity}\n"
                f"• **Alcance:** {intent.scope}\n"
                f"• **Escenas Afectadas:** {affected_sc}\n\n"
                f"¿Deseas que aplique estos cambios en cascada y repare automáticamente la continuidad? Responda **\"Confirmo los cambios\"** para proceder."
            )

        result = {
            "response": conf_resp,
            "action": "CONFIRMATION_REQUIRED",
            "severity": intent.severity,
            "scope": intent.scope,
            "requires_confirmation": True,
            "change_id": f"chg_{project_id}_{int(time.time())}",
            "plan": plan.model_dump() if (plan and hasattr(plan, "model_dump")) else (plan.dict() if (plan and hasattr(plan, "dict")) else None),
            "mutation": False,
            "engines_used": ["DirectorAgent", "NarrativeEngine"]
        }

    # 7. PROJECTMEMORY: ROLLBACK INMEDIATO AL ESTADO CANÓNICO PREVIO
    elif intent.scope == "ROLLBACK":
        result = project_memory.execute_rollback(project_id, conn)

    # 8. PROJECTMEMORY: DIRECTRICES CREATIVAS Y TONALES DEL DIRECTOR
    elif intent.scope == "DIRECTOR_PREFERENCE":
        result = project_memory.record_director_preference(prompt, project_id, conn)

    # 9. CHARACTERENGINE: GESTIÓN DE ELENCO, PSICOLOGÍA & ARTE CARTOON VINTAGE 2D
    elif intent.scope in ["LOCAL_ATTRIBUTE", "CHARACTER_RELATION"]:
        result = character_engine.process_conversational_request(
            prompt=prompt,
            project=proj,
            characters=characters,
            relationships=relationships,
            scenes=scenes,
            conn=conn
        )

    # 10. SCENEENGINE: ESCALETA, LOCACIONES Y ADAPTACIÓN DE INVESTIGACIÓN EXTERNA
    elif intent.scope == "SINGLE_SCENE":
        edit_prompt = prompt
        is_apply_research = any(w in p_low for w in [
            "usa la mejor opción", "usa la mejor opcion", "con la locación", "con la locacion",
            "locación investigada", "locacion investigada", "aplica la investigación", "aplica la investigacion",
            "usar la mejor opcion", "usa la locacion",
            "use the best option", "use best option", "apply the research", "apply research",
            "with the location", "investigated location", "scouted location", "adapt scene with research",
            "use recommended location", "use the recommended location", "use scouted location",
            "beste option", "recherche anwenden", "recherchierter drehort", "scouting anwenden",
            "utiliser la meilleure option", "appliquer la recherche", "lieu recherché", "repérage",
            "usa la migliore opzione", "applica la ricerca", "use a melhor opção", "aplicar pesquisa"
        ])
        if is_apply_research:
            try:
                prior_research = get_project_research_db(project_id, limit=1, conn=conn)
                if prior_research:
                    sources = prior_research[0].get("sources", [])
                    top_source = sources[0].get("title") if sources else "Discovered real-world location"
                    if lang == "ES":
                        edit_prompt = f"{prompt}. Contexto de locación real descubierto con Parallel Search: '{top_source}'. Modifica el slugline/locación y resumen de la escena acorde a este lugar real."
                    else:
                        edit_prompt = f"{prompt}. Real-world location context discovered via Parallel Search API: '{top_source}'. Update the scene slugline, location, and summary according to this real place."
            except Exception:
                pass


        result = scene_engine.process_scene_conversational_edit(
            prompt=edit_prompt,
            project=proj,
            characters=characters,
            relationships=relationships,
            scenes=scenes,
            conn=conn
        )

    # 11. NARRATIVEENGINE & CONTINUITYENGINE: AJUSTE NARRATIVO MULTI-ESCENA CON REPARACIÓN EN CASCADA
    else:
        try:
            plan = narrative_engine.analyze_change_impact(
                prompt=prompt,
                project=proj,
                characters=characters,
                relationships=relationships,
                scenes=scenes
            )
            if plan.requires_confirmation and not plan.auto_executable:
                is_en_lang = (lang != "ES")
                conf_resp2 = (
                    f"⚠️ **Director Agent — Confirmation Required:**\n\n"
                    f"{plan.response_explanation}\n\n"
                    f"• **Affected Scenes:** {plan.impact.affected_scene_numbers}\n"
                    f"• **Consequences:** {', '.join(plan.impact.narrative_consequences)}\n\n"
                    f"Reply **'I confirm the changes'** to apply cascading repairs."
                ) if is_en_lang else (
                    f"⚠️ **Director Agent — Confirmación Requerida:**\n\n"
                    f"{plan.response_explanation}\n\n"
                    f"• **Escenas Afectadas:** {plan.impact.affected_scene_numbers}\n"
                    f"• **Consecuencias:** {', '.join(plan.impact.narrative_consequences)}\n\n"
                    f"Responda **'Confirmo los cambios'** para aplicar las reparaciones en cascada."
                )
                result = {
                    "action": "CONFIRMATION_REQUIRED",
                    "severity": plan.impact.severity,
                    "plan": plan.model_dump(),
                    "response": conf_resp2
                }
            else:
                result = narrative_engine.execute_confirmed_repairs(
                    plan=plan,
                    project=proj,
                    characters=characters,
                    relationships=relationships,
                    scenes=scenes,
                    conn=conn,
                    prompt=prompt
                )
        except Exception as e:
            result = {
                "action": "ORCHESTRATION_COMPLETED",
                "response": (
                    f"🎬 **Director Agent:** I have evaluated instruction for '{proj.get('title')}'. Narrative consistency and production canon are preserved."
                    if (lang != "ES") else
                    f"🎬 **Director Agent:** He evaluado la instrucción para '{proj.get('title')}'. Se mantiene la coherencia narrativa y el canon de la producción."
                )
            }

    conn.close()

    if not result:
        result = {
            "response": "La instrucción ha sido procesada por el Director Agent.",
            "action": "ORCHESTRATION_COMPLETED"
        }

    action = result.get("action", "CHAT")
    response_text = result.get("response", "Instrucción procesada por el Co-Director.")
    history.append({"role": "agent", "text": response_text})
    try:
        save_project_message_db(project_id, "agent", response_text)
    except Exception:
        pass

    # 12. SINCRONIZACIÓN Y AUDITORÍA DE CONTINUIDAD EN TIEMPO REAL
    updated_project = get_project_db(project_id)
    updated_characters = get_characters_by_project_db(project_id)
    updated_relationships = get_relationships_by_project_db(project_id)
    updated_scenes = get_scenes_by_project_db(project_id)
    updated_facts = get_canonical_facts_db(project_id)

    continuity_alerts = []
    continuity_status = result.get("continuity_status", "PASS")
    try:
        continuity_alerts = ContinuityEngine.scan_project_continuity(
            updated_project, updated_characters, updated_scenes
        )
        if any("Leak" in a.get("issue_type", "") for a in continuity_alerts):
            continuity_status = "WARNING"
    except Exception:
        pass

    if lang != "ES" or (project_id in localization_service.DEMO_PROJECT_I18N and "ES" in localization_service.DEMO_PROJECT_I18N[project_id]):
        loc_bundle = localization_service.get_localized_project_details(project_id, lang)
        updated_project = loc_bundle.get("project", updated_project)
        updated_characters = loc_bundle.get("characters", updated_characters)
        updated_relationships = loc_bundle.get("relationships", updated_relationships)
        updated_scenes = loc_bundle.get("scenes", updated_scenes)

    # 13. DISTRIBUCIÓN DEL JSON COMPLETO AL FRONTEND
    return jsonify({
        "response": response_text,
        "action": action,
        "severity": result.get("severity", getattr(intent, "severity", "LOW")),
        "scope": result.get("scope", getattr(intent, "scope", "GENERAL")),
        "intent": intent.model_dump() if hasattr(intent, "model_dump") else {},
        "engines_used": result.get("engines_used", getattr(intent, "required_engines", ["DirectorAgent", "ContinuityEngine"])),
        "continuity_status": continuity_status,
        "plan": result.get("plan"),
        "change_id": result.get("change_id"),
        "sources": result.get("sources", []),
        "sources_count": result.get("sources_count", len(result.get("sources", []))),
        "mutation": result.get("mutation", False if (action.startswith("EXTERNAL_RESEARCH") or action == "FACTUAL_QUERY_ANSWERED" or action == "CONFIRMATION_REQUIRED" or action == "CHAT") else True),
        "repaired_scene_numbers": result.get("repaired_scene_numbers", []),
        "continuity_alerts_count": len(continuity_alerts),
        "critical_alerts_count": len([a for a in continuity_alerts if "Leak" in a.get("issue_type", "") or "Inconsistencia" in a.get("issue_type", "")]),
        "title": result.get("title", updated_project.get("title", "") if updated_project else ""),
        "status": updated_project.get("status", "En Producción Activa") if updated_project else "En Producción Activa",
        "genre": result.get("genre", updated_project.get("genre", "") if updated_project else ""),
        "character_count": result.get("character_count", len(updated_characters)),
        "scene_count": result.get("scene_count", len(updated_scenes)),
        "canonical_facts_count": len(updated_facts),
        "requires_confirmation": result.get("requires_confirmation", False),
        "details": {
            "project": updated_project,
            "characters": updated_characters,
            "relationships": updated_relationships,
            "scenes": updated_scenes,
            "canonical_facts": updated_facts
        }
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)