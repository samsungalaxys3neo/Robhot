# File che collega tutto, fa il loop e mostra il video 

import cv2
from Gesture_Control.camera import Camera # importa la classe camera (camera.py)
from Gesture_Control.hand_tracking import HandTracker # importa la classe hand tracker (hand_tracking.py)
from Gesture_Control.gesture import GestureDetector # importa la classe gesture detector (gesture.py)

# Crea oggetto webcam 
cam = Camera()

# crea oggetto hand tracker
tracker = HandTracker()

# crea oggetto gesture detector
detector = GestureDetector()

# Loop principale (stream video continuo)
while True:
    frame = cam.get_frame()
    # ottiene un frame dalla webcam 

    # se il frame non è valido, salta il ciclo:
    if frame is None:
        continue

    # processa il frame per trovare le mani
    results = tracker.process(frame)

    open_palm = False
    waving = False

    if results.multi_hand_landmarks:
        # se vengono trovate mani, controlla gesti
        gestures = detector.detect(results.multi_hand_landmarks[0])

        open_palm = gestures["open_palm"]
        waving = gestures["waving"]

       # DEBUGGING: Stampa per capire lo stato della mano aperta
        print(f"Open Palm: {open_palm}")

    if waving:
        print("Rilevato waving, mostro CIAO!")
        cv2.putText(frame, "CIAO!", (30, 150), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255,255), 3)

    elif open_palm:
        print("Rilevato palmo aperto, mostro STOP!") 
        cv2.putText(frame, "STOP!", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255,255), 3)

    tracker.draw(frame, results)
    # disegna i landmark delle mani sul frame

    cv2.imshow("Robhot", frame) # mostra il frame a schermo

    # controlla se l'utente ha premuto 'q' per uscire
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# rilascia le risorse
cam.release()
# chiude mediapipe
tracker.close()
# chiude tutte le finestre aperte OpenCV
cv2.destroyAllWindows()