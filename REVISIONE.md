# Revisione IGC-Hub – 2 novembre 2026

Branch: `revisione-2026-11`. Controlli ripetibili con `python3 scripts/valida_dati.py`.

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
| J2 | E | **Anche i DOI con prefisso corretto sono in parte inesistenti.** | A campione su Crossref, 5 non risolvono (es. `…2014.891267`, `…2014.935503`, `…2012.668423`, `…2024.2359973`, `…2014.959569`). Altri esistono ma con titolo diverso: per esempio `…2019.1633426` è "Geomorphology of the Rio Cisles basin (Odle Group…)", non "Geomorphology of the Dolomites". |
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
