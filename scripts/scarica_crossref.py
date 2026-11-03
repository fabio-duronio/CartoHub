#!/usr/bin/env python3
"""Scarica da Crossref i metadati del Journal of Maps sull'Italia.

Uso:
  python3 -I scripts/scarica_crossref.py <output.json>

1. Ricerca: ISSN 1744-5647 con "Italy" nei metadati bibliografici (paginata con cursore).
2. Integrazione: ogni DOI elencato in dati/journal_of_maps/localizzazioni.csv che la
   ricerca non ha restituito (es. titolo senza "Italy") viene scaricato singolarmente.

L'output ha la stessa forma della risposta Crossref ({"message": {"items": [...]}}),
così build_jom.py lo legge senza modifiche.
"""
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANUALI = ROOT / "dati/journal_of_maps/localizzazioni.csv"
API = "https://api.crossref.org/works"
CAMPI = "DOI,title,issued,license,container-title,ISSN"
HEADERS = {"User-Agent": "IGC-Hub/1.0 (https://github.com/fabio-duronio/cartografia-geologica-italiana)"}


def get(url, tentativi=4):
    for i in range(tentativi):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if i == tentativi - 1:
                raise
        except (urllib.error.URLError, TimeoutError):
            if i == tentativi - 1:
                raise
        time.sleep(5 * (i + 1))


def ricerca():
    items, cursore = [], "*"
    while True:
        q = urllib.parse.urlencode({"filter": "issn:1744-5647", "query.bibliographic": "Italy",
                                    "rows": 500, "select": CAMPI, "cursor": cursore})
        msg = get(f"{API}?{q}")["message"]
        items += msg["items"]
        if not msg["items"] or len(items) >= msg["total-results"]:
            return items
        cursore = msg["next-cursor"]


def doi_manuali():
    if not MANUALI.exists():
        return []
    with open(MANUALI, encoding="utf-8-sig", newline="") as fh:
        return [r["DOI"].strip().lower().removeprefix("https://doi.org/")
                for r in csv.DictReader(fh, delimiter=";") if (r.get("DOI") or "").strip()]


def main(out):
    items = ricerca()
    print(f"Ricerca Crossref: {len(items)} record")
    presenti = {it["DOI"].lower() for it in items}
    for doi in doi_manuali():
        if doi in presenti:
            continue
        r = get(f"{API}/{urllib.parse.quote(doi)}")
        if r is None:
            sys.exit(f"DOI non trovato su Crossref (controlla localizzazioni.csv): {doi}")
        items.append({k: v for k, v in r["message"].items() if k in CAMPI.split(",")})
        presenti.add(doi)
        print(f"Aggiunto da localizzazioni.csv: {doi}")
        time.sleep(1)
    Path(out).write_text(json.dumps({"message": {"items": items}}, ensure_ascii=False), encoding="utf-8")
    print(f"Totale: {len(items)} record in {out}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
