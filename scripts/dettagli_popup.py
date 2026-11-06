#!/usr/bin/env python3
"""Aggiunge a ogni GeoJSON di dati/ il campo "Dettagli": il testo del popup di uMap.

Uso:  python3 -I scripts/dettagli_popup.py

uMap non sa nascondere le righe vuote di un modello di popup: il testo viene quindi
preparato qui, con la sintassi di uMap (**grassetto**, [[link|testo]]), e il modello
del livello in uMap è solo:  # {Title}  +  {Dettagli}.
Etichette e link sono gli stessi dei popup di index.html.
Lo script è idempotente e conserva la formattazione di ciascun file.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "dati"


def riga(etichetta, valore):
    v = str(valore if valore is not None else "").strip()
    return f"**{etichetta}:** {v}" if v else ""


def link(url, testo):
    u = str(url or "").strip()
    return f"[[{u}|{testo}]]" if u.startswith("https://") or u.startswith("http://") else ""


def posizione(p):
    prec = p.get("Precisione")
    if not prec:
        return ""
    if prec == "Coordinate":
        return "coordinate indicate nel paper"
    unita = {"Comune": ("del comune", "indicato"), "Provincia": ("della provincia", "indicata"),
             "Regione": ("della regione", "indicata")}
    art, part = unita.get(prec, (f"di {prec.lower()}", "indicato"))
    chi = f"{part} dal curatore" if "manuale" in str(p.get("Fonte", "")) else part.replace("indicat", "citat") + " nel titolo"
    return f"centroide {art} {chi}"


def dettagli(p):
    t = p.get("Type")
    if t == "Official Map":  # Progetto CARG 1:50.000
        righe = [riga("Stato", p.get("Stato")) or "Nessuno stato indicato su CARG-GATE",
                 riga("Anno di stampa", p.get("Anno_stampa")), riga("Coordinatori", p.get("Coordinatori")),
                 riga("Banca dati", p.get("Banca_dati")),
                 link(p.get("URL"), "Scheda su CARG-GATE"), link(p.get("DOI_carta"), "Carta (DOI)"),
                 link(p.get("DOI_note"), "Note illustrative (DOI)")]
    elif t == "Historical Map (1:100.000)":
        righe = [riga("Edizioni", p.get("Edizioni")),
                 link(p.get("URL"), "Scheda nel catalogo ISPRA"),
                 link(p.get("URL_note"), "Note illustrative (catalogo ISPRA)")]
    elif t == "Research Map":  # Journal of Maps e Altre riviste
        unita = "provincia" if p.get("Precisione") == "Provincia" else "regione"
        if p.get("Ambito") == "Regionale":  # studio a scala regionale confermato (regionali.csv)
            pos = riga("Area di studio", f"intera {unita} / area vasta")
        elif p.get("Ambito") == "Da localizzare":  # ripiego automatico: studio locale non ancora posizionato
            pos = riga("Posizione", f"localizzazione da completare ({unita} citata nel titolo)")
        else:
            pos = riga("Posizione", posizione(p))
        righe = [riga("Rivista", p.get("Rivista")),  # solo livello «Altre riviste»; vuoto per il Journal of Maps
                 riga("Luogo", p.get("Location")), riga("Anno", p.get("Anno")), riga("Licenza", p.get("Licenza")),
                 pos, link(p.get("URL"), "Articolo (DOI)")]
    else:  # Geoportali regionali
        righe = [str(p.get("Description") or "").strip(), link(p.get("URL"), "Vai al geoportale")]
    return "\n".join(r for r in righe if r)


def main():
    for path in sorted(ROOT.rglob("*.geojson")):
        raw = path.read_text(encoding="utf-8")
        d = json.loads(raw)
        for f in d.get("features", []):
            f["properties"]["Dettagli"] = dettagli(f["properties"])
        kw = {"indent": 1} if raw.startswith("{\n") else {"separators": (",", ":")}
        nuovo = json.dumps(d, ensure_ascii=False, **kw)
        if nuovo != raw:
            path.write_text(nuovo, encoding="utf-8")
        print(f"{path.relative_to(ROOT.parent)}: {len(d.get('features', []))} popup")


if __name__ == "__main__":
    main()
