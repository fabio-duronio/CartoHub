#!/usr/bin/env python3
"""Controllo qualità dei GeoJSON del progetto Geologiaintasca – Cartografia geologica italiana.

Uso:  python3 scripts/valida_dati.py
Esce con codice 1 se trova errori bloccanti (E), 0 se ci sono solo avvisi (W).
Non richiede librerie esterne.
"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "dati"
CAMPI = {"Title", "URL", "Location", "Type"}
BBOX_ITALIA = (6.0, 35.0, 19.0, 47.5)  # lon_min, lat_min, lon_max, lat_max
# Prefissi DOI del Journal of Maps: attuale (Taylor & Francis) e storici (2005-2011)
JOM_PREFIX = ("10.1080/17445647.", "10.1080/jom.", "10.4113/jom.")

problemi = []
doi_jom = {}  # DOI -> file, per i duplicati tra i due livelli Journal of Maps


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
        if url and not url.startswith("https://"):
            segnala("W", nome, f"#{i} URL non https: {url}")
        titoli[str(p.get("Title", "")).strip().lower()] += 1
        if p.get("DOI"):
            dois[p["DOI"]] += 1
        if g.get("type") == "Point":
            x, y = g["coordinates"][:2]
            if not (BBOX_ITALIA[0] <= x <= BBOX_ITALIA[2] and BBOX_ITALIA[1] <= y <= BBOX_ITALIA[3]):
                segnala("E", nome, f"#{i} '{p.get('Title')}' fuori dall'Italia: {x},{y}")
            continue
        if g.get("type") == "Polygon":
            anelli = g["coordinates"]
        elif g.get("type") == "MultiPolygon":
            anelli = [r for pol in g["coordinates"] for r in pol]
        else:
            segnala("E", nome, f"#{i} geometria mancante o di tipo non gestito: {g.get('type')}")
            continue
        if any(r[0] != r[-1] for r in anelli):
            segnala("E", nome, f"#{i} anello non chiuso")
        if g["type"] == "Polygon" and len(anelli[0]) == 5:
            rettangoli += 1
        x0, y0, x1, y1 = bbox(anelli)
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
        fuori = [x for x in dois if not str(x).lower().startswith(JOM_PREFIX)]
        if fuori:
            segnala("E", nome, f"{len(fuori)} DOI non appartengono al Journal of Maps (prefissi {JOM_PREFIX})")
        for x in dois:
            k = str(x).lower()
            if k in doi_jom:
                segnala("E", nome, f"DOI {x} presente anche in {doi_jom[k]}")
            doi_jom.setdefault(k, nome)
        regionale = "jom_regionali" in nome
        for f in fs:
            p = f["properties"]
            prec, ambito = p.get("Precisione"), p.get("Ambito")
            if not regionale and prec in ("Regione", "Provincia"):
                segnala("E", nome, f"{p.get('DOI')}: precisione '{prec}' nel livello principale (va in jom_regionali)")
            if regionale and (prec not in ("Regione", "Provincia") or ambito not in ("Regionale", "Da localizzare")):
                segnala("E", nome, f"{p.get('DOI')}: precisione '{prec}' / ambito '{ambito}' non previsti nel livello regionale")
            if not p.get("Dettagli"):
                segnala("E", nome, f"{p.get('DOI')}: campo Dettagli vuoto (eseguire scripts/dettagli_popup.py)")

    if "carta_100k" in nome:
        # Punti di controllo: il foglio deve contenere la località che gli dà il nome
        controlli = {"Pescara": (14.21, 42.46), "Sulmona": (13.93, 42.05), "Lanciano": (14.39, 42.23)}
        visti = set()
        for f in fs:
            loc = str(f["properties"].get("Location", ""))
            if loc in controlli:
                visti.add(loc)
                x, y = controlli[loc]
                g = f["geometry"]
                anelli = g["coordinates"] if g["type"] == "Polygon" else [r for q in g["coordinates"] for r in q]
                x0, y0, x1, y1 = bbox(anelli)
                if not (x0 <= x <= x1 and y0 <= y <= y1):
                    segnala("E", nome, f"il foglio {loc} non contiene {loc}: quadro d'unione non georeferenziato")
        for loc in set(controlli) - visti:
            segnala("E", nome, f"foglio di controllo '{loc}' assente")
        if len(fs) < 270:
            segnala("E", nome, f"solo {len(fs)} fogli: quadro d'unione ISPRA incompleto?")
        senza = sum(1 for f in fs if not f["properties"].get("N_edizioni"))
        if senza > 30:
            segnala("E", nome, f"{senza} fogli senza schede: catalogo ISPRA non raggiunto o cambiato?")
        elif senza:
            segnala("W", nome, f"{senza} fogli senza schede nel catalogo ISPRA")

    if "carg" in nome:
        # Punti di controllo: località note che devono cadere nel foglio con quel nome.
        controlli = {"L'Aquila": (13.40, 42.35), "Napoli": (14.25, 40.85), "Genova": (8.93, 44.41),
                     "Sciacca": (13.08, 37.51)}
        trovati = set()
        for f in fs:
            loc = str(f["properties"].get("Location", ""))
            if loc in controlli:
                trovati.add(loc)
                x, y = controlli[loc]
                g = f["geometry"]
                anelli = g["coordinates"] if g["type"] == "Polygon" else [r for q in g["coordinates"] for r in q]
                x0, y0, x1, y1 = bbox(anelli)
                if not (x0 <= x <= x1 and y0 <= y <= y1):
                    segnala("E", nome, f"il foglio {loc} non contiene {loc} ({x},{y}): griglia non georeferenziata")
        for loc in set(controlli) - trovati:
            segnala("E", nome, f"foglio di controllo '{loc}' assente")
        # Stati: diciture di CARG-GATE copiate testualmente; una dicitura nuova è solo un avviso
        ufficiali = {"", "Stampato", "In attesa di stampa", "In allestimento per la stampa", "Rilevamento in corso"}
        nuovi = Counter(str(f["properties"].get("Stato", "")) for f in fs
                        if str(f["properties"].get("Stato", "")) not in ufficiali)
        if nuovi:
            segnala("W", nome, f"diciture di stato non previste (da aggiungere a stili e legenda): {dict(nuovi)}")
        if len(fs) < 600:
            segnala("E", nome, f"solo {len(fs)} fogli: risposta di CARG-GATE incompleta?")

    print(f"{nome}: {len(fs)} feature")


def controlla_csv_jom():
    """Un DOI può stare in un solo file (e una sola volta) tra localizzazioni, regionali ed esclusioni."""
    cartella = ROOT / "journal_of_maps"
    visti = {}
    for nome in ("localizzazioni.csv", "regionali.csv", "esclusioni.csv"):
        path = cartella / nome
        if not path.exists():
            continue
        with open(path, encoding="utf-8-sig", newline="") as fh:
            for n, r in enumerate(csv.DictReader(fh, delimiter=";"), start=2):
                doi = (r.get("DOI") or "").strip().lower().removeprefix("https://doi.org/")
                if not doi:
                    continue
                if doi in visti:
                    segnala("E", f"dati/journal_of_maps/{nome}", f"riga {n}: DOI {doi} già in {visti[doi]}")
                else:
                    visti[doi] = f"{nome} riga {n}"


def main():
    files = sorted(ROOT.rglob("*.geojson"))
    for f in files:
        controlla_file(f)
    controlla_csv_jom()
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
