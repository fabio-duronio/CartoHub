#!/usr/bin/env python3
"""Ricostruisce dati/carg/carg_50k_fogli.geojson dal quadro d'unione ufficiale ISPRA.

Uso:
  python3 -I scripts/build_carg.py <quadro_unione_ispra.geojson>

Fonte: ISPRA – Servizio Geologico d'Italia, servizio "Antropico25k", layer 0
"Quadro unione Fogli" (fogli geologici 1:50.000, CARG e pre-CARG):
https://sinacloud.isprambiente.it/arcgisgeo/rest/services/servizi/Antropico25k/MapServer/0
Scaricato con: query?where=1=1&outFields=*&returnGeometry=true&outSR=4326&f=geojson
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dati/carg/carg_50k_fogli.geojson"
PAGINA_CARG = ("https://www.isprambiente.gov.it/it/attivita/suolo-e-territorio/cartografia/"
               "carte-geologiche-e-geotematiche/carta-geologica-alla-scala-1-a-50000")
FONTE = "ISPRA - Servizio Geologico d'Italia, Quadro unione Fogli 1:50.000"

# Interpretazione dei codici del campo "stato" (non documentati nel servizio).
STATO = {
    "bd": "Realizzato",
    "finanziati": "Finanziato / in corso",
}


MINUSCOLE = {"di", "del", "della", "delle", "dei", "e", "ed", "da", "in", "la", "le", "il", "sul", "al"}


def formatta_nome(nome):
    """'ISOLE DI STROMBOLI E PANAREA' -> 'Isole di Stromboli e Panarea'."""
    testo = re.sub(r"\s*-\s*", "-", " ".join(str(nome or "").split()))
    parole = testo.lower().split(" ")
    out = []
    for i, w in enumerate(parole):
        if i and w in MINUSCOLE:
            out.append(w)
        else:
            out.append("-".join(x[:1].upper() + x[1:] for x in w.split("-")))
    testo = " ".join(out)
    # apostrofi: "l'aquila" -> "L'Aquila", "vetta d'italia" -> "Vetta d'Italia"
    testo = re.sub(r"(\w)'(\w)", lambda m: m.group(1) + "'" + m.group(2).upper(), testo)
    return re.sub(r" D'", " d'", testo)


def url_https(u):
    """Gli URL ISPRA usano ancora http e il vecchio dominio isprambiente.it."""
    if not u:
        return None
    u = u.strip().replace("http://www.isprambiente.it/", "https://www.isprambiente.gov.it/")
    return u.replace("http://www.isprambiente.gov.it/", "https://www.isprambiente.gov.it/")


def main(path_in):
    src = json.load(open(path_in, encoding="utf-8"))["features"]
    # I fogli accorpati (es. "1-7") sono più poligoni con lo stesso numero:
    # li uniamo in una sola feature MultiPolygon, così un clic = un foglio pubblicato.
    gruppi = {}
    for f in sorted(src, key=lambda x: x["properties"]["nfog"]):
        gruppi.setdefault(str(f["properties"]["foglio"]).strip(), []).append(f)

    out = []
    for foglio, parti in gruppi.items():
        f = next((x for x in parti if x["properties"].get("url")), parti[0])
        p = f["properties"]
        nome = formatta_nome(p["nome"])
        stati = [q["properties"].get("stato") for q in parti]
        stato_raw = next((s for s in stati if s not in (None, "<Null>")), None)
        url = url_https(p.get("url"))
        poligoni = [[[[round(x, 5), round(y, 5)] for x, y in r] for r in q["geometry"]["coordinates"]]
                    for q in parti]
        geom = ({"type": "Polygon", "coordinates": poligoni[0]} if len(poligoni) == 1
                else {"type": "MultiPolygon", "coordinates": poligoni})
        estensioni = sorted({q["properties"].get("estensione") for q in parti if q["properties"].get("estensione")})
        out.append({
            "type": "Feature",
            "properties": {
                "Title": f"Foglio {foglio} – {nome}",
                "Foglio": foglio,
                "Location": nome,
                "Type": "Official Map",
                "Stato": STATO.get(stato_raw, "Non avviato o non indicato"),
                "Raster": "Sì" if p.get("raster") == "SI" else "No",
                "Estensione": " + ".join(estensioni),
                "URL": url or PAGINA_CARG,
                "URL_tipo": "Pagina del foglio" if url else "Pagina generale CARG",
                "Fonte": FONTE,
            },
            "geometry": geom,
        })
    fc = {"type": "FeatureCollection", "features": out}
    OUT.write_text(json.dumps(fc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Scritti {len(out)} fogli in {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
