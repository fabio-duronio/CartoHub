# Geologiaintasca – Cartografia geologica italiana

Indice geografico delle risorse cartografiche geologiche italiane. Riunisce i rimandi a dati di istituzioni nazionali, enti regionali e ricerca accademica, oggi distribuiti su portali diversi. Nasce dalle pagine di divulgazione geoscientifica [Geologiaintasca](https://www.facebook.com/profile.php?id=61565694163261).

[**Mappa web (GitHub Pages)**](https://fabio-duronio.github.io/geologiaintasca/) · [Mappa uMap](https://umap.openstreetmap.fr/it/map/geologiaintasca-cartografia-geologica-italiana_1338725)

---

## Dataset

I dati sono file GeoJSON nella cartella `dati/`, letti sia dalla mappa web sia da uMap.

| Livello | File | Elementi (nov. 2026) | Fonte |
|---|---|---|---|
| Progetto CARG 1:50.000 | `dati/carg/carg_50k_fogli.geojson` | 634 fogli | CARG-GATE (ISPRA) |
| Carta Geologica d'Italia 1:100.000 | `dati/carta_100k/carta_100k_fogli.geojson` | 278 fogli | Quadro d'unione e catalogo Biblioteca ISPRA |
| Journal of Maps | `dati/journal_of_maps/jom_italia.geojson` | 191 pubblicazioni | Crossref + confini ISTAT |
| JoM – studi a scala regionale | `dati/journal_of_maps/jom_regionali.geojson` | 122 pubblicazioni | Crossref + confini ISTAT |
| Altre riviste | `dati/altre_riviste/altre_riviste.geojson` | 4 pubblicazioni | Selezione manuale + confini ISTAT |
| Geoportali regionali | `dati/geoportali_regionali/geoportali_regionali.geojson` | 21 enti | Selezione manuale + confini ISTAT |

Campi comuni a tutti i livelli: `Title`, `URL`, `Location`, `Type`. Il campo `Dettagli` contiene il testo del popup di uMap (stesse etichette e link di `index.html`), generato da `scripts/dettagli_popup.py`.

### 1. Cartografia ufficiale (Progetto CARG)
Fogli della Carta Geologica d'Italia alla scala 1:50.000, con lo stato di realizzazione indicato su **[CARG-GATE](https://progetto-carg.isprambiente.it/cartografiaCARG/index.php?source=cartageologica)** (ISPRA). **Si aggiorna da solo ogni lunedì.**
* **Stato:** copiato testualmente da CARG-GATE: *Stampato*, *In attesa di stampa*, *In allestimento per la stampa*, *Rilevamento in corso*. Se il portale non indica uno stato, il campo resta vuoto: nessuno stato viene dedotto.
* **Colori:** gli stessi della legenda di CARG-GATE.
* **Link:** la scheda del foglio sul portale, il DOI della carta e il DOI delle note illustrative (archivio Open Access di ISPRA, quando disponibili).
* **Altri campi:** anno di stampa, coordinatori scientifici, stato della banca dati.

*Fonte: CARG-GATE – ISPRA, Servizio Geologico d'Italia, licenza CC BY 4.0. La regione nel link alla scheda si ricava dai confini ISTAT.*

### 2. Carta Geologica d'Italia 1:100.000 (serie storica)
Fogli della Carta Geologica d'Italia alla scala 1:100.000, con le edizioni presenti nel catalogo della Biblioteca ISPRA.
* **Geometria:** quadro d'unione ufficiale ISPRA (servizio `geologica100k`, layer `CGI100K_Quadro_di_unione`).
* **Edizioni:** dal catalogo della Biblioteca ISPRA, che ha messo online l'intera serie (prima e seconda edizione). Per ogni foglio sono elencate tutte le edizioni trovate, con anno, eventuale titolo diverso (es. il 141 Pescara nella 1ª edizione si chiamava "Chieti") e presenza della copia digitale. Edizione e anno sono copiati dalla scheda; se l'edizione non è indicata, lo si dichiara.
* **Link:** alla scheda del catalogo dell'edizione più recente con copia digitale e alle note illustrative. Le scansioni non vengono riprodotte, perché il catalogo non ne dichiara la licenza.
* **Fogli senza schede:** restano sulla mappa con la dicitura "Nessuna scheda trovata nel catalogo ISPRA".
* **Aggiornamento:** automatico il primo lunedì di ogni mese ([`aggiorna-100k.yml`](.github/workflows/aggiorna-100k.yml)).

*Fonte: ISPRA – Servizio Geologico d'Italia (quadro d'unione 1:100.000; catalogo OPAC della Biblioteca ISPRA).*

### 3. Ricerca scientifica (Journal of Maps)
Articoli del *Journal of Maps* su aree italiane, in due livelli. Il punto indica la località, non l'area cartografata. **I livelli si aggiornano da soli ogni lunedì** (vedi *Aggiornamento automatico*).
* **Journal of Maps** (`jom_italia.geojson`): studi localizzati. Il campo `Precisione` dice come è stato ottenuto il punto:
  * `Coordinate`: coordinate indicate nel paper (localizzazione manuale);
  * `Comune`: centroide del comune ISTAT indicato dal curatore oppure, in automatico, citato nel titolo. Il campo `Fonte` distingue i due casi.
* **JoM – studi a scala regionale** (`jom_regionali.geojson`): punto sul centroide della regione o della provincia (`Precisione` `Regione` o `Provincia`). Il campo `Ambito` distingue:
  * `Regionale`: studio su un'intera regione, provincia o area vasta, confermato in `regionali.csv`;
  * `Da localizzare`: nel titolo c'è solo la regione o la provincia; lo studio è locale e va ancora posizionato. Sta qui e non nel livello principale, così un centroide non viene scambiato per il luogo dello studio.
* **Non posizionate:** le pubblicazioni senza un toponimo ISTAT nel titolo (es. Etna, Campi Flegrei, Dolomiti) o che citano più regioni, e senza una localizzazione manuale, sono elencate in `jom_da_localizzare.csv` e non vengono collocate a stima.
* **Licenza:** il campo `Licenza` riporta quella dichiarata in Crossref (CC BY 4.0, CC BY-NC 4.0, CC BY-NC-ND 4.0). Quando Crossref non la indica, va verificata sulla pagina dell'articolo prima di riusarne le figure.

*Fonte: metadati [Crossref](https://www.crossref.org/) (ISSN 1744-5647); confini ISTAT per la localizzazione.*

**In uMap** il livello regionale si aggiunge come livello con dati remoti:
* URL: `https://raw.githubusercontent.com/fabio-duronio/geologiaintasca/main/dati/journal_of_maps/jom_regionali.geojson`
* tipo di livello **Cluster**: gli articoli della stessa regione hanno le stesse coordinate e, senza cluster, solo l'ultimo sarebbe cliccabile;
* modello del popup come gli altri livelli: `# {Title}` + `{Dettagli}`; nascosto all'apertura della mappa.

### 3b. Altre riviste (selezione manuale)
Carte geologiche allegate ad articoli di riviste diverse dal *Journal of Maps* (es. *Geological Field Trips and Maps*), aggiunte **solo quando un post di Geologiaintasca riguarda una carta allegata**. Nessuna ricerca automatica: queste riviste pubblicano poche carte e molti contributi senza carta, quindi un indice automatico richiederebbe comunque un filtro a mano.
* **Criteri:** territorio italiano, carta allegata all'articolo (tavola o materiale supplementare), Open Access con licenza aperta dichiarata sulla pagina dell'articolo.
* **Posizione:** come per il Journal of Maps, `Precisione` `Comune` (centroide del comune ISTAT indicato dal curatore) o `Coordinate` (solo se scritte nel testo). Nessuna coordinata stimata.
* **Metadati:** titolo, anno e licenza copiati dalla pagina dell'articolo, perché non tutte le riviste li depositano completi su Crossref.

*Fonte: pagine degli articoli citati; confini ISTAT per la localizzazione.*

### 4. Geologia ISPRA (solo nella mappa web)
Due livelli di visualizzazione forniti dai servizi WMS del Servizio Geologico d'Italia, spenti all'apertura. Le immagini e le informazioni al clic arrivano direttamente da ISPRA: il repository non ne conserva copia.
* **Geologia CARG 1:25.000:** unità geologiche, depositi quaternari, limiti geologici, elementi tettonici, elementi strutturali e giaciture dei fogli CARG disponibili nel servizio (210 a novembre 2026), visibili da zoom 11.
* **Geologia 1:100.000:** unità geologiche, limiti, tettonica, tracce delle sezioni, stratimetria e simboli puntuali (sondaggi, pozzi, miniere, emissioni gassose, cave, forme carsiche, località d'interesse, sorgenti) della Carta Geologica d'Italia 1:100.000 su tutto il territorio. Unità e limiti sono visibili da zoom 10, gli altri elementi da zoom 11-12.
* **Clic sulla mappa:** nome, sigla, tipo ed età dell'unità nel punto; per la 1:25.000 anche il tipo di deposito quaternario.

*Fonte: servizi `geo/SGI_ISPRA_Geologia25k` e `servizi/geologica100k` su sinacloud.isprambiente.it (ISPRA – Servizio Geologico d'Italia).*

**Strumenti della mappa web:** quattro sfondi (OpenStreetMap, OpenTopoMap con curve di livello, ortofoto AGEA 2022-2024 a 20 cm, rilievo ombreggiato TINITALY dell'INGV), opacità regolabile per ciascun livello di geologia direttamente nel pannello dei livelli, barra di scala con rapporto numerico, ricerca unica: mentre si scrive cerca fogli CARG e 1:100.000 (numero o nome), articoli del Journal of Maps (titolo o luogo) e coordinate «lat, lon»; con Invio aggiunge le località di OpenStreetMap; pulsante «Posizione attuale» (GPS del dispositivo); numeri dei fogli CARG sulla mappa da zoom 9; legenda richiudibile, chiusa su telefono.

### 5. Geoportali regionali
Geoportali e WebGIS delle Regioni e delle Province autonome di Trento e Bolzano.

*Fonte link: selezione manuale. Confini: ISTAT, 1° gennaio 2026 (CC BY 4.0), via [openpolis/geojson-italy](https://github.com/openpolis/geojson-italy), semplificati a circa 300 m.*

---

## Link diretti alla mappa web
Per collegare un post a un punto preciso della mappa:
* `https://fabio-duronio.github.io/geologiaintasca/?carg=628` apre il foglio CARG 628 con la sua scheda;
* `https://fabio-duronio.github.io/geologiaintasca/?carta100k=141` apre il foglio 141 della Carta 1:100.000;
* `https://fabio-duronio.github.io/geologiaintasca/?doi=10.1080/17445647.2013.842508` apre l'articolo del Journal of Maps;
* `https://fabio-duronio.github.io/geologiaintasca/#13/42.35000/13.40000` apre la mappa a quello zoom e su quel punto. L'indirizzo nella barra del browser si aggiorna mentre ci si sposta, quindi basta copiarlo.

Nei popup il pulsante «Copia link» prepara questi indirizzi.

---
## Aggiornamento automatico
Quattro GitHub Action aggiornano i dati: [`aggiorna-carg.yml`](.github/workflows/aggiorna-carg.yml) rigenera ogni lunedì i fogli CARG da CARG-GATE, [`aggiorna-100k.yml`](.github/workflows/aggiorna-100k.yml) la Carta 1:100.000 il primo lunedì del mese, [`aggiorna-jom.yml`](.github/workflows/aggiorna-jom.yml) il livello Journal of Maps, [`aggiorna-altre-riviste.yml`](.github/workflows/aggiorna-altre-riviste.yml) il livello Altre riviste (solo quando cambia il suo CSV). L'Action del Journal of Maps parte:
* **ogni lunedì**, scaricando da Crossref i nuovi articoli sull'Italia;
* **a ogni modifica di `localizzazioni.csv`**, così una localizzazione aggiunta compare sulla mappa in pochi minuti;
* **a mano**, da *Actions → Aggiorna Journal of Maps → Run workflow*.

Se il validatore trova errori, l'Action si ferma e non modifica i dati. Se non ci sono novità, non fa commit.

### Aggiungere una localizzazione o uno studio regionale
Il file [`dati/journal_of_maps/localizzazioni.csv`](dati/journal_of_maps/localizzazioni.csv) (separatore `;`) prevale sulla localizzazione automatica e permette di aggiungere articoli che la ricerca per "Italy" non trova.

```
DOI;Comune;Provincia;Lat;Lon;Note
10.1080/17445647.2012.668423;Gaiole in Chianti;SI;;;Monti del Chianti
10.1080/17445647.2013.842508;;;40.827;14.139;Campi Flegrei, coordinate dal testo
```
* `Comune` (nome ufficiale ISTAT) + `Provincia` (sigla), **oppure** `Lat` + `Lon` in gradi decimali.
* Si modifica direttamente da GitHub: icona della matita sul file, incolla la riga, *Commit changes*.
* Un comune inesistente o una riga incompleta fanno fallire l'Action con il numero della riga, e GitHub invia una notifica.

Gli studi su un'intera regione, provincia o area vasta stanno in [`regionali.csv`](dati/journal_of_maps/regionali.csv) (`DOI;Area;Regione;Provincia;Note`): punto sul centroide della provincia (sigla) se indicata, altrimenti della regione (nome ISTAT); `Area` è il nome mostrato sulla mappa, se diverso da quello della regione o della provincia.

Gli articoli da non mettere sulla mappa (commenti, temi non cartografici, carte a scala nazionale, nessun luogo indicato) stanno in [`esclusioni.csv`](dati/journal_of_maps/esclusioni.csv) (`DOI;Categoria;Motivo`): non compaiono né sulla mappa né tra quelli da localizzare.

Un DOI può comparire in un solo file tra `localizzazioni.csv`, `regionali.csv` ed `esclusioni.csv`: un doppione fa fallire l'Action.

Per ogni post di Geologiaintasca su un articolo del Journal of Maps viene preparata la riga da aggiungere.

### Aggiungere un articolo di un'altra rivista
Il file [`dati/altre_riviste/localizzazioni.csv`](dati/altre_riviste/localizzazioni.csv) (separatore `;`) alimenta il livello *Altre riviste*. A ogni modifica l'Action [`aggiorna-altre-riviste.yml`](.github/workflows/aggiorna-altre-riviste.yml) rigenera il livello in pochi minuti.

```
DOI;Rivista;Titolo;Anno;Licenza;Comune;Provincia;Lat;Lon;Note
10.3301/GFT.2026.13;Geological Field Trips and Maps;Evolution of the Fiastrone Gorge…;2026;CC BY 4.0;Fiastra;MC;;;Gola del Fiastrone
```
* `DOI`, `Rivista`, `Titolo`, `Anno`, `Licenza` obbligatori. Nelle `Note` niente punto e virgola (è il separatore): usare la virgola. Poi `Comune` + `Provincia` **oppure** `Lat` + `Lon`, come per il Journal of Maps.
* Un DOI del Journal of Maps, un DOI ripetuto, un campo obbligatorio vuoto o un comune inesistente fanno fallire l'Action con il numero della riga.

## Rigenerare i dati
Ogni livello ha uno script che lo ricostruisce dalla fonte. Le istruzioni per scaricare i dati di partenza sono nell'intestazione di ciascuno script.

```bash
python3 -I scripts/scarica_carggate.py carggate.json   # serve accesso a progetto-carg.isprambiente.it
python3 -I scripts/build_carg.py carggate.json <regions>
python3 -I scripts/build_100k.py                       # serve accesso ai siti ISPRA (quadro d'unione e catalogo)
python3 -I scripts/scarica_crossref.py crossref.json   # serve accesso a api.crossref.org
python3 -I scripts/build_jom.py crossref.json <regions> <provinces> <municipalities>
python3 -I scripts/build_altre_riviste.py <municipalities>
python3 -I scripts/build_geoportali.py <regions> <provinces>
python3 -I scripts/dettagli_popup.py                   # testo dei popup (campo Dettagli)
python3 -I scripts/valida_dati.py                      # controllo qualità: va eseguito prima di ogni commit
```

## Limiti noti
* **Journal of Maps:** il punto indica una località, non l'area cartografata. Nel livello regionale il punto è il centro della regione o della provincia.
* **Carta 1:100.000:** alcuni fogli non hanno schede nel catalogo ISPRA; le scansioni non sono riprodotte perché il catalogo non ne dichiara la licenza.
* **Geologia ISPRA:** è servita dai server ISPRA; se il servizio non risponde, il livello resta vuoto. I servizi non dichiarano una licenza: si cita la fonte.
* **Geoportali regionali:** i link sono scelti a mano e possono cambiare senza preavviso; quello dell'Abruzzo è solo in http.

## Roadmap
- [x] Fogli CARG da CARG-GATE, con stato ufficiale e aggiornamento settimanale
- [x] Carta Geologica d'Italia 1:100.000, con edizioni dal catalogo ISPRA
- [x] Journal of Maps da Crossref, con DOI verificati, localizzazioni manuali e aggiornamento settimanale
- [x] Geoportali regionali su confini ISTAT
- [x] Geologia CARG 1:25.000 e 1:100.000 come livelli WMS ISPRA nella mappa web
- [ ] Localizzare gli articoli `Da localizzare` del livello regionale e quelli rimasti in `jom_da_localizzare.csv` (servono gli abstract o i paper)
- [ ] Verificare i link dei geoportali regionali
- [ ] Cartografia geologica marina (CARG Mare)

## Licenze e disclaimer
Il repository è un **indice di collegamenti** a risorse esterne.

* **Codice:** licenza [MIT](LICENSE).
* **Fogli CARG:** © ISPRA – Servizio Geologico d'Italia, dati di CARG-GATE con licenza **CC BY 4.0** dichiarata dal portale.
* **Carta 1:100.000:** © ISPRA – Servizio Geologico d'Italia. Sono indicizzati quadro d'unione e schede del catalogo; le scansioni restano sul sito ISPRA.
* **Geologia 1:25.000 e 1:100.000:** © ISPRA – Servizio Geologico d'Italia, servizi di visualizzazione WMS; immagini e informazioni al clic sono fornite direttamente da ISPRA.
* **Confini amministrativi:** © ISTAT, licenza CC BY 4.0.
* **Sfondi della mappa web:** © OpenStreetMap contributors (ODbL); OpenTopoMap (CC BY-SA); ortofoto AGEA voli 2022, 2023 e 2024, © AGEA – Agenzia per le Erogazioni in Agricoltura, servizi WMTS del [GeoPortale AGEA](https://geoportale.agea.gov.it/) (CC BY 4.0); TINITALY/1.1 © INGV, Tarquini S., Isola I., Favalli M., Battistini A., Dotta G. (2023), [doi:10.13127/tinitaly/1.1](https://doi.org/10.13127/tinitaly/1.1) (CC BY 4.0).
* **Ricerca delle località:** [Nominatim](https://nominatim.openstreetmap.org/), © OpenStreetMap contributors; una ricerca alla volta, come richiesto dalle regole d'uso del servizio.
* **Journal of Maps:** sono indicizzati solo i metadati bibliografici. Gli articoli restano di autori ed editore, con la licenza indicata su ciascuno.

*Geologiaintasca non è titolare dei dati cartografici collegati: fornisce solo il servizio di indicizzazione geografica.*

## Contribuire
1. Apri una **Issue** per segnalare una mappa, un errore o una localizzazione.
2. Fai un **fork** e invia una pull request, dopo aver eseguito `scripts/valida_dati.py`.
