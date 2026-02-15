import time
import cv2
import platform
import argparse
import subprocess
import re
import os
import json
import csv
import sys

from hand_detector import HandDetector
from gesture_detector import GestureDetector
from camera import CameraUI

# Optional Arduino hook: if present, use it to send a 'W' when a wave is detected.
#try:
#    import arduino_controller as arduino_ctrl
#except Exception:
#    arduino_ctrl = None
arduino_ctrl = None

def emit_gesture(name: str):
    sys.stdout.write(f"EV GESTURE {name}\n")
    sys.stdout.flush()


def open_camera(preferred_index: int = 0):
    cap = None
    system = platform.system()

    if system == "Darwin":
        try:
            proc = subprocess.run(
                ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
                capture_output=True,
                text=True,
            )
            out = proc.stderr or proc.stdout or ""
            video_section = False
            devices = []
            for line in out.splitlines():
                if "AVFoundation video devices:" in line:
                    video_section = True
                    continue
                if video_section:
                    m = re.search(r"\[(\d+)\] (.+)", line)
                    if m:
                        idx = int(m.group(1))
                        name = m.group(2).strip()
                        devices.append((idx, name))
                    if "AVFoundation audio devices:" in line:
                        break

            prefer_keywords = ("FaceTime", "Built-in", "iSight", "Camera", "USB")
            exclude_keywords = ("iPhone", "Phone", "Android", "IPWebcam", "Raspi")

            chosen = None
            for idx, name in devices:
                nlower = name.lower()
                if any(k.lower() in nlower for k in exclude_keywords):
                    continue
                if any(k.lower() in nlower for k in prefer_keywords):
                    chosen = name
                    break

            if chosen:
                try:
                    cap = cv2.VideoCapture(chosen, cv2.CAP_AVFOUNDATION)
                    if cap is not None and cap.isOpened():
                        return cap, chosen
                except Exception:
                    cap = None

        except FileNotFoundError:
            pass
        except Exception:
            pass

        for i in range(0, 5):
            try:
                c = cv2.VideoCapture(i, cv2.CAP_AVFOUNDATION)
                if c is not None and c.isOpened():
                    return c, i
            except Exception:
                pass

    for i in range(0, 5):
        try:
            c = cv2.VideoCapture(i)
            if c is not None and c.isOpened():
                return c, i
        except Exception:
            continue

    return None, None


def main(cam_index: int | None = None, wave_permissive: bool = False):
    # Load persisted config (preferred camera index)
    cfg_path = os.path.expanduser("~/.gesture_control.json")
    cfg = {}
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}

    # If no cam_index provided, prefer saved config
    if cam_index is None and isinstance(cfg.get("cam_index"), int):
        cam_index = cfg.get("cam_index")

    if cam_index is None:
        cap, used_idx = open_camera(0)
    else:
        cap = cv2.VideoCapture(int(cam_index))
        used_idx = int(cam_index)

    if cap is None or not cap.isOpened():
        raise RuntimeError("Unable to open any camera")

    hd = HandDetector()
    gd = GestureDetector(wave_permissive=wave_permissive)
    ui = CameraUI()

    event_hold_s = 2.0
    last_event = ""
    last_event_ts = 0.0

    # Recording (toggle with 'p') - collects per-frame diagnostics while recording
    is_recording = False
    record_buffer = []
    record_start_ts = 0.0
    record_max_s = 5.0  # auto-stop after this many seconds
    record_dir = os.path.join(os.getcwd(), "wave_records")
    # Keep waves visible for a short window even if detection was a
    # single-frame spike. This prevents the "blink" effect where a
    # wave is detected but only shows up for a millisecond.
    wave_display_s = 0.8
    wave_display_expires = {}
    wave_display_payloads = {}
    # per-gesture cooldown to avoid spamming Arduino/LCD
    gesture_last_sent = {}
    gesture_send_cooldown = 1.0  # seconds

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        # Mirror horizontally (selfie-style) only. Use flipCode=1.
        frame = cv2.flip(frame, 1)
        ts = time.time()

        hp = hd.process(frame, ts)
        hands = [{"landmarks": h.landmarks, "handedness": h.handedness, "score": h.score} for h in hp.hands]

        events, per_hand, total = gd.process(hands, ts)

        for h in hands:
            if h["handedness"] in ("left", "right"):
                ui.draw_hand(frame, h["landmarks"], h["handedness"])

        priority = ["wave", "thumbs_up", "middle_finger", "peace", "open_palm", "yolo"]
        perhand_best = {}

        for side in ("right", "left"):
            if side not in per_hand:
                continue

            names = [ev.name for ev in events if ev.hand == side and ev.name != "count"]
            chosen = None
            for p in priority:
                if p in names:
                    chosen = p
                    break

            if not chosen:
                cnt = per_hand[side].count
                if cnt > 0:
                    chosen = f"{cnt} fingers"
                else:
                    chosen = "hand"

            perhand_best[side] = chosen.replace("_", " ")

        # Register any new wave events to keep them visible for a short
        # time window (wave_display_s) even if subsequent frames don't
        # re-fire the detector.
        if not hands:
            events = []
        else:

            for ev in events:
                # Keep wave HUD visible briefly
                if ev.name == "count":
                    continue    
                emit_gesture(ev.name) # chiamo la funzione per arduino per ogni gesto

                if ev.name == "wave":
                  wave_display_expires[ev.hand] = ts + wave_display_s
                  wave_display_payloads[ev.hand] = ev.payload

            # Send a message/command to Arduino for notable gestures (not 'count')
            
            #if arduino_ctrl is not None and ev.name != "count":
            #    last = gesture_last_sent.get(ev.name, 0.0)
            #    if ts - last >= gesture_send_cooldown:
            #        try:
            #            # send_gesture handles mapping and also triggers servo for 'wave'
            #            arduino_ctrl.send_gesture(ev.name, getattr(ev, 'payload', None))
            #           gesture_last_sent[ev.name] = ts
            #        except Exception as e:
            #            print(f"Failed to send Arduino gesture '{ev.name}': {e}")

        # Build a human-readable wave_info from any active wave displays
        wave_info = None
        for side, exp in list(wave_display_expires.items()):
            if ts <= exp and side in wave_display_payloads:
                p = wave_display_payloads[side]
                wave_info = f"{side} wave amp={p.get('amp_norm', 0):.3f} flips={p.get('flips', 0)} open={p.get('open_ratio', 0):.2f}"
                break
            else:
                # expired, clean up
                wave_display_expires.pop(side, None)
                wave_display_payloads.pop(side, None)

        combined = " | ".join([f"{side}: {perhand_best[side]}" for side in ("right", "left") if side in perhand_best])

        if wave_info:
            combined = (combined + " | " + wave_info) if combined else wave_info

    # If debug is on, append live wave statistics for each hand (amp/flips/open_ratio)
        if ui.debug:
            dbg_lines = []
            for side in ("right", "left"):
                if side in per_hand and getattr(per_hand[side], "wave_stats", None):
                    ws = per_hand[side].wave_stats
                    amp = ws.get("amp_norm", ws.get("amp_x", 0))
                    dbg_lines.append(f"{side} amp={amp:.3f} flips={ws['flips']} open={ws['open_ratio']:.2f}")
            if dbg_lines:
                dbg_txt = " | ".join(dbg_lines)
                combined = (combined + " | " + dbg_txt) if combined else dbg_txt

        if combined:
            last_event = combined
            last_event_ts = ts
        elif ts - last_event_ts > event_hold_s:
            last_event = ""

        # If currently recording, append per-hand diagnostics to buffer
        if is_recording:
            for side, ph in per_hand.items():
                ws = getattr(ph, "wave_stats", None) or {}
                record_buffer.append(
                    {
                        "ts": ts,
                        "side": side,
                        "states": getattr(ph, "states", None),
                        "count": getattr(ph, "count", None),
                        "amp_norm": ws.get("amp_norm", ws.get("amp_x", 0)),
                        "flips": ws.get("flips", 0),
                        "open_ratio": ws.get("open_ratio", 0),
                        "conf": ws.get("conf", 0),
                    }
                )

        # Show recording status in HUD
        hud_text = last_event
        if is_recording:
            hud_text = (hud_text + " | " if hud_text else "") + f"RECORDING ({len(record_buffer)} samples)"

        ui.draw_hud(frame, hud_text, total)

        cv2.imshow("gesture_detector", frame)
        k = cv2.waitKey(1) & 0xFF
        if k == 27 or k == ord("q"):
            break
        if k == ord("d"):
            ui.debug = not ui.debug
        if k == ord("p"):
            # Toggle recording mode: start/stop collecting per-frame diagnostics
            if not is_recording:
                is_recording = True
                record_buffer = []
                record_start_ts = ts
                print(f"Started recording diagnostics at {record_start_ts:.3f} (max {record_max_s}s). Press 'p' again to stop.")
            else:
                # Stop and dump buffer
                is_recording = False
                print(f"Stopped recording at {ts:.3f}. Collected {len(record_buffer)} samples.")
                if record_buffer:
                    # Print collected samples to terminal (human readable)
                    for rec in record_buffer:
                        print(f"{rec['ts']:.3f}\t{rec['side']}\tstates={rec['states']}\tcount={rec['count']}\tamp={rec['amp_norm']:.4f}\tflips={rec['flips']}\topen={rec['open_ratio']:.3f}\tconf={rec['conf']:.3f}")

                    # Save to CSV for easy sharing
                    try:
                        os.makedirs(record_dir, exist_ok=True)
                        fname = os.path.join(record_dir, f"wave_record_{int(record_start_ts)}.csv")
                        with open(fname, "w", newline="") as cf:
                            writer = csv.writer(cf)
                            writer.writerow(["ts", "side", "states", "count", "amp_norm", "flips", "open_ratio", "conf"])
                            for rec in record_buffer:
                                writer.writerow([
                                    f"{rec['ts']:.6f}",
                                    rec["side"],
                                    str(rec["states"]),
                                    rec["count"],
                                    f"{rec['amp_norm']:.6f}",
                                    rec["flips"],
                                    f"{rec['open_ratio']:.6f}",
                                    f"{rec['conf']:.6f}",
                                ])
                        print(f"Saved recording to {fname}")
                    except Exception as e:
                        print(f"Failed to save recording: {e}")

        # Auto-stop recording when exceeding max duration
        if is_recording and (ts - record_start_ts) > record_max_s:
            is_recording = False
            print(f"Auto-stopped recording after {record_max_s}s. Collected {len(record_buffer)} samples.")
            if record_buffer:
                try:
                    os.makedirs(record_dir, exist_ok=True)
                    fname = os.path.join(record_dir, f"wave_record_{int(record_start_ts)}.csv")
                    with open(fname, "w", newline="") as cf:
                        writer = csv.writer(cf)
                        writer.writerow(["ts", "side", "states", "count", "amp_norm", "flips", "open_ratio", "conf"])
                        for rec in record_buffer:
                            writer.writerow([
                                f"{rec['ts']:.6f}",
                                rec["side"],
                                str(rec["states"]),
                                rec["count"],
                                f"{rec['amp_norm']:.6f}",
                                rec["flips"],
                                f"{rec['open_ratio']:.6f}",
                                f"{rec['conf']:.6f}",
                            ])
                    print(f"Saved recording to {fname}")
                except Exception as e:
                    print(f"Failed to save recording: {e}")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gesture detector")
    parser.add_argument("--cam", type=int, default=None, help="Camera index to use (default: auto-detect built-in)")
    parser.add_argument("--save-cam", action="store_true", help="Save the chosen --cam index to ~/.gesture_control.json for future runs")
    parser.add_argument("--wave-permissive", action="store_true", help="Enable very permissive wave detection (more sensitive)")
    args = parser.parse_args()
    # If user passed --save-cam together with --cam, persist it
    if args.save_cam and args.cam is not None:
        cfg_path = os.path.expanduser("~/.gesture_control.json")
        try:
            with open(cfg_path, "w") as f:
                json.dump({"cam_index": int(args.cam)}, f)
            print(f"Saved preferred camera index {args.cam} to {cfg_path}")
        except Exception as e:
            print(f"Failed to save config: {e}")

    main(args.cam, wave_permissive=args.wave_permissive)
