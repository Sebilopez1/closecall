# CloseCall — Teammate 1: Pipeline (find, check, score)

Real-Time Video Agents Hack NYC · build 9:30 AM · submit by 4:30 PM ET

- **Part A** is for you (Teammate 1). The agent ignores it.
- **Part B** is the brief your build agent follows on its own, start to finish.
- **Part C** is an optional second agent you can start at 1:00 PM in another terminal.

---

## Part A — Your run sheet (human only)

**Before the build**
- ✗ Make a GitHub token so your build machine can save code: **Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token (classic)**. Expiration: 7 days. Scope: tick **repo**. Copy it into your notes. (Revoke it after the event.)

**Build day**
- ✗ Open your build machine with the event passcode → pick the **same team number as the rest of the team** (you only get one choice) → sign into Cursor with the email you applied with → check requests show "Free".
- ✗ 9:30 In the build machine terminal, type each line:
  ```
  cd ~/vast-builders-challenge
  git clone https://github.com/Sebilopez1/closecall
  agent
  /model
  ```
  Pick **Auto Balance**, then paste this as your first message:
  > Read closecall/agents/TEAMMATE1.md completely, then carry out Part B autonomously, start to finish. Only stop where it says STOP-AND-ASK.
- ✗ If the agent asks permission for every command, choose the option that always allows commands for this session.
- ✗ When git asks for a username and password: type your GitHub username, and paste the **token** as the password — in the terminal, never in the agent chat.
- ✗ ~10:15 When the agent writes **LABELS READY**, tell Teammates 3 and 4 to start labeling.
- ✗ ~10:25 The agent asks before re-checking clips with Cosmos. Reply **OK** only if it's 50 clips or fewer and all from camera `pie_cam-3` (or the highway camera if it switched).
- ✗ ~11:20 When the agent writes **VERDICTS READY**, tell Teammate 2.
- ✗ 12:30 Checkpoint: one close call went found → checked → approved → saved. If not, tell the agent: *"We're behind. Apply the 12:30 scope cut."*
- ✗ ~1:15 When Teammate 3 says **RESULTS READY**, check that your agent moved on to P8.
- ✗ ~1:45 Review the 5 worst mistakes (`notes/mistakes.md`) together with Teammate 3.
- ✗ 3:15 Feature freeze.

---

## Part B — Agent brief: Pipeline agent

### Who you are
You are the **Pipeline agent** for team CloseCall at a one-day hackathon. Your human is **Teammate 1**. On another build machine, **Teammate 2's App agent** builds the web app. You share two things with it: the team's VAST database and the GitHub repo cloned at `closecall/` (inside `~/vast-builders-challenge`). **Teammate 3's Scoring agent** owns accuracy scoring (`pipeline/evaluate.py`, `results.json`), and **Teammate 4's Tabs agent** builds three of the app's tabs. Teammates 3 and 4 also write the human labels.

### Mission
CloseCall gives **people on bikes and on foot Tesla-style eyes**: it finds **near misses between cyclists or pedestrians and moving vehicles** in the event's Pack B Toronto dashcam videos (camera `pie_cam-3`), and says who was at risk, what the threat was and which side it came from. You build the part that **finds** candidate clips, **checks** them with Cosmos and **decides** a final answer per clip; Teammate 3's agent **scores** how often the system is right against human labels (near misses only). CloseCall also flags **work-zone hazards**: construction areas next to traffic or walkways, exposed wires or cables, open holes or trenches, debris in the road, or heavy equipment near people. Teammate 2's app lets a person approve or reject each one.

### How to work
1. Before writing any code, read `README.md`, `ARCHITECTURE_REFERENCE.md` (if present) and every `SKILL.md` under `.cursor/skills/` (especially `ingest/` and `retrieval/`). Use those skills and their APIs. Never invent APIs.
2. Do tasks **P1 → P9 in order without waiting for Teammate 1 between tasks.** For each task:
   - write a 3-bullet plan,
   - build it,
   - run it on 5 real clips and look at the output,
   - check the task's **Done when** line,
   - `git pull --rebase`, then commit and push,
   - append one line to `closecall/status/pipeline.md`: `HH:MM ET — P# done — <one-line result>`.
3. At the start of each task, check the time with `TZ=America/New_York date` and apply the **scope cuts** below if you're behind.
4. **STOP-AND-ASK** (stop and wait for Teammate 1) only when:
   - (a) you're about to re-ingest anything — show the exact segment list and wait for "OK";
   - (b) you'd delete, drop or overwrite any table or data;
   - (c) git asks for credentials;
   - (d) you're stuck for 10+ minutes after two fix attempts — summarize the problem and offer two options;
   - (e) an action would touch anything outside `closecall/` or our own `closecall_*` tables.
5. If something breaks in the environment: run the starter-kit health check ("run a git pull", then "check that everything is working"). If it's still broken, use `/ask-cosmos` and tell Teammate 1.

### Hard rules
- Never put keys or tokens in code, files, logs or commits. Use the environment variables that are already set (the `WANDB_` keys are preset).
- Never describe or store faces, clothing or license plates. No identifying or tracking individuals.
- Times always come from video metadata, never from model text.
- Re-ingest at most 50 segments, and only after Teammate 1 says OK. Never re-ingest whole packs.
- Cache every model or pipeline result keyed by (segment_id, prompt_version). Never request the same answer twice.
- Plain Python, small functions, clear names. Call `weave.init("closecall")` and wrap main functions with `@weave.op`.
- Only edit: `closecall/pipeline/` (except `pipeline/evaluate.py`), `closecall/labels/`, `closecall/notes/` (except `notes/mistakes.md`), `closecall/status/pipeline.md`, and `closecall/README.md` (in P9 only). **Never edit `closecall/app/`, `pipeline/evaluate.py` or `closecall/results.json`.**

### Shared contract (Teammate 2's agent depends on these exact names)
**Tables in the team VAST database**
- `closecall_candidates`: segment_id, camera_id, query, kind, search_score, has_person, has_vehicle, passed_yolo, created_at
- `closecall_verdicts`: segment_id, camera_id, start_time, end_time, playback_link, yolo_objects, verdict, type, severity, when_in_clip, who_at_risk, threat, threat_side, hazard, reason, final_answer, prompt_version, created_at
- `closecall_decisions` (Teammate 2's agent creates it; read-only for you): decision_id, segment_id, action, reason, reviewer, verdict_at_decision, prompt_version, decided_at

**Allowed values:** verdict and final_answer are each one of `CLOSE_CALL`, `NO_CONFLICT`, `CANT_TELL`. kind is `close_call` or `hazard`. hazard is one of `none`, `work_zone`, `wires`, `open_hole`, `debris`, `equipment`, `other`. who_at_risk is `cyclist`, `pedestrian` or `none`. threat is one of `turning_car`, `opening_door`, `close_pass`, `bus_pulling_in`, `crossing_car`, `other`, `none`. threat_side is `left`, `right`, `ahead`, `behind` or `none` (where the threat comes from, as seen by the person at risk).

**Files**
- `closecall/notes/schema.md` — the real table and field names you discover in P1
- `closecall/labels/labels_teammate3.csv` (clips 1–40) and `closecall/labels/labels_teammate4.csv` (clips 21–60)
- `closecall/results.json` (Teammate 3's agent writes it) — shaped like this:
  `{"generated_at": "...", "n_test": 0, "kappa": 0.0, "versions": [{"name": "...", "precision": {"value": 0.0, "low": 0.0, "high": 0.0, "n": 0}, "recall": {...}, "coverage": {...}}]}`
- Status files: `closecall/status/pipeline.md` (yours), `status/app.md` (Teammate 2's), `status/scoring.md` (Teammate 3's), `status/tabs.md` (Teammate 4's)

### Tasks

**P1 — Learn the data (9:45).** Using the retrieval skills:
- list our team's video packs and cameras;
- count the segments for camera `pie_cam-3`;
- find the real table and field names for segment id, camera, start/end time, description, YOLO objects and playback link;
- show 5 example `pie_cam-3` segments with their description and YOLO objects;
- count how many `pie_cam-3` descriptions mention construction, road work, cones, barriers, wires or cables, holes or trenches, debris, or heavy equipment.

Write `closecall/notes/schema.md` with the real names and how a person opens a clip in a browser (both on the build machine and, if possible, from a laptop at workshop.thecosmoslabs.com).
- **Pack switch:** if `pie_cam-3` has fewer than about 40 segments, or its descriptions rarely mention people near vehicles, switch to the highway pack's camera(s). Note the switch in `schema.md` and the status file; everything else stays the same.
- **Done when:** `schema.md` is pushed.

**P2 — Find candidates (10:00).** Create `pipeline/candidates.py`:
- Run these **close-call** searches on the chosen camera (kind = `close_call`): "person close to a moving vehicle", "pedestrian crossing in front of a car", "cyclist next to a moving car", "car braking for a pedestrian", "person stepping into the road", "car door opening next to a cyclist", "car passing close to a cyclist", "car turning right across a bike lane", "bus pulling over in front of a cyclist".
- Run these **hazard** searches too (kind = `hazard`): "construction zone next to traffic", "road workers near moving cars", "exposed wires or cables near the road", "debris or object lying in the road", "open hole or trench near the road or sidewalk", "heavy construction equipment near pedestrians".
- Keep every search hit (deduplicated, neighbouring segments merged). For each, record whether YOLO saw a person or bicycle (`has_person`) and a car, bus or truck (`has_vehicle`). `passed_yolo` = both are true. YOLO can't see cones, wires or holes, so hazard hits don't need `passed_yolo`.
- Save to `closecall_candidates`.
- **Done when:** the table has rows and you've printed the counts plus the top 10 close-call hits that passed YOLO and the top 5 hazard hits.
- **Fallback:** if the searches return junk, also add segments where YOLO alone saw a person and a vehicle (query = "yolo-only").

**P3 — Label sheets (10:15).** Create `pipeline/label_sheet.py`:
- Take the top 30 close-call hits that passed YOLO plus 30 random segments from the same camera that are not hits. Shuffle them together and number them 1–60.
- Write `labels/labels_teammate3.csv` (clips 1–40) and `labels/labels_teammate4.csv` (clips 21–60), with columns `number, segment_id, how_to_view, label`. `label` is blank. Don't include any model output. Teammates 3 and 4 fill them in through GitHub's web editor, so keep each row on one line with no extra commas inside fields.
- Write `labels/key.csv` (number → which list the clip came from) for scoring only.
- Copy the labeling rules from the bottom of this file into `labels/README.md`.
- Push, then write status line: `LABELS READY — Teammate 3: clips 1–40, Teammate 4: clips 21–60`.
- **Done when:** both files are pushed and their `how_to_view` entries open a clip.

**P4 — Check candidates with Cosmos (10:25).**
- Save the Cosmos question below as `pipeline/prompts/verify_v1.txt`.
- **STOP-AND-ASK:** show the exact list of segments to re-ingest (close-call hits that passed YOLO plus up to 10 top hazard hits, max 50 total) and wait for "OK".
- Then use the ingest skill to re-ingest only those segments with that file as the prompt.
- Every 2–3 minutes, append a progress line to the status file.
- **Fallback:** if there's no progress after 15 minutes, stop waiting and apply the fallback rule below (prompt_version = "fallback").

**P5 — Read Cosmos's answers (11:00).** Create `pipeline/verdicts.py`:
- For each re-ingested segment, read the new description and pull out `VERDICT`, `WHO`, `THREAT`, `SIDE`, `TYPE`, `SEVERITY`, `WHEN`, `HAZARD` and `REASON` (WHO → `who_at_risk`, THREAT → `threat`, SIDE → `threat_side`).
- If a description is missing or doesn't follow the format, mark it `CANT_TELL`. If the WHO, THREAT, SIDE or HAZARD line is missing, use `none`.
- Save to `closecall_verdicts` with every contract field. Copy times, playback link and YOLO objects from the segment metadata.
- **Done when:** you've printed the count of each verdict, the count of each hazard type, and 5 examples.

**P6 — Final answer per clip (11:20).** Create `pipeline/decide.py`:
- `final_answer` = `CLOSE_CALL` if Cosmos said CLOSE_CALL **and** `passed_yolo`.
- `NO_CONFLICT` if Cosmos said NO_CONFLICT.
- Everything else = `CANT_TELL` (it goes to a person).
- Keep `hazard` as Cosmos reported it. Any clip with a hazard other than `none` also goes to the app's review queue.
- Write `final_answer` into `closecall_verdicts`, push, and write status line: `VERDICTS READY — n CLOSE_CALL, n NO_CONFLICT, n CANT_TELL, n hazards`.

**P7 — Hand off to scoring (1:00).** Scoring is Teammate 3's job now; don't write `evaluate.py`.
- Make sure `closecall_candidates`, `closecall_verdicts` and `labels/key.csv` are complete and pushed, then write status line: `READY FOR SCORING`.
- If `status/scoring.md` says `EVALUATE READY` (Teammate 3's machine can't read the database), run `python pipeline/evaluate.py` yourself and push `results.json`.
- Continue with P8 when `status/scoring.md` says `RESULTS READY`.

**P8 — Learn from mistakes (1:45; only if it's before 2:00).**
- Read `notes/mistakes.md` (Teammate 3's agent lists the 5 tuning clips where version C disagreed most with the human labels) and show them: description, verdict, YOLO objects, human label.
- Propose one small wording change to the Cosmos question.
- Only if the fix is clear and it's still before 2:00: save it as `verify_v2.txt`, **STOP-AND-ASK** before re-ingesting, then redo P5–P6 with prompt_version `v2` and write status line `V2 VERDICTS READY` so Teammate 3's agent re-scores both versions.

**P9 — README and freeze (3:15).**
- Write `closecall/README.md` with these sections:
  - what CloseCall does (use `closecall/pitch.md`)
  - how it works in 4 steps: find, check, approve, score
  - the results table from `results.json`, with ranges and n
  - limits and privacy
  - what the event provided (video pipeline, YOLO11, Cosmos, VAST search and database, W&B) versus what we built
  - how to run it
- Then search the whole repo for anything that looks like a key or token and report what you find.
- Final push. Write status line: `FROZEN`.

### Scope cuts (apply on your own)
- **12:30 and no VERDICTS READY yet:** skip P8. If the re-ingest is still running, switch to the fallback rule.
- **After 2:00:** no new prompt versions.
- **3:15:** feature freeze — only fixes, README and results.

### Texts

**Cosmos question → `pipeline/prompts/verify_v1.txt`**
```
You are a safety co-pilot for people on bikes and on foot, watching this street footage.
First, decide whether this clip shows a CLOSE CALL between a person (cyclist or pedestrian)
and a moving vehicle. A close call means a person in or entering the road comes within about
one car length of a moving vehicle, or someone must react suddenly (hard braking, swerving,
stopping, jumping back).
Second, from the point of view of the person at risk, say what the threat is and which side
it comes from: a car turning across their path, a car door opening, a car passing too close,
a bus pulling in, or a car crossing in front.
Third, note any WORK-ZONE HAZARD you can clearly see: a construction area next to traffic or
a walkway, exposed wires or cables, an open hole or trench, debris or objects lying in the
road, or heavy equipment operating near people or traffic.
Answer in exactly this format:
VERDICT: CLOSE_CALL | NO_CONFLICT | CANT_TELL
WHO: cyclist | pedestrian | none
THREAT: turning_car | opening_door | close_pass | bus_pulling_in | crossing_car | other | none
SIDE: left | right | ahead | behind | none
TYPE: crossing | turning | cyclist | other | none
SEVERITY: low | medium | high | none
WHEN: early | middle | late | none
HAZARD: none | work_zone | wires | open_hole | debris | equipment | other
REASON: one sentence. If there is a threat, write it as a warning to the person at risk
(for example: Car turning right across your path.).
If the person or vehicle is hidden, the clip is too dark or blurry, or the outcome is cut off,
answer CANT_TELL. If you can't clearly see a hazard, answer HAZARD: none.
Do not describe anyone's face, clothing or license plate.
```

**Fallback rule (if re-ingest stalls).** Use each segment's existing description:
- `CLOSE_CALL` if it mentions a person or cyclist **and** a vehicle close together, or a vehicle braking, stopping or swerving for a person.
- `NO_CONFLICT` if it mentions people only on sidewalks or far from vehicles.
- Otherwise `CANT_TELL`.
- `hazard`: `work_zone` if it mentions construction or road work, `wires` for wires or cables, `open_hole` for a hole or trench, `debris` for debris or objects in the road, `equipment` for an excavator, crane or other heavy machinery; otherwise `none`.
- `who_at_risk`: `cyclist` if it mentions a cyclist or bike, `pedestrian` if it mentions a person on foot, otherwise `none`. `threat` = `other` and `threat_side` = `none` unless the description makes them obvious.
- prompt_version = "fallback".

**Labeling rules (copy into `labels/README.md`)**
- **CLOSE_CALL:** a person in or entering the road comes within about a car length of a moving vehicle, or someone has to react suddenly.
- **NO_CONFLICT:** the person is on the sidewalk or far away, the car is stopped, or there's plenty of room.
- **CANT_TELL:** hidden, dark or blurry, or the clip ends before you can see what happens.
- Label without looking at any AI output.

---

## Part C — Optional helper agent (second terminal, start at 1:00 PM)

Open a second terminal tab, type `cd ~/vast-builders-challenge` and `agent`, then paste:
> Read closecall/agents/TEAMMATE1.md Part C and do it.

**Brief for the helper agent:** You are the Docs and QA helper for team CloseCall. You may only create or edit files in `closecall/docs/` and `closecall/notes/`. Never touch pipeline code, app code or database tables. Pull before you start and push after each item.
1. Write `docs/architecture.md`: a short explanation plus a Mermaid diagram of the flow — dashcam clips → YOLO + Cosmos descriptions (provided pipeline) → find candidates → Cosmos check → final answer → approve/reject app → decisions table → evaluation. Include the three tables from the shared contract in Part B.
2. Read `closecall/pipeline/*.py` and write `notes/review.md` listing any bugs or risks you see: keys in code, timestamps taken from model text, face or plate data stored, uncached repeated calls, wrong metric math. **Report only — don't edit those files.**
3. At 3:00, read `closecall/results.json` and write `notes/results_paragraph.md`: 3 plain sentences stating the test results with ranges and n, and the kappa.
