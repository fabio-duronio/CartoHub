# Italian Geological Cartography Hub (IGC-Hub)
### L'Hub digitale aperto per la cartografia geologica in Italia.

**Progetto a cura di [Geologiaintasca](https://www.geologiaintasca.it)**

Questo repository ospita un indice geografico (GeoJSON) delle risorse cartografiche geologiche italiane. L'obiettivo è riunire in un'unica mappa i rimandi a dati di istituzioni nazionali, enti regionali e ricerca accademica, oggi distribuiti su portali diversi.

[**Mappa interattiva (uMap)**](https://umap.openstreetmap.fr/it/map/cartografia-geologica-italiana_1338725) · [Anteprima Leaflet](index.html)

> [!NOTE]
> **Dati ricostruiti a novembre 2026** da fonti ufficiali (ISPRA, ISTAT, Crossref). Cosa è cambiato e quali limiti restano: [REVISIONE.md](REVISIONE.md).

---

## Dataset

| Livello | File | Feature | Fonte |
|---|---|---|---|
| Progetto CARG 1:50.000 | `dati/carg/carg_50k_fogli.geojson` | 636 fogli | Quadro d'unione ISPRA |
| Journal of Maps | `dati/journal_of_maps/jom_italia.geojson` | 226 pubblicazioni | Crossref + confini ISTAT |
| Geoportali regionali | `dati/geoportali_regionali/geoportali_regionali.geojson` | 21 enti | Selezione manuale + confini ISTAT |

Campi comuni a tutti i livelli: `Title`, `URL`, `Location`, `Type`.

### 1. Cartografia ufficiale (Progetto CARG)
Quadro d'unione dei fogli geologici alla scala 1:50.000 (CARG e pre-CARG), con la posizione reale di ogni foglio.
* **Campi:** `Foglio`, `Stato`, `Raster`, `Estensione` (fogli standard, estesi o accorpati), `URL`.
* **Stato** (dal campo ISPRA `stato`): 214 *Realizzato*, 64 *Finanziato / in corso*, 358 *Non avviato o non indicato*. Le etichette interpretano i codici ISPRA (`bd`, `finanziati`), che il servizio non documenta.
* **URL:** 243 fogli hanno la pagina dedicata ISPRA. Gli altri rimandano alla pagina generale CARG, e il campo `URL_tipo` lo indica.
* I fogli accorpati (es. 1-7 Vipiteno) sono un'unica feature: un clic corrisponde a un foglio pubblicato.

*Fonte: ISPRA – Servizio Geologico d'Italia, servizio [Antropico25k, layer "Quadro unione Fogli"](https://sinacloud.isprambiente.it/arcgisgeo/rest/services/servizi/Antropico25k/MapServer/0).*

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
Una GitHub Action ([`aggiorna-jom.yml`](.github/workflows/aggiorna-jom.yml)) rigenera il livello Journal of Maps:
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

La skill di Geologiaintasca produce la riga già pronta per ogni post su un articolo del Journal of Maps.

## Rigenerare i dati
Ogni livello ha uno script che lo ricostruisce dalla fonte. Le istruzioni per scaricare i dati di partenza sono nell'intestazione di ciascuno script.

```bash
python3 scripts/build_carg.py <quadro_unione_ispra.geojson>
python3 scripts/scarica_crossref.py crossref.json   # serve accesso a api.crossref.org
python3 scripts/build_jom.py crossref.json <regions> <provinces> <municipalities>
python3 scripts/build_geoportali.py <regions> <provinces>
python3 scripts/valida_dati.py   # controllo qualità: va eseguito prima di ogni commit
```

## Roadmap
- [x] Griglia CARG dal quadro d'unione ufficiale ISPRA
- [x] Livello Journal of Maps da Crossref, con DOI verificati
- [x] Confini regionali ufficiali ISTAT
- [x] Aggiornamento settimanale automatico del Journal of Maps e localizzazioni manuali
- [ ] Localizzare le pubblicazioni in `jom_da_localizzare.csv` (anche gradualmente, con i post di Geologiaintasca)
- [ ] Verificare i link dei geoportali regionali (6 sostituiti il 3/11/2026, da ricontrollare)
- [ ] Carta Geologica d'Italia 1:100.000 (277 fogli)
- [ ] Cartografia geologica marina (CARG Mare)

## Licenze e disclaimer
Il repository è un **indice di collegamenti** a risorse esterne.

* **Codice:** licenza [MIT](LICENSE).
* **Quadro d'unione CARG:** © ISPRA – Servizio Geologico d'Italia, licenza **CC BY 4.0**, come per i dati CARG 1:50.000 nei metadati INSPIRE ISPRA (scelta confermata dal curatore del progetto il 3/11/2026).
* **Confini amministrativi:** © ISTAT, licenza CC BY 4.0.
* **Journal of Maps:** sono indicizzati solo i metadati bibliografici. Gli articoli restano di autori ed editore, con la licenza indicata su ciascuno.

*Geologiaintasca non è titolare dei dati cartografici collegati: fornisce solo il servizio di indicizzazione geografica.*

## Contribuire
1. Apri una **Issue** per segnalare una mappa, un errore o una localizzazione.
2. Fai un **fork** e invia una pull request, dopo aver eseguito `scripts/valida_dati.py`.
