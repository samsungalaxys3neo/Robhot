from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional

from gestures import GestureEvent, WaveTracker, finger_states, count_fingers, is_open_palm, is_yolo_shaka, is_peace

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
        # If wave_permissive is True use much more permissive WaveTracker params
        if wave_permissive:
            wp = {
                "window": 10,
                # Make the permissive preset match your recorded magnitudes.
                # Lower amp_thr so small lateral motions count as waves.
                "amp_thr": 0.012,
                "flips_thr": 0,
                "min_dx": 0.0008,
                "open_ratio": 0.20,
                "cooldown_s": 0.4,
                "smooth_k": 0.12,
                # Allow vertical component to be larger without blocking.
                "horiz_vert_ratio": 0.6,
            }
            self._wave = {"left": WaveTracker(**wp), "right": WaveTracker(**wp)}
        else:
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

            open_palm = is_open_palm(states)
            # prefer wrist x/y for lateral movement detection (more stable than center)
            wrist_x = lms[0][0] if len(lms) > 0 else center[0]
            wrist_y = lms[0][1] if len(lms) > 0 else center[1]
            fired, amp_x, amp_y, flips, open_ratio, conf = self._wave[handed].update(wrist_x, wrist_y, open_palm, ts)
            # attach live wave stats to per-hand result for debug/inspection
            per_hand[handed].wave_stats = {"amp_x": amp_x, "amp_y": amp_y, "flips": flips, "open_ratio": open_ratio, "conf": conf}
            if fired:
                events.append(GestureEvent(name="wave", hand=handed, confidence=conf, ts=ts, payload={"amp_x": amp_x, "amp_y": amp_y, "flips": flips, "open_ratio": open_ratio}))

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
