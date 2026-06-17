"""
Rotação de estratégias para conquistas (achievements).

StrategyRotator é thread-safe e compartilhado entre workers.
"""
import threading
from .game import log


# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY ROTATION — sequência para cobrir todas as conquistas pendentes
# ═══════════════════════════════════════════════════════════════════════════════

STRATEGY_ROTATION = [
    ("same_copa",    "Era de ouro (XI da mesma Copa)",          8),
    ("same_sel",     "Patriota (XI da mesma seleção)",          8),
    ("dream_team",   "Dream Team (force 85+)",                  8),
    ("old_copas",    "Saudosista (até 1970)",                   8),
    ("modern_copas", "Moderninho (2010+)",                      8),
    ("same_decade",  "Contemporâneos (mesma década)",           8),
    ("all_conmebol", "Conmebol total",                          8),
    ("brasil5",      "Canarinho (5+ BRA)",                      5),
    ("african",      "Zebra africana (5+ CAF)",                 8),
    ("asian",        "Zebra asiática (5+ AFC)",                 8),
    ("outsider",     "Outsider (5+ fora UEFA/CONMEBOL)",        8),
    ("extinct5",     "Cortina de ferro (5+ extintas)",          8),
    ("impossible",   "O impossível (invicto, force<78)",       15),
    ("normal",       "Normal (títulos + conquistas de placar)", 20),
]


class StrategyRotator:
    """Rotaciona estratégias para cobrir todas as conquistas pendentes."""

    def __init__(self):
        self._idx = 0
        self._attempts = 0
        self._lock = threading.Lock()

    def next(self) -> tuple:
        """Retorna (strategy, description)."""
        with self._lock:
            if self._idx >= len(STRATEGY_ROTATION):
                self._idx = len(STRATEGY_ROTATION) - 1

            strat, desc, max_att = STRATEGY_ROTATION[self._idx]
            self._attempts += 1

            if self._attempts >= max_att:
                self._attempts = 0
                self._idx += 1
                if self._idx >= len(STRATEGY_ROTATION):
                    self._idx = 0

            return strat, desc

    def report_unlock(self, achievement_name: str):
        """Quando uma conquista é desbloqueada, avança para a próxima estratégia."""
        with self._lock:
            self._attempts = 0
            self._idx += 1
            if self._idx >= len(STRATEGY_ROTATION):
                self._idx = 0
            log(f"   🎯 Conquista obtida! Próxima estratégia: {STRATEGY_ROTATION[self._idx][1]}")


# Instância global compartilhada entre threads
_global_rotator = StrategyRotator()
