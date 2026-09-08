import streamlit as st
from core.state import get_all_projects, get_current_project
from core.db import get_connection
from components.cinema_icons import get_svg_icon

def render_library_view():
    """Renders Biblioteca de Proyectos matching Agentic Cinema Studio replacement template."""
    all_projects = get_all_projects()
    active_project = get_current_project()

    # Controls Bar: Search & "Crear Nuevo Proyecto" Button
    c_search, c_create = st.columns([8, 4])

    with c_search:
        search_query = st.text_input(
            "Buscar",
            placeholder="Buscar por título o género...",
            label_visibility="collapsed",
            key="lib_search_input"
        )

    with c_create:
        if st.button("✦ CREAR NUEVO PROYECTO", key="btn_create_project_main", type="primary", use_container_width=True):
            # Immediately switch to Visionary Agent Chat
            st.session_state.active_nav = "view-chat"
            st.session_state.chat_prefill = "Genera una nueva historia de cine sobre "
            st.rerun()

    # Filter projects
    filtered_projects = all_projects
    if search_query:
        filtered_projects = [
            p for p in all_projects
            if search_query.lower() in p['title'].lower() or search_query.lower() in p.get('genre', '').lower()
        ]

    st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)

    # Project Cards Grid (repeat(auto-fill, minmax(290px, 1fr)))
    cols = st.columns(3)

    for idx, p in enumerate(filtered_projects):
        with cols[idx % 3]:
            is_active = p['id'] == active_project.id
            border_glow = "var(--gold-primary)" if is_active else "var(--border-subtle)"
            status_text = p.get('status', 'Pre-Production').upper()

            st.markdown(
                f"""
                <div class="project-card" style="border-color: {border_glow};">
                    <div class="card-banner">
                        <div class="card-banner-decor">35MM MASTER REEL</div>
                    </div>
                    <div class="card-body">
                        <div class="card-title">{p['title']}</div>
                        <div class="card-meta">
                            <span>Formato: <b>{p.get('format', 'FILM')}</b></span>
                            <span class="badge-status">{status_text}</span>
                        </div>
                        <div style="font-size: 0.8rem; color: var(--text-muted); line-height: 1.4;">
                            {p.get('logline', 'Producción cinematográfica de estudio.')[:90]}...
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            c_act1, c_act2, c_act3 = st.columns([5, 3, 3])
            with c_act1:
                if st.button("→ Abrir / Chat", key=f"open_proj_{p['id']}", use_container_width=True):
                    st.session_state.active_project_id = p['id']
                    st.session_state.active_nav = "view-chat"
                    st.rerun()
            with c_act2:
                if st.button("Archivar", key=f"arch_proj_{p['id']}", use_container_width=True):
                    st.info(f"Proyecto '{p['title']}' archivado.")
            with c_act3:
                if st.button("Eliminar", key=f"del_proj_btn_{p['id']}", use_container_width=True):
                    conn = get_connection()
                    conn.execute("DELETE FROM projects WHERE id = ?", (p['id'],))
                    conn.commit()
                    conn.close()
                    st.success("Proyecto eliminado.")
                    st.rerun()
