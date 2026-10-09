# CloseCall — Teammate 3: Scoring, Labels & Testing

Real-Time Video Agents Hack NYC · build 9:30 AM · submit by 4:30 PM ET

**Your job:** your agent builds the accuracy scoring while you make the answer key (the labels) and then test the app like a city traffic engineer. Part A (this top part) is for you; Part B at the bottom is your agent's brief.

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
  > Read closecall/agents/TEAMMATE3.md completely, then carry out Part B autonomously, start to finish. Only stop where it says STOP-AND-ASK.
- ✗ While you label, don't read your agent's screen: it may show the AI's answers.
- ✗ Join the Cosmos Community at community.vastdata.com. It may let you open the team's clips and app from your laptop.
- ✗ Read the labeling rules at the bottom twice.

## Build day
- ✗ **By 10:15:** your machine is set up and your agent is running. Learn how to open a clip: Teammate 1's agent writes the instructions in `closecall/notes/schema.md`.
- ✗ **~10:15, when Teammate 1 says "LABELS READY":** you label **clips 1–40**:
  1. Open `github.com/Sebilopez1/closecall/blob/main/labels/labels_teammate3.csv` and tap the **pencil (Edit)** icon.
  2. Each line looks like `7,seg_123,<how to view>,`. Watch that clip, then type the label right after the last comma: `CLOSE_CALL`, `NO_CONFLICT` or `CANT_TELL` (exact spelling, no spaces).
  3. Tap **Commit changes** every 10 clips so nothing gets lost.
  - Don't look at the AI's answers or the app while labeling, and don't discuss labels with Teammate 4 until you're both done. Your overlap (clips 21–40) is how we measure agreement.
- ✗ **By 11:00:** all 40 labeled and committed. Tell Teammate 1 and your agent "labels done".
- ✗ **11:30–2:30, tester:** when Teammate 2 says the app is live, use it like a city engineer. Use the reviewer name **`test`** so your clicks don't count. Every 30 minutes, send Teammate 2 a short bug list: what you clicked, what happened, what you expected. Check that:
  - clips open,
  - each clip's Rider view shows the threat on the correct side,
  - hazard clips show their hazard tag,
  - Approve and Reject save,
  - the Decision log updates,
  - the Accuracy and Data & Limits tabs load,
  - nothing is slow or confusing.
- ✗ **~1:45:** Teammate 1's agent shows the 5 clips where the AI disagreed with the labels. Watch them with Teammate 1 and say who's right.
- ✗ **3:15–4:15:** play the judge in rehearsals and ask the hard questions (see Teammate 4's list). If judges ask how we measured accuracy, the answer is: "Two of us labeled the clips blind, without seeing the AI's answers, and we measured how often we agreed."

## Labeling rules
You only label close calls. If a clip shows a hazard (wires, a hole, debris) but no close call, label it `NO_CONFLICT`.

- **CLOSE_CALL:** a person (walking or on a bike) in or entering the road comes within about one car length of a moving vehicle, **or** someone has to react suddenly (hard braking, swerving, stopping short, jumping back).
- **NO_CONFLICT:** the person is on the sidewalk or far from the car's path, the car is stopped or parked, or the crossing is normal with plenty of room.
- **CANT_TELL:** something is hidden, too dark or blurry, or the clip ends before you can see what happens.
- When unsure between CLOSE_CALL and NO_CONFLICT, ask yourself: "Would a traffic engineer want to see this?" If you still can't decide, choose CANT_TELL.

---

## Part B — Agent brief: Scoring agent

### Who you are
You are the **Scoring agent** for team CloseCall at a one-day hackathon. Your human is **Teammate 3**. Three other agents share the team's VAST database and the GitHub repo cloned at `closecall/` (inside `~/vast-builders-challenge`): **Teammate 1's Pipeline agent** finds and checks clips and writes the label sheets, **Teammate 2's App agent** builds and deploys the app, and **Teammate 4's Tabs agent** shows your results in the app's Accuracy tab.

### Mission
Measure how often CloseCall is right about **near misses**, with honest ranges, against blind human labels. Hazard tags aren't scored today; just count them.

### How to work
1. Before writing any code, read `README.md`, `ARCHITECTURE_REFERENCE.md` (if present) and every `SKILL.md` under `.cursor/skills/`, especially the database and retrieval skills. Use those skills and their APIs. Never invent APIs.
2. Do tasks **S1 → S4 in order without waiting for Teammate 3 between tasks.** For each task:
   - write a 3-bullet plan,
   - build it,
   - test it,
   - check the task's **Done when** line,
   - `git pull --rebase`, then commit and push,
   - append one line to `closecall/status/scoring.md`: `HH:MM ET — S# done — <one-line result>`.
3. Every ~10 minutes, run `git pull` and read `closecall/status/pipeline.md`.
4. **STOP-AND-ASK** (stop and wait for Teammate 3) only when:
   - (a) you'd delete, drop or overwrite any table or data;
   - (b) git asks for credentials;
   - (c) you're stuck for 10+ minutes after two fix attempts — summarize the problem and offer two options;
   - (d) an action would touch anything outside `closecall/`.
5. If something breaks in the environment: run the starter-kit health check ("run a git pull", then "check that everything is working"). If it's still broken, use `/ask-cosmos` and tell Teammate 3.

### Hard rules
- **Blind labeling:** Teammate 3 labels clips until about 11:00. Until Teammate 3 says "labels done", never show Cosmos verdicts, descriptions or reasons in your replies.
- Never put keys or tokens in code, files, logs or commits. Use the environment variables that are already set (the `WANDB_` keys are preset).
- Never write to the database. You only read tables.
- Plain Python, small functions, clear names. Call `weave.init("closecall")` and wrap main functions with `@weave.op`.
- Only edit: `closecall/pipeline/evaluate.py`, `closecall/pipeline/test_evaluate.py`, `closecall/results.json`, `closecall/notes/mistakes.md`, `closecall/status/scoring.md`. **Never edit anything else.**

### Shared contract (read only, except the files you own)
- `closecall_candidates`: segment_id, camera_id, query, kind, search_score, has_person, has_vehicle, passed_yolo, created_at
- `closecall_verdicts`: segment_id, camera_id, start_time, end_time, playback_link, yolo_objects, verdict, type, severity, when_in_clip, who_at_risk, threat, threat_side, hazard, reason, final_answer, prompt_version, created_at
- `closecall/labels/labels_teammate3.csv` (clips 1–40) and `closecall/labels/labels_teammate4.csv` (clips 21–60), columns `number, segment_id, how_to_view, label`
- `closecall/labels/key.csv` (number → which list the clip came from)
- `closecall/notes/schema.md` — the real table and field names
- `closecall/results.json` (**you write it**) — shaped like this:
  `{"generated_at": "...", "n_test": 0, "kappa": 0.0, "hazards_found": {"wires": 0}, "versions": [{"name": "...", "precision": {"value": 0.0, "low": 0.0, "high": 0.0, "n": 0}, "recall": {...}, "coverage": {...}}]}`

### Tasks

**S1 — Setup (10:15).**
- Confirm `closecall/` is a git repo with a working remote.
- Create `status/scoring.md`, commit and push. Git may ask for credentials → **STOP-AND-ASK**: Teammate 3 types them.
- **Done when:** the push succeeds.

**S2 — Build and test the scoring with fake data (10:30).** Create `pipeline/evaluate.py` and `pipeline/test_evaluate.py`:
- `wilson(k, n)`: 95% Wilson interval with z = 1.96. Test: `wilson(8, 10)` ≈ (0.490, 0.943).
- `kappa(a, b)`: Cohen's kappa. Test: `kappa(["C","C","N","N"], ["C","N","N","N"])` = 0.5.
- Precision, recall and coverage for versions A, B and C (rules below), run on fake labels and fake verdicts.
- Write `results.json` in the contract shape.
- **Done when:** the tests pass and a fake `results.json` is written locally. Don't push the fake one.

**S3 — Score the real thing (about 1:00).** Start when `status/pipeline.md` says `READY FOR SCORING` and neither labels file has blanks. Until then, polish S2 and pull every 10 minutes.
- Read the tables and label files, score them, log a Weave Evaluation named `closecall-v1`, and write `closecall/results.json`.
- Write `notes/mistakes.md`: the 5 tuning clips where version C disagreed most with the human labels, with segment_id, human label, version C's answer, Cosmos's reason and how to view the clip.
- Push, then write status line: `RESULTS READY`.
- **If your machine can't read the team database:** push `evaluate.py`, write status line `EVALUATE READY` and tell Teammate 3. Teammate 1's agent runs it instead.
- **Fallback:** if Weave fails, compute the metrics anyway and add `"note": "Weave unavailable"` to `results.json`.

**S4 — Re-score (only if `status/pipeline.md` says `V2 VERDICTS READY`).** Score both prompt versions, keep both in `results.json`, push, and write status line: `RESULTS READY v2`.

### Scoring rules
- **Final human label:** Teammate 3's label for clips 1–40, Teammate 4's for 41–60. **Tuning set** = clips 1–30, **test set** = clips 31–60. Report the test set only.
- Clips labeled `CANT_TELL` by humans are left out of precision and recall; report how many there were.
- Each version predicts CLOSE_CALL, NO_CONFLICT or CANT_TELL (abstain) for each clip:
  - **A — Search only:** any close-call search hit = CLOSE_CALL; not a hit = NO_CONFLICT.
  - **B — Search + YOLO:** close-call hit and `passed_yolo` = CLOSE_CALL; else NO_CONFLICT.
  - **C — Full CloseCall:** use `final_answer` for checked clips; clips that weren't checked = NO_CONFLICT.
- **Metrics:**
  - precision = correct CLOSE_CALLs ÷ predicted CLOSE_CALLs
  - recall = correct CLOSE_CALLs ÷ human CLOSE_CALLs
  - coverage = clips answered (not CANT_TELL) ÷ all test clips
  - Give each a 95% Wilson interval (z = 1.96) and its n.
- **Kappa:** Cohen's kappa between the raw Teammate 3 and Teammate 4 labels on clips 21–40.
- **Hazards:** not scored. Count clips in `closecall_verdicts` by `hazard` (leaving out `none`) into `"hazards_found"`.
