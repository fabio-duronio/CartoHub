# Geologiaintasca – Cartografia geologica italiana
### L'Hub digitale aperto per la cartografia geologica in Italia.

**Progetto a cura di [Geologiaintasca](https://www.facebook.com/profile.php?id=61565694163261)**

Indice geografico (GeoJSON) delle risorse cartografiche geologiche italiane. Riunisce i rimandi a dati di istituzioni nazionali, enti regionali e ricerca accademica, oggi distribuiti su portali diversi.

[**Mappa web (GitHub Pages)**](https://fabio-duronio.github.io/geologiaintasca/) · [Mappa uMap](https://umap.openstreetmap.fr/it/map/italian-geological-cartography-hub-igc-hub_1338725)

> [!NOTE]
> **Dati ricostruiti a novembre 2026** da fonti ufficiali (ISPRA, ISTAT, Crossref). Cosa è cambiato e quali limiti restano: [REVISIONE.md](REVISIONE.md).

---

## Dataset

| Livello | File | Feature | Fonte |
|---|---|---|---|
| Progetto CARG 1:50.000 | `dati/carg/carg_50k_fogli.geojson` | 634 fogli | CARG-GATE (ISPRA) |
| Carta Geologica d'Italia 1:100.000 | `dati/carta_100k/carta_100k_fogli.geojson` | 278 fogli | Quadro d'unione e catalogo Biblioteca ISPRA |
| Journal of Maps | `dati/journal_of_maps/jom_italia.geojson` | 313 pubblicazioni | Crossref + confini ISTAT |
| Geoportali regionali | `dati/geoportali_regionali/geoportali_regionali.geojson` | 21 enti | Selezione manuale + confini ISTAT |

Campi comuni a tutti i livelli: `Title`, `URL`, `Location`, `Type`. Il campo `Dettagli` contiene il testo del popup di uMap (stesse etichette e link di `index.html`), generato da `scripts/dettagli_popup.py`.

### 1. Cartografia ufficiale (Progetto CARG)
Fogli della Carta Geologica d'Italia alla scala 1:50.000, con lo stato di realizzazione indicato su **[CARG-GATE](https://progetto-carg.isprambiente.it/cartografiaCARG/index.php?source=cartageologica)** (ISPRA). **Si aggiorna da solo ogni lunedì.**
* **Stato:** copiato testualmente da CARG-GATE: *Stampato*, *In attesa di stampa*, *In allestimento per la stampa*, *Rilevamento in corso*. Se il portale non indica uno stato, il campo resta vuoto: nessuno stato viene dedotto.
* **Colori:** gli stessi della legenda di CARG-GATE.
* **Link:** la scheda del foglio sul portale, il DOI della carta e il DOI delle note illustrative (archivio Open Access di ISPRA, quando disponibili).
* **Altri campi:** anno di stampa, coordinatori scientifici, stato della banca dati.

*Fonte: CARG-GATE – ISPRA, Servizio Geologico d'Italia, licenza CC BY 4.0. La regione nel link alla scheda si ricava dai confini ISTAT.*

### 1b. Carta Geologica d'Italia 1:100.000 (serie storica)
Fogli della Carta Geologica d'Italia alla scala 1:100.000, con le edizioni presenti nel catalogo della Biblioteca ISPRA.
* **Geometria:** quadro d'unione ufficiale ISPRA (servizio `geologica100k`, layer `CGI100K_Quadro_di_unione`).
* **Edizioni:** dal catalogo della Biblioteca ISPRA, che ha messo online l'intera serie (prima e seconda edizione). Per ogni foglio sono elencate tutte le edizioni trovate, con anno, eventuale titolo diverso (es. il 141 Pescara nella 1ª edizione si chiamava "Chieti") e presenza della copia digitale. Edizione e anno sono copiati dalla scheda; se l'edizione non è indicata, lo si dichiara.
* **Link:** alla scheda del catalogo dell'edizione più recente con copia digitale e alle note illustrative. Le scansioni non vengono riprodotte, perché il catalogo non ne dichiara la licenza.
* **Fogli senza schede:** restano sulla mappa con la dicitura "Nessuna scheda trovata nel catalogo ISPRA".
* **Aggiornamento:** automatico il primo lunedì di ogni mese ([`aggiorna-100k.yml`](.github/workflows/aggiorna-100k.yml)).

*Fonte: ISPRA – Servizio Geologico d'Italia (quadro d'unione 1:100.000; catalogo OPAC della Biblioteca ISPRA).*

### 2. Ricerca scientifica (Journal of Maps)
Articoli del *Journal of Maps* su aree italiane. Il punto indica la località, non l'area cartografata. **Il livello si aggiorna da solo ogni lunedì** (vedi *Aggiornamento automatico*).
* **Posizione:** il campo `Precisione` dice come è stato ottenuto il punto:
  * `Coordinate`: coordinate indicate nel paper (localizzazione manuale);
  * `Comune`, `Provincia`, `Regione`: centroide dell'unità ISTAT indicata dal curatore oppure, in automatico, citata nel titolo. Il campo `Fonte` distingue i due casi.
* **Non posizionate:** 9 pubblicazioni non hanno un toponimo ISTAT nel titolo (es. Etna, Campi Flegrei, Dolomiti) oppure citano più regioni, e non hanno ancora una localizzazione manuale. Sono elencate in `jom_da_localizzare.csv` e non vengono collocate a stima.
* **Licenza:** il campo `Licenza` riporta quella dichiarata in Crossref: 132 CC BY 4.0, 33 CC BY-NC 4.0, 4 CC BY-NC-ND 4.0. Per 144 articoli Crossref non indica la licenza: va verificata sulla pagina dell'articolo prima di riusarne le figure.

*Fonte: metadati [Crossref](https://www.crossref.org/) (ISSN 1744-5647); confini ISTAT per la localizzazione.*

### 3. Geologia ISPRA (solo nella mappa web)
Due livelli di visualizzazione forniti dai servizi WMS del Servizio Geologico d'Italia, spenti all'apertura. Le immagini e le informazioni al clic arrivano direttamente da ISPRA: il repository non ne conserva copia.
* **Geologia CARG 1:25.000:** unità geologiche ed elementi tettonici dei fogli CARG disponibili nel servizio (210 a novembre 2026), visibili da zoom 11.
* **Geologia 1:100.000:** unità geologiche, limiti e tettonica della Carta Geologica d'Italia 1:100.000 su tutto il territorio, visibili da zoom 10.
* **Clic sulla mappa:** nome, sigla, tipo ed età dell'unità nel punto.

*Fonte: servizi `geo/SGI_ISPRA_Geologia25k` e `servizi/geologica100k` su sinacloud.isprambiente.it (ISPRA – Servizio Geologico d'Italia).*

### 4. Geoportali regionali
Geoportali e WebGIS delle Regioni e delle Province autonome di Trento e Bolzano.

*Fonte link: selezione manuale. Confini: ISTAT, 1° gennaio 2026 (CC BY 4.0), via [openpolis/geojson-italy](https://github.com/openpolis/geojson-italy), semplificati a circa 300 m.*

---

## Aggiornamento automatico
Tre GitHub Action aggiornano i dati: [`aggiorna-carg.yml`](.github/workflows/aggiorna-carg.yml) rigenera ogni lunedì i fogli CARG da CARG-GATE, [`aggiorna-100k.yml`](.github/workflows/aggiorna-100k.yml) la Carta 1:100.000 il primo lunedì del mese, [`aggiorna-jom.yml`](.github/workflows/aggiorna-jom.yml) il livello Journal of Maps. Quest'ultima parte:
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
python3 scripts/build_100k.py                      # serve accesso ai siti ISPRA (quadro d'unione e catalogo)
python3 scripts/scarica_crossref.py crossref.json   # serve accesso a api.crossref.org
python3 scripts/build_jom.py crossref.json <regions> <provinces> <municipalities>
python3 scripts/build_geoportali.py <regions> <provinces>
python3 scripts/dettagli_popup.py   # testo dei popup di uMap (campo Dettagli)
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
- [x] Carta Geologica d'Italia 1:100.000 (278 fogli, edizioni dal catalogo ISPRA)
- [ ] Cartografia geologica marina (CARG Mare)
- [x] Geologia CARG 1:25.000 e 1:100.000 come livelli WMS ISPRA nella mappa web (i servizi indicati nel catalogo GeoSciencesIR non erano raggiungibili a novembre 2026)

## Licenze e disclaimer
Il repository è un **indice di collegamenti** a risorse esterne.

* **Codice:** licenza [MIT](LICENSE).
* **Fogli CARG:** © ISPRA – Servizio Geologico d'Italia, dati di CARG-GATE con licenza **CC BY 4.0** dichiarata dal portale.
* **Carta 1:100.000:** © ISPRA – Servizio Geologico d'Italia. Sono indicizzati quadro d'unione e schede del catalogo; le scansioni restano sul sito ISPRA.
* **Geologia 1:25.000 e 1:100.000:** © ISPRA – Servizio Geologico d'Italia, servizi di visualizzazione WMS; immagini e informazioni al clic sono fornite direttamente da ISPRA.
* **Confini amministrativi:** © ISTAT, licenza CC BY 4.0.
* **Journal of Maps:** sono indicizzati solo i metadati bibliografici. Gli articoli restano di autori ed editore, con la licenza indicata su ciascuno.

*Geologiaintasca non è titolare dei dati cartografici collegati: fornisce solo il servizio di indicizzazione geografica.*

## Contribuire
1. Apri una **Issue** per segnalare una mappa, un errore o una localizzazione.
2. Fai un **fork** e invia una pull request, dopo aver eseguito `scripts/valida_dati.py`.
