import streamlit as st
import time
from core.models import Project
from services.agent_orchestrator import AgentOrchestrator

def render_control_room(project: Project):
    """Renders the AI Control Room displaying live Gemini <-> IBM collaboration."""
    st.markdown('<div class="glass-card-gold">', unsafe_allow_html=True)
    st.markdown("### 🎛️ AI CONTROL ROOM — MULTI-AGENT COLLABORATION MATRIX")
    st.markdown("Watch Gemini (Creative Brain) and IBM watsonx.ai (Production Intelligence) negotiate creative solutions under production constraints.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div style="background: rgba(229, 9, 20, 0.1); border: 1px solid rgba(229, 9, 20, 0.3); border-radius: 10px; padding: 14px;">
            <h4 style="color: #F87171; margin:0;">🤖 AGENT 1 — GEMINI / VERTEX AI</h4>
            <p style="font-size: 0.85rem; color: #CBD5E1; margin-top: 4px;">Role: <b>CREATIVE BRAIN</b></p>
            <ul style="font-size: 0.8rem; color: #94A3B8; padding-left: 18px; margin: 0;">
                <li>Story structure & screenplay</li>
                <li>Character DNA & dialogue</li>
                <li>Scene descriptions & visual concepts</li>
                <li>Creative alternatives & scene rewrites</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 10px; padding: 14px;">
            <h4 style="color: #60A5FA; margin:0;">💼 AGENT 2 — IBM watsonx.ai</h4>
            <p style="font-size: 0.85rem; color: #CBD5E1; margin-top: 4px;">Role: <b>PRODUCTION INTELLIGENCE & GUARDRAIL</b></p>
            <ul style="font-size: 0.8rem; color: #94A3B8; padding-left: 18px; margin: 0;">
                <li>Production feasibility & budget drivers</li>
                <li>Script breakdown & resource bottlenecks</li>
                <li>Risk analysis & age rating audit</li>
                <li>Sustainability & Stage Complexity (Theatre)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🔄 Live Agentic Loop Simulation")

    if st.button("⚡ Run Full Co-Director Agentic Audit Loop", type="primary"):
        with st.status("Executing Multi-Agent Co-Director Loop...", expanded=True) as status:
            st.write("🧠 **Step 1: Gemini (Creative Brain)** generates preliminary 34 screenplay scenes and character arcs...")
            time.sleep(0.6)
            st.write("📊 **Step 2: IBM watsonx.ai (Production Intelligence)** audits production metrics: <i>Estimated Cost $68,400 > Target $50,000</i>. Flags 6 high VFX scenes & 3 exterior location costs.")
            time.sleep(0.8)
            st.write("💡 **Step 3: IBM watsonx → Gemini**: '12 locations & 6 VFX sequences create $18,400 budget overrun. Propose creative adaptations.'")
            time.sleep(0.7)
            st.write("🎨 **Step 4: Gemini (Creative Brain)** rewrites Scenes 5 & 11 from space walkway EVA to interior hangar corridor and replaces vapor pyro with LED light pulses.")
            time.sleep(0.8)
            st.write("✅ **Step 5: IBM watsonx** validates revised scenes: Estimated cost decreased to <b>$49,500</b>. Production feasibility status: <b>FEASIBLE</b>.")
            status.update(label="✅ Agentic Loop Complete — Project Optimized!", state="complete")
        st.success("Gemini & IBM watsonx agentic cycle complete! Budget utilization optimized to 99.0% ($49,500 / $50,000).")

    st.markdown("</div>", unsafe_allow_html=True)
