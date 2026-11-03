#!/usr/bin/env python3
"""Costruisce dati/carta_100k/carta_100k_fogli.geojson: Carta Geologica d'Italia 1:100.000.

Uso:
  python3 -I scripts/build_100k.py            # scarica le fonti (serve accesso ai siti ISPRA)
  python3 -I scripts/build_100k.py <quadro.geojson> <catalogo.json>   # da file già scaricati

Fonti (ISPRA – Servizio Geologico d'Italia):
- quadro d'unione dei fogli: servizio "geologica100k", layer 1 "CGI100K_Quadro_di_unione"
  https://sinacloud.isprambiente.it/arcgisgeo/rest/services/servizi/geologica100k/MapServer/1
- edizioni e copie digitali: catalogo OPAC della Biblioteca ISPRA (https://sbnweb.isprambiente.it/opac2/GEA)

Regole:
- una scheda del catalogo è un foglio della serie se è materiale cartografico in scala 1:100.000
  (campo UNIMARC 123 $b100000) e indica il numero del foglio nella serie (campo 461 $v);
- edizione e anno sono copiati dalla scheda (campi 205 e 210); se l'edizione manca resta "non indicata";
- il link porta alla scheda del catalogo, non alla scansione: la licenza delle scansioni non è dichiarata;
- un foglio senza schede resta sulla mappa con la dicitura "Nessuna scheda trovata nel catalogo ISPRA".
"""
import json
import re
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dati/carta_100k/carta_100k_fogli.geojson"
QUADRO = ("https://sinacloud.isprambiente.it/arcgisgeo/rest/services/servizi/geologica100k/MapServer/1/query"
          "?where=1%3D1&outFields=SHEET,TITLE,CURRENT_ED,EDITION_DA&returnGeometry=true&outSR=4326&f=geojson")
API = "https://sbnweb.isprambiente.it/opac2/api/GEA/search/documents"
SCHEDA = "https://sbnweb.isprambiente.it/opac2/GEA/dettaglio/documento/"
QUERY = ["foglio della Carta Geologica d'Italia 1:100.000", "foglio della Carta geologica d'Italia al 100.000",
         "Carta geologica d'Italia alla scala 1:100.000", "carta geologica d'italia 100000",
         "Carta geologica delle Tre Venezie"]
HEADERS = {"Content-Type": "application/json", "Accept": "application/json",
           "User-Agent": "IGC-Hub/1.0 (https://github.com/fabio-duronio/cartografia-geologica-italiana)",
           "Referer": "https://sbnweb.isprambiente.it/opac2/GEA/result"}
FONTE = "ISPRA – Servizio Geologico d'Italia: quadro d'unione 1:100.000 e catalogo della Biblioteca ISPRA"


def http_json(url, dati=None):
    for i in range(4):
        try:
            req = urllib.request.Request(url, data=dati, headers=HEADERS if dati else {"User-Agent": HEADERS["User-Agent"]})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except Exception:
            if i == 3:
                raise
            time.sleep(10 * (i + 1))


def scarica_catalogo():
    record = {}
    for q in QUERY:
        start = 0
        while True:
            body = {"start": start, "maxRows": 100, "sort": "score", "order": "asc",
                    "filters": {"operator": "AND", "filters": [{"operator": "AND", "filters": [
                        {"field": "group", "value": "", "otherFiltersGroup": [{"field": "any", "value": q}]}]}]}}
            sd = http_json(API, json.dumps(body).encode())["solrDocs"]
            docs = sd.get("documenti", [])
            for d in docs:
                record.setdefault(d["id"], {k: d.get(k) for k in ("id", "recordType", "syntetic_title", "unimarc")})
            start += len(docs)
            if not docs or start >= sd.get("numFound", 0):
                break
            time.sleep(1)
    return list(record.values())


MINUSCOLE = {"di", "del", "della", "delle", "dei", "e", "ed", "da", "in", "la", "le", "il", "sul", "al"}


def formatta_nome(nome):
    """'PASSO DEL BRENNERO' -> 'Passo del Brennero', "ISOLA D'ISCHIA" -> "Isola d'Ischia"."""
    out = []
    for i, w in enumerate(" ".join(str(nome or "").split()).lower().split(" ")):
        out.append(w if i and w in MINUSCOLE else "-".join(x[:1].upper() + x[1:] for x in w.split("-")))
    testo = re.sub(r"(\w)'(\w)", lambda m: m.group(1) + "'" + m.group(2).upper(), " ".join(out))
    testo = re.sub(r"\.(\w)", lambda m: "." + m.group(1).upper(), testo)  # S.efisio -> S.Efisio
    return re.sub(r" D'", " d'", testo)


def norm_foglio(s):
    return re.sub(r"\s+", "", str(s)).upper().lstrip("0")


def campo(u, tag, sub):
    m = re.search(rf"\n{tag} [^\n]*?\${sub}([^\n$]+)", u)
    return m.group(1).strip() if m else ""


def edizione_leggibile(ed):
    e = ed.strip().rstrip(".").strip()
    m = re.match(r"^(\d+)\s*\.?\s*ed(?:izione)?\b", e, re.I)
    return f"{m.group(1)}ª edizione" if m else (e or "edizione non indicata")


def schede_per_foglio(catalogo):
    per_foglio = defaultdict(list)
    for x in catalogo:
        u = x.get("unimarc") or ""
        if x.get("recordType") != "e" or not re.search(r"\n123 [^\n]*\$b100000", u):
            continue
        v = campo(u, "461", "v")
        if not v:
            continue
        anno = re.search(r"\d{4}", campo(u, "210", "d"))
        titolo = campo(u, "200", "a")
        serie = "Carta geologica delle Tre Venezie" if "Tre Venezie" in u else "Carta Geologica d'Italia"
        ed = {
            "id": x["id"],
            "anno": int(anno.group(0)) if anno else None,
            "edizione": edizione_leggibile(campo(u, "205", "a")),
            "titolo": titolo,
            "serie": serie,
            "digitale": bool(re.search(r"\n856 ", u)),
            "nota": (re.search(r"\n421 [^\n]*\$1001(GEA\d+)", u) or [None, None])[1],
        }
        for parte in re.split(r"\s*(?:-|–|,| e )\s*", v):
            if parte.strip():
                per_foglio[norm_foglio(parte)].append(ed)
    return per_foglio


def main(p_quadro=None, p_catalogo=None):
    quadro = json.load(open(p_quadro, encoding="utf-8")) if p_quadro else http_json(QUADRO)
    catalogo = json.load(open(p_catalogo, encoding="utf-8")) if p_catalogo else scarica_catalogo()
    per_foglio = schede_per_foglio(catalogo)

    out, senza = [], []
    for f in sorted(quadro["features"], key=lambda f: (len(str(f["properties"]["SHEET"])), str(f["properties"]["SHEET"]))):
        p = f["properties"]
        foglio = str(p["SHEET"]).strip()
        nome = " – ".join(formatta_nome(t) for t in str(p["TITLE"]).split(" - "))
        eds = {}
        for parte in re.split(r"\s*-\s*", foglio):
            for e in per_foglio.get(norm_foglio(parte), []):
                eds[e["id"]] = e
        eds = sorted(eds.values(), key=lambda e: (e["anno"] or 0, e["id"]))
        if not eds:
            senza.append(foglio)
        con_copia = [e for e in eds if e["digitale"]]
        principale = (con_copia or eds or [None])[-1]
        elenco = "; ".join(
            f"{e['edizione']} {e['anno'] or 's.d.'}"
            + (f" ({e['titolo']})" if e["titolo"] and e["titolo"].lower() not in nome.lower() else "")
            + (" – copia digitale" if e["digitale"] else "")
            for e in eds)
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        out.append({
            "type": "Feature",
            "properties": {
                "Title": f"Foglio {foglio} – {nome}",
                "Foglio": foglio,
                "Location": nome,
                "Type": "Historical Map (1:100.000)",
                "Edizioni": elenco or "Nessuna scheda trovata nel catalogo ISPRA",
                "N_edizioni": len(eds),
                "Copia_digitale": "Sì" if con_copia else "No",
                "URL": SCHEDA + principale["id"] if principale else "",
                "URL_note": SCHEDA + principale["nota"] if principale and principale["nota"] else "",
                "Fonte": FONTE,
            },
            "geometry": {"type": "MultiPolygon",
                         "coordinates": [[[[round(x, 5), round(y, 5)] for x, y in r] for r in pol] for pol in polys]},
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": out},
                              ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Fogli: {len(out)} ({OUT.stat().st_size // 1024} KB) | con schede: {len(out) - len(senza)} | "
          f"con copia digitale: {sum(1 for x in out if x['properties']['Copia_digitale'] == 'Sì')}")
    print(f"Senza schede nel catalogo ({len(senza)}): {senza}")


if __name__ == "__main__":
    if len(sys.argv) not in (1, 3):
        sys.exit(__doc__)
    main(*sys.argv[1:])
