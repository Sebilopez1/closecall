# CloseCall — Teammate 4: App tabs, Story & Submission

Real-Time Video Agents Hack NYC · build 9:30 AM · submit by 4:30 PM ET

**Your job:** your agent builds three of the app's tabs (Decision log, Accuracy, Data & Limits) and the counter row while you label clips, keep the team's clock and make sure we submit on time. Part A (this top part) is for you; Part B at the bottom is your agent's brief.

**What we're building (1 line):** CloseCall gives people on bikes and on foot Tesla-style eyes: it finds near misses with cars in dashcam video, shows who was at risk and where the threat came from, lets a person approve or reject each one, and reports how often it's right.

---

## Setup
- ✗ Accept the invite to the GitHub repo `Sebilopez1/closecall` (check your email or github.com/notifications).
- ✗ Make a GitHub token: **Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token (classic)**. Expiration: 7 days. Scope: tick **repo**. Copy it into your notes. (Revoke it after the event.)
- ✗ On your build machine, pick the **same team number as the rest of the team** (you only get one choice) so you share one database. Then, in the terminal (not the agent chat):
  ```
  cd ~/vast-builders-challenge
  git clone https://github.com/Sebilopez1/closecall
  git config --global credential.helper 'cache --timeout=36000'
  cd closecall && git push
  ```
  Username: your GitHub username. Password: paste the token. Then type `cd ..`, `agent` and `/model` → **Auto Balance**, and paste:
  > Read closecall/agents/TEAMMATE4.md completely, then carry out Part B autonomously, start to finish. Only stop where it says STOP-AND-ASK.
- ✗ While you label, don't read your agent's screen: it may show the AI's answers.
- ✗ Install Loom (or know your screen recorder) and test a 30-second recording with your voice.
- ✗ Read the pitch and the demo script below.
- ✗ Confirm with the organizers whether 4:30 is the submission **deadline** or when submissions **open**, and the demo video length limit. Tell the team.

## Build day
- ✗ **Timekeeper.** Set these phone alarms, and at each one ask the team its question:

| Alarm | Question to ask the team |
|---|---|
| 10:00 | Is the dashcam footage there? If not, switch to highway footage now. |
| 11:00 | Are all labels committed? |
| 12:30 | Has one close call gone all the way: found → checked → approved → saved? If not, cut extras. |
| 2:00 | No new feature ideas from here on. |
| 3:15 | **Freeze.** Only fixes from now on. Record the video. |
| 3:45 | Video link and public repo ready? Submit. |
| 4:15 | Submitted? Screenshot taken? Rehearse twice. |

- ✗ **~10:15, when Teammate 1 says "LABELS READY":** you label **clips 21–60**:
  1. Open `github.com/Sebilopez1/closecall/blob/main/labels/labels_teammate4.csv` and tap the **pencil (Edit)** icon.
  2. Each line looks like `27,seg_123,<how to view>,`. Watch that clip, then type the label right after the last comma: `CLOSE_CALL`, `NO_CONFLICT` or `CANT_TELL` (exact spelling, no spaces; rules below).
  3. Tap **Commit changes** every 10 clips. When you're done, tell your agent "labels done".
  - Don't look at the AI's answers, and don't discuss labels with Teammate 3 until you're both done. Your overlap (clips 21–40) measures agreement.
- ✗ **11:00–3:00, story:**
  - Write the submission text in your notes: project name, description (the pitch below), tools used (list below), repo link, all four names and emails.
  - Practice the 60-second pitch and the 3-minute demo with Teammate 1 at lunch.
  - When Teammate 1 says "RESULTS READY", fill the X and Y in the pitch, plus the demo numbers (N, P0, P, R, C).
  - Prepare answers to the judge questions below.
- ✗ **3:15, record the demo video** (3 minutes max). Teammate 2 clicks through the app while you record, following the demo script. Upload it (Loom, or YouTube as unlisted), then check the link works in a private browser window.
- ✗ **3:45, submit** at tokensand.com/vastnyc → **Submit your project**:
  - repo link: github.com/Sebilopez1/closecall
  - demo video link
  - description and tools used
  - all four names and emails

  Screenshot the confirmation and send it to the team.
- ✗ **Judging:** lead the 60-second pitch while Teammate 2 shows the app.

## Pitch (the submission description)
Cars get more cameras and sensors every year; people on bikes still get a bell. In 2024, 1,103 cyclists were killed on US roads (NHTSA), mostly in moments a rider can't see coming: a car turning across the bike lane, a door opening, a car passing too close, a bus pulling in. CloseCall gives people on bikes and on foot Tesla-style eyes. It watches street footage on their behalf and, for each moment, says who was at risk, what the threat was and which side it came from, shown as a simple rider view with a one-line warning. A safety manager approves or rejects each one, and every decision is saved with its evidence. It also flags construction hazards like exposed wires and open holes, says "can't tell" when the video is unclear instead of guessing, and measures how often it's right: correct X% of the time, give or take Y, on clips we labeled by hand. Today we prove it on street footage; next it runs on a phone or helmet camera and warns riders live. It looks at places and patterns, never people: no face recognition, no license plates, no tracking.

**Tools used:** NVIDIA Cosmos Reason (via the VAST video pipeline) to check each clip · Cosmos Embed + VAST semantic search to find moments · YOLO11 for person and vehicle detection · VAST DataEngine and VastDB as the system of record · W&B Weave for evaluation and tracing · CoreWeave GPUs hosting the models and our app · Cursor.

## Demo script (3 minutes)
- 0:00 **Teammate 1:** "Tesla gives cars eyes. People on bikes get a bell. In 2024, 1,103 cyclists were killed on US roads. CloseCall gives riders and walkers the same eyes."
- 0:25 **Teammate 2:** Review tab → open a real cyclist clip → the Rider view shows the threat and the side it comes from, with Cosmos's one-line warning → type a reason → **Approve** → Decision log shows the saved record: who, when, which prompt version.
- 1:05 **Teammate 2:** an "Unclear — needs a person" clip: "When the video can't settle it, CloseCall says so instead of guessing."
- 1:20 **Teammate 2:** a work-zone hazard clip: "It also flags exposed wires, open holes and debris."
- 1:35 **Teammate 1:** Accuracy tab: "On N clips we labeled by hand, search alone was right P0% of the time. With our checks it's P%, give or take R, and it says can't tell on C%."
- 2:15 **Teammate 1:** Data & Limits tab: "No faces, no plates, no tracking. Places and patterns, not people."
- 2:35 **Teammate 2:** "Next: the same eyes on a phone or helmet camera, warning riders live, starting with delivery and bike-share fleets. Every ride adds to a map of dangerous streets for cities."

## Judge questions and answers
- **How accurate is it?** "On N clips two of us labeled blind, precision is P with this range, and it says 'can't tell' on C% and sends those to a person."
- **Why not just trust the AI?** "We measured it: our checks raised precision from P0 to P. When it's unsure, a human decides."
- **Do near misses matter?** "Bellevue, Washington analyzed about 5,000 hours of intersection video and found near-crashes accurately predict where future crashes happen."
- **Why bikes?** "Cars keep getting new sensors; riders get almost none. In 2024, 1,103 cyclists were killed on US roads. Radar taillights only see what's behind you; a camera that understands the scene can tell a car is about to turn or a door is about to open."
- **Is this real-time?** "Today we run recorded clips through the event's video pipeline. The phone version runs detection on the device and warns the rider live."
- **Who would use it?** "Riders first, through delivery and bike-share fleets that ride all day. Cities get a map of dangerous streets from every ride. Helmet and e-bike makers can license it."
- **What did you build versus what was provided?** "The event provided the video pipeline and models. We built the candidate finder, the Cosmos check and decision rule, the approval app with decision history, and the accuracy test."
- **Privacy?** "No faces, no plates, no tracking people. Only places and patterns."
- **What happens when it's wrong?** "A person rejects it, the rejection is logged, and it becomes a new test case."
- **What's next?** "Run it on a phone or helmet camera with live warnings, score the rider-view answers against hand labels, then pilot with one delivery or bike-share fleet."

## Labeling rules
- **CLOSE_CALL:** a person in or entering the road comes within about one car length of a moving vehicle, or someone has to react suddenly.
- **NO_CONFLICT:** on the sidewalk or far away, the car is stopped, or there's plenty of room.
- **CANT_TELL:** hidden, too dark or blurry, or the clip ends too soon.
- A hazard with no close call (wires, a hole, debris) is `NO_CONFLICT`. Hazards aren't labeled today.

---

## Part B — Agent brief: Tabs agent

### Who you are
You are the **Tabs agent** for team CloseCall at a one-day hackathon. Your human is **Teammate 4**. Three other agents share the team's VAST database and the GitHub repo cloned at `closecall/` (inside `~/vast-builders-challenge`): **Teammate 2's App agent** owns the app shell, the Review tab and the decisions table, and is the **only one who deploys**; **Teammate 1's Pipeline agent** writes the clip tables; **Teammate 3's Scoring agent** writes `results.json`.

### Mission
Build three of the app's four tabs (**Decision log**, **Accuracy** and **Data & Limits**) plus the **counter row**, each in its own file that the app shell imports.

### How to work
1. Before writing any code, read `README.md`, `ARCHITECTURE_REFERENCE.md` (if present) and every `SKILL.md` under `.cursor/skills/`, especially the database and deploy skills, so you use the same framework as the app. Never invent APIs.
2. `git pull` and read `closecall/status/app.md`. Teammate 2's agent writes `SHELL READY — tabs in app/tabs/` once the app has one file per tab. Until then, build your parts against stand-in data in the framework the deploy skill expects.
3. Do tasks **T1 → T5 in order without waiting for Teammate 4 between tasks.** For each task:
   - write a 3-bullet plan,
   - build it,
   - run the app on your own machine to test it (never deploy),
   - check the task's **Done when** line,
   - `git pull --rebase`, then commit and push,
   - append one line to `closecall/status/tabs.md`: `HH:MM ET — T# done — <one-line result>`, then a line `TABS UPDATED` so Teammate 2's agent redeploys.
4. **STOP-AND-ASK** (stop and wait for Teammate 4) only when:
   - (a) you'd delete, drop or overwrite any table or data;
   - (b) git asks for credentials;
   - (c) you're stuck for 10+ minutes after two fix attempts — summarize the problem and offer two options;
   - (d) an action would touch anything outside `closecall/`.
5. If something breaks in the environment: run the starter-kit health check ("run a git pull", then "check that everything is working"). If it's still broken, use `/ask-cosmos` and tell Teammate 4.

### Hard rules
- **Blind labeling:** Teammate 4 labels clips until about 11:00. Until Teammate 4 says "labels done", never show Cosmos verdicts or reasons in your replies.
- Never deploy. Only Teammate 2's agent deploys.
- Never put keys or tokens in code, files, logs or commits. Use the environment variables that are already set.
- No face recognition, no license plates, no identifying or tracking people.
- Never write to the database. You only read tables.
- Decisions made with reviewer name `test` are for testing. Hide them everywhere.
- Only edit: `closecall/app/tabs/decision_log.*`, `closecall/app/tabs/accuracy.*`, `closecall/app/tabs/data_limits.*`, `closecall/app/tabs/counters.*`, `closecall/status/tabs.md`. **Never edit anything else.** If you need a change in the shell, add a line `REQUEST: ...` to `status/tabs.md` for Teammate 2's agent.

### Shared contract (read only)
- `closecall_verdicts`: segment_id, camera_id, start_time, end_time, playback_link, yolo_objects, verdict, type, severity, when_in_clip, who_at_risk, threat, threat_side, hazard, reason, final_answer, prompt_version, created_at
- `closecall_decisions`: decision_id, segment_id, action (approve or reject), reason, reviewer, verdict_at_decision, prompt_version, decided_at
- `closecall/results.json` (Teammate 3's agent writes it) — shaped like this:
  `{"generated_at": "...", "n_test": 0, "kappa": 0.0, "hazards_found": {"wires": 0}, "versions": [{"name": "...", "precision": {"value": 0.0, "low": 0.0, "high": 0.0, "n": 0}, "recall": {...}, "coverage": {...}}]}`
- `closecall/notes/schema.md` — the real table and field names

### Tasks

**T1 — Data & Limits tab (10:15).** Show exactly the text below. **Done when:** it renders locally.

**T2 — Decision log tab (10:30).** A table of every real decision (hide reviewer `test`) with segment, action, verdict at decision, prompt version, reviewer, time and reason. Newest first. With no rows yet, show "No decisions yet." **Done when:** it renders with real or stand-in rows.

**T3 — Counter row (11:00).** clips checked · close calls found · hazards found · waiting for review · decisions made, counted from `closecall_verdicts` and `closecall_decisions` (ignore reviewer `test`). **Done when:** the numbers match a manual count.

**T4 — Accuracy tab (as soon as `status/scoring.md` says RESULTS READY; until then show "Results will appear here after scoring").**
- Pull first and read `closecall/results.json`.
- Show a table of the versions with precision, recall and coverage, each written as `value (low–high), n=…`. Also show n_test, kappa and hazards found by type.
- Under it: "Measured on our hand-labeled test clips. Ranges are 95% intervals. Hazard tags aren't scored yet."

**T5 — Polish (2:30).** Match the Review tab's look: even spacing, readable fonts, no clutter. Push and write `TABS UPDATED`. At 3:00, write `TABS FROZEN`.

### Data & Limits text
```
CloseCall looks at places and patterns, never people: no face recognition, no license plates,
no tracking anyone. Raw video stays in VAST; only events and decisions are saved. Every action
is approved by a person and logged. Limits: tested on a small hand-labeled set of dashcam
clips; Cosmos can misjudge fast, dark or hidden scenes, so unclear clips go to a person.
Hazard tags are Cosmos's reading of the clip and are not yet scored against hand labels.
```
