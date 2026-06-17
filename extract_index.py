#!/usr/bin/env python3
"""
Extrai o player_index.json do JS bundle do 7a0.com.br.

O array de jogadores ("SEL:COPA:playerId", ~5700 entradas) está dentro
de um JSON.parse('...') no chunk da página de play.

Uso:
    python extract_index.py
"""
import json
import re
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

BASE = "https://7a0.com.br"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/131.0.0.0 Safari/537.36",
}

# Regex para "SEL:COPA:playerId" (ex: "BRA:1970:pele", "ARG:1986:maradona")
PLAYER_RE = re.compile(r'"([A-Z]{2,4}:\d{4}:[a-z0-9-]+)"')


def extract():
    print("[1/3] Baixando /play ...")
    resp = requests.get(f"{BASE}/play", headers=HEADERS, timeout=15)
    resp.raise_for_status()
    html = resp.text

    chunks = re.findall(r'src="(/_next/static/chunks/[^"]+\.js)"', html)
    print(f"   {len(chunks)} chunks encontrados")

    # Priorizar: play page chunk primeiro
    play_chunks = [c for c in chunks if "play" in c.lower()]
    other_chunks = [c for c in chunks if "play" not in c.lower()]
    ordered = play_chunks + other_chunks

    for i, chunk_url in enumerate(ordered):
        full_url = f"{BASE}{chunk_url}"
        short = chunk_url.split("/")[-1][:50]
        print(f"[2/3] Chunk {i+1}/{len(ordered)}: {short}...")

        try:
            r = requests.get(full_url, headers=HEADERS, timeout=30)
            if r.status_code != 200:
                continue
            js = r.text
        except Exception:
            continue

        # Procurar por JSON.parse('["SEL:COPA:playerId", ...')
        marker = js.find('JSON.parse(\'["')
        if marker < 0:
            continue

        # Extrair todos os player IDs com regex (ignora escapes JS)
        # Limitar busca ao trecho do array (marker até ~160KB depois)
        search_end = min(len(js), marker + 200000)
        entries = PLAYER_RE.findall(js[marker:search_end])

        if len(entries) > 500:
            print(f"   ENCONTRADO: {len(entries)} jogadores")
            Path("player_index.json").write_text(
                json.dumps(entries, ensure_ascii=False), encoding="utf-8"
            )
            print(f"\n[3/3] player_index.json salvo — {len(entries)} jogadores")
            return True

    print("\n[ERRO] Array de jogadores nao encontrado nos chunks.")
    return False


if __name__ == "__main__":
    sys.exit(0 if extract() else 1)
