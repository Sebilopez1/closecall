# CloseCall

**Tesla-style eyes for people on bikes and on foot.**

Cars get more sensors every year; people on bikes still get a bell. CloseCall watches street footage on behalf of cyclists and pedestrians: for each near miss it says who was at risk, what the threat was (a turning car, an opening door, a close pass, a bus pulling in) and which side it came from, shown as a Tesla-style rider view. It also flags construction-zone hazards like exposed wires, open holes and debris. It checks each clip with NVIDIA Cosmos and lets a safety manager approve or reject it. Every decision is saved with its evidence, and we measure how often the system is right on clips we labeled by hand.

Built at Real-Time Video Agents Hack NYC, October 9, 2026.

## How it works
1. **Find:** search the event's Toronto dashcam footage for cyclists and pedestrians near moving vehicles (YOLO must see both): close passes, opening doors, right turns across bike lanes, buses pulling in. Also search for work zones with wires, holes, debris or equipment.
2. **Check:** Cosmos re-watches each candidate with our question and answers `CLOSE_CALL`, `NO_CONFLICT` or `CANT_TELL`, plus who was at risk, what the threat was and which side it came from, and a hazard tag (`wires`, `open_hole`, `debris`, `equipment`, `work_zone` or `none`). Unclear clips go to a person instead of being guessed.
3. **Approve:** a person approves or rejects each clip in the web app, next to its rider view. Every decision is logged: who, when, which prompt version.
4. **Score:** near-miss precision, recall and coverage against hand labels, each with a 95% range. Hazard tags aren't scored yet.

**Privacy:** places and patterns, never people. No face recognition, no license plates, no tracking.

**Next:** the same eyes on a phone or helmet camera with live warnings, starting with delivery and bike-share fleets. Every ride adds to a map of dangerous streets for cities.

**Results:** added here after scoring.

---

## For the team

### Who opens what
| Teammate | Role | Works on | Open this |
|---|---|---|---|
| 1 | Pipeline: find, check, score | build machine | `agents/TEAMMATE1.md` |
| 2 | App: review, decisions, accuracy | build machine | `agents/TEAMMATE2.md` |
| 3 | Scoring (accuracy, Weave), labels 1–40, testing | build machine | `agents/TEAMMATE3.md` |
| 4 | App tabs (Decision log, Accuracy, Data & Limits), labels 21–60, story, submission | build machine | `agents/TEAMMATE4.md` |

### Build machine setup (everyone, same team number)
Type these in the build machine **terminal**, not the agent chat:
```
cd ~/vast-builders-challenge
git clone https://github.com/Sebilopez1/closecall
git config --global credential.helper 'cache --timeout=36000'
cd closecall && git push
```
- **Username:** your GitHub username.
- **Password:** paste your GitHub token (nothing shows while you paste; that's normal).
- You should see `Everything up-to-date`. Git now remembers your login for 10 hours.

Then start the agent:
```
cd ..
agent
/model
```
Pick **Auto Balance** and paste the first message from your TEAMMATE file.

### How the agents work together
- GitHub is the shared folder. The four agents never talk directly.
- For every task, each agent: pulls → builds → tests → commits → pushes → writes one line in its status file.
- Status files: `status/pipeline.md` (Teammate 1), `status/app.md` (Teammate 2), `status/scoring.md` (Teammate 3) and `status/tabs.md` (Teammate 4). Signals to watch for: `SHELL READY`, `LABELS READY`, `VERDICTS READY`, `READY FOR SCORING`, `RESULTS READY`, `TABS UPDATED`, `APP FROZEN`, `FROZEN`.
- Each agent edits only its own files, so they never overwrite each other. Only Teammate 2's agent deploys the app.
- Teammates 3 and 4 fill in their label files on github.com (pencil icon → **Commit changes**). Accept the repo invite first.
- Run git only inside `closecall/`. The parent folder is the event's own repo.

### Repo map
```
agents/        one brief per teammate
pipeline/      find, check, decide (Teammate 1's agent); evaluate.py (Teammate 3's agent)
app/           the web app shell and Review tab (Teammate 2's agent)
app/tabs/      one file per tab; Decision log, Accuracy, Data & Limits, counters (Teammate 4's agent)
labels/        hand labels: labels_teammate3.csv, labels_teammate4.csv
notes/         schema.md (real table and field names), reviews
status/        pipeline.md, app.md, scoring.md, tabs.md: progress lines
docs/          demo click path, submission text, judge Q&A
pitch.md       project description
results.json   accuracy numbers (after scoring)
```

### Timeline (ET)
| Time | What happens |
|---|---|
| 9:30 | Build starts |
| ~10:15 | `LABELS READY`: Teammates 3 and 4 start labeling |
| ~11:20 | `VERDICTS READY`: the app switches to real clips |
| 12:30 | Checkpoint: one close call found → checked → approved → saved |
| 1:00 | Scoring |
| 2:00 | No new features |
| 3:15 | Freeze; record the demo video |
| 3:45 | Submit |

### Rules
- Never put keys or tokens in code, files or commits.
- No faces, no license plates, no tracking people.
- Reviewer name `test` is for testing; those clicks are hidden from the Decision log.
