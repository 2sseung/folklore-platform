"""공통 CSS 주입 및 페이지 타이틀 렌더링"""
import streamlit as st

# 섹션별 SVG 아이콘
ICONS = {
    "탐색": """<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24"
      fill="none" stroke="#8B1A1A" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>
    </svg>""",
    "이해": """<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24"
      fill="none" stroke="#8B1A1A" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
      <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
    </svg>""",
    "활용": """<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24"
      fill="none" stroke="#8B1A1A" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 19l7-7 3 3-7 7-3-3z"/>
      <path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/>
      <path d="M2 2l7.586 7.586"/>
      <circle cx="11" cy="11" r="2"/>
    </svg>""",
    "기여": """<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24"
      fill="none" stroke="#8B1A1A" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/>
      <path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/>
    </svg>""",
    # 서사지리 전용 (32px — page_title용)
    "서사지리": """<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24"
      fill="none" stroke="#8B1A1A" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="5" cy="18" r="2.5"/>
      <circle cx="19" cy="6" r="2.5"/>
      <path d="M7 16.5 C 10 11 14 9 17 7.5" stroke-dasharray="3 2"/>
    </svg>""",
    # 소형 인라인 아이콘
    "지명": """<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
      fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
      <circle cx="12" cy="10" r="3"/>
    </svg>""",
    "비교": """<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
      fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M18 20V10"/><path d="M12 20V4"/><path d="M6 20v-6"/>
    </svg>""",
    "AI": """<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
      fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
      <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
    </svg>""",
    "분석": """<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
      fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
    </svg>""",
}

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Nanum Myeongjo', Georgia, serif !important; }
.stApp {
    background-color: #F7F2E8;
    background-image:
        radial-gradient(ellipse at 20% 50%, rgba(139,26,26,0.03) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 20%, rgba(196,163,90,0.04) 0%, transparent 60%);
}
[data-testid="stMarkdownContainer"] { overflow: visible !important; }
.block-container { padding-top: 4.5rem !important; padding-bottom: 2rem; max-width: 1200px; }
[data-testid="stSidebar"] { background-color: #EDE5D0; border-right: 1px solid #C4A35A44; }
h1 { color: #2C1810 !important; font-weight: 800 !important;
     border-bottom: 2px solid #8B1A1A; padding-bottom: 0.4rem; margin-bottom: 0.8rem !important; }
h2, h3 { color: #4A2010 !important; font-weight: 700 !important; }
.stButton > button {
    background-color: #8B1A1A !important; color: #F7F2E8 !important;
    border: none !important; border-radius: 2px !important;
    font-family: 'Nanum Myeongjo', serif !important; font-size: 0.95rem !important;
    padding: 0.55rem 1.2rem !important;
    transition: background-color 0.2s, box-shadow 0.2s !important;
    box-shadow: 1px 2px 4px rgba(44,24,16,0.18) !important;
}
.stButton > button:hover { background-color: #6B1010 !important; box-shadow: 2px 3px 8px rgba(44,24,16,0.28) !important; }
.stTextInput > div > div > input, .stTextArea textarea, .stSelectbox > div > div {
    background-color: #FBF8F2 !important; border: 1px solid #C4A35A88 !important;
    border-radius: 2px !important; font-family: 'Nanum Myeongjo', serif !important; color: #2C1810 !important;
}
.stTextInput > div > div > input:focus, .stTextArea textarea:focus {
    border-color: #8B1A1A !important; box-shadow: 0 0 0 2px rgba(139,26,26,0.15) !important;
}
[data-testid="stInfoBox"] { background-color: #EDE5D0 !important; border-left: 4px solid #C4A35A !important; }
hr { border-color: #C4A35A55 !important; }
[data-testid="stExpander"] { border: 1px solid #C4A35A55 !important; border-radius: 2px !important; background-color: #FBF8F2 !important; }
.stCaption, small { color: #7A5C4A !important; }
[data-testid="stTabs"] button { font-family: 'Nanum Myeongjo', serif !important; color: #4A2010 !important; }
[data-testid="stTabs"] button[aria-selected="true"] { border-bottom-color: #8B1A1A !important; color: #8B1A1A !important; }
.main-card { background: #FBF8F2; border: 1px solid #C4A35A66; border-top: 3px solid #8B1A1A;
             border-radius: 2px; padding: 1.5rem; height: 100%; box-shadow: 1px 2px 6px rgba(44,24,16,0.08); }
.page-title { display: flex; align-items: center; gap: 0.7rem; overflow: visible;
              border-bottom: 2px solid #8B1A1A; padding: 0.3rem 0 0.5rem 0; margin-bottom: 1.2rem; }
.page-title-text { font-size: 1.5rem; font-weight: 800; color: #2C1810; white-space: nowrap; line-height: 1.3; }
.page-title-sub { font-size: 0.85rem; color: #8B1A1A; margin-left: auto; letter-spacing: 1px; }
.ai-note { color: #7A5C4A; font-size: 0.82rem; }
.ai-note::before { content: "※ "; color: #8B1A1A; }
</style>
"""


def inject_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def page_title(section: str, subtitle: str):
    """SVG 아이콘 + 타이틀 렌더링"""
    icon = ICONS.get(section, "")
    st.markdown(f"""
    <div class="page-title">
      <div style="flex-shrink:0;line-height:0">{icon}</div>
      <span class="page-title-text">{section} — {subtitle}</span>
    </div>
    """, unsafe_allow_html=True)
