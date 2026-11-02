#!/usr/bin/env python3
"""Controllo qualità dei GeoJSON di IGC-Hub.

Uso:  python3 scripts/valida_dati.py
Esce con codice 1 se trova errori bloccanti (E), 0 se ci sono solo avvisi (W).
Non richiede librerie esterne.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "dati"
CAMPI = {"Title", "URL", "Location", "Type"}
BBOX_ITALIA = (6.0, 35.0, 19.0, 47.5)  # lon_min, lat_min, lon_max, lat_max
JOM_PREFIX = "10.1080/17445647."

problemi = []


def segnala(livello, file, msg):
    problemi.append((livello, file, msg))


def bbox(coords):
    xs = [p[0] for anello in coords for p in anello]
    ys = [p[1] for anello in coords for p in anello]
    return min(xs), min(ys), max(xs), max(ys)


def controlla_file(path):
    nome = path.relative_to(ROOT.parent).as_posix()
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        segnala("E", nome, f"JSON non valido: {e}")
        return
    fs = d.get("features", [])
    if not fs:
        segnala("E", nome, "nessuna feature")
        return

    titoli = Counter()
    dois = Counter()
    rettangoli = 0
    for i, f in enumerate(fs):
        p = f.get("properties") or {}
        g = f.get("geometry") or {}
        mancanti = CAMPI - p.keys()
        if mancanti:
            segnala("E", nome, f"#{i} campi mancanti: {sorted(mancanti)}")
        url = str(p.get("URL", ""))
        if not url.startswith("https://"):
            segnala("W", nome, f"#{i} URL non https: {url}")
        titoli[str(p.get("Title", "")).strip().lower()] += 1
        if p.get("DOI"):
            dois[p["DOI"]] += 1
        if g.get("type") != "Polygon":
            continue
        ring = g["coordinates"][0]
        if ring[0] != ring[-1]:
            segnala("E", nome, f"#{i} anello non chiuso")
        if len(ring) == 5:
            rettangoli += 1
        x0, y0, x1, y1 = bbox(g["coordinates"])
        if x0 < BBOX_ITALIA[0] or y0 < BBOX_ITALIA[1] or x1 > BBOX_ITALIA[2] or y1 > BBOX_ITALIA[3]:
            segnala("E", nome, f"#{i} '{p.get('Title')}' fuori dall'Italia: {x0},{y0},{x1},{y1}")

    for t, c in titoli.items():
        if c > 1:
            segnala("E", nome, f"titolo duplicato x{c}: {t}")
    for doi, c in dois.items():
        if c > 1:
            segnala("E", nome, f"DOI duplicato x{c}: {doi}")
    if rettangoli == len(fs):
        segnala("W", nome, f"tutte le {len(fs)} geometrie sono rettangoli (bounding box, non perimetri reali)")

    if "journal_of_maps" in nome:
        fuori = [x for x in dois if not str(x).startswith(JOM_PREFIX)]
        if fuori:
            segnala("E", nome, f"{len(fuori)} DOI non appartengono al Journal of Maps (prefisso {JOM_PREFIX})")

    if "carg" in nome:
        # Verifica di plausibilità: il Foglio 1 (Passo di Resia) si trova intorno a 10.5°E, 46.8°N.
        for f in fs:
            if str(f["properties"].get("Title", "")).startswith("Foglio 1 "):
                x0, y0, x1, y1 = bbox(f["geometry"]["coordinates"])
                if not (x0 <= 10.5 <= x1 + 0.5 and y0 - 0.5 <= 46.8 <= y1 + 0.5):
                    segnala("E", nome, f"Foglio 1 posizionato a {x0}-{x1}°E: griglia non georeferenziata correttamente")
        dimensioni = Counter(
            (round(bbox(f["geometry"]["coordinates"])[2] - bbox(f["geometry"]["coordinates"])[0], 3),
             round(bbox(f["geometry"]["coordinates"])[3] - bbox(f["geometry"]["coordinates"])[1], 3))
            for f in fs)
        attesa = (0.333, 0.2)  # fogli IGM 1:50.000: 20' x 12'
        if attesa not in dimensioni:
            segnala("E", nome, f"dimensione fogli {dict(dimensioni)} diversa da 20'x12' ({attesa}°)")
        segnaposto = sum(1 for f in fs if not re.match(r"^10\.", str(f["properties"].get("DOI", ""))))
        if segnaposto:
            segnala("W", nome, f"{segnaposto} valori DOI non sono DOI (testo segnaposto)")

    print(f"{nome}: {len(fs)} feature")


def main():
    files = sorted(ROOT.rglob("*.geojson"))
    for f in files:
        controlla_file(f)
    print()
    for livello in ("E", "W"):
        righe = [p for p in problemi if p[0] == livello]
        etichetta = "ERRORI" if livello == "E" else "AVVISI"
        print(f"{etichetta}: {len(righe)}")
        for _, file, msg in righe[:40]:
            print(f"  [{livello}] {file}: {msg}")
        if len(righe) > 40:
            print(f"  ... altri {len(righe) - 40}")
    sys.exit(1 if any(p[0] == "E" for p in problemi) else 0)


if __name__ == "__main__":
    main()
