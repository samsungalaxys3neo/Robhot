from collections import deque
import time

# Gestore per il gesto dinamico "waving"
class WaveGesture:
    def __init__(self, window=25, amp_thr=0.10, flips_thr=2, open_ratio=0.7, cooldown_s=3.0, waving_display_time=3.0):
        # Buffer per memorizzare posizioni e stati
        self.xbuf = deque(maxlen=window)  # buffer per posizioni x (orizzontale)
        self.openbuf = deque(maxlen=window)  # buffer per stati di mano aperta/chiusa    
        self.amp_thr = amp_thr  # soglia di ampiezza minima per considerare un movimento
        self.flips_thr = flips_thr  # soglia di numero minimo di inversioni di direzione per considerare un wave
        self.open_ratio = open_ratio  # soglia di percentuale minima di frame con mano aperta
        self.cooldown_s = cooldown_s  # tempo di cooldown tra un wave e l'altro (evitare spam di rilevamento)
        self.cooldown_until = 0.0  # timestamp fino a quando non si può rilevare un nuovo wave

        # cooldown separato per messaggio ciao
        self.waving_display_time = waving_display_time # durata minima per visualizzare ciao 
        self.waving_display_until = 0.0 # timestamp fino a quando mostrare ciao

    def _palm_center_x(self, lm):
        # Usando alcuni landmark, calcola la posizione orizzontale media del palmo 
        ids = [0, 5, 9, 13, 17]  # landmark per il centro del palmo
        return sum(lm.landmark[i].x for i in ids) / len(ids)
    
    def update (self, lm, open_palm):
        # Aggiunge posizione orizzontale e stato della mano aperta ai buffer
        cx = self._palm_center_x(lm)
        self.xbuf.append(cx)
        self.openbuf.append(open_palm)

        now = time.time()
        if now < self.cooldown_until:
            return False
        
        if now < self.waving_display_until:
            return True
        # se buffer non completo, impossibile fare analisi valida
        if len(self.xbuf) < self.xbuf.maxlen:
            return False
        
        # calcola ampiezza del movimento ( differenza tra posizione piu lontana e piu vicina)
        amp = max(self.xbuf) - min(self.xbuf)
        if amp < self.amp_thr:  # se ampiezza troppo piccola, non consideriamo il movimento
            return False
        
        # conta numero di inversioni direzione (movimento laterale alternato)
        flips = 0
        prev = self.xbuf[1] - self.xbuf[0]
        for i in range(2, len(self.xbuf)):
            dx = self.xbuf[i] - self.xbuf[i-1]
            if dx == 0:
                continue
            if prev == 0:
                prev = dx
                continue 
            if (dx > 0) != (prev > 0): # segno diverso indica inversione
                flips += 1
                prev = dx

        # se ci sono abbastanza inversioni di direzione (flips), e l'ampiezza è sufficiente, è un waving
        if flips >= self.flips_thr:
            self.cooldown_until = now + self.cooldown_s  # attiva cooldown
            self.waving_display_until = now + self.waving_display_time  # mostra ciao per un certo tempo
            return True
        
        return False
    
# gestore per tutti i gesti 
class GestureDetector:
    
    def __init__(self):
        self.wave = WaveGesture()  # istanza per monitorare il waving
        self.open_palm_buffer = deque(maxlen=10)  # buffer separato per monitorare solo la mano aperta

    def is_open_palm(self, hand_landmarks):  # hand_landmarks è una singola mano, non tutte
        # dentro hand_landmarks ci sono 21 punti (landmark) della mano
        tips = [8, 12, 16, 20]  # punta
        pips = [6, 10, 14, 18]  # snodo centrale

        extended = 0  # conta delle dita estese

        # Debug: Stampa i valori di y per le punte e gli snodi per ogni dito
        for tip, pip in zip(tips, pips):
            print(f"Dito {tip}: {hand_landmarks.landmark[tip].y} - Dito {pip}: {hand_landmarks.landmark[pip].y}")

            # Verifica se la punta del dito è sopra l'articolazione centrale
            if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
                extended += 1

        print(f"Dita estese: {extended}")  # Debug: Mostra quante dita sono estese

        return extended >= 4  # Se almeno 4 dita sono estese, considera la mano aperta
    
    def detect (self, lm):
        # Rilevamento per ogni gesto
        open_palm = self.is_open_palm(lm)  # controlla se mano aperta
        self.open_palm_buffer.append(open_palm)  # Memorizza lo stato della mano aperta
        waving = self.wave.update(lm, open_palm)  # controlla se waving

        # Se la mano è aperta per almeno il 70% dei frame negli ultimi 10 frame, la considera come "aperta"
        if sum(self.open_palm_buffer) >= 0.7 * len(self.open_palm_buffer):
            open_palm = True
        else:
            open_palm = False

        return {
            "open_palm": open_palm,
            "waving": waving
        }
