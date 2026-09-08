import streamlit as st
import pandas as pd
import plotly.express as px
from core.models import Project
from core.translations import get_text
from services.ibm_service import IBMProductionProvider
from services.agent_orchestrator import AgentOrchestrator

def render_production_tab(project: Project):
    """Renders Stage 06 PRODUCTION: Stripboard Schedule, Production Ledger, Theatre Mode Stage Complexity, & Eco Impact."""
    lang = st.session_state.get("language", "ES")
    ibm = IBMProductionProvider()
    orchestrator = AgentOrchestrator()

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown(f"### {get_text('stage_06', lang)} — WORKSPACE DE PRODUCCIÓN & RODAJE")
    st.markdown("Gestión integrada del plan de rodaje, presupuesto por departamentos, complejidad escénica y logística verde.")

    # Sub-Navigation Tabs inside Production Workspace
    p_tab1, p_tab2, p_tab3, p_tab4 = st.tabs([
        "💰 LIBRO DE PRESUPUESTO",
        "📅 PLAN DE RODAJE (STRIPBOARD)",
        "🎭 MODO TEATRO & MONTAJE",
        "🌱 IMPACTO ECOLÓGICO"
    ])

    with p_tab1:
        st.markdown("#### Presupuesto y Optimización de Costos")
        is_over = project.estimated_budget > project.target_budget
        variance = project.estimated_budget - project.target_budget

        if is_over:
            st.markdown(f'<div class="glass-card-red"><h4>⚠️ SOBRE PRESUPUESTO: +${variance:,.2f}</h4><p>Costo Estimado: <b>${project.estimated_budget:,.2f}</b> | Presupuesto Objetivo: <b>${project.target_budget:,.2f}</b></p></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="glass-card"><h4>✅ PRESUPUESTO DENTRO DEL LÍMITE</h4><p>Costo Estimado: <b>${project.estimated_budget:,.2f}</b> | Margen Restante: <b>${(project.target_budget - project.estimated_budget):,.2f}</b></p></div>', unsafe_allow_html=True)

        st.markdown("##### Estrategias de Optimización de Costos por Agentes AI")
        for opt in project.budget_options:
            with st.expander(f"📌 {opt.title} — Ahorro Est. ${opt.estimated_savings:,.2f}", expanded=True):
                st.markdown(f"**Descripción:** {opt.description}")
                st.markdown(f"**Escenas Afectadas:** {opt.affected_scenes}")
                if opt.status == "Applied":
                    st.markdown('<span class="badge-online">✓ ESTRATEGIA APLICADA</span>', unsafe_allow_html=True)
                else:
                    if st.button(f"⚡ Aplicar Estrategia con Gemini", key=f"prod_opt_{opt.id}"):
                        res = orchestrator.run_budget_optimization_loop(project, opt)
                        opt.status = "Applied"
                        st.success(res["gemini_rewrite"]["explanation"])
                        st.rerun()

    with p_tab2:
        st.markdown("#### Plan de Rodaje Optimizado por Días")
        gantt_df = pd.DataFrame([
            dict(Task="Bloque Observatorio", Start="2026-09-01", Finish="2026-09-04", Location="Observatorio"),
            dict(Task="Bloque Red de Energía", Start="2026-09-05", Finish="2026-09-08", Location="Energía"),
            dict(Task="Bloque Comando", Start="2026-09-09", Finish="2026-09-12", Location="Comando"),
            dict(Task="Bloque Hangar Principal", Start="2026-09-13", Finish="2026-09-18", Location="Hangar"),
            dict(Task="Bloque Núcleo A.R.I.A.", Start="2026-09-19", Finish="2026-09-22", Location="Núcleo"),
            dict(Task="Puente Clímax", Start="2026-09-23", Finish="2026-09-28", Location="Puente")
        ])
        fig = px.timeline(gantt_df, x_start="Start", x_end="Finish", y="Task", color="Location", title="Cronograma de Rodaje")
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#E2E8F0"), height=300)
        st.plotly_chart(fig, width="stretch")

    with p_tab3:
        if project.format == "THEATRE":
            st.markdown("#### Auditoría de Montaje y Tramoya Escénica")
            sample_scene = project.scenes[3]
            stage_audit = ibm.calculate_stage_complexity(sample_scene)

            t1, t2, t3 = st.columns(3)
            t1.metric("Complejidad Escénica", f"{stage_audit['complexity_score']}%", stage_audit['rating'])
            t2.metric("Actores en Escena", stage_audit['actors_on_stage'])
            t3.metric("Tiempo de Transición Est.", f"{stage_audit['estimated_transition_seconds']}s")

            for reason in stage_audit['reasons']:
                st.markdown(f"- ⏱️ {reason}")
        else:
            st.info("El análisis de Modo Teatro se activa automáticamente al seleccionar el formato THEATRE en el encabezado.")

    with p_tab4:
        st.markdown("#### Sustentabilidad e Impacto Ecológico")
        eco_data = ibm.analyze_sustainability(project)
        st.metric("Puntaje Eco de Producción", f"{eco_data['eco_score']} / 100", eco_data['label'])
        for rec in eco_data['recommendations']:
            st.markdown(f"- 🌱 {rec}")

    st.markdown("</div>", unsafe_allow_html=True)
