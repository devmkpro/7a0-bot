# 7a0.com.br Auto Player 🎮⚽

Bot 100% Python para o [7a0.com.br](https://7a0.com.br) — joga partidas solo e online automaticamente, sem navegador.

## O que faz

- **Modo Solo**: draft inteligente → simulação Poisson do torneio (grupos + mata-mata) → grava resultado via API
- **Modo Online**: cria salas WebSocket, conecta ghosts, joga draft multiplayer, submete vitória
- **Multi-thread**: N partidas simultâneas (offline ou online)
- **Rotação de conquistas**: alterna estratégias automaticamente para desbloquear todas as conquistas

## Instalação

```bash
git clone https://github.com/devmkpro/7a0-bot.git
cd 7a0-bot
pip install -r requirements.txt
```

### Cookies

Crie um arquivo `.env` na raiz:

```
SESSION_TOKEN=seu_token_aqui
SESSION_DATA=seu_data_aqui
```

Para obter os cookies: acesse [7a0.com.br](https://7a0.com.br), faça login, e extraia os cookies do DevTools (F12 → Application → Cookies).

### player_index.json

Este arquivo contém o índice global de jogadores (extraído do JS bundle do site). É necessário para o bot funcionar. Se o arquivo não existir ou estiver desatualizado:

```bash
python extract_index.py
```

O script baixa os chunks JS do site e extrai o array de jogadores automaticamente.

## Uso

### Modo Solo (offline)

```bash
python play.py                          # 1 partida
python play.py -g 10 -t 4               # 10 partidas em 4 threads
python play.py -g 0 -t 3                # loop infinito em 3 threads
python play.py --focus titles            # foco em títulos (sempre melhor time)
python play.py --formation 4-3-3         # formação específica
python play.py --strategy dream_team     # força dream team (85+)
```

### Modo Online

```bash
python play.py --online                  # 1 sala online
python play.py --online -t 10            # 10 salas simultâneas
python play.py --online --ghost 1        # 1 ghost por sala (máximo do servidor)
python play.py --join ABCD               # entrar em sala existente como ghost
```

### Online Loop (multi-thread dedicado)

```bash
python online_loop.py                    # 3 threads, infinito
python online_loop.py -t 10              # 10 threads
python online_loop.py -g 20 -t 5         # 20 partidas/thread em 5 threads
python online_loop.py --ghost-strat best # ghosts fortes
```

## Arquitetura

```
a7a0_bot/
├── __init__.py       # exports do pacote
├── constants.py      # SQUAD_INDEX, TOURNAMENT, formações, confederações
├── prng.py           # PRNG seeded (MurmurHash3), Poisson, simulação
├── game.py           # Game7a0 (solo): draft, torneio, gravação
├── online.py         # OnlinePlayer, GhostPlayer, salas WebSocket
├── achievements.py   # StrategyRotator, rotação de conquistas
└── database.py       # SQLite: registro de partidas (solo + online)

play.py               # CLI principal (offline + online)
online_loop.py        # CLI dedicado para online multi-thread
extract_index.py      # extrai player_index.json do JS bundle do site
player_index.json     # índice global de jogadores (extraído do JS)
```

### Módulos

| Módulo | Responsabilidade |
|--------|-----------------|
| `constants.py` | Dados estáticos: squads (150+), torneio, formações, confederações |
| `prng.py` | PRNG idêntico ao JS (MurmurHash3), Poisson, simulação de partidas |
| `game.py` | Engine solo: fetch de squads, draft inteligente, torneio, submissão |
| `online.py` | WebSocket: salas multiplayer, ghosts automáticos, submissão online |
| `achievements.py` | Rotação thread-safe de estratégias para desbloquear conquistas |

### Estratégias de conquistas

O bot rotaciona automaticamente entre estas estratégias:

| Estratégia | Conquista | Descrição |
|-----------|-----------|-----------|
| `same_copa` | Era de ouro | XI inteiro da mesma Copa |
| `same_sel` | Patriota | XI inteiro da mesma seleção |
| `dream_team` | Dream Team | XI com force 85+ |
| `old_copas` | Saudosista | XI de Copas até 1970 |
| `modern_copas` | Moderninho | XI de Copas 2010+ |
| `same_decade` | Contemporâneos | XI da mesma década |
| `all_conmebol` | Conmebol total | XI todo CONMEBOL |
| `african` | Zebra africana | 5+ da CAF |
| `asian` | Zebra asiática | 5+ da AFC |
| `outsider` | Outsider | 5+ fora de UEFA/CONMEBOL |
| `extinct5` | Cortina de ferro | 5+ seleções extintas |
| `impossible` | O impossível | Invicto, force < 78 |
| `normal` | — | Títulos + conquistas de placar |

## Requisitos

- Python 3.10+
- `requests` — HTTP
- `websocket-client` — modo online

## Disclaimer

Este projeto é para fins educacionais. Use com responsabilidade.
