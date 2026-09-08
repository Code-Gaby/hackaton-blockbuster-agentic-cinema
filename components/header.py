import streamlit as st
from core.state import get_current_project, add_new_project, get_all_projects
from core.translations import get_text
from services.gemini_service import GeminiCreativeProvider
from services.ibm_service import IBMProductionProvider

def render_header():
    """Renders top velvet curtain banner, 6-language switcher, format selector, and project status."""
    project = get_current_project()
    gemini = GeminiCreativeProvider()
    ibm = IBMProductionProvider()

    lang = st.session_state.get("language", "ES")

    # Velvet Curtain & Marquee Banner
    st.markdown(
        f"""
        <div class="velvet-curtains-header">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div class="cinematic-title">{get_text('studio_title', lang)}</div>
                    <div class="cinematic-subtitle">{get_text('studio_subtitle', lang)}</div>
                </div>
                <div class="ticket-stub">HOLLYWOOD DIGITAL STUDIO</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Top Control Bar: Project Selector, Format Radio, Language, & Agent Status
    c_proj, c_format, c_lang, c_status = st.columns([4, 3, 3, 4])

    with c_proj:
        all_projects = get_all_projects()
        project_ids = [p["id"] for p in all_projects]
        project_titles = [f"{p['title']} ({p['format']})" + (" [DEMO]" if p.get('is_demo') else "") for p in all_projects]
        
        current_idx = project_ids.index(project.id) if project.id in project_ids else 0
        selected_idx = st.selectbox(
            get_text("current_project", lang),
            range(len(project_titles)),
            format_func=lambda i: project_titles[i],
            index=current_idx
        )
        
        if project_ids[selected_idx] != st.session_state.active_project_id:
            st.session_state.active_project_id = project_ids[selected_idx]
            st.rerun()

    with c_format:
        new_format = st.radio(
            get_text("format_mode", lang),
            ["FILM", "THEATRE", "SERIES"],
            index=["FILM", "THEATRE", "SERIES"].index(project.format),
            horizontal=True
        )
        if new_format != project.format:
            project.format = new_format
            st.rerun()

    with c_lang:
        languages = {"ES": "Español", "EN": "English", "FR": "Français", "DE": "Deutsch", "IT": "Italiano", "PT": "Português"}
        lang_keys = list(languages.keys())
        current_lang_idx = lang_keys.index(lang) if lang in lang_keys else 0
        
        selected_lang_key = st.selectbox(
            get_text("lang_selector", lang),
            lang_keys,
            format_func=lambda k: languages[k],
            index=current_lang_idx
        )
        if selected_lang_key != lang:
            st.session_state.language = selected_lang_key
            st.rerun()

    with c_status:
        st.markdown("<div style='text-align: right; padding-top: 10px;'>", unsafe_allow_html=True)
        g_label = get_text("gemini_online", lang) if gemini.connected else "GEMINI: Active (Demo)"
        g_badge = f'<span class="badge-online">{g_label}</span>'
        ibm_badge = f'<span class="badge-gold">IBM watsonx: Online</span>' if ibm.connected else f'<span class="badge-gold">{get_text("demo_mode", lang)} (IBM)</span>'
        st.markdown(f"{g_badge} &nbsp; {ibm_badge}", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Clean Project Onboarding Modal / Expander
    with st.expander(f"+ {get_text('create_project', lang)}", expanded=False):
        st.markdown("#### Crear Nuevo Proyecto Limpio (Sin Datos Demo)")
        c1, c2, c3, c4 = st.columns(4)
        n_title = c1.text_input(get_text("project_title", lang), "Mi Nueva Película")
        n_genre = c2.selectbox(get_text("genre", lang), ["Sci-Fi Thriller", "Psychological Drama", "Cyberpunk Noir", "Historical Epic", "Musical Theatre"])
        n_fmt = c3.selectbox(get_text("format", lang), ["FILM", "THEATRE", "SERIES"])
        n_budget = c4.number_input(get_text("target_budget", lang), min_value=5000.0, max_value=5000000.0, value=50000.0, step=5000.0)
        n_logline = st.text_area("Describe tu idea inicial (Prompt para la IA):", "Una historia sobre...")
        
        if st.button(get_text("initialize_project", lang)):
            add_new_project(n_title, n_genre, n_fmt, n_budget, n_logline)
            st.success(f"¡Proyecto '{n_title}' creado con éxito de forma limpia!")
            st.rerun()

    st.markdown('<div class="cinema-film-strip"></div>', unsafe_allow_html=True)
