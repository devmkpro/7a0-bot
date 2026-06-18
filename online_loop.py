#!/usr/bin/env python3
"""
Loop de vitórias online MULTI-THREAD — 100% Python, sem navegador.

Cria N salas simultâneas, cada uma com seus ghosts, draft completo,
REVEAL_AT, submissão de resultado. Resultados salvos em SQLite.

Uso:
    python online_loop.py                        # 3 threads, infinito
    python online_loop.py --threads 5            # 5 salas paralelas
    python online_loop.py --games 20 --threads 4 # 20 partidas em 4 threads
    python online_loop.py --ghost 3              # 3 ghosts por sala
    python online_loop.py --ghost-strat best     # ghosts fortes
"""
import argparse
import json
import os
import random
import sys
import threading
import time
from pathlib import Path

# ── .env loader ──────────────────────────────────────────────────────────────
_env_path = Path('.env')
if _env_path.exists():
    for line in _env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, _, v = line.partition('=')
            os.environ.setdefault(k.strip(), v.strip())

from a7a0_bot.online import run_online_room
from a7a0_bot.game import log
from a7a0_bot.database import init_db, record_online, print_stats


# ═══════════════════════════════════════════════════════════════════════════════
# WORKER ONLINE — roda N partidas online numa thread dedicada
# ═══════════════════════════════════════════════════════════════════════════════

def online_worker(
    thread_id: int,
    n_games: int,
    cookies: dict,
    n_ghosts: int,
    game_mode: str,
    turn_seconds: int,
    formation: str,
    host_strategy: str,
    ghost_strategy: str,
    verbose: bool,
    stop_event: threading.Event,
    delay_range: tuple = (2, 5),
):
    """Worker que cria salas online em sequência dentro de uma thread."""
    stagger = (thread_id - 1) * 1.5
    if stagger > 0:
        time.sleep(stagger)

    loop = (n_games == 0)
    i = 0

    while not stop_event.is_set():
        i += 1
        label = f"Partida {i}" if loop else f"Partida {i}/{n_games}"
        log(f"{label} iniciando... [sala + {n_ghosts} ghost(s)]", thread_id)

        try:
            result = run_online_room(
                cookies=cookies,
                n_ghosts=n_ghosts,
                game_mode=game_mode,
                turn_seconds=turn_seconds,
                formation=formation,
                host_strategy=host_strategy,
                ghost_strategy=ghost_strategy,
                verbose=verbose,
            )

            if result:
                record_online(
                    room_code=result.get("code", "?"),
                    seed=result.get("seed", ""),
                    success=True,
                    ghost_count=n_ghosts,
                    game_mode=game_mode,
                    host_strat=host_strategy,
                    ghost_strat=ghost_strategy,
                    result_json=json.dumps(result.get("result"), ensure_ascii=False) if result.get("result") else None,
                )
                log(f"{label} ✅ sala={result.get('code')}", thread_id)
            else:
                record_online(
                    room_code="?", seed="", success=False,
                    ghost_count=n_ghosts, game_mode=game_mode,
                    host_strat=host_strategy, ghost_strat=ghost_strategy,
                )
                log(f"{label} ❌ falhou", thread_id)

        except Exception as e:
            import traceback
            record_online(
                room_code="?", seed="", success=False,
                ghost_count=n_ghosts, game_mode=game_mode,
                host_strat=host_strategy, ghost_strat=ghost_strategy,
                error=str(e),
            )
            log(f"{label} 💥 ERRO: {e}", thread_id)
            log(traceback.format_exc(), thread_id)

        if not loop and i >= n_games:
            break

        if not stop_event.is_set():
            delay = random.uniform(*delay_range)
            log(f"Pausa {delay:.1f}s antes da próxima...", thread_id)
            time.sleep(delay)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    init_db()

    parser = argparse.ArgumentParser(
        description="7a0 Online Loop — multi-thread, várias salas simultâneas"
    )
    parser.add_argument("--games", "-g", type=int, default=0,
                        help="Total de partidas por thread (0 = infinito, default)")
    parser.add_argument("--threads", "-t", type=int, default=3,
                        help="Número de salas simultâneas (default: 3)")
    parser.add_argument("--ghost", "--ghosts", type=int, default=1,
                        help="Ghosts por sala (default: 1; max efetivo=1 — servidor limita a 2 jogadores/sala)")
    parser.add_argument("--ghost-strat", "--ghost-strategy", default="worst",
                        choices=["best", "worst", "normal"],
                        help="Estratégia dos ghosts (default: worst = time fraco)")
    parser.add_argument("--game-mode", default="classico",
                        choices=["classico", "almanaque"],
                        help="Modo de jogo (default: classico)")
    parser.add_argument("--turn-seconds", type=int, default=20,
                        help="Segundos por turno no draft (default: 20)")
    parser.add_argument("--formation", default="auto",
                        help="Formação do host (default: auto)")
    parser.add_argument("--host-strategy", default="best",
                        choices=["best", "normal", "worst"],
                        help="Estratégia do host (default: best)")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Menos verbosidade")
    args = parser.parse_args()

    # Validar cookies
    session_token = os.environ.get("SESSION_TOKEN", "")
    session_data = os.environ.get("SESSION_DATA", "")
    if not session_token or not session_data:
        print("❌ SESSION_TOKEN e SESSION_DATA não encontrados no .env")
        sys.exit(1)

    cookies = {
        "__Secure-better-auth.session_token": session_token,
        "__Secure-better-auth.session_data": session_data,
    }

    n_threads = max(1, args.threads)
    n_games_per_thread = args.games
    total_label = "∞" if n_games_per_thread == 0 else str(n_games_per_thread * n_threads)

    print(f"\n{'='*60}")
    print(f"  7a0 ONLINE LOOP — MULTI-THREAD")
    print(f"{'='*60}")
    print(f"  Threads     : {n_threads} salas simultâneas")
    print(f"  Partidas    : {'∞ por thread' if n_games_per_thread == 0 else f'{n_games_per_thread}/thread (total {total_label})'}")
    print(f"  Ghosts/sala : {args.ghost} ({args.ghost_strat})")
    print(f"  Host        : {args.host_strategy} | {args.formation}")
    print(f"  Modo        : {args.game_mode} | Turno: {args.turn_seconds}s")
    print(f"  Verbosidade : {'normal' if not args.quiet else 'reduzida'}")
    print(f"  Pressione Ctrl+C para parar.")
    print(f"{'='*60}\n")

    stop_event = threading.Event()
    threads = []
    start_time = time.time()

    for tid in range(n_threads):
        t = threading.Thread(
            target=online_worker,
            args=(
                tid + 1,
                n_games_per_thread,
                cookies,
                args.ghost,
                args.game_mode,
                args.turn_seconds,
                args.formation,
                args.host_strategy,
                args.ghost_strat,
                not args.quiet,
                stop_event,
            ),
            daemon=True,
        )
        threads.append(t)
        t.start()

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print(f"\n\n⚡ Ctrl+C! Parando {n_threads} thread(s)...")
        stop_event.set()
        for t in threads:
            t.join(timeout=60)

    elapsed = time.time() - start_time

    print_stats()
    print(f"  Tempo total: {elapsed:.0f}s")


if __name__ == "__main__":
    main()
