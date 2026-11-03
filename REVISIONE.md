# Revisione IGC-Hub – 2 novembre 2026

Branch: `revisione-2026-11`. Controlli ripetibili con `python3 scripts/valida_dati.py`.

## 0. Aggiornamento: dati ricostruiti (stesso giorno)

Tutti i problemi bloccanti delle sezioni 1 e 2 sono stati risolti ricostruendo i dati da fonti ufficiali. Il validatore ora riporta **0 errori**; restano 6 avvisi, tutti relativi a link regionali in http.

| Livello | Prima | Dopo | Fonte | Script |
|---|---|---|---|---|
| CARG | 652 rettangoli in posizione inventata | 636 fogli georeferenziati 20'×12', con stato ISPRA | Quadro d'unione ISPRA (Antropico25k, layer 0) | `build_carg.py` |
| Journal of Maps | 119 voci, 84 DOI di altre riviste | 226 pubblicazioni con DOI Crossref, licenza e precisione della localizzazione | Crossref ISSN 1744-5647 + confini ISTAT | `build_jom.py` |
| Geoportali | 21 rettangoli sovrapposti | 21 confini ISTAT (Trento e Bolzano separate) | ISTAT 2026 via openpolis | `build_geoportali.py` |

**Scelte di metodo (Journal of Maps)**
- Le pubblicazioni sono **punti**, non poligoni. Crossref non fornisce l'area cartografata, e un rettangolo stimato sembrerebbe preciso senza esserlo. Il punto si trova sul centroide dell'unità ISTAT citata nel titolo; il campo `Precisione` dice quale (comune, provincia o regione).
- Regole contro i falsi positivi, ciascuna verificata sui casi reali emersi:
  - un nome di regione o comune vale solo se scritto con la maiuscola ("Adriatic piedmont" non è il Piemonte, "thrust zone" non è il comune di Zone);
  - un toponimo non vale se fa parte di un nome composto ("Santa Barbara Basin" non è il comune di Barbara; "Ferriere-Mollieres Shear Zone" non è Ferriere in provincia di Piacenza; "Piemonte-Ligurian units" non è il Piemonte);
  - i comuni omonimi di regioni o subregioni sono esclusi (Molise, Salento);
  - un comune con nome non univoco in Italia viene accettato solo se il titolo cita anche la sua regione.
- I DOI storici del Journal of Maps (`10.4113/jom.*`, `10.1080/jom.*`, 2005-2011) sono validi. Se lo stesso articolo ha due DOI, si tiene quello Taylor & Francis.
- È stato escluso un record che Crossref associa all'ISSN del Journal of Maps ma con DOI di un'altra rivista (`10.1080/17530350.*`).
- 128 pubblicazioni non sono posizionate: non hanno toponimi ISTAT nel titolo, come per Etna, Campi Flegrei o Dolomiti, oppure citano più regioni. Sono elencate in `dati/journal_of_maps/jom_da_localizzare.csv`.

**Limiti noti**
- Stato dei fogli CARG: le etichette interpretano codici ISPRA non documentati (`bd` → Realizzato, `finanziati` → Finanziato / in corso).
- Licenza del quadro d'unione ISPRA: il servizio riporta solo "© Servizio Geologico d'Italia – ISPRA". **Decisione (3/11/2026):** si adotta la CC BY 4.0, la licenza dichiarata da ISPRA per i dati CARG 1:50k, con attribuzione a ISPRA.
- Link dei geoportali regionali: il curatore ha verificato che i 6 link in http non funzionavano. Sono stati sostituiti con risorse trovate sui siti ufficiali o sul catalogo nazionale RNDT (geodati.gov.it) e vanno ricontrollati. Gli altri 15 link non sono ancora verificati.

| Ente | Nuovo link | Note |
|---|---|---|
| Abruzzo | geoportale.regione.abruzzo.it/Cartanet/catalogo/difesa-suolo-geologia | il vecchio link usava "geoportal"; resta in http |
| Calabria | geodati.gov.it – Carta Geologica raster 1:25.000 | scheda del catalogo nazionale, non il visualizzatore |
| Lazio | dati.lazio.it – Carta Geologica informatizzata 1:25.000 | open data regionali |
| Puglia | SIT Puglia – servizi WMS | la Puglia non ha una carta geologica regionale: il prodotto di riferimento è la Carta Idrogeomorfologica |
| Trento | provincia.tn.it – Carta Geologica della Provincia | |
| Bolzano | Geocatalogo provinciale – Carta geologica | scheda di metadati con i servizi |
- Precisione regionale: per 116 pubblicazioni il punto indica solo la regione, ad esempio il centro della Calabria.

---

*Le sezioni seguenti documentano lo stato iniziale del repository.*

Livelli: **E** = errore bloccante (dato sbagliato) · **W** = avviso (dato approssimato o fragile).

## 1. Problemi nei dati (non corretti in questa revisione)

### CARG – `dati/carg/carg_50k_fogli.geojson`
| # | Liv. | Problema | Evidenza |
|---|---|---|---|
| C1 | E | **La griglia non è georeferenziata.** I 652 fogli sono disposti in sequenza su 28 righe da 24 colonne, partendo da 6°E. Non corrispondono alla posizione reale. | Il Foglio 1 (Passo di Resia, circa 10,5°E) risulta a 6,0–6,5°E. I fogli sardi (es. 459 Alghero, 481 Nuoro) cadono tra 4° e 6°E, cioè in mare o in Francia. |
| C2 | E | **La dimensione dei fogli è sbagliata.** Tutti i poligoni misurano 0,5°×0,333° invece di 20'×12' (0,333°×0,2°), il formato dei fogli IGM 1:50.000. | 652 su 652 |
| C3 | W | Il campo `DOI` contiene testo segnaposto ("Disponibile su OAR…", "Non disponibile / In lavorazione") e non DOI. | 652 su 652 |
| C4 | W | I nomi dei fogli non sono verificati rispetto all'elenco ufficiale. I due file originali erano in disaccordo (es. Foglio 4 risultava "GRAN PILASTRO" in uno e "VALLE AURINA" nell'altro). | confronto tra FINAL e DEFINITIVE |

**Conseguenza:** su uMap il livello CARG mostra un reticolo che non coincide con il territorio. È la causa più probabile dei problemi di visualizzazione.

**Correzione proposta:** sostituire la griglia con il quadro d'unione ufficiale dei fogli 1:50.000 di ISPRA. Il dataset raster CARG 1:50k è dichiarato CC BY 4.0 nei metadati INSPIRE; la licenza dello specifico quadro d'unione vettoriale va verificata prima di usarlo. Nomi e URL vanno presi dalla stessa fonte, non ricostruiti.

### Journal of Maps – `dati/journal_of_maps/jom_italia.geojson`
| # | Liv. | Problema | Evidenza |
|---|---|---|---|
| J1 | E | **84 DOI su 119 non appartengono al Journal of Maps.** Alcuni rimandano a riviste o libri senza relazione con il titolo. | Esempi: `10.1038/044271a0` (Nature, 1891) per il Vesuvio, `10.1093/owc/…` (Oxford World's Classics) per il Brennero, `10.17656/jzs.10477` (rivista irachena) usato sia per la Toscana sia per la Sardegna. |
| J2 | E | **I titoli non corrispondono ai DOI.** ~~Una prima versione di questo rapporto indicava 5 DOI come inesistenti: l'affermazione era sbagliata.~~ Le mancate risposte venivano dallo strumento di consultazione, non da Crossref. L'export Crossref completo conferma che `…2014.891267`, `…2014.935503`, `…2012.668423` e `…2014.959569` esistono. Resta il problema dei titoli. | Per esempio `…2019.1633426` è "Geomorphology of the Rio Cisles basin (Odle Group…)", non "Geomorphology of the Dolomites"; `…2014.891267` è "Drought events… (Calabria)", non "Drought events in Calabria". Solo 28 dei 119 DOI originali compaiono nell'export Crossref "Italy". |
| J3 | E | 4 DOI duplicati, assegnati a pubblicazioni diverse. | `…2013.842507` usato per Monviso e per Argentera |
| J4 | E | I titoli sono generici ("Geology of X") e non corrispondono ai titoli reali. | — |
| J5 | W | Le geometrie sono rettangoli approssimati, non l'area cartografata. | 119 su 119 |
| J6 | W | Il README dichiarava "oltre 130" pubblicazioni, ma il file ne contiene 119. | — |

**Conseguenza:** il livello non è utilizzabile così com'è. Pubblicarlo significa diffondere riferimenti bibliografici errati.

**Correzione proposta:** rigenerare il livello da Crossref (ISSN 1744-5647, filtro su area italiana), tenendo solo DOI verificati. Il bounding box di ogni mappa va preso dall'articolo, non stimato. Il Journal of Maps è una rivista Open Access indicizzata in DOAJ; la licenza va però verificata articolo per articolo prima di usare figure (ad esempio nei post di Geologiaintasca).

### Geoportali regionali – `dati/geoportali_regionali/geoportali_regionali.geojson`
| # | Liv. | Problema |
|---|---|---|
| R1 | W | Le regioni sono rappresentate come rettangoli che si sovrappongono: un clic al confine può aprire la regione sbagliata. |
| R2 | W | 6 URL in `http` (Abruzzo, Calabria, Lazio, Puglia, Trento, Bolzano); alcuni puntano a portali probabilmente dismessi (es. Trento `server.pt`). Link non verificati in questa revisione. |

**Correzione proposta:** usare i confini amministrativi ufficiali generalizzati e verificare a mano i 21 link.

## 2. Correzioni applicate in questo branch
| Modifica | Motivo |
|---|---|
| Eliminato `carg_italy_FINAL.geojson`; tenuto `carg_italy_DEFINITIVE.geojson`, rinominato `carg_50k_fogli.geojson` | Due file con le stesse 652 geometrie errate e attributi in conflitto. DEFINITIVE ha URL OAR uniformi; FINAL aveva 413 fogli "non disp." con URL generici. La versione eliminata resta nella cronologia git. |
| Cartelle e file rinominati senza spazi né maiuscole (`dati/carg/`, `dati/geoportali_regionali/`, `jom_italia.geojson`) | Gli spazi rendono fragili gli URL raw e gli script. |
| Aggiunto il campo `Type` ("Research Map") al livello JoM | Schema uniforme su tutti i livelli: serve per stili e filtri su uMap. |
| `index.html` riscritto | Puntava a due file inesistenti (`journal_of_maps_italy_top150.geojson`, `carg_italy_GRID_FIXED.geojson`), quindi la mappa era vuota. Ora carica i tre livelli, senza la libreria leaflet-ajax non più mantenuta, protegge i popup dall'HTML nei dati e mostra un avviso di revisione. |
| Aggiunto `LICENSE` (MIT) | La licenza MIT era dichiarata nel README ma mancava il file, quindi su GitHub non risultava applicata. |
| README aggiornato | Percorsi, conteggi reali, stato dei dati, roadmap con le priorità. Rimosso il riferimento a IODL 2.0: ISPRA dichiara CC BY 4.0 per i dati CARG 1:50k, e la licenza va citata per ciascun ente, non presunta. |
| Aggiunto `scripts/valida_dati.py` | Rende i controlli ripetibili a ogni aggiornamento. Nessuna dipendenza esterna. |

## 3. Altre note
- Il commit `bd6f4c3` ("Update fmt.Println output from 'Hello' to 'Goodbye'") ha un messaggio che non c'entra con la modifica, che riguarda il GeoJSON JoM. Conviene usare messaggi descrittivi.
- La maggior parte dei commit sono upload dall'interfaccia web, quindi le modifiche ai dati non sono tracciabili riga per riga. Con lo script di validazione conviene passare a commit da git locale.

## 4. Decisioni aperte (per il proprietario del progetto)
1. Licenza della **struttura dati curata**: la MIT è pensata per il software. Per un indice di dati di solito si usa CC BY 4.0 o ODbL.
2. Se pubblicare la mappa uMap nello stato attuale o metterla offline finché CARG e JoM non sono ricostruiti.
3. Perimetro del progetto (vedi discussione successiva).
