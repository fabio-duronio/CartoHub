#!/usr/bin/env python3
"""Ricostruisce il livello «Altre riviste»:
  dati/altre_riviste/altre_riviste.geojson

Uso:
  python3 -I scripts/build_altre_riviste.py <municipalities.geojson>

Confini ISTAT (CC BY 4.0): repository openpolis/geojson-italy (stesso commit di aggiorna-jom.yml).

Livello manuale: contiene solo le carte geologiche allegate ad articoli di riviste diverse dal
Journal of Maps, aggiunte quando un post di Geologiaintasca ne parla. Nessuna ricerca automatica.

Fonte: dati/altre_riviste/localizzazioni.csv, separatore ';', colonne
  DOI;Rivista;Titolo;Anno;Licenza;Comune;Provincia;Lat;Lon;Note
  - Titolo, Anno e Licenza si copiano dalla pagina dell'articolo: non tutte le riviste
    depositano su Crossref licenza e metadati completi, e il livello non dipende dalla rete.
  - Licenza: solo carte con licenza aperta dichiarata (es. CC BY 4.0); altrimenti la riga non va aggiunta.
  - con Lat e Lon: punto esatto (Precisione «Coordinate»), solo se scritte nel testo;
  - altrimenti Comune (nome ISTAT) + sigla Provincia: centroide del comune (Precisione «Comune»).
  Un comune non trovato, un campo obbligatorio vuoto, un DOI del Journal of Maps (va nel suo
  livello) o un DOI ripetuto fanno fallire lo script con il numero della riga.
"""
import csv
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "dati/altre_riviste/localizzazioni.csv"
OUT = ROOT / "dati/altre_riviste/altre_riviste.geojson"
OBBLIGATORI = ("DOI", "Rivista", "Titolo", "Anno", "Licenza")

# Stesse regole di localizzazione del Journal of Maps (centroide, confini ISTAT, controlli sulle coordinate)
_spec = importlib.util.spec_from_file_location("build_jom", ROOT / "scripts/build_jom.py")
jom = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(jom)


def main(p_com):
    comuni = json.load(open(p_com, encoding="utf-8"))["features"]
    per_comune = {}
    for f in comuni:
        p = f["properties"]
        per_comune[(jom.norm(p["name"]), p["prov_acr"].upper())] = f
        per_comune.setdefault((jom.norm(p["name"].split("/")[0]), p["prov_acr"].upper()), f)

    features, errori, visti = [], [], {}
    with open(CSV, encoding="utf-8-sig", newline="") as fh:
        for n, r in enumerate(csv.DictReader(fh, delimiter=";"), start=2):
            if None in r:  # colonne in più: quasi sempre un «;» dentro le Note, che ne taglierebbe il testo
                errori.append(f"riga {n}: troppe colonne (un ';' nelle Note? usare la virgola)")
                continue
            r = {k.strip(): (v or "").strip() for k, v in r.items() if k}
            if not any(r.values()):
                continue
            doi = r.get("DOI", "").removeprefix("https://doi.org/")
            vuoti = [c for c in OBBLIGATORI if not r.get(c)]
            if vuoti:
                errori.append(f"riga {n}: campi vuoti {vuoti}")
                continue
            if doi.lower().startswith(jom.JOM_PREFIX):
                errori.append(f"riga {n}: {doi} è del Journal of Maps, va in dati/journal_of_maps/localizzazioni.csv")
                continue
            if doi.lower() in visti:
                errori.append(f"riga {n}: DOI {doi} già alla riga {visti[doi.lower()]}")
                continue
            visti[doi.lower()] = n
            if r.get("Lat") and r.get("Lon"):
                try:
                    lat, lon = float(r["Lat"].replace(",", ".")), float(r["Lon"].replace(",", "."))
                except ValueError:
                    errori.append(f"riga {n}: Lat/Lon non numeriche")
                    continue
                if not (35 <= lat <= 47.5 and 6 <= lon <= 19):
                    errori.append(f"riga {n}: coordinate fuori dall'Italia ({lat}, {lon})")
                    continue
                punto, prec = [round(lon, 5), round(lat, 5)], "Coordinate"
                luogo = r.get("Comune") or f"{lat:.4f}, {lon:.4f}"
            elif r.get("Comune") and r.get("Provincia"):
                f = per_comune.get((jom.norm(r["Comune"]), r["Provincia"].upper()))
                if f is None:
                    errori.append(f"riga {n}: comune '{r['Comune']}' ({r['Provincia']}) non trovato nei confini ISTAT")
                    continue
                p = f["properties"]
                punto, prec, luogo = jom.centroide(f["geometry"]), "Comune", f"{p['name']} ({p['prov_acr']})"
            else:
                errori.append(f"riga {n}: servono Lat e Lon, oppure Comune e Provincia")
                continue
            try:
                anno = int(r["Anno"])
            except ValueError:
                errori.append(f"riga {n}: Anno non numerico ({r['Anno']})")
                continue
            features.append({
                "type": "Feature",
                "properties": {
                    "Title": r["Titolo"],
                    "DOI": doi,
                    "URL": f"https://doi.org/{doi}",
                    "Location": luogo,
                    "Type": "Research Map",
                    "Rivista": r["Rivista"],
                    "Anno": anno,
                    "Licenza": r["Licenza"],
                    "Precisione": prec,
                    "Fonte": "Pagina dell'articolo (metadati); localizzazione manuale (Geologiaintasca)",
                },
                "geometry": {"type": "Point", "coordinates": punto},
            })
    if errori:
        sys.exit("Errori in " + str(CSV.relative_to(ROOT)) + ":\n  " + "\n  ".join(errori))
    features.sort(key=lambda f: f["properties"]["DOI"].lower())
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": features},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Altre riviste: {len(features)} articoli")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
