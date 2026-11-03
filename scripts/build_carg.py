#!/usr/bin/env python3
"""Ricostruisce dati/carg/carg_50k_fogli.geojson dai dati di CARG-GATE (ISPRA).

Uso:
  python3 -I scripts/build_carg.py <carggate.json> <limits_IT_regions.geojson>

Fonte: CARG-GATE, portale del Servizio Geologico d'Italia (ISPRA), licenza CC BY 4.0
https://progetto-carg.isprambiente.it/cartografiaCARG/index.php?source=cartageologica
Il file di input si ottiene con scripts/scarica_carggate.py.

Regole:
- lo stato è copiato testualmente da CARG-GATE (campo stato_realizzazione):
  "Stampato", "In attesa di stampa", "In allestimento per la stampa", "Rilevamento in corso".
  Se il portale non indica uno stato, il campo resta vuoto: nessuno stato viene dedotto.
- i link puntano alla scheda del foglio sul portale (servono regione e numero del foglio)
  e ai DOI ufficiali della carta e delle note illustrative (archivio OAR di ISPRA).
- la regione serve solo a costruire il link: si ricava dai confini ISTAT (CC BY 4.0).
"""
import json
import re
import sys
import urllib.parse
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dati/carg/carg_50k_fogli.geojson"
PORTALE = "https://progetto-carg.isprambiente.it/cartografiaCARG/index.php"
FONTE = "CARG-GATE – ISPRA, Servizio Geologico d'Italia (CC BY 4.0)"
STATI_UFFICIALI = {"Stampato", "In attesa di stampa", "In allestimento per la stampa", "Rilevamento in corso"}
# Nomi ISTAT -> nomi usati da CARG-GATE (dove differiscono)
REGIONE_PORTALE = {"Trentino-Alto Adige/Südtirol": "Trentino-Alto Adige",
                   "Valle d'Aosta/Vallée d'Aoste": "Valle d'Aosta"}
MINUSCOLE = {"di", "del", "della", "delle", "dei", "e", "ed", "da", "in", "la", "le", "il", "sul", "al"}


def formatta_nome(nome):
    """'ISOLE DI STROMBOLI E PANAREA' -> 'Isole di Stromboli e Panarea'."""
    testo = re.sub(r"\s*-\s*", "-", " ".join(str(nome or "").split()))
    out = []
    for i, w in enumerate(testo.lower().split(" ")):
        out.append(w if i and w in MINUSCOLE else "-".join(x[:1].upper() + x[1:] for x in w.split("-")))
    testo = re.sub(r"(\w)'(\w)", lambda m: m.group(1) + "'" + m.group(2).upper(), " ".join(out))
    return re.sub(r" D'", " d'", testo)


def numero_portale(numero):
    """'001-007' -> '1-7', '628' -> '628', '577BIS' -> '577bis' (come nelle schede del portale)."""
    parti = []
    for p in str(numero).split("-"):
        m = re.match(r"0*(\d+)(.*)", p.strip())
        parti.append((m.group(1) + m.group(2).lower()) if m else p.strip().lower())
    return "-".join(parti)


def anelli(geom):
    pol = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    return pol


def dentro(x, y, poligono):
    """Punto in poligono (con buchi), ray casting."""
    def nel_ring(r):
        c = False
        for (x0, y0), (x1, y1) in zip(r, r[1:]):
            if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
                c = not c
        return c
    return nel_ring(poligono[0]) and not any(nel_ring(h) for h in poligono[1:])


def regione_del_foglio(geom, regioni):
    """Regione con più punti di campionamento dentro il foglio (griglia 7x7 sul riquadro)."""
    xs = [p[0] for pol in anelli(geom) for p in pol[0]]
    ys = [p[1] for pol in anelli(geom) for p in pol[0]]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    voti = Counter()
    for i in range(7):
        for j in range(7):
            x = x0 + (x1 - x0) * (i + 0.5) / 7
            y = y0 + (y1 - y0) * (j + 0.5) / 7
            if not any(dentro(x, y, pol) for pol in anelli(geom)):
                continue
            for nome, polys, (bx0, by0, bx1, by1) in regioni:
                if not (bx0 <= x <= bx1 and by0 <= y <= by1):  # filtro rapido sul riquadro
                    continue
                if any(dentro(x, y, p) for p in polys):
                    voti[nome] += 1
                    break
    if voti:
        return voti.most_common(1)[0][0]
    # foglio quasi tutto in mare: regione col centroide più vicino al centro del foglio
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    def dist(item):
        pts = [p for pol in item[1] for p in pol[0]]
        return min((p[0] - cx) ** 2 + (p[1] - cy) ** 2 for p in pts)
    return min(regioni, key=dist)[0]


def doi_url(d):
    return f"https://doi.org/{d}" if d else ""


def main(p_cg, p_reg):
    fc = json.load(open(p_cg, encoding="utf-8"))
    regioni = []
    for f in json.load(open(p_reg, encoding="utf-8"))["features"]:
        polys = anelli(f["geometry"])
        xs = [q[0] for pol in polys for q in pol[0]]
        ys = [q[1] for pol in polys for q in pol[0]]
        regioni.append((REGIONE_PORTALE.get(f["properties"]["reg_name"], f["properties"]["reg_name"]),
                        polys, (min(xs), min(ys), max(xs), max(ys))))

    out, stati, sconosciuti = [], Counter(), Counter()
    for f in sorted(fc["features"], key=lambda f: f["properties"].get("id_foglio") or 0):
        p = f["properties"]
        numero = numero_portale(p.get("numero_foglio"))
        nome = formatta_nome(p.get("nome_foglio"))
        stato = (p.get("stato_realizzazione") or "").strip()
        if stato and stato not in STATI_UFFICIALI:
            sconosciuti[stato] += 1  # dicitura nuova del portale: la si tiene così com'è
        stati[stato or "(nessuno)"] += 1
        regione = regione_del_foglio(f["geometry"], regioni)
        url = PORTALE + "?" + urllib.parse.urlencode(
            {"source": "cartageologica", "regione": regione, "foglio": numero})
        geom = {"type": "MultiPolygon",
                "coordinates": [[[[round(x, 5), round(y, 5)] for x, y in r] for r in pol]
                                for pol in anelli(f["geometry"])]}
        out.append({
            "type": "Feature",
            "properties": {
                "Title": f"Foglio {numero} – {nome}",
                "Foglio": numero,
                "Location": nome,
                "Type": "Official Map",
                "Stato": stato,
                "Anno_stampa": p.get("anno_stampa") or "",
                "Coordinatori": p.get("coordinatori_scientifici") or "",
                "Banca_dati": p.get("banca_dati") or "",
                "Regione": regione,
                "URL": url,
                "DOI_carta": doi_url(p.get("doi_foglio")),
                "DOI_note": doi_url(p.get("doi_note_illustrative")),
                "Fonte": FONTE,
            },
            "geometry": geom,
        })

    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": out},
                              ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Fogli: {len(out)} ({OUT.stat().st_size // 1024} KB)")
    print("Stati:", dict(stati))
    if sconosciuti:
        print("ATTENZIONE: diciture di stato nuove su CARG-GATE:", dict(sconosciuti))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
