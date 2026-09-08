import streamlit as st
import plotly.graph_objects as go
from core.models import Project
from services.agent_orchestrator import AgentOrchestrator

def render_budget_tab(project: Project):
    """Renders Budget Manager & AI Cost Optimizer with interactive agentic rewrites."""
    orchestrator = AgentOrchestrator()

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 💰 BUDGET ANALYSIS & AI COST OPTIMIZER")

    is_over = project.estimated_budget > project.target_budget
    variance = project.estimated_budget - project.target_budget

    b_col1, b_col2 = st.columns([1, 1])

    with b_col1:
        if is_over:
            st.markdown(f'<div class="glass-card-red"><h4>⚠️ OVER BUDGET: +${variance:,.2f}</h4><p>Estimated Cost: <b>${project.estimated_budget:,.2f}</b> | Target: <b>${project.target_budget:,.2f}</b></p></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="glass-card"><h4>✅ WITHIN BUDGET</h4><p>Estimated Cost: <b>${project.estimated_budget:,.2f}</b> | Budget Remaining: <b>${(project.target_budget - project.estimated_budget):,.2f}</b></p></div>', unsafe_allow_html=True)

        st.markdown("#### Major Cost Drivers Identified by IBM watsonx:")
        for driver in project.budget_drivers:
            st.markdown(f"- **{driver.category}**: +${driver.amount:,.2f} — *{driver.description}*")

    with b_col2:
        # Plotly Donut Chart
        labels = [d.category for d in project.budget_drivers] + ["Base Crew & Gear"]
        amounts = [d.amount for d in project.budget_drivers] + [max(1000.0, project.estimated_budget - sum(d.amount for d in project.budget_drivers))]

        fig = go.Figure(data=[go.Pie(labels=labels, values=amounts, hole=.4, marker=dict(colors=['#E50914', '#D4AF37', '#60A5FA', '#F87171', '#34D399']))])
        fig.update_layout(
            title_text="Estimated Cost Breakdown",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#E2E8F0"),
            height=280,
            margin=dict(l=10, r=10, t=30, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # AI COST OPTIMIZER OPTIONS
    st.markdown('<div class="glass-card-gold">', unsafe_allow_html=True)
    st.markdown("### 💡 AI COST OPTIMIZER OPTIONS — GEMINI & IBM COLLABORATIVE REWRITE")
    st.markdown("Select an optimization strategy below. Gemini will rewrite the affected scenes while preserving narrative continuity, and IBM will re-validate the production budget.")

    for opt in project.budget_options:
        with st.expander(f"📌 {opt.title} — Save ${opt.estimated_savings:,.2f} ({opt.impact_level} Impact)", expanded=True):
            st.markdown(f"**Description:** {opt.description}")
            st.markdown(f"**Affected Scenes:** {opt.affected_scenes}")
            
            if opt.status == "Applied":
                st.markdown('<span class="badge-green">✓ OPTIMIZATION APPLIED</span>', unsafe_allow_html=True)
            else:
                if st.button(f"⚡ Apply Strategy & Trigger Gemini Scene Rewrite", key=f"apply_{opt.id}"):
                    with st.spinner("Gemini rewriting scenes & IBM re-auditing budget..."):
                        res = orchestrator.run_budget_optimization_loop(project, opt)
                        opt.status = "Applied"
                        st.success(res["gemini_rewrite"]["explanation"])
                        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
