import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
import random
from dotenv import load_dotenv
import anthropic

from utils.db import get_conn, search_items_by_title, get_item_by_id

load_dotenv()
st.set_page_config(page_title="활용 — 현대역 & 재가공", layout="wide")
from utils.style import inject_css, page_title
inject_css()
page_title("활용", "현대역 & 재가공")

conn = get_conn()

# ── 설화 선택 ─────────────────────────────────────────────────────────────────
st.subheader("설화 선택")

col_search, col_random = st.columns([4, 1])
with col_search:
    keyword = st.text_input("제목 검색", placeholder="제목 키워드 입력")
with col_random:
    st.markdown("<br/>", unsafe_allow_html=True)
    if st.button("무작위 추천"):
        rows = conn.execute(
            "SELECT id FROM items WHERE content IS NOT NULL AND content != '' ORDER BY RANDOM() LIMIT 1"
        ).fetchone()
        if rows:
            st.session_state['use_id'] = rows['id']

if keyword:
    results = search_items_by_title(conn, keyword)
    if results:
        options = {f"[{r['id']}] {r['title']} ({r['region']} {r['district']})": r['id'] for r in results}
        selected_label = st.selectbox("설화 선택", [""] + list(options.keys()))
        if selected_label:
            st.session_state['use_id'] = options[selected_label]

use_id = st.session_state.get('use_id')

if not use_id:
    st.info("제목을 검색하거나 랜덤 추천 버튼을 눌러 설화를 선택하세요.")
    st.stop()

item = get_item_by_id(conn, use_id)
if not item:
    st.error("설화를 찾을 수 없습니다.")
    st.stop()

item = dict(item)
content = item.get('content', '') or ''

# 원문 미리보기
with st.expander(f"원문 미리보기 — {item['title']}", expanded=True):
    if content:
        st.write(content[:600] + ("..." if len(content) > 600 else ""))
    else:
        st.caption("본문 없음")

if not content:
    st.warning("본문 전사가 없는 자료입니다. 재가공 기능을 사용할 수 없습니다.")
    st.stop()

# ── 변환 형식 선택 ────────────────────────────────────────────────────────────
st.divider()
st.subheader("변환 형식 선택")

FORMAT_OPTIONS = {
    "현대어 윤문본": "원문의 서사 구조와 표현을 살리되 현대 독자가 읽기 쉽게 윤문하세요.",
    "아동용 재서술본": "초등학생이 이해할 수 있는 쉬운 문장으로 재서술하세요. 어려운 어휘는 풀어 쓰세요.",
    "영어 번역본": "Translate this Korean folk tale into natural English, preserving its narrative structure.",
    "웹툰/영상 대본 형식": "이 설화를 웹툰 또는 영상 콘텐츠용 대본 형식(씬 번호, 지문, 대사)으로 변환하세요.",
}

selected_format = st.radio("형식", list(FORMAT_OPTIONS.keys()), horizontal=True)

# ── 생성 ─────────────────────────────────────────────────────────────────────
st.divider()

if st.button("생성하기", type="primary"):
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        st.error(".env 파일에 ANTHROPIC_API_KEY를 설정하세요.")
    else:
        system_prompt = FORMAT_OPTIONS[selected_format]
        user_message = f"다음 한국 설화를 지시에 따라 변환해주세요.\n\n[제목]: {item['title']}\n[원문]: {content}"

        client = anthropic.Anthropic(api_key=api_key)

        result_placeholder = st.empty()
        result_container = st.container()

        with result_container:
            st.markdown(
                "<div style='background:#FFF7ED;border:1px solid #FED7AA;"
                "border-radius:8px;padding:16px;margin-top:8px'>",
                unsafe_allow_html=True
            )

            def stream_response():
                with client.messages.stream(
                    model="claude-sonnet-4-6",
                    max_tokens=2048,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_message}]
                ) as stream:
                    for text in stream.text_stream:
                        yield text

            generated_text = st.write_stream(stream_response())
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown('<p class="ai-note">AI가 생성한 파생 텍스트로, 원본 전사본과 다를 수 있습니다</p>', unsafe_allow_html=True)

        st.session_state['generated_text'] = generated_text
        st.session_state['generated_format'] = selected_format
        st.session_state['generated_title'] = item['title']

# ── 출력 ─────────────────────────────────────────────────────────────────────
if 'generated_text' in st.session_state and st.session_state['generated_text']:
    st.divider()
    st.subheader("출력")

    gen_text = st.session_state['generated_text']
    gen_format = st.session_state.get('generated_format', '')
    gen_title = st.session_state.get('generated_title', '')

    st.code(gen_text, language=None)

    fname = f"{gen_title}_{gen_format}.txt"
    st.download_button(
        label="텍스트 파일 내려받기",
        data=gen_text.encode('utf-8'),
        file_name=fname,
        mime="text/plain",
    )

conn.close()
