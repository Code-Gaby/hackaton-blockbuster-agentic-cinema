import streamlit as st
import plotly.express as px
import pandas as pd
from core.models import Project

def render_summary_view(project: Project):
    """Renders Resumen Global de Producción (IBM Watsonx Analytics) matching replacement template."""
    
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <div style="font-family: 'Cinzel', serif; font-size: 1.2rem; font-weight: 700; color: #FFF;">
                RESUMEN GLOBAL DE PRODUCCIÓN & ANALYTICS
            </div>
            <span class="badge-status">IBM WATSONX ENGINE</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    c_left, c_right = st.columns([6, 6])

    with c_left:
        st.markdown(
            f"""
            <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: 12px; padding: 22px; margin-bottom: 16px;">
                <div style="font-size: 0.75rem; color: var(--gold-primary); font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">Logline Oficial</div>
                <div style="color: var(--text-main); font-size: 0.95rem; line-height: 1.5; margin-top: 6px;">{project.logline}</div>

                <div style="font-size: 0.75rem; color: var(--gold-primary); font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-top: 14px;">Premisa & Sinopsis</div>
                <div style="color: var(--text-muted); font-size: 0.85rem; line-height: 1.5; margin-top: 4px;">{project.synopsis}</div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                <div style="background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: 8px; padding: 14px;">
                    <div style="font-size: 0.75rem; color: var(--text-muted);">Presupuesto Estimado</div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: var(--gold-primary); margin-top: 4px;">${project.estimated_budget:,.2f}</div>
                </div>
                <div style="background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: 8px; padding: 14px;">
                    <div style="font-size: 0.75rem; color: var(--text-muted);">Días de Rodaje</div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: var(--text-main); margin-top: 4px;">{project.shooting_days} Días</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c_right:
        st.markdown("##### Curva de Tensión Dramática & Ritmo")
        tension_df = pd.DataFrame({
            "Minuto": [0, 15, 30, 45, 60, 75, 90, 105, 120],
            "Tensión": [20, 35, 55, 45, 75, 88, 98, 40, 20]
        })

        fig = px.line(tension_df, x="Minuto", y="Tensión", line_shape="spline", markers=True)
        fig.update_traces(line_color="#e50914", line_width=3, marker=dict(size=7, color="#d4af37"))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#f3f4f6"),
            height=260,
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis=dict(gridcolor="rgba(212,175,55,0.1)"),
            yaxis=dict(gridcolor="rgba(212,175,55,0.1)")
        )
        st.plotly_chart(fig, use_container_width=True)
