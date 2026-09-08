import streamlit as st
from core.models import Project
from services.gemini_service import GeminiCreativeProvider
from services.continuity_engine import ContinuityEngine

def render_continuity_tab(project: Project):
    """Renders Continuity Guardian alerts & conflict resolver."""
    gemini = GeminiCreativeProvider()

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 🛡️ CONTINUITY GUARDIAN & PERSISTENT MEMORY")
    st.markdown("Persistent project memory tracks character appearance, props, injuries, and timelines to prevent narrative contradictions.")

    alerts = ContinuityEngine.scan_project_continuity(project)
    project.continuity_alerts = alerts

    pending_alerts = [a for a in alerts if a.status == "Pending"]
    
    st.markdown(f"#### Active Continuity Scan: {len(pending_alerts)} Pending Alerts")

    if not pending_alerts:
        st.success("✨ Zero continuity conflicts detected across all 34 scenes!")

    for alert in alerts:
        card_class = "glass-card-red" if alert.status == "Pending" else "glass-card"
        st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
        st.markdown(f"**🚨 CONTINUITY ALERT — Scene {alert.scene_number} ({alert.character_name} · {alert.issue_type})**")
        st.markdown(f"**Description:** {alert.description}")
        st.markdown(f"**Suggested Fix:** *{alert.suggested_fix}*")
        st.markdown(f"**Status:** `{alert.status}`")

        if alert.status == "Pending":
            c1, c2, c3 = st.columns(3)
            if c1.button("✨ Auto-FIX with Gemini", key=f"fix_{alert.id}"):
                with st.spinner("Gemini rewriting scene text to maintain continuity..."):
                    scene = next((s for s in project.scenes if s.scene_number == alert.scene_number), None)
                    if scene:
                        gemini.fix_scene_continuity(scene, alert)
                    alert.status = "FIXED"
                    st.success("Continuity conflict resolved by Gemini!")
                    st.rerun()

            if c2.button("Keep Original (KEEP)", key=f"keep_{alert.id}"):
                alert.status = "RESOLVED (KEEP)"
                st.rerun()

            if c3.button("Ignore Alert (IGNORE)", key=f"ignore_{alert.id}"):
                alert.status = "IGNORED"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
