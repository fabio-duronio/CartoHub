#!/usr/bin/env python3
"""Ricostruisce dati/geoportali_regionali/geoportali_regionali.geojson
sostituendo i rettangoli con i confini amministrativi ISTAT (CC BY 4.0).

Uso:
  python3 -I scripts/build_geoportali.py <limits_IT_regions.geojson> <limits_IT_provinces.geojson>

I file di input sono quelli del repository openpolis/geojson-italy
(confini ISTAT, licenza CC BY 4.0). Attributi e link dei geoportali
vengono presi dal GeoJSON esistente, quindi non vanno ridigitati.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dati/geoportali_regionali/geoportali_regionali.geojson"
TOLLERANZA = 0.003  # gradi, circa 300 m: sufficiente alla scala nazionale
ATTRIBUZIONE = "Confini: ISTAT (CC BY 4.0), via openpolis/geojson-italy"


def dp(punti, tol):
    """Semplificazione Douglas-Peucker di una polilinea."""
    if len(punti) < 3:
        return punti
    (x1, y1), (x2, y2) = punti[0], punti[-1]
    dx, dy = x2 - x1, y2 - y1
    norma = (dx * dx + dy * dy) ** 0.5
    dmax, idx = -1.0, 0
    for i in range(1, len(punti) - 1):
        px, py = punti[i]
        if norma == 0:
            d = ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
        else:
            d = abs(dy * px - dx * py + x2 * y1 - y2 * x1) / norma
        if d > dmax:
            dmax, idx = d, i
    if dmax <= tol:
        return [punti[0], punti[-1]]
    return dp(punti[: idx + 1], tol)[:-1] + dp(punti[idx:], tol)


def semplifica_anello(anello):
    a = dp(anello, TOLLERANZA)
    if len(a) < 4:  # isolotti troppo piccoli: scartati
        return None
    if a[0] != a[-1]:
        a.append(a[0])
    return [[round(x, 4), round(y, 4)] for x, y in a]


def semplifica(geom):
    poligoni = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    out = []
    for pol in poligoni:
        esterno = semplifica_anello(pol[0])
        if esterno is None:
            continue
        buchi = [b for b in (semplifica_anello(r) for r in pol[1:]) if b]
        out.append([esterno] + buchi)
    return {"type": "MultiPolygon", "coordinates": out}


def norm(s):
    return (s.lower().replace("regione ", "").replace("-", " ").replace("/", " ")
            .replace("'", " ").replace("  ", " ").strip())


def main(path_reg, path_prov):
    regioni = json.load(open(path_reg, encoding="utf-8"))["features"]
    province = json.load(open(path_prov, encoding="utf-8"))["features"]
    attuale = json.load(open(OUT, encoding="utf-8"))

    per_nome = {}
    for f in regioni:
        nome = f["properties"]["reg_name"]
        per_nome[norm(nome.split("/")[0])] = f
        per_nome[norm(nome)] = f
    for f in province:
        if f["properties"].get("prov_acr") in ("TN", "BZ"):
            per_nome["prov_" + f["properties"]["prov_acr"]] = f

    nuove, mancanti = [], []
    for f in attuale["features"]:
        titolo = f["properties"]["Title"]
        if "(Trento)" in titolo:
            chiave = "prov_TN"
        elif "(Bolzano)" in titolo:
            chiave = "prov_BZ"
        else:
            chiave = norm(titolo)
        src = per_nome.get(chiave)
        if src is None:
            # tentativo per prefisso (es. "valle d aosta" vs "valle d aosta vallée d aoste")
            src = next((v for k, v in per_nome.items() if k.startswith(chiave) or chiave.startswith(k)), None)
        if src is None:
            mancanti.append(titolo)
            continue
        props = dict(f["properties"])
        props["Type"] = "Regional Portal"
        props["Fonte_confini"] = ATTRIBUZIONE
        nuove.append({"type": "Feature", "properties": props, "geometry": semplifica(src["geometry"])})

    if mancanti:
        sys.exit(f"Regioni non abbinate: {mancanti}")
    attuale["features"] = nuove
    OUT.write_text(json.dumps(attuale, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Scritte {len(nuove)} feature in {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
