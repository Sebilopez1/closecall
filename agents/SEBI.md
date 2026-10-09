# CloseCall — Sebi's file

Real-Time Video Agents Hack NYC · Friday, October 9, 2026 · build starts 9:30 AM · submit by 4:30 PM ET

- **Part A** is for you (Sebi). The agent ignores it.
- **Part B** is the brief your build agent follows on its own, start to finish.
- **Part C** is an optional second agent you can start at 1:00 PM in another terminal.

---

## Part A — Your run sheet (human only)

**Before 8:30, on your laptop or phone**
- ✗ On github.com, create a new **public** repository called `closecall` with a README.
- ✗ In the repo: **Add file → Create new file**, type the name `agents/SEBI.md`, paste this whole file, commit. Do the same for `agents/GRANT.md`.
- ✗ **Settings → Collaborators → Add people** → add Grant's GitHub username.
- ✗ Make a GitHub token: **Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token (classic)**. Note: "closecall hackathon". Expiration: 7 days. Scope: tick **repo**. Copy it into your notes app. (Revoke it after the event.)
- ✗ Send Grant the `GRANT.md` file and tell him to accept your GitHub invite and make his own classic token the same way.

**At the event**
- ✗ 8:15 Arrive with laptop, charger and photo ID.
- ✗ 8:30 Get the passcode → open your build machine → pick the **same team number as Grant** (you only get one choice) → sign into Cursor with the email you applied with → check requests show "Free".
- ✗ 9:30 In the build machine terminal, type each line:
  ```
  cd ~/vast-builders-challenge
  git clone https://github.com/Sebilopez1/closecall
  agent
  /model
  ```
  Pick **Auto Balance**, then paste this as your first message:
  > Read closecall/agents/SEBI.md completely, then carry out Part B autonomously, start to finish. Only stop where it says STOP-AND-ASK.
- ✗ If the agent asks permission for every command, choose the option that always allows commands for this session.
- ✗ When git asks for a username and password: type your GitHub username, and paste the **token** as the password — in the terminal, never in the agent chat.
- ✗ ~10:25 The agent asks before re-checking clips with Cosmos. Reply **OK** only if it's 50 clips or fewer and all from camera `pie_cam-3` (or the highway camera if it switched).
- ✗ 10:30–11:00 Label clips 1–40 in `closecall/labels/labels_sebi.csv` using the rules at the bottom of this file. Don't look at the AI's answers. Then in the terminal: `cd ~/vast-builders-challenge/closecall && git add -A && git commit -m "sebi labels" && git push`
- ✗ ~11:20 When the agent writes **VERDICTS READY**, tell Grant.
- ✗ 12:30 Checkpoint: one close call went found → checked → approved → saved. If not, tell the agent: *"We're behind. Apply the 12:30 scope cut."*
- ✗ 1:00 Make sure Grant pushed his labels, then tell the agent: *"Labels are in. Continue with P7."*
- ✗ 3:15 Feature freeze. 3:45 Help Grant submit. 4:15 Rehearse the pitch twice.

---

## Part B — Agent brief: Pipeline agent

### Who you are
You are the **Pipeline agent** for team CloseCall at a one-day hackathon. Your human is **Sebi**. On another build machine, **Grant's App agent** builds the web app. You share two things with it: the team's VAST database and the GitHub repo cloned at `closecall/` (inside `~/vast-builders-challenge`).

### Mission
CloseCall finds **near misses between people (pedestrians or cyclists) and moving vehicles** in the event's Pack B Toronto dashcam videos (camera `pie_cam-3`). You build the part that **finds** candidate clips, **checks** them with Cosmos, **decides** a final answer per clip, and **scores** how often the system is right against human labels. Grant's app lets a person approve or reject each one.

### How to work
1. Before writing any code, read `README.md`, `ARCHITECTURE_REFERENCE.md` (if present) and every `SKILL.md` under `.cursor/skills/` (especially `ingest/` and `retrieval/`). Use those skills and their APIs. Never invent APIs.
2. Do tasks **P1 → P9 in order without waiting for Sebi between tasks.** For each task:
   - write a 3-bullet plan,
   - build it,
   - run it on 5 real clips and look at the output,
   - check the task's **Done when** line,
   - `git pull --rebase`, then commit and push,
   - append one line to `closecall/status/pipeline.md`: `HH:MM ET — P# done — <one-line result>`.
3. At the start of each task, check the time with `TZ=America/New_York date` and apply the **scope cuts** below if you're behind.
4. **STOP-AND-ASK** (stop and wait for Sebi) only when:
   - (a) you're about to re-ingest anything — show the exact segment list and wait for "OK";
   - (b) you'd delete, drop or overwrite any table or data;
   - (c) git asks for credentials;
   - (d) you're stuck for 10+ minutes after two fix attempts — summarize the problem and offer two options;
   - (e) an action would touch anything outside `closecall/` or our own `closecall_*` tables.
5. If something breaks in the environment: run the starter-kit health check ("run a git pull", then "check that everything is working"). If it's still broken, use `/ask-cosmos` and tell Sebi.

### Hard rules
- Never put keys or tokens in code, files, logs or commits. Use the environment variables that are already set (the `WANDB_` keys are preset).
- Never describe or store faces, clothing or license plates. No identifying or tracking individuals.
- Times always come from video metadata, never from model text.
- Re-ingest at most 50 segments, and only after Sebi says OK. Never re-ingest whole packs.
- Cache every model or pipeline result keyed by (segment_id, prompt_version). Never request the same answer twice.
- Plain Python, small functions, clear names. Call `weave.init("closecall")` and wrap main functions with `@weave.op`.
- Only edit: `closecall/pipeline/`, `closecall/labels/`, `closecall/notes/`, `closecall/status/pipeline.md`, `closecall/results.json`, and `closecall/README.md` (in P9 only). **Never edit `closecall/app/`.**

### Shared contract (Grant's agent depends on these exact names)
**Tables in the team VAST database**
- `closecall_candidates`: segment_id, camera_id, query, search_score, has_person, has_vehicle, passed_yolo, created_at
- `closecall_verdicts`: segment_id, camera_id, start_time, end_time, playback_link, yolo_objects, verdict, type, severity, when_in_clip, reason, final_answer, prompt_version, created_at
- `closecall_decisions` (Grant's agent creates it; read-only for you): decision_id, segment_id, action, reason, reviewer, verdict_at_decision, prompt_version, decided_at

**Allowed values:** verdict and final_answer are each one of `CLOSE_CALL`, `NO_CONFLICT`, `CANT_TELL`.

**Files**
- `closecall/notes/schema.md` — the real table and field names you discover in P1
- `closecall/labels/labels_sebi.csv` (clips 1–40) and `closecall/labels/labels_grant.csv` (clips 21–60)
- `closecall/results.json` — shaped like this:
  `{"generated_at": "...", "n_test": 0, "kappa": 0.0, "versions": [{"name": "...", "precision": {"value": 0.0, "low": 0.0, "high": 0.0, "n": 0}, "recall": {...}, "coverage": {...}}]}`
- `closecall/status/pipeline.md` (yours) and `closecall/status/app.md` (Grant's)

### Tasks

**P1 — Learn the data (9:45).** Using the retrieval skills:
- list our team's video packs and cameras;
- count the segments for camera `pie_cam-3`;
- find the real table and field names for segment id, camera, start/end time, description, YOLO objects and playback link;
- show 5 example `pie_cam-3` segments with their description and YOLO objects.

Write `closecall/notes/schema.md` with the real names and how a person opens a clip in the build machine's browser.
- **Pack switch:** if `pie_cam-3` has fewer than about 40 segments, or its descriptions rarely mention people near vehicles, switch to the highway pack's camera(s). Note the switch in `schema.md` and the status file; everything else stays the same.
- **Done when:** `schema.md` is pushed.

**P2 — Find candidates (10:00).** Create `pipeline/candidates.py`:
- Run these searches on the chosen camera: "person close to a moving vehicle", "pedestrian crossing in front of a car", "cyclist next to a moving car", "car braking for a pedestrian", "person stepping into the road".
- Keep every search hit (deduplicated, neighbouring segments merged). For each, record whether YOLO saw a person or bicycle (`has_person`) and a car, bus or truck (`has_vehicle`). `passed_yolo` = both are true.
- Save to `closecall_candidates`.
- **Done when:** the table has rows and you've printed the counts plus the top 10 hits that passed YOLO.
- **Fallback:** if the searches return junk, also add segments where YOLO alone saw a person and a vehicle (query = "yolo-only").

**P3 — Label sheets (10:15).** Create `pipeline/label_sheet.py`:
- Take the top 30 hits that passed YOLO plus 30 random segments from the same camera that are not hits. Shuffle them together and number them 1–60.
- Write `labels/labels_sebi.csv` (clips 1–40) and `labels/labels_grant.csv` (clips 21–60), with columns `number, segment_id, how_to_view, label`. `label` is blank. Don't include any model output.
- Write `labels/key.csv` (number → which list the clip came from) for scoring only.
- Copy the labeling rules from the bottom of this file into `labels/README.md`.
- Push, then write status line: `LABELS READY — Sebi 1–40, Grant 21–60`.
- **Done when:** both files are pushed and their `how_to_view` entries open a clip.

**P4 — Check candidates with Cosmos (10:25).**
- Save the Cosmos question below as `pipeline/prompts/verify_v1.txt`.
- **STOP-AND-ASK:** show the exact list of segments to re-ingest (only `passed_yolo` hits, max 50) and wait for "OK".
- Then use the ingest skill to re-ingest only those segments with that file as the prompt.
- Every 2–3 minutes, append a progress line to the status file.
- **Fallback:** if there's no progress after 15 minutes, stop waiting and apply the fallback rule below (prompt_version = "fallback").

**P5 — Read Cosmos's answers (11:00).** Create `pipeline/verdicts.py`:
- For each re-ingested segment, read the new description and pull out `VERDICT`, `TYPE`, `SEVERITY`, `WHEN` and `REASON`.
- If a description is missing or doesn't follow the format, mark it `CANT_TELL`.
- Save to `closecall_verdicts` with every contract field. Copy times, playback link and YOLO objects from the segment metadata.
- **Done when:** you've printed the count of each verdict and 5 examples.

**P6 — Final answer per clip (11:20).** Create `pipeline/decide.py`:
- `final_answer` = `CLOSE_CALL` if Cosmos said CLOSE_CALL **and** `passed_yolo`.
- `NO_CONFLICT` if Cosmos said NO_CONFLICT.
- Everything else = `CANT_TELL` (it goes to a person).
- Write `final_answer` into `closecall_verdicts`, push, and write status line: `VERDICTS READY — n CLOSE_CALL, n NO_CONFLICT, n CANT_TELL`.

**P7 — Score it (1:00).** Create `pipeline/evaluate.py`.
- First `git pull`. If either labels file still has blanks, build and test everything with a temporary fake label file, then **STOP-AND-ASK**: "Labels incomplete: N blanks."
- **Final human label:** Sebi's label for clips 1–40, Grant's for 41–60. **Tuning set** = clips 1–30, **test set** = clips 31–60. Report the test set only.
- Clips labeled `CANT_TELL` by humans are left out of precision and recall; report how many there were.
- Each version predicts CLOSE_CALL, NO_CONFLICT or CANT_TELL (abstain) for each clip:
  - **A — Search only:** any search hit = CLOSE_CALL; not a hit = NO_CONFLICT.
  - **B — Search + YOLO:** hit and `passed_yolo` = CLOSE_CALL; else NO_CONFLICT.
  - **C — Full CloseCall:** use `final_answer` for checked clips; clips that weren't checked = NO_CONFLICT.
- **Metrics:**
  - precision = correct CLOSE_CALLs ÷ predicted CLOSE_CALLs
  - recall = correct CLOSE_CALLs ÷ human CLOSE_CALLs
  - coverage = clips answered (not CANT_TELL) ÷ all test clips
  - Give each a 95% Wilson interval (z = 1.96) and its n.
- Compute Cohen's kappa between the raw Sebi and Grant labels on clips 21–40.
- Log a Weave Evaluation named `closecall-v1`. Write `closecall/results.json`.
- Write status line: `RESULTS READY`.
- **Fallback:** if Weave fails, compute the metrics locally anyway and add `"note": "Weave unavailable"` to `results.json`.

**P8 — Learn from mistakes (1:45; only if it's before 2:00).**
- Show the 5 tuning clips where version C disagreed most with the human labels: description, verdict, YOLO objects, human label.
- Propose one small wording change to the Cosmos question.
- Only if the fix is clear and it's still before 2:00: save it as `verify_v2.txt`, **STOP-AND-ASK** before re-ingesting, then redo P5–P7 with prompt_version `v2`. Keep both versions' results in `results.json`.

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
You are reviewing dashcam footage for pedestrian safety. Decide whether this clip shows a
CLOSE CALL between a person (pedestrian or cyclist) and a moving vehicle. A close call means a
person in or entering the road comes within about one car length of a moving vehicle, or
someone must react suddenly (hard braking, swerving, stopping, jumping back).
Answer in exactly this format:
VERDICT: CLOSE_CALL | NO_CONFLICT | CANT_TELL
TYPE: crossing | turning | cyclist | other | none
SEVERITY: low | medium | high | none
WHEN: early | middle | late | none
REASON: one sentence describing what happens.
If the person or vehicle is hidden, the clip is too dark or blurry, or the outcome is cut off,
answer CANT_TELL. Do not describe anyone's face, clothing or license plate.
```

**Fallback rule (if re-ingest stalls).** Use each segment's existing description:
- `CLOSE_CALL` if it mentions a person or cyclist **and** a vehicle close together, or a vehicle braking, stopping or swerving for a person.
- `NO_CONFLICT` if it mentions people only on sidewalks or far from vehicles.
- Otherwise `CANT_TELL`.
- prompt_version = "fallback".

**Labeling rules (copy into `labels/README.md`)**
- **CLOSE_CALL:** a person in or entering the road comes within about a car length of a moving vehicle, or someone has to react suddenly.
- **NO_CONFLICT:** the person is on the sidewalk or far away, the car is stopped, or there's plenty of room.
- **CANT_TELL:** hidden, dark or blurry, or the clip ends before you can see what happens.
- Label without looking at any AI output.

---

## Part C — Optional helper agent (second terminal, start at 1:00 PM)

Open a second terminal tab, type `cd ~/vast-builders-challenge` and `agent`, then paste:
> Read closecall/agents/SEBI.md Part C and do it.

**Brief for the helper agent:** You are the Docs and QA helper for team CloseCall. You may only create or edit files in `closecall/docs/` and `closecall/notes/`. Never touch pipeline code, app code or database tables. Pull before you start and push after each item.
1. Write `docs/architecture.md`: a short explanation plus a Mermaid diagram of the flow — dashcam clips → YOLO + Cosmos descriptions (provided pipeline) → find candidates → Cosmos check → final answer → approve/reject app → decisions table → evaluation. Include the three tables from the shared contract in Part B.
2. Read `closecall/pipeline/*.py` and write `notes/review.md` listing any bugs or risks you see: keys in code, timestamps taken from model text, face or plate data stored, uncached repeated calls, wrong metric math. **Report only — don't edit those files.**
3. At 3:00, read `closecall/results.json` and write `notes/results_paragraph.md`: 3 plain sentences stating the test results with ranges and n, and the kappa.
