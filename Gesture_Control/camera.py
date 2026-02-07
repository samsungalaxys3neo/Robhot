from typing import Any, Dict, List, Tuple
import cv2
from gestures import to_px

Vec2 = Tuple[float, float]

class CameraUI:
    def __init__(self):
        self.debug = True

    def draw_hand(self, frame: Any, lms: List[Vec2], handedness: str) -> None:
        h, w = frame.shape[:2]
        # Colors in BGR: left = pink, right = dark purple
        if handedness == "left":
            color = (180, 105, 255)  # pink-ish (B,G,R)
        else:
            color = (128, 0, 128)  # dark purple
            
        for x, y in lms:
            cx, cy = to_px((x, y), w, h)
            cv2.circle(frame, (cx, cy), 3, color, -1)

        key_ids = [0, 4, 8, 12, 16, 20]
        for idx in key_ids:
            if idx < len(lms):
                cx, cy = to_px(lms[idx], w, h)
                cv2.circle(frame, (cx, cy), 6, color, 2)

        if self.debug:
            lines = []
            labels = {0: "W", 4: "T", 8: "I", 12: "M", 16: "R", 20: "P"}
            for idx in key_ids:
                if idx < len(lms):
                    cx, cy = to_px(lms[idx], w, h)
                    lines.append(f"{labels[idx]}({cx},{cy})")
            txt = " ".join(lines)
            y0 = 25 if handedness == "left" else 50
            # draw a filled rectangle behind the text for visibility
            txt_full = f"{handedness.upper()} {txt}"
            (tw, th), _ = cv2.getTextSize(txt_full, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
            cv2.rectangle(frame, (8, y0 - th - 6), (12 + tw, y0 + 6), (0, 0, 0), -1)
            cv2.putText(frame, txt_full, (10, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

    def draw_hud(self, frame: Any, last_event: str, count_total: int) -> None:
        # Draw a dark translucent panel for HUD background (approximate by filled rect)
        hud_x, hud_y = 8, 68
        hud_w, hud_h = 300, 90
        cv2.rectangle(frame, (hud_x, hud_y), (hud_x + hud_w, hud_y + hud_h), (0, 0, 0), -1)
        # Count (use bright yellow)
        cv2.putText(frame, f"count={count_total}", (10, 92), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 215, 255), 2)
        # Last event (bright cyan)
        if last_event:
            cv2.putText(frame, last_event, (10, 122), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (200, 255, 255), 2)
        # Debug status (white)
        cv2.putText(frame, f"debug={'ON' if self.debug else 'OFF'} (press D)", (10, 152), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (230, 230, 230), 2)
