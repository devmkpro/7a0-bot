#!/usr/bin/env python3
"""
7a0.com.br — Auto Player (100% HTTP, multi-thread)

Modo offline: simula partidas solo (draft + torneio Poisson + gravação).
Modo online: cria salas WebSocket e conecta ghosts.

Usage:
    python play.py                        # 1 partida offline
    python play.py --games 5 --threads 3  # 5 partidas em 3 threads
    python play.py --online               # 1 sala online
    python play.py --online --threads 10  # 10 salas simultâneas
"""
import argparse
import json
import os
import random
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from a7a0_bot.game import Game7a0, log
from a7a0_bot.online import run_online_room, _WS_AVAILABLE
from a7a0_bot.achievements import STRATEGY_ROTATION, _global_rotator
from a7a0_bot.database import init_db, record_solo, record_online, print_stats


# ═══════════════════════════════════════════════════════════════════════════════
# .env LOADER
# ═══════════════════════════════════════════════════════════════════════════════

def load_env():
    """Load .env file from script directory."""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


# ═══════════════════════════════════════════════════════════════════════════════
# WORKER — roda N partidas offline numa thread dedicada
# ═══════════════════════════════════════════════════════════════════════════════

def worker(
    thread_id: int,
    n_games: int,
    cookies: dict,
    formation: str,
    style: str,
    mode: str,
    results_out: list,
    stop_event: threading.Event,
    strategy: str = "auto",
    focus: str = "achievements",
    delay_range: tuple = (2, 4),
):
    """Joga partidas sequencialmente numa thread."""
    stagger = (thread_id - 1) * 0.8
    if stagger > 0:
        time.sleep(stagger)

    if focus == "titles":
        effective_style = "Ofensivo" if style == "auto" else style
        effective_mode = "Clássico" if mode == "auto" else mode
    else:
        effective_style = style
        effective_mode = mode

    game = Game7a0(cookies)
    loop = n_games == 0
    i = 0

    while not stop_event.is_set():
        i += 1
        label = f"Jogo {i}" if loop else f"Jogo {i}/{n_games}"

        if strategy == "auto":
            cur_strategy, strat_desc = _global_rotator.next()
        else:
            cur_strategy, strat_desc = strategy, strategy

        log(f"{label} iniciando... [{strat_desc}]", thread_id)
        try:
            result = game.play_game(formation, effective_style, effective_mode, strategy=cur_strategy)
            results_out.append(result)
            status = "CAMPEA0" if result["champion"] else f"{result['wins']}V GF:{result['gf']} GA:{result['ga']}"
            unlocked = result.get("unlocked", [])
            if unlocked:
                log(f"{label} CONQUISTAS: {', '.join(unlocked)}", thread_id)
                if strategy == "auto":
                    for ach in unlocked:
                        _global_rotator.report_unlock(ach)
            log(f"{label} concluido — {status}", thread_id)
        except Exception as e:
            import traceback
            log(f"{label} ERRO: {e}\n{traceback.format_exc()}", thread_id)

        if not loop and i >= n_games:
            break

        if not stop_event.is_set():
            time.sleep(random.uniform(*delay_range))


# ═══════════════════════════════════════════════════════════════════════════════
# ONLINE WORKER — roda N salas online numa thread
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
    """Worker que cria salas online em sequência numa thread."""
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
                record_online(room_code="?", seed="", success=False,
                              ghost_count=n_ghosts, game_mode=game_mode,
                              host_strat=host_strategy, ghost_strat=ghost_strategy)
                log(f"{label} ❌ falhou", thread_id)
        except Exception as e:
            import traceback
            record_online(room_code="?", seed="", success=False,
                          ghost_count=n_ghosts, game_mode=game_mode,
                          host_strat=host_strategy, ghost_strat=ghost_strategy,
                          error=str(e))
            log(f"{label} 💥 ERRO: {e}", thread_id)

        if not loop and i >= n_games:
            break

        if not stop_event.is_set():
            time.sleep(random.uniform(*delay_range))


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    load_env()
    init_db()

    parser = argparse.ArgumentParser(description="7a0 Auto Player (100% HTTP, multi-thread)")
    parser.add_argument("--games", "-g", type=int, default=1,
                        help="Total de partidas a jogar (0 = infinito)")
    parser.add_argument("--threads", "-t", type=int, default=1,
                        help="Número de threads paralelas (default: 1)")
    parser.add_argument("--formation", "-f", default="auto",
                        help="Formacao (default: auto)")
    parser.add_argument("--style", "-s", default="auto",
                        choices=["Defensivo", "Equilibrado", "Ofensivo", "auto"],
                        help="Estilo (default: auto=Ofensivo)")
    parser.add_argument("--mode", "-m", default="auto",
                        choices=["Classico", "Clássico", "De almanaque", "auto"],
                        help="Modo (default: auto)")
    parser.add_argument("--strategy", default="auto",
                        help="Estrategia de conquistas (default: auto)")
    parser.add_argument("--focus", default="achievements",
                        choices=["achievements", "titles"],
                        help="Foco: achievements (rotaciona) ou titles (sempre melhor)")

    # Online mode
    parser.add_argument("--online", action="store_true",
                        help="Modo online: cria sala e conecta ghosts")
    parser.add_argument("--ghost", "--ghosts", type=int, default=1,
                        help="Ghosts por sala (default: 1; servidor limita a 2 jogadores/sala)")
    parser.add_argument("--join", default="",
                        help="Entrar numa sala existente como ghost anonimo")
    parser.add_argument("--play", default="",
                        help="Entrar numa sala com sua conta real e jogar automaticamente")
    parser.add_argument("--password", "--pw", default="",
                        help="Senha da sala (para salas privadas)")
    parser.add_argument("--online-verbose", action="store_true", default=True,
                        help="Mostrar mensagens WS detalhadas")

    args = parser.parse_args()

    # ── Cookies ───────────────────────────────────────────────────────────
    session_token = os.environ.get("SESSION_TOKEN", "")
    session_data = os.environ.get("SESSION_DATA", "")
    if not session_token or not session_data:
        print("❌ Cookies não encontrados. Crie o arquivo .env com:")
        print("   SESSION_TOKEN=valor_do_cookie")
        print("   SESSION_DATA=valor_do_cookie")
        sys.exit(1)

    cookies = {
        "__Secure-better-auth.session_token": session_token,
        "__Secure-better-auth.session_data": session_data,
    }

    # ── Modo Play (conta real em sala existente) ─────────────────────────
    if args.play:
        if not _WS_AVAILABLE:
            print("❌ Modo play requer: pip install websocket-client")
            sys.exit(1)

        from a7a0_bot.online import GhostPlayer, get_user_id
        from a7a0_bot.game import Game7a0

        code = args.play.upper()
        print(f"\n{'='*60}")
        print(f"  PLAY — Entrando na sala {code} com conta real")
        print(f"{'='*60}\n")

        real_user_id = get_user_id(cookies)
        if real_user_id:
            print(f"  userId: {real_user_id[:16]}...")
        else:
            print(f"  AVISO: userId nao encontrado — usando cookies mesmo")

        game = Game7a0(cookies)
        host_formation = "4-3-3" if args.formation == "auto" else args.formation

        player = GhostPlayer(
            room_code=code,
            game7a0=game,
            formation=host_formation,
            strategy="best",          # sempre melhor jogador
            style="ofensivo",
            user_id=real_user_id or None,
            cookies=cookies,          # cookies reais = conta logada
            password=args.password,   # senha da sala (se privada)
            label="PLAYER",
            is_host=False,
            verbose=args.online_verbose,
        )

        print(f"  Conectando a wss://7a0.com.br/api/room/{code}/ws ...")
        if not player.connect(timeout=15):
            print("  ❌ Falhou ao conectar")
            sys.exit(1)
        print(f"  ✅ Conectado! seat={player.seat}")
        print(f"  Aguardando draft... (Ctrl+C para sair)\n")

        try:
            deadline = time.time() + 300  # 5 min timeout
            while time.time() < deadline:
                if player._game_result:
                    print(f"\n  🏆 GAME_RESULT recebido!")
                    print(f"  {json.dumps(player._game_result)[:500]}")
                    break
                if player._draft_done_sent and player._reveal_at_sent:
                    # Espera mais um pouco pelo GAME_RESULT
                    time.sleep(5)
                    if player._game_result:
                        print(f"\n  🏆 GAME_RESULT recebido!")
                        break
                    print(f"\n  ✅ Draft completo + REVEAL_AT enviado!")
                    print(f"  Aguardando resultado final...")
                    time.sleep(10)
                    if player._game_result:
                        print(f"\n  🏆 GAME_RESULT recebido!")
                    break
                time.sleep(0.5)
            else:
                print(f"\n  ⏰ Timeout (5 min)")
        except KeyboardInterrupt:
            print(f"\n  ⚡ Interrompido")

        player.disconnect()
        print(f"\n  Desconectado da sala {code}")
        sys.exit(0)

    # ── Modo Online ───────────────────────────────────────────────────────
    if args.online or args.join:
        if not _WS_AVAILABLE:
            print("❌ Modo online requer: pip install websocket-client")
            sys.exit(1)

        game_mode_online = "classico"
        if args.mode in ("De almanaque",):
            game_mode_online = "almanaque"

        if args.join:
            # Ghost puro em sala existente
            print(f"\n{'='*60}")
            print(f"  MODO ONLINE — GHOST em sala {args.join.upper()}")
            print(f"{'='*60}\n")
            from a7a0_bot.online import GhostPlayer
            from a7a0_bot.game import Game7a0
            game = Game7a0(cookies)
            ghosts = []
            for i in range(args.ghost):
                g = GhostPlayer(
                    room_code=args.join.upper(),
                    game7a0=game,
                    formation=args.formation,
                    strategy="normal",
                    label=f"GHOST-{i+1}",
                    verbose=args.online_verbose,
                )
                if g.connect(timeout=10):
                    print(f"  Ghost {i+1} conectado, seat={g.seat}")
                    ghosts.append(g)
                else:
                    print(f"  Ghost {i+1} falhou")
                time.sleep(0.4)
            if ghosts:
                print(f"\n  {len(ghosts)} ghost(s) na sala. Aguardando (Ctrl+C para sair)...")
                try:
                    while True:
                        if any(g._game_result for g in ghosts):
                            break
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
                for g in ghosts:
                    g.disconnect()
        else:
            # Criar salas online (multi-thread)
            n_threads = max(1, args.threads)
            n_games = args.games if args.games > 0 else 0

            print(f"\n{'='*60}")
            print(f"  7a0 ONLINE — {n_threads} sala(s) simultânea(s)")
            print(f"  Ghosts/sala: {args.ghost} | Modo: {game_mode_online}")
            print(f"{'='*60}\n")

            stop_event = threading.Event()
            threads = []
            start_time = time.time()

            for tid in range(n_threads):
                t = threading.Thread(
                    target=online_worker,
                    args=(
                        tid + 1, n_games, cookies, args.ghost,
                        game_mode_online, 20, args.formation,
                        "best", "worst", args.online_verbose,
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
                print(f"\n⚡ Ctrl+C! Parando...")
                stop_event.set()
                for t in threads:
                    t.join(timeout=60)

            elapsed = time.time() - start_time
            print_stats()
            print(f"  Tempo total: {elapsed:.0f}s")

        sys.exit(0)

    # ── Modo Offline ──────────────────────────────────────────────────────
    n_threads = max(1, args.threads)
    loop_mode = (args.games == 0)

    if loop_mode:
        games_per_thread = [0] * n_threads
        mode_str = "LOOP INFINITO"
    else:
        total_games = max(1, args.games)
        games_per_thread = [total_games // n_threads] * n_threads
        for i in range(total_games % n_threads):
            games_per_thread[i] += 1
        mode_str = f"{total_games} partidas"

    print(f"\n{'='*60}")
    print(f"  7a0 AUTO PLAYER — {mode_str} em {n_threads} thread(s)")
    if not loop_mode:
        print(f"  Distribuicao: {games_per_thread}")

    if args.focus == "titles":
        effective_strategy = "normal"
        strat_label = "normal (foco em titulos)"
    else:
        effective_strategy = args.strategy
        strat_label = args.strategy if args.strategy != "auto" else "auto (rotaciona conquistas)"

    focus_label = "TITULOS" if args.focus == "titles" else "CONQUISTAS"
    print(f"  Foco     : {focus_label}")
    print(f"  Formacao : {args.formation if args.formation != 'auto' else 'auto'}")
    print(f"  Estrateg : {strat_label}")
    if loop_mode:
        print(f"  Pressione Ctrl+C para parar.")
    print(f"{'='*60}\n")

    if args.focus == "achievements" and effective_strategy == "auto":
        print("  Ordem de conquistas:")
        for s, d, n in STRATEGY_ROTATION:
            print(f"    {d} ({n}x)")
        print()

    all_results = []
    threads = []
    stop_event = threading.Event()
    start_time = time.time()

    for tid in range(n_threads):
        n = games_per_thread[tid]
        t = threading.Thread(
            target=worker,
            args=(tid + 1, n, cookies, args.formation, args.style, args.mode,
                  all_results, stop_event),
            kwargs={"strategy": effective_strategy, "focus": args.focus},
            daemon=True,
        )
        threads.append(t)
        t.start()

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n\nCtrl+C detectado. Aguardando threads finalizarem...")
        stop_event.set()
        for t in threads:
            t.join(timeout=30)

    elapsed = time.time() - start_time

    # Gravar no SQLite
    for r in all_results:
        record_solo(r)

    # Resumo
    print_stats()
    print(f"  Tempo total: {elapsed:.1f}s ({elapsed/max(len(all_results),1):.1f}s/jogo)")


if __name__ == "__main__":
    main()
