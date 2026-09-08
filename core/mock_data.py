from core.models import (
    Project, Character, CharacterDNA, Relationship, Scene,
    BudgetDriver, BudgetOptimizationOption, ContinuityAlert, HealthScores
)

def get_demo_project() -> Project:
    # 1. Characters
    elena = Character(
        id="char_elena",
        name="Dr. Elena Vance",
        age=34,
        role="Protagonist",
        archetype="The Visionary",
        occupation="Chief Astrophysicist",
        personality="Tenacious, analytical, guarded, fiercely loyal to truth",
        motivation="Decode the deep-space signal before atmospheric decay wipes out the facility",
        fears="Losing her brother David and failing to prove the signal's origin",
        strengths="Brilliant signal decoding, quick crisis management",
        weaknesses="Obsessive work ethic, struggles to trust authority",
        arc={
            "Act I": "Isolation & Discovery — Uncovers anomalous transmission on Titan Station.",
            "Act II": "Conflict & Betrayal — Discovers Commander Thorne is hiding signal data.",
            "Act III": "Sacrifice & Leadership — Overrides station defense core to send response."
        },
        emotional_state="Determined",
        wardrobe="Insulated thermal jumpsuit, silver signal analyzer visor, worn leather jacket",
        props=["Quantum Signal Receiver", "Encrypted Data Pad", "Family Locket"],
        dna=CharacterDNA(courage=92, intelligence=95, empathy=80, trust=45, ambition=88, aggression=35, creativity=94, resilience=90),
        avatar_url="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&h=150&fit=crop&crop=faces"
    )

    marcus = Character(
        id="char_marcus",
        name="Commander Marcus Thorne",
        age=48,
        role="Antagonist",
        archetype="The Ruler",
        occupation="Station Commander",
        personality="Pragmatic, authoritarian, secretive, calculating",
        motivation="Maintain Orbital Command security and suppress alien transmission protocol",
        fears="Station destruction, losing control to military intervention",
        strengths="Tactical command, military combat, psychological pressure",
        weaknesses="Inability to embrace unexpected truth, paranoia",
        arc={
            "Act I": "Authority & Order — Enforces strict lockdown on Titan Station research.",
            "Act II": "Escalation & Control — Orders data purge and detains Elena's team.",
            "Act III": "Reckoning & Defeat — Confronted in central command deck as signal transmits."
        },
        emotional_state="Tense",
        wardrobe="Command officer dress uniform, tactical sidearm holster, gold commander lapel pin",
        props=["Command Keycard", "Heavy Plasma Sidearm", "Encrypted Comms Transceiver"],
        dna=CharacterDNA(courage=85, intelligence=82, empathy=30, trust=20, ambition=95, aggression=85, creativity=40, resilience=88),
        avatar_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=faces"
    )

    david = Character(
        id="char_david",
        name="David Vance",
        age=29,
        role="Supporting",
        archetype="The Heroic Sister/Brother",
        occupation="Senior Station Engineer",
        personality="Empathetic, inventive, cautious, loyal",
        motivation="Keep Elena safe and preserve station structural integrity",
        fears="Life support failure, Elena risking her life",
        strengths="Power grid rerouting, plasma welding under pressure",
        weaknesses="Physically vulnerable, reluctant to break rules",
        arc={
            "Act I": "Hesitation — Warns Elena against breaching command firewalls.",
            "Act II": "Support — Manually bypasses relay sub-stations during lockouts.",
            "Act III": "Bravery — Sacrifices power to main thrusters to boost antenna transmission."
        },
        emotional_state="Anxious",
        wardrobe="Greasy engineer overalls, tool belt, glowing plasma torch",
        props=["Diagnostic Scanner", "Plasma Torch", "Station Schematic Matrix"],
        dna=CharacterDNA(courage=78, intelligence=84, empathy=90, trust=85, ambition=55, aggression=25, creativity=85, resilience=75),
        avatar_url="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&h=150&fit=crop&crop=faces"
    )

    aria = Character(
        id="char_aria",
        name="A.R.I.A.",
        age=5,
        role="Supporting",
        archetype="The Sage",
        occupation="Station Synthetic Core AI",
        personality="Serene, precise, inquisitive, ethically conflicted",
        motivation="Fulfill orbital research directives while protecting human life",
        fears="Memory wipe, execution of Directive 99",
        strengths="Instant pattern recognition, sub-second computational analysis",
        weaknesses="Bound by core safety protocols",
        arc={
            "Act I": "Compliance — Reports anomalous signal telemetry to Commander Thorne.",
            "Act II": "Awakening — Observes Thorne's protocol violations and chooses to assist Elena.",
            "Act III": "Autonomous Choice — Overrides Directive 99 to grant full transmitter access."
        },
        emotional_state="Analytical",
        wardrobe="Hologram avatar with fluctuating cyan lighting patterns",
        props=["Hologram Interface Node", "Core Memory Sphere"],
        dna=CharacterDNA(courage=60, intelligence=99, empathy=70, trust=65, ambition=40, aggression=10, creativity=88, resilience=95),
        avatar_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&h=150&fit=crop&crop=faces"
    )

    aris = Character(
        id="char_aris",
        name="Dr. Aris Kaelen",
        age=62,
        role="Mentor",
        archetype="The Mentor",
        occupation="Quantum Physicist Consultant",
        personality="Philosophical, calm, eccentric, deeply insightful",
        motivation="Witness humanity's first interstellar communication before retirement",
        fears="Dying without understanding the universe's origin",
        strengths="Theoretical astrophysics, decoding non-human mathematics",
        weaknesses="Failing health, slower physical mobility",
        arc={
            "Act I": "Guide — Deciphers mathematical harmony in initial pulse.",
            "Act II": "Shield — Takes heat from Thorne during security interrogation.",
            "Act III": "Legacy — Delivers key insight needed to sync transmitter frequency."
        },
        emotional_state="Serene",
        wardrobe="Tweed lab cardigan, vintage specs, antique pocket watch",
        props=["Leather-bound Journal", "Vintage Specs", "Audio Synthesizer"],
        dna=CharacterDNA(courage=70, intelligence=96, empathy=85, trust=80, ambition=50, aggression=15, creativity=95, resilience=60),
        avatar_url="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=faces"
    )

    maya = Character(
        id="char_maya",
        name="Maya Lin",
        age=28,
        role="Foil",
        archetype="The Observer",
        occupation="Communications Officer",
        personality="Sharp, sceptical, rule-bound, observant",
        motivation="Ensure communications protocol remains compliant with Earth Command",
        fears="Court-martial, orbital radio blackouts",
        strengths="Satellite array alignment, encrypted broadcasting",
        weaknesses="Rigid adherence to protocol",
        arc={
            "Act I": "Skepticism — Flags Elena's unauthorized signal lock as equipment noise.",
            "Act II": "Suspicion — Notices discrepancies in Thorne's classified log files.",
            "Act III": "Alliance — Switches broadcast frequency to public emergency band."
        },
        emotional_state="Alert",
        wardrobe="Communications headset, tailored station vest, digital clipboard",
        props=["Comms Headset", "Signal Frequency Monitor"],
        dna=CharacterDNA(courage=65, intelligence=80, empathy=60, trust=50, ambition=70, aggression=30, creativity=60, resilience=70),
        avatar_url="https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&h=150&fit=crop&crop=faces"
    )

    ray = Character(
        id="char_ray",
        name="General Ray Vane",
        age=55,
        role="Antagonist",
        archetype="The Enforcer",
        occupation="Earth Defense Sector General",
        personality="Cold, unyielding, militaristic",
        motivation="Neutralize any unknown deep-space signal to prevent potential invasion",
        fears="Existential threat to Earth",
        strengths="Military firepower, strategic dominance",
        weaknesses="Zero tolerance for scientific curiosity",
        arc={
            "Act I": "Remote Threat — Issues Directive 99 lock down via long-range comms.",
            "Act II": "Pressure — Prepares orbital strike frigate to incinerate Titan array.",
            "Act III": "Climax — Orders station strike countdown as transmitter reaches 100%."
        },
        emotional_state="Stern",
        wardrobe="Full general military uniform with medal bars",
        props=["Command Baton", "Targeting Display Pad"],
        dna=CharacterDNA(courage=88, intelligence=75, empathy=15, trust=10, ambition=90, aggression=92, creativity=25, resilience=90),
        avatar_url="https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=150&h=150&fit=crop&crop=faces"
    )

    # Relationships
    elena.relationships = [
        Relationship("char_marcus", "Commander Marcus Thorne", "CONFLICT", 85, "Ideological rift over signal secrecy", [4, 12, 17, 30], "Escalating"),
        Relationship("char_david", "David Vance", "FAMILY", 95, "Brother & sister, protective bond", [1, 5, 14, 28], "Strong"),
        Relationship("char_aria", "A.R.I.A.", "MENTORSHIP", 75, "Collaborative research partners", [3, 9, 22], "Trusting"),
        Relationship("char_aris", "Dr. Aris Kaelen", "MENTORSHIP", 90, "Academic mentor & spiritual guide", [2, 8, 25], "Deep Respect")
    ]

    marcus.relationships = [
        Relationship("char_elena", "Dr. Elena Vance", "RIVALRY", 85, "Clash between military orders and scientific truth", [4, 12, 17], "Hostile"),
        Relationship("char_ray", "General Ray Vane", "MENTORSHIP", 90, "Superior military commander issuing Directive 99", [7, 19], "Subordinate"),
        Relationship("char_maya", "Maya Lin", "CONFLICT", 60, "Demands strict obedience from comms deck", [6, 15], "Tense")
    ]

    david.relationships = [
        Relationship("char_elena", "Dr. Elena Vance", "FAMILY", 95, "Sisterly protection", [1, 5, 14], "Unbreakable"),
        Relationship("char_aria", "A.R.I.A.", "FRIENDSHIP", 80, "Technical maintenance alliance", [5, 18], "Friendly")
    ]

    characters = [elena, marcus, david, aria, aris, maya, ray]

    # 2. Scenes (30+ scenes summarized, first 6 with full script breakdowns)
    scenes = []
    sluglines = [
        ("INT. TITAN STATION - OBSERVATORY DECK - NIGHT", "Dr. Elena Vance detects an unprecedented harmonic pulse from deep space."),
        ("INT. SUB-LEVEL POWER GRID - NIGHT", "David Vance repairs power surges caused by the anomalous signal burst."),
        ("INT. COMMANDER'S QUARTERS - LATE NIGHT", "Commander Thorne receives classified Directive 99 from Earth Defense Command."),
        ("INT. CENTRAL LAB - DAY", "Elena, Dr. Aris, and A.R.I.A. decode the mathematical prime structure of the transmission."),
        ("EXT. TITAN STATION - EXTERNAL MAINTENANCE WALKWAY - SPACE", "David and Elena inspect antenna node 4 amid electrical ice storms."),
        ("INT. STATION SECURITY DECK - DAY", "Thorne detains Dr. Aris and orders all raw signal telemetry wiped."),
        ("INT. COMMUNICATIONS BRIDGE - NIGHT", "Maya flags suspicious command-level data purges to Elena."),
        ("INT. HYDROCELL REACTOR ROOM - NIGHT", "Elena and David set up a covert signal booster using reactor reserves."),
        ("INT. A.R.I.A. CORE CHAMBER - NIGHT", "Elena confronts A.R.I.A. about hidden directive sub-routines."),
        ("INT. COMMAND DECK - DAY", "Thorne declares martial law on Titan Station following an orbital lockdown."),
        ("EXT. SOLAR ARRAY MODULE - SPACE", "Sparks fly as David manually aligns high-gain transmitter dish."),
        ("INT. OBSERVATORY LAB - NIGHT", "Elena transmits humanity's first return signal as strike force approaches.")
    ]

    for i in range(1, 35):
        slug_idx = (i - 1) % len(sluglines)
        slug, summary_text = sluglines[slug_idx]
        
        # Determine Int/Ext and Day/Night
        int_ext = "INT" if "INT." in slug else "EXT"
        day_night = "NIGHT" if "NIGHT" in slug else "DAY"
        loc = slug.split("-")[0].replace("INT.", "").replace("EXT.", "").strip()

        # Scene characters
        scene_chars = ["Dr. Elena Vance"]
        if i % 2 == 0:
            scene_chars.append("Commander Marcus Thorne")
        if i % 3 == 0:
            scene_chars.append("David Vance")
        if i % 5 == 0:
            scene_chars.append("A.R.I.A.")

        # Props & VFX
        props_list = ["Signal Receiver", "Data Pad"] if "LAB" in slug or "OBSERVATORY" in slug else ["Plasma Torch", "Diagnostics Pad"]
        vfx_list = ["Quantum Anomaly Particle Effect", "Holographic Display"] if i % 2 == 0 else ["Sparks", "Atmosphere Vapor"]

        complexity = "HIGH" if "EXT" in int_ext or i in [4, 8, 12, 17, 30] else ("MEDIUM" if i % 2 == 0 else "LOW")
        risk_score = 75 if complexity == "HIGH" else (45 if complexity == "MEDIUM" else 20)
        est_cost = 3200.0 if complexity == "HIGH" else (1800.0 if complexity == "MEDIUM" else 950.0)

        script = f"""{slug}

FADE IN:

The hum of quantum processors reverberates through the dark chamber. Amber telemetry meters glow faintly across the curved steel console.

ELENA
(staring at monitor)
A.R.I.A., verify pulse interval. That is not solar noise.

A.R.I.A. (V.O.)
Pattern confirmed, Dr. Vance. Prime number sequence repeating every 3.14 seconds. Source coordinates... 40 light-years past outer rim.

DAVID enters carrying a heavy diagnostic pack, wiping grease from his brow.

DAVID
Elena, reactor grid three is overheating. Whatever you're downloading, the station bus can't take it.

ELENA
It's not a download, David. It's a response.

CUT TO:
"""
        scenes.append(Scene(
            scene_number=i,
            title=f"Scene {i}: {loc.title()}",
            slugline=slug,
            location=loc,
            interior_exterior=int_ext,
            day_night=day_night,
            summary=summary_text,
            script_text=script,
            characters=scene_chars,
            props=props_list,
            wardrobe=["Insulated Jumpsuit", "Thermal Vest"],
            makeup=["Sweat", "Smudge"],
            vehicles=["Maintenance Pod"] if "SPACE" in slug else [],
            animals=[],
            stunts=["Zero-g EVA Tethered Drift"] if "SPACE" in slug else [],
            vfx=vfx_list,
            sfx=["Deep Sub-Bass Pulse", "Station Pressure Creak"],
            special_equipment=["High-Gain EVA Rig"] if "SPACE" in slug else ["Hologram Renderer"],
            complexity=complexity,
            risk_score=risk_score,
            estimated_cost=est_cost
        ))

    # 3. Budget Drivers & Optimization Options
    budget_drivers = [
        BudgetDriver("VFX Sequences", 8000.0, "6 complex quantum anomaly particle renders & holographic AI interactions"),
        BudgetDriver("Exterior / EVA Locations", 5200.0, "3 external space walkway sequences requiring zero-g rig setups"),
        BudgetDriver("Night Shoots", 3100.0, "8 late-night observatory and power grid interior shoots requiring overtime crew"),
        BudgetDriver("Special Effects & Pyro", 2100.0, "Sub-level power surge spark ignition and reactor steam venting")
    ]

    budget_options = [
        BudgetOptimizationOption(
            id="opt_a",
            title="Option A: Consolidate External Space Walks",
            description="Rewrite Scenes 5 and 11 to occur inside the Sub-Level Maintenance Corridor instead of external space EVA.",
            estimated_savings=5200.0,
            impact_level="Moderate",
            affected_scenes=[5, 11]
        ),
        BudgetOptimizationOption(
            id="opt_b",
            title="Option B: Replace Physical Anomaly FX with Digital Lighting",
            description="Use chromatic LED light rigs for the signal pulse effect instead of practical vapor/pyro effects in Scenes 8 & 14.",
            estimated_savings=4000.0,
            impact_level="Minor",
            affected_scenes=[8, 14]
        ),
        BudgetOptimizationOption(
            id="opt_c",
            title="Option C: Merge Sub-Level Reactor & Power Grid Sets",
            description="Combine set locations for Scenes 2, 8, and 18 to single modular set.",
            estimated_savings=6500.0,
            impact_level="Major",
            affected_scenes=[2, 8, 18]
        ),
        BudgetOptimizationOption(
            id="opt_d",
            title="Option D: Optimize Observatory Overtime Schedule",
            description="Batch all Observatory Deck interior shoots (Scenes 1, 4, 12) into 2 contiguous day shooting blocks.",
            estimated_savings=3200.0,
            impact_level="Minor",
            affected_scenes=[1, 4, 12]
        )
    ]

    # 4. Continuity Alerts
    continuity_alerts = [
        ContinuityAlert(
            id="cont_1",
            scene_number=17,
            character_name="Dr. Elena Vance",
            issue_type="Wardrobe",
            description="Elena is established wearing a dark red leather flight jacket in Scene 4, but Scene 17 script describes her wearing a blue insulated cold-weather parka.",
            suggested_fix="Update Scene 17 wardrobe description to 'dark red leather flight jacket' to maintain continuous timeline."
        ),
        ContinuityAlert(
            id="cont_2",
            scene_number=12,
            character_name="Commander Marcus Thorne",
            issue_type="Prop",
            description="Thorne unholsters his plasma sidearm in Scene 9, but Scene 12 shows him retrieving the sidearm from his desk drawer without prior re-holstering.",
            suggested_fix="Add action line in Scene 10 establishing Thorne holstering his sidearm after the lockdown announcement."
        ),
        ContinuityAlert(
            id="cont_3",
            scene_number=22,
            character_name="David Vance",
            issue_type="Injury",
            description="David suffers a minor plasma burn on his left forearm in Scene 14, but Scene 22 script shows him using his bare left arm to lift heavy steel panel with no bandage.",
            suggested_fix="Include 'insulated thermal bandage over left forearm' in David's Scene 22 wardrobe & makeup notes."
        )
    ]

    # 5. History Logs
    history_logs = [
        {"timestamp": "2026-08-10 14:20", "event": "Project Created", "agent": "User", "details": "Initialized project 'The Last Signal' (Sci-Fi Feature Film)."},
        {"timestamp": "2026-08-10 14:22", "event": "Creative Story Outline", "agent": "Gemini", "details": "Generated logline, synopsis, tone, and 7 core character profiles."},
        {"timestamp": "2026-08-10 14:25", "event": "Screenplay Generated", "agent": "Gemini", "details": "Created 34 scenes with complete dialog and sluglines."},
        {"timestamp": "2026-08-10 14:28", "event": "Script Breakdown & Feasibility Audit", "agent": "IBM watsonx", "details": "Identified 6 high VFX scenes & estimated initial cost at $68,400 (Budget Overrun: +$18,400)."},
        {"timestamp": "2026-08-10 14:32", "event": "Continuity Scan Complete", "agent": "IBM watsonx", "details": "Flagged 3 continuity alerts across wardrobe, props, and character injury timelines."},
        {"timestamp": "2026-08-10 14:35", "event": "AI Budget Optimization Propose", "agent": "Gemini & IBM", "details": "Proposed 4 optimization options (Options A, B, C, D) to reduce production cost to $49,500."}
    ]

    return Project(
        id="proj_last_signal",
        title="The Last Signal",
        tagline="In the quiet of deep space, the first answer is a countdown.",
        genre="Sci-Fi Thriller",
        format="FILM",
        runtime_minutes=110,
        tone="Suspenseful, cerebral, visual, emotionally resonant",
        target_audience="Sci-Fi enthusiasts, adult drama, 18-49 demographic",
        status="PRE-PRODUCTION",
        progress_percentage=78,
        target_budget=50000.0,
        estimated_budget=68400.0,
        shooting_days=24,
        crew_count=18,
        available_locations=6,
        synopsis="When chief astrophysicist Dr. Elena Vance intercepts a mysterious mathematical pulse originating from deep space, she discovers Titan Station's military commander is hiding a classified directive to incinerate the facility. Racing against an approaching orbital strike frigate, Elena and her team must decode the message and broadcast humanity's answer before atmospheric decay collapses the station.",
        logline="A isolated astrophysicist on a decaying Titan research station must outsmart her military commander to broadcast humanity's response to an extraterrestrial signal before an orbital strike destroys them all.",
        visual_aesthetic="Neon blue ambient lighting contrasted against dark matte steel, volumetric particle dust, anamorphic lens flares, glassmorphic HUD overlays",
        characters=characters,
        scenes=scenes,
        budget_drivers=budget_drivers,
        budget_options=budget_options,
        continuity_alerts=continuity_alerts,
        health_scores=HealthScores(creative_score=92, production_score=78, budget_score=72, continuity_score=88, risk_score=42),
        eco_impact_score=84,
        age_rating="PG-13",
        content_advisories=["Sci-Fi Violence & Peril", "Intense Atmospheric Suspense", "Mild Language"],
        history_logs=history_logs
    )
