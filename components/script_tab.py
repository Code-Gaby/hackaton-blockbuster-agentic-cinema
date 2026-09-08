import streamlit as st
from core.models import Project, Scene
from core.translations import get_text
from services.continuity_engine import ContinuityEngine

def render_script_tab(project: Project):
    """Renders Stage 04 SCENES: Contact-Strip Scene Reel & 3-Pane Screenplay Layout."""
    lang = st.session_state.get("language", "ES")
    continuity_engine = ContinuityEngine()

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown(f"### {get_text('stage_04', lang)} — SCENE & SCREENPLAY WORKSPACE")
    st.markdown("Reel horizontal de escenas, lector de guion técnico e inspector de producción desglosado.")

    if not project.scenes:
        st.info("Este proyecto aún no tiene escenas registradas. Inicie la creación de escenas con su Co-Director IA.")
    else:
        # Horizontal Contact-Strip Scene Reel
        st.markdown("#### Carrete de Escenas (Contact-Strip Scene Reel)")
        scene_nums = [s.scene_number for s in project.scenes]
        
        if "active_scene_num" not in st.session_state or st.session_state.active_scene_num not in scene_nums:
            st.session_state.active_scene_num = scene_nums[0]

        # Horizontal Scroll Buttons for Scene Selector
        reel_cols = st.columns(min(len(project.scenes), 8))
        for idx, s_num in enumerate(scene_nums[:8]):
            with reel_cols[idx]:
                is_act = s_num == st.session_state.active_scene_num
                btn_type = "✓ SCENE " + str(s_num) if is_act else "SCENE " + str(s_num)
                if st.button(btn_type, key=f"reel_btn_{s_num}"):
                    st.session_state.active_scene_num = s_num
                    st.rerun()

        active_scene: Scene = next((s for s in project.scenes if s.scene_number == st.session_state.active_scene_num), project.scenes[0])

        st.markdown("---")
        
        # 3-Pane Layout: Screenplay Text (Center/Left) & Production Inspector (Right)
        col_script, col_inspector = st.columns([7, 5])

        with col_script:
            st.markdown(f"### {active_scene.slugline}")
            st.markdown(f"*Resumen:* {active_scene.summary}")
            
            # Contextual Annotation Indicators
            st.markdown('<div style="margin-bottom: 10px;"><span class="badge-gold">● VFX DETECTADO</span> &nbsp; <span class="badge-online">● STUNT</span> &nbsp; <span class="badge-gold">● PROPS</span></div>', unsafe_allow_html=True)
            
            st.markdown(f'<div class="screenplay-box">{active_scene.script_text}</div>', unsafe_allow_html=True)

        with col_inspector:
            st.markdown(f"### INSPECTOR DE PRODUCCIÓN")
            st.markdown(f"**Escena N°:** {active_scene.scene_number}")
            st.markdown(f"**Ubicación:** {active_scene.location} ({active_scene.interior_exterior} / {active_scene.day_night})")
            st.markdown(f"**Complejidad:** {active_scene.complexity} | **Puntaje de Riesgo:** {active_scene.risk_score}/100")
            st.markdown(f"**Costo Estimado de Rodaje:** ${active_scene.estimated_cost:,.2f}")

            st.markdown("##### Personajes en Escena:")
            for char_name in active_scene.characters:
                st.markdown(f"- 👤 {char_name}")

            st.markdown("##### Desglose Técnico:")
            st.markdown(f"- **VFX:** {', '.join(active_scene.vfx) if active_scene.vfx else 'Ninguno'}")
            st.markdown(f"- **Props:** {', '.join(active_scene.props) if active_scene.props else 'Ninguno'}")
            st.markdown(f"- **SFX:** {', '.join(active_scene.sfx) if active_scene.sfx else 'Ninguno'}")

            # Continuity Audit for Active Scene
            c_facts = continuity_engine.scan_scene_continuity(project, active_scene)
            if c_facts:
                st.markdown("##### Alertas de Continuidad Detectadas:")
                for fact in c_facts:
                    st.markdown(f'<div class="glass-card-red">⚠️ <b>{fact.issue_type}:</b> {fact.description}<br/><i>Sugerencia:</i> {fact.suggested_fix}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="glass-card">✓ Continuidad verificada sin conflictos para esta escena.</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
