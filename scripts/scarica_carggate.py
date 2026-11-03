#!/usr/bin/env python3
"""Scarica da CARG-GATE (ISPRA) i fogli della Carta Geologica d'Italia 1:50.000.

Uso:
  python3 -I scripts/scarica_carggate.py <output.json>

È lo stesso servizio che usa la pagina "Carta Geologica" del portale
https://progetto-carg.isprambiente.it/cartografiaCARG/index.php?source=cartageologica
(richiesta POST oper=CARTA_GEOLOGICA). Licenza dei dati del portale: CC BY 4.0.
Salva il GeoJSON dei fogli così come lo restituisce il servizio.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

URL = "https://progetto-carg.isprambiente.it/assets/db/jcartografia.php"
HEADERS = {"User-Agent": "IGC-Hub/1.0 (https://github.com/fabio-duronio/cartografia-geologica-italiana)",
           "Content-Type": "application/x-www-form-urlencoded"}


def main(out):
    dati = urllib.parse.urlencode({"oper": "CARTA_GEOLOGICA"}).encode()
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(URL, data=dati, headers=HEADERS), timeout=120) as r:
                raw = json.load(r)
            break
        except Exception:
            if i == 3:
                raise
            time.sleep(10 * (i + 1))
    gc = raw[0]["jsonb_build_object"]
    fc = json.loads(gc) if isinstance(gc, str) else gc
    n = len(fc.get("features", []))
    if n < 600:  # il portale elenca 634 fogli: un numero molto più basso indica una risposta anomala
        sys.exit(f"Risposta anomala da CARG-GATE: {n} fogli")
    Path(out).write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
    print(f"CARG-GATE: {n} fogli in {out}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
