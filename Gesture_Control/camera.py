# Driving della webcam
# Serve ad isolare la parte di: apertura webcam, lettura frame, mirror, chiusura webcam
# Espone una classe con 3 elementi:
# - init: apre la webcam
# - read_frame: legge un frame e lo specchia
# - release: chiude la webcam

import cv2
class Camera:
    def __init__(self, device = 0): # device = 0 è il primo device disponibile
        self.cap = cv2.VideoCapture(device, cv2.CAP_AVFOUNDATION)   
    # cap_avfoundation è il giusto backend per MacOS.

        if not self.cap.isOpened():
            raise RuntimeError("Impossibile aprire la webcam!")
    # Controlla se la webcam è stata aperta correttamente.

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        frame = cv2.flip(frame, 1)
        return frame # ritorna il frame con matrice numpy (HxWx3)
    # Legge un frame dalla webcam, lo specchia orizzontalmente e lo restit

    def release(self):
        self.cap.release()
    # Rilascia la risorsa della webcam  



