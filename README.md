# CloseCall

**Vision Zero evidence from the cameras cities already have.**

Cities decide which streets to fix from crash reports that arrive months late and never count near misses. CloseCall searches the street video a city already has and turns it into specific, checkable findings: a taxi passing a work-zone flagger, a car stopped in the crosswalk, a door opened into traffic, a close pass on a cyclist. Each one is measured in metres where the video allows and linked to its 5-second clip. A person reviews the findings, every decision is logged, and the danger score is checked against blind ratings from people.

Built at Real-Time Video Agents Hack NYC, October 9, 2026. Live app (event network): https://team-15-app.thecosmoslabs.com/app/

## Who it's for
- **City transportation and Vision Zero teams**, and the consultants who write their safety action plans: where people get squeezed, measured on video, and whether a fix worked (same questions before and after). Federal Safe Streets and Roads for All grants fund this kind of traffic-conflict video analysis.
- **Work-zone offices, utilities and contractors**: how close traffic comes to flaggers and crews, and when.
- **Transit and curb managers**: blocked lanes, doors opening into traffic, delivery trucks where a loading zone is needed.

## How it works
1. **Find.** Search the event's video library (VAST, through the NVIDIA VSS search service): 3,537 five-second clips from 13 cameras. CloseCall searches every street location (five San Francisco intersections; two New York cameras, one at a Walker St work zone) plus a New York bike camera and a Toronto dashcam, for work zones, crossings, curb problems and close passes on cyclists. Each location keeps up to 12 clips per scan.
2. **Sense.** YOLO11 boxes every car, bus, truck, bike and person in all 150 frames of a clip. CloseCall uses each object's real size as a ruler to estimate gaps in metres: between a vehicle and a person at the same depth on street cameras, and between the rider and each vehicle on the bike camera.
3. **Understand.** NVIDIA Cosmos describes each clip in words. CloseCall turns those descriptions into specific findings: a worker or flagger in the street, a car door open into traffic, a vehicle blocking a lane, a vehicle stopped in the crosswalk, someone crossing outside the crosswalk, a stroller or wheelchair in the crossing.
4. **Score.** Each clip gets a danger score from 0.0 to 10.0; 5.0 and up is a close call. Measured gaps drive the score, and Cosmos describing a close pass, swerving or hard braking adds to it.
5. **Hotspots.** One row per place: close calls, what CloseCall sees most, the closest measured gap and the worst clip, one click from the video.
6. **Review and measure.** A person approves or rejects each finding with a reason; every decision is saved with who, when and the score. Teammates rate clips 0 to 10 without seeing the AI's score, and the Accuracy tab compares the two, next to a baseline that trusts the search alone.

**Privacy:** places and patterns, never people. No face recognition, no license plates, no tracking. Raw video stays in VAST; the app keeps only findings, scores, decisions and ratings. This is planning evidence, not ticketing.

**Results:** see the Accuracy tab; final numbers are in `pitch.md`.

**Limits:** distances are estimates from one camera (roughly ±30–50%) until a camera is calibrated, which one known lane width would do. Findings from Cosmos's descriptions are only as good as the descriptions, so each one links to its clip for a person to check. The hand-rated set is small.

**Next:** per-camera calibration, close calls per hour by place and time of day, and before/after reports for each street fix.

---

## For the team

### Run and deploy (build machine terminal)
```
cd ~/vast-builders-challenge/closecall
git pull
bash deploy/deploy.sh      # code changes reach the running app in about a minute
bash deploy/logs.sh        # app logs
```
Credentials come from `/config` on the build machine and go straight into a Kubernetes Secret, never into the repo. Re-scan the footage with the **Re-scan footage** button in the app.

### Search the whole library
`https://team-15-app.thecosmoslabs.com/app/api/search?q=<question>&camera=<camera id>&top_k=50` returns clips with Cosmos's description and a `video` link to play each one. Leave out `camera` to search all 13 cameras.

### Rate clips (everyone)
App → **Label (blind)** → type your name → watch the clip → rate 0 to 10 → **Save rating**. Use **Can't judge — skip** if you can't tell. Everyone gets the clips in the same order, so two people rating the first 30 gives us agreement between people too.

### Git rules
- Pull before you push. Never `git push --force`.
- Changing anything in `app/`? Push to your own branch (`git push origin HEAD:yourname-work`) and say so; it gets merged into main after a check.
- Never put keys or tokens in code, files or commits.
- No faces, no license plates, no tracking people.
- Reviewer or rater name `test` is for testing; those clicks are left out of the log and the scores.

### Repo map
```
app/main.py       server: VSS search, detections, findings, scoring, API, video proxy
app/index.html    web app: Review, Hotspots, Label (blind), Decision log, Accuracy, Data & Limits
deploy/           deploy.sh (Kubernetes), logs.sh
findings/         what each teammate found in their cameras
pitch.md          pitch, demo click path, judge Q&A
agents/, status/, app/tabs/   the earlier multi-agent plan (not used by the live app)
```
API: `api/clips`, `api/hotspots`, `api/search`, `api/accuracy`, `api/decisions`, `api/export` (all JSON).
