import streamlit as st
from core.models import Project

def render_history_tab(project: Project):
    """Renders Cinematic Production Timeline of past events and agentic cycles."""
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 🎞️ CINEMATIC PRODUCTION HISTORY TIMELINE")
    st.markdown("Auditable chronological record of creative story updates, script breakdowns, budget optimizations, and continuity fixes.")

    for log in reversed(project.history_logs):
        agent_badge = '<span class="badge-red">GEMINI</span>' if "Gemini" in log['agent'] else ('<span class="badge-gold">IBM watsonx</span>' if "IBM" in log['agent'] else '<span class="badge-green">DIRECTOR</span>')
        st.markdown(
            f"""
            <div style="background: rgba(22, 22, 30, 0.8); border-left: 4px solid #D4AF37; border-radius: 8px; padding: 14px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between;">
                    <strong style="color: #FFFFFF; font-size: 1.05rem;">{log['event']}</strong>
                    <span style="color: #94A3B8; font-size: 0.82rem;">{log['timestamp']}</span>
                </div>
                <div style="margin-top: 4px;">
                    Agent: {agent_badge}
                </div>
                <p style="color: #CBD5E1; font-size: 0.88rem; margin-top: 6px; margin-bottom: 0;">{log['details']}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)
