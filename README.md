# Italian Geological Cartography Hub (IGC-Hub)
### L'Hub digitale aperto per la cartografia geologica in Italia.

**Progetto a cura di [Geologiaintasca](https://www.geologiaintasca.it)**

Questo repository ospita il database geografico unificato (GeoJSON) delle risorse cartografiche geologiche italiane. L'obiettivo è aggregare in un'unica mappa interattiva i dati provenienti da istituzioni nazionali, enti regionali e ricerca accademica, facilitando la consultazione di risorse oggi distribuite su portali diversi.

[**🗺️ VAI ALLA MAPPA INTERATTIVA (uMap)**](https://umap.openstreetmap.fr/it/map/cartografia-geologica-italiana_1338725)

---

## 📂 Dataset Attuali

L'Hub integra attualmente tre livelli informativi complementari:

### 1. 🔵 Cartografia Ufficiale (Progetto CARG)
Il quadro d'unione completo della cartografia geologica ufficiale italiana alla scala 1:50.000.
*   **Contenuto:** Griglia di tutti i 652 fogli geologici previsti dal progetto CARG.
*   **Funzionalità:** Ogni poligono rimanda direttamente alla pagina ufficiale ISPRA per il download del foglio o la consultazione dei dati.
*   **Fonte Dati:** Elaborazione basata sui dati pubblici del Servizio Geologico d'Italia (ISPRA).

### 2. 🔴 Ricerca Scientifica (Journal of Maps)
Una selezione curata di oltre 130 pubblicazioni scientifiche tratte dal *Journal of Maps*.
*   **Contenuto:** Mappe di dettaglio, geomorfologia, rischi geologici e nuovi rilevamenti accademici che aggiornano o integrano la cartografia ufficiale.
*   **Fonte Dati:** Metadati estratti da Crossref/Taylor & Francis.

### 3. 🟢 Geoportali Regionali (Regional Gate)
Il punto di accesso diretto alla cartografia geologica di dettaglio (spesso 1:10.000) gestita dalle Regioni.
*   **Contenuto:** Quadro d'unione regionale.
*   **Funzionalità:** Cliccando sulla regione di interesse, si accede direttamente al Geoportale/WebGIS specifico regionale per consultare la cartografia vettoriale di dettaglio.
*   **Fonte Dati:** Selezione manuale dei migliori servizi cartografici regionali attivi.

---

## 🚀 Roadmap (Sviluppi futuri)
Il progetto è in continua evoluzione. I prossimi obiettivi includono:

- [ ] **Carta Geologica d'Italia 1:100.000 (Vecchia Serie):** Digitalizzazione del quadro d'unione della storica carta geologica nazionale (277 fogli), ancora essenziale nelle aree non coperte dal CARG.
- [ ] **Cartografia Geologica Marina:** Integrazione dei fogli geologici della piattaforma continentale (Progetto MaGIC/CARG Mare).
- [ ] **Miglioramento precisione:** Affinamento manuale dei poligoni delle pubblicazioni scientifiche (Journal of Maps) tramite community.

---

## ⚖️ Licenze e Disclaimer

Questo repository funge da **indice e aggregatore** di collegamenti a risorse esterne.

*   **Codice e Struttura Dati:** Il codice di questo repository e la struttura dei file GeoJSON sono rilasciati sotto licenza **MIT** (Open Source).
*   **Dati "CARG" e Regionali:** I riferimenti appartengono ai rispettivi Enti (ISPRA, Regioni). I dati sono trattati in conformità con la licenza **IODL 2.0 (Italian Open Data License)** ove applicabile.
*   **Dati "Journal of Maps":** I metadati sono di pubblico dominio. I contenuti linkati sono proprietà degli editori e degli autori.

*Geologiaintasca non è proprietaria dei dati cartografici linkati, ma fornisce esclusivamente il servizio di indicizzazione geografica.*

## 🤝 Contribuire
Il progetto è aperto alla comunità geologica italiana.
Hai una mappa da segnalare o vuoi proporre un nuovo livello informativo?
1.  Apri una **Issue** per discutere la proposta.
2.  Fai un **Fork** del repository e invia una Pull Request.
