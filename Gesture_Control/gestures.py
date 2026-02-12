from dataclasses import dataclass
from collections import deque
from typing import Any, Dict, List, Tuple
import math

Vec2 = Tuple[float, float]

@dataclass
class GestureEvent:
    name: str
    hand: str
    confidence: float
    ts: float
    payload: Dict[str, Any]

def dist(a: Vec2, b: Vec2) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])

def to_px(p: Vec2, w: int, h: int) -> Tuple[int, int]:
    return (int(p[0] * w), int(p[1] * h))

def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)

def finger_states(lms: List[Vec2], handedness: str) -> Dict[str, bool]:
    if len(lms) < 21:
        return {"thumb": False, "index": False, "middle": False, "ring": False, "pinky": False}

    wrist = lms[0]

    thumb_tip, thumb_ip, thumb_mcp = lms[4], lms[3], lms[2]
    index_tip, index_pip = lms[8], lms[6]
    middle_tip, middle_pip = lms[12], lms[10]
    ring_tip, ring_pip = lms[16], lms[14]
    pinky_tip, pinky_pip = lms[20], lms[18]

    palm_scale = dist(wrist, lms[9])
    if palm_scale < 1e-6:
        palm_scale = 0.1

    m = 0.08 * palm_scale

    idx = dist(wrist, index_tip) > dist(wrist, index_pip) + m
    mid = dist(wrist, middle_tip) > dist(wrist, middle_pip) + m
    rng = dist(wrist, ring_tip) > dist(wrist, ring_pip) + m
    pky = dist(wrist, pinky_tip) > dist(wrist, pinky_pip) + m

    thb = dist(wrist, thumb_tip) > dist(wrist, thumb_mcp) + (0.06 * palm_scale)
    if handedness in ("left", "right"):
        th_dir = (thumb_tip[0] > thumb_ip[0]) if handedness == "left" else (thumb_tip[0] < thumb_ip[0])
        thb = thb and th_dir

    return {"thumb": thb, "index": idx, "middle": mid, "ring": rng, "pinky": pky}

def count_fingers(states: Dict[str, bool]) -> int:
    return int(states["thumb"]) + int(states["index"]) + int(states["middle"]) + int(states["ring"]) + int(states["pinky"])

def is_open_palm(states: Dict[str, bool]) -> bool:
    return states["thumb"] and states["index"] and states["middle"] and states["ring"] and states["pinky"]

def is_yolo_shaka(states: Dict[str, bool]) -> bool:
    return states["thumb"] and (not states["index"]) and (not states["middle"]) and (not states["ring"]) and states["pinky"]


def is_peace(states: Dict[str, bool]) -> bool:
    """Detect 'peace' gesture: index and middle extended, ring and pinky down.

    The thumb is allowed to be either extended or not (some people hold the
    thumb up while showing the peace sign). We therefore only require index
    and middle to be True and ring/pinky to be False.
    """
    return states.get("index", False) and states.get("middle", False) and (not states.get("ring", False)) and (not states.get("pinky", False))

class WaveTracker:
    def __init__(
        self,
        window: int = 12,
        amp_thr_norm: float = 0.18,
        flips_thr: int = 2,
        min_dx_norm: float = 0.02,
        open_ratio: float = 0.55,
        cooldown_s: float = 1.0,
        smooth_k: float = 0.20,
    ):
        self.window = window
        self.amp_thr_norm = amp_thr_norm
        self.flips_thr = flips_thr
        self.min_dx_norm = min_dx_norm
        self.open_ratio = open_ratio
        self.cooldown_s = cooldown_s
        self.smooth_k = smooth_k

        self.xbuf = deque(maxlen=window)
        self.openbuf = deque(maxlen=window)
        self.cooldown_until = 0.0
        self._x_smooth = None

    def _crossings(self, xs: List[float], deadband: float) -> int:
        """
        Count robust centerline crossings with hysteresis (deadband).
        This detects macro oscillations (go-and-return) even when per-frame
        dx is small after smoothing.
        """
        if len(xs) < 4:
            return 0
        mid = (max(xs) + min(xs)) * 0.5
        crossings = 0
        state = 0
        for x in xs:
            if x > mid + deadband:
                new_state = 1
            elif x < mid - deadband:
                new_state = -1
            else:
                new_state = state
            if state != 0 and new_state != 0 and new_state != state:
                crossings += 1
            state = new_state
        return crossings

    def update(self, x: float, is_open: bool, palm_scale: float, ts: float):
        if ts < self.cooldown_until:
            return (False, 0.0, 0, 0.0, 0.0)

        ps = palm_scale if palm_scale > 1e-6 else 0.1

        # deadband around centerline (scaled by palm size)
        deadband = (self.min_dx_norm * ps) * 1.2

        if self._x_smooth is None:
            self._x_smooth = x
        else:
            self._x_smooth = (1.0 - self.smooth_k) * self._x_smooth + self.smooth_k * x

        self.xbuf.append(self._x_smooth)
        self.openbuf.append(1 if is_open else 0)

        if len(self.xbuf) < self.window:
            return (False, 0.0, 0, 0.0, 0.0)

        xs = list(self.xbuf)
        amp = max(xs) - min(xs)
        amp_norm = amp / ps

        # robust crossings-based flips count
        flips = self._crossings(xs, deadband=deadband)

        open_ratio = sum(self.openbuf) / float(len(self.openbuf))
        conf = _clamp01(0.55 + 0.45 * min(1.0, amp_norm / (self.amp_thr_norm * 1.5)))

        # Primary strict condition: require sufficient amplitude, crossings and open hand
        ok_primary = (amp_norm >= self.amp_thr_norm) and (flips >= self.flips_thr) and (open_ratio >= self.open_ratio)

        # Secondary (fallback) scoring: if amplitude and crossings together are convincing,
        # allow firing even if flips < flips_thr. This helps when smoothing reduces frame-to-frame
        # direction changes but the macro-oscillation is clear.
        amp_score = amp_norm / max(1e-6, self.amp_thr_norm)
        flips_score = min(flips / max(1, self.flips_thr), 3.0)
        combined_score = 0.6 * amp_score + 0.4 * flips_score
        ok_fallback = (combined_score >= 1.2) and (open_ratio >= self.open_ratio)

        ok = ok_primary or ok_fallback
        if ok:
            self.xbuf.clear()
            self.openbuf.clear()
            self.cooldown_until = ts + self.cooldown_s
            return (True, amp_norm, flips, open_ratio, conf)

        return (False, amp_norm, flips, open_ratio, conf)
