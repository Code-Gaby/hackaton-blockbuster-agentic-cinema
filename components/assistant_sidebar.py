import streamlit as st
from core.models import Project
from core.translations import get_text
from services.gemini_service import GeminiCreativeProvider

def render_assistant_sidebar(project: Project):
    """Renders persistent context-aware AI Co-Director Assistant drawer."""
    gemini = GeminiCreativeProvider()
    lang = st.session_state.get("language", "ES")

    st.sidebar.markdown(f"### {get_text('assistant_title', lang)}")
    st.sidebar.caption(get_text("assistant_caption", lang))

    # Quick Suggestion Action Buttons
    st.sidebar.markdown("**Acciones Rápidas:**")
    q1 = st.sidebar.button(get_text("quick_cheaper", lang))
    q2 = st.sidebar.button(get_text("quick_continuity", lang))
    q3 = st.sidebar.button(get_text("quick_emotional", lang))
    q4 = st.sidebar.button(get_text("quick_risks", lang))

    user_query = None
    if q1:
        user_query = "Optimizar presupuesto y hacer la producción más económica."
    elif q2:
        user_query = "Buscar contradicciones de continuidad en el guion."
    elif q3:
        user_query = "¿Quién es el centro emocional de la historia?"
    elif q4:
        user_query = "¿Cuáles son las escenas con mayor riesgo de producción?"

    # Render History
    for msg in st.session_state.assistant_messages:
        role_label = "Co-Director AI" if msg["role"] == "assistant" else "Director"
        st.sidebar.markdown(f"**{role_label}:**")
        st.sidebar.markdown(msg["content"])
        st.sidebar.markdown("---")

    input_text = st.sidebar.text_input(get_text("ask_assistant", lang), key="assistant_chat_input")
    if st.sidebar.button(get_text("send_query", lang)) or user_query:
        query = user_query if user_query else input_text
        if query:
            st.session_state.assistant_messages.append({"role": "user", "content": query})
            with st.spinner("Co-Director AI analizando producción..."):
                reply = gemini.answer_co_director_query(query, {"title": project.title, "budget": project.target_budget})
                st.session_state.assistant_messages.append({"role": "assistant", "content": reply})
            st.rerun()
