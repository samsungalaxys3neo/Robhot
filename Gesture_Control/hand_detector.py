from dataclasses import dataclass
from typing import Any, List, Optional, Tuple
import cv2
import mediapipe as mp

Vec2 = Tuple[float, float]

@dataclass
class HandObs:
    landmarks: List[Vec2]
    handedness: str
    score: float

@dataclass
class HandsPacket:
    hands: List[HandObs]
    ts: float
    frame_bgr: Any

class HandDetector:
    def __init__(
        self,
        max_num_hands: int = 2,
        model_complexity: int = 1,
        min_detection_confidence: float = 0.6,
        min_tracking_confidence: float = 0.6,
    ):
        self._mp_hands = mp.solutions.hands
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    def process(self, frame_bgr: Any, ts: float) -> HandsPacket:
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        res = self._hands.process(frame_rgb)

        hands: List[HandObs] = []
        if res.multi_hand_landmarks:
            for i, lmset in enumerate(res.multi_hand_landmarks):
                lms: List[Vec2] = [(lm.x, lm.y) for lm in lmset.landmark]
                handed = "unknown"
                score = 0.0
                if res.multi_handedness and i < len(res.multi_handedness):
                    cls = res.multi_handedness[i].classification[0]
                    handed = cls.label.lower()
                    score = float(cls.score)
                hands.append(HandObs(landmarks=lms, handedness=handed, score=score))

        return HandsPacket(hands=hands, ts=ts, frame_bgr=frame_bgr)
