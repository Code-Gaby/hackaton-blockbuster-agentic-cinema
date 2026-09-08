import streamlit as st
from core.models import Project
from core.translations import get_text
from services.gemini_service import GeminiCreativeProvider

def render_story_tab(project: Project):
    """Renders Story concept, logline, synopsis, themes, and tone development."""
    gemini = GeminiCreativeProvider()
    lang = st.session_state.get("language", "ES")

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown(f"### {get_text('tab_story', lang)}")

    c1, c2 = st.columns([3, 2])
    with c1:
        project.logline = st.text_area(get_text("logline", lang), project.logline, height=90)
        project.synopsis = st.text_area(get_text("synopsis", lang), project.synopsis, height=190)

    with c2:
        project.tone = st.text_input("Tono y Atmósfera Dramática", project.tone)
        project.visual_aesthetic = st.text_area("Estética Visual y Dirección de Arte", project.visual_aesthetic, height=110)
        project.target_audience = st.text_input("Público Objetivo", project.target_audience)

    if st.button("Desarrollar y Expandir Historia con Gemini AI"):
        with st.spinner("Gemini Creative Brain generando nuevos arcos narrativos..."):
            new_outline = gemini.generate_story_outline(project.synopsis, project.format, project.genre)
            project.logline = new_outline["logline"]
            project.synopsis = new_outline["synopsis"]
            project.tone = new_outline["tone"]
            project.visual_aesthetic = new_outline["visual_aesthetic"]
            st.success("¡Historia expandida con éxito por Gemini!")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
