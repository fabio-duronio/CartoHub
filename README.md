# Italian Geological Cartography Hub (IGC-Hub)
### L'Hub digitale aperto per la cartografia geologica in Italia.

**Progetto a cura di [Geologiaintasca](https://www.facebook.com/profile.php?id=61565694163261)**

Questo repository ospita un indice geografico (GeoJSON) delle risorse cartografiche geologiche italiane. L'obiettivo è riunire in un'unica mappa i rimandi a dati di istituzioni nazionali, enti regionali e ricerca accademica, oggi distribuiti su portali diversi.

[**Mappa interattiva (uMap)**](https://umap.openstreetmap.fr/it/map/cartografia-geologica-italiana_1338725) · [Anteprima Leaflet](index.html)

> [!NOTE]
> **Dati ricostruiti a novembre 2026** da fonti ufficiali (ISPRA, ISTAT, Crossref). Cosa è cambiato e quali limiti restano: [REVISIONE.md](REVISIONE.md).

---

## Dataset

| Livello | File | Feature | Fonte |
|---|---|---|---|
| Progetto CARG 1:50.000 | `dati/carg/carg_50k_fogli.geojson` | 634 fogli | CARG-GATE (ISPRA) |
| Journal of Maps | `dati/journal_of_maps/jom_italia.geojson` | 226 pubblicazioni | Crossref + confini ISTAT |
| Geoportali regionali | `dati/geoportali_regionali/geoportali_regionali.geojson` | 21 enti | Selezione manuale + confini ISTAT |

Campi comuni a tutti i livelli: `Title`, `URL`, `Location`, `Type`.

### 1. Cartografia ufficiale (Progetto CARG)
Fogli della Carta Geologica d'Italia alla scala 1:50.000, presi da **[CARG-GATE](https://progetto-carg.isprambiente.it/cartografiaCARG/index.php?source=cartageologica)**, il portale ufficiale del Servizio Geologico d'Italia (ISPRA). **Si aggiorna da solo ogni lunedì.**
* **Stato:** copiato testualmente da CARG-GATE: *Stampato*, *In attesa di stampa*, *In allestimento per la stampa*, *Rilevamento in corso*. Se il portale non indica uno stato, il campo resta vuoto: nessuno stato viene dedotto.
* **Colori:** gli stessi della legenda di CARG-GATE.
* **Link:** la scheda del foglio sul portale, il DOI della carta e il DOI delle note illustrative (archivio Open Access di ISPRA, quando disponibili).
* **Altri campi:** anno di stampa, coordinatori scientifici, stato della banca dati.

*Fonte: CARG-GATE – ISPRA, Servizio Geologico d'Italia, licenza CC BY 4.0. La regione nel link alla scheda si ricava dai confini ISTAT.*

### 2. Ricerca scientifica (Journal of Maps)
Pubblicazioni del *Journal of Maps* su aree italiane, ognuna con DOI verificato su Crossref. **Il livello si aggiorna da solo ogni lunedì** (vedi *Aggiornamento automatico*).
* **Posizione:** un punto, non l'area cartografata: serve a trovare la pubblicazione, non a delimitarla. Il campo `Precisione` dice come è stato ottenuto:
  * `Coordinate`: coordinate indicate nel paper (localizzazione manuale);
  * `Comune`, `Provincia`, `Regione`: centroide dell'unità ISTAT indicata dal curatore oppure, in automatico, citata nel titolo. Il campo `Fonte` distingue i due casi.
* **Non posizionate:** 128 pubblicazioni non hanno un toponimo ISTAT nel titolo (es. Etna, Campi Flegrei, Dolomiti) oppure citano più regioni. Sono elencate in `jom_da_localizzare.csv` e non vengono collocate a stima.
* **Licenza:** il campo `Licenza` riporta quella dichiarata in Crossref: 95 CC BY 4.0, 20 CC BY-NC 4.0, 3 CC BY-NC-ND 4.0. Per 108 articoli Crossref non indica la licenza: va verificata sulla pagina dell'articolo prima di riusarne le figure.

*Fonte: metadati [Crossref](https://www.crossref.org/) (ISSN 1744-5647); confini ISTAT per la localizzazione.*

### 3. Geoportali regionali
Accesso ai geoportali e WebGIS delle Regioni e delle Province autonome di Trento e Bolzano (21 enti), dove si trova la cartografia geologica di dettaglio.

*Fonte link: selezione manuale. Confini: ISTAT, 1° gennaio 2026 (CC BY 4.0), via [openpolis/geojson-italy](https://github.com/openpolis/geojson-italy), semplificati a circa 300 m.*

---

## Aggiornamento automatico
Due GitHub Action aggiornano i dati ogni lunedì: [`aggiorna-carg.yml`](.github/workflows/aggiorna-carg.yml) rigenera i fogli CARG da CARG-GATE, [`aggiorna-jom.yml`](.github/workflows/aggiorna-jom.yml) il livello Journal of Maps. Quest'ultima parte:
* **ogni lunedì**, scaricando da Crossref i nuovi articoli sull'Italia;
* **a ogni modifica di `localizzazioni.csv`**, così una localizzazione aggiunta compare sulla mappa in pochi minuti;
* **a mano**, da *Actions → Aggiorna Journal of Maps → Run workflow*.

Se il validatore trova errori, l'Action si ferma e non modifica i dati. Se non ci sono novità, non fa commit.

### Aggiungere una localizzazione
Il file [`dati/journal_of_maps/localizzazioni.csv`](dati/journal_of_maps/localizzazioni.csv) (separatore `;`) prevale sulla localizzazione automatica e permette di aggiungere articoli che la ricerca per "Italy" non trova.

```
DOI;Comune;Provincia;Lat;Lon;Note
10.1080/17445647.2012.668423;Gaiole in Chianti;SI;;;Monti del Chianti
10.1080/17445647.2013.842508;;;40.827;14.139;Campi Flegrei, coordinate dal testo
```
* `Comune` (nome ufficiale ISTAT) + `Provincia` (sigla), **oppure** `Lat` + `Lon` in gradi decimali.
* Si modifica direttamente da GitHub: icona della matita sul file, incolla la riga, *Commit changes*.
* Un comune inesistente o una riga incompleta fanno fallire l'Action con il numero della riga, e GitHub invia una notifica.

Gli articoli da non mettere sulla mappa (commenti, temi non cartografici, carte a scala nazionale, nessun luogo indicato) stanno in [`esclusioni.csv`](dati/journal_of_maps/esclusioni.csv) (`DOI;Categoria;Motivo`): non compaiono né sulla mappa né tra quelli da localizzare.

La skill di Geologiaintasca produce la riga già pronta per ogni post su un articolo del Journal of Maps.

## Rigenerare i dati
Ogni livello ha uno script che lo ricostruisce dalla fonte. Le istruzioni per scaricare i dati di partenza sono nell'intestazione di ciascuno script.

```bash
python3 scripts/scarica_carggate.py carggate.json   # serve accesso a progetto-carg.isprambiente.it
python3 scripts/build_carg.py carggate.json <regions>
python3 scripts/scarica_crossref.py crossref.json   # serve accesso a api.crossref.org
python3 scripts/build_jom.py crossref.json <regions> <provinces> <municipalities>
python3 scripts/build_geoportali.py <regions> <provinces>
python3 scripts/valida_dati.py   # controllo qualità: va eseguito prima di ogni commit
```

## Roadmap
- [x] Fogli CARG da CARG-GATE, con stato ufficiale e aggiornamento settimanale
- [x] Livello Journal of Maps da Crossref, con DOI verificati
- [x] Confini regionali ufficiali ISTAT
- [x] Aggiornamento settimanale automatico del Journal of Maps e localizzazioni manuali
- [x] Localizzate 87 pubblicazioni, escluse 33 (3/11/2026)
- [ ] Localizzare le 9 pubblicazioni rimaste in `jom_da_localizzare.csv` (servono i paper)
- [ ] Verificare i link dei geoportali regionali (6 sostituiti il 3/11/2026, da ricontrollare)
- [ ] Carta Geologica d'Italia 1:100.000 (277 fogli)
- [ ] Cartografia geologica marina (CARG Mare)

## Licenze e disclaimer
Il repository è un **indice di collegamenti** a risorse esterne.

* **Codice:** licenza [MIT](LICENSE).
* **Fogli CARG:** © ISPRA – Servizio Geologico d'Italia, dati di CARG-GATE con licenza **CC BY 4.0** dichiarata dal portale.
* **Confini amministrativi:** © ISTAT, licenza CC BY 4.0.
* **Journal of Maps:** sono indicizzati solo i metadati bibliografici. Gli articoli restano di autori ed editore, con la licenza indicata su ciascuno.

*Geologiaintasca non è titolare dei dati cartografici collegati: fornisce solo il servizio di indicizzazione geografica.*

## Contribuire
1. Apri una **Issue** per segnalare una mappa, un errore o una localizzazione.
2. Fai un **fork** e invia una pull request, dopo aver eseguito `scripts/valida_dati.py`.
