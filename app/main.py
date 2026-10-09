"""CloseCall: Tesla-style eyes for people on bikes and on foot.

Small stdlib-only web app that runs on the team's Kubernetes namespace (see deploy/deploy.sh).
It reads the event's indexed dashcam footage through the VSS retrieval API, combines Cosmos's
description of each clip with the YOLO detections, and works out, from the point of view of the
cyclist or pedestrian, what the threat was and which side it came from. A person approves or
rejects each clip; decisions and blind labels are saved with their evidence.

Credentials come only from the environment (a Kubernetes Secret built from /config on the VM).
"""
import datetime
import hashlib
import json
import math
import os
import re
import ssl
import threading
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VSS_URL = os.environ.get("VSS_URL", "").rstrip("/")
VSS_USERNAME = os.environ.get("VSS_USERNAME", "")
VSS_PASSWORD = os.environ.get("VSS_PASSWORD", "")
PORT = int(os.environ.get("PORT", "8080"))
DATA_DIR = os.environ.get("DATA_DIR", "/data")
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CAMERA = os.environ.get("CLOSECALL_CAMERA", "").strip()          # e.g. pie_cam-3 (optional)
TAGS = [t for t in os.environ.get("CLOSECALL_TAGS", "").split(",") if t.strip()]
MIN_SIM = float(os.environ.get("CLOSECALL_MIN_SIMILARITY", "0.25"))
TOP_K = int(os.environ.get("CLOSECALL_TOP_K", "20"))
MAX_CLIPS = int(os.environ.get("CLOSECALL_MAX_CLIPS", "60"))
INSECURE = os.environ.get("VSS_INSECURE", "1") == "1"
RIDER_CAMS = {c.strip() for c in os.environ.get("CLOSECALL_RIDER_CAMS", "nyc_bike_gopro-1").split(",") if c.strip()}
SKIP_CAMS = {c.strip() for c in os.environ.get("CLOSECALL_SKIP_CAMS", "smartspace_cam-1,sdg_warehouse_cam-2").split(",") if c.strip()}
VERSION = "rider_v5"
CUTOFF = 5.0          # a danger score of 5.0 or more counts as a close call (for people and for the AI)

RIDER_QUERIES = [
    ("close_pass", "car passing close to a cyclist"),
    ("close_pass", "cyclist riding next to moving traffic"),
    ("opening_door", "car door opening next to a cyclist"),
    ("turning_car", "car turning right across a bike lane"),
    ("bus_pulling_in", "bus pulling over in front of a cyclist"),
    ("crossing_car", "pedestrian crossing in front of a moving car"),
    ("crossing_car", "person stepping into the road in front of a car"),
    ("braking", "car braking hard for a person"),
]
HAZARD_QUERIES = [
    ("hazard", "construction zone next to traffic"),
    ("hazard", "debris or object lying in the road"),
    ("hazard", "exposed wires or cables near the road"),
    ("hazard", "open hole or trench near the road"),
]

BIKE = {"bicycle", "bike", "cyclist", "bicyclist"}
PED = {"person", "pedestrian", "people"}
VEH = {"car", "bus", "truck", "motorcycle", "motorbike", "van", "vehicle", "suv", "pickup"}

os.makedirs(DATA_DIR, exist_ok=True)
_lock = threading.Lock()
STATE = {"status": "idle", "started": None, "finished": None, "error": None, "clips": [], "log": []}


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def log(msg):
    line = f"{now_iso()} {msg}"
    print(line, flush=True)
    STATE["log"] = (STATE["log"] + [line])[-80:]


# ---------------------------------------------------------------- VSS client
_ctx = ssl.create_default_context()
if INSECURE:
    _ctx.check_hostname = False
    _ctx.verify_mode = ssl.CERT_NONE
_token = {"value": None, "at": 0}


def _http(method, url, body=None, headers=None, timeout=60):
    data = None
    hdrs = dict(headers or {})
    if body is not None:
        data = json.dumps(body).encode()
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    return urllib.request.urlopen(req, context=_ctx, timeout=timeout)


def login(force=False):
    if _token["value"] and not force and time.time() - _token["at"] < 1800:
        return _token["value"]
    with _http("POST", VSS_URL + "/api/v1/auth/login",
               {"username": VSS_USERNAME, "password": VSS_PASSWORD}) as r:
        _token["value"] = json.loads(r.read())["access_token"]
        _token["at"] = time.time()
    return _token["value"]


def vss(method, path, body=None, params=None, timeout=90):
    url = VSS_URL + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for attempt in range(2):
        try:
            with _http(method, url, body, {"Authorization": "Bearer " + login(force=attempt > 0)},
                       timeout=timeout) as r:
                raw = r.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            if e.code == 401 and attempt == 0:
                continue
            detail = e.read()[:400].decode("utf-8", "replace")
            raise RuntimeError(f"{method} {path} -> {e.code}: {detail}")


def search(query, camera=None, top_k=None):
    body = {"query": query, "top_k": top_k or TOP_K, "llm_top_n": 0, "min_similarity": MIN_SIM,
            "include_public": True}
    if TAGS:
        body["tags"] = TAGS
    if camera or CAMERA:
        body["metadata_filters"] = {"camera_id": camera or CAMERA}
    try:
        return vss("POST", "/api/v1/search", body)
    except RuntimeError as e:
        if "-> 422" in str(e) or "-> 400" in str(e):
            body.pop("llm_top_n", None)
            body["llm_top_n"] = 1
            return vss("POST", "/api/v1/search", body)
        raise


# ---------------------------------------------------------------- parsing helpers
def first(d, keys, default=None):
    if not isinstance(d, dict):
        return default
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default


def as_float(x, default=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def clip_fields(item):
    """Pull the fields we need out of one search result, whatever the exact key names are."""
    meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
    src = first(item, ["source", "segment_source", "s3_uri", "uri"]) or first(meta, ["source"])
    start = first(item, ["segment_start_sec", "start_time", "segment_start", "start_sec", "best_match_start_sec", "start"]) \
        or first(meta, ["start_time", "segment_start"])
    end = first(item, ["segment_end_sec", "end_time", "segment_end", "end_sec", "best_match_end_sec", "end"]) \
        or first(meta, ["end_time", "segment_end"])
    return {
        "source": src,
        "original_video": first(item, ["original_video", "parent", "video"]) or first(meta, ["original_video"]),
        "similarity": as_float(first(item, ["similarity_score", "similarity", "score"]), 0.0),
        "caption": first(item, ["reasoning_content", "caption", "description", "text"]) or "",
        "camera_id": first(item, ["camera_id", "camera"]) or first(meta, ["camera_id", "camera"]) or "",
        "location": first(item, ["location"]) or first(meta, ["location"]) or "",
        "start": start,
        "end": end,
        "tags": item.get("tags") or meta.get("tags") or [],
        "filename": first(item, ["filename"]) or "",
    }


def _box(d, W=None, H=None):
    b = first(d, ["bbox", "box", "xyxy", "bbox_xyxy", "coordinates", "bounding_box"])
    x1 = y1 = x2 = y2 = None
    if isinstance(b, dict):
        if all(k in b for k in ("x1", "y1", "x2", "y2")):
            x1, y1, x2, y2 = (as_float(b[k]) for k in ("x1", "y1", "x2", "y2"))
        elif all(k in b for k in ("x", "y", "w", "h")):
            x1, y1 = as_float(b["x"]), as_float(b["y"])
            x2, y2 = x1 + as_float(b["w"]), y1 + as_float(b["h"])
        elif all(k in b for k in ("left", "top", "width", "height")):
            x1, y1 = as_float(b["left"]), as_float(b["top"])
            x2, y2 = x1 + as_float(b["width"]), y1 + as_float(b["height"])
    elif isinstance(b, (list, tuple)) and len(b) >= 4:
        x1, y1, x2, y2 = (as_float(v) for v in b[:4])
        fmt = str(first(d, ["bbox_format", "format"], "")).lower()
        if fmt in ("xywh", "ltwh") or (x2 is not None and x1 is not None and x2 < x1) or \
                (y2 is not None and y1 is not None and y2 < y1):
            x2, y2 = x1 + x2, y1 + y2
    elif all(k in d for k in ("x1", "y1", "x2", "y2")):
        x1, y1, x2, y2 = (as_float(d[k]) for k in ("x1", "y1", "x2", "y2"))
    elif all(k in d for k in ("x", "y", "w", "h")):
        x1, y1 = as_float(d["x"]), as_float(d["y"])
        x2, y2 = x1 + as_float(d["w"]), y1 + as_float(d["h"])
    if None in (x1, y1, x2, y2):
        return None
    if max(x2, y2) > 1.5:  # pixels
        W = W or 1920.0
        H = H or 1080.0
        x1, x2, y1, y2 = x1 / W, x2 / W, y1 / H, y2 / H
    return [max(0.0, min(1.0, v)) for v in (x1, y1, x2, y2)]


def _obj(d, W, H):
    label = str(first(d, ["label", "class_name", "class", "name", "category", "cls", "object"], "")).lower()
    if label.isdigit():
        label = {"0": "person", "1": "bicycle", "2": "car", "3": "motorcycle", "5": "bus", "7": "truck"}.get(label, label)
    box = _box(d, W, H)
    if not box or not label:
        return None
    return {"label": label, "conf": as_float(first(d, ["confidence", "conf", "score", "probability"]), 1.0),
            "box": [round(v, 4) for v in box],
            "id": first(d, ["track_id", "id", "object_id"])}


def norm_detections(js):
    """Normalize the YOLO sidecar into {frames:[{t, objs:[{label, conf, box[x1,y1,x2,y2] 0..1}]}]}."""
    if js is None:
        return {"frames": [], "fps": None}
    root = js
    if isinstance(js, dict):
        for k in ("detections", "data", "result", "results", "frames"):
            if k in js and isinstance(js[k], (list, dict)):
                root = js[k] if k != "frames" else js
                break
    W = as_float(first(js if isinstance(js, dict) else {}, ["width", "image_width", "frame_width", "img_w"]))
    H = as_float(first(js if isinstance(js, dict) else {}, ["height", "image_height", "frame_height", "img_h"]))
    fps = as_float(first(js if isinstance(js, dict) else {}, ["fps", "frame_rate"]))
    shape = js.get("video_shape") if isinstance(js, dict) else None
    if isinstance(shape, list) and len(shape) >= 2 and not (W and H):
        H, W = as_float(shape[0]), as_float(shape[1])
    frames = []
    seq = None
    if isinstance(root, dict) and isinstance(root.get("frames"), list):
        seq = root["frames"]
    elif isinstance(root, list):
        seq = root
    elif isinstance(root, dict):
        # {"0": [...], "1": [...]} keyed by frame/time
        try:
            seq = [{"t": float(k), "objects": v} for k, v in root.items() if isinstance(v, list)]
        except ValueError:
            seq = []
    for i, f in enumerate(seq or []):
        if isinstance(f, dict) and any(k in f for k in ("objects", "detections", "boxes", "objs", "predictions")):
            fw = as_float(first(f, ["width", "image_width"]), W)
            fh = as_float(first(f, ["height", "image_height"]), H)
            if isinstance(f.get("shape"), list) and len(f["shape"]) >= 2:
                fh, fw = as_float(f["shape"][0], fh), as_float(f["shape"][1], fw)
            t = as_float(first(f, ["t", "timestamp", "time", "ts", "pts", "time_sec", "frame", "frame_idx",
                                   "frame_index", "frame_id"]), float(i))
            items = first(f, ["objects", "detections", "boxes", "objs", "predictions"]) or []
            objs = [o for o in (_obj(d, fw, fh) for d in items if isinstance(d, dict)) if o]
            frames.append({"t": t, "objs": objs})
        elif isinstance(f, dict):
            # flat list of detections, each with its own frame/time
            o = _obj(f, W, H)
            t = as_float(first(f, ["t", "timestamp", "time", "ts", "frame", "frame_idx", "frame_index"]), 0.0)
            if o:
                if frames and frames[-1]["t"] == t:
                    frames[-1]["objs"].append(o)
                else:
                    frames.append({"t": t, "objs": [o]})
    frames.sort(key=lambda fr: fr["t"])
    return {"frames": frames, "fps": fps, "aspect": round(W / H, 4) if W and H else None}


# ---------------------------------------------------------------- rider analysis
def kind_of(label):
    if label in BIKE:
        return "bike"
    if label in PED:
        return "person"
    if label in VEH:
        return "vehicle"
    return "other"


def overlap(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    area = (a[2] - a[0]) * (a[3] - a[1]) or 1e-6
    return inter / area


def gap(a, b):
    dx = max(0.0, max(a[0], b[0]) - min(a[2], b[2]))
    dy = max(0.0, max(a[1], b[1]) - min(a[3], b[3]))
    return math.hypot(dx, dy)


RIDER_THREAT = {"pulling_away": "close_pass", "you_passing": "squeeze", "alongside": "alongside",
                "closing_in": "too_close_ahead", "ahead": "too_close_ahead", "someone_ahead": "other"}
SIDE_WORDS = {"left": "on your left", "right": "on your right", "ahead": "ahead of you", "behind": "from behind"}
THREAT_WORDS = {
    "close_pass": "{veh} passing too close {side}",
    "opening_door": "Car door opening {side}",
    "turning_car": "{veh} turning across your path {side}",
    "bus_pulling_in": "Bus pulling in {side}",
    "crossing_car": "{veh} heading into your path {side}",
    "braking": "{veh} braking hard {side}",
    "other": "{veh} too close {side}",
}


def cam_mode(cam):
    """rider = camera on the bike (the rider's own eyes); dashcam = camera in a car; fixed = street camera."""
    cam = (cam or "").lower()
    if cam in RIDER_CAMS or "bike" in cam or "gopro" in cam:
        return "rider"
    if "pie" in cam or "dash" in cam:
        return "dashcam"
    return "fixed"


def vru_vehicle_risk(frames, use_ego, skip_own_body=False, aspect_ratio=16 / 9):
    """How close any vehicle gets to a person on a bike or on foot that the camera can see. Two boxes only
    count as close when their bottoms (where they touch the ground) are at about the same depth, and the
    closeness has to last a few frames."""
    per_frame = []
    for f in frames:
        top = {"risk": 0.0}
        vrus = [o for o in f["objs"] if kind_of(o["label"]) in ("bike", "person") and o["conf"] >= 0.35]
        vehs = [o for o in f["objs"] if kind_of(o["label"]) == "vehicle" and o["conf"] >= 0.35
                and o["box"][3] - o["box"][1] >= 0.04]
        bikes = [o for o in vrus if kind_of(o["label"]) == "bike"]
        for v in vrus:
            vb = v["box"]
            if skip_own_body and vb[3] >= 0.95:          # bike cam: the rider's own arms and handlebars
                continue
            if kind_of(v["label"]) == "person" and any(overlap(vb, b["box"]) > 0.2 for b in bikes):
                continue                                  # a person on a bicycle counts once, as the cyclist
            if any(overlap(vb, c["box"]) > 0.8 for c in vehs):
                continue                                  # someone sitting inside a car or bus
            h = max(1e-3, vb[3] - vb[1])
            cx = (vb[0] + vb[2]) / 2
            if use_ego:
                # dashcam: a big, central person/bike box means the camera car itself is very close
                ego = max(0.0, min(1.0, (h - 0.22) / 0.33)) * (1.0 if abs(cx - 0.5) < 0.3 else 0.6)
                if ego > top["risk"]:
                    eside = "behind" if kind_of(v["label"]) == "bike" or bikes else ("left" if cx > 0.5 else "right")
                    top = {"risk": ego, "side": eside, "veh": "Car", "t": f["t"], "ego": True}
            for car in vehs:
                cb = car["box"]
                depth = abs(cb[3] - vb[3]) / h            # how far apart their bottoms are, in person heights
                if depth > 0.35:
                    continue
                dx = max(0.0, cb[0] - vb[2], vb[0] - cb[2])
                gap_m = dx * aspect_ratio / h * 1.7       # a person is about 1.7 m tall
                r = max(0.0, min(1.0, 1.0 - gap_m / 1.5)) * (1.0 if depth <= 0.15 else (0.35 - depth) / 0.2)
                if r > top["risk"]:
                    side = "left" if (cb[0] + cb[2]) / 2 < cx else "right"
                    top = {"risk": r, "side": side, "veh": car["label"].capitalize(), "t": f["t"], "ego": False,
                           "clearance_m": round(gap_m, 2)}
        per_frame.append(top)
    ranked = sorted(per_frame, key=lambda b: -b["risk"])
    best = ranked[min(4, len(ranked) - 1)] if ranked else {"risk": 0.0}   # the 5th strongest frame counts
    if best["risk"] <= 0:
        return {"risk": 0.0, "side": "none", "veh": "Car", "t": None, "ego": False}
    return best


# Typical real heights (m). A box's height in the picture is a ruler: it says how far away the vehicle is,
# and how far its inner edge sits from the middle of the picture says how far it is to the side.
VEH_HEIGHT = {"car": 1.5, "suv": 1.7, "van": 2.0, "pickup": 1.8, "bus": 3.0, "truck": 3.0,
              "motorcycle": 1.4, "motorbike": 1.4, "vehicle": 1.6}
FOCAL_Y = float(os.environ.get("CLOSECALL_FOCAL_Y", "1.0"))   # bike cam focal length, in picture heights


MOTION_WEIGHT = {"pulling_away": 0.75, "alongside": 0.7, "you_passing": 0.6}


def _iou(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def vehicle_tracks(frames, step=2):
    """Follow each vehicle from frame to frame (greedy box overlap), so one odd box doesn't count."""
    tracks, active = [], []
    for i, f in enumerate(frames):
        if i % step:
            continue
        boxes = [o for o in f["objs"] if kind_of(o["label"]) == "vehicle" and o["conf"] >= 0.35
                 and o["box"][3] - o["box"][1] >= 0.05 and o["box"][1] < 0.85]   # bottom strip: own bike parts
        used = set()
        for tr in active:
            bi, bv = -1, 0.2
            for j, o in enumerate(boxes):
                if j not in used:
                    v = _iou(tr["last"], o["box"])
                    if v > bv:
                        bi, bv = j, v
            if bi >= 0:
                used.add(bi)
                tr["pts"].append({"t": f["t"], "box": boxes[bi]["box"]})
                tr["last"], tr["miss"] = boxes[bi]["box"], 0
            else:
                tr["miss"] += 1
        for j, o in enumerate(boxes):
            if j not in used:
                tr = {"label": o["label"], "pts": [{"t": f["t"], "box": o["box"]}], "last": o["box"], "miss": 0}
                active.append(tr)
                tracks.append(tr)
        active = [tr for tr in active if tr["miss"] <= 3]
    return [tr for tr in tracks if len(tr["pts"]) >= 3]


def _geo(box, label, aspect_ratio):
    x1, y1, x2, y2 = box
    h, w = max(1e-3, y2 - y1), x2 - x1
    height = VEH_HEIGHT.get(label, 1.6)
    if x2 < 0.5:
        side, u = "left", 0.5 - x2
    elif x1 > 0.5:
        side, u = "right", x1 - 0.5
    else:
        side, u = "ahead", 0.0
    return {"side": side, "h": h, "w": w, "clipped": y2 >= 0.97 or y1 <= 0.01,
            "aspect": w * aspect_ratio / h,          # about 1 when seen from behind, about 3 from the side
            "X": aspect_ratio * height * u / h,       # metres between its near side and the rider's line
            "Z": FOCAL_Y * height / h}                # metres ahead of the camera


def rider_cam_risk(frames, aspect_ratio=16 / 9):
    """Camera on the bike: the rider is the camera. For every vehicle, estimate how far it is to the side
    of the rider (clearance) and how far ahead, from its box alone, and keep the closest moment."""
    best = {"risk": 0.0, "side": "none", "veh": "Car", "t": None, "ego": True, "clearance_m": None,
            "distance_m": None, "motion": None}
    for tr in vehicle_tracks(frames):
        label = tr["label"]
        big = 1.15 if label in ("bus", "truck") else 1.0
        g = [dict(_geo(p["box"], label, aspect_ratio), t=p["t"]) for p in tr["pts"]]
        # beside the rider: seen mostly from behind (box not too wide), within 3 m, in at least 3 samples
        near = [p for p in g if p["side"] != "ahead" and not p["clipped"] and p["aspect"] <= 2.2 and p["Z"] <= 3.0]
        if len(near) >= 3:
            at = sorted(near, key=lambda p: p["X"])[1]            # 2nd closest, so one odd box doesn't count
            i = g.index(at)
            dh = g[min(len(g) - 1, i + 6)]["h"] - g[max(0, i - 6)]["h"]
            motion = "pulling_away" if dh < -0.04 else "you_passing" if dh > 0.04 else "alongside"
            # a vehicle passing the rider counts more than the rider squeezing past slow traffic
            r = max(0.0, min(1.0, (1.0 - at["X"]) / 1.0)) * big * (1.0 if at["Z"] <= 2.0 else 0.85) \
                * MOTION_WEIGHT[motion]
            if r > best["risk"]:
                best = {"risk": r, "side": at["side"], "veh": label.capitalize(), "t": at["t"], "ego": True,
                        "clearance_m": round(at["X"], 2), "distance_m": round(at["Z"], 1), "motion": motion}
        # in the rider's path: straight ahead and closer than 2 m
        ahead = [p for p in g if p["side"] == "ahead" and not p["clipped"] and p["Z"] <= 2.0]
        if len(ahead) >= 3:
            at = sorted(ahead, key=lambda p: p["Z"])[1]
            closing = g[0]["h"] < 0.8 * at["h"]
            r = max(0.0, min(1.0, (2.0 - at["Z"]) / 1.0)) * (0.8 if closing else 0.5)
            if r > best["risk"]:
                best = {"risk": r, "side": "ahead", "veh": label.capitalize(), "t": at["t"], "ego": True,
                        "clearance_m": None, "distance_m": round(at["Z"], 1),
                        "motion": "closing_in" if closing else "ahead"}
        # a big vehicle right alongside, filling half the picture: too close to measure, so a person checks
        along = [p for p in g if p["side"] != "ahead" and p["clipped"] and p["h"] >= 0.6 and p["w"] >= 0.45]
        if len(along) >= 3 and best["risk"] < 0.4:
            best = {"risk": 0.4, "side": along[1]["side"], "veh": label.capitalize(), "t": along[1]["t"],
                    "ego": True, "clearance_m": None, "distance_m": None, "motion": "alongside"}
    return best


def rider_warning(best):
    veh, side = best["veh"], SIDE_WORDS.get(best["side"], "")
    m = best.get("clearance_m")
    dist = "very close" if m is None else "less than 20 cm" if m < 0.2 else f"about {m:.1f} m"
    motion = best.get("motion")
    if motion == "pulling_away":
        text = f"{veh} passed {dist} from you {side}"
    elif motion == "you_passing":
        text = f"You squeezed past a {veh.lower()} with {dist} to spare {side}" if m is not None else \
            f"You squeezed past a {veh.lower()} {side}"
    elif motion == "closing_in":
        text = f"{veh} slowing right in front of you, about {best.get('distance_m')} m ahead"
    elif motion == "ahead":
        text = f"{veh} right in front of you, about {best.get('distance_m')} m ahead"
    else:
        text = f"{veh} alongside you, {dist} {side}"
    return " ".join(text.split()) + "."


def analyze(c, det):
    cap = (c.get("caption") or "").lower()
    kinds = set(c.get("kinds", []))
    frames = det.get("frames", [])
    mode = cam_mode(c.get("camera_id"))
    aspect = det.get("aspect") or 16 / 9
    has_bike = any(kind_of(o["label"]) == "bike" for f in frames for o in f["objs"])
    has_ped = any(kind_of(o["label"]) == "person" for f in frames for o in f["objs"])
    if not frames:
        has_bike = bool(re.search(r"cyclist|bicycl|bike", cap))
        has_ped = bool(re.search(r"pedestrian|person|people|walk", cap))
    if mode == "rider":
        who = "cyclist"
        best = rider_cam_risk(frames, aspect)
        # someone else the rider can see (the cyclist ahead, a pedestrian) with a vehicle right next to them
        other = vru_vehicle_risk(frames, use_ego=False, skip_own_body=True, aspect_ratio=aspect)
        if min(other["risk"] * 0.6, 0.3) > best["risk"]:          # a note, never a close call by itself
            best = dict(other, risk=min(other["risk"] * 0.6, 0.3), motion="someone_ahead")
    else:
        who = "cyclist" if has_bike or re.search(r"cyclist|bicycl", cap) else ("pedestrian" if has_ped else "none")
        best = vru_vehicle_risk(frames, use_ego=(mode == "dashcam"), aspect_ratio=aspect)
        best = dict(best, risk=best["risk"] * 0.55)      # boxes side by side in a street view are weaker evidence

    # Cosmos itself describing a close interaction is a second, independent signal
    cue = bool(re.search(r"brak(es|ing)? (hard|sudden)|sudden(ly)? (brak|stop)|swerv|abrupt|close call|near miss|"
                         r"narrowly|cut(s|ting)? off|honk|jumps? back|pass(es|ing)? (very )?close|passing closely|"
                         r"passes closely|weav|between (the )?(cars|vehicles|lanes|traffic)|squeez|tight gap", cap))
    risk = min(1.0, best["risk"] + (0.25 if cue else 0.0))
    score = round(10 * risk, 1)                                  # danger score, 0.0 to 10.0
    severity = "high" if score >= 7.5 else "medium" if score >= CUTOFF else "low" if score >= 2.0 else "none"

    threat = "other"
    if mode == "rider" and best["risk"] > 0:
        threat = RIDER_THREAT.get(best.get("motion"), "other")
    for k, pat in (("opening_door", r"door"), ("bus_pulling_in", r"\bbus\b"), ("turning_car", r"turn"),
                   ("close_pass", r"pass|overtak|alongside"), ("crossing_car", r"cross"), ("braking", r"brak")):
        if threat == "other" and re.search(pat, cap):
            threat = k
            break
    if threat == "other" and kinds - {"hazard"} and mode != "rider":
        threat = sorted(kinds - {"hazard"})[0]
    if threat == "other" and best.get("ego") and mode == "dashcam":
        threat = "close_pass" if who == "cyclist" else "crossing_car"

    hazard = "none"
    for k, pat in (("wires", r"wire|cable"), ("open_hole", r"\bhole\b|trench|pothole|excavat"),
                   ("equipment", r"excavator|crane|bulldozer|backhoe|forklift|heavy equipment"),
                   ("debris", r"debris|rubble|object (lying|in) the road"),
                   ("work_zone", r"construction|road ?work|work zone|traffic cone|orange cone|barrier|scaffold")):
        if re.search(pat, cap):
            hazard = k
            break

    murky = bool(re.search(r"\bdark\b|blurr|unclear|obscur|hard to see|can'?t see", cap))
    if not frames and (murky or who != "none" or not cap):
        verdict = "CANT_TELL"                                    # nothing to measure: a person checks
    elif score >= CUTOFF and (who != "none" or mode == "rider"):
        verdict = "CLOSE_CALL"
    else:
        verdict = "NO_CONFLICT"
    shown = verdict == "CLOSE_CALL" or (verdict == "NO_CONFLICT" and score >= 2.0)

    side = best["side"] if shown else "none"
    veh = "Bus" if threat == "bus_pulling_in" else best["veh"]
    if verdict == "CANT_TELL":
        warning = "Too dark or blurry to be sure. A person should check this clip." if murky else \
            "No object detections for this clip, so nothing to measure. A person should check it."
    elif mode == "rider" and shown and best.get("motion") and best.get("motion") != "someone_ahead":
        warning = rider_warning(best)
    elif who == "none" or not shown:
        warning = "No threat to anyone on a bike or on foot." if hazard == "none" else \
            "Watch the road: " + hazard.replace("_", " ") + " ahead."
    elif mode == "rider" and best.get("motion") == "someone_ahead":
        warning = f"{best['veh']} right next to the cyclist or person ahead of you."
    else:
        warning = THREAT_WORDS.get(threat, THREAT_WORDS["other"]).format(
            veh=veh, side=SIDE_WORDS.get(side, "")).strip() + "."
    return {"verdict": verdict, "score": None if verdict == "CANT_TELL" else score, "who_at_risk": who,
            "threat": threat if shown else "none", "threat_side": side, "severity": severity,
            "risk": round(risk, 3), "peak_t": best["t"], "hazard": hazard, "warning": warning,
            "has_detections": bool(frames), "cue": cue, "camera_mode": mode,
            "clearance_m": best.get("clearance_m"), "distance_m": best.get("distance_m"),
            "motion": best.get("motion"), "approaching": best.get("motion") == "closing_in"}


# ---------------------------------------------------------------- build the clip list
def build():
    with _lock:
        if STATE["status"] == "running":
            return
        STATE.update(status="running", started=now_iso(), error=None)
    try:
        login(force=True)
        found = {}
        plan = [(k, q, cam) for k, q in RIDER_QUERIES for cam in sorted(RIDER_CAMS)] + \
               [(k, q, None) for k, q in RIDER_QUERIES + HAZARD_QUERIES]
        for kind, q, cam in plan:
            try:
                res = search(q, camera=cam, top_k=15 if cam else None)
            except Exception as e:  # keep going with the other searches
                log(f"search failed for '{q}' ({cam or 'all cameras'}): {e}")
                continue
            items = (res or {}).get("results") or []
            log(f"search '{q}' ({cam or 'all cameras'}): {len(items)} hits")
            for it in items:
                f = clip_fields(it)
                if not f["source"] or f["camera_id"] in SKIP_CAMS:
                    continue
                c = found.setdefault(f["source"], dict(f, kinds=[], queries=[]))
                c["similarity"] = max(c["similarity"], f["similarity"])
                if kind not in c["kinds"]:
                    c["kinds"].append(kind)
                c["queries"].append(q)
        ranked = sorted(found.values(), key=lambda c: -c["similarity"])[:MAX_CLIPS]
        clips = []
        for i, c in enumerate(ranked):
            try:
                raw = vss("GET", "/api/v1/videos/detections", params={"source": c["source"]})
                det = norm_detections(raw)
            except Exception as e:
                det = {"frames": [], "fps": None, "error": str(e)[:200]}
            c["detections"] = det
            c["analysis"] = analyze(c, det)
            c["id"] = hashlib.sha1(c["source"].encode()).hexdigest()[:12]
            clips.append(c)
            if i % 5 == 4:
                STATE["clips"] = clips[:]
        STATE["clips"] = clips
        with open(os.path.join(DATA_DIR, "clips.json"), "w") as fh:
            json.dump({"version": VERSION, "clips": clips}, fh)
        STATE.update(status="ready", finished=now_iso())
        log(f"ready: {len(clips)} clips")
    except Exception as e:
        STATE.update(status="error", error=f"{e}", finished=now_iso())
        log("build failed: " + traceback.format_exc()[-600:])


def load_cached():
    p = os.path.join(DATA_DIR, "clips.json")
    if os.path.exists(p):
        try:
            saved = json.load(open(p))
            if isinstance(saved, dict) and saved.get("version") == VERSION:
                STATE["clips"] = saved["clips"]
                STATE["status"] = "ready"
        except Exception:
            pass


# ---------------------------------------------------------------- decisions, labels, accuracy
def read_jsonl(name):
    p = os.path.join(DATA_DIR, name)
    if not os.path.exists(p):
        return []
    out = []
    for line in open(p):
        try:
            out.append(json.loads(line))
        except ValueError:
            pass
    return out


def append_jsonl(name, row):
    with _lock:
        with open(os.path.join(DATA_DIR, name), "a") as fh:
            fh.write(json.dumps(row) + "\n")


def wilson(k, n, z=1.96):
    if n == 0:
        return {"value": None, "low": None, "high": None, "n": 0}
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return {"value": round(p, 3), "low": round(max(0, centre - half), 3), "high": round(min(1, centre + half), 3), "n": n}


def kappa(a, b):
    n = len(a)
    if n == 0:
        return None
    cats = set(a) | set(b)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    return round((po - pe) / (1 - pe), 3) if pe < 1 else 1.0


def pearson(pairs):
    n = len(pairs)
    if n < 3:
        return None
    mx, my = sum(x for x, _ in pairs) / n, sum(y for _, y in pairs) / n
    sxy = sum((x - mx) * (y - my) for x, y in pairs)
    sxx, syy = sum((x - mx) ** 2 for x, _ in pairs), sum((y - my) ** 2 for _, y in pairs)
    return round(sxy / math.sqrt(sxx * syy), 2) if sxx > 0 and syy > 0 else None


def accuracy():
    labels = [r for r in read_jsonl("labels.jsonl") if r.get("labeler", "").lower() != "test"]
    by_clip = {}
    for r in labels:
        by_clip.setdefault(r["clip_id"], {})[r["labeler"]] = r              # last rating per person wins
    clips = {c["id"]: c for c in STATE["clips"]}
    labelers = sorted({r["labeler"] for r in labels})
    rows = []                                                             # (human score, human verdict, clip)
    for cid, per in by_clip.items():
        if cid not in clips:
            continue
        rated = [r for r in per.values() if r.get("label") != "CANT_TELL"]
        scores = [r["score"] for r in rated if r.get("score") is not None]
        if scores:
            hs = round(sum(scores) / len(scores), 2)                      # average of everyone who rated it
            rows.append((hs, "CLOSE_CALL" if hs >= CUTOFF else "NO_CONFLICT", clips[cid]))
        elif rated:
            rows.append((None, sorted(r["label"] for r in rated)[0], clips[cid]))   # older 3-button labels
        else:
            rows.append((None, "CANT_TELL", clips[cid]))
    judged = [r for r in rows if r[1] != "CANT_TELL"]

    def evaluate(pred_bin, pred_score=None):
        tp = sum(1 for _, h, c in judged if h == "CLOSE_CALL" and pred_bin(c) == "CLOSE_CALL")
        pp = sum(1 for _, h, c in judged if pred_bin(c) == "CLOSE_CALL")
        hp = sum(1 for _, h, c in judged if h == "CLOSE_CALL")
        answered = [(h, pred_bin(c)) for _, h, c in judged if pred_bin(c) != "CANT_TELL"]
        out = {"precision": wilson(tp, pp), "recall": wilson(tp, hp),
               "coverage": wilson(sum(1 for _, _, c in rows if pred_bin(c) != "CANT_TELL"), len(rows)),
               "agreement": wilson(sum(1 for h, p in answered if h == p), len(answered)), "mae": None, "corr": None}
        if pred_score:
            pairs = [(hs, pred_score(c)) for hs, _, c in judged if hs is not None and pred_score(c) is not None]
            if pairs:
                out["mae"] = {"value": round(sum(abs(h - p) for h, p in pairs) / len(pairs), 2), "n": len(pairs)}
                out["corr"] = pearson(pairs)
        return out

    versions = [
        {"name": "A — search only (every clip it found counts as a close call)",
         **evaluate(lambda c: "CLOSE_CALL" if c["kinds"] and c["kinds"] != ["hazard"] else "NO_CONFLICT")},
        {"name": "C — CloseCall danger score (Cosmos + YOLO, metres around the rider)",
         **evaluate(lambda c: c["analysis"]["verdict"], lambda c: c["analysis"].get("score"))},
    ]
    k = None
    if len(labelers) >= 2:
        a_lab, b_lab = labelers[0], labelers[1]
        both = [(p[a_lab], p[b_lab]) for p in by_clip.values() if a_lab in p and b_lab in p]
        sc = [(x["score"], y["score"]) for x, y in both if x.get("score") is not None and y.get("score") is not None]
        k = {"labelers": [a_lab, b_lab], "n": len(both),
             "kappa": kappa([x["label"] for x, _ in both], [y["label"] for _, y in both]),
             "mean_diff": round(sum(abs(x - y) for x, y in sc) / len(sc), 2) if sc else None, "n_scored": len(sc)}
    return {"n_labeled": len(rows), "human_cant_tell": len(rows) - len(judged), "labelers": labelers,
            "kappa": k, "versions": versions, "cutoff": CUTOFF}


# ---------------------------------------------------------------- HTTP
def public_clip(c, blind=False):
    out = {k: c.get(k) for k in ("id", "source", "original_video", "camera_id", "location", "start", "end",
                                  "similarity", "filename")}
    out["duration"] = None
    if not blind:
        out.update(caption=c.get("caption"), kinds=c.get("kinds"), queries=c.get("queries"),
                   analysis=c.get("analysis"), has_detections=bool(c.get("detections", {}).get("frames")))
    return out


class Handler(BaseHTTPRequestHandler):
    server_version = "CloseCall/1.0"

    def log_message(self, fmt, *args):
        pass

    def send_json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            return {}

    def do_GET(self):
        try:
            u = urllib.parse.urlparse(self.path)
            q = dict(urllib.parse.parse_qsl(u.query))
            p = u.path.rstrip("/") or "/"
            if p == "/health":
                return self.send_json({"ok": True})
            if p in ("/", "/index.html"):
                body = open(os.path.join(APP_DIR, "index.html"), "rb").read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                return self.wfile.write(body)
            if p == "/api/status":
                return self.send_json({k: STATE[k] for k in ("status", "started", "finished", "error", "log")}
                                      | {"clips": len(STATE["clips"]), "camera": CAMERA, "tags": TAGS})
            if p == "/api/clips":
                decided = {d["clip_id"] for d in read_jsonl("decisions.jsonl") if d.get("reviewer", "").lower() != "test"}
                out = []
                for c in STATE["clips"]:
                    pc = public_clip(c)
                    pc["decided"] = c["id"] in decided
                    out.append(pc)
                return self.send_json({"status": STATE["status"], "clips": out})
            if p == "/api/detections":
                c = next((c for c in STATE["clips"] if c["id"] == q.get("id")), None)
                return self.send_json(c.get("detections") if c else {"frames": []})
            if p == "/api/label-queue":
                who = (q.get("labeler") or "").strip().lower()
                done = {r["clip_id"] for r in read_jsonl("labels.jsonl") if r.get("labeler", "").lower() == who
                        and (r.get("score") is not None or r.get("label") == "CANT_TELL")}   # old 3-button labels: rate again
                order = sorted(STATE["clips"], key=lambda c: c["id"])
                return self.send_json({"clips": [public_clip(c, blind=True) for c in order if c["id"] not in done],
                                       "done": len(done), "total": len(order)})
            if p == "/api/decisions":
                rows = [d for d in read_jsonl("decisions.jsonl") if d.get("reviewer", "").lower() != "test"]
                return self.send_json({"decisions": rows[::-1]})
            if p == "/api/accuracy":
                return self.send_json(accuracy())
            if p == "/api/export":
                return self.send_json({"exported_at": now_iso(), "decisions": read_jsonl("decisions.jsonl"),
                                       "labels": read_jsonl("labels.jsonl"),
                                       "clips": [public_clip(c) for c in STATE["clips"]]})
            if p == "/api/debug":
                return self.send_json(debug_info(q))
            if p == "/video":
                return self.proxy_video(q)
            self.send_json({"error": "not found"}, 404)
        except Exception as e:
            self.send_json({"error": str(e)[:500]}, 500)

    def do_POST(self):
        try:
            p = urllib.parse.urlparse(self.path).path.rstrip("/")
            b = self.read_body()
            if p == "/api/refresh":
                threading.Thread(target=build, daemon=True).start()
                return self.send_json({"ok": True})
            clip = next((c for c in STATE["clips"] if c["id"] == b.get("clip_id")), None)
            if p == "/api/decide":
                if not clip or b.get("action") not in ("approve", "reject"):
                    return self.send_json({"error": "need clip_id and action approve|reject"}, 400)
                a = clip["analysis"]
                row = {"decision_id": hashlib.sha1(f"{clip['id']}{time.time()}".encode()).hexdigest()[:12],
                       "clip_id": clip["id"], "segment": clip["source"], "action": b["action"],
                       "reason": (b.get("reason") or "")[:500], "reviewer": (b.get("reviewer") or "anonymous")[:60],
                       "verdict_at_decision": a["verdict"], "who_at_risk": a["who_at_risk"], "threat": a["threat"],
                       "threat_side": a["threat_side"], "severity": a["severity"], "hazard": a["hazard"],
                       "score_at_decision": a.get("score"), "prompt_version": VERSION, "decided_at": now_iso()}
                append_jsonl("decisions.jsonl", row)
                return self.send_json({"ok": True, "decision": row})
            if p == "/api/label":
                sc, label = b.get("score"), b.get("label")
                if sc is not None:
                    try:
                        sc = round(float(sc), 1)
                    except (TypeError, ValueError):
                        sc = -1.0
                    if not 0.0 <= sc <= 10.0:
                        return self.send_json({"error": "score must be 0.0 to 10.0"}, 400)
                    label = "CLOSE_CALL" if sc >= CUTOFF else "NO_CONFLICT"
                if not clip or label not in ("CLOSE_CALL", "NO_CONFLICT", "CANT_TELL") or not (b.get("labeler") or "").strip():
                    return self.send_json({"error": "need clip_id, labeler and a score (or label CANT_TELL)"}, 400)
                append_jsonl("labels.jsonl", {"clip_id": clip["id"], "score": sc, "label": label,
                                              "labeler": b["labeler"].strip()[:40], "labeled_at": now_iso()})
                return self.send_json({"ok": True})
            self.send_json({"error": "not found"}, 404)
        except Exception as e:
            self.send_json({"error": str(e)[:500]}, 500)

    def proxy_video(self, q):
        c = next((c for c in STATE["clips"] if c["id"] == q.get("id")), None)
        if not c:
            return self.send_json({"error": "unknown clip"}, 404)
        url = VSS_URL + "/api/v1/videos/stream?" + urllib.parse.urlencode({"source": c["source"], "token": login()})
        hdrs = {}
        if self.headers.get("Range"):
            hdrs["Range"] = self.headers["Range"]
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=hdrs), context=_ctx, timeout=120)
        except urllib.error.HTTPError as e:
            r = e
        self.send_response(r.status if hasattr(r, "status") else r.code)
        for h in ("Content-Type", "Content-Length", "Content-Range", "Accept-Ranges"):
            if r.headers.get(h):
                self.send_header(h, r.headers[h])
        self.end_headers()
        try:
            while True:
                chunk = r.read(64 * 1024)
                if not chunk:
                    break
                self.wfile.write(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            r.close()


def debug_info(q):
    """What the real API returns, so the parsing can be checked. Never includes credentials or tokens."""
    out = {"vss_url_set": bool(VSS_URL), "camera": CAMERA, "tags": TAGS}
    try:
        login(force=True)
        out["login"] = "ok"
    except Exception as e:
        out["login"] = f"failed: {e}"
        return out
    for name, path, params in (("schema", "/api/v1/metadata/schema", None),
                               ("cameras", "/api/v1/metadata/values", {"field": "camera_id", "limit": 100})):
        try:
            out[name] = vss("GET", path, params=params)
        except Exception as e:
            out[name] = f"error: {e}"
    try:
        stats = vss("GET", "/api/v1/dashboard/stats", params={"scope": "all"})
        out["dashboard"] = {k: stats.get(k) for k in ("overview", "objects", "metadata")}
    except Exception as e:
        out["dashboard"] = f"error: {e}"
    try:
        res = search(q.get("q") or "cyclist next to a moving car")
        items = (res or {}).get("results") or []
        out["search_keys"] = sorted(res.keys()) if isinstance(res, dict) else str(type(res))
        out["search_sample"] = [{k: (str(v)[:300] if not isinstance(v, (int, float, bool)) else v)
                                 for k, v in it.items()} for it in items[:2]]
        if items:
            src = clip_fields(items[0])["source"]
            raw = vss("GET", "/api/v1/videos/detections", params={"source": src})
            txt = json.dumps(raw)
            out["detections_raw_head"] = txt[:2500]
            out["detections_normalized"] = {"frames": len(norm_detections(raw)["frames"]),
                                            "first": (norm_detections(raw)["frames"] or [None])[0]}
    except Exception as e:
        out["search_error"] = str(e)[:500]
    return out


def _code_hash():
    try:
        return hashlib.sha1(open(os.path.abspath(__file__), "rb").read()).hexdigest()
    except OSError:
        return None


def watch_code():
    """Kubernetes refreshes the mounted ConfigMap in place; restart this process (same pod, same
    /data disk) when main.py changes, so decisions and labels survive code updates."""
    first_hash = _code_hash()
    while True:
        time.sleep(5)
        h = _code_hash()
        if h and first_hash and h != first_hash:
            log("main.py changed, restarting the process")
            os.execv(__import__("sys").executable, [__import__("sys").executable, os.path.abspath(__file__)])


if __name__ == "__main__":
    load_cached()
    if not STATE["clips"]:
        threading.Thread(target=build, daemon=True).start()
    threading.Thread(target=watch_code, daemon=True).start()
    log(f"CloseCall listening on :{PORT}")
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    srv.allow_reuse_address = True
    srv.serve_forever()
