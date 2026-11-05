#!/usr/bin/env python3
"""Ricostruisce i due livelli Journal of Maps da un export Crossref:
  dati/journal_of_maps/jom_italia.geojson     studi localizzati (comune o coordinate)
  dati/journal_of_maps/jom_regionali.geojson  studi a scala regionale e articoli da localizzare

Uso:
  python3 -I scripts/build_jom.py <crossref.json> <regions.geojson> <provinces.geojson> <municipalities.geojson>

Export Crossref (Journal of Maps, ISSN 1744-5647):
  https://api.crossref.org/works?filter=issn:1744-5647&query.bibliographic=Italy&rows=1000&select=DOI,title,issued,license,subject
Confini ISTAT (CC BY 4.0): repository openpolis/geojson-italy.

Metodo di localizzazione (dichiarato nel campo "Precisione"):
  ogni pubblicazione è un punto sul centroide dell'unità ISTAT più specifica
  nominata nel titolo: comune > provincia > regione. Un comune viene accettato
  solo se il nome è univoco in Italia oppure se la regione è citata nel titolo.
  Con solo la provincia o la regione l'articolo va nel livello regionale
  (Ambito "Da localizzare"), mai sul livello principale.
  Le pubblicazioni senza toponimo riconoscibile NON vengono posizionate:
  finiscono in dati/journal_of_maps/jom_da_localizzare.csv.

Localizzazioni manuali (prevalgono su quelle automatiche):
  dati/journal_of_maps/localizzazioni.csv, colonne DOI;Comune;Provincia;Lat;Lon;Note
  - con Lat e Lon: punto esatto (Precisione "Coordinate");
  - altrimenti Comune + sigla Provincia: centroide del comune ISTAT (Precisione "Comune").
  Un comune non trovato o una riga incompleta fanno fallire lo script, così l'errore si vede.

Studi a scala regionale o di area vasta (confermati):
  dati/journal_of_maps/regionali.csv, colonne DOI;Area;Regione;Provincia;Note
  Punto sul centroide della provincia (sigla) se indicata, altrimenti della regione (nome ISTAT).
  Area è il nome mostrato sulla mappa; se vuota, il nome della provincia o della regione.
  Livello regionale, Ambito "Regionale".

Un DOI può stare in un solo file tra localizzazioni.csv, regionali.csv ed esclusioni.csv.

Esclusioni: dati/journal_of_maps/esclusioni.csv, colonne DOI;Categoria;Motivo.
  Articoli che non vanno sulla mappa (commenti, temi non cartografici, scala nazionale,
  nessun luogo indicato): non compaiono né sulla mappa né tra quelli da localizzare.
"""
import csv
import html
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dati/journal_of_maps/jom_italia.geojson"
OUT_REG = ROOT / "dati/journal_of_maps/jom_regionali.geojson"
REGIONALI = ROOT / "dati/journal_of_maps/regionali.csv"
OUT_CSV = ROOT / "dati/journal_of_maps/jom_da_localizzare.csv"
MANUALI = ROOT / "dati/journal_of_maps/localizzazioni.csv"
ESCLUSIONI = ROOT / "dati/journal_of_maps/esclusioni.csv"

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
                "padua": "Padova", "syracuse": "Siracusa", "mantua": "Mantova",
                "tremiti islands": "Isole Tremiti", "lampedusa island": "Lampedusa e Linosa",
                "giglio island": "Isola del Giglio"}
# Unità geologiche e nomi composti che contengono un toponimo ma non indicano quel luogo.
# Tolti dal titolo prima del riconoscimento della regione o del comune.
NON_REGIONE = [r"tertiary piedmont basin", r"piedmont basin", r"(lower )?piedmont zone"]  # unità tettoniche
NON_COMUNE = [r"aosta valley", r"valle d.aosta"]  # la regione, non il comune di Aosta
# Nomi di comuni che sono anche parole comuni nei titoli: esclusi dal riconoscimento
# Salento: comune campano omonimo della penisola pugliese
ESCLUSI = {"Italia", "Mare", "Monte", "Valle", "Lago", "Isola", "Porto", "Salento"}


def nome_licenza(url):
    """'http://creativecommons.org/licenses/by-nc/4.0/)' -> 'CC BY-NC 4.0' (ignora caratteri spuri nell'URL)."""
    m = re.search(r"licenses/([a-z-]+)/(\d+\.\d+)", url.lower())
    return f"CC {m.group(1).upper()} {m.group(2)}" if m else ""


def apostrofi(s):
    """Prima della conversione in ASCII, che li eliminerebbe incollando le parole:
    apostrofo tipografico -> apostrofo ("L’Aquila" non diventa "LAquila");
    lineetta – o — -> spazio ("Entracque–Colle di Tenda" non diventa "EntracqueColle")."""
    for c in "\u2019\u2018\u02bc":
        s = s.replace(c, "'")
    return s.replace("\u2013", " ").replace("\u2014", " ")


def maschera(titolo, espressioni):
    for e in espressioni:
        titolo = re.sub(r"(?i)(?<![a-z])" + e + r"(?![a-z])", " ", titolo)
    return titolo


def pulisci_titolo(s):
    """Titolo Crossref -> testo semplice: niente tag HTML, entità decodificate.
    <sub>/<sup> si attaccano alla parola precedente (P<sub>2</sub>O -> P2O, M<sub>w</sub> -> Mw)."""
    s = re.sub(r"(?<=\w)<(i|em|b|strong|span)\b[^>]*>(?=\w)", " ", s, flags=re.I)
    s = re.sub(r"(?<=\w)</(i|em|b|strong|span)>(?=[\w(])", " ", s, flags=re.I)
    s = re.sub(r"</?(?!su[bp]\b)[a-z][^>]*>", "", s, flags=re.I)
    formula = re.search(r"<sub>", s, flags=re.I) is not None
    s = re.sub(r"\s*<(sub|sup)>\s*(.*?)\s*</\1>", r"\2", s, flags=re.I | re.S)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = " ".join(s.split())
    if formula:  # "P2 O5", "K2 O" -> "P2O5", "K2O"
        s = re.sub(r"(?<=[A-Z]\d) (?=[A-Z](\d|\W|$))", "", s)
    s = re.sub(r"\u2018\s+", "\u2018", re.sub(r"\s+\u2019", "\u2019", s))  # ‘ Bosco ’ -> ‘Bosco’
    return re.sub(r"\s+([,:;.)])", r"\1", s)


def norm(s):
    s = unicodedata.normalize("NFKD", apostrofi(s)).encode("ascii", "ignore").decode()
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
    # Parole senza apostrofo: "L'Aquila" -> "L", "Aquila", come nel nome normalizzato "l aquila"
    t = unicodedata.normalize("NFKD", apostrofi(titolo)).encode("ascii", "ignore").decode()
    parole = list(re.finditer(r"[A-Za-z0-9]+", t))
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
    # Parole senza apostrofo: "L'Aquila" -> "L", "Aquila", come nel nome normalizzato "l aquila"
    t = unicodedata.normalize("NFKD", apostrofi(titolo)).encode("ascii", "ignore").decode()
    parole = list(re.finditer(r"[A-Za-z0-9]+", t))
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
        # nomi bilingui ("Santa Cristina Valgardena/St. Christina in Gröden"): basta il nome italiano
        per_comune.setdefault((norm(p["name"].split("/")[0]), p["prov_acr"].upper()), f)
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


def leggi_regionali(path, regioni, province):
    """DOI (minuscolo) -> (coordinate, precisione, luogo) per gli studi a scala regionale o di area vasta."""
    if not path.exists():
        return {}
    per_regione = {}
    for f in regioni:
        nome = f["properties"]["reg_name"]
        per_regione[norm(nome)] = f
        for parte in nome.split("/"):
            per_regione[norm(parte)] = f
    per_sigla = {f["properties"]["prov_acr"].upper(): f for f in province}
    out, errori = {}, []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for n, r in enumerate(csv.DictReader(fh, delimiter=";"), start=2):
            r = {k.strip(): (v or "").strip() for k, v in r.items() if k}
            doi = r.get("DOI", "").lower().removeprefix("https://doi.org/")
            if not doi:
                continue
            if r.get("Provincia"):
                f = per_sigla.get(r["Provincia"].upper())
                if f is None:
                    errori.append(f"riga {n}: sigla di provincia '{r['Provincia']}' non trovata nei confini ISTAT")
                    continue
                prec, nome = "Provincia", f"Provincia di {f['properties']['prov_name']}"
            elif r.get("Regione"):
                f = per_regione.get(norm(r["Regione"]))
                if f is None:
                    errori.append(f"riga {n}: regione '{r['Regione']}' non trovata nei confini ISTAT")
                    continue
                prec, nome = "Regione", f["properties"]["reg_name"].split("/")[0]
            else:
                errori.append(f"riga {n}: serve la Regione (nome ISTAT) o la sigla della Provincia")
                continue
            out[doi] = (centroide(f["geometry"]), prec, r.get("Area") or nome)
    if errori:
        sys.exit("Errori in " + str(path.relative_to(ROOT)) + ":\n  " + "\n  ".join(errori))
    return out


def duplicati_csv(*paths):
    """DOI ripetuti dentro uno stesso CSV o presenti in più CSV: errore bloccante."""
    visti, errori = {}, []
    for path in paths:
        if not path.exists():
            continue
        with open(path, encoding="utf-8-sig", newline="") as fh:
            for n, r in enumerate(csv.DictReader(fh, delimiter=";"), start=2):
                doi = (r.get("DOI") or "").strip().lower().removeprefix("https://doi.org/")
                if not doi:
                    continue
                dove = f"{path.name} riga {n}"
                if doi in visti:
                    errori.append(f"{doi}: {visti[doi]} e {dove}")
                else:
                    visti[doi] = dove
    if errori:
        sys.exit("DOI presenti più volte nei CSV di localizzazione:\n  " + "\n  ".join(errori))


def leggi_esclusioni(path):
    if not path.exists():
        return {}
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return {r["DOI"].strip().lower(): (r.get("Categoria") or "").strip()
                for r in csv.DictReader(fh, delimiter=";") if (r.get("DOI") or "").strip()}


def main(p_cr, p_reg, p_prov, p_com):
    items = json.load(open(p_cr, encoding="utf-8"))["message"]["items"]
    regioni = json.load(open(p_reg, encoding="utf-8"))["features"]
    province = json.load(open(p_prov, encoding="utf-8"))["features"]
    comuni = json.load(open(p_com, encoding="utf-8"))["features"]

    duplicati_csv(MANUALI, REGIONALI, ESCLUSIONI)
    manuali = leggi_manuali(MANUALI, comuni)
    regionali = leggi_regionali(REGIONALI, regioni, province)
    esclusi = leggi_esclusioni(ESCLUSIONI)
    n_esclusi = 0
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
    features, features_reg, scartati = [], [], []
    for it in items:
        titolo = pulisci_titolo((it.get("title") or [""])[0])
        if not titolo:
            continue
        if it["DOI"].lower() in esclusi:
            n_esclusi += 1
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
        titolo = pulisci_titolo(it["title"][0])
        tit_reg = maschera(titolo, NON_REGIONE)
        tit_com = maschera(tit_reg, NON_COMUNE)
        t, t_com = norm(tit_reg), norm(tit_com)
        anno = (it.get("issued", {}).get("date-parts") or [[None]])[0][0]
        lic = sorted({nome_licenza(l["URL"]) for l in it.get("license", []) if "creativecommons" in l["URL"]} - {""})
        licenza = lic[0] if lic else "Non indicata in Crossref"

        # Maiuscola obbligatoria: "Adriatic piedmont" è la fascia pedemontana, non il Piemonte
        reg_citate = {nome for k, nome in gaz_reg.items() if contiene(t, k) and maiuscolo(tit_reg, k)}
        # Le unità tettoniche ("Tertiary Piedmont Basin") non filtrano i comuni, ma se nel titolo
        # non c'è altro restano l'unico indizio della regione per il ripiego regionale.
        reg_ripiego = reg_citate or {nome for k, nome in gaz_reg.items()
                                     if contiene(norm(titolo), k) and maiuscolo(titolo, k)}
        # Provincia solo se il titolo parla esplicitamente di provincia ("X Province", "province of X")
        prov = [f for k, f in gaz_prov.items()
                if (contiene(t, k + " province") or contiene(t, "province of " + k))
                and (not reg_citate or f["properties"]["reg_name"] in reg_citate)]
        com = []
        for k, fs in com_per_nome.items():
            if not fs or not contiene(t_com, k) or k in gaz_reg:
                continue
            if not citazione_valida(tit_com, k, com_per_nome):
                continue
            cand = [f for f in fs if not reg_citate or f["properties"]["reg_name"] in reg_citate]
            if len(cand) == 1:
                com.append(cand[0])
        # Con più comuni citati si sceglie il nome più lungo (meno ambiguo).
        com.sort(key=lambda f: -len(f["properties"]["name"]))

        doi = it["DOI"].lower()
        man = manuali.get(doi) or regionali.get(doi)
        if man:
            punto, prec, luogo = man
        elif prov:
            f = prov[0]
            geom, prec, luogo = f["geometry"], "Provincia", f"Provincia di {f['properties']['prov_name']}"
        elif com:
            f = com[0]
            geom, prec, luogo = f["geometry"], "Comune", f"{f['properties']['name']} ({f['properties']['prov_acr']})"
        elif len(reg_ripiego) == 1:
            nome = next(iter(reg_ripiego))
            geom, prec, luogo = reg_by_name[nome]["geometry"], "Regione", nome.split("/")[0]
        else:
            motivo = "più regioni citate" if len(reg_ripiego) > 1 else "nessun toponimo ISTAT riconosciuto"
            scartati.append({"DOI": it["DOI"], "Title": titolo, "Anno": anno, "Motivo": motivo})
            continue
        if not man:
            punto = centroide(geom)
            fonte = "Crossref (metadati); localizzazione automatica dal titolo, confini ISTAT"
        else:
            fonte = "Crossref (metadati); localizzazione manuale (Geologiaintasca)"
        # Regione o provincia: livello regionale. "Regionale" se confermato in regionali.csv,
        # "Da localizzare" se è solo il ripiego automatico (studio locale ancora da posizionare).
        regionale = prec in ("Regione", "Provincia")
        extra = {"Ambito": "Regionale" if doi in regionali else "Da localizzare"} if regionale else {}

        (features_reg if regionale else features).append({
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
                **extra,
            },
            "geometry": {"type": "Point", "coordinates": punto},
        })

    for path, fs in ((OUT, features), (OUT_REG, features_reg)):
        path.write_text(json.dumps({"type": "FeatureCollection", "features": fs},
                                   ensure_ascii=False, indent=1), encoding="utf-8")
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["DOI", "Title", "Anno", "Motivo"])
        w.writeheader()
        w.writerows(scartati)
    print(f"Crossref: {len(items)} record, {len(per_titolo)} dopo dedup")
    usati = {f["properties"]["DOI"].lower() for f in features + features_reg}
    for nome, d in (("localizzazioni.csv", manuali), ("regionali.csv", regionali)):
        orfani = sorted(set(d) - usati)
        if orfani:
            print(f"ATTENZIONE: {len(orfani)} DOI in {nome} non presenti nei dati Crossref: {orfani}")
    conf = sum(1 for f in features_reg if f["properties"]["Ambito"] == "Regionale")
    print(f"Localizzati: {len(features)} (di cui manuali: {len(set(manuali) & usati)})  |  "
          f"scala regionale: {conf}  |  regione o provincia da completare: {len(features_reg) - conf}  |  "
          f"esclusi: {n_esclusi}  |  senza luogo: {len(scartati)}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(*sys.argv[1:])
