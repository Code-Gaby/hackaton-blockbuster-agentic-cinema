import streamlit as st
from core.models import Project
from services.ibm_service import IBMProductionProvider

def render_sustainability_tab(project: Project):
    """Renders Eco Production Impact Score & Green Filming recommendations."""
    ibm = IBMProductionProvider()

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 🌱 PRODUCTION SUSTAINABILITY & ECO AUDIT")

    eco_data = ibm.analyze_sustainability(project)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(
            f"""
            <div style="background: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34, 197, 94, 0.4); border-radius: 12px; padding: 24px; text-align: center;">
                <div style="font-size: 3rem;">🌱</div>
                <h2 style="color: #4ADE80; margin: 8px 0;">{eco_data['eco_score']} / 100</h2>
                <h5 style="color: #FFFFFF;">{eco_data['label']}</h5>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown("#### Carbon Footprint Breakdown")
        for item in eco_data['carbon_breakdown']:
            st.markdown(f"**{item['category']} ({item['percentage']}%)**: `{item['score']}` — *{item['detail']}*")
            st.progress(item['percentage'] / 100.0)

    st.markdown("#### 💡 IBM Green Filming Recommendations")
    for rec in eco_data['recommendations']:
        st.markdown(f"- 🌱 {rec}")

    st.markdown("</div>", unsafe_allow_html=True)
