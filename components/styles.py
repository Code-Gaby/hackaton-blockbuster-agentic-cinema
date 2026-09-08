import streamlit as st

def apply_cinematic_styles():
    """Injects high-end dark luxury Hollywood CSS matching Agentic Cinema Studio specifications."""
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700;900&family=Outfit:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;600;700&display=swap');

    :root {
      --bg-deep: #08090d;
      --bg-surface: #10131c;
      --bg-surface-elevated: #161b26;
      --gold-primary: #d4af37;
      --gold-glow: #f5d77f;
      --ruby-accent: #e50914;
      --ruby-dark: #8b0000;
      --text-main: #f3f4f6;
      --text-muted: #9ca3af;
      --border-subtle: rgba(212, 175, 55, 0.18);
      --border-glow: rgba(212, 175, 55, 0.45);
      --glass-bg: rgba(16, 19, 28, 0.85);
      --font-stack: 'Outfit', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    }

    * {
      box-sizing: border-box;
      font-family: var(--font-stack);
    }

    /* Main Viewport & Reset Streamlit Base */
    .stApp {
      background-color: var(--bg-deep) !important;
      background: radial-gradient(circle at top right, rgba(229, 9, 20, 0.04), transparent 40%),
                  radial-gradient(circle at bottom left, rgba(212, 175, 55, 0.03), transparent 50%),
                  var(--bg-deep) !important;
      color: var(--text-main) !important;
    }

    header[data-testid="stHeader"] {
      display: none !important;
    }

    .main .block-container {
      padding: 0 32px 40px 32px !important;
      max-width: 100% !important;
    }

    /* SVG Icons and 1-Cycle Micro-Animations */
    .icon {
      width: 22px;
      height: 22px;
      stroke: currentColor;
      fill: none;
      stroke-width: 2;
      stroke-linecap: round;
      stroke-linejoin: round;
      transition: transform 0.3s ease, stroke 0.3s ease;
      flex-shrink: 0;
      vertical-align: middle;
    }

    /* 1-Cycle Hover Animations */
    .nav-btn:hover .icon-masks .mask-happy {
      animation: maskHappyMove 0.6s ease-out forwards;
    }
    .nav-btn:hover .icon-masks .mask-sad {
      animation: maskSadMove 0.6s ease-out forwards;
    }
    @keyframes maskHappyMove {
      0% { transform: translateY(0); }
      50% { transform: translateY(-3px) rotate(-4deg); }
      100% { transform: translateY(0); }
    }
    @keyframes maskSadMove {
      0% { transform: translateY(0); }
      50% { transform: translateY(3px) rotate(4deg); }
      100% { transform: translateY(0); }
    }

    .nav-btn:hover .icon-reel {
      animation: reelSpin 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    @keyframes reelSpin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(180deg); }
    }

    .btn-create:hover .icon-clapper .clap-top {
      animation: clapperSnap 0.5s ease forwards;
    }
    @keyframes clapperSnap {
      0% { transform: rotate(0deg); transform-origin: 2px 8px; }
      40% { transform: rotate(-25deg); transform-origin: 2px 8px; }
      70% { transform: rotate(0deg); transform-origin: 2px 8px; }
      100% { transform: rotate(0deg); }
    }

    /* Left Sidebar Navigation */
    [data-testid="stSidebar"] {
      background-color: var(--bg-surface) !important;
      border-right: 1px solid var(--border-subtle) !important;
      padding: 0 !important;
    }

    [data-testid="stSidebar"] .block-container {
      padding: 24px 16px !important;
    }

    .brand-wrap {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 0 8px 20px 8px;
      border-bottom: 1px solid var(--border-subtle);
      margin-bottom: 16px;
    }

    .brand-icon {
      width: 38px;
      height: 38px;
      background: linear-gradient(135deg, var(--gold-primary), var(--ruby-dark));
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      box-shadow: 0 0 15px rgba(212, 175, 55, 0.3);
    }

    .brand-text h1 {
      font-family: 'Cinzel', serif;
      font-size: 1.15rem;
      font-weight: 700;
      letter-spacing: 1px;
      color: var(--text-main);
      margin: 0;
      line-height: 1.2;
    }

    .brand-text span {
      font-size: 0.7rem;
      color: var(--gold-primary);
      text-transform: uppercase;
      letter-spacing: 2px;
    }

    .nav-btn {
      width: 100%;
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 12px 14px;
      background: transparent;
      border: 1px solid transparent;
      border-radius: 8px;
      color: var(--text-muted);
      cursor: pointer;
      font-size: 0.9rem;
      font-weight: 500;
      transition: all 0.25s ease;
      text-align: left;
      margin-bottom: 4px;
    }

    .nav-btn:hover {
      background: rgba(212, 175, 55, 0.08);
      color: var(--gold-glow);
      border-color: rgba(212, 175, 55, 0.2);
    }

    .nav-btn.active {
      background: linear-gradient(90deg, rgba(212, 175, 55, 0.15), transparent);
      color: var(--gold-primary) !important;
      border-left: 3px solid var(--gold-primary);
      border-color: rgba(212, 175, 55, 0.25);
      font-weight: 700;
    }

    /* Header Bar */
    .header-bar {
      height: 70px;
      padding: 0 0;
      border-bottom: 1px solid var(--border-subtle);
      display: flex;
      align-items: center;
      justify-content: space-between;
      backdrop-filter: blur(10px);
      background: var(--glass-bg);
      margin-bottom: 24px;
    }

    .view-title-wrap {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .view-title {
      font-family: 'Cinzel', serif;
      font-size: 1.3rem;
      font-weight: 700;
      color: var(--text-main);
      margin: 0;
    }

    .badge-status {
      padding: 3px 10px;
      border-radius: 4px;
      background: rgba(212, 175, 55, 0.12);
      color: var(--gold-primary);
      font-size: 0.75rem;
      font-weight: 600;
      letter-spacing: 0.5px;
      border: 1px solid var(--border-subtle);
    }

    /* Library Controls & Project Grid */
    .library-controls {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 28px;
      gap: 16px;
    }

    .btn-create {
      background: linear-gradient(135deg, var(--gold-primary), #9a781b);
      color: #000 !important;
      border: none;
      padding: 10px 20px;
      font-size: 0.85rem;
      font-weight: 700;
      border-radius: 8px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 10px;
      box-shadow: 0 4px 15px rgba(212, 175, 55, 0.25);
      transition: all 0.25s ease;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      text-decoration: none;
    }

    .btn-create:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(212, 175, 55, 0.4);
      background: linear-gradient(135deg, var(--gold-glow), var(--gold-primary));
    }

    .project-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
      gap: 24px;
    }

    .project-card {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      transition: all 0.3s ease;
    }

    .project-card:hover {
      border-color: var(--gold-primary);
      transform: translateY(-4px);
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
    }

    .card-banner {
      height: 130px;
      background: linear-gradient(180deg, rgba(8, 9, 13, 0.2), var(--bg-surface)),
                  radial-gradient(circle at center, #261f10, #10131c);
      display: flex;
      align-items: center;
      justify-content: center;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      position: relative;
    }

    .card-banner-decor {
      border: 2px dashed rgba(212, 175, 55, 0.3);
      padding: 10px 18px;
      border-radius: 6px;
      font-family: 'IBM Plex Mono', monospace;
      font-size: 0.75rem;
      letter-spacing: 2px;
      color: var(--gold-primary);
      text-transform: uppercase;
      background: rgba(0,0,0,0.3);
    }

    .card-body {
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      flex: 1;
    }

    .card-title {
      font-family: 'Cinzel', serif;
      font-size: 1.05rem;
      font-weight: 700;
      color: var(--text-main);
    }

    .card-meta {
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 0.75rem;
      color: var(--text-muted);
    }

    .card-actions {
      display: flex;
      gap: 8px;
      margin-top: 10px;
      padding-top: 10px;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
    }

    .btn-action {
      flex: 1;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--border-subtle);
      color: var(--text-main);
      padding: 7px 10px;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      transition: all 0.2s ease;
    }

    .btn-action:hover {
      background: var(--gold-primary);
      color: #000;
    }

    .btn-action.danger:hover {
      background: var(--ruby-accent);
      color: #fff;
    }

    /* Chat Container & Film Reel Spinner */
    .chat-container {
      display: flex;
      flex-direction: column;
      max-width: 900px;
      margin: 0 auto;
    }

    .chat-messages {
      display: flex;
      flex-direction: column;
      gap: 16px;
      margin-bottom: 20px;
    }

    .message {
      display: flex;
      gap: 14px;
      max-width: 85%;
    }

    .message.user {
      align-self: flex-end;
      flex-direction: row-reverse;
    }

    .message.agent {
      align-self: flex-start;
    }

    .msg-avatar {
      width: 34px;
      height: 34px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    .message.user .msg-avatar {
      background: var(--ruby-dark);
      color: #fff;
    }

    .message.agent .msg-avatar {
      background: var(--gold-primary);
      color: #000;
    }

    .msg-content {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      padding: 14px 18px;
      border-radius: 12px;
      font-size: 0.9rem;
      line-height: 1.6;
    }

    .message.user .msg-content {
      background: linear-gradient(135deg, rgba(229, 9, 20, 0.15), rgba(16, 19, 28, 0.9));
      border-color: rgba(229, 9, 20, 0.3);
    }

    .message.agent .msg-content {
      border-left: 3px solid var(--gold-primary);
    }

    /* Film Loader Spinner */
    .film-loader {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 14px 20px;
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      width: fit-content;
      margin: 16px 0;
    }

    .reel-spinner {
      width: 24px;
      height: 24px;
      animation: infiniteSpin 1.2s linear infinite;
    }
    @keyframes infiniteSpin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }

    .film-loader-text {
      font-family: 'IBM Plex Mono', monospace;
      font-size: 0.8rem;
      color: var(--gold-primary);
      font-weight: 700;
      letter-spacing: 1px;
    }

    .chat-input-area {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 12px;
      padding: 8px 12px;
      display: flex;
      align-items: center;
      gap: 12px;
      margin-top: 14px;
    }

    .btn-send {
      background: var(--ruby-accent);
      border: none;
      color: #fff;
      padding: 10px 18px;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s ease;
    }

    .btn-send:hover {
      background: #ff1f2d;
      box-shadow: 0 0 12px rgba(229, 9, 20, 0.5);
    }

    /* Character Cards with Film Perforations */
    .character-card {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 10px;
      padding: 20px;
      display: flex;
      gap: 20px;
      position: relative;
      margin-bottom: 16px;
    }

    .film-perforations {
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 8px;
      background: repeating-linear-gradient(to bottom, transparent 0, transparent 8px, rgba(212, 175, 55, 0.3) 8px, rgba(212, 175, 55, 0.3) 14px);
    }

    .character-avatar-mock {
      width: 64px;
      height: 64px;
      background: var(--bg-surface-elevated);
      border: 1px solid var(--gold-primary);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--gold-primary);
      flex-shrink: 0;
    }

    /* Relationship Link Cards */
    .relation-link {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 14px 20px;
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: 8px;
      margin-bottom: 12px;
    }

    .relation-tag {
      font-size: 0.75rem;
      font-weight: bold;
      padding: 4px 10px;
      border-radius: 4px;
    }

    .relation-tag.ally {
      background: rgba(212, 175, 55, 0.15);
      color: var(--gold-primary);
    }

    .relation-tag.enemy {
      background: rgba(229, 9, 20, 0.15);
      color: var(--ruby-accent);
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
