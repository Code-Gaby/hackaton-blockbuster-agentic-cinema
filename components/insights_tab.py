import streamlit as st
import time
from core.models import Project
from core.translations import get_text
from services.ibm_service import IBMProductionProvider
from services.agent_orchestrator import AgentOrchestrator

def render_insights_tab(project: Project):
    """Renders Stage 07 INSIGHTS: IBM & Gemini AI Production Intelligence, Control Room, & Making-Of Timeline."""
    lang = st.session_state.get("language", "ES")
    ibm = IBMProductionProvider()

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown(f"### {get_text('stage_07', lang)} — AI PRODUCTION INTELLIGENCE & CONTROL ROOM")
    st.markdown("Auditoría analítica impulsada por IBM watsonx.ai e inteligencia creativa de Gemini 2.5.")

    # Primary Insight Block (Single Primary Insight + WHY + WHAT CAN WE DO)
    analysis = ibm.analyze_production_feasibility(project)
    
    st.markdown(
        f"""
        <div class="glass-card-gold">
            <div style="font-family: 'Cinzel', serif; color: #D4AF37; font-size: 1.1rem; font-weight: 700;">
                PRIMARY AI PRODUCTION INSIGHT
            </div>
            <h3 style="color: #FFFFFF; margin-top: 6px;">
                "{analysis['ibm_recommendation']}"
            </h3>
            <hr style="border: 0.5px solid rgba(212,175,55,0.3); margin: 14px 0;">
            <div style="color: #CBD5E1; font-size: 0.9rem;">
                <strong>¿POR QUÉ (WHY)?</strong>
                <p>El presupuesto estimado actual de ${analysis['estimated_budget']:,.2f} supera el presupuesto objetivo por ${analysis['variance']:,.2f} debido a 6 secuencias complejas de efectos visuales y 3 escenarios externos.</p>
                <strong>¿QUÉ PODEMOS HACER (WHAT CAN WE DO)?</strong>
                <p>Utilizar el optimizador de presupuesto de Gemini para consolidar las locaciones exteriores en el hangar principal y sustituir efectos pirotécnicos por iluminación volumétrica LED.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Live Agentic Loop Simulation
    st.markdown("#### 🎛️ BUCLE DE CO-DIRECCIÓN DE AGENTES")
    if st.button(get_text("run_agent_loop", lang), type="primary"):
        with st.status("Ejecutando bucle de co-dirección Gemini + IBM...", expanded=True) as status:
            st.write("🧠 **Paso 1: Gemini (Cerebro Creativo)** genera 34 escenas preliminares de guion...")
            time.sleep(0.5)
            st.write("📊 **Paso 2: IBM watsonx.ai (Inteligencia de Producción)** audita métricas: <i>Costo $68,400 > Objetivo $50,000</i>. Detecta 6 escenas de alto VFX y 3 locaciones exteriores.")
            time.sleep(0.6)
            st.write("💡 **Paso 3: IBM watsonx → Gemini**: '12 locaciones y 6 VFX generan sobrecostos de $18,400. Proponer alternativas creativas.'")
            time.sleep(0.5)
            st.write("🎨 **Paso 4: Gemini (Cerebro Creativo)** reescribe escenas 5 y 11 trasladándolas al corredor del hangar principal y sustituyendo vapores por luces LED pulsantes.")
            time.sleep(0.6)
            st.write("✅ **Paso 5: IBM watsonx** valida las escenas modificadas: Costo estimado reducido a <b>$49,500</b>. Estado: <b>FACTIBLE</b>.")
            status.update(label="✅ Bucle de Agentes Completado — ¡Proyecto Optimizado!", state="complete")
        st.success("¡Ciclo completado! Presupuesto optimizado al 99.0% ($49,500 / $50,000).")

    st.markdown("</div>", unsafe_allow_html=True)

    # "The Making Of..." Production History Log
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### THE MAKING OF — HISTORIAL AUDITABLE DE PRODUCCIÓN")

    for log in reversed(project.history_logs):
        st.markdown(
            f"""
            <div style="background: rgba(14, 11, 18, 0.85); border-left: 4px solid #D4AF37; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between;">
                    <strong style="color: #FFFFFF; font-size: 1rem;">{log['event']}</strong>
                    <span style="color: #94A3B8; font-size: 0.8rem;">{log['timestamp']}</span>
                </div>
                <p style="color: #CBD5E1; font-size: 0.88rem; margin-top: 6px; margin-bottom: 0;">{log['details']}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)
