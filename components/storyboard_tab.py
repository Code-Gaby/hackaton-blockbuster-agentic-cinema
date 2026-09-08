import streamlit as st
from core.models import Project, Scene

def render_storyboard_tab(project: Project):
    """Renders Storyboard Shot Generator & Camera Angles."""
    lang = st.session_state.get("language", "ES")

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### STORYBOARD Y GENERADOR DE PLANOS CINEMATOGRÁFICOS")
    st.markdown("Visualización shot-by-shot con sugerencias de ángulos de cámara, lentes, encuadres e iluminación dramática.")

    scene_options = [f"Escena {s.scene_number}: {s.location}" for s in project.scenes]
    sel_idx = st.selectbox("Seleccionar Escena para Storyboard", range(len(scene_options)), format_func=lambda i: scene_options[i])
    scene: Scene = project.scenes[sel_idx]

    st.markdown(f"#### Planos Sugeridos: Escena {scene.scene_number} — {scene.location}")

    shots = [
        {"shot": "Plano 1: Establecimiento Wide Shot", "angle": "Plano General Gran Angular (24mm)", "lighting": "Luz fría volumétrica de fondo con contraluz dorado", "action": f"Vista amplia de {scene.location}. La silueta de los personajes destaca contra los monitores."},
        {"shot": "Plano 2: Primer Plano Medio (Medium Close-Up)", "angle": "Ángulo Contrapicado Picado leve (50mm)", "lighting": "Luz clave cenital sobre los ojos del personaje", "action": f"Reacción dramática durante la confrontación. Foco crítico en la mirada."},
        {"shot": "Plano 3: Plano Detalle de Prop (Insert Shot)", "angle": "Macro (85mm focal fija)", "lighting": "Chispa lumínica puntual", "action": f"Enfoque táctil en el objeto clave ({scene.props[0] if scene.props else 'Dispositivo'})."}
    ]

    s1, s2, s3 = st.columns(3)
    cols = [s1, s2, s3]
    for idx, sh in enumerate(shots):
        with cols[idx]:
            st.markdown(f"""
            <div style="background: rgba(14,12,20,0.85); border: 1px solid rgba(212,175,55,0.25); border-radius: 12px; padding: 18px;">
                <div style="height: 120px; background: linear-gradient(135deg, #2A080C 0%, #100C16 100%); border-radius: 8px; display: flex; align-items: center; justify-content: center; border: 1px dashed rgba(212,175,55,0.3); margin-bottom: 12px;">
                    <span style="color: #D4AF37; font-family: 'Cinzel', serif; font-size: 0.9rem; letter-spacing: 1px;">KEYFRAME BOARD #{idx+1}</span>
                </div>
                <h5 style="color: #F87171; margin: 0 0 6px 0;">{sh['shot']}</h5>
                <p style="font-size: 0.8rem; color: #CBD5E1; margin-bottom: 4px;"><b>Cámara:</b> {sh['angle']}</p>
                <p style="font-size: 0.8rem; color: #CBD5E1; margin-bottom: 4px;"><b>Iluminación:</b> {sh['lighting']}</p>
                <p style="font-size: 0.8rem; color: #94A3B8;"><b>Acción:</b> {sh['action']}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
