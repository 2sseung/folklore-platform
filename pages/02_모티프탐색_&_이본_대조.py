import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
from dotenv import load_dotenv
import anthropic

import folium
from streamlit_folium import st_folium

from utils.db import (
    get_conn, get_item_by_id, search_items_by_title, search_items_by_motif,
    get_all_motifs, get_motifs_for_item, get_atu_types_for_item,
    get_subjects_for_item, get_narrative_units, get_item_meta,
    get_similar_items_by_motif, get_places_for_item,
)

load_dotenv()
st.set_page_config(page_title="모티프탐색 & 이본 대조", layout="wide")
from utils.style import inject_css, page_title, ICONS
inject_css()
page_title("이해", "모티프탐색 & 이본 대조")

conn = get_conn()

# ── 설화 선택 ─────────────────────────────────────────────────────────────────
st.subheader("설화 선택")
search_mode = st.radio("검색 방법", ["제목 검색", "모티프로 검색"], horizontal=True)

if search_mode == "제목 검색":
    keyword = st.text_input("제목 검색", placeholder="제목 키워드 입력")
    if keyword:
        results = search_items_by_title(conn, keyword)
    else:
        results = []
else:
    motifs = get_all_motifs(conn)
    motif_options = {f"{m['motif_code']} - {m['motif_name']}": m['motif_code'] for m in motifs}
    selected_motif_label = st.selectbox("모티프 선택", [""] + list(motif_options.keys()))
    if selected_motif_label:
        results = search_items_by_motif(conn, motif_options[selected_motif_label])
    else:
        results = []

if results:
    options = {f"[{r['id']}] {r['title']} ({r['region']} {r['district']})": r['id'] for r in results}
    selected_label = st.selectbox("설화 선택", [""] + list(options.keys()))
    if selected_label:
        st.session_state['focus_id'] = options[selected_label]

# ── 선택된 설화 상세 ──────────────────────────────────────────────────────────
focus_id = st.session_state.get('focus_id')
if not focus_id:
    st.info("위에서 설화를 선택하세요.")
    st.stop()

item = get_item_by_id(conn, focus_id)
if not item:
    st.error("설화를 찾을 수 없습니다.")
    st.stop()

item = dict(item)
meta = get_item_meta(conn, focus_id)
motifs = get_motifs_for_item(conn, focus_id)
atu_types = get_atu_types_for_item(conn, focus_id)
subjects = get_subjects_for_item(conn, focus_id)
nu_rows = get_narrative_units(conn, focus_id)
narrative_units = [r['unit_text'] for r in nu_rows]

st.divider()
st.subheader(item['title'])

meta_col, badge_col = st.columns([3, 2])
with meta_col:
    st.markdown(f"**지역** {item.get('region','')} {item.get('district','')} {item.get('location','')}")
    st.markdown(f"**제보자** {item.get('narrator', '-')}")
    if meta:
        st.markdown(f"**시대** {meta['era'] or '-'}")
        st.markdown(f"**서사 구조** {meta['structure'] or '-'}")

with badge_col:
    if motifs:
        st.markdown("**모티프**")
        for m in motifs:
            st.markdown(
                f"<span style='background:#3B82F6;color:white;padding:2px 6px;"
                f"border-radius:3px;font-size:0.8em;margin:2px;display:inline-block'>"
                f"{m['motif_code']} {m['motif_name']}</span>",
                unsafe_allow_html=True
            )
    if atu_types:
        st.markdown("**ATU 유형**")
        for a in atu_types:
            st.markdown(
                f"<span style='background:#8B5CF6;color:white;padding:2px 6px;"
                f"border-radius:3px;font-size:0.8em;margin:2px;display:inline-block'>"
                f"{a['atu_type']}</span>",
                unsafe_allow_html=True
            )
    if subjects:
        st.markdown("**주제어**")
        st.write(", ".join(s['subject'] for s in subjects))

# 본문
content = item.get('content', '') or ''
if content:
    with st.expander("본문 전문 보기", expanded=False):
        st.write(content)

# 서사 단락
if narrative_units:
    st.markdown("**서사 단락**")
    for i, unit in enumerate(narrative_units, 1):
        st.info(f"**{i}.** {unit}")

# ── 서사 지명 미니맵 ──────────────────────────────────────────────────────────
places = get_places_for_item(conn, focus_id)
geo_places = [p for p in places if p['lat'] is not None and p['lng'] is not None]
has_collect = item.get('lat') is not None and item.get('lng') is not None

if has_collect or geo_places:
    st.divider()
    st.markdown(f"""<div style="display:flex;align-items:center;gap:0.5rem;margin:1rem 0 0.5rem">
  {ICONS['서사지리']}<span style="font-size:1.1rem;font-weight:700;color:#4A2010;">채록지 · 서사 지명</span>
</div>""", unsafe_allow_html=True)

    all_lats = []
    all_lngs = []
    if has_collect:
        all_lats.append(item['lat']); all_lngs.append(item['lng'])
    for p in geo_places:
        all_lats.append(p['lat']); all_lngs.append(p['lng'])

    center = [sum(all_lats) / len(all_lats), sum(all_lngs) / len(all_lngs)]
    m = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron")

    if has_collect:
        folium.CircleMarker(
            location=[item['lat'], item['lng']],
            radius=8, color="#1D4ED8", fill=True, fill_color="#3B82F6", fill_opacity=0.85,
            tooltip=f"채록지: {item.get('location') or item.get('district') or ''}",
        ).add_to(m)

    for p in geo_places:
        folium.Marker(
            location=[p['lat'], p['lng']],
            icon=folium.DivIcon(html=(
                '<div style="font-size:18px;line-height:1;margin-top:-9px;margin-left:-9px">'
                '▲</div>'
            ), icon_size=(18, 18), icon_anchor=(9, 9)),
            tooltip=f"{ICONS['지명']} {p['place_name']}",
        ).add_to(m)
        if has_collect:
            folium.PolyLine(
                locations=[[item['lat'], item['lng']], [p['lat'], p['lng']]],
                color="#8B1A1A", weight=1.5, dash_array="6 4", opacity=0.5,
            ).add_to(m)

    legend_html = (
        '<div style="font-size:0.8rem;color:#4A2010;margin-top:0.3rem;">'
        '<span style="color:#3B82F6">●</span> 채록지 &nbsp;&nbsp;'
        '<span style="color:#8B1A1A">▲</span> 서사 지명'
        '</div>'
    )
    st.markdown(legend_html, unsafe_allow_html=True)
    st_folium(m, width="100%", height=320, returned_objects=[])

    if geo_places:
        with st.expander(f"서사 지명 목록 ({len(geo_places)}건 좌표 확인)"):
            for p in geo_places:
                status = p['geocode_status'] or ''
                st.markdown(
                    f"{ICONS['지명']} **{p['place_name']}** "
                    f"<span style='color:#9A7A6A;font-size:0.8rem'>({p['lat']:.4f}, {p['lng']:.4f}) {status}</span>",
                    unsafe_allow_html=True,
                )

# ── 이본 대조 ─────────────────────────────────────────────────────────────────
st.divider()
st.markdown(f"""<div style="display:flex;align-items:center;gap:0.5rem;margin:1rem 0 0.5rem">
  {ICONS['비교']}<span style="font-size:1.1rem;font-weight:700;color:#4A2010;">이본 대조</span>
</div>""", unsafe_allow_html=True)

similar = get_similar_items_by_motif(conn, focus_id)
if not similar:
    st.caption("공통 모티프를 공유하는 이본이 없습니다.")
else:
    st.markdown(f"공통 모티프 기준 유사 설화 {len(similar)}건")

    if 'compare_checked' not in st.session_state:
        st.session_state['compare_checked'] = []

    checked = []
    for sim in similar:
        sim = dict(sim)
        label = f"[{sim['id']}] {sim['title']} ({sim['region']} {sim['district']}) — 공통 모티프 {sim['common_motif_count']}개"
        if st.checkbox(label, key=f"sim_{sim['id']}"):
            checked.append(sim['id'])

    if len(checked) == 2:
        if st.button("대조 보기", type="primary"):
            st.session_state['compare_ids'] = checked

    elif len(checked) > 2:
        st.warning("2개만 선택하세요.")

compare_ids = st.session_state.get('compare_ids', [])
if len(compare_ids) == 2:
    c1, c2 = compare_ids
    item1 = dict(get_item_by_id(conn, c1) or {})
    item2 = dict(get_item_by_id(conn, c2) or {})
    nu1 = [r['unit_text'] for r in get_narrative_units(conn, c1)]
    nu2 = [r['unit_text'] for r in get_narrative_units(conn, c2)]

    st.divider()
    st.subheader("병렬 이본 대조")
    lcol, rcol = st.columns(2)
    with lcol:
        st.markdown(f"**{item1.get('title',c1)}**")
        st.caption(f"{item1.get('region','')} {item1.get('district','')}")
        if nu1:
            for i, u in enumerate(nu1, 1):
                st.info(f"**{i}.** {u}")
        else:
            st.write(item1.get('content', '본문 없음')[:500])
    with rcol:
        st.markdown(f"**{item2.get('title',c2)}**")
        st.caption(f"{item2.get('region','')} {item2.get('district','')}")
        if nu2:
            for i, u in enumerate(nu2, 1):
                st.info(f"**{i}.** {u}")
        else:
            st.write(item2.get('content', '본문 없음')[:500])

# ── LLM Q&A ──────────────────────────────────────────────────────────────────
st.divider()
st.markdown(f"""<div style="display:flex;align-items:center;gap:0.5rem;margin:1rem 0 0.5rem">
  {ICONS['AI']}<span style="font-size:1.1rem;font-weight:700;color:#4A2010;">AI 질의응답</span>
</div>""", unsafe_allow_html=True)

if not content:
    st.warning("본문 전사가 없는 자료입니다. Q&A 기능을 사용할 수 없습니다.")
else:
    if 'qa_history' not in st.session_state:
        st.session_state['qa_history'] = []

    for qa in st.session_state['qa_history']:
        with st.chat_message("user"):
            st.write(qa['q'])
        with st.chat_message("assistant"):
            st.write(qa['a'])

    question = st.chat_input("이 설화에 대해 질문하세요")
    if question:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            st.error(".env 파일에 ANTHROPIC_API_KEY를 설정하세요.")
        else:
            nu_text = "\n".join(f"{i+1}. {u}" for i, u in enumerate(narrative_units))
            system_prompt = f"""당신은 한국 구비문학 전문 연구 보조 AI입니다.
아래 설화 전사본을 바탕으로 사용자의 질문에 답하세요.
추측이나 외부 지식보다 본문 근거를 우선하세요.

[설화 제목]: {item['title']}
[전사본]: {content}
[서사 단락]: {nu_text}"""

            with st.chat_message("user"):
                st.write(question)

            with st.chat_message("assistant"):
                client = anthropic.Anthropic(api_key=api_key)

                def stream_response():
                    with client.messages.stream(
                        model="claude-sonnet-4-6",
                        max_tokens=1024,
                        system=system_prompt,
                        messages=[{"role": "user", "content": question}]
                    ) as stream:
                        for text in stream.text_stream:
                            yield text

                response = st.write_stream(stream_response())
                st.markdown('<p class="ai-note">AI 생성 응답으로 원본 전사본과 다를 수 있습니다</p>', unsafe_allow_html=True)
                st.session_state['qa_history'].append({'q': question, 'a': response})

conn.close()
