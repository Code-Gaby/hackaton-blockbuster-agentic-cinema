"""
Agentic Cinema — Vector SVG Icon Asset System (Pure SVG, Zero external images, Zero Emojis)
Exact SVGs with classes for single-cycle hover micro-animations.
"""

def get_svg_icon(name: str, size: int = 22, color: str = "currentColor") -> str:
    """Returns clean inline SVG matching Agentic Cinema Studio specifications."""
    
    if name in ["projects", "film_reel", "library_reel"]:
        return f"""<svg class="icon icon-reel" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="9"/>
            <circle cx="12" cy="12" r="3"/>
            <path d="M12 3v6m0 6v6M3 12h6m6 0h6"/>
        </svg>"""

    elif name in ["characters", "theatre_masks", "masks"]:
        # Comedy & Tragedy Theatre Masks (Happy & Sad masks) with single-cycle animation classes
        return f"""<svg class="icon icon-masks" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <g class="mask-happy">
                <path d="M3 6a5 5 0 0 1 10 0v2a5 5 0 0 1-10 0V6z"/>
                <circle cx="6.5" cy="6" r="0.6" fill="{color}"/>
                <circle cx="9.5" cy="6" r="0.6" fill="{color}"/>
                <path d="M6 8.5c.8.8 2.2.8 3 0"/>
            </g>
            <g class="mask-sad">
                <path d="M11 11a5 5 0 0 1 10 0v2a5 5 0 0 1-10 0v-2z"/>
                <circle cx="14.5" cy="11" r="0.6" fill="{color}"/>
                <circle cx="17.5" cy="11" r="0.6" fill="{color}"/>
                <path d="M14.5 14.5c.8-.8 2.2-.8 3 0"/>
            </g>
        </svg>"""

    elif name in ["chat", "visionary_agent", "star_agent"]:
        return f"""<svg class="icon icon-chat" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2l2.4 5 5.6.8-4 4 1 5.6-5-2.6-5 2.6 1-5.6-4-4 5.6-.8z"/>
        </svg>"""

    elif name in ["relations", "relationships", "network"]:
        return f"""<svg class="icon icon-relations" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="6" cy="6" r="3"/>
            <circle cx="18" cy="18" r="3"/>
            <line x1="8.5" y1="8.5" x2="15.5" y2="15.5"/>
            <circle cx="18" cy="6" r="3"/>
            <line x1="8.5" y1="6" x2="15.5" y2="6"/>
        </svg>"""

    elif name in ["scenes", "scenarios", "clapper"]:
        return f"""<svg class="icon icon-scenes" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 7l4 4-4 4"/>
            <path d="M8 7h13v10H8z"/>
        </svg>"""

    elif name in ["summary", "production_summary", "doc"]:
        return f"""<svg class="icon icon-summary" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
        </svg>"""

    elif name in ["create_project", "btn_clapper"]:
        return f"""<svg class="icon icon-clapper" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path class="clap-top" d="M4 4h16l-2 4H2z"/>
            <rect x="2" y="8" width="20" height="12" rx="2"/>
        </svg>"""

    elif name == "brand":
        return f"""<svg class="icon" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 6h16M4 12h16M4 18h16"/>
            <circle cx="9" cy="6" r="1.5" fill="{color}"/>
            <circle cx="15" cy="18" r="1.5" fill="{color}"/>
        </svg>"""

    elif name == "search":
        return f"""<svg class="icon" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>"""

    elif name in ["send", "arrow_send"]:
        return f"""<svg class="icon" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22 2 15 22 11 13 2 9 22 2" fill="{color}"/>
        </svg>"""

    elif name in ["delete", "trash"]:
        return f"""<svg class="icon" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6V20A2 2 0 0 1 17 22H7A2 2 0 0 1 5 20V6M8 6V4A2 2 0 0 1 10 2H14A2 2 0 0 1 16 4V6"/>
        </svg>"""

    elif name in ["archive", "folder"]:
        return f"""<svg class="icon" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="21 8 21 21 3 21 3 8"/>
            <rect x="1" y="3" width="22" height="5"/>
            <line x1="10" y1="12" x2="14" y2="12"/>
        </svg>"""

    elif name == "settings":
        return f"""<svg class="icon" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
        </svg>"""

    return f"""<svg class="icon" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>"""
