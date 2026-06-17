"""
Dados estáticos do jogo 7a0.com.br.

Contém: SQUAD_INDEX, TOURNAMENT, FORMATION_SLOTS, posições,
confederações, mapas de conquistas.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# SQUAD INDEX — All 150+ squads with slugs (from JS bundle module 1531)
# ═══════════════════════════════════════════════════════════════════════════════

SQUAD_INDEX = [
    {"sel":"BRA","copa":1950,"slug":"BRA-1950-f0aa69a9"},{"sel":"CHI","copa":1950,"slug":"CHI-1950-403d2f22"},
    {"sel":"ENG","copa":1950,"slug":"ENG-1950-9411ac8c"},{"sel":"ESP","copa":1950,"slug":"ESP-1950-4a99ebe4"},
    {"sel":"ITA","copa":1950,"slug":"ITA-1950-f0e0ad37"},{"sel":"MEX","copa":1950,"slug":"MEX-1950-bb0154e9"},
    {"sel":"PAR","copa":1950,"slug":"PAR-1950-21b57bd4"},{"sel":"SUI","copa":1950,"slug":"SUI-1950-f418d703"},
    {"sel":"SWE","copa":1950,"slug":"SWE-1950-9158dc23"},{"sel":"URU","copa":1950,"slug":"URU-1950-62949036"},
    {"sel":"USA","copa":1950,"slug":"USA-1950-6cb5a98c"},{"sel":"YUG","copa":1950,"slug":"YUG-1950-5835fbe2"},
    {"sel":"AUT","copa":1954,"slug":"AUT-1954-58df51d8"},{"sel":"BRA","copa":1954,"slug":"BRA-1954-917f36b5"},
    {"sel":"ENG","copa":1954,"slug":"ENG-1954-791fe817"},{"sel":"FRA","copa":1954,"slug":"FRA-1954-356d3248"},
    {"sel":"GER","copa":1954,"slug":"GER-1954-3473d8b6"},{"sel":"HUN","copa":1954,"slug":"HUN-1954-e4615542"},
    {"sel":"ITA","copa":1954,"slug":"ITA-1954-1de5710f"},{"sel":"SCO","copa":1954,"slug":"SCO-1954-345afb32"},
    {"sel":"SUI","copa":1954,"slug":"SUI-1954-323c49b4"},{"sel":"TCH","copa":1954,"slug":"TCH-1954-bb88ec2c"},
    {"sel":"TUR","copa":1954,"slug":"TUR-1954-a648e60f"},{"sel":"URU","copa":1954,"slug":"URU-1954-93a6ea37"},
    {"sel":"YUG","copa":1954,"slug":"YUG-1954-d251b371"},
    {"sel":"ARG","copa":1958,"slug":"ARG-1958-05981798"},{"sel":"BRA","copa":1958,"slug":"BRA-1958-ceff109b"},
    {"sel":"ENG","copa":1958,"slug":"ENG-1958-3505f834"},{"sel":"FRA","copa":1958,"slug":"FRA-1958-8b348412"},
    {"sel":"GER","copa":1958,"slug":"GER-1958-73ea6cd5"},{"sel":"HUN","copa":1958,"slug":"HUN-1958-08ddf028"},
    {"sel":"NIR","copa":1958,"slug":"NIR-1958-e2e37c47"},{"sel":"PAR","copa":1958,"slug":"PAR-1958-0cb9bc03"},
    {"sel":"SWE","copa":1958,"slug":"SWE-1958-4140b4cf"},{"sel":"URS","copa":1958,"slug":"URS-1958-0dae207f"},
    {"sel":"WAL","copa":1958,"slug":"WAL-1958-cdba669b"},{"sel":"YUG","copa":1958,"slug":"YUG-1958-f1dcb145"},
    {"sel":"ARG","copa":1962,"slug":"ARG-1962-2cce5e4c"},{"sel":"BRA","copa":1962,"slug":"BRA-1962-971e855a"},
    {"sel":"CHI","copa":1962,"slug":"CHI-1962-9594a2c2"},{"sel":"ENG","copa":1962,"slug":"ENG-1962-956cfed6"},
    {"sel":"ESP","copa":1962,"slug":"ESP-1962-c38db356"},{"sel":"GER","copa":1962,"slug":"GER-1962-e32491eb"},
    {"sel":"HUN","copa":1962,"slug":"HUN-1962-afd66cec"},{"sel":"ITA","copa":1962,"slug":"ITA-1962-dd290103"},
    {"sel":"MEX","copa":1962,"slug":"MEX-1962-99181d8c"},{"sel":"TCH","copa":1962,"slug":"TCH-1962-3d9d9577"},
    {"sel":"URS","copa":1962,"slug":"URS-1962-a5438ff3"},{"sel":"YUG","copa":1962,"slug":"YUG-1962-7ab00604"},
    {"sel":"ARG","copa":1966,"slug":"ARG-1966-94a7de8d"},{"sel":"BRA","copa":1966,"slug":"BRA-1966-712b5a5b"},
    {"sel":"ENG","copa":1966,"slug":"ENG-1966-3015d733"},{"sel":"ESP","copa":1966,"slug":"ESP-1966-31e41480"},
    {"sel":"FRA","copa":1966,"slug":"FRA-1966-ecee5680"},{"sel":"GER","copa":1966,"slug":"GER-1966-b10682f2"},
    {"sel":"HUN","copa":1966,"slug":"HUN-1966-7d063179"},{"sel":"ITA","copa":1966,"slug":"ITA-1966-f7216f21"},
    {"sel":"MEX","copa":1966,"slug":"MEX-1966-c6383187"},{"sel":"POR","copa":1966,"slug":"POR-1966-d0941636"},
    {"sel":"URS","copa":1966,"slug":"URS-1966-8c6d41b0"},
    {"sel":"BEL","copa":1970,"slug":"BEL-1970-5a86670c"},{"sel":"BRA","copa":1970,"slug":"BRA-1970-4b0e863a"},
    {"sel":"BUL","copa":1970,"slug":"BUL-1970-7de6e20f"},{"sel":"ENG","copa":1970,"slug":"ENG-1970-6d20a939"},
    {"sel":"GER","copa":1970,"slug":"GER-1970-1fbf381d"},{"sel":"ITA","copa":1970,"slug":"ITA-1970-ebd2d53f"},
    {"sel":"MEX","copa":1970,"slug":"MEX-1970-da64fcae"},{"sel":"PER","copa":1970,"slug":"PER-1970-218e7416"},
    {"sel":"ROU","copa":1970,"slug":"ROU-1970-3e8fd805"},{"sel":"URU","copa":1970,"slug":"URU-1970-53ea2ad7"},
    {"sel":"ARG","copa":1974,"slug":"ARG-1974-d588c475"},{"sel":"BRA","copa":1974,"slug":"BRA-1974-d381d554"},
    {"sel":"CHI","copa":1974,"slug":"CHI-1974-1e3263f6"},{"sel":"GER","copa":1974,"slug":"GER-1974-36443d93"},
    {"sel":"ITA","copa":1974,"slug":"ITA-1974-b7ac06b1"},{"sel":"NED","copa":1974,"slug":"NED-1974-c81e07af"},
    {"sel":"POL","copa":1974,"slug":"POL-1974-74094ee5"},{"sel":"SCO","copa":1974,"slug":"SCO-1974-0d10cd0b"},
    {"sel":"SWE","copa":1974,"slug":"SWE-1974-29d47349"},{"sel":"URU","copa":1974,"slug":"URU-1974-8b707d86"},
    {"sel":"ARG","copa":1978,"slug":"ARG-1978-9489689d"},{"sel":"AUT","copa":1978,"slug":"AUT-1978-2d508789"},
    {"sel":"BRA","copa":1978,"slug":"BRA-1978-8ecd057d"},{"sel":"ESP","copa":1978,"slug":"ESP-1978-f80f6436"},
    {"sel":"FRA","copa":1978,"slug":"FRA-1978-79a91316"},{"sel":"ITA","copa":1978,"slug":"ITA-1978-d5e414a3"},
    {"sel":"MEX","copa":1978,"slug":"MEX-1978-a34f4d01"},{"sel":"NED","copa":1978,"slug":"NED-1978-e3cd7284"},
    {"sel":"PER","copa":1978,"slug":"PER-1978-32e77aef"},{"sel":"POL","copa":1978,"slug":"POL-1978-66a6e1a3"},
    {"sel":"SCO","copa":1978,"slug":"SCO-1978-10282cda"},
    {"sel":"ALG","copa":1982,"slug":"ALG-1982-e5837181"},{"sel":"ARG","copa":1982,"slug":"ARG-1982-95b6abbd"},
    {"sel":"AUT","copa":1982,"slug":"AUT-1982-20aa206f"},{"sel":"BEL","copa":1982,"slug":"BEL-1982-4538ce6a"},
    {"sel":"BRA","copa":1982,"slug":"BRA-1982-000a5ba5"},{"sel":"CMR","copa":1982,"slug":"CMR-1982-c68ffc91"},
    {"sel":"ENG","copa":1982,"slug":"ENG-1982-079c9893"},{"sel":"FRA","copa":1982,"slug":"FRA-1982-aaa57b72"},
    {"sel":"GER","copa":1982,"slug":"GER-1982-a3a7378b"},{"sel":"ITA","copa":1982,"slug":"ITA-1982-590ea2b6"},
    {"sel":"POL","copa":1982,"slug":"POL-1982-69beb7d9"},{"sel":"SCO","copa":1982,"slug":"SCO-1982-2c5c09ca"},
    {"sel":"ARG","copa":1986,"slug":"ARG-1986-5d16a802"},{"sel":"BEL","copa":1986,"slug":"BEL-1986-e0a8913c"},
    {"sel":"BRA","copa":1986,"slug":"BRA-1986-6452a899"},{"sel":"BUL","copa":1986,"slug":"BUL-1986-79fb1b2d"},
    {"sel":"DEN","copa":1986,"slug":"DEN-1986-09d98cfb"},{"sel":"ENG","copa":1986,"slug":"ENG-1986-42f22c4f"},
    {"sel":"ESP","copa":1986,"slug":"ESP-1986-a90eb43f"},{"sel":"FRA","copa":1986,"slug":"FRA-1986-9101315a"},
    {"sel":"GER","copa":1986,"slug":"GER-1986-cff7d25f"},{"sel":"ITA","copa":1986,"slug":"ITA-1986-9e5cec96"},
    {"sel":"MAR","copa":1986,"slug":"MAR-1986-f3966794"},{"sel":"MEX","copa":1986,"slug":"MEX-1986-8296feb9"},
    {"sel":"PAR","copa":1986,"slug":"PAR-1986-1491869c"},{"sel":"POL","copa":1986,"slug":"POL-1986-d5f1239a"},
    {"sel":"URU","copa":1986,"slug":"URU-1986-770a16b4"},
    {"sel":"ARG","copa":1990,"slug":"ARG-1990-fb699d82"},{"sel":"BRA","copa":1990,"slug":"BRA-1990-cfc15d4e"},
    {"sel":"CMR","copa":1990,"slug":"CMR-1990-52f72c37"},{"sel":"COL","copa":1990,"slug":"COL-1990-b52aa660"},
    {"sel":"CZE","copa":1990,"slug":"CZE-1990-2bd3f7dc"},{"sel":"EGY","copa":1990,"slug":"EGY-1990-39213bf4"},
    {"sel":"ENG","copa":1990,"slug":"ENG-1990-80cba7ff"},{"sel":"GER","copa":1990,"slug":"GER-1990-e2d2e829"},
    {"sel":"IRL","copa":1990,"slug":"IRL-1990-fcf0deb0"},{"sel":"ITA","copa":1990,"slug":"ITA-1990-375d41c5"},
    {"sel":"NED","copa":1990,"slug":"NED-1990-10593365"},{"sel":"ROU","copa":1990,"slug":"ROU-1990-8f7c6fc2"},
    {"sel":"YUG","copa":1990,"slug":"YUG-1990-349f7a1d"},
    {"sel":"ARG","copa":1994,"slug":"ARG-1994-305865d2"},{"sel":"BRA","copa":1994,"slug":"BRA-1994-c682ea9c"},
    {"sel":"BUL","copa":1994,"slug":"BUL-1994-8f13051d"},{"sel":"COL","copa":1994,"slug":"COL-1994-172a71d5"},
    {"sel":"GER","copa":1994,"slug":"GER-1994-e11c9ef7"},{"sel":"ITA","copa":1994,"slug":"ITA-1994-95cd31d2"},
    {"sel":"MEX","copa":1994,"slug":"MEX-1994-7d2a671d"},{"sel":"NED","copa":1994,"slug":"NED-1994-9414488e"},
    {"sel":"NGA","copa":1994,"slug":"NGA-1994-8ace4c77"},{"sel":"ROU","copa":1994,"slug":"ROU-1994-78ef2c6a"},
    {"sel":"SWE","copa":1994,"slug":"SWE-1994-400486ba"},{"sel":"USA","copa":1994,"slug":"USA-1994-76b70802"},
    {"sel":"ARG","copa":1998,"slug":"ARG-1998-1949e2e9"},{"sel":"BRA","copa":1998,"slug":"BRA-1998-eaafed4b"},
    {"sel":"COL","copa":1998,"slug":"COL-1998-324fd01c"},{"sel":"CRO","copa":1998,"slug":"CRO-1998-5106215f"},
    {"sel":"DEN","copa":1998,"slug":"DEN-1998-2daebdda"},{"sel":"ENG","copa":1998,"slug":"ENG-1998-be606a57"},
    {"sel":"FRA","copa":1998,"slug":"FRA-1998-6cd66e36"},{"sel":"GER","copa":1998,"slug":"GER-1998-e32815ca"},
    {"sel":"ITA","copa":1998,"slug":"ITA-1998-e83ce438"},{"sel":"NED","copa":1998,"slug":"NED-1998-c04a194a"},
    {"sel":"NGA","copa":1998,"slug":"NGA-1998-5004db0c"},{"sel":"PAR","copa":1998,"slug":"PAR-1998-ea6a7590"},
    {"sel":"YUG","copa":1998,"slug":"YUG-1998-c2715106"},
    {"sel":"ARG","copa":2002,"slug":"ARG-2002-6a4747f9"},{"sel":"BRA","copa":2002,"slug":"BRA-2002-509365e2"},
    {"sel":"CMR","copa":2002,"slug":"CMR-2002-30ae3218"},{"sel":"DEN","copa":2002,"slug":"DEN-2002-689e07b9"},
    {"sel":"ESP","copa":2002,"slug":"ESP-2002-ea566cdb"},{"sel":"FRA","copa":2002,"slug":"FRA-2002-b2ad793c"},
    {"sel":"GER","copa":2002,"slug":"GER-2002-279b435f"},{"sel":"IRL","copa":2002,"slug":"IRL-2002-889441e1"},
    {"sel":"JPN","copa":2002,"slug":"JPN-2002-badeea6c"},{"sel":"KOR","copa":2002,"slug":"KOR-2002-b6faaa2b"},
    {"sel":"MEX","copa":2002,"slug":"MEX-2002-ecaf6590"},{"sel":"NGA","copa":2002,"slug":"NGA-2002-4152b626"},
    {"sel":"SEN","copa":2002,"slug":"SEN-2002-81778089"},{"sel":"TUR","copa":2002,"slug":"TUR-2002-36a6336b"},
    {"sel":"USA","copa":2002,"slug":"USA-2002-2eeaacd8"},
    {"sel":"ARG","copa":2006,"slug":"ARG-2006-3c17ee87"},{"sel":"AUS","copa":2006,"slug":"AUS-2006-abfe2985"},
    {"sel":"BRA","copa":2006,"slug":"BRA-2006-b8054dfc"},{"sel":"CIV","copa":2006,"slug":"CIV-2006-2e020d2f"},
    {"sel":"CZE","copa":2006,"slug":"CZE-2006-00791ebd"},{"sel":"ECU","copa":2006,"slug":"ECU-2006-705b54e8"},
    {"sel":"ENG","copa":2006,"slug":"ENG-2006-2ed6e9be"},{"sel":"FRA","copa":2006,"slug":"FRA-2006-270b2f7c"},
    {"sel":"GER","copa":2006,"slug":"GER-2006-9ba34b07"},{"sel":"ITA","copa":2006,"slug":"ITA-2006-dd67da98"},
    {"sel":"POR","copa":2006,"slug":"POR-2006-e77be181"},{"sel":"SUI","copa":2006,"slug":"SUI-2006-76a62f8f"},
    {"sel":"UKR","copa":2006,"slug":"UKR-2006-bbd908af"},
    {"sel":"ARG","copa":2010,"slug":"ARG-2010-a221b61e"},{"sel":"BRA","copa":2010,"slug":"BRA-2010-22769b89"},
    {"sel":"CHI","copa":2010,"slug":"CHI-2010-71c87c46"},{"sel":"CIV","copa":2010,"slug":"CIV-2010-47b8dead"},
    {"sel":"ENG","copa":2010,"slug":"ENG-2010-bbfcd2e3"},{"sel":"ESP","copa":2010,"slug":"ESP-2010-b92bcad8"},
    {"sel":"GHA","copa":2010,"slug":"GHA-2010-8d462ec4"},{"sel":"GRE","copa":2010,"slug":"GRE-2010-65e81e21"},
    {"sel":"JPN","copa":2010,"slug":"JPN-2010-72b001c0"},{"sel":"KOR","copa":2010,"slug":"KOR-2010-ac7475eb"},
    {"sel":"MEX","copa":2010,"slug":"MEX-2010-ed1d612e"},{"sel":"NED","copa":2010,"slug":"NED-2010-84548ec0"},
    {"sel":"PAR","copa":2010,"slug":"PAR-2010-72313d50"},{"sel":"URU","copa":2010,"slug":"URU-2010-74594dd6"},
    {"sel":"ALG","copa":2014,"slug":"ALG-2014-c9f7f39a"},{"sel":"ARG","copa":2014,"slug":"ARG-2014-ce495a63"},
    {"sel":"BRA","copa":2014,"slug":"BRA-2014-0f83f480"},{"sel":"CHI","copa":2014,"slug":"CHI-2014-14fe633f"},
    {"sel":"CIV","copa":2014,"slug":"CIV-2014-42db6dd4"},{"sel":"COL","copa":2014,"slug":"COL-2014-b4685d91"},
    {"sel":"CRC","copa":2014,"slug":"CRC-2014-7edbdeb1"},{"sel":"FRA","copa":2014,"slug":"FRA-2014-f926f1da"},
    {"sel":"GER","copa":2014,"slug":"GER-2014-acffef39"},{"sel":"GHA","copa":2014,"slug":"GHA-2014-0feccfb5"},
    {"sel":"GRE","copa":2014,"slug":"GRE-2014-4c85a70d"},{"sel":"NED","copa":2014,"slug":"NED-2014-fd0c6150"},
    {"sel":"NGA","copa":2014,"slug":"NGA-2014-cce76555"},{"sel":"SUI","copa":2014,"slug":"SUI-2014-b2bbc221"},
    {"sel":"URU","copa":2014,"slug":"URU-2014-81a07977"},
    {"sel":"ARG","copa":2018,"slug":"ARG-2018-d94d9d6f"},{"sel":"BEL","copa":2018,"slug":"BEL-2018-8bc61b1e"},
    {"sel":"BRA","copa":2018,"slug":"BRA-2018-d299a231"},{"sel":"CRO","copa":2018,"slug":"CRO-2018-21c8a676"},
    {"sel":"EGY","copa":2018,"slug":"EGY-2018-bd2a4d04"},{"sel":"ENG","copa":2018,"slug":"ENG-2018-b4929741"},
    {"sel":"ESP","copa":2018,"slug":"ESP-2018-bd7fd4b1"},{"sel":"FRA","copa":2018,"slug":"FRA-2018-89ffeeae"},
    {"sel":"KOR","copa":2018,"slug":"KOR-2018-3afc5f82"},{"sel":"MAR","copa":2018,"slug":"MAR-2018-2c8a5ef1"},
    {"sel":"POR","copa":2018,"slug":"POR-2018-5c8a53c0"},{"sel":"RUS","copa":2018,"slug":"RUS-2018-20688b0d"},
    {"sel":"SUI","copa":2018,"slug":"SUI-2018-b316d42b"},{"sel":"SWE","copa":2018,"slug":"SWE-2018-092d8bf6"},
    {"sel":"ARG","copa":2022,"slug":"ARG-2022-5aa0e1ee"},{"sel":"AUS","copa":2022,"slug":"AUS-2022-255010d5"},
    {"sel":"BRA","copa":2022,"slug":"BRA-2022-03265289"},{"sel":"CRC","copa":2022,"slug":"CRC-2022-944f3823"},
    {"sel":"CRO","copa":2022,"slug":"CRO-2022-6257e69c"},{"sel":"ECU","copa":2022,"slug":"ECU-2022-7ced142f"},
    {"sel":"FRA","copa":2022,"slug":"FRA-2022-d1c881bc"},{"sel":"JPN","copa":2022,"slug":"JPN-2022-867f9ce2"},
    {"sel":"KOR","copa":2022,"slug":"KOR-2022-b56027e1"},{"sel":"MAR","copa":2022,"slug":"MAR-2022-f98b2002"},
    {"sel":"POR","copa":2022,"slug":"POR-2022-c43fc119"},{"sel":"SEN","copa":2022,"slug":"SEN-2022-c4af4f41"},
    {"sel":"SRB","copa":2022,"slug":"SRB-2022-0806c266"},
    {"sel":"ARG","copa":2026,"slug":"ARG-2026-76523f8e"},{"sel":"BEL","copa":2026,"slug":"BEL-2026-8f86c184"},
    {"sel":"BRA","copa":2026,"slug":"BRA-2026-c0a35709"},{"sel":"ECU","copa":2026,"slug":"ECU-2026-35a979ac"},
    {"sel":"ENG","copa":2026,"slug":"ENG-2026-0d8223e1"},{"sel":"ESP","copa":2026,"slug":"ESP-2026-38b89435"},
    {"sel":"FRA","copa":2026,"slug":"FRA-2026-017f92e8"},{"sel":"GER","copa":2026,"slug":"GER-2026-ee17c481"},
    {"sel":"NED","copa":2026,"slug":"NED-2026-2800ecf6"},{"sel":"POR","copa":2026,"slug":"POR-2026-cbc4fd74"},
]


# ═══════════════════════════════════════════════════════════════════════════════
# TOURNAMENT STRUCTURE (module 5177)
# ═══════════════════════════════════════════════════════════════════════════════

TOURNAMENT = {
    "phases": [
        {"key": "GRUPOS", "type": "group", "opponents": [
            {"label": "Grupo · 1º jogo", "overall": 68},
            {"label": "Grupo · 2º jogo", "overall": 72},
            {"label": "Grupo · 3º jogo", "overall": 76},
        ]},
        {"key": "OITAVAS", "type": "knockout", "opponent": {"label": "Oitavas", "overall": 79}},
        {"key": "QUARTAS", "type": "knockout", "opponent": {"label": "Quartas", "overall": 83}},
        {"key": "SEMI", "type": "knockout", "opponent": {"label": "Semifinal", "overall": 87}},
        {"key": "FINAL", "type": "knockout", "opponent": {"label": "Final", "overall": 91}},
    ],
    "model": {"baseLambda": 1.4, "slope": 0.08, "minLambda": 0.15, "maxLambda": 5},
    "penalty": {"base": 0.5, "slope": 0.012, "min": 0.1, "max": 0.9},
    "badge": {"esmagadorGD": 18},
}


# ═══════════════════════════════════════════════════════════════════════════════
# FORMATIONS
# ═══════════════════════════════════════════════════════════════════════════════

FORMATION_SLOTS = {
    "4-3-3":   ["GOL","LD","ZAG","ZAG","LE","VOL","MC","MEI","PD","CA","PE"],
    "4-4-2":   ["GOL","LD","ZAG","ZAG","LE","ME","MC","MC","MD","CA","CA"],
    "4-2-3-1": ["GOL","LD","ZAG","ZAG","LE","VOL","VOL","MEI","PE","PD","CA"],
    "4-2-4":   ["GOL","LD","ZAG","ZAG","LE","VOL","VOL","PE","CA","CA","PD"],
    "3-5-2":   ["GOL","ZAG","ZAG","ZAG","LD","VOL","MC","ME","LE","CA","CA"],
    "5-3-2":   ["GOL","LD","ZAG","ZAG","ZAG","LE","VOL","MC","MEI","CA","CA"],
    "4-5-1":   ["GOL","LD","ZAG","ZAG","LE","ME","MC","MC","MD","MEI","CA"],
    "3-4-3":   ["GOL","ZAG","ZAG","ZAG","ME","MC","MC","MD","PE","CA","PD"],
}

POSITION_ATTACK = {
    "GOL":0,"LD":0,"ZAG":0,"LE":0,"MD":0.5,"ME":0.5,
    "VOL":0.2,"MC":0.5,"MEI":0.8,"PD":1,"CA":1,"PE":1,
}
POSITION_DEFENSE = {
    "GOL":1,"LD":1,"ZAG":1,"LE":1,"MD":0.5,"ME":0.5,
    "VOL":0.8,"MC":0.5,"MEI":0.2,"PD":0,"CA":0,"PE":0,
}

POSITION_CATEGORY = {
    "GOL":"GK","LD":"DEF","ZAG":"DEF","LE":"DEF","MD":"MID","ME":"MID",
    "VOL":"VOL","MC":"MID","MEI":"MEI","PD":"ATT","CA":"ATT","PE":"ATT",
}
POSITION_WEIGHT = {"GK":0.01,"DEF":0.12,"VOL":0.22,"MID":0.45,"MEI":0.7,"ATT":1.0}


# ═══════════════════════════════════════════════════════════════════════════════
# CONFEDERATIONS — para conquistas
# ═══════════════════════════════════════════════════════════════════════════════

CONMEBOL = {"ARG","BRA","CHI","URU","PAR","PER","COL","ECU","BOL","VEN"}
UEFA     = {"ENG","FRA","GER","ITA","ESP","POR","NED","BEL","SUI","SWE","YUG",
            "TCH","HUN","AUT","SCO","NIR","WAL","POL","DEN","CRO","SRB","URS",
            "ROU","BUL","CZE","SVK","SVN","GRE","TUR","NOR","IRL","WAL"}
CAF      = {"MAR","SEN","CMR","GHA","TUN","ALG","NGA","ZAI","EGY","IVC","ANG"}
AFC      = {"JPN","KOR","AUS","IRN","SAU","IRQ","UAE","CHN","IND","IDN","KWT",
            "PRK","OMA"}
EXTINCT  = {"URS","YUG","TCH","GDR","ZAI","FRG"}

EXTINCT_SUCCESSOR = {
    "URS": "RUS", "YUG": "SRB", "TCH": "CZE", "ZAI": "COD", "FRG": "GER",
}

COPAS_ATE_1970  = {1950, 1954, 1958, 1962, 1966, 1970}
COPAS_2010_MAIS = {2010, 2014, 2018, 2022, 2026}


# ═══════════════════════════════════════════════════════════════════════════════
# ACHIEVEMENT MODES — como obter cada conquista
# ═══════════════════════════════════════════════════════════════════════════════

ACHIEVEMENT_MODES = {
    "imperador":          "normal",
    "muralha":            "normal",
    "nos_penaltis":       "normal",
    "por_um_fio":         "normal",
    "artilheiro_torneio": "normal",
    "era_de_ouro":        "same_copa",
    "patriota":           "same_sel",
    "dream_team":         "dream_team",
    "saudosista":         "old_copas",
    "moderninho":         "modern_copas",
    "contemporaneos":     "same_decade",
    "conmebol_total":     "all_conmebol",
    "outsider":           "outsider",
    "zebra_africana":     "african",
    "zebra_asiatica":     "asian",
    "canarinho":          "brasil5",
    "cortina_de_ferro":   "extinct5",
    "cinderela":          "weak_team",
    "o_impossivel":       "impossible",
}


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def get_confederation(sel: str) -> str:
    """Retorna a confederação de uma seleção."""
    if sel in CONMEBOL: return "CONMEBOL"
    if sel in UEFA:     return "UEFA"
    if sel in CAF:      return "CAF"
    if sel in AFC:      return "AFC"
    return "OTHER"


def get_decade(copa: int) -> int:
    """Retorna a década de uma Copa (1990 → 1990, 2002 → 2000)."""
    return (copa // 10) * 10
