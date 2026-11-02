# Italian Geological Cartography Hub (IGC-Hub)
### L'Hub digitale aperto per la cartografia geologica in Italia.

**Progetto a cura di [Geologiaintasca](https://www.geologiaintasca.it)**

Questo repository ospita un indice geografico (GeoJSON) delle risorse cartografiche geologiche italiane. L'obiettivo è riunire in un'unica mappa interattiva i rimandi a dati di istituzioni nazionali, enti regionali e ricerca accademica, oggi distribuiti su portali diversi.

[**Mappa interattiva (uMap)**](https://umap.openstreetmap.fr/it/map/cartografia-geologica-italiana_1338725) · [Anteprima Leaflet](index.html)

> [!WARNING]
> **Dati in revisione (novembre 2026).** Le geometrie attuali sono indicative: la griglia CARG non corrisponde alla posizione reale dei fogli, e parte dei riferimenti del livello Journal of Maps non è verificata. Non usare la mappa per localizzare un foglio o una pubblicazione. Dettagli e piano di correzione in [REVISIONE.md](REVISIONE.md).

---

## Dataset

| Livello | File | Feature | Stato |
|---|---|---|---|
| Progetto CARG 1:50.000 | `dati/carg/carg_50k_fogli.geojson` | 652 | Griglia da ricostruire |
| Journal of Maps | `dati/journal_of_maps/jom_italia.geojson` | 119 | DOI da verificare |
| Geoportali regionali | `dati/geoportali_regionali/geoportali_regionali.geojson` | 21 | Geometrie semplificate, link da verificare |

Tutti i file condividono lo stesso schema: `Title`, `URL`, `Location`, `Type` (più `DOI` o `Description` dove pertinente).

### 1. Cartografia ufficiale (Progetto CARG)
Quadro dei 652 fogli geologici previsti dal Progetto CARG alla scala 1:50.000. Ogni foglio rimanda alla ricerca nell'archivio Open Access di ISPRA (OAR).
*Fonte: Servizio Geologico d'Italia – ISPRA.*

### 2. Ricerca scientifica (Journal of Maps)
Selezione di pubblicazioni con mappe di aree italiane: geologia, geomorfologia, rischi geologici.
*Fonte metadati: Crossref.*

### 3. Geoportali regionali
Accesso diretto ai geoportali e WebGIS regionali e delle Province autonome di Trento e Bolzano (21 enti), dove si trova la cartografia geologica di dettaglio (spesso 1:10.000 o 1:25.000).
*Fonte: selezione manuale dei servizi regionali.*

---

## Controllo qualità
```bash
python3 scripts/valida_dati.py
```
Lo script controlla schema, duplicati, posizione geografica, DOI e dimensione dei fogli. Va eseguito prima di ogni commit sui dati.

## Roadmap
- [ ] **Priorità:** ricostruire la griglia CARG dal quadro d'unione ufficiale ISPRA (fogli 20'×12').
- [ ] **Priorità:** ricostruire il livello Journal of Maps da Crossref (solo DOI con prefisso `10.1080/17445647.`).
- [ ] Sostituire i rettangoli regionali con i confini amministrativi ufficiali.
- [ ] Carta Geologica d'Italia 1:100.000 (277 fogli), utile nelle aree non coperte dal CARG.
- [ ] Cartografia geologica marina (CARG Mare).

## Licenze e disclaimer
Il repository è un **indice di collegamenti** a risorse esterne.

* **Codice:** licenza [MIT](LICENSE).
* **Dati CARG e regionali:** appartengono ai rispettivi enti (ISPRA, Regioni, Province autonome), che restano titolari delle licenze.
* **Journal of Maps:** sono indicizzati solo i metadati bibliografici (titolo, DOI). Gli articoli restano di autori ed editore, con la licenza indicata su ciascuno.

*Geologiaintasca non è titolare dei dati cartografici collegati: fornisce solo il servizio di indicizzazione geografica.*

## Contribuire
1. Apri una **Issue** per segnalare una mappa o un errore.
2. Fai un **fork** e invia una pull request, dopo aver eseguito `scripts/valida_dati.py`.
