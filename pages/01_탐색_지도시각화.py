import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
import pandas as pd
import folium
from folium.plugins import FastMarkerCluster
from streamlit_folium import st_folium

st.set_page_config(page_title="탐색 — 지도 시각화", layout="wide")

DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'items_설화.csv'))

CATEGORY_COLORS = {
    "설화": "#3B82F6",
    "민요": "#22C55E",
    "무가": "#A855F7",
    "현대 구전설화": "#F97316",
}

# ── 데이터 로드 ────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH, dtype=str)
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lng'] = pd.to_numeric(df['lng'], errors='coerce')
    return df

@st.cache_data
def prepare_map_rows(cats: tuple):
    """FastMarkerCluster용 [lat, lng, color, title, id] 리스트 — 캐싱"""
    sub = df[df['category'].isin(cats)].dropna(subset=['lat', 'lng'])
    rows = []
    for _, r in sub.iterrows():
        color = CATEGORY_COLORS.get(r.get('category', ''), '#888888')
        rows.append([
            r['lat'], r['lng'], color,
            str(r.get('title', '(제목 없음)')),
            str(r.get('id', '')),
        ])
    return rows

df = load_data()

# ── 사이드바: 카테고리 필터 ────────────────────────────────────────────────────
st.sidebar.header("카테고리 필터")
selected_cats = []
for cat, color in CATEGORY_COLORS.items():
    if st.sidebar.checkbox(cat, value=True, key=f"cat_{cat}"):
        selected_cats.append(cat)

# ── 레이아웃 ──────────────────────────────────────────────────────────────────
st.title("🗺️ 탐색 — 지도 시각화")

map_col, info_col = st.columns([7, 3])

# ── 데이터 필터링 ──────────────────────────────────────────────────────────────
if selected_cats:
    filtered = df[df['category'].isin(selected_cats)]
else:
    filtered = df.iloc[0:0]

total = len(filtered)
no_coords = filtered[filtered['lat'].isna() | filtered['lng'].isna()]
has_coords = filtered.dropna(subset=['lat', 'lng'])

if len(no_coords) > 0:
    st.info(f"좌표 정보 없어 지도에서 제외된 자료: {len(no_coords)}건 (전체 {total}건 중)")

# ── 지도 생성 ──────────────────────────────────────────────────────────────────

# JS 콜백: 브라우저에서 직접 CircleMarker 렌더링 (FastMarkerCluster)
MARKER_CALLBACK = """
function(row) {
    var marker = L.circleMarker([row[0], row[1]], {
        radius: 6,
        color: row[2],
        fillColor: row[2],
        fillOpacity: 0.8,
        weight: 1.5
    });
    marker.bindPopup('<b>' + row[3] + '</b><br/><small>' + row[4] + '</small>');
    marker.bindTooltip(row[3], {sticky: true});
    return marker;
}
"""

with map_col:
    m = folium.Map(location=[36.5, 127.5], zoom_start=6, tiles="CartoDB positron")

    if selected_cats:
        map_rows = prepare_map_rows(tuple(selected_cats))
        if map_rows:
            FastMarkerCluster(data=map_rows, callback=MARKER_CALLBACK).add_to(m)

    map_data = st_folium(m, width="100%", height=600, returned_objects=["last_object_clicked_popup"])

# ── 클릭 이벤트 처리 ──────────────────────────────────────────────────────────
clicked_popup = map_data.get("last_object_clicked_popup") if map_data else None
if clicked_popup:
    # 팝업 HTML에서 id 추출
    import re
    match = re.search(r'<small>(.*?)</small>', str(clicked_popup))
    if match:
        st.session_state['selected_id'] = match.group(1)

# ── 우측 패널: 선택된 설화 정보 ──────────────────────────────────────────────
with info_col:
    selected_id = st.session_state.get('selected_id')
    if not selected_id:
        st.info("지도에서 자료를 클릭하세요")
    else:
        row = df[df['id'] == selected_id]
        if row.empty:
            st.warning("선택된 자료를 찾을 수 없습니다.")
        else:
            r = row.iloc[0]
            cat = r.get('category', '')
            color = CATEGORY_COLORS.get(cat, '#888888')

            st.markdown(f"### {r.get('title', '(제목 없음)')}")
            st.markdown(
                f"<span style='background:{color};color:white;padding:2px 8px;"
                f"border-radius:4px;font-size:0.85em'>{cat}</span>",
                unsafe_allow_html=True
            )

            st.markdown("---")
            region_str = " > ".join(filter(None, [
                str(r.get('region', '') or ''),
                str(r.get('district', '') or ''),
                str(r.get('location', '') or ''),
            ]))
            st.markdown(f"**지역** {region_str}")
            st.markdown(f"**조사일** {r.get('date', '-')}")
            st.markdown(f"**조사자** {r.get('collectors', '-')}")
            st.markdown(f"**제보자** {r.get('narrator', '-')}")

            context = str(r.get('context', '') or '')
            if context:
                st.markdown(f"**구연 상황** {context}")

            content = str(r.get('content', '') or '')
            if content:
                st.markdown("**본문 미리보기**")
                if len(content) > 200:
                    preview = content[:200] + "..."
                    with st.expander(preview):
                        st.write(content)
                else:
                    st.write(content)
            else:
                st.caption("본문 전사 없음")
