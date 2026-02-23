import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import math
import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

from utils.db import (
    get_conn,
    search_places_by_name, get_items_by_place_name,
    get_narrative_geo_pairs,
)

st.set_page_config(page_title="서사 지리 분석", layout="wide")
from utils.style import inject_css, page_title, ICONS
inject_css()
page_title("서사지리", "서사 지리 분석")

conn = get_conn()

# ── 유틸 ─────────────────────────────────────────────────────────────────────

def haversine_km(lat1, lng1, lat2, lng2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def dist_color(km):
    if km < 50:
        return "#16A34A"   # 녹색
    if km < 150:
        return "#D97706"   # 황색
    return "#DC2626"       # 적색


# ── 탭 ───────────────────────────────────────────────────────────────────────

tab_a, tab_b = st.tabs(["지명 역추적", "채록지–서사지 괴리"])

# ═══════════════════════════════════════════════════════════════════════════════
# Tab A : 지명 역추적
# ═══════════════════════════════════════════════════════════════════════════════
with tab_a:
    st.markdown(
        f"""<div style="display:flex;align-items:center;gap:0.5rem;margin:0.5rem 0 1rem">
  {ICONS['지명']}<span style="font-weight:700;color:#4A2010;font-size:1rem;">
  특정 지명이 등장하는 설화를 지도에서 확인합니다.</span>
</div>""",
        unsafe_allow_html=True,
    )

    kw = st.text_input("지명 검색", placeholder="예: 한라산, 금강산, 서울")

    if kw:
        place_rows = search_places_by_name(conn, kw)
        if not place_rows:
            st.info("해당 키워드로 지오코딩된 지명이 없습니다.")
        else:
            place_options = {r['place_name']: r for r in place_rows}
            selected_place = st.selectbox(
                "지명 선택",
                list(place_options.keys()),
                format_func=lambda n: f"{n}  ({place_options[n]['lat']:.3f}, {place_options[n]['lng']:.3f})",
            )

            if selected_place:
                pr = place_options[selected_place]
                items = get_items_by_place_name(conn, selected_place)

                st.caption(f"**{selected_place}** 을(를) 서사 지명으로 포함하는 설화 {len(items)}건")

                m = folium.Map(
                    location=[pr['lat'], pr['lng']],
                    zoom_start=7,
                    tiles="CartoDB positron",
                )

                # 지명 마커 (적색 별)
                folium.Marker(
                    location=[pr['lat'], pr['lng']],
                    icon=folium.Icon(color="red", icon="star", prefix="fa"),
                    tooltip=f"⭐ {selected_place}",
                    popup=selected_place,
                ).add_to(m)

                # 채록지 마커 클러스터
                cluster = MarkerCluster(name="채록지").add_to(m)
                for it in items:
                    if it['lat'] is None or it['lng'] is None:
                        continue
                    folium.CircleMarker(
                        location=[it['lat'], it['lng']],
                        radius=7,
                        color="#1D4ED8",
                        fill=True,
                        fill_color="#3B82F6",
                        fill_opacity=0.8,
                        tooltip=f"{it['title']} ({it['region']} {it['district']})",
                        popup=folium.Popup(
                            f"<b>{it['title']}</b><br>{it['region']} {it['district']}<br>"
                            f"<small>{it['category']}</small>",
                            max_width=220,
                        ),
                    ).add_to(cluster)

                legend = (
                    '<div style="font-size:0.8rem;color:#4A2010;margin:0.3rem 0;">'
                    '<span style="color:#DC2626">★</span> 서사 지명 &nbsp;'
                    '<span style="color:#3B82F6">●</span> 채록지'
                    '</div>'
                )
                st.markdown(legend, unsafe_allow_html=True)
                st_folium(m, width="100%", height=480, returned_objects=[])

                with st.expander("설화 목록"):
                    for it in items:
                        coord_str = f"{it['lat']:.4f}, {it['lng']:.4f}" if it['lat'] else "좌표 없음"
                        st.markdown(
                            f"- **{it['title']}** — {it['region']} {it['district']} "
                            f"<span style='color:#9A7A6A;font-size:0.8rem'>({coord_str})</span>",
                            unsafe_allow_html=True,
                        )

# ═══════════════════════════════════════════════════════════════════════════════
# Tab B : 채록지–서사지 괴리
# ═══════════════════════════════════════════════════════════════════════════════
with tab_b:
    st.markdown(
        """<div style="color:#4A2010;font-size:0.95rem;margin:0.5rem 0 1rem">
채록된 장소와 이야기 속 배경 지명 사이의 거리를 시각화합니다.<br>
<span style="color:#16A34A">●</span> 50km 미만 &nbsp;
<span style="color:#D97706">●</span> 50–150km &nbsp;
<span style="color:#DC2626">●</span> 150km 이상
</div>""",
        unsafe_allow_html=True,
    )

    regions = ["전체", "경기", "강원", "충청", "전라", "경상", "제주"]
    region_filter = st.selectbox("지역 필터", regions)

    region_arg = None if region_filter == "전체" else region_filter

    @st.cache_data(ttl=600)
    def load_pairs(region):
        rows = get_narrative_geo_pairs(conn, region=region, limit=500)
        return [dict(r) for r in rows]

    pairs = load_pairs(region_arg)

    if not pairs:
        st.info("해당 조건에 맞는 데이터가 없습니다.")
    else:
        dists = []
        for row in pairs:
            km = haversine_km(row['c_lat'], row['c_lng'], row['p_lat'], row['p_lng'])
            dists.append(km)

        n = len(dists)
        avg_km = sum(dists) / n
        max_km = max(dists)
        near = sum(1 for d in dists if d < 50)
        mid = sum(1 for d in dists if 50 <= d < 150)
        far = sum(1 for d in dists if d >= 150)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("분석 쌍", f"{n:,}건")
        col2.metric("평균 거리", f"{avg_km:.1f} km")
        col3.metric("최대 거리", f"{max_km:.1f} km")
        col4.metric("50km 미만 비율", f"{near/n*100:.0f}%")

        # 지도
        m2 = folium.Map(location=[36.5, 127.8], zoom_start=7, tiles="CartoDB positron")

        for row, km in zip(pairs, dists):
            color = dist_color(km)
            # 채록지
            folium.CircleMarker(
                location=[row['c_lat'], row['c_lng']],
                radius=4,
                color="#1D4ED8",
                fill=True,
                fill_color="#93C5FD",
                fill_opacity=0.6,
                tooltip=f"채록: {row['title']} ({row['region']})",
            ).add_to(m2)
            # 서사 지명
            folium.CircleMarker(
                location=[row['p_lat'], row['p_lng']],
                radius=4,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                tooltip=f"지명: {row['place_name']} ({km:.1f} km)",
            ).add_to(m2)
            # 연결선
            folium.PolyLine(
                locations=[[row['c_lat'], row['c_lng']], [row['p_lat'], row['p_lng']]],
                color=color,
                weight=1,
                opacity=0.45,
            ).add_to(m2)

        st_folium(m2, width="100%", height=520, returned_objects=[])

        st.markdown("---")
        st.markdown("**거리 분포**")
        bar_col1, bar_col2, bar_col3 = st.columns(3)
        bar_col1.metric("50km 미만 (일치)", f"{near}건 ({near/n*100:.0f}%)")
        bar_col2.metric("50–150km (근거리 괴리)", f"{mid}건 ({mid/n*100:.0f}%)")
        bar_col3.metric("150km 이상 (원거리 괴리)", f"{far}건 ({far/n*100:.0f}%)")

conn.close()
