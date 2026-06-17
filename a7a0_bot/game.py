"""
Game engine solo — draft, simulação de torneio, submissão de resultado.

Game7a0 orquestra tudo: fetch de squads, draft inteligente, simulação
Poisson do torneio (grupos + mata-mata), e gravação via API.
"""
import json
import random
import re
import threading
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path

import requests

from .constants import (
    SQUAD_INDEX, TOURNAMENT, FORMATION_SLOTS,
    POSITION_ATTACK, POSITION_DEFENSE, POSITION_CATEGORY, POSITION_WEIGHT,
    CONMEBOL, UEFA, CAF, AFC, EXTINCT,
    COPAS_ATE_1970, COPAS_2010_MAIS,
    ACHIEVEMENT_MODES,
    get_confederation, get_decade,
)
from .prng import make_rng, simulate_match, generate_goals


# ═══════════════════════════════════════════════════════════════════════════════
# LOGGING (thread-safe)
# ═══════════════════════════════════════════════════════════════════════════════

_log_lock = threading.Lock()


def log(msg, thread_id: int = 0):
    ts = datetime.now().strftime("%H:%M:%S")
    prefix = f"[T{thread_id}]" if thread_id else "   "
    with _log_lock:
        print(f"[{ts}]{prefix} {msg}", flush=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PLAYER DRAFT HELPERS (module 6564)
# ═══════════════════════════════════════════════════════════════════════════════

LEGEND_GKS = {"rogerio-ceni", "jose-luis-chilavert", "rene-higuita"}


def find_best_slot(player: dict, slots: list, draft: list) -> int:
    """Find the best empty slot for a player based on position match."""
    best_slot = -1
    best_weight = -1
    for i, pos in enumerate(slots):
        if draft[i] is not None:
            continue
        if pos in player["positions"]:
            w = calc_slot_weight(player, pos)
            if w > best_weight:
                best_weight = w
                best_slot = i
    return best_slot


def calc_slot_weight(player: dict, position: str) -> float:
    """Calculate how well a player fits a position."""
    return POSITION_WEIGHT.get(POSITION_CATEGORY.get(position, ""), 0.1) * player["force"]


def calc_team_stats(draft: list, formation: str = "4-3-3") -> tuple:
    """Calculate team attack/defense/overall from draft — JS module 8397."""
    slots = FORMATION_SLOTS[formation]
    atk_sum = def_sum = total_force = count = 0
    for i, player in enumerate(draft):
        if player is None:
            continue
        pos = slots[i]
        atk_sum += player["force"] * POSITION_ATTACK.get(pos, 0)
        def_sum += player["force"] * POSITION_DEFENSE.get(pos, 0)
        total_force += player["force"]
        count += 1

    atk_base = sum(POSITION_ATTACK.get(pos, 0) for pos in slots)
    def_base = sum(POSITION_DEFENSE.get(pos, 0) for pos in slots)

    attack = round(atk_sum / atk_base) if atk_base > 0 else 0
    defense = round(def_sum / def_base) if def_base > 0 else 0
    overall = round(total_force / count) if count > 0 else 0
    return attack, defense, overall


# ═══════════════════════════════════════════════════════════════════════════════
# GAME ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class Game7a0:
    """Engine para partidas solo no 7a0.com.br (100% HTTP, sem navegador)."""

    FORMATIONS = ["4-3-3", "4-4-2", "4-2-3-1", "4-2-4", "3-5-2", "5-3-2", "4-5-1", "3-4-3"]
    MODES = ["clássico", "de almanaque"]

    def __init__(self, cookies: dict, user_agent: str = None):
        self.session = requests.Session()
        self.session.cookies.update(cookies)
        self.session.headers.update({
            "accept": "*/*",
            "accept-language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "referer": "https://7a0.com.br/play",
            "sec-ch-ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": user_agent or (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/149.0.0.0 Safari/537.36"
            ),
        })
        self.squad_cache = {}
        self._squad_cache_lock = threading.Lock()
        self.slug_map = {s["slug"]: s for s in SQUAD_INDEX}
        self.sel_copa_map = {(s["sel"], s["copa"]): s["slug"] for s in SQUAD_INDEX}
        self._player_index_map = self._load_player_index()
        self._game_count = 0

    # ── Player Index ──────────────────────────────────────────────────────────

    @staticmethod
    def _load_player_index() -> dict:
        """Load global player index from player_index.json.
        Returns dict: 'SEL:COPA:playerId' → int index.
        """
        index_path = Path(__file__).parent.parent / "player_index.json"
        if not index_path.exists():
            raise FileNotFoundError("player_index.json not found. Run extract_index.py first.")
        with open(index_path, encoding="utf-8") as f:
            arr = json.load(f)
        return {v: i for i, v in enumerate(arr)}

    def _get_player_index(self, sel, copa, player_id):
        return self._player_index_map.get(f"{sel}:{copa}:{player_id}", -1)

    # ── Squad Fetching ────────────────────────────────────────────────────────

    def fetch_squad(self, sel: str, copa: int) -> list:
        """Fetch squad JSON from server (thread-safe cache)."""
        key = f"{sel}:{copa}"
        with self._squad_cache_lock:
            if key in self.squad_cache:
                return self.squad_cache[key]

        slug = self.sel_copa_map.get((sel, copa))
        if not slug:
            raise ValueError(f"No squad found for {sel} {copa}")

        url = f"https://7a0.com.br/squads/{slug}.json"
        resp = self.session.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # Apply almanaque force modifier (module 6851)
        for p in data["squad"]:
            player_id = p.get("playerId", "")
            h = 0x811c9dc5
            salted = player_id + "7a0::alm::v1"
            for ch in salted:
                h ^= ord(ch)
                h = (h * 0x1000193) & 0xFFFFFFFF
            mask = h & 0xFF
            p["force"] = (p["f"] ^ mask) & 0xFF

        with self._squad_cache_lock:
            self.squad_cache[key] = data["squad"]
        return data["squad"]

    # ── Squad Selection ───────────────────────────────────────────────────────

    def pick_random_sel_copa(self, rng, recent=None) -> tuple:
        """Pick a random selection + World Cup — uniform random."""
        if recent is None:
            recent = set()
        candidates = [e for e in SQUAD_INDEX if f"{e['sel']}:{e['copa']}" not in recent]
        if not candidates:
            candidates = list(SQUAD_INDEX)
        idx = int(rng() * len(candidates))
        entry = candidates[idx % len(candidates)]
        return entry["sel"], entry["copa"]

    def pick_sel_copa_for_strategy(self, rng, recent: set, strategy: str,
                                    constraint_sel=None, constraint_copa=None,
                                    constraint_copas=None, constraint_decade=None,
                                    constraint_confed=None) -> tuple:
        """Versão constrangida do pick_random_sel_copa para conquistas de elenco."""
        pool = SQUAD_INDEX

        if strategy == "same_sel" and constraint_sel:
            pool = [e for e in pool if e["sel"] == constraint_sel]
        elif strategy == "same_copa" and constraint_copa:
            pool = [e for e in pool if e["copa"] == constraint_copa]
        elif strategy == "old_copas":
            pool = [e for e in pool if e["copa"] in COPAS_ATE_1970]
        elif strategy == "modern_copas":
            pool = [e for e in pool if e["copa"] in COPAS_2010_MAIS]
        elif strategy == "same_decade" and constraint_decade is not None:
            pool = [e for e in pool if get_decade(e["copa"]) == constraint_decade]
        elif strategy == "all_conmebol":
            pool = [e for e in pool if e["sel"] in CONMEBOL]
        elif strategy in ("outsider",):
            pool = [e for e in pool if e["sel"] not in UEFA and e["sel"] not in CONMEBOL]
        elif strategy == "african":
            pool = [e for e in pool if e["sel"] in CAF]
        elif strategy == "asian":
            pool = [e for e in pool if e["sel"] in AFC]
        elif strategy == "extinct5":
            pool = [e for e in pool if e["sel"] in EXTINCT]
        elif strategy == "best":
            TOP_SQUADS = [
                ("BRA", 1970), ("FRA", 1998), ("GER", 1974),
                ("NED", 1974), ("ITA", 1982), ("ARG", 1986),
                ("BRA", 1994), ("ESP", 2010), ("GER", 2014),
            ]
            for sel, copa in TOP_SQUADS:
                if f"{sel}:{copa}" not in recent:
                    if any(e["sel"] == sel and e["copa"] == copa for e in SQUAD_INDEX):
                        return sel, copa
            for sel, copa in TOP_SQUADS:
                if any(e["sel"] == sel and e["copa"] == copa for e in SQUAD_INDEX):
                    return sel, copa
        elif strategy == "worst":
            worst_sel, worst_copa, worst_avg = None, None, 999
            for e in SQUAD_INDEX:
                if f"{e['sel']}:{e['copa']}" in recent:
                    continue
                avg_force = e.get("avg_force", e.get("force", 75))
                if avg_force < worst_avg:
                    worst_avg = avg_force
                    worst_sel, worst_copa = e["sel"], e["copa"]
            if worst_sel:
                return worst_sel, worst_copa

        filtered = [e for e in pool if f"{e['sel']}:{e['copa']}" not in recent]
        if not filtered:
            filtered = list(pool) if pool else list(SQUAD_INDEX)
        if not filtered:
            return self.pick_random_sel_copa(rng, recent)

        idx = int(rng() * len(filtered))
        entry = filtered[idx % len(filtered)]
        return entry["sel"], entry["copa"]

    # ── Game Code / XI ────────────────────────────────────────────────────────

    @staticmethod
    def _to_base36(n: int) -> str:
        if n == 0:
            return "0"
        chars = "0123456789abcdefghijklmnopqrstuvwxyz"
        result = []
        while n > 0:
            result.append(chars[n % 36])
            n //= 36
        return "".join(reversed(result))

    def build_game_code(self, formation: str, mode: str, seed: str, filled_players: list) -> str:
        """Build the game code string that the server uses to replay/validate."""
        form_idx = self.FORMATIONS.index(formation) if formation in self.FORMATIONS else 0
        mode_idx = self.MODES.index(mode) if mode in self.MODES else 0
        rules = 3
        header = f"{form_idx}{mode_idx}{rules}"

        player_indices = []
        for p in filled_players:
            if p is None:
                player_indices.append("0")
                continue
            idx = self._get_player_index(p.get("sel", ""), p.get("copa", 0), p["playerId"])
            if idx < 0:
                log(f"   ⚠️ Player not in index: {p['playerId']}")
                idx = 0
            player_indices.append(self._to_base36(idx))

        return "-".join([header, seed] + player_indices)

    LEGENDS = frozenset({
        "pele", "maradona", "messi", "ronaldo", "c-ronaldo", "zidane",
        "cruyff", "beckenbauer", "platini", "puskas", "di-stefano",
        "eusebio", "muller-g", "garrincha", "rivald0", "ronaldinho",
        "rogerio-ceni", "jose-luis-chilavert", "rene-higuita",
    })

    def build_xi(self, draft, formation):
        """Build the xi array (player lineup with metadata) for ctx."""
        slots = FORMATION_SLOTS[formation]
        xi = []
        for i, p in enumerate(draft):
            if p is None:
                continue
            xi.append({
                "playerId": p["playerId"],
                "name": p["name"],
                "sel": p.get("sel", ""),
                "copa": p.get("copa", 0),
                "positions": p["positions"],
                "number": p["number"],
                "force": p["force"],
                "legend": p["playerId"] in self.LEGENDS,
            })
        return xi

    # ── Draft Helpers ─────────────────────────────────────────────────────────

    def pick_best_player(self, candidates, formation, draft, rng):
        """Escolhe o jogador que MAXIMIZA o overall do time."""
        slots = FORMATION_SLOTS[formation]
        best_player = None
        best_score = -1

        for p, _ in candidates:
            slot_idx = find_best_slot(p, slots, draft)
            if slot_idx < 0:
                continue
            test_draft = list(draft)
            test_draft[slot_idx] = p
            _, _, sim_overall = calc_team_stats(test_draft, formation)
            score = sim_overall * 1000 + p["force"]
            if score > best_score:
                best_score = score
                best_player = p
        return best_player

    def best_formation_for_draft(self, draft_players):
        """Calcula qual formação maximizaria o overall do time."""
        best_formation = "4-3-3"
        best_ovr = -1

        for formation, slots in FORMATION_SLOTS.items():
            test_draft = [None] * 11
            used = set()
            for i, pos in enumerate(slots):
                best_p = None
                best_f = -1
                for p in draft_players:
                    if p["playerId"] in used:
                        continue
                    if pos in p["positions"] and p["force"] > best_f:
                        best_f = p["force"]
                        best_p = p
                if best_p:
                    test_draft[i] = best_p
                    used.add(best_p["playerId"])
            _, _, ovr = calc_team_stats(test_draft, formation)
            if ovr > best_ovr:
                best_ovr = ovr
                best_formation = formation
        return best_formation, best_ovr

    # ── Play Full Game ────────────────────────────────────────────────────────

    def play_game(self, formation="4-3-3", style="Equilibrado", mode="Clássico",
                  strategy="normal"):
        """Play a complete solo game: draft → simulate tournament → record result."""
        # ── Mode auto-alternância ─────────────────────────────────────────
        if mode == "auto":
            self._game_count += 1
            mode = "De almanaque" if (self._game_count % 4 == 0) else "Clássico"
        if style == "auto":
            style = "Ofensivo"

        # ── Seed (identical to JS) ────────────────────────────────────────
        seed_raw = int(random.random() * 0xFFFFFFFF)
        seed = self._to_base36(seed_raw)[:16]
        salt = str(uuid.uuid4())[:16]
        rng = make_rng(f"{seed}:{salt}:roll:0")

        # ── Auto formation ────────────────────────────────────────────────
        auto_formation = (formation == "auto")
        if auto_formation:
            formation = "4-3-3"

        log(f"\n🎮 INICIANDO PARTIDA")
        log(f"   Seed: {seed}")
        log(f"   Formação: {formation} | Estilo: {style} | Modo: {mode}")

        # ── Strategy constraints ──────────────────────────────────────────
        constraint_sel = constraint_copa = constraint_decade = force_cap = None

        if strategy == "same_sel":
            sel_counts = Counter(e["sel"] for e in SQUAD_INDEX)
            constraint_sel = sel_counts.most_common(1)[0][0]
            log(f"   🎯 Estratégia same_sel: {constraint_sel}")
        elif strategy == "same_copa":
            copa_counts = Counter(e["copa"] for e in SQUAD_INDEX)
            constraint_copa = copa_counts.most_common(1)[0][0]
            log(f"   🎯 Estratégia same_copa: {constraint_copa}")
        elif strategy == "same_decade":
            decade_counts = Counter(get_decade(e["copa"]) for e in SQUAD_INDEX)
            constraint_decade = decade_counts.most_common(1)[0][0]
            log(f"   🎯 Estratégia same_decade: {constraint_decade}s")
        elif strategy == "dream_team":
            log(f"   🎯 Estratégia dream_team: force >= 85")
        elif strategy == "impossible":
            force_cap = 77
            log(f"   🎯 Estratégia impossible: force <= {force_cap}")
        elif strategy == "weak_team":
            force_cap = 79
            log(f"   🎯 Estratégia weak_team: force <= {force_cap}")

        # ── Draft Phase ───────────────────────────────────────────────────
        draft = [None] * 11
        used_players = set()
        recent_squads = set()
        roll_index = 0

        for slot_idx in range(11):
            roll_index += 1
            rng = make_rng(f"{seed}:{salt}:roll:{roll_index}")

            sel, copa = self.pick_sel_copa_for_strategy(
                rng, recent_squads, strategy,
                constraint_sel=constraint_sel,
                constraint_copa=constraint_copa,
                constraint_decade=constraint_decade,
            )
            recent_squads.add(f"{sel}:{copa}")
            if len(recent_squads) > 6:
                recent_squads = set(list(recent_squads)[-6:])

            squad = self.fetch_squad(sel, copa)
            for p in squad:
                p["sel"] = sel
                p["copa"] = copa

            log(f"   Roll {slot_idx+1}/11: {sel} {copa} ({len(squad)} jogadores)")

            available = [p for p in squad if p["playerId"] not in used_players]
            if not available:
                log(f"   ⚠️ Sem jogadores disponíveis")
                continue

            if force_cap is not None:
                available_capped = [p for p in available if p["force"] <= force_cap]
                if available_capped:
                    available = available_capped

            if strategy == "dream_team":
                available_strong = [p for p in available if p["force"] >= 85]
                if available_strong:
                    available = available_strong

            slots = FORMATION_SLOTS[formation]
            empty_positions = set(slots[i] for i in range(len(slots)) if draft[i] is None)

            candidates = []
            for p in available:
                can_fill = any(pos in p["positions"] for pos in empty_positions)
                if can_fill:
                    candidates.append((p, p["force"]))

            if not candidates:
                for p in available:
                    slot_i = find_best_slot(p, slots, draft)
                    if slot_i >= 0:
                        candidates.append((p, p["force"]))
                        break

            if not candidates:
                log(f"   ⚠️ Nenhum jogador encaixa nas vagas restantes")
                continue

            chosen = self.pick_best_player(candidates, formation, draft, rng)
            if chosen is None:
                chosen = candidates[0][0]

            best_slot = find_best_slot(chosen, slots, draft)
            if best_slot >= 0:
                draft[best_slot] = chosen
                used_players.add(chosen["playerId"])
                log(f"   → #{chosen['number']} {chosen['name']} ({'/'.join(chosen['positions'])}) force={chosen['force']} → {slots[best_slot]}")
            else:
                log(f"   ⚠️ {chosen['name']} não encaixa em nenhuma vaga vazia")

        # ── Auto-formation optimization ───────────────────────────────────
        draft_players = [p for p in draft if p is not None]
        if auto_formation and draft_players:
            best_form, best_ovr_auto = self.best_formation_for_draft(draft_players)
            if best_form != formation:
                log(f"   🔄 Formação otimizada: {formation} → {best_form} (OVR {best_ovr_auto})")
            formation = best_form

            slots = FORMATION_SLOTS[formation]
            new_draft = [None] * 11
            used = set()
            sorted_players = sorted(draft_players, key=lambda p: -p["force"])
            for p in sorted_players:
                best_s = -1
                best_w = -1
                for i, pos in enumerate(slots):
                    if new_draft[i] is not None:
                        continue
                    if pos in p["positions"]:
                        w = p["force"]
                        if w > best_w:
                            best_w = w
                            best_s = i
                if best_s >= 0:
                    new_draft[best_s] = p
                    used.add(p["playerId"])
            for p in sorted_players:
                if p["playerId"] in used:
                    continue
                for i in range(11):
                    if new_draft[i] is None:
                        new_draft[i] = p
                        used.add(p["playerId"])
                        break
            draft = new_draft

        # ── Calculate Team Stats ──────────────────────────────────────────
        attack, defense, overall = calc_team_stats(draft, formation)
        game_code = self.build_game_code(formation, mode, seed, draft)

        log(f"\n📊 Time montado — ATK:{attack} DEF:{defense} OVR:{overall}")
        log(f"   Formacao final: {formation}")
        log(f"   Code: {game_code}")
        for i, p in enumerate(draft):
            pos = FORMATION_SLOTS[formation][i]
            if p:
                log(f"   {pos}: #{p['number']} {p['name']} ({p['force']})")

        # ── Tournament Simulation ─────────────────────────────────────────
        campaign = []
        group_points = group_gf = group_ga = 0
        eliminated = False

        for phase_info in TOURNAMENT["phases"]:
            if phase_info["type"] == "group":
                for opp_info in phase_info["opponents"]:
                    if eliminated:
                        break
                    opp_ovr = opp_info["overall"]
                    gf, ga, outcome = simulate_match(rng, overall, opp_ovr)
                    group_points += {"V": 3, "D": 1, "E": 0}[outcome]
                    group_gf += gf
                    group_ga += ga
                    advanced = group_points >= 4 or (group_points >= 3 and group_gf - group_ga > 0)
                    campaign.append({
                        "phase": phase_info["key"],
                        "opp": opp_info["label"],
                        "oppOverall": opp_ovr,
                        "gf": gf, "ga": ga,
                        "outcome": outcome,
                        "advanced": advanced if phase_info["key"] == "GRUPOS" and opp_info == phase_info["opponents"][-1] else (outcome != "E"),
                    })
                    if phase_info["key"] == "GRUPOS" and opp_info == phase_info["opponents"][-1]:
                        if not advanced:
                            eliminated = True
            else:
                if eliminated:
                    break
                opp_info = phase_info["opponent"]
                opp_ovr = opp_info["overall"]
                gf, ga, outcome = simulate_match(rng, overall, opp_ovr)
                if outcome == "D":
                    pen_cfg = TOURNAMENT["penalty"]
                    pen_base = pen_cfg["base"] + (overall - opp_ovr) * pen_cfg["slope"]
                    pen_base = max(pen_cfg["min"], min(pen_cfg["max"], pen_base))
                    my_pens = sum(1 for _ in range(5) if rng() < pen_base)
                    opp_pens = sum(1 for _ in range(5) if rng() < (1 - pen_base))
                    while my_pens == opp_pens:
                        my_pens += 1 if rng() < pen_base else 0
                        opp_pens += 1 if rng() < (1 - pen_base) else 0
                    advanced = my_pens > opp_pens
                    campaign.append({
                        "phase": phase_info["key"],
                        "opp": opp_info["label"],
                        "oppOverall": opp_ovr,
                        "gf": gf, "ga": ga,
                        "outcome": "E",
                        "advanced": advanced,
                        "penalties": True,
                    })
                else:
                    advanced = outcome == "V"
                    campaign.append({
                        "phase": phase_info["key"],
                        "opp": opp_info["label"],
                        "oppOverall": opp_ovr,
                        "gf": gf, "ga": ga,
                        "outcome": outcome,
                        "advanced": advanced,
                    })
                if not advanced:
                    eliminated = True

        # ── Results ───────────────────────────────────────────────────────
        wins = sum(1 for c in campaign if c["outcome"] == "V")
        losses = sum(1 for c in campaign if c["outcome"] == "E")
        draws = sum(1 for c in campaign if c["outcome"] == "D")
        total_gf = sum(c["gf"] for c in campaign)
        total_ga = sum(c["ga"] for c in campaign)
        champion = campaign[-1]["phase"] == "FINAL" and campaign[-1]["advanced"] if campaign else False
        seven_zero = any(c["gf"] - c["ga"] >= 7 for c in campaign)
        unbeaten = losses == 0

        badge = None
        if total_gf - total_ga >= TOURNAMENT["badge"]["esmagadorGD"]:
            badge = "ESMAGADOR DE RECORDES"
        elif unbeaten and champion:
            badge = "MURALHA"

        log(f"\n{'🏆' if champion else '📋'} RESULTADO: {wins}V {draws}D {losses}E | GF:{total_gf} GA:{total_ga}")
        if champion:
            log(f"   🏆 CAMPEÃO!")
        if badge:
            log(f"   🏅 {badge}")

        # ── Record Match via API ──────────────────────────────────────────
        summary = {
            "wins": wins, "gf": total_gf, "ga": total_ga,
            "champion": champion, "sevenZero": seven_zero,
            "unbeaten": unbeaten, "badge": badge,
            "isOnlineWin": False,
        }
        filled_players = [p for p in draft if p is not None]
        game_code = self.build_game_code(formation, mode, seed, draft)
        xi = self.build_xi(draft, formation)

        match_ctx = {
            "mode": "solo",
            "almanaque": mode.lower() == "de almanaque",
            "champion": champion,
            "unbeaten": unbeaten,
            "humansInRoom": 1,
            "oppHumanInFinal": False,
            "isHost": True,
            "matches": [
                {
                    "phase": c["phase"],
                    "gf": c["gf"],
                    "ga": c["ga"],
                    "advanced": c["advanced"],
                    "penalties": c.get("penalties", False),
                    "oppOverall": c["oppOverall"],
                    "oppHuman": False,
                    "goals": c.get("goals", []),
                }
                for c in campaign
            ],
        }

        request_id = str(uuid.uuid4())
        record_body = {
            "kind": "solo",
            "summary": summary,
            "ctx": {"xi": xi, "match": match_ctx},
            "requestId": request_id,
            "replay": json.dumps({"code": game_code}),
        }

        unlocked_list = []
        try:
            resp = self.session.post(
                "https://7a0.com.br/api/match/record",
                json=record_body,
                headers={"content-type": "application/json"},
                timeout=10,
            )
            if resp.ok:
                data = resp.json()
                unlocked_list = data.get("unlocked", [])
                if unlocked_list:
                    log(f"   CONQUISTAS: {', '.join(unlocked_list)}")
                log(f"   OK Resultado gravado!")
            else:
                log(f"   ERRO ao gravar: {resp.status_code} {resp.text[:100]}")
        except Exception as e:
            log(f"   ERRO de rede: {e}")

        return {
            "seed": seed, "formation": formation, "style": style, "mode": mode,
            "draft": [{"name": p["name"], "pos": FORMATION_SLOTS[formation][i], "force": p["force"]}
                      for i, p in enumerate(draft) if p],
            "attack": attack, "defense": defense, "overall": overall,
            "campaign": campaign, "champion": champion,
            "wins": wins, "gf": total_gf, "ga": total_ga,
            "unlocked": unlocked_list,
            "strategy": strategy,
        }
