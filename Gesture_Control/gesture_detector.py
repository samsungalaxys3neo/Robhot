from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional

from gestures import GestureEvent, WaveTracker, finger_states, count_fingers, is_open_palm, is_yolo_shaka, is_peace, dist

Vec2 = Tuple[float, float]


@dataclass
class PerHandResult:
    handedness: str
    score: float
    states: Dict[str, bool]
    count: int
    center: Vec2
    wave_stats: Optional[Dict[str, float]] = None


class GestureDetector:
    def __init__(self, wave_permissive: bool = False):
        # Use normalized WaveTracker for both hands. Keep detection stable
        # and debuggable by using a single, scale-normalized tracker.
        self._wave = {"left": WaveTracker(), "right": WaveTracker()}

    def _center(self, lms: List[Vec2]) -> Vec2:
        sx = 0.0
        sy = 0.0
        for x, y in lms:
            sx += x
            sy += y
        n = float(len(lms)) if lms else 1.0
        return (sx / n, sy / n)

    def _thumbs_up(self, lms: List[Vec2], states: Dict[str, bool]) -> bool:
        if len(lms) < 21:
            return False
        wrist = lms[0]
        thumb_tip = lms[4]
        thumb_ip = lms[3]
        thumb_vertical = (thumb_tip[1] < thumb_ip[1]) and (thumb_tip[1] < wrist[1])
        others_down = (not states["index"]) and (not states["middle"]) and (not states["ring"]) and (not states["pinky"])
        return bool(states["thumb"] and thumb_vertical and others_down)

    

    def _middle_finger(self, states: Dict[str, bool]) -> bool:
        # Recognize middle finger gesture when the middle finger is extended
        # and index/ring/pinky are not extended. Allow the thumb to be either
        # extended or not (user may show middle + thumb).
        return states["middle"] and (not states["index"]) and (not states["ring"]) and (not states["pinky"])

    def process(self, hands: List[Dict[str, Any]], ts: float) -> Tuple[List[GestureEvent], Dict[str, PerHandResult], int]:
        per_hand: Dict[str, PerHandResult] = {}
        events: List[GestureEvent] = []

        for h in hands:
            lms: List[Vec2] = h["landmarks"]
            handed = h["handedness"]
            score = float(h["score"])
            if handed not in ("left", "right"):
                continue

            states = finger_states(lms, handed)
            cnt = count_fingers(states)
            center = self._center(lms)

            per_hand[handed] = PerHandResult(
                handedness=handed,
                score=score,
                states=states,
                count=cnt,
                center=center,
            )

            if is_open_palm(states):
                events.append(GestureEvent(name="open_palm", hand=handed, confidence=score, ts=ts, payload={"count": cnt}))

            if self._thumbs_up(lms, states):
                events.append(GestureEvent(name="thumbs_up", hand=handed, confidence=score, ts=ts, payload={}))

            if self._middle_finger(states):
                events.append(GestureEvent(name="middle_finger", hand=handed, confidence=score, ts=ts, payload={}))

            if is_yolo_shaka(states):
                events.append(GestureEvent(name="yolo", hand=handed, confidence=score, ts=ts, payload={"style": "shaka"}))

            # peace gesture (index + middle)
            if is_peace(states):
                events.append(GestureEvent(name="peace", hand=handed, confidence=score, ts=ts, payload={}))

            # For wave detection we require the hand to be mostly open, but
            # allow 4 or 5 fingers (some people keep the thumb slightly in).
            open_palm = (cnt >= 4)
            # Prefer palm center (landmark 9) as x source; it's more stable
            # than the wrist or the centroid of all points.
            wrist = lms[0] if len(lms) > 0 else center
            palm = lms[9] if len(lms) > 9 else wrist
            palm_scale = dist(wrist, palm)

            fired, amp_norm, flips, open_ratio, conf = self._wave[handed].update(
                x=palm[0], is_open=open_palm, palm_scale=palm_scale, ts=ts
            )
            # attach normalized wave stats to per-hand result for debug/inspection
            per_hand[handed].wave_stats = {"amp_norm": amp_norm, "flips": flips, "open_ratio": open_ratio, "conf": conf}
            # Lightweight debug: print when there is notable motion or flips
            if (flips > 0) or (amp_norm >= 0.15):
                print(f"[WAVE_DBG] ts={ts:.2f} hand={handed} amp={amp_norm:.3f} flips={flips} open_ratio={open_ratio:.2f} fired={fired}")

            if fired:
                events.append(
                    GestureEvent(
                        name="wave",
                        hand=handed,
                        confidence=conf,
                        ts=ts,
                        payload={"amp_norm": amp_norm, "flips": flips, "open_ratio": open_ratio},
                    )
                )

        left_cnt = per_hand["left"].count if "left" in per_hand else 0
        right_cnt = per_hand["right"].count if "right" in per_hand else 0
        total = left_cnt + right_cnt
        if total > 10:
            total = 10

        hands_tag = "both" if ("left" in per_hand and "right" in per_hand) else ("left" if "left" in per_hand else ("right" if "right" in per_hand else "none"))
        conf_count = 1.0 if hands_tag != "none" else 0.0

        events.append(
            GestureEvent(
                name="count",
                hand=hands_tag,
                confidence=conf_count,
                ts=ts,
                payload={"left": left_cnt, "right": right_cnt, "total": total},
            )
        )

        return events, per_hand, total
