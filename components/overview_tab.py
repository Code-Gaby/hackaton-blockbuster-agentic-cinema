import streamlit as st
import plotly.graph_objects as go
from core.models import Project
from core.translations import get_text

def render_overview_tab(project: Project):
    """Renders Stage 01 VISION: Project Hero Dossier, Production Pulse, & 3 Primary Insights."""
    lang = st.session_state.get("language", "ES")

    # Project Hero Poster Dossier
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    c_poster, c_details = st.columns([2, 5])

    with c_poster:
        st.markdown(
            f"""
            <div style="background: linear-gradient(180deg, rgba(229,9,20,0.25) 0%, rgba(10,8,14,0.95) 100%);
                        border: 1px solid rgba(212,175,55,0.4); border-radius: 16px; padding: 28px; text-align: center;">
                <div style="font-family: 'Cinzel', serif; color: #D4AF37; font-size: 0.85rem; letter-spacing: 2px;">CINEMA PRODUCTION DOSSIER</div>
                <h2 style="color: #FFFFFF; font-family: 'Cinzel', serif; font-weight: 900; margin-top: 14px; letter-spacing: 1px;">{project.title.upper()}</h2>
                <p style="color: #D4AF37; font-size: 0.9rem; font-style: italic;">"{project.tagline}"</p>
                <hr style="border: 0.5px solid rgba(212,175,55,0.2); margin: 18px 0;">
                <div style="text-align: left; font-size: 0.85rem; color: #CBD5E1; line-height: 1.8;">
                    <p><b>{get_text('genre', lang)}:</b> {project.genre}</p>
                    <p><b>{get_text('format', lang)}:</b> {project.format}</p>
                    <p><b>Duración:</b> {project.runtime_minutes} mins</p>
                    <p><b>Estado:</b> <span class="badge-gold">{project.status}</span></p>
                    <p><b>Clasificación:</b> <span class="badge-online">{project.age_rating}</span></p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c_details:
        st.markdown(f"# {project.title}")
        st.markdown(f"**{get_text('logline', lang)}:** {project.logline}")
        st.markdown(f"**{get_text('synopsis', lang)}:** {project.synopsis}")
        
        # Production Pulse Progress Timeline
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### PRODUCTION PULSE TIMELINE")
        st.markdown(
            """
            <div style="display: flex; justify-content: space-between; background: rgba(10,8,14,0.9); border: 1px solid rgba(212,175,55,0.2); border-radius: 12px; padding: 14px 20px; font-family: 'Cinzel', serif; font-size: 0.82rem; color: #94A3B8;">
                <span style="color:#4ADE80;">IDEA ✓</span>
                <span style="color:#4ADE80;">STORY ✓</span>
                <span style="color:#4ADE80;">SCRIPT ✓</span>
                <span style="color:#D4AF37; font-weight:700;">BREAKDOWN ●</span>
                <span>VISUALS ○</span>
                <span>PRODUCTION ○</span>
                <span>SHOOT ○</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # 3 Primary Health Cards (Level 1 Summary)
        hs = project.health_scores
        h1, h2, h3 = st.columns(3)
        with h1:
            st.markdown(f'<div class="metric-card"><div class="metric-card-val">{hs.creative_score}%</div><div class="metric-card-lbl">CREATIVE HEALTH</div></div>', unsafe_allow_html=True)
        with h2:
            st.markdown(f'<div class="metric-card"><div class="metric-card-val">${project.estimated_budget/1000:.1f}k / ${project.target_budget/1000:.0f}k</div><div class="metric-card-lbl">BUDGET FEASIBILITY</div></div>', unsafe_allow_html=True)
        with h3:
            st.markdown(f'<div class="metric-card"><div class="metric-card-val">{hs.continuity_score}%</div><div class="metric-card-lbl">CONTINUITY INTEGRITY</div></div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
