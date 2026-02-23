import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
import anthropic
import json

from utils.db import get_conn, insert_contribution, get_contributions

load_dotenv()
st.set_page_config(page_title="기여 — 설화 입력", layout="wide")
from utils.style import inject_css, page_title, ICONS
inject_css()
page_title("기여", "설화 입력")

st.info(
    "내가 알고 있는 설화를 직접 기록해 플랫폼에 기여할 수 있습니다.\n"
    "기여 데이터는 원본 데이터와 구분되어 표시됩니다."
)

conn = get_conn()

tab_input, tab_list = st.tabs(["설화 입력", "기여 목록"])

# ── 입력 탭 ───────────────────────────────────────────────────────────────────
with tab_input:
    with st.form("contribution_form", clear_on_submit=False):
        st.subheader("메타데이터")
        title = st.text_input("제목 *")
        col1, col2 = st.columns(2)
        with col1:
            region = st.text_input("채록 지역 (광역) *", placeholder="예: 경상남도")
        with col2:
            district = st.text_input("채록 지역 (기초)", placeholder="예: 창녕군")
        location = st.text_input("채록 장소 (상세)", placeholder="예: 이방면 동산리")
        narrator = st.text_input("제보자 이름")
        collected_date = st.date_input("채록 일자", value=None)

        st.subheader("본문")
        content = st.text_area("본문 * (최소 100자 이상)", height=250)
        content_len = len(content) if content else 0
        st.caption(f"현재 {content_len}자")

        submitted = st.form_submit_button("제출하기", type="primary")

    # AI 모티프 태깅 (폼 밖)
    st.divider()
    st.markdown(f"""<div style="display:flex;align-items:center;gap:0.5rem;margin:1rem 0 0.4rem">
  {ICONS['AI']}<span style="font-size:1.1rem;font-weight:700;color:#4A2010;">AI 모티프 태깅 초안</span>
</div>""", unsafe_allow_html=True)
    st.caption("본문 입력 후 아래 버튼을 눌러 AI가 제안하는 모티프 초안을 확인하세요.")

    if 'motif_draft' not in st.session_state:
        st.session_state['motif_draft'] = ''

    motif_content = st.session_state.get('_draft_content', '')
    analyze_btn = st.button("모티프 분석하기")
    if analyze_btn:
        if not content or len(content) < 10:
            st.warning("본문을 먼저 입력하세요.")
        else:
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if not api_key:
                st.error(".env 파일에 ANTHROPIC_API_KEY를 설정하세요.")
            else:
                client = anthropic.Anthropic(api_key=api_key)
                prompt = f"""다음 설화 본문을 읽고 아래 JSON 형식으로 분석 결과를 반환하세요.

{{
  "motifs": ["모티프코드-설명", ...],
  "atu_types": ["ATU XXX", ...],
  "narrative_units": ["서사단락1", "서사단락2", ...],
  "structure": "서사구조 요약",
  "era": "시대"
}}

[설화 본문]:
{content}

JSON만 출력하고 다른 설명은 하지 마세요."""

                with st.spinner("AI가 분석 중입니다..."):
                    resp = client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=1024,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    raw = resp.content[0].text.strip()
                    # JSON 추출 (```json ... ``` 형식 처리)
                    if raw.startswith("```"):
                        raw = raw.split("```")[1]
                        if raw.startswith("json"):
                            raw = raw[4:]
                    st.session_state['motif_draft'] = raw.strip()
                    st.session_state['_draft_content'] = content

    if st.session_state['motif_draft']:
        st.markdown('<p class="ai-note">AI가 제안한 초안입니다. 검토 후 수정하세요.</p>', unsafe_allow_html=True)
        edited_draft = st.text_area("모티프 초안 (편집 가능)", st.session_state['motif_draft'], height=200)
        st.session_state['motif_draft'] = edited_draft

    # 제출 처리
    if submitted:
        errors = []
        if not title:
            errors.append("제목을 입력하세요.")
        if not region:
            errors.append("광역 지역을 입력하세요.")
        if not content or len(content) < 100:
            errors.append("본문을 100자 이상 입력하세요.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            data = {
                'title': title,
                'region': region,
                'district': district or '',
                'location': location or '',
                'narrator': narrator or '',
                'collected_date': str(collected_date) if collected_date else '',
                'content': content,
                'submitted_at': datetime.now().isoformat(),
                'motif_draft': st.session_state.get('motif_draft', ''),
            }
            insert_contribution(conn, data)
            st.success(f"설화 「{title}」이(가) 성공적으로 제출되었습니다.")
            st.session_state['motif_draft'] = ''
            st.session_state.pop('_draft_content', None)

# ── 기여 목록 탭 ──────────────────────────────────────────────────────────────
with tab_list:
    st.subheader("기여된 설화 목록")
    contribs = get_contributions(conn)
    if not contribs:
        st.info("아직 기여된 설화가 없습니다.")
    else:
        for c in contribs:
            c = dict(c)
            with st.expander(
                f"[기여] {c['title']} — {c['region']} {c.get('district','')} ({c['submitted_at'][:10]})"
            ):
                col_a, col_b = st.columns([3, 2])
                with col_a:
                    st.markdown(f"**제보자** {c.get('narrator','-')}")
                    st.markdown(f"**채록일** {c.get('collected_date','-')}")
                    st.markdown(f"**장소** {c.get('location','-')}")
                    content_preview = c.get('content', '')[:300]
                    st.write(content_preview + ("..." if len(c.get('content','')) > 300 else ""))
                with col_b:
                    if c.get('motif_draft'):
                        st.markdown("**AI 모티프 초안**")
                        try:
                            draft = json.loads(c['motif_draft'])
                            if draft.get('motifs'):
                                st.write("모티프:", ", ".join(draft['motifs']))
                            if draft.get('era'):
                                st.write("시대:", draft['era'])
                            if draft.get('structure'):
                                st.write("구조:", draft['structure'])
                        except Exception:
                            st.code(c['motif_draft'])
                    st.caption(
                        f"<span style='background:#EAB308;color:white;padding:2px 6px;"
                        f"border-radius:3px;font-size:0.8em'>기여 자료</span>",
                        unsafe_allow_html=True
                    )

conn.close()
