"""
Módulo online — WebSocket multiplayer para 7a0.com.br.

Contém: OnlinePlayer, GhostPlayer, run_online_room, create_room,
get_user_id, _submit_online_result.
"""
import json
import threading
import time
import uuid
from datetime import datetime

import requests

from .constants import FORMATION_SLOTS
from .prng import make_rng
from .game import Game7a0, log


# ═══════════════════════════════════════════════════════════════════════════════
# WEBSOCKET IMPORT
# ═══════════════════════════════════════════════════════════════════════════════

try:
    import websocket  # websocket-client
    _WS_AVAILABLE = True
except ImportError:
    _WS_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════════
# API CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

BASE = "https://7a0.com.br"
WS_BASE = "wss://7a0.com.br"

_COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Origin": "https://7a0.com.br",
    "Referer": "https://7a0.com.br/multi",
}


# ═══════════════════════════════════════════════════════════════════════════════
# HTTP HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def get_user_id(cookies: dict) -> str:
    """Retorna o userId real da sessão autenticada, ou string vazia se não logado."""
    try:
        resp = requests.get(
            f"{BASE}/api/auth/get-session",
            cookies=cookies,
            headers=_COMMON_HEADERS,
            timeout=8,
        )
        if resp.ok:
            data = resp.json()
            return data.get("session", {}).get("userId", "") or ""
    except Exception:
        pass
    return ""


def create_room(cookies: dict, mode: str = "final", game_mode: str = "classico",
                turn_seconds: int = 30, password: str = "") -> dict:
    """POST /api/room — cria uma nova sala. Retorna {code, seed, anonId}."""
    anon_id = str(uuid.uuid4())
    body = {
        "anonId": anon_id,
        "mode": mode,
        "gameMode": game_mode,
        "minPlayers": 2,
        "turnSeconds": turn_seconds,
        "draftMode": "turnos",
    }
    if password:
        body["password"] = password

    resp = requests.post(
        f"{BASE}/api/room",
        json=body,
        cookies=cookies,
        headers={**_COMMON_HEADERS, "Content-Type": "application/json"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    data["anonId"] = anon_id
    return data


def join_room_http(room_code: str, password: str = "") -> dict:
    """GET /api/room/{code} — obtém info da sala (guest sem cookies)."""
    params = {}
    if password:
        params["password"] = password
    resp = requests.get(
        f"{BASE}/api/room/{room_code}",
        params=params,
        headers=_COMMON_HEADERS,
        timeout=10,
    )
    if resp.ok:
        return resp.json()
    return {"code": room_code}


# ═══════════════════════════════════════════════════════════════════════════════
# ONLINE PLAYER (WebSocket base)
# ═══════════════════════════════════════════════════════════════════════════════

class OnlinePlayer:
    """
    Jogador online conectado via WebSocket.

    Protocolo:
      → JOIN → ← JOINED_ACK → ← STATE_SNAPSHOT → ← CAN_START
      → READY → host: START → ← ROOM_STARTED
      → ROLL → ROLL_CONFIRM → ← PICK_PHASE → → PICK → ← DRAFT_COMPLETE
      → DRAFT_DONE → ← GAME_RESULT
    """

    def __init__(self, room_code: str, anon_id: str = None, user_id: str = None,
                 cookies: dict = None, password: str = "",
                 label: str = "player", verbose: bool = True):
        if not _WS_AVAILABLE:
            raise RuntimeError("pip install websocket-client")
        self.room_code = room_code
        self.anon_id = anon_id or str(uuid.uuid4())
        self.user_id = user_id or f"ghost-{self.anon_id[:8]}"
        self.cookies = cookies or {}
        self.password = password
        self.label = label
        self.verbose = verbose

        self.ws = None
        self.seat = None
        self.state = None
        self.messages = []
        self._lock = threading.Lock()
        self._ready_event = threading.Event()
        self._snapshot_event = threading.Event()
        self._game_result = None
        self._draft_complete = None
        self._connected = False
        self._thread = None
        self.can_start = False

    def _log(self, msg):
        if self.verbose:
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"[{ts}][{self.label}] {msg}", flush=True)

    def _cookie_header(self) -> str:
        return "; ".join(f"{k}={v}" for k, v in self.cookies.items())

    def connect(self, timeout: float = 10.0) -> bool:
        """Abre WebSocket e envia JOIN. Bloqueia até JOINED_ACK ou timeout."""
        ws_url = f"{WS_BASE}/api/room/{self.room_code}/ws"
        self._log(f"Conectando a {ws_url}")

        headers = {
            "Origin": "https://7a0.com.br",
            "User-Agent": _COMMON_HEADERS["User-Agent"],
        }
        if self.cookies:
            headers["Cookie"] = self._cookie_header()

        self.ws = websocket.WebSocketApp(
            ws_url,
            header=headers,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        self._thread = threading.Thread(
            target=self.ws.run_forever,
            kwargs={"ping_interval": 20, "ping_timeout": 10},
            daemon=True,
        )
        self._thread.start()
        return self._ready_event.wait(timeout=timeout)

    def _on_open(self, ws):
        self._connected = True
        self._log(f"WS aberto — enviando JOIN (anonId={self.anon_id[:8]}...)")
        join_msg = {
            "type": "JOIN",
            "anonId": self.anon_id,
            "userId": self.user_id,
        }
        if self.password:
            join_msg["password"] = self.password
        ws.send(json.dumps(join_msg))

    def _on_message(self, ws, raw):
        try:
            msg = json.loads(raw)
        except Exception:
            msg = {"raw": raw}

        with self._lock:
            self.messages.append(msg)

        mtype = msg.get("type", "")
        self._log(f"<< {mtype}: {json.dumps(msg)[:200]}")

        if mtype == "JOINED_ACK":
            self.seat = msg.get("seat")
            self._ready_event.set()
        elif mtype == "STATE_SNAPSHOT":
            self.state = msg
            self._snapshot_event.set()
        elif mtype == "CAN_START":
            self.can_start = msg.get("value", False)
        elif mtype == "GAME_RESULT":
            self._game_result = msg

        self._handle_auto(msg)

    def _handle_auto(self, msg):
        pass  # GhostPlayer sobrescreve

    def _on_error(self, ws, err):
        self._log(f"WS ERRO: {err}")

    def _on_close(self, ws, code, reason):
        self._connected = False
        self._log(f"WS fechado: {code} {reason}")

    def send(self, data: dict):
        if self.ws and self._connected:
            raw = json.dumps(data)
            self._log(f">> {raw[:200]}")
            self.ws.send(raw)

    def disconnect(self):
        if self.ws:
            self.ws.close()

    def wait_for(self, msg_type: str, timeout: float = 15.0) -> dict | None:
        """Bloqueia até receber uma mensagem do tipo dado."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._lock:
                for m in reversed(self.messages):
                    if m.get("type") == msg_type:
                        return m
            time.sleep(0.1)
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# GHOST PLAYER (auto-draft via WebSocket)
# ═══════════════════════════════════════════════════════════════════════════════

class GhostPlayer(OnlinePlayer):
    """
    Jogador automático (host ou guest fantasma).

    Gerencia lobby (READY), draft (ROLL/PICK), e resultado (DRAFT_DONE/REVEAL_AT).
    """

    def __init__(self, room_code: str, game7a0: "Game7a0" = None,
                 formation: str = "auto", strategy: str = "normal",
                 style: str = "equilibrado", nick: str = "",
                 is_host: bool = False, **kwargs):
        super().__init__(room_code, **kwargs)
        self.game7a0 = game7a0
        self.strategy = strategy
        self.style = style
        self.nick = nick
        self.is_host = is_host
        self._my_formation = formation if formation != "auto" else "4-3-3"
        self._lobby_ready_sent = False

        # Draft state
        self._roll_sent = False
        self._roll_confirm_sent = False
        self._draft_done_sent = False
        self._reveal_at_sent = False
        self._my_roll = None
        self._my_picks = []
        self._used_ids = set()
        self._pick_lock = threading.Lock()

    # ── LOBBY ─────────────────────────────────────────────────────────────────

    def send_ready(self, ready: bool = True):
        """Envia READY com formation+style."""
        if not ready:
            self.send({"type": "READY", "ready": False})
            self._lobby_ready_sent = False
            return
        if self._lobby_ready_sent:
            return
        self._lobby_ready_sent = True
        payload = {
            "type": "READY",
            "ready": True,
            "formation": self._my_formation,
            "style": self.style,
        }
        if self.nick:
            payload["name"] = self.nick
        self.send(payload)

    # ── ROLL ──────────────────────────────────────────────────────────────────

    def _do_roll(self):
        """Sorteia um time e envia ROLL + ROLL_CONFIRM."""
        if self._roll_sent or not self.game7a0:
            return
        self._roll_sent = True
        seed = (self.state or {}).get("seed", "") if self.state else ""
        rng = make_rng(f"{seed}:{self.anon_id}:roll")
        recent = set()

        if self.strategy == "worst":
            WEAK_CANDIDATES = [
                ("ZAI", 1974), ("HAI", 1974), ("BOL", 1994), ("ELS", 1970),
                ("MAR", 1970), ("TUN", 1978), ("KUW", 1982), ("IRQ", 1986),
                ("UAE", 1990), ("SAU", 1994), ("CHN", 2002), ("ANG", 2006),
                ("TOG", 2006), ("TRI", 2006), ("NZL", 2010), ("HON", 2010),
            ]
            best_weak_sel, best_weak_copa = None, None
            best_weak_overall = 999
            for weak_sel, weak_copa in WEAK_CANDIDATES:
                try:
                    sq = self.game7a0.fetch_squad(weak_sel, weak_copa)
                    if sq:
                        forces = [p["force"] for p in sq]
                        avg = sum(forces) / len(forces) if forces else 99
                        if avg < best_weak_overall:
                            best_weak_overall = avg
                            best_weak_sel, best_weak_copa = weak_sel, weak_copa
                except Exception:
                    pass
            if best_weak_sel:
                sel, copa = best_weak_sel, best_weak_copa
                self._log(f"WORST strategy: escolheu {sel} {copa} (overall≈{best_weak_overall:.1f})")
            else:
                sel, copa = self.game7a0.pick_sel_copa_for_strategy(rng, recent, "normal")
        else:
            sel, copa = self.game7a0.pick_sel_copa_for_strategy(rng, recent, self.strategy)

        squad = self.game7a0.fetch_squad(sel, copa)
        pool = [
            {
                "playerId": p["playerId"],
                "name": p["name"],
                "positions": p.get("positions", [p.get("pos", "")]),
                "number": p.get("number", 0),
                "force": p["force"],
                "legend": p.get("legend", False),
            }
            for p in squad
        ]
        self._my_roll = {"sel": sel, "copa": copa, "pool": pool}
        self._log(f"ROLL: {sel} {copa} ({len(pool)} jogadores)")
        self.send({
            "type": "ROLL",
            "roll": {"sel": sel, "copa": copa},
            "pool": pool,
            "rerollsLeft": 3,
        })
        time.sleep(0.2)
        if not self._roll_confirm_sent:
            self._roll_confirm_sent = True
            self.send({"type": "ROLL_CONFIRM"})

    # ── PICK ──────────────────────────────────────────────────────────────────

    def _do_pick(self, turn_seat: int):
        """Escolhe o melhor slot/jogador disponível e envia PICK."""
        if turn_seat != self.seat or not self.game7a0 or not self._my_roll:
            return
        with self._pick_lock:
            roll = self._my_roll
            pool = roll["pool"]
            sel, copa = roll["sel"], roll["copa"]

            filled_slots = {p["slot"] for p in self._my_picks}
            available = [p for p in pool if p["playerId"] not in self._used_ids]
            if not available:
                available = list(pool)

            slots = FORMATION_SLOTS.get(self._my_formation, FORMATION_SLOTS["4-3-3"])
            target_slot = None
            for idx, slot_pos in enumerate(slots):
                if idx not in filled_slots:
                    target_slot = idx
                    target_pos = slot_pos
                    break
            if target_slot is None:
                self._log("Todos os slots preenchidos — enviando DRAFT_DONE")
                self._send_draft_done()
                return

            pos_match = [p for p in available
                         if target_pos in p.get("positions", [p.get("pos", "")])]
            candidates = pos_match if pos_match else available
            chosen = max(candidates, key=lambda p: p.get("force", 0))

            self._my_picks.append({
                "playerId": chosen["playerId"],
                "slot": target_slot,
                "name": chosen["name"],
                "pos": target_pos,
                "number": chosen.get("number", 0),
                "force": chosen.get("force", 0),
                "sel": sel,
                "copa": copa,
                "positions": chosen.get("positions", [target_pos]),
                "legend": chosen.get("legend", False),
            })
            self._used_ids.add(chosen["playerId"])

            self._log(
                f"PICK slot={target_slot} pos={target_pos} "
                f"{chosen['name']} force={chosen.get('force',0)}"
            )
            self.send({
                "type": "PICK",
                "playerId": chosen["playerId"],
                "slot": target_slot,
                "name": chosen["name"],
                "pos": target_pos,
                "number": chosen.get("number", 0),
                "force": chosen.get("force", 0),
                "sel": sel,
                "copa": copa,
                "positions": chosen.get("positions", [target_pos]),
                "legend": chosen.get("legend", False),
            })

            total_slots = len(FORMATION_SLOTS.get(self._my_formation, FORMATION_SLOTS["4-3-3"]))
            if len(self._my_picks) >= total_slots:
                threading.Timer(0.3, self._send_draft_done).start()

    def _send_draft_done(self):
        """Envia DRAFT_DONE quando todos os 11 slots foram preenchidos."""
        if self._draft_done_sent:
            return
        self._draft_done_sent = True
        squad = self._my_picks[:]
        self._log(f"DRAFT_DONE com {len(squad)} jogadores")
        self.send({"type": "DRAFT_DONE", "squad": squad})

    # ── HANDLER CENTRAL ───────────────────────────────────────────────────────

    def _handle_auto(self, msg):
        mtype = msg.get("type", "")

        if mtype == "JOINED_ACK":
            threading.Timer(0.4, self.send_ready).start()

        elif mtype == "WAITING_READY":
            self.send_ready()

        elif mtype == "ROOM_STARTED":
            self._log("Sala iniciada — fazendo roll...")
            threading.Timer(0.3, self._do_roll).start()

        elif mtype == "ROLLED":
            if msg.get("seat") == self.seat and not self._roll_confirm_sent:
                self._roll_confirm_sent = True
                self.send({"type": "ROLL_CONFIRM"})

        elif mtype == "PICK_PHASE":
            turn_seat = msg.get("turnSeat")
            self._log(f"PICK_PHASE: vez do seat {turn_seat} (eu sou {self.seat})")
            if turn_seat == self.seat:
                threading.Timer(0.3, self._do_pick, args=[turn_seat]).start()

        elif mtype == "PICKED":
            pid = msg.get("playerId")
            if pid:
                self._used_ids.add(pid)
            if msg.get("turnSeat") == self.seat:
                threading.Timer(0.3, self._do_pick, args=[msg.get("turnSeat")]).start()

        elif mtype == "DRAFT_COMPLETE":
            self._draft_complete = msg
            threading.Timer(0.2, self._send_draft_done).start()

        elif mtype == "STATE_SNAPSHOT":
            snap = msg
            if snap.get("draftPhase") == "picking" and snap.get("turnSeat") == self.seat:
                board = snap.get("boardPicks", {})
                for seat_key, picks in board.items():
                    for pk in (picks or []):
                        self._used_ids.add(pk.get("playerId", ""))
                threading.Timer(0.3, self._do_pick, args=[self.seat]).start()
            elif snap.get("draftPhase") == "rolling" and not self._roll_sent:
                threading.Timer(0.3, self._do_roll).start()

        elif mtype == "REVEAL_AT":
            round_num = msg.get("round", 0)
            self._log(f"REVEAL_AT recebido (round={round_num}) — enviando confirmação")
            def _send_reveal(r):
                self.send({"type": "REVEAL_AT", "round": r})
                self._reveal_at_sent = True
            threading.Timer(0.5, _send_reveal, args=[round_num]).start()

        elif mtype == "GAME_RESULT":
            self._log(f"GAME_RESULT recebido")
            self._game_result = msg


# ═══════════════════════════════════════════════════════════════════════════════
# SUBMIT ONLINE RESULT
# ═══════════════════════════════════════════════════════════════════════════════

def _submit_online_result(session, cookies: dict, room_info: dict,
                          draft_complete: dict, host_anon_id: str,
                          host_seat: int, host_formation: str) -> list:
    """
    Submete o resultado de uma partida online via POST /api/match/record.

    Replica exatamente o que o browser faz após DRAFT_COMPLETE.
    """
    players = draft_complete.get("players", [])
    seed = room_info.get("seed", "")
    room_code = room_info.get("code", "")
    mode = room_info.get("mode", "final")

    if not players:
        log("submit_online: sem jogadores no draft — abortando")
        return []

    # Build seats array (formato exato do JS)
    seats = []
    for p in players:
        p_seat = p.get("seat")
        p_roll = p.get("roll", {})
        p_squad = p.get("squad", [])

        forces = [pk.get("force", 0) for pk in p_squad if pk.get("force")]
        ovr = round(sum(forces) / len(forces)) if forces else 75

        entry = {
            "kind": p.get("kind", "human"),
            "roll": {"sel": p_roll.get("sel", ""), "copa": p_roll.get("copa", 0)},
            "overall": ovr,
        }
        if p_seat == host_seat:
            entry["id"] = host_anon_id
        elif p.get("anonId"):
            entry["id"] = p["anonId"]
        seats.append(entry)

    # Opponent
    opponent = opponent_user_id = None
    for p in players:
        if p.get("seat") != host_seat:
            opponent = p.get("anonId") or p.get("userId")
            opponent_user_id = p.get("userId")
            break

    # Summary — host always wins
    summary = {
        "wins": 1, "gf": 3, "ga": 0,
        "champion": True, "sevenZero": False,
        "unbeaten": True, "badge": None,
        "isOnlineWin": True,
    }

    # ctx.match
    host_player_data = next((p for p in players if p.get("seat") == host_seat), None)
    host_forces = [pk.get("force", 0) for pk in (host_player_data.get("squad", []) if host_player_data else [])]
    host_overall = round(sum(host_forces) / len(host_forces)) if host_forces else 75
    opp_player = next((p for p in players if p.get("seat") != host_seat), None)
    opp_forces = [pk.get("force", 0) for pk in (opp_player.get("squad", []) if opp_player else [])]
    opp_overall = round(sum(opp_forces) / len(opp_forces)) if opp_forces else 65

    match_ctx = {
        "mode": mode,
        "almanaque": room_info.get("gameMode", "classico") == "almanaque",
        "champion": True, "unbeaten": True,
        "humansInRoom": len(players),
        "oppHumanInFinal": True, "isHost": True,
        "matches": [{
            "phase": "FINAL", "gf": summary["gf"], "ga": summary["ga"],
            "advanced": True, "penalties": False,
            "oppOverall": opp_overall, "oppHuman": True, "goals": [],
        }],
    }

    # ctx.xi
    host_player = next((p for p in players if p.get("seat") == host_seat), None)
    xi = []
    if host_player:
        for pk in host_player.get("squad", []):
            xi.append({
                "playerId": pk.get("playerId", ""),
                "name": pk.get("name", ""),
                "sel": pk.get("sel", ""),
                "copa": pk.get("copa", 0),
                "positions": pk.get("positions", []),
                "number": pk.get("number", 0),
                "force": pk.get("force", 0),
                "legend": pk.get("legend", False),
            })

    request_id = f"{mode}:{seed}" if seed else str(uuid.uuid4())
    bracket_size = 4 if len(players) == 2 else len(players)
    replay_obj = {
        "seed": seed,
        "bracketSize": bracket_size,
        "seats": seats,
    }

    body = {
        "kind": mode,
        "summary": summary,
        "ctx": {"xi": xi, "match": match_ctx},
        "requestId": request_id,
        "replay": json.dumps(replay_obj),
        "roomId": room_code,
    }
    if opponent:
        body["opponent"] = opponent
    if opponent_user_id:
        body["opponentUserId"] = opponent_user_id

    log(f"Submetendo resultado online — roomId={room_code} seed={seed} seats={len(seats)}")

    headers = {
        **_COMMON_HEADERS,
        "Content-Type": "application/json",
        "Referer": f"https://7a0.com.br/multi/{room_code}",
    }
    for attempt in range(4):
        try:
            resp = requests.post(
                f"{BASE}/api/match/record",
                json=body,
                cookies=cookies,
                headers=headers,
                timeout=12,
            )
            if resp.ok:
                data = resp.json()
                unlocked = data.get("unlocked", [])
                log(f"Resultado online gravado! unlocked={unlocked}")
                return unlocked
            elif resp.status_code in (400, 413):
                log(f"Erro permanente {resp.status_code}: {resp.text[:200]}")
                return []
            else:
                log(f"Erro transiente {resp.status_code} (tentativa {attempt+1}/4)")
        except Exception as e:
            log(f"Erro de rede (tentativa {attempt+1}/4): {e}")
        if attempt < 3:
            time.sleep(0.7 * (attempt + 1))

    log("Falha ao gravar resultado online apos 4 tentativas")
    return []


# ═══════════════════════════════════════════════════════════════════════════════
# RUN ONLINE ROOM — cria sala, conecta ghosts, joga draft, submete
# ═══════════════════════════════════════════════════════════════════════════════

def run_online_room(cookies: dict, n_ghosts: int = 1,
                    game_mode: str = "classico", turn_seconds: int = 30,
                    formation: str = "auto", host_strategy: str = "best",
                    ghost_strategy: str = "worst",
                    verbose: bool = True) -> dict | None:
    """
    Cria uma sala, conecta n_ghosts fantasmas, joga draft completo e retorna resultado.
    """
    if not _WS_AVAILABLE:
        print("pip install websocket-client")
        return None

    # 1. Criar sala
    log("Criando sala online...")
    room = create_room(cookies, mode="final", game_mode=game_mode,
                       turn_seconds=turn_seconds)
    code = room["code"]
    seed = room["seed"]
    host_anon = room["anonId"]
    log(f"Sala criada: {code} | seed={seed}")
    log(f"URL: https://7a0.com.br/multi/{code}")

    # 2. Dataset compartilhado
    game = Game7a0(cookies)

    # 2b. Buscar userId real
    real_user_id = get_user_id(cookies)
    if real_user_id:
        log(f"userId autenticado: {real_user_id[:16]}...")
    else:
        log("AVISO: userId nao encontrado — usando anonId como fallback")

    # 3. Conectar host
    host_formation = "4-3-3" if formation == "auto" else formation
    host = GhostPlayer(
        room_code=code,
        game7a0=game,
        formation=host_formation,
        strategy=host_strategy,
        style="ofensivo",
        anon_id=host_anon,
        user_id=real_user_id or None,
        cookies=cookies,
        label="HOST",
        is_host=True,
        verbose=verbose,
    )
    if not host.connect(timeout=12):
        log("Falhou ao conectar host")
        return None
    log(f"Host conectado, seat={host.seat}")

    # 4. Conectar ghosts
    ghosts: list[GhostPlayer] = []
    for i in range(n_ghosts):
        ghost = GhostPlayer(
            room_code=code,
            game7a0=game,
            formation="4-4-2",
            strategy=ghost_strategy,
            style="defensivo",
            label=f"GHOST-{i+1}",
            is_host=False,
            verbose=verbose,
        )
        if ghost.connect(timeout=10):
            log(f"Ghost {i+1} conectado, seat={ghost.seat}")
            ghosts.append(ghost)
        else:
            log(f"Ghost {i+1} falhou ao conectar")
        time.sleep(0.4)

    if not ghosts:
        log("Nenhum ghost conectou — abortando")
        host.disconnect()
        return None

    # 5. Aguardar CAN_START
    log("Aguardando READY de todos os jogadores...")
    deadline_ready = time.time() + 25
    while time.time() < deadline_ready:
        if host.can_start:
            break
        time.sleep(0.3)
    if not host.can_start:
        log("CAN_START nao chegou — tentando START assim mesmo")
    else:
        log("CAN_START = true")

    # 6. Host envia START
    time.sleep(0.2)
    log("Enviando START...")
    host.send({"type": "START"})

    # 7. Aguardar fim de jogo (timeout 5 min)
    log("Aguardando fim do draft e REVEAL_AT...")
    all_players = [host] + ghosts
    deadline_game = time.time() + 300
    result = None
    draft_complete_data = None

    while time.time() < deadline_game:
        for p in all_players:
            if p._draft_complete and draft_complete_data is None:
                draft_complete_data = p._draft_complete
            if p._game_result and result is None:
                result = p._game_result

        if result:
            log(f"GAME_RESULT via WS: {json.dumps(result)[:300]}")
            break

        all_done = all(p._draft_done_sent for p in all_players)
        if all_done:
            log("Todos enviaram DRAFT_DONE — aguardando DRAFT_COMPLETE (max 5s)...")
            wait_dc = time.time() + 5
            while time.time() < wait_dc:
                for p in all_players:
                    if p._draft_complete and draft_complete_data is None:
                        draft_complete_data = p._draft_complete
                if draft_complete_data:
                    break
                time.sleep(0.2)
            time.sleep(1)
            break

        time.sleep(0.5)

    log(f"Loop encerrado: draft_complete={'SIM' if draft_complete_data else 'NAO'} "
        f"result={'SIM' if result else 'NAO'} "
        f"draft_done_host={host._draft_done_sent} "
        f"reveal_host={host._reveal_at_sent}")

    # 8. Submeter resultado
    submitted = False
    if draft_complete_data:
        unlocked = _submit_online_result(
            session=None, cookies=cookies, room_info=room,
            draft_complete=draft_complete_data,
            host_anon_id=host_anon, host_seat=host.seat,
            host_formation=host_formation,
        )
        submitted = True
    elif host._draft_done_sent:
        players_local = []
        for p in all_players:
            players_local.append({
                "seat": p.seat,
                "anonId": p.anon_id,
                "kind": "human",
                "roll": p._my_roll or {},
                "squad": p._my_picks,
            })
        draft_complete_data = {"players": players_local}
        log("Usando dados locais de picks para submeter resultado")
        unlocked = _submit_online_result(
            session=None, cookies=cookies, room_info=room,
            draft_complete=draft_complete_data,
            host_anon_id=host_anon, host_seat=host.seat,
            host_formation=host_formation,
        )
        submitted = True

    if not submitted:
        log("AVISO: draft nao completou — resultado nao submetido")

    # 9. Fechar conexões
    time.sleep(1)
    for p in all_players:
        p.disconnect()

    return {"code": code, "seed": seed, "result": result}
