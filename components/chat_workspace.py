import streamlit as st
from core.models import Project
from services.gemini_service import GeminiCreativeProvider
from services.ibm_service import IBMProductionProvider
from components.cinema_icons import get_svg_icon

def render_chat_workspace(project: Project):
    """Renders Visionary Agent Studio Chat matching Agentic Cinema replacement template."""
    gemini = GeminiCreativeProvider()
    ibm = IBMProductionProvider()

    st.markdown(
        """
        <div class="chat-container">
        """,
        unsafe_allow_html=True
    )

    # Chat Messages Feed
    st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
    
    for msg in st.session_state.assistant_messages:
        if msg["role"] == "user":
            st.markdown(
                f"""
                <div class="message user">
                    <div class="msg-avatar">
                        {get_svg_icon('chat', 18, '#FFFFFF')}
                    </div>
                    <div class="msg-content">
                        <strong>Director:</strong> {msg['content']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div class="message agent">
                    <div class="msg-avatar">
                        {get_svg_icon('brand', 18, '#000000')}
                    </div>
                    <div class="msg-content">
                        <strong>Visionary Agent:</strong> {msg['content']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown('</div>', unsafe_allow_html=True)

    # Input Box & Send Button
    prefill = st.session_state.pop("chat_prefill", "")
    
    c_inp, c_btn = st.columns([10, 2])
    with c_inp:
        user_prompt = st.text_input(
            "Mensaje",
            value=prefill,
            placeholder="Ej: Genera una historia de cine sobre una mujer con superpoderes en 1990...",
            label_visibility="collapsed",
            key="studio_chat_input"
        )
    with c_btn:
        send_clicked = st.button("Generar ✦", type="primary", use_container_width=True)

    if send_clicked and user_prompt.strip():
        st.session_state.assistant_messages.append({"role": "user", "content": user_prompt})

        # Spinning Film Reel Loader matching specification
        st.markdown(
            f"""
            <div class="film-loader">
                {get_svg_icon('film_reel', 24, 'var(--gold-primary)')}
                <span class="film-loader-text">REBOBINANDO CINTA & SINTETIZANDO HISTORIA...</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.spinner("Sintetizando arcos dramáticos con Gemini y factibilidad con IBM watsonx..."):
            response_text = gemini.generate_creative_response(user_prompt, project)

        st.session_state.assistant_messages.append({"role": "assistant", "content": response_text})
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
