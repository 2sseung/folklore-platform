"""
공통 DB 연결 및 쿼리 유틸리티
"""
import sqlite3
import os
from functools import lru_cache

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'folklore.db'))


def ensure_db():
    """DB가 없으면 build_db.py를 실행해 생성한다."""
    if os.path.exists(DB_PATH):
        return
    import subprocess, sys
    scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
    build_script = os.path.join(scripts_dir, 'build_db.py')
    subprocess.run([sys.executable, build_script], check=True)


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# ─── items ───────────────────────────────────────────────────────────────────

def get_all_items(conn, categories=None):
    """카테고리 필터링된 전체 items 반환 (지도용)"""
    if categories:
        placeholders = ','.join('?' * len(categories))
        sql = f"SELECT id, title, category, region, district, location, lat, lng FROM items WHERE category IN ({placeholders})"
        return conn.execute(sql, categories).fetchall()
    return conn.execute(
        "SELECT id, title, category, region, district, location, lat, lng FROM items"
    ).fetchall()


def get_item_by_id(conn, item_id):
    return conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()


def search_items_by_title(conn, keyword, limit=50):
    return conn.execute(
        "SELECT id, title, region, district, category FROM items WHERE title LIKE ? LIMIT ?",
        (f'%{keyword}%', limit)
    ).fetchall()


def search_items_by_motif(conn, motif_code, limit=50):
    return conn.execute("""
        SELECT i.id, i.title, i.region, i.district, i.category
        FROM items i
        JOIN item_motifs im ON i.id = im.item_id
        JOIN motifs m ON im.motif_id = m.id
        WHERE m.motif_code = ?
        LIMIT ?
    """, (motif_code, limit)).fetchall()


def get_items_with_lat_lng(conn, categories=None):
    """lat/lng 있는 items만 반환"""
    if categories:
        placeholders = ','.join('?' * len(categories))
        sql = f"""
            SELECT id, title, category, region, district, location, lat, lng
            FROM items
            WHERE lat IS NOT NULL AND lng IS NOT NULL AND category IN ({placeholders})
        """
        return conn.execute(sql, categories).fetchall()
    return conn.execute("""
        SELECT id, title, category, region, district, location, lat, lng
        FROM items WHERE lat IS NOT NULL AND lng IS NOT NULL
    """).fetchall()


def count_items_without_coords(conn, categories=None):
    if categories:
        placeholders = ','.join('?' * len(categories))
        sql = f"SELECT COUNT(*) FROM items WHERE (lat IS NULL OR lng IS NULL) AND category IN ({placeholders})"
        return conn.execute(sql, categories).fetchone()[0]
    return conn.execute(
        "SELECT COUNT(*) FROM items WHERE lat IS NULL OR lng IS NULL"
    ).fetchone()[0]


# ─── motifs ──────────────────────────────────────────────────────────────────

def get_motifs_for_item(conn, item_id):
    return conn.execute("""
        SELECT m.motif_code, m.motif_name
        FROM motifs m
        JOIN item_motifs im ON m.id = im.motif_id
        WHERE im.item_id = ?
    """, (item_id,)).fetchall()


def get_all_motifs(conn):
    return conn.execute("SELECT motif_code, motif_name FROM motifs ORDER BY motif_code").fetchall()


def get_atu_types_for_item(conn, item_id):
    return conn.execute(
        "SELECT atu_type FROM atu_types WHERE item_id = ?", (item_id,)
    ).fetchall()


def get_subjects_for_item(conn, item_id):
    return conn.execute(
        "SELECT subject FROM subjects WHERE item_id = ?", (item_id,)
    ).fetchall()


# ─── narrative_units ─────────────────────────────────────────────────────────

def get_narrative_units(conn, item_id):
    return conn.execute(
        "SELECT unit_text FROM narrative_units WHERE item_id = ? ORDER BY unit_order",
        (item_id,)
    ).fetchall()


# ─── item_meta ───────────────────────────────────────────────────────────────

def get_item_meta(conn, item_id):
    return conn.execute(
        "SELECT structure, era FROM item_meta WHERE item_id = ?", (item_id,)
    ).fetchone()


# ─── places ──────────────────────────────────────────────────────────────────

def get_places_for_item(conn, item_id):
    return conn.execute("""
        SELECT p.place_name, p.lat, p.lng, p.geocode_status
        FROM places p
        JOIN item_places ip ON p.id = ip.place_id
        WHERE ip.item_id = ?
    """, (item_id,)).fetchall()


def search_places_by_name(conn, keyword, limit=30):
    return conn.execute(
        "SELECT place_name, lat, lng FROM places WHERE place_name LIKE ? AND lat IS NOT NULL AND lng IS NOT NULL LIMIT ?",
        (f'%{keyword}%', limit)
    ).fetchall()


def get_items_by_place_name(conn, place_name, limit=200):
    return conn.execute("""
        SELECT i.id, i.title, i.region, i.district, i.category, i.lat, i.lng
        FROM items i
        JOIN item_places ip ON i.id = ip.item_id
        JOIN places p ON ip.place_id = p.id
        WHERE p.place_name = ?
        LIMIT ?
    """, (place_name, limit)).fetchall()


def get_narrative_geo_pairs(conn, region=None, limit=400):
    """채록지 + 서사 지명 좌표 쌍 (둘 다 있는 경우)"""
    if region:
        return conn.execute("""
            SELECT i.id, i.title, i.region, i.district,
                   i.lat AS c_lat, i.lng AS c_lng,
                   p.place_name, p.lat AS p_lat, p.lng AS p_lng
            FROM items i
            JOIN item_places ip ON i.id = ip.item_id
            JOIN places p ON ip.place_id = p.id
            WHERE i.lat IS NOT NULL AND i.lng IS NOT NULL
              AND p.lat IS NOT NULL AND p.lng IS NOT NULL
              AND i.region LIKE ?
            LIMIT ?
        """, (f'%{region}%', limit)).fetchall()
    return conn.execute("""
        SELECT i.id, i.title, i.region, i.district,
               i.lat AS c_lat, i.lng AS c_lng,
               p.place_name, p.lat AS p_lat, p.lng AS p_lng
        FROM items i
        JOIN item_places ip ON i.id = ip.item_id
        JOIN places p ON ip.place_id = p.id
        WHERE i.lat IS NOT NULL AND i.lng IS NOT NULL
          AND p.lat IS NOT NULL AND p.lng IS NOT NULL
        LIMIT ?
    """, (limit,)).fetchall()


# ─── 이본 대조 ────────────────────────────────────────────────────────────────

def get_similar_items_by_motif(conn, item_id, limit=20):
    """공통 모티프 수 내림차순으로 이본 반환"""
    return conn.execute("""
        SELECT i.id, i.title, i.region, i.district, COUNT(*) AS common_motif_count
        FROM items i
        JOIN item_motifs im ON i.id = im.item_id
        WHERE im.motif_id IN (
            SELECT motif_id FROM item_motifs WHERE item_id = ?
        )
        AND i.id != ?
        GROUP BY i.id
        ORDER BY common_motif_count DESC
        LIMIT ?
    """, (item_id, item_id, limit)).fetchall()


# ─── user_contributions ──────────────────────────────────────────────────────

def insert_contribution(conn, data: dict):
    conn.execute("""
        INSERT INTO user_contributions
            (title, region, district, location, narrator, collected_date, content, submitted_at, motif_draft, status)
        VALUES (?,?,?,?,?,?,?,?,?, 'pending')
    """, (
        data.get('title'), data.get('region'), data.get('district'),
        data.get('location'), data.get('narrator'), data.get('collected_date'),
        data.get('content'), data.get('submitted_at'), data.get('motif_draft'),
    ))
    conn.commit()


def get_contributions(conn):
    return conn.execute(
        "SELECT * FROM user_contributions ORDER BY submitted_at DESC"
    ).fetchall()


def get_contribution_map_items(conn):
    """기여 설화 중 lat/lng 있는 것 (motif_draft에서 파싱 불필요, items 레이어와 구분용)"""
    return conn.execute("""
        SELECT id, title, region, district, location, submitted_at
        FROM user_contributions
    """).fetchall()
