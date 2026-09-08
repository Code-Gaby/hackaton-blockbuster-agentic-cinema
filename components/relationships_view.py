import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network
from core.models import Project
from core.db import get_relationships_by_project_db

def render_relationships_view(project: Project):
    """Renders Red de Relaciones Narrativas matching Agentic Cinema Studio replacement template."""
    
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <div style="font-family: 'Cinzel', serif; font-size: 1.2rem; font-weight: 700; color: #FFF;">
                RED DE RELACIONES NARRATIVAS
            </div>
            <span class="badge-status">GRAFO RELACIONAL</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    rels_db = get_relationships_by_project_db(project.id)

    # Pyvis interactive graph matching dark luxury palette
    net = Network(height="340px", width="100%", bgcolor="#10131c", font_color="#f3f4f6")
    net.force_atlas_2based()

    for char in project.characters:
        color = "#d4af37" if "protag" in char.role.lower() else ("#e50914" if "antag" in char.role.lower() else "#9ca3af")
        shape = "dot"
        net.add_node(char.name, label=f"{char.name}\n({char.role})", color=color, shape=shape, size=24)

    for r in rels_db:
        edge_color = "#e50914" if "CONFLICT" in r['rel_type'] else ("#d4af37" if "ALLIANCE" in r['rel_type'] else "#9ca3af")
        target_name = r.get('target_character_name', 'Personaje')
        source_name = next((c.name for c in project.characters if c.id == r['source_character_id']), 'Elena Vance')
        net.add_edge(source_name, target_name, title=r['history'], color=edge_color, width=2.5)

    try:
        html_code = net.generate_html()
        components.html(html_code, height=350)
    except Exception:
        st.info("Grafo relacional activo.")

    # Relationship Cards matching replacement template (.relation-link, .relation-tag)
    st.markdown("#### Desglose de Dinámicas y Conflictos")
    for r in rels_db:
        is_enemy = "CONFLICT" in r['rel_type']
        tag_class = "enemy" if is_enemy else "ally"
        tag_label = "CONFLICTO / TENSIÓN" if is_enemy else "ALIANZA / MENTORÍA"
        
        target_name = r.get('target_character_name', 'Personaje')
        source_name = next((c.name for c in project.characters if c.id == r['source_character_id']), 'Elena Vance')

        st.markdown(
            f"""
            <div class="relation-link">
                <div>
                    <strong style="color: var(--text-main); font-size: 0.95rem;">{source_name} ↔ {target_name}</strong>
                    <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 4px;">{r['history']}</div>
                </div>
                <span class="relation-tag {tag_class}">{tag_label}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
