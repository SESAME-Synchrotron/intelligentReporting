#!/usr/bin/env python3
"""
Generate a one-line-per-table schema description from an SQLite database,
e.g.

    TABLE Album (AlbumId INTEGER PK, Title TEXT, ArtistId INTEGER FK→Artist.ArtistId)
"""

import sqlite3
import argparse
from collections import defaultdict
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
def load_fk_map(conn) -> dict:
    """
    Build  {table: {column: (ref_table, ref_column)}}  using PRAGMA foreign_key_list.
    """
    fk_map = defaultdict(dict)
    for (tbl_name,) in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ):
        for row in conn.execute(f"PRAGMA foreign_key_list('{tbl_name}')"):
            # rows: (id,seq,table,from,to,on_update,on_delete,match)
            _, _, ref_table, from_col, to_col, *_ = row
            fk_map[tbl_name][from_col] = (ref_table, to_col)
    return fk_map


def compact_schema(conn) -> str:
    fk_map = load_fk_map(conn)
    lines = []

    for (tbl_name,) in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ):
        cols_txt = []
        pk_cols = {row["name"] for row in conn.execute(f"PRAGMA table_info('{tbl_name}')") if row["pk"]}
        for row in conn.execute(f"PRAGMA table_info('{tbl_name}')"):
            col, ctype = row["name"], row["type"].upper() or "TEXT"
            notes = []
            if col in pk_cols:
                notes.append("PK")
            if col in fk_map[tbl_name]:
                ref_tbl, ref_col = fk_map[tbl_name][col]
                notes.append(f"FK→{ref_tbl}.{ref_col}")
            cols_txt.append(f"{col} {ctype}" + (f" {' '.join(notes)}" if notes else ""))
        lines.append(f"TABLE {tbl_name} ({', '.join(cols_txt)})")

    return "### SCHEMA\n" + "\n".join(lines) + "\n### END SCHEMA"


# ──────────────────────────────────────────────────────────────────────────────
def main(db_path: Path):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        print(compact_schema(conn))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dump compact schema for GPT prompts.")
    parser.add_argument(
    "-d", "--database",
    metavar="FILE",
    required=True,
    help="Path to the SQLite .db file",
)
    main(Path(parser.parse_args().database))
