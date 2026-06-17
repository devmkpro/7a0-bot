"""
PRNG seeded (MurmurHash3) + Poisson + simulação de partidas.

Port EXATO do JS do 7a0.com.br — módulos 89, 7794, 8860, 4440.
"""
import math
from .constants import TOURNAMENT


# ═══════════════════════════════════════════════════════════════════════════════
# MURMURHASH3-BASED SEEDED PRNG (module 89 — identical to JS)
# ═══════════════════════════════════════════════════════════════════════════════

def _murmurhash3_seed(seed_str: str) -> int:
    """MurmurHash3 initialization — exact JS port of _8() seed function."""
    h = (0x6a09e667 ^ len(seed_str)) & 0xFFFFFFFF
    for ch in seed_str:
        c = ord(ch)
        h = (h ^ c) & 0xFFFFFFFF
        h = (h * 0xcc9e2d51) & 0xFFFFFFFF
        h = ((h << 13) | (h >> 19)) & 0xFFFFFFFF
    return h & 0xFFFFFFFF


def make_rng(seed_str: str):
    """
    Create a seeded PRNG function [0,1) — exact JS port.

    JS source:
      let e = Math.imul((a = a + 0x6d2b79f5 | 0) ^ a >>> 15, 1 | a);
      return (((e = e + Math.imul(e ^ e >>> 7, 61 | e) ^ e) ^ e >>> 14) >>> 0) / 0x100000000;
    """
    state = _murmurhash3_seed(seed_str)

    def next_float():
        nonlocal state
        state = (state + 0x6d2b79f5) & 0xFFFFFFFF
        e = ((state ^ (state >> 15)) * (1 | state)) & 0xFFFFFFFF
        m = ((e ^ (e >> 7)) * (61 | e)) & 0xFFFFFFFF
        e = ((e + m) & 0xFFFFFFFF) ^ e
        e = (e ^ (e >> 14)) & 0xFFFFFFFF
        return e / 0x100000000

    return next_float


# ═══════════════════════════════════════════════════════════════════════════════
# POISSON DISTRIBUTION (module 7794)
# ═══════════════════════════════════════════════════════════════════════════════

def poisson_sample(rng, lam: float) -> int:
    """Sample from Poisson distribution — exact JS port."""
    if lam <= 0:
        return 0
    limit = math.exp(-lam)
    count = 0
    product = 1.0
    while True:
        count += 1
        product *= rng()
        if product <= limit:
            break
    return count - 1


# ═══════════════════════════════════════════════════════════════════════════════
# MATCH SIMULATION (module 8860 + 7794)
# ═══════════════════════════════════════════════════════════════════════════════

def calc_lambda(my_overall: int, opp_overall: int) -> float:
    """Calculate Poisson lambda from overalls — exact JS port."""
    base = TOURNAMENT["model"]["baseLambda"]
    slope = TOURNAMENT["model"]["slope"]
    min_l = TOURNAMENT["model"]["minLambda"]
    max_l = TOURNAMENT["model"]["maxLambda"]
    lam = base + (my_overall - opp_overall) * slope
    return max(min_l, min(max_l, lam))


def simulate_match(rng, my_overall: int, opp_overall: int) -> tuple:
    """Simulate a single match — returns (gf, ga, outcome)."""
    my_lam = calc_lambda(my_overall, opp_overall)
    opp_lam = calc_lambda(opp_overall, my_overall)
    gf = poisson_sample(rng, my_lam)
    ga = poisson_sample(rng, opp_lam)
    outcome = "V" if gf > ga else ("D" if gf == ga else "E")
    return gf, ga, outcome


# ═══════════════════════════════════════════════════════════════════════════════
# GOAL GENERATION (module 4440)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_goal_times(rng, count: int) -> list:
    """Generate unique minute marks for goals."""
    if count <= 0:
        return []
    minutes = set()
    while len(minutes) < count:
        m = 1 + int(90 * pow(rng(), 0.85))
        minutes.add(m)
    return sorted(minutes)


def generate_goals(rng, my_goals: int, my_squad: list, opp_overall: int) -> list:
    """Generate full match events (goals with scorers and minutes)."""
    events = []
    scorers = [p["name"] for p in my_squad if "GOL" not in p["positions"]]
    if not scorers:
        scorers = [p["name"] for p in my_squad]
    my_minutes = generate_goal_times(rng, my_goals)
    for i, m in enumerate(my_minutes):
        name = scorers[i % len(scorers)] if scorers else "?"
        events.append({"min": m, "scorer": name, "opp": False})
    return sorted(events, key=lambda e: e["min"])
