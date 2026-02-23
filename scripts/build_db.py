"""
CSV + JSONL → SQLite (data/folklore.db) 빌드 스크립트
실행: python scripts/build_db.py
"""
import sqlite3
import csv
import json
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CSV_PATH = os.path.join(ROOT_DIR, 'items_설화.csv')
JSONL_PATH = os.path.join(ROOT_DIR, 'motifs_merged.jsonl')
DB_PATH = os.path.join(ROOT_DIR, 'folklore.db')

DDL = """
CREATE TABLE IF NOT EXISTS items (
    id TEXT PRIMARY KEY,
    source TEXT, code TEXT, region TEXT, district TEXT,
    category TEXT, title TEXT, collectors TEXT, date TEXT,
    location TEXT, narrator TEXT, context TEXT, content TEXT,
    audio_file TEXT, lat REAL, lng REAL
);

CREATE TABLE IF NOT EXISTS motifs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    motif_code TEXT UNIQUE,
    motif_name TEXT
);

CREATE TABLE IF NOT EXISTS item_motifs (
    item_id TEXT REFERENCES items(id),
    motif_id INTEGER REFERENCES motifs(id)
);

CREATE TABLE IF NOT EXISTS atu_types (
    item_id TEXT REFERENCES items(id),
    atu_type TEXT
);

CREATE TABLE IF NOT EXISTS subjects (
    item_id TEXT REFERENCES items(id),
    subject TEXT
);

CREATE TABLE IF NOT EXISTS places (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    place_name TEXT UNIQUE,
    lat REAL,
    lng REAL,
    geocode_status TEXT
);

CREATE TABLE IF NOT EXISTS item_places (
    item_id TEXT REFERENCES items(id),
    place_id INTEGER REFERENCES places(id)
);

CREATE TABLE IF NOT EXISTS narrative_units (
    item_id TEXT REFERENCES items(id),
    unit_order INTEGER,
    unit_text TEXT
);

CREATE TABLE IF NOT EXISTS item_meta (
    item_id TEXT PRIMARY KEY REFERENCES items(id),
    structure TEXT,
    era TEXT
);

CREATE TABLE IF NOT EXISTS user_contributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    region TEXT,
    district TEXT,
    location TEXT,
    narrator TEXT,
    collected_date TEXT,
    content TEXT,
    submitted_at TEXT,
    motif_draft TEXT,
    status TEXT DEFAULT 'pending'
);
"""


def safe_float(val):
    try:
        return float(val) if val not in (None, '', 'None') else None
    except (ValueError, TypeError):
        return None


def load_csv(conn):
    cur = conn.cursor()
    print("Loading items_설화.csv ...")
    with open(CSV_PATH, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            rows.append((
                row.get('id'), row.get('source'), row.get('code'),
                row.get('region'), row.get('district'), row.get('category'),
                row.get('title'), row.get('collectors'), row.get('date'),
                row.get('location'), row.get('narrator'), row.get('context'),
                row.get('content'), row.get('audio_file'),
                safe_float(row.get('lat')), safe_float(row.get('lng')),
            ))
    cur.executemany(
        "INSERT OR REPLACE INTO items VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        rows
    )
    print(f"  → {len(rows)} items inserted")
    conn.commit()


def get_or_create_motif(cur, motif_str):
    """'D1711-도술 승려' 형식 파싱 → motifs 테이블에서 id 반환"""
    if '-' in motif_str:
        code, name = motif_str.split('-', 1)
        code = code.strip()
        name = name.strip()
    else:
        code = motif_str.strip()
        name = ''
    cur.execute("SELECT id FROM motifs WHERE motif_code = ?", (code,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO motifs (motif_code, motif_name) VALUES (?,?)", (code, name))
    return cur.lastrowid


def get_or_create_place(cur, place_dict):
    """place_coords 항목 → places 테이블에서 id 반환"""
    name = place_dict.get('name', '').strip()
    if not name:
        return None
    cur.execute("SELECT id FROM places WHERE place_name = ?", (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO places (place_name, lat, lng, geocode_status) VALUES (?,?,?,?)",
        (name, safe_float(place_dict.get('lat')), safe_float(place_dict.get('lng')),
         place_dict.get('status', 'failed'))
    )
    return cur.lastrowid


def load_jsonl(conn):
    cur = conn.cursor()
    print("Loading motifs_merged.jsonl ...")
    count = 0
    with open(JSONL_PATH, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            item_id = rec.get('id')
            if not item_id:
                continue

            # motifs
            for motif_str in rec.get('motifs', []):
                if not motif_str:
                    continue
                mid = get_or_create_motif(cur, motif_str)
                cur.execute(
                    "INSERT OR IGNORE INTO item_motifs (item_id, motif_id) VALUES (?,?)",
                    (item_id, mid)
                )

            # atu_types
            for atu in rec.get('atu_types', []):
                if atu:
                    cur.execute(
                        "INSERT INTO atu_types (item_id, atu_type) VALUES (?,?)",
                        (item_id, atu)
                    )

            # subjects
            for subj in rec.get('subjects', []):
                if subj:
                    cur.execute(
                        "INSERT INTO subjects (item_id, subject) VALUES (?,?)",
                        (item_id, subj)
                    )

            # place_coords
            for pc in rec.get('place_coords', []):
                pid = get_or_create_place(cur, pc)
                if pid:
                    cur.execute(
                        "INSERT OR IGNORE INTO item_places (item_id, place_id) VALUES (?,?)",
                        (item_id, pid)
                    )

            # narrative_units (list or string)
            nu = rec.get('narrative_units', '')
            if isinstance(nu, list):
                for i, unit in enumerate(nu):
                    if unit:
                        cur.execute(
                            "INSERT INTO narrative_units (item_id, unit_order, unit_text) VALUES (?,?,?)",
                            (item_id, i, unit)
                        )
            elif isinstance(nu, str) and nu.strip():
                cur.execute(
                    "INSERT INTO narrative_units (item_id, unit_order, unit_text) VALUES (?,?,?)",
                    (item_id, 0, nu.strip())
                )

            # item_meta (structure, era)
            structure = rec.get('structure', '')
            era = rec.get('era', '')
            if structure or era:
                cur.execute(
                    "INSERT OR REPLACE INTO item_meta (item_id, structure, era) VALUES (?,?,?)",
                    (item_id, structure, era)
                )

            count += 1
            if count % 5000 == 0:
                conn.commit()
                print(f"  {count} records processed...")

    conn.commit()
    print(f"  → {count} JSONL records processed")


def build_indexes(conn):
    cur = conn.cursor()
    print("Building indexes ...")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_items_region ON items(region)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_items_category ON items(category)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_item_motifs_item ON item_motifs(item_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_item_motifs_motif ON item_motifs(motif_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_atu_item ON atu_types(item_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_subjects_item ON subjects(item_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_places_name ON places(place_name)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_item_places_item ON item_places(item_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_nu_item ON narrative_units(item_id)")
    conn.commit()
    print("  → Done")


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript(DDL)
    conn.commit()

    load_csv(conn)
    load_jsonl(conn)
    build_indexes(conn)
    conn.close()
    print(f"\nDB built: {DB_PATH}")


if __name__ == '__main__':
    main()
