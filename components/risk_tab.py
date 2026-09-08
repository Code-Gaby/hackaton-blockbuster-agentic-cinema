import streamlit as st
from core.models import Project
from services.ibm_service import IBMProductionProvider

def render_risk_tab(project: Project):
    """Renders Scene Risk Analysis Matrix & Age Rating / Content Advisory."""
    ibm = IBMProductionProvider()

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### ⚠️ SCENE RISK MATRIX & CONTENT ADVISORY AUDIT")

    r1, r2 = st.columns([1, 1])

    with r1:
        st.markdown("#### 🎬 Scene Risk Breakdown")
        high_risk = [s for s in project.scenes if s.risk_score >= 60]
        st.markdown(f"**High-Risk Scenes ({len(high_risk)} total):**")
        for s in high_risk[:5]:
            st.markdown(f"- **Scene {s.scene_number} ({s.location})**: Risk Score `{s.risk_score}%` — *Stunts: {', '.join(s.stunts) if s.stunts else 'High VFX'}*")
        
        st.markdown("""
        **Risk Evaluation Factors:**
        * Stunt & Zero-g tethered wirework
        * High voltage plasma spark ignitions
        * Overtime night observatory shoots
        """)

    with r2:
        st.markdown("#### 🔞 Preliminary Age Rating & Content Advisory")
        rating_data = ibm.analyze_age_rating(project)
        
        st.markdown(f"**Suggested Rating:** <span class='badge-gold'>{rating_data['suggested_rating']}</span> &nbsp; (Confidence: {rating_data['confidence_score']}%)", unsafe_allow_html=True)
        st.caption(rating_data['summary'])

        st.markdown("**Content Intensity Factors:**")
        for factor in rating_data['risk_factors']:
            c = "badge-yellow" if factor['intensity'] == "MODERATE" else ("badge-green" if factor['intensity'] == "MILD" or factor['intensity'] == "NONE" else "badge-red")
            st.markdown(f"- **{factor['category']}**: <span class='{c}'>{factor['intensity']}</span> — *{factor['notes']}*", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
