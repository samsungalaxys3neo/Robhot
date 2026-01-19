# Questo file usa mediapipe per analizzare un frame e trovare le mani

import cv2 # per conversione colore
import mediapipe as mp # per il rilevamento mani

class HandTracker:
    def __init__(self):
        self.mp_hands = mp.solutions.hands # modulo mani
        self.mp_draw = mp.solutions.drawing_utils # modulo disegno dei landmark sul frame

        self.hands = self.mp_hands.Hands(
            static_image_mode = False, # video, no immagini statiche
            max_num_hands = 2, # massimo 2 mani

            ### parametri da settare (controlla)
            model_complexity = 1, # complessità del modello
            min_detection_confidence = 0.6, # soglia di rilevamento
            min_tracking_confidence = 0.6  # soglia di confidenza per il tracking
        )

    def process(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) # converte BGR a RGB
        return self.hands.process(rgb) # processa il frame e ritorna i risultati
    
    def draw(self, frame, results):
        if results.multi_hand_landmarks: # se mediapipe ha trovato almeno una mano
            for hand_landmarks in results.multi_hand_landmarks: # per ogni mano trovata
                self.mp_draw.draw_landmarks(
                    frame, # il frame su cui disegnare
                    hand_landmarks, # i landmark della mano
                    self.mp_hands.HAND_CONNECTIONS, # le connessioni tra i landmark
                    landmark_drawing_spec = self.mp_draw.DrawingSpec(
                        color = (255, 105, 180), # rosa BGR
                        thickness = 3, # spessore linee
                        circle_radius = 6 # raggio cerchi landmark
                    ),
                    connection_drawing_spec = self.mp_draw.DrawingSpec(
                        color = (255, 51 , 153), # rosa BGR
                        thickness = 2, # spessore linee
                    )
                )
    def close(self): 
        self.hands.close() # rilascia le risorse del modello mediapipe