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
        window: int = 14,
        # Lowered amp_thr because some users exhibit smaller lateral
        # movements; this value works better for recorded samples where
        # amp_x is often in the ~0.01-0.03 range.
        amp_thr: float = 0.012,
        flips_thr: int = 1,
    min_dx: float = 0.002,
        open_ratio: float = 0.45,
        cooldown_s: float = 0.8,
        smooth_k: float = 0.20,
        # Relax horizontal dominance so modest vertical motion doesn't
        # block wave detection on users who move more up/down while
        # waving.
        horiz_vert_ratio: float = 0.7,
    ):
        self.window = window
        self.amp_thr = amp_thr
        self.flips_thr = flips_thr
        self.min_dx = min_dx
        self.open_ratio = open_ratio
        self.cooldown_s = cooldown_s
        self.smooth_k = smooth_k
        self.horiz_vert_ratio = horiz_vert_ratio

        self.xbuf = deque(maxlen=window)
        self.ybuf = deque(maxlen=window)
        self.openbuf = deque(maxlen=window)
        self._x_smooth = None
        self._y_smooth = None
        self.cooldown_until = 0.0

    def _dir_flips(self, xs: List[float]) -> int:
        """Count direction flips in the x-buffer.

        Uses a small epsilon derived from min_dx to ignore micro-jitter but
        remains sensitive to real direction changes. Returns number of sign
        changes (a single back-and-forth produces 1 flip).
        """
        if len(xs) < 3:
            return 0
        flips = 0
        last_sign = 0
        eps = max(self.min_dx * 0.2, 1e-6)
        for i in range(1, len(xs)):
            dx = xs[i] - xs[i - 1]
            if abs(dx) < eps:
                sign = 0
            else:
                sign = 1 if dx > 0 else -1
            if sign == 0:
                continue
            if last_sign != 0 and sign != last_sign:
                flips += 1
            last_sign = sign
        return flips

    def update(self, center_x: float, center_y: float, is_open: bool, ts: float) -> Tuple[bool, float, float, int, float, float]:
        if ts < self.cooldown_until:
            return (False, 0.0, 0.0, 0, 0.0, 0.0)

        if self._x_smooth is None:
            self._x_smooth = center_x
        else:
            self._x_smooth = (1.0 - self.smooth_k) * self._x_smooth + self.smooth_k * center_x

        if self._y_smooth is None:
            self._y_smooth = center_y
        else:
            self._y_smooth = (1.0 - self.smooth_k) * self._y_smooth + self.smooth_k * center_y

        self.xbuf.append(self._x_smooth)
        self.ybuf.append(self._y_smooth)
        self.openbuf.append(1 if is_open else 0)

        if len(self.xbuf) < self.window:
            return (False, 0.0, 0.0, 0, 0.0, 0.0)

        xs = list(self.xbuf)
        ys = list(self.ybuf)
        amp_x = max(xs) - min(xs)
        amp_y = max(ys) - min(ys)
        flips = self._dir_flips(xs)
        open_ratio = sum(self.openbuf) / float(len(self.openbuf))
        conf = _clamp01(0.55 + 0.45 * min(1.0, amp_x / (self.amp_thr * 1.5)))

        # require that horizontal amplitude dominates vertical movement to
        # avoid false positives when the hand is raised vertically
        horiz_dominant = (amp_x >= (amp_y * self.horiz_vert_ratio))

        # Primary: horizontal amplitude threshold and horizontal dominance.
        # Do NOT require flips here so we can be permissive; flips will be
        # used in downstream checks but should not block detection entirely.
        primary = (amp_x >= self.amp_thr) and horiz_dominant

        ok = False
        # Strong case: require flips and open hand ratio (conservative)
        if (flips >= self.flips_thr) and (open_ratio >= self.open_ratio) and primary:
            ok = True
        else:
            # Very permissive cases: allow wave even with few/no flips when
            # amplitude is clearly above threshold or the hand is fairly open.
            # These rules are ordered by preference to avoid firing on small jitter.
            if primary:
                # Case A: amplitude well above threshold (clear lateral motion)
                if amp_x >= (self.amp_thr * 1.2):
                    ok = True
                # Case B: at least one flip and some openness
                elif flips >= 1 and open_ratio >= max(0.2, self.open_ratio * 0.5):
                    ok = True
                # Case C: hand reasonably open even if flips are 0
                elif open_ratio >= max(0.35, self.open_ratio * 0.6):
                    ok = True
                # Case D: very small amplitude but many flips (fast tiny wave)
                elif flips >= (self.flips_thr + 1) and amp_x >= (self.amp_thr * 0.6):
                    ok = True

        if ok:
            self.xbuf.clear()
            self.ybuf.clear()
            self.openbuf.clear()
            self.cooldown_until = ts + self.cooldown_s
            return (True, amp_x, amp_y, flips, open_ratio, conf)

        return (False, amp_x, amp_y, flips, open_ratio, conf)
