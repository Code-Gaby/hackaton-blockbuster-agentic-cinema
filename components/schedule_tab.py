import streamlit as st
import pandas as pd
import plotly.express as px
from core.models import Project

def render_schedule_tab(project: Project):
    """Renders Smart Shooting Schedule & Plotly Gantt timeline."""
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 📅 SMART SHOOTING SCHEDULE & GANTT TIMELINE")
    st.markdown("IBM schedule optimization groups scenes by location, actor availability, and lighting setups to minimize set resets.")

    # Grouped Shooting Days Data
    schedule_data = [
        {"Day": "Day 1-3", "Location": "Observatory Deck", "Scenes": "1, 4, 12", "Actors": "Dr. Elena Vance, Dr. Aris Kaelen", "Time": "Night", "Status": "Scheduled"},
        {"Day": "Day 4-6", "Location": "Sub-Level Power Grid", "Scenes": "2, 8, 18", "Actors": "David Vance, Dr. Elena Vance", "Time": "Night", "Status": "Scheduled"},
        {"Day": "Day 7-9", "Location": "Commander's Quarters", "Scenes": "3, 10, 19", "Actors": "Commander Marcus Thorne, Maya Lin", "Time": "Day", "Status": "Scheduled"},
        {"Day": "Day 10-14", "Location": "Main Hangar Corridor", "Scenes": "5, 11, 20, 24", "Actors": "Dr. Elena Vance, David Vance", "Time": "Day", "Status": "Scheduled"},
        {"Day": "Day 15-18", "Location": "A.R.I.A. Core Chamber", "Scenes": "9, 16, 28", "Actors": "Dr. Elena Vance, A.R.I.A.", "Time": "Night", "Status": "Scheduled"},
        {"Day": "Day 19-24", "Location": "Command Bridge Climax", "Scenes": "30, 31, 32, 33, 34", "Actors": "Full Cast", "Time": "Day/Night", "Status": "Scheduled"}
    ]

    st.dataframe(schedule_data, use_container_width=True)

    # Plotly Timeline Gantt Chart
    gantt_df = pd.DataFrame([
        dict(Task="Observatory Deck Block", Start="2026-09-01", Finish="2026-09-04", Location="Observatory"),
        dict(Task="Sub-Level Grid Block", Start="2026-09-05", Finish="2026-09-08", Location="Power Grid"),
        dict(Task="Commander Quarters Block", Start="2026-09-09", Finish="2026-09-12", Location="Command"),
        dict(Task="Main Hangar Block", Start="2026-09-13", Finish="2026-09-18", Location="Hangar"),
        dict(Task="A.R.I.A. Core Block", Start="2026-09-19", Finish="2026-09-22", Location="AI Core"),
        dict(Task="Climax Command Bridge", Start="2026-09-23", Finish="2026-09-28", Location="Bridge")
    ])

    fig = px.timeline(gantt_df, x_start="Start", x_end="Finish", y="Task", color="Location", title="Production Shooting Timeline")
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#E2E8F0"),
        height=320,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
