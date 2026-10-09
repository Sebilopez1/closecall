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


def search(query):
    body = {"query": query, "top_k": TOP_K, "llm_top_n": 0, "min_similarity": MIN_SIM,
            "include_public": True}
    if TAGS:
        body["tags"] = TAGS
    if CAMERA:
        body["metadata_filters"] = {"camera_id": CAMERA}
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
    start = first(item, ["start_time", "segment_start", "start_sec", "best_match_start_sec", "start"]) \
        or first(meta, ["start_time", "segment_start"])
    end = first(item, ["end_time", "segment_end", "end_sec", "best_match_end_sec", "end"]) \
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
    return {"frames": frames, "fps": fps}


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


def analyze(c, det):
    cap = (c.get("caption") or "").lower()
    kinds = set(c.get("kinds", []))
    frames = det.get("frames", [])
    has_bike = any(kind_of(o["label"]) == "bike" for f in frames for o in f["objs"])
    has_ped = any(kind_of(o["label"]) == "person" for f in frames for o in f["objs"])
    has_veh = any(kind_of(o["label"]) == "vehicle" for f in frames for o in f["objs"])
    if not frames:
        has_bike = bool(re.search(r"cyclist|bicycl|bike", cap))
        has_ped = bool(re.search(r"pedestrian|person|people|walk", cap))
        has_veh = bool(re.search(r"car|vehicle|bus|truck|van", cap))
    who = "cyclist" if has_bike or re.search(r"cyclist|bicycl", cap) else ("pedestrian" if has_ped else "none")

    best = {"risk": 0.0, "side": "none", "veh": "Car", "t": None, "ego": False}
    for f in frames:
        vrus = [o for o in f["objs"] if kind_of(o["label"]) in ("bike", "person")]
        vehs = [o for o in f["objs"] if kind_of(o["label"]) == "vehicle" and o["conf"] >= 0.3]
        # a person sitting on a bicycle counts as a cyclist, not a separate pedestrian
        bikes = [o for o in vrus if kind_of(o["label"]) == "bike"]
        for v in vrus:
            if kind_of(v["label"]) == "person" and any(overlap(v["box"], b["box"]) > 0.2 for b in bikes):
                continue
            h = max(1e-3, v["box"][3] - v["box"][1])
            cx = (v["box"][0] + v["box"][2]) / 2
            # the dashcam car itself: a big, central person/bike box means the camera car is very close
            ego = max(0.0, min(1.0, (h - 0.22) / 0.33)) * (1.0 if abs(cx - 0.5) < 0.3 else 0.6)
            if ego > best["risk"]:
                # a cyclist rides with traffic, so the camera car is behind them; a pedestrian crosses it,
                # so the car comes from the side facing the middle of the image
                eside = "behind" if kind_of(v["label"]) == "bike" or bikes else ("left" if cx > 0.5 else "right")
                best = {"risk": ego, "side": eside, "veh": "Car", "t": f["t"], "ego": True}
            for car in vehs:
                g = gap(v["box"], car["box"]) / h          # gap measured in "person heights"
                r = max(0.0, min(1.0, 1.0 - g / 2.5))       # ~2.5 heights is about one car length
                ch = car["box"][3] - car["box"][1]
                if ch < 0.08:                                # far-away traffic doesn't count
                    r *= 0.4
                if r > best["risk"]:
                    vx = (car["box"][0] + car["box"][2]) / 2
                    dx = vx - cx
                    dy = car["box"][3] - v["box"][3]         # + = car nearer the camera than the person
                    if abs(dx) * 1.2 >= abs(dy):
                        side = "left" if dx < 0 else "right"
                    else:
                        side = "behind" if dy > 0 else "ahead"
                    best = {"risk": r, "side": side, "veh": car["label"].capitalize(), "t": f["t"], "ego": False}

    cue = bool(re.search(r"brak|swerv|sudden|abrupt|close call|near miss|almost|narrowly|cut(s|ting)? off|yield|jump", cap))
    risk = best["risk"] + (0.15 if cue else 0.0)
    severity = "high" if risk >= 0.75 else "medium" if risk >= 0.45 else "low" if risk >= 0.2 else "none"

    threat = "other"
    for k, pat in (("opening_door", r"door"), ("bus_pulling_in", r"\bbus\b"), ("turning_car", r"turn"),
                   ("close_pass", r"pass|overtak|alongside"), ("crossing_car", r"cross"), ("braking", r"brak")):
        if re.search(pat, cap):
            threat = k
            break
    if threat == "other" and kinds - {"hazard"}:
        threat = sorted(kinds - {"hazard"})[0]
    if threat == "other" and best["ego"]:
        threat = "close_pass" if who == "cyclist" else "crossing_car"

    hazard = "none"
    for k, pat in (("wires", r"wire|cable"), ("open_hole", r"\bhole\b|trench|pothole|excavat"),
                   ("equipment", r"excavator|crane|bulldozer|backhoe|forklift|heavy equipment"),
                   ("debris", r"debris|rubble|object (lying|in) the road"),
                   ("work_zone", r"construction|road ?work|work zone|cone|barrier|scaffold")):
        if re.search(pat, cap):
            hazard = k
            break

    murky = bool(re.search(r"\bdark\b|blurr|unclear|obscur|hard to see|can'?t see", cap))
    if (who == "none" and not frames and not cap) or (murky and (not frames or who != "none")):
        verdict = "CANT_TELL"
    elif who != "none" and (severity == "high" or (severity == "medium" and cue)):
        verdict = "CLOSE_CALL"
    elif who != "none" and severity == "medium":
        verdict = "CANT_TELL"
    elif not frames and who != "none" and cue:
        verdict = "CANT_TELL"
    else:
        verdict = "NO_CONFLICT"

    side = best["side"] if verdict != "NO_CONFLICT" or best["risk"] > 0.2 else "none"
    veh = "Bus" if threat == "bus_pulling_in" else best["veh"]
    if verdict == "CANT_TELL" and murky:
        warning = "Too dark or blurry to be sure. A person should check this clip."
    elif who == "none" or verdict == "NO_CONFLICT":
        warning = "No threat to anyone on a bike or on foot." if hazard == "none" else \
            "Watch the road: " + hazard.replace("_", " ") + " ahead."
    else:
        warning = THREAT_WORDS.get(threat, THREAT_WORDS["other"]).format(
            veh=veh, side=SIDE_WORDS.get(side, "")).strip() + "."
    return {"verdict": verdict, "who_at_risk": who, "threat": threat if verdict != "NO_CONFLICT" else "none",
            "threat_side": side if verdict != "NO_CONFLICT" else "none", "severity": severity,
            "risk": round(min(1.0, risk), 3), "peak_t": best["t"], "hazard": hazard, "warning": warning,
            "has_detections": bool(frames), "cue": cue}


# ---------------------------------------------------------------- build the clip list
def build():
    with _lock:
        if STATE["status"] == "running":
            return
        STATE.update(status="running", started=now_iso(), error=None)
    try:
        login(force=True)
        found = {}
        for kind, q in RIDER_QUERIES + HAZARD_QUERIES:
            try:
                res = search(q)
            except Exception as e:  # keep going with the other searches
                log(f"search failed for '{q}': {e}")
                continue
            items = (res or {}).get("results") or []
            log(f"search '{q}': {len(items)} hits")
            for it in items:
                f = clip_fields(it)
                if not f["source"]:
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
            json.dump(clips, fh)
        STATE.update(status="ready", finished=now_iso())
        log(f"ready: {len(clips)} clips")
    except Exception as e:
        STATE.update(status="error", error=f"{e}", finished=now_iso())
        log("build failed: " + traceback.format_exc()[-600:])


def load_cached():
    p = os.path.join(DATA_DIR, "clips.json")
    if os.path.exists(p):
        try:
            STATE["clips"] = json.load(open(p))
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


def accuracy():
    labels = [r for r in read_jsonl("labels.jsonl") if r.get("labeler", "").lower() != "test"]
    by_clip = {}
    for r in labels:
        by_clip.setdefault(r["clip_id"], {})[r["labeler"]] = r["label"]   # last label per labeler wins
    clips = {c["id"]: c for c in STATE["clips"]}
    labelers = sorted({r["labeler"] for r in labels})
    rows = []
    for cid, per in by_clip.items():
        if cid not in clips:
            continue
        human = per[sorted(per)[0]]                                    # first labeler alphabetically
        rows.append((human, clips[cid]["analysis"]["verdict"], clips[cid]))

    def score(pred_of):
        tp = sum(1 for h, _, c in rows if h == "CLOSE_CALL" and pred_of(c) == "CLOSE_CALL")
        pp = sum(1 for h, _, c in rows if h != "CANT_TELL" and pred_of(c) == "CLOSE_CALL")
        hp = sum(1 for h, _, c in rows if h == "CLOSE_CALL")
        ans = sum(1 for h, _, c in rows if pred_of(c) != "CANT_TELL")
        return {"precision": wilson(tp, pp), "recall": wilson(sum(1 for h, _, c in rows if h == "CLOSE_CALL" and pred_of(c) == "CLOSE_CALL"), hp),
                "coverage": wilson(ans, len(rows))}

    versions = [
        {"name": "A — search only", **score(lambda c: "CLOSE_CALL" if c["kinds"] and c["kinds"] != ["hazard"] else "NO_CONFLICT")},
        {"name": "C — CloseCall (Cosmos + YOLO rider check)", **score(lambda c: c["analysis"]["verdict"])},
    ]
    k = None
    if len(labelers) >= 2:
        a_lab, b_lab = labelers[0], labelers[1]
        both = [(p[a_lab], p[b_lab]) for p in by_clip.values() if a_lab in p and b_lab in p]
        k = {"labelers": [a_lab, b_lab], "n": len(both), "kappa": kappa([x for x, _ in both], [y for _, y in both])}
    return {"n_labeled": len(rows), "human_cant_tell": sum(1 for h, _, _ in rows if h == "CANT_TELL"),
            "labelers": labelers, "kappa": k, "versions": versions}


# ---------------------------------------------------------------- HTTP
def public_clip(c, blind=False):
    out = {k: c.get(k) for k in ("id", "source", "original_video", "camera_id", "location", "start", "end",
                                  "similarity")}
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
                done = {r["clip_id"] for r in read_jsonl("labels.jsonl") if r.get("labeler", "").lower() == who}
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
                       "prompt_version": "rider_v1", "decided_at": now_iso()}
                append_jsonl("decisions.jsonl", row)
                return self.send_json({"ok": True, "decision": row})
            if p == "/api/label":
                if not clip or b.get("label") not in ("CLOSE_CALL", "NO_CONFLICT", "CANT_TELL") or not b.get("labeler"):
                    return self.send_json({"error": "need clip_id, label and labeler"}, 400)
                append_jsonl("labels.jsonl", {"clip_id": clip["id"], "label": b["label"],
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
