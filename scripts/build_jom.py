#!/usr/bin/env python3
"""Ricostruisce dati/journal_of_maps/jom_italia.geojson da un export Crossref.

Uso:
  python3 -I scripts/build_jom.py <crossref.json> <regions.geojson> <provinces.geojson> <municipalities.geojson>

Export Crossref (Journal of Maps, ISSN 1744-5647):
  https://api.crossref.org/works?filter=issn:1744-5647&query.bibliographic=Italy&rows=1000&select=DOI,title,issued,license,subject
Confini ISTAT (CC BY 4.0): repository openpolis/geojson-italy.

Metodo di localizzazione (dichiarato nel campo "Precisione"):
  ogni pubblicazione è un punto sul centroide dell'unità ISTAT più specifica
  nominata nel titolo: comune > provincia > regione. Un comune viene accettato
  solo se il nome è univoco in Italia oppure se la regione è citata nel titolo.
  Le pubblicazioni senza toponimo riconoscibile NON vengono posizionate:
  finiscono in dati/journal_of_maps/jom_da_localizzare.csv.

Localizzazioni manuali (prevalgono su quelle automatiche):
  dati/journal_of_maps/localizzazioni.csv, colonne DOI;Comune;Provincia;Lat;Lon;Note
  - con Lat e Lon: punto esatto (Precisione "Coordinate");
  - altrimenti Comune + sigla Provincia: centroide del comune ISTAT (Precisione "Comune").
  Un comune non trovato o una riga incompleta fanno fallire lo script, così l'errore si vede.
"""
import csv
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dati/journal_of_maps/jom_italia.geojson"
OUT_CSV = ROOT / "dati/journal_of_maps/jom_da_localizzare.csv"
MANUALI = ROOT / "dati/journal_of_maps/localizzazioni.csv"

JOM_PREFIX = ("10.1080/17445647.", "10.1080/jom.", "10.4113/jom.")  # attuale e storici

# Nomi inglesi usati nei titoli (traduzioni, non stime)
ALIAS_REGIONI = {
    "tuscany": "Toscana", "sicily": "Sicilia", "sardinia": "Sardegna", "apulia": "Puglia",
    "lombardy": "Lombardia", "piedmont": "Piemonte", "aosta valley": "Valle d'Aosta/Vallée d'Aoste",
    "friuli venezia giulia": "Friuli-Venezia Giulia", "friuli-venezia giulia": "Friuli-Venezia Giulia",
    "trentino": "Trentino-Alto Adige/Südtirol", "south tyrol": "Trentino-Alto Adige/Südtirol",
    "emilia romagna": "Emilia-Romagna", "latium": "Lazio", "abruzzi": "Abruzzo",
}
ALIAS_COMUNI = {"rome": "Roma", "naples": "Napoli", "florence": "Firenze", "venice": "Venezia",
                "milan": "Milano", "turin": "Torino", "genoa": "Genova", "leghorn": "Livorno",
                "padua": "Padova", "syracuse": "Siracusa", "mantua": "Mantova"}
# Nomi di comuni che sono anche parole comuni nei titoli: esclusi dal riconoscimento
# Salento: comune campano omonimo della penisola pugliese
ESCLUSI = {"Italia", "Mare", "Monte", "Valle", "Lago", "Isola", "Porto", "Salento"}


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def anelli(geom):
    pol = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    return [p[0] for p in pol]


def centroide(geom):
    """Centroide del poligono esterno più grande (formula dell'area)."""
    def area_c(r):
        a = cx = cy = 0.0
        for (x0, y0), (x1, y1) in zip(r, r[1:]):
            k = x0 * y1 - x1 * y0
            a += k
            cx += (x0 + x1) * k
            cy += (y0 + y1) * k
        return a / 2, cx, cy
    best = max((area_c(r) for r in anelli(geom)), key=lambda t: abs(t[0]))
    a, cx, cy = best
    return [round(cx / (6 * a), 4), round(cy / (6 * a), 4)]


DESCRITTIVI = {"northern", "southern", "eastern", "western", "central", "upper", "lower", "the",
               "of", "and", "in", "at", "near", "between", "from", "to", "around", "greater"}


def citazione_valida(titolo, nome_norm, nomi_comuni):
    """True se nel titolo c'è almeno un'occorrenza del toponimo che:
    - inizia con la maiuscola ("thrust zone" non è il comune di Zone);
    - non è preceduta da un'altra parola maiuscola ("Santa Barbara" non è Barbara),
      salvo aggettivi descrittivi ("Northern Siena Basin");
    - non è unita con un trattino a un nome che non è un comune
      ("Ferriere-Mollieres Shear Zone"; ammesso "Laconi-Asuni", entrambi comuni)."""
    t = unicodedata.normalize("NFKD", titolo).encode("ascii", "ignore").decode()
    parole = list(re.finditer(r"[A-Za-z0-9']+", t))
    n = nome_norm.split()
    for i in range(len(parole) - len(n) + 1):
        if [norm(w.group()) for w in parole[i:i + len(n)]] != n:
            continue
        primo, ultimo = parole[i], parole[i + len(n) - 1]
        if not primo.group()[:1].isupper():
            continue
        if i > 0:
            prec = parole[i - 1]
            tra = t[prec.end():primo.start()]
            if prec.group()[:1].isupper() and norm(prec.group()) not in DESCRITTIVI and tra.strip() == "":
                continue
            if tra == "-" and norm(prec.group()) not in nomi_comuni:
                continue
        if i + len(n) < len(parole):
            succ = parole[i + len(n)]
            if t[ultimo.end():succ.start()] == "-" and norm(succ.group()) not in nomi_comuni:
                continue
        return True
    return False


def maiuscolo(titolo, nome_norm):
    """True se almeno un'occorrenza del toponimo nel titolo originale inizia con la maiuscola.
    Esclude i composti col trattino ("Piemonte-Ligurian units" è un'unità tettonica)."""
    t = unicodedata.normalize("NFKD", titolo).encode("ascii", "ignore").decode()
    parole = list(re.finditer(r"[A-Za-z0-9']+", t))
    n = nome_norm.split()
    for i in range(len(parole) - len(n) + 1):
        if [norm(w.group()) for w in parole[i:i + len(n)]] != n or not parole[i].group()[:1].isupper():
            continue
        fine = parole[i + len(n) - 1].end()
        if t[fine:fine + 1] == "-" and i + len(n) < len(parole):
            continue
        return True
    return False


def contiene(testo, nome):
    if nome not in testo:  # filtro rapido: evita la regex per i ~7.900 comuni non citati
        return False
    return re.search(r"(?<![a-z0-9])" + re.escape(nome) + r"(?![a-z0-9])", testo) is not None


def leggi_manuali(path, comuni):
    """DOI (minuscolo) -> (coordinate, precisione, luogo). Errori bloccanti con messaggio chiaro."""
    if not path.exists():
        return {}
    per_comune = {}
    for f in comuni:
        p = f["properties"]
        per_comune[(norm(p["name"]), p["prov_acr"].upper())] = f
    out, errori = {}, []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for n, r in enumerate(csv.DictReader(fh, delimiter=";"), start=2):
            r = {k.strip(): (v or "").strip() for k, v in r.items() if k}
            doi = r.get("DOI", "").lower().removeprefix("https://doi.org/")
            if not doi:
                continue
            if r.get("Lat") and r.get("Lon"):
                try:
                    lat, lon = float(r["Lat"].replace(",", ".")), float(r["Lon"].replace(",", "."))
                except ValueError:
                    errori.append(f"riga {n}: Lat/Lon non numeriche")
                    continue
                if not (35 <= lat <= 47.5 and 6 <= lon <= 19):
                    errori.append(f"riga {n}: coordinate fuori dall'Italia ({lat}, {lon})")
                    continue
                luogo = r.get("Comune") or f"{lat:.4f}, {lon:.4f}"
                out[doi] = ([round(lon, 5), round(lat, 5)], "Coordinate", luogo)
            elif r.get("Comune") and r.get("Provincia"):
                f = per_comune.get((norm(r["Comune"]), r["Provincia"].upper()))
                if f is None:
                    errori.append(f"riga {n}: comune '{r['Comune']}' ({r['Provincia']}) non trovato nei confini ISTAT")
                    continue
                p = f["properties"]
                out[doi] = (centroide(f["geometry"]), "Comune", f"{p['name']} ({p['prov_acr']})")
            else:
                errori.append(f"riga {n}: servono Lat e Lon, oppure Comune e Provincia")
    if errori:
        sys.exit("Errori in " + str(path.relative_to(ROOT)) + ":\n  " + "\n  ".join(errori))
    return out


def main(p_cr, p_reg, p_prov, p_com):
    items = json.load(open(p_cr, encoding="utf-8"))["message"]["items"]
    regioni = json.load(open(p_reg, encoding="utf-8"))["features"]
    province = json.load(open(p_prov, encoding="utf-8"))["features"]
    comuni = json.load(open(p_com, encoding="utf-8"))["features"]

    manuali = leggi_manuali(MANUALI, comuni)
    reg_by_name = {f["properties"]["reg_name"]: f for f in regioni}
    gaz_reg = {}
    for nome in reg_by_name:
        for parte in nome.split("/"):
            gaz_reg[norm(parte)] = nome
    for alias, nome in ALIAS_REGIONI.items():
        gaz_reg[norm(alias)] = nome

    gaz_prov = {norm(f["properties"]["prov_name"]): f for f in province}

    com_per_nome = defaultdict(list)
    for f in comuni:
        nome = f["properties"]["name"]
        if nome in ESCLUSI or len(nome) < 4:
            continue
        com_per_nome[norm(nome)].append(f)
    for alias, nome in ALIAS_COMUNI.items():
        com_per_nome[norm(alias)] = com_per_nome.get(norm(nome), [])

    # Dedup: lo stesso articolo compare con DOI vecchi (10.4113/jom.*) e nuovi (10.1080/...)
    def rank(doi):
        return 0 if doi.startswith("10.1080/17445647.") else 1 if doi.startswith("10.1080/jom.") else 2
    per_titolo = {}
    features, scartati = [], []
    for it in items:
        titolo = " ".join((it.get("title") or [""])[0].split())
        if not titolo:
            continue
        if not it["DOI"].lower().startswith(JOM_PREFIX):
            anno = (it.get("issued", {}).get("date-parts") or [[None]])[0][0]
            scartati.append({"DOI": it["DOI"], "Title": titolo, "Anno": anno,
                             "Motivo": "DOI non del Journal of Maps (record Crossref associato all'ISSN)"})
            continue
        k = norm(titolo)
        if k not in per_titolo or rank(it["DOI"].lower()) < rank(per_titolo[k]["DOI"].lower()):
            per_titolo[k] = it

    for it in sorted(per_titolo.values(), key=lambda x: x["DOI"]):
        titolo = " ".join(it["title"][0].split())
        t = norm(titolo)
        anno = (it.get("issued", {}).get("date-parts") or [[None]])[0][0]
        lic = sorted({l["URL"].rstrip("/") for l in it.get("license", []) if "creativecommons" in l["URL"]})
        licenza = lic[0].split("licenses/")[-1].upper().replace("/", " ").strip() if lic else "Non indicata in Crossref"

        # Maiuscola obbligatoria: "Adriatic piedmont" è la fascia pedemontana, non il Piemonte
        reg_citate = {nome for k, nome in gaz_reg.items() if contiene(t, k) and maiuscolo(titolo, k)}
        # Provincia solo se il titolo parla esplicitamente di provincia ("X Province", "province of X")
        prov = [f for k, f in gaz_prov.items()
                if (contiene(t, k + " province") or contiene(t, "province of " + k))
                and (not reg_citate or f["properties"]["reg_name"] in reg_citate)]
        com = []
        for k, fs in com_per_nome.items():
            if not fs or not contiene(t, k) or k in gaz_reg:
                continue
            if not citazione_valida(titolo, k, com_per_nome):
                continue
            cand = [f for f in fs if not reg_citate or f["properties"]["reg_name"] in reg_citate]
            if len(cand) == 1:
                com.append(cand[0])
        # Con più comuni citati si sceglie il nome più lungo (meno ambiguo).
        com.sort(key=lambda f: -len(f["properties"]["name"]))

        man = manuali.get(it["DOI"].lower())
        if man:
            punto, prec, luogo = man
        elif prov:
            f = prov[0]
            geom, prec, luogo = f["geometry"], "Provincia", f"Provincia di {f['properties']['prov_name']}"
        elif com:
            f = com[0]
            geom, prec, luogo = f["geometry"], "Comune", f"{f['properties']['name']} ({f['properties']['prov_acr']})"
        elif len(reg_citate) == 1:
            nome = next(iter(reg_citate))
            geom, prec, luogo = reg_by_name[nome]["geometry"], "Regione", nome.split("/")[0]
        else:
            motivo = "più regioni citate" if len(reg_citate) > 1 else "nessun toponimo ISTAT riconosciuto"
            scartati.append({"DOI": it["DOI"], "Title": titolo, "Anno": anno, "Motivo": motivo})
            continue
        if not man:
            punto = centroide(geom)
            fonte = "Crossref (metadati); localizzazione automatica dal titolo, confini ISTAT"
        else:
            fonte = "Crossref (metadati); localizzazione manuale (Geologiaintasca)"

        features.append({
            "type": "Feature",
            "properties": {
                "Title": titolo,
                "DOI": it["DOI"],
                "URL": f"https://doi.org/{it['DOI']}",
                "Location": luogo,
                "Type": "Research Map",
                "Anno": anno,
                "Licenza": licenza,
                "Precisione": prec,
                "Fonte": fonte,
            },
            "geometry": {"type": "Point", "coordinates": punto},
        })

    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": features},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["DOI", "Title", "Anno", "Motivo"])
        w.writeheader()
        w.writerows(scartati)
    print(f"Crossref: {len(items)} record, {len(per_titolo)} dopo dedup")
    usati = {f["properties"]["DOI"].lower() for f in features}
    orfani = sorted(set(manuali) - usati)
    if orfani:
        print(f"ATTENZIONE: {len(orfani)} DOI in localizzazioni.csv non presenti nei dati Crossref: {orfani}")
    print(f"Localizzati: {len(features)} (di cui manuali: {len(set(manuali) & usati)})  |  da localizzare: {len(scartati)}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(*sys.argv[1:])
