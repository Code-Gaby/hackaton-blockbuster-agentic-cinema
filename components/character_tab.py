import streamlit as st
import plotly.express as px
import pandas as pd
from core.models import Project, Character
from core.translations import get_text
from core.state import add_new_character_to_project, delete_character

def render_character_tab(project: Project):
    """Renders Stage 03 CAST: Cast Workspace with large portrait cards & safe deletion confirmation."""
    lang = st.session_state.get("language", "ES")

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown(f"### {get_text('stage_03', lang)} — WORKSPACE DE REPARTO & ARCOS")
    st.markdown("Gestión integrada de personajes, Radar ADN, evolución por actos y grafo de relaciones.")

    if not project.characters:
        st.info("Este proyecto aún no tiene personajes registrados. Utilice el formulario a continuación o solicite a su Co-Director IA que cree el reparto inicial.")
    else:
        # Cast Board Grid (Large Portrait Cards)
        st.markdown("#### Cartelera de Casting & Reparto Principal")
        cols = st.columns(min(len(project.characters), 4))

        if "selected_char_index" not in st.session_state or st.session_state.selected_char_index >= len(project.characters):
            st.session_state.selected_char_index = 0

        for idx, char in enumerate(project.characters):
            with cols[idx % 4]:
                st.image(char.avatar_url, width=130)
                st.markdown(f"**{char.name}**")
                st.markdown(f"*Rol:* {char.role} | *Arquetipo:* {char.archetype}")
                
                is_sel = idx == st.session_state.selected_char_index
                btn_label = "✓ SELECCIONADO" if is_sel else "VER INSPECTOR"
                if st.button(btn_label, key=f"sel_char_btn_{char.id}"):
                    st.session_state.selected_char_index = idx
                    st.rerun()

        # Active Selected Character Context Inspector
        sel_char: Character = project.characters[st.session_state.selected_char_index]
        st.markdown("---")
        st.markdown(f"### INSPECTOR DE PERSONAJE: {sel_char.name.upper()}")

        c_left, c_right = st.columns([1, 1])

        with c_left:
            st.markdown(f"**Ocupación:** {sel_char.occupation}")
            st.markdown(f"**Personalidad:** {sel_char.personality}")
            st.markdown(f"**Motivación:** {sel_char.motivation}")
            st.markdown(f"**Temores:** {sel_char.fears}")
            st.markdown(f"**Vestuario:** {sel_char.wardrobe}")

            # Safe Character Deletion Workflow
            with st.expander(f"⚠️ Eliminar {sel_char.name} del Reparto", expanded=False):
                st.warning(f"{sel_char.name} participa en escenas y relaciones de la historia. Eliminar este personaje removerá sus referencias del proyecto.")
                if st.button(f"Confirmar Eliminación de {sel_char.name}", key=f"del_confirm_{sel_char.id}"):
                    delete_character(project.id, sel_char.id, sel_char.name)
                    st.session_state.selected_char_index = 0
                    st.success(f"Personaje '{sel_char.name}' eliminado con éxito de la base de datos.")
                    st.rerun()

        with c_right:
            st.markdown("##### Radar ADN del Personaje")
            dna_data = pd.DataFrame(dict(
                r=[sel_char.dna.courage, sel_char.dna.intelligence, sel_char.dna.empathy, sel_char.dna.trust, sel_char.dna.ambition, sel_char.dna.creativity],
                theta=['Valentía', 'Inteligencia', 'Empatía', 'Confianza', 'Ambición', 'Creatividad']
            ))
            fig = px.line_polar(dna_data, r='r', theta='theta', line_close=True)
            fig.update_traces(fill='toself', line_color='#D4AF37')
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#E2E8F0"), height=260, margin=dict(l=20,r=20,t=20,b=20))
            st.plotly_chart(fig, width="stretch")

    # Form to Add New Character directly into SQLite database
    with st.expander("+ Agregar Nuevo Personaje al Proyecto", expanded=False):
        st.markdown("#### Formulario de Incorporación al Reparto")
        f1, f2, f3, f4 = st.columns(4)
        c_name = f1.text_input("Nombre del Personaje", "Maya Lin")
        c_age = f2.number_input("Edad", 18, 90, 32)
        c_role = f3.selectbox("Rol", ["Protagonist", "Antagonist", "Supporting", "Mentor"])
        c_arch = f4.text_input("Arquetipo", "The Innovator")

        f5, f6 = st.columns(2)
        c_occ = f5.text_input("Ocupación", "Especialista en Robótica")
        c_pers = f6.text_input("Personalidad", "Resuelta y perspicaz")

        c_mot = st.text_input("Motivación Principal", "Descubrir el origen de la anomalía")
        c_fear = st.text_input("Temores", "Perder a su equipo de investigación")
        c_ward = st.text_input("Vestuario", "Traje técnico de laboratorio")
        c_props = st.text_input("Objetos/Props (Separados por coma)", "Datapad, Lente de Análisis")

        if st.button("Guardar Personaje en la Base de Datos"):
            add_new_character_to_project(
                project, c_name, c_age, c_role, c_arch, c_occ, c_pers, c_mot, c_fear,
                "Liderazgo, Tenacidad", "Prudencia excesiva", c_ward, c_props
            )
            st.success(f"¡Personaje '{c_name}' insertado en la base de datos del proyecto!")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
