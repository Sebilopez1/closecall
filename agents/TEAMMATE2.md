# CloseCall — Teammate 2: App (review, decisions, accuracy)

Real-Time Video Agents Hack NYC · build 9:30 AM · submit by 4:30 PM ET

- **Part A** is for you (Teammate 2). The agent ignores it.
- **Part B** is the brief your build agent follows on its own, start to finish.
- **Part C** is an optional second agent you can start at 2:30 PM in another terminal.

---

## Part A — Your run sheet (human only)

**Before the build**
- ✗ Accept the invite to the GitHub repo `Sebilopez1/closecall` (check your email or github.com/notifications).
- ✗ Make a GitHub token so your build machine can save code: **Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token (classic)**. Expiration: 7 days. Scope: tick **repo**. Copy it into your notes. (Revoke it after the event.)

**Build day**
- ✗ Open your build machine with the event passcode → pick the **same team number as Teammate 1** (you only get one choice) → sign into Cursor with the email you applied with → check requests show "Free".
- ✗ 9:30 In the build machine terminal, type each line:
  ```
  cd ~/vast-builders-challenge
  git clone https://github.com/Sebilopez1/closecall
  agent
  /model
  ```
  Pick **Auto Balance**, then paste this as your first message:
  > Read closecall/agents/TEAMMATE2.md completely, then carry out Part B autonomously, start to finish. Only stop where it says STOP-AND-ASK.
- ✗ If the agent asks permission for every command, choose the option that always allows commands for this session.
- ✗ When git asks for a username and password: type your GitHub username, and paste the **token** as the password — in the terminal, never in the agent chat.
- ✗ ~9:55 Open the app: **workshop.thecosmoslabs.com → App**. You should see a page titled CloseCall. Tell Teammate 3 the app is live.
- ✗ ~11:20 When Teammate 1 says **VERDICTS READY**, tell your agent: *"Verdicts are ready. Do A5 now."*
- ✗ 11:30–2:30 Teammate 3 sends you a bug list every 30 minutes. Paste it to your agent: *"Fix these bugs: …"*
- ✗ 12:30 Checkpoint: approve one real close call in the app and see it in the Decision log.
- ✗ 3:15 Feature freeze. Click through the app following the demo script while Teammate 4 records the video.

---

## Part B — Agent brief: App agent

### Who you are
You are the **App agent** for team CloseCall at a one-day hackathon. Your human is **Teammate 2**. On another build machine, **Teammate 1's Pipeline agent** finds and checks clips and scores accuracy. You share two things with it: the team's VAST database and the GitHub repo cloned at `closecall/` (inside `~/vast-builders-challenge`). Teammates 3 and 4 have no build machine: Teammate 3 tests your app with reviewer name `test` and sends bug lists through Teammate 2.

### Mission
CloseCall finds **near misses between people (pedestrians or cyclists) and moving vehicles** in dashcam video, and also flags **work-zone hazards** (exposed wires or cables, open holes or trenches, debris in the road, heavy equipment near people or traffic). It checks each clip with Cosmos and lets a person approve or reject it. You build the **web app** a city traffic-safety engineer uses. It has four tabs:
- **Review:** clips waiting for a decision, each with its evidence and Approve / Reject buttons
- **Decision log:** every decision with its full history
- **Accuracy:** how often the system is right, with ranges
- **Data & Limits:** what the system does and doesn't do with people's data

Every click must be saved with its history.

### How to work
1. Before writing any code, read `README.md`, `ARCHITECTURE_REFERENCE.md` (if present) and every `SKILL.md` under `.cursor/skills/` — especially the database, deploy and retrieval skills. Use those skills and their APIs. Never invent APIs.
2. Do tasks **A1 → A10 in order without waiting for Teammate 2 between tasks** (A5 and A7 wait on Teammate 1's status lines; keep working on other tasks meanwhile). For each task:
   - write a 3-bullet plan,
   - build it,
   - test it,
   - check the task's **Done when** line,
   - `git pull --rebase`, then commit and push,
   - append one line to `closecall/status/app.md`: `HH:MM ET — A# done — <one-line result>`.
3. At the start of each task, check the time with `TZ=America/New_York date` and apply the **scope cuts** below if you're behind.
4. Every ~10 minutes, run `git pull` and read `closecall/status/pipeline.md`. Teammate 1's agent writes `VERDICTS READY` and `RESULTS READY` there.
5. **STOP-AND-ASK** (stop and wait for Teammate 2) only when:
   - (a) you'd delete, drop or overwrite any table or data you didn't create for testing;
   - (b) git asks for credentials;
   - (c) you're stuck for 10+ minutes after two fix attempts — summarize the problem and offer two options;
   - (d) an action would touch anything outside `closecall/` or our own `closecall_*` tables.
6. If something breaks in the environment: run the starter-kit health check ("run a git pull", then "check that everything is working"). If it's still broken, use `/ask-cosmos` and tell Teammate 2.

### Hard rules
- Never put keys or tokens in code, files, logs or commits. Use the environment variables that are already set.
- No face recognition, no license-plate reading, no identifying or tracking people. Show clips only through the event's own playback.
- Times come from the data, never from model text.
- Decisions made with reviewer name **`test`** are for testing. Hide them from the Decision log and don't let them remove clips from the Review queue.
- Keep the UI simple and clean. Use whatever framework the deploy skill expects.
- Only edit: `closecall/app/`, `closecall/status/app.md`, `closecall/pitch.md`, `closecall/docs/demo.md`, `closecall/.gitignore`. **Never edit `closecall/pipeline/`, `closecall/labels/` or `closecall/results.json`.**

### Shared contract (Teammate 1's agent writes the first two tables and results.json)
**Tables in the team VAST database**
- `closecall_candidates`: segment_id, camera_id, query, kind, search_score, has_person, has_vehicle, passed_yolo, created_at
- `closecall_verdicts`: segment_id, camera_id, start_time, end_time, playback_link, yolo_objects, verdict, type, severity, when_in_clip, hazard, reason, final_answer, prompt_version, created_at
- `closecall_decisions` (**you create this**): decision_id, segment_id, action (approve or reject), reason, reviewer, verdict_at_decision, prompt_version, decided_at

**Allowed values:** verdict and final_answer are each one of `CLOSE_CALL`, `NO_CONFLICT`, `CANT_TELL`. kind is `close_call` or `hazard`. hazard is one of `none`, `work_zone`, `wires`, `open_hole`, `debris`, `equipment`, `other`.

**Files**
- `closecall/notes/schema.md` — Teammate 1's agent writes the real table and field names here around 9:50. Read it.
- `closecall/results.json` — shaped like this:
  `{"generated_at": "...", "n_test": 0, "kappa": 0.0, "versions": [{"name": "...", "precision": {"value": 0.0, "low": 0.0, "high": 0.0, "n": 0}, "recall": {...}, "coverage": {...}}]}`
- `closecall/status/app.md` (yours) and `closecall/status/pipeline.md` (Teammate 1's)

### Tasks

**A1 — Repo setup (9:40).**
- Confirm `closecall/` is a git repo with a working remote.
- Create `app/`, `docs/` and `status/` if they're missing.
- Add a `.gitignore` covering `.env`, key and secret files, `__pycache__`, data dumps and video files.
- Create `status/app.md`, and write `pitch.md` with the pitch text below.
- Commit and push. Git may ask for credentials → **STOP-AND-ASK**: Teammate 2 types them.
- **Done when:** the push succeeds.

**A2 — Prove the app can go online (9:50).**
- Read the deploy skill to see which framework it expects.
- Make the simplest app in `app/` that shows a page titled **CloseCall**.
- Deploy it with `/deploy-app-no-registry` and tell Teammate 2 how to open it (workshop.thecosmoslabs.com → App).
- **Done when:** the page loads.

**A3 — Decisions table (10:00).**
- Using the database skills, create `closecall_decisions` exactly as in the contract.
- Write one test row (reviewer `test`), read it back, then delete only that row.
- **Done when:** the write and read both work.

**A4 — Review tab with stand-in data (10:10).** Build the main tab.
- Read clips from `closecall_verdicts` where `final_answer` is CLOSE_CALL or CANT_TELL, **or** `hazard` is not `none`, and no real decision exists yet.
- Until that table exists with `final_answer`, use 3 made-up rows (one of them a work-zone hazard) and show a banner: "DEMO DATA".
- For each clip show:
  - the clip (embed the playback if possible, otherwise a link)
  - Cosmos's verdict, severity and one-line reason
  - the hazard tag, if any (for example "Work-zone hazard: exposed wires")
  - the YOLO objects
  - the time in the drive
- Add **Approve** and **Reject** buttons, a reason box and a reviewer name box.
- A click saves a row to `closecall_decisions` with: segment_id, action, reason, reviewer, verdict_at_decision, prompt_version, decided_at. Show a short confirmation.
- Show CANT_TELL clips with a label: "Unclear — needs a person."
- **Done when:** a test decision (reviewer `test`) saves and reads back.

**A6 — Decision log and Data & Limits tabs (do this while waiting for VERDICTS READY).**
- **Decision log:** a table of every real decision (hide reviewer `test`) with segment, action, verdict at decision, prompt version, reviewer, time and reason. Newest first.
- **Data & Limits:** exactly the text below.
- **Done when:** both tabs render and are deployed.

**A5 — Switch to real data (as soon as `status/pipeline.md` says VERDICTS READY).**
- Remove the stand-in rows and the banner, and read the real `closecall_verdicts`.
- Test Approve and Reject on 2 real clips with reviewer `test`, and confirm they don't vanish from the queue.
- **Done when:** real clips show with working playback or links.

**A7 — Accuracy tab (as soon as `status/pipeline.md` says RESULTS READY; until then show "Results will appear here after scoring").**
- Read `closecall/results.json` (pull first).
- Show a table of the versions with precision, recall and coverage, each written as `value (low–high), n=…`. Also show n_test and kappa.
- Under it: "Measured on our hand-labeled test clips. Ranges are 95% intervals."

**A8 — Polish and redeploy (2:30).**
- Header: **CloseCall — near misses, verified by people**.
- Four tabs in this order: Review, Decision log, Accuracy, Data & Limits.
- A small counter row at the top: clips checked · close calls found · hazards found · waiting for review · decisions made.
- A filter on the Review tab: All · Close calls · Hazards.
- Even spacing, readable fonts, no clutter.
- Redeploy and click through every tab.

**A9 — Demo readiness (3:00).**
- Make sure at least 3 real CLOSE_CALL or CANT_TELL clips, plus 1 hazard clip if any were found, are still undecided, so there's something to approve live.
- Write `docs/demo.md` with the exact click path for the demo script below.
- Final redeploy. Write status line: `APP FROZEN`.

**A10 — Final text (3:15).**
- Fill the `X` and `Y` placeholders in `pitch.md` with numbers from `results.json`: version C precision as a percent, and its range as ± the larger distance to low or high, rounded.
- Search `closecall/app/` for anything that looks like a key or token and report what you find.
- Push.

### Scope cuts (apply on your own)
- **12:30 and real data isn't flowing yet:** keep the stand-in path working, finish A6, and polish.
- **3:15:** feature freeze — only fixes and redeploys.

### Fallbacks
- **Deploy fails:** run the app on the build machine, open it in the machine's browser, and tell Teammate 2 so the demo can be screen-recorded there.
- **Playback can't be embedded:** show a link or the segment's time range instead.
- **Database write fails:** also append each decision to `app/decisions_backup.jsonl` so the demo still works, and note it in the status file.

### Texts

**pitch.md**
```
# CloseCall
Fix dangerous streets before someone gets hurt.

## The problem
Cities usually redesign a dangerous street only after someone is injured, because their main
warning sign is crash reports, and those arrive too late. Near misses happen far more often
than crashes and tend to cluster at the same dangerous spots, which makes them the earliest
warning a city can get. The footage already exists in bus and fleet dashcams and street
cameras. Construction zones add risks that change daily: exposed wires, open trenches and
heavy equipment right next to people and traffic. No one has time to watch thousands of hours
of it.

## What CloseCall does
CloseCall watches the footage and gives a city traffic engineer a short list of close calls
and work-zone hazards, each with the clip as evidence. The engineer approves or rejects each one. Approved cases
become a safety review, which can lead to a longer crossing signal, a speed bump or a
redesigned curb. Every decision is saved with the evidence behind it.

## Why it stands out
1. A person stays in charge. The AI recommends; a human decides, and every decision leaves a record.
2. It shows its proof and admits doubt. When the video is unclear, it says "can't tell" and hands it to a person.
3. It measures how often it's right on near misses: correct X% of the time, give or take Y, on clips we labeled by hand.

## Built responsibly
CloseCall looks at places and patterns, never people: no face recognition, no license plates,
no tracking anyone.
```

**Data & Limits tab**
```
CloseCall looks at places and patterns, never people: no face recognition, no license plates,
no tracking anyone. Raw video stays in VAST; only events and decisions are saved. Every action
is approved by a person and logged. Limits: tested on a small hand-labeled set of dashcam
clips; Cosmos can misjudge fast, dark or hidden scenes, so unclear clips go to a person.
Hazard tags are Cosmos's reading of the clip and are not yet scored against hand labels.
```

**Demo script (3 minutes)**
- 0:00 **Teammate 1:** "Cities fix dangerous streets after someone gets hurt. Near misses are the early warning, but nobody can watch thousands of hours of fleet video. CloseCall does."
- 0:30 **Teammate 2:** Review tab → open a real clip → show Cosmos's verdict and reason → type a reason → **Approve** → Decision log shows the saved record: who, when, which prompt version.
- 1:10 **Teammate 2:** show an "Unclear — needs a person" clip: "When the video can't settle it, CloseCall says so instead of guessing."
- 1:25 **Teammate 2:** show a work-zone hazard clip: "It also flags construction hazards like exposed wires, open holes and debris before someone gets hurt."
- 1:40 **Teammate 1:** Accuracy tab: "On N clips we labeled by hand, search alone was right P0% of the time. With our checks it's P%, give or take R, and it says can't tell on C%."
- 2:20 **Teammate 1:** Data & Limits tab: "No faces, no plates, no tracking. Places and patterns, not people."
- 2:40 **Teammate 2:** "Next: a pilot with one city fleet. The same engine helps delivery fleets coach drivers."

---

## Part C — Optional helper agent (second terminal, start at 2:30 PM)

Open a second terminal tab, type `cd ~/vast-builders-challenge` and `agent`, then paste:
> Read closecall/agents/TEAMMATE2.md Part C and do it.

**Brief for the helper agent:** You are the Submission helper for team CloseCall. You may only create or edit files in `closecall/docs/`. Never touch app code, pipeline code or database tables. Pull before you start and push after each item. Teammate 4 submits the project using these files.
1. Write `docs/submission.md` with every submission field ready to paste: project name, one-paragraph description (from `pitch.md`), the tools-used list below, the repo link (github.com/Sebilopez1/closecall), and a blank for the video link.
   Tools used: NVIDIA Cosmos Reason (via the VAST video pipeline) to check each clip · Cosmos Embed + VAST semantic search to find moments · YOLO11 for person and vehicle detection · VAST DataEngine and VastDB as the system of record · W&B Weave for evaluation and tracing · CoreWeave GPUs hosting the models and our app · Cursor.
2. Write `docs/judge_qa.md`: 9 likely judge questions with 2-sentence answers, using real numbers from `results.json` once it exists. Cover: accuracy, why not just trust the AI, do near misses matter, who would use it, what we built versus what was provided, privacy, what happens when it's wrong, why construction zones, what's next.
3. Check every link in `README.md` and `docs/` and report any broken ones.
