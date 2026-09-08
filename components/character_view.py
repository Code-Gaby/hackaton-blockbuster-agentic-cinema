import streamlit as st
from core.models import Project, Character
from core.state import add_new_character_to_project, delete_character
from components.cinema_icons import get_svg_icon

def render_character_view(project: Project):
    """Renders Personajes & Casting matching Agentic Cinema Studio replacement template."""
    
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <div style="font-family: 'Cinzel', serif; font-size: 1.2rem; font-weight: 700; color: #FFF;">
                PERSONAJES & CASTING
            </div>
            <span class="badge-status">DNA PSICOLÓGICO</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not project.characters:
        st.info("No hay personajes registrados en esta producción. Inicie una conversación con el Visionary Agent o use el formulario inferior.")
    else:
        # Characters Grid (repeat(auto-fit, minmax(360px, 1fr)))
        cols = st.columns(2)
        for idx, char in enumerate(project.characters):
            with cols[idx % 2]:
                role_color = "var(--gold-primary)" if "protag" in char.role.lower() else ("var(--ruby-accent)" if "antag" in char.role.lower() else "var(--text-muted)")
                
                st.markdown(
                    f"""
                    <div class="character-card">
                        <div class="film-perforations"></div>
                        <div class="character-avatar-mock">
                            {get_svg_icon('theatre_masks', 32, 'var(--gold-primary)')}
                        </div>
                        <div style="flex: 1;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div style="font-family: 'Cinzel', serif; font-size: 1.1rem; font-weight: 700; color: var(--text-main);">{char.name}</div>
                                <span style="font-size: 0.75rem; font-weight: bold; color: {role_color}; text-transform: uppercase;">{char.role}</span>
                            </div>
                            <div style="font-size: 0.78rem; color: var(--gold-primary); margin-top: 2px;">{char.archetype} • {char.occupation}</div>
                            <div style="font-size: 0.82rem; color: var(--text-muted); margin-top: 8px; line-height: 1.4;">
                                <b>Objetivo:</b> {char.motivation}
                            </div>
                            <div style="font-size: 0.8rem; color: var(--text-main); margin-top: 6px;">
                                <b>Psicología:</b> {char.personality}
                            </div>
                            <div style="display: flex; gap: 8px; margin-top: 10px;">
                                <span style="background: rgba(212,175,55,0.1); border: 1px solid var(--border-subtle); padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; color: var(--gold-glow);">Valor: {char.dna.courage}/10</span>
                                <span style="background: rgba(212,175,55,0.1); border: 1px solid var(--border-subtle); padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; color: var(--gold-glow);">Astucia: {char.dna.intelligence}/10</span>
                                <span style="background: rgba(212,175,55,0.1); border: 1px solid var(--border-subtle); padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; color: var(--gold-glow);">Resiliencia: {char.dna.resilience}/10</span>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if st.button(f"Eliminar a {char.name}", key=f"del_c_{char.id}"):
                    delete_character(project.id, char.id, char.name)
                    st.success(f"Personaje '{char.name}' eliminado.")
                    st.rerun()

    # Form to add character
    st.markdown("---")
    with st.expander("+ Agregar Nuevo Personaje al Reparto", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c_name = c1.text_input("Nombre", "Dra. Elena Vance")
        c_age = c2.number_input("Edad", 18, 90, 34)
        c_role = c3.selectbox("Rol", ["Protagonista", "Antagonista", "Secundario", "Mentor"])
        c_arch = c4.text_input("Arquetipo", "The Visionary")
        
        c_mot = st.text_input("Motivación", "Proteger el descubrimiento cuántico y su equipo")
        c_pers = st.text_input("Personalidad & Rasgos", "Brillante, analítica, implacable")
        c_props = st.text_input("Props / Objetos Clave", "Grabadora analógica de 1990, Linterna UV")
        
        if st.button("Guardar Personaje en Reparto", type="primary"):
            add_new_character_to_project(
                project, c_name, c_age, c_role, c_arch, "Científica Principal",
                c_pers, c_mot, "La desintegración del portal", "Liderazgo, Inteligencia", "Obsesión por la verdad",
                "Chaqueta de cuero roja", c_props
            )
            st.success(f"¡{c_name} añadido al reparto!")
            st.rerun()
