"""7a0_bot — Bot 100% Python para 7a0.com.br"""
from .constants import *
from .prng import make_rng, poisson_sample, simulate_match, calc_lambda, generate_goals
from .game import Game7a0, calc_team_stats, find_best_slot
from .online import OnlinePlayer, GhostPlayer, run_online_room, create_room, get_user_id
from .achievements import StrategyRotator, STRATEGY_ROTATION
