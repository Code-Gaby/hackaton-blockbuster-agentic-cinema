import streamlit as st
from components.cinema_icons import get_svg_icon
from core.models import Project

def render_sidebar_navigation(project: Project) -> str:
    """Renders the Left Sidebar Navigation matching Agentic Cinema Studio specifications."""
    
    # Default view on load is Biblioteca (view-library)
    if "active_nav" not in st.session_state:
        st.session_state.active_nav = "view-library"

    active = st.session_state.active_nav

    with st.sidebar:
        # Brand Header matching replacement HTML
        st.markdown(
            f"""
            <div class="brand-wrap">
                <div class="brand-icon">
                    {get_svg_icon('brand', 22, '#FFFFFF')}
                </div>
                <div class="brand-text">
                    <h1>AGENTIC</h1>
                    <span>Cinema Studio</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        nav_items = [
            {"id": "view-library", "label": "Biblioteca", "icon": "projects"},
            {"id": "view-chat", "label": "Visionary Agent", "icon": "chat"},
            {"id": "view-characters", "label": "Personajes", "icon": "theatre_masks"},
            {"id": "view-relations", "label": "Red de Reparto", "icon": "relations"},
            {"id": "view-scenes", "label": "Escenarios", "icon": "scenes"},
            {"id": "view-summary", "label": "Resumen de Producción", "icon": "summary"}
        ]

        for item in nav_items:
            is_active = active == item["id"]
            active_class = "active" if is_active else ""
            icon_color = "var(--gold-primary)" if is_active else "currentColor"
            icon_html = get_svg_icon(item["icon"], 20, icon_color)

            # Render button with vector SVG and active state
            if st.button(
                f"{item['label']}",
                key=f"nav_btn_{item['id']}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.active_nav = item["id"]
                st.rerun()

        # Studio Info Badge
        st.markdown(
            f"""
            <div style="margin-top: 30px; padding: 12px 14px; background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: 8px;">
                <div style="font-size: 0.7rem; color: var(--gold-primary); text-transform: uppercase; font-weight: 700; letter-spacing: 1px;">PRODUCCIÓN ACTIVA</div>
                <div style="font-weight: 700; color: var(--text-main); font-size: 0.9rem; margin-top: 2px;">{project.title}</div>
                <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 4px;">Formato: <b>{project.format}</b> • {project.progress_percentage}%</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    return st.session_state.active_nav
