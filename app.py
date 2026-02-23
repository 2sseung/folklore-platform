import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="한국구비문학대계 인터랙티브 플랫폼",
    page_icon="📚",
    layout="wide",
)

st.markdown("""
<style>
/* ── 구글 폰트: 나눔명조 ── */
@import url('https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Nanum Myeongjo', Georgia, serif !important;
}

/* ── 전체 배경 ── */
.stApp {
    background-color: #F7F2E8;
    background-image:
        radial-gradient(ellipse at 20% 50%, rgba(139,26,26,0.03) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 20%, rgba(196,163,90,0.04) 0%, transparent 60%);
}

/* ── 마크다운 컨테이너 클리핑 방지 ── */
[data-testid="stMarkdownContainer"] { overflow: visible !important; }

/* ── 메인 콘텐츠 패딩 (헤더 높이만큼 확보) ── */
.block-container {
    padding-top: 4.5rem !important;
    padding-bottom: 2.5rem;
    max-width: 1200px;
}

/* ── 사이드바 ── */
[data-testid="stSidebar"] {
    background-color: #EDE5D0;
    border-right: 1px solid #C4A35A44;
}
[data-testid="stSidebar"] .stMarkdown p {
    color: #2C1810;
}

/* ── 제목 (h1~h3) ── */
h1 {
    color: #2C1810 !important;
    font-weight: 800 !important;
    letter-spacing: -0.5px;
    border-bottom: 2px solid #8B1A1A;
    padding-bottom: 0.4rem;
    margin-bottom: 0.8rem !important;
}
h2, h3 {
    color: #4A2010 !important;
    font-weight: 700 !important;
}

/* ── 버튼 ── */
.stButton > button {
    background-color: #8B1A1A !important;
    color: #F7F2E8 !important;
    border: none !important;
    border-radius: 2px !important;
    font-family: 'Nanum Myeongjo', serif !important;
    font-size: 0.95rem !important;
    padding: 0.55rem 1.2rem !important;
    transition: background-color 0.2s, box-shadow 0.2s !important;
    box-shadow: 1px 2px 4px rgba(44,24,16,0.18) !important;
}
.stButton > button:hover {
    background-color: #6B1010 !important;
    box-shadow: 2px 3px 8px rgba(44,24,16,0.28) !important;
}

/* ── 입력창 ── */
.stTextInput > div > div > input,
.stTextArea textarea,
.stSelectbox > div > div {
    background-color: #FBF8F2 !important;
    border: 1px solid #C4A35A88 !important;
    border-radius: 2px !important;
    font-family: 'Nanum Myeongjo', serif !important;
    color: #2C1810 !important;
}
.stTextInput > div > div > input:focus,
.stTextArea textarea:focus {
    border-color: #8B1A1A !important;
    box-shadow: 0 0 0 2px rgba(139,26,26,0.15) !important;
}

/* ── 정보 박스 (st.info / st.success / st.warning) ── */
[data-testid="stInfoBox"] {
    background-color: #EDE5D0 !important;
    border-left: 4px solid #C4A35A !important;
}
[data-testid="stSuccessBox"] {
    border-left: 4px solid #5C7A4E !important;
}

/* ── 구분선 ── */
hr {
    border-color: #C4A35A55 !important;
}

/* ── expander ── */
[data-testid="stExpander"] {
    border: 1px solid #C4A35A55 !important;
    border-radius: 2px !important;
    background-color: #FBF8F2 !important;
}

/* ── 캡션 ── */
.stCaption, small {
    color: #7A5C4A !important;
}

/* ── 탭 ── */
[data-testid="stTabs"] button {
    font-family: 'Nanum Myeongjo', serif !important;
    color: #4A2010 !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    border-bottom-color: #8B1A1A !important;
    color: #8B1A1A !important;
}

/* ── 첫 화면 카드 영역 ── */
.main-card {
    background: #FBF8F2;
    border: 1px solid #C4A35A66;
    border-top: 3px solid #8B1A1A;
    border-radius: 2px;
    padding: 1.5rem;
    height: 100%;
    box-shadow: 1px 2px 6px rgba(44,24,16,0.08);
}
</style>
""", unsafe_allow_html=True)

# DB 자동 빌드 (최초 실행 또는 재시작 후 DB 없을 때)
from utils.db import ensure_db, DB_PATH
if not os.path.exists(DB_PATH):
    with st.spinner("데이터베이스를 처음 구축하는 중입니다... (수 분 소요)"):
        try:
            ensure_db()
            st.success("데이터베이스 구축 완료!")
            st.rerun()
        except Exception as e:
            st.error(f"DB 빌드 실패: {e}")
            st.stop()

st.markdown("""
<div style="text-align:center; padding: 2rem 0 1rem 0;">
  <div style="font-size:0.85rem; color:#8B1A1A; letter-spacing:4px; margin-bottom:0.5rem;">
    한국학중앙연구원 X KUCLAB
  </div>
  <h1 style="font-size:2.2rem; font-weight:800; color:#2C1810; border:none; padding:0; margin:0;">
    한국구비문학대계
  </h1>
  <div style="font-size:1.1rem; color:#7A5C4A; margin-top:0.5rem; letter-spacing:2px;">
    인터랙티브 탐색 플랫폼
  </div>
  <div style="width:60px; height:2px; background:#8B1A1A; margin:1rem auto;"></div>
  <p style="color:#4A2010; max-width:520px; margin:0 auto; line-height:1.8; font-size:0.98rem;">
    전국 각지에서 채록된 설화·민요·무가·현대 구전설화를<br>
    탐색하고, 이해하고, 활용하고, 기여하는 공간입니다.
  </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# SVG 아이콘 (단청 적색 라인 스타일)
ICONS = {
    "탐색": """<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24"
      fill="none" stroke="#8B1A1A" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>
    </svg>""",
    "이해": """<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24"
      fill="none" stroke="#8B1A1A" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
      <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
    </svg>""",
    "활용": """<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24"
      fill="none" stroke="#8B1A1A" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 19l7-7 3 3-7 7-3-3z"/>
      <path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/>
      <path d="M2 2l7.586 7.586"/>
      <circle cx="11" cy="11" r="2"/>
    </svg>""",
    "기여": """<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24"
      fill="none" stroke="#8B1A1A" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/>
      <path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/>
    </svg>""",
}

CARDS = [
    ("탐색", "채록지 지도를 통해 전국의 설화·민요·무가 자료를 시각적으로 탐색합니다.", "지도로 탐색하기", "btn_explore", "pages/01_탐색_지도시각화.py"),
    ("이해", "모티프·이본을 비교 분석하고 AI와 함께 설화를 깊이 이해합니다.", "모티프 탐색하기", "btn_understand", "pages/02_이해_모티프탐색.py"),
    ("활용", "설화를 현대어·아동용·영문·대본 등 다양한 형식으로 재가공합니다.", "현대역 생성하기", "btn_use", "pages/03_활용_현대역.py"),
    ("기여", "내가 알고 있는 설화를 직접 기록해 플랫폼에 기여할 수 있습니다.", "설화 입력하기", "btn_contribute", "pages/04_기여_설화입력.py"),
]

col1, col2, col3, col4 = st.columns(4)

for col, (title, desc, btn_label, btn_key, page) in zip(
    [col1, col2, col3, col4], CARDS
):
    with col:
        st.markdown(f"""
        <div class="main-card">
          <div style="margin-bottom:0.7rem;">{ICONS[title]}</div>
          <div style="font-size:1.05rem; font-weight:700; color:#2C1810;
                      border-bottom:1px solid #C4A35A66; padding-bottom:0.4rem;
                      margin-bottom:0.6rem;">{title}</div>
          <p style="font-size:0.88rem; color:#4A2010; line-height:1.7;
                    min-height:60px; margin:0 0 1rem 0;">{desc}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button(btn_label, use_container_width=True, key=btn_key):
            st.switch_page(page)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; padding:1rem 0; border-top:1px solid #C4A35A44;">
  <span style="color:#9A7A6A; font-size:0.82rem; letter-spacing:1px;">
    데이터 출처 — 한국구비문학대계 (한국학중앙연구원)
  </span>
</div>
""", unsafe_allow_html=True)
