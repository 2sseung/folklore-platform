import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

st.set_page_config(
    page_title="한국구비문학대계 인터랙티브 플랫폼",
    page_icon="📚",
    layout="wide",
)

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

st.title("📚 한국구비문학대계 인터랙티브 플랫폼")
st.markdown("한국 구비문학 자료를 탐색하고, 이해하고, 활용하고, 기여하는 공간입니다.")

st.divider()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("### 🗺️ 탐색")
    st.markdown("채록지 지도를 통해 전국의 설화·민요·무가 자료를 시각적으로 탐색합니다.")
    if st.button("지도로 탐색하기", use_container_width=True, key="btn_explore"):
        st.switch_page("pages/01_탐색_지도시각화.py")

with col2:
    st.markdown("### 📖 이해")
    st.markdown("모티프·이본을 비교 분석하고 AI와 함께 설화를 깊이 이해합니다.")
    if st.button("모티프 탐색하기", use_container_width=True, key="btn_understand"):
        st.switch_page("pages/02_이해_모티프탐색.py")

with col3:
    st.markdown("### ✏️ 활용")
    st.markdown("설화를 현대어·아동용·영문·대본 등 다양한 형식으로 재가공합니다.")
    if st.button("현대역 생성하기", use_container_width=True, key="btn_use"):
        st.switch_page("pages/03_활용_현대역.py")

with col4:
    st.markdown("### 🤝 기여")
    st.markdown("내가 알고 있는 설화를 직접 기록해 플랫폼에 기여할 수 있습니다.")
    if st.button("설화 입력하기", use_container_width=True, key="btn_contribute"):
        st.switch_page("pages/04_기여_설화입력.py")

st.divider()
st.caption("데이터 출처: 한국구비문학대계 (한국학중앙연구원)")
