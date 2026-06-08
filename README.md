# Grafix

Grafix è una piccola applicazione desktop di geometria e grafici di funzioni, scritta in Python con interfaccia **Tkinter** e disegno tramite **matplotlib**. L'idea è una versione minimale di programmi come GeoGebra: si possono disegnare punti, segmenti, rette e cerchi sul piano cartesiano, tracciare funzioni ed equazioni, e fare alcune costruzioni geometriche (punto medio, intersezioni, distanze).

È un progetto realizzato come lavoro di fine anno scolastico, interamente da solo.

---

## Come si avvia

Serve **Python 3.10+** e queste librerie:

```
pip install numpy matplotlib
```

(`tkinter` è incluso in quasi tutte le installazioni di Python su Windows; su Linux può servire `sudo apt install python3-tk`.)

Per lanciare il programma:

```
python main.py
```

---

## Com'è organizzato il codice

Il progetto è diviso in cinque file, ognuno con un compito preciso:

- **`main.py`** — punto di ingresso: crea la finestra Tkinter e avvia l'app.
- **`app.py`** — il cuore del programma. Costruisce l'interfaccia, tiene la lista degli oggetti (punti, rette, cerchi, funzioni, curve implicite), interpreta i comandi scritti nella casella delle formule e contiene tutta la "matematica" (intersezioni, distanze, ricerca degli zeri, calcolatrice).
- **`graph_canvas.py`** — gestisce il piano cartesiano: disegno degli oggetti, zoom e spostamento della vista (pan), e tutta la parte di clic del mouse (selezione, creazione di punti/segmenti/rette/cerchi, menu di scelta quando più oggetti sono vicini).
- **`models.py`** — le classi che rappresentano gli oggetti: `Point`, `Line`, `Circle`, `FunctionPlot`, `ImplicitPlot`. Qui c'è anche l'ambiente "sicuro" con le funzioni matematiche ammesse (`sin`, `cos`, `sqrt`, `log`...).
- **`utils.py`** — `ExpressionHelper`, cioè il traduttore delle formule: trasforma quello che scrivi tu (es. `2x^2`, `√x`, `log2(x)`) in qualcosa che Python può calcolare.

---

## Come funziona, a grandi linee

### La barra in alto (modalità di disegno)
Ogni pulsante attiva una "modalità" e i clic sul grafico cambiano significato di conseguenza:

- **Muovi** — sposta la vista trascinando, e seleziona gli oggetti.
- **Nuovo punto / segmento / retta / cerchio** — crea l'oggetto cliccando sul piano.
- **Punto medio** — calcola il punto medio di un segmento.
- **Intersezione** — trova i punti di incontro tra due oggetti.
- **Distanza** — misura la distanza tra due oggetti.

Ci sono poi i pulsanti per cambiare colore all'oggetto selezionato, tornare alla vista iniziale ed eliminare l'oggetto scelto.

### La casella delle formule
A sinistra puoi scrivere direttamente comandi e equazioni. Il programma capisce da solo di che tipo si tratta:

| Cosa scrivi | Cosa ottieni |
|---|---|
| `A(1,2)` o `A=(1,2)` | un punto chiamato A |
| `line(A,B)` o `retta(A,B)` | la retta per due punti già esistenti |
| `circle(cx,cy,r)` | un cerchio da centro e raggio |
| `y = 2x+3`, `y = sin(x)` | una funzione esplicita |
| `x^2 + y^2 = 9` | un cerchio (riconosciuto in forma canonica) |
| `x^2/4 + y^2/9 = 1` | un'ellisse / curva implicita |
| equazioni generiche con `=` | una curva implicita F(x,y)=0 |

Il traduttore delle formule (`ExpressionHelper`) gestisce diverse comodità: `^` come potenza, le moltiplicazioni implicite (`2x` → `2*x`), la radice anche senza parentesi (`sqrt4`), il simbolo `√`, e i logaritmi in base qualsiasi (`log2(x)`, `log10(x)`).

### Il motore matematico
- **Intersezioni**: retta–retta, retta–cerchio e cerchio–cerchio sono risolte in forma chiusa; le intersezioni che coinvolgono funzioni o curve implicite sono trovate numericamente, cercando gli zeri con un metodo robusto (bracketing alla Brent + Newton smorzato come ripiego) e, per le implicite, campionando il piano a "marching squares".
- **Distanza**: tra punti, punto–retta (con gestione corretta dei segmenti), punto/retta–cerchio, cerchio–cerchio, e tra rette parallele. Vengono trattate come rette anche le funzioni di primo grado (`y = mx + q`) e le equazioni implicite lineari, riconoscendole automaticamente.
- **Calcolatrice**: in basso a sinistra valuta espressioni numeriche con le stesse funzioni matematiche del resto del programma.

---

## Limiti noti e possibili bug

Il programma è stato sviluppato da solo, quindi non tutto ha potuto essere curato o testato al massimo. Alcune cose da tenere a mente:

- **La distanza funziona solo tra oggetti "lineari" o cerchi.** La distanza tra due curve qualsiasi (es. una parabola e un cerchio) non è gestita: in quei casi il programma risponde che la coppia non è supportata.
- **Le intersezioni con funzioni/curve implicite sono numeriche**, quindi approssimate: in casi limite (tangenze, asintoti, curve molto fitte o molto "ripide") qualche soluzione può sfuggire o, più raramente, comparirne una spuria.
- **Il traduttore delle formule usa delle euristiche** (soprattutto per le moltiplicazioni implicite): espressioni scritte in modo insolito potrebbero essere interpretate diversamente da come ti aspetti. In caso di dubbio, conviene usare le parentesi.
- **Prestazioni**: con molte curve sullo schermo e zoom ampi il ridisegno può rallentare un po', perché alcune cose vengono ricampionate ad ogni aggiornamento.
- Possono esserci altri bug non ancora scoperti.

Se incontri un problema, **segnalalo**: ogni segnalazione aiuta a migliorare il programma.

---

## Segnalazione bug e contatti

- **Email:** barbierigiulio8@gmail.com
- **Telegram:** [@itsmegiulioxx](https://t.me/itsmegiulioxx)

Quando segnali un bug, se puoi, indica cosa stavi facendo, cosa hai scritto/cliccato e cosa è successo (un eventuale messaggio di errore copiato dalla console è oro).

---

