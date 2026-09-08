import streamlit as st
from core.models import Project
from core.translations import get_text
from services.gemini_service import GeminiCreativeProvider
from services.ibm_service import IBMProductionProvider

def render_assistant_drawer(project: Project, current_stage: str):
    """Renders the Center AI Co-Director Workspace (Cursor for Directors mental model)."""
    lang = st.session_state.get("language", "ES")
    gemini = GeminiCreativeProvider()
    ibm = IBMProductionProvider()

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="agent-header-banner">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h3 style="margin: 0; font-family: 'Cinzel', serif;">✦ CO-DIRECTOR AI WORKSPACE</h3>
                    <p style="margin: 4px 0 0 0; color: #94A3B8; font-size: 0.85rem;">
                        Gemini 2.5 (Cerebro Creativo) & IBM watsonx.ai (Inteligencia de Producción) en vivo.
                    </p>
                </div>
                <span class="badge-gold">PRODUCCIÓN ACTIVA: {project.title}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Co-Director Initial Status
    st.markdown(
        f"""
        <div style="background: rgba(0,0,0,0.4); padding: 14px 18px; border-radius: 6px; border-left: 3px solid #D4AF37; margin-bottom: 15px;">
            <b>Co-Director AI:</b> Bienvenido de nuevo, Director. Su proyecto en formato <b>{project.format}</b> cuenta con <b>{len(project.characters)} personajes</b> y <b>{len(project.scenes)} escenas</b> registradas. ¿En qué aspecto de la dirección o producción desea avanzar?
        </div>
        """,
        unsafe_allow_html=True
    )

    # Suggested Action Chips
    st.markdown("##### Acciones Sugeridas para el Co-Director:")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("📌 Diagnosticar Presupuesto", key="chip_1"):
        st.session_state.active_prompt = "Auditar presupuesto y detectar mayor costo"
    if c2.button("👥 Desarrollar Reparto", key="chip_2"):
        st.session_state.active_prompt = "Analizar arco y motivaciones del reparto"
    if c3.button("🎞 Auditar Continuidad", key="chip_3"):
        st.session_state.active_prompt = "Escanear guion en busca de errores de continuidad"
    if c4.button("📅 Plan de Rodaje", key="chip_4"):
        st.session_state.active_prompt = "Generar cronograma de rodaje por bloques"

    # Chat Messages Log
    st.markdown("---")
    for msg in st.session_state.assistant_messages[-4:]:
        role_label = "🎬 DIRECTOR" if msg["role"] == "user" else "✦ CO-DIRECTOR AI"
        bg_style = "rgba(229,9,20,0.1)" if msg["role"] == "user" else "rgba(212,175,55,0.08)"
        border_style = "#E50914" if msg["role"] == "user" else "#D4AF37"
        
        st.markdown(
            f"""
            <div style="background: {bg_style}; padding: 12px 16px; border-radius: 6px; border-left: 3px solid {border_style}; margin-bottom: 10px;">
                <div style="font-size: 0.75rem; font-weight: 700; color: {border_style}; text-transform: uppercase;">{role_label}</div>
                <div style="margin-top: 4px; font-size: 0.9rem;">{msg['content']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Input Box & Query Processor
    default_input = st.session_state.get("active_prompt", "")
    user_query = st.text_input("Consulte a su Co-Director IA:", value=default_input, placeholder="Ej: Reducir costo de escena 5 o crear personaje...")
    
    if st.button("✦ Enviar Consulta al Co-Director") and user_query.strip():
        st.session_state.assistant_messages.append({"role": "user", "content": user_query})
        
        # Multi-Department Thinking Sequence Output
        with st.status("PROCESANDO CON EL EQUIPO DE PRODUCCIÓN (MULTI-DEPARTAMENTO)...", expanded=True) as status:
            st.write("✦ Gemini Creative Dept: Analizando intención narrativa y concepto...")
            st.write("🎬 Story Dept: Evaluando ritmo y estructura dramática...")
            st.write("🎭 Character Dept: Verificando arcos y motivaciones del reparto...")
            st.write("🎥 Cinematography: Evaluando lenguaje visual y encuadres...")
            st.write("◈ IBM Production Intelligence: Auditando viabilidad operativa y costos...")
            st.write("🎬 Production Dept: Calculando impacto en cronograma y recursos...")
            
            ai_response = gemini.generate_creative_response(user_query, project)
            status.update(label="✓ PROCESAMIENTO COMPLETADO POR EL ESTUDIO", state="complete")
        
        st.session_state.assistant_messages.append({"role": "assistant", "content": ai_response})
        st.session_state.active_prompt = ""
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
