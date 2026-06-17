"""
Registro de partidas em SQLite — substitui os JSONs soltos.

Tabelas:
    solo_games   — partidas offline (draft + torneio + resultado)
    online_games — partidas online (sala + ghost + resultado)
"""
import sqlite3
import json
import threading
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "7a0_history.db"

_local = threading.local()


def _conn() -> sqlite3.Connection:
    """Conexão thread-local com o banco."""
    if not hasattr(_local, "conn"):
        _local.conn = sqlite3.connect(str(DB_PATH), timeout=10)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
    return _local.conn


def init_db():
    """Cria as tabelas se não existem."""
    conn = _conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS solo_games (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            played_at   TEXT NOT NULL DEFAULT (datetime('now')),
            seed        TEXT,
            formation   TEXT,
            style       TEXT,
            mode        TEXT,
            strategy    TEXT,
            overall     INTEGER,
            attack      INTEGER,
            defense     INTEGER,
            wins        INTEGER,
            draws       INTEGER,
            losses      INTEGER,
            gf          INTEGER,
            ga          INTEGER,
            champion    INTEGER DEFAULT 0,
            badge       TEXT,
            unlocked    TEXT,
            campaign    TEXT,
            draft       TEXT
        );

        CREATE TABLE IF NOT EXISTS online_games (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            played_at   TEXT NOT NULL DEFAULT (datetime('now')),
            room_code   TEXT,
            seed        TEXT,
            success     INTEGER DEFAULT 0,
            ghost_count INTEGER DEFAULT 1,
            game_mode   TEXT,
            host_strat  TEXT,
            ghost_strat TEXT,
            result_json TEXT,
            error       TEXT
        );

        CREATE INDEX IF NOT EXISTS ix_solo_champion ON solo_games(champion);
        CREATE INDEX IF NOT EXISTS ix_solo_strategy ON solo_games(strategy);
        CREATE INDEX IF NOT EXISTS ix_online_success ON online_games(success);
        CREATE INDEX IF NOT EXISTS ix_online_room ON online_games(room_code);
    """)
    conn.commit()


def record_solo(result: dict):
    """Registra uma partida solo."""
    conn = _conn()
    campaign = result.get("campaign", [])
    draws = sum(1 for c in campaign if c["outcome"] == "D")
    losses = sum(1 for c in campaign if c["outcome"] == "E")

    conn.execute("""
        INSERT INTO solo_games
            (seed, formation, style, mode, strategy, overall, attack, defense,
             wins, draws, losses, gf, ga, champion, badge, unlocked, campaign, draft)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        result.get("seed"),
        result.get("formation"),
        result.get("style"),
        result.get("mode"),
        result.get("strategy"),
        result.get("overall"),
        result.get("attack"),
        result.get("defense"),
        result.get("wins"),
        draws,
        losses,
        result.get("gf"),
        result.get("ga"),
        1 if result.get("champion") else 0,
        result.get("badge"),
        json.dumps(result.get("unlocked", []), ensure_ascii=False),
        json.dumps(campaign, ensure_ascii=False),
        json.dumps(result.get("draft", []), ensure_ascii=False),
    ))
    conn.commit()


def record_online(room_code: str, seed: str, success: bool,
                  ghost_count: int = 1, game_mode: str = "classico",
                  host_strat: str = "best", ghost_strat: str = "worst",
                  result_json: str = None, error: str = None):
    """Registra uma partida online."""
    conn = _conn()
    conn.execute("""
        INSERT INTO online_games
            (room_code, seed, success, ghost_count, game_mode,
             host_strat, ghost_strat, result_json, error)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        room_code, seed, 1 if success else 0,
        ghost_count, game_mode, host_strat, ghost_strat,
        result_json, error,
    ))
    conn.commit()


def get_stats() -> dict:
    """Retorna estatísticas gerais."""
    conn = _conn()

    solo = conn.execute("""
        SELECT COUNT(*) as total,
               SUM(champion) as champs,
               SUM(wins) as total_wins,
               SUM(gf) as total_gf,
               SUM(ga) as total_ga
        FROM solo_games
    """).fetchone()

    online = conn.execute("""
        SELECT COUNT(*) as total,
               SUM(success) as wins
        FROM online_games
    """).fetchone()

    return {
        "solo": {
            "total": solo["total"] or 0,
            "champions": solo["champs"] or 0,
            "wins": solo["total_wins"] or 0,
            "gf": solo["total_gf"] or 0,
            "ga": solo["total_ga"] or 0,
        },
        "online": {
            "total": online["total"] or 0,
            "wins": online["wins"] or 0,
        },
    }


def print_stats():
    """Imprime resumo das estatísticas."""
    s = get_stats()
    solo = s["solo"]
    onl = s["online"]

    print(f"\n{'='*60}")
    print(f"  HISTÓRICO — {DB_PATH.name}")
    print(f"{'='*60}")
    print(f"  OFFLINE")
    print(f"    Partidas  : {solo['total']}")
    print(f"    Campeoes  : {solo['champions']}")
    print(f"    Vitorias  : {solo['wins']}")
    print(f"    GF / GA   : {solo['gf']} / {solo['ga']}")
    print(f"  ONLINE")
    print(f"    Partidas  : {onl['total']}")
    print(f"    Vitorias  : {onl['wins']}")
    print(f"{'='*60}")
