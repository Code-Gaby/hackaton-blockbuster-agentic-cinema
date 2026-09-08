import streamlit as st
from core.models import Project

def render_scenes_view(project: Project):
    """Renders Línea de Escenarios matching Agentic Cinema Studio replacement template."""
    
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <div style="font-family: 'Cinzel', serif; font-size: 1.2rem; font-weight: 700; color: #FFF;">
                LÍNEA DE ESCENARIOS & SECUENCIAS
            </div>
            <span class="badge-status">PLAN DE RODAJE</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not project.scenes:
        st.info("No hay escenas registradas en este proyecto. Genere el guion con el Visionary Agent.")
    else:
        # Scenes Grid (repeat(auto-fill, minmax(280px, 1fr)))
        cols = st.columns(3)
        for idx, scene in enumerate(project.scenes):
            with cols[idx % 3]:
                st.markdown(
                    f"""
                    <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 8px; padding: 16px; margin-bottom: 16px; border-left: 3px solid var(--gold-primary);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span class="badge-status" style="font-size: 0.7rem;">ESCENA {scene.scene_number}</span>
                            <span style="font-size: 0.75rem; color: var(--gold-primary); font-weight: 600;">{scene.time_of_day}</span>
                        </div>
                        <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.88rem; font-weight: 700; color: var(--text-main); margin-bottom: 6px;">
                            {scene.slugline}
                        </div>
                        <div style="font-size: 0.8rem; color: var(--text-muted); line-height: 1.4; margin-bottom: 10px;">
                            {scene.summary}
                        </div>
                        <div style="font-size: 0.75rem; color: var(--text-main); border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px;">
                            <b>Reparto:</b> {", ".join(scene.characters)}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
