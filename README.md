# CloseCall

**Tesla-style eyes for people on bikes.**

Cars get radar, cameras and blind-spot warnings; people on bikes get a bell. CloseCall turns the camera on a bike into sensing: it finds every vehicle around the rider, estimates in metres how much room each one left, and gives every clip a danger score from 0.0 to 10.0 with the reason, like "Car passed about 0.3 m from you on your left." A person reviews the close calls, every decision is logged, and the score is measured against blind ratings from people.

Built at Real-Time Video Agents Hack NYC, October 9, 2026. Live app (event network): https://team-15-app.thecosmoslabs.com/app/

## How it works
1. **Find.** Search the event's video library (VAST, through the NVIDIA VSS search service) for riding situations: cars passing cyclists, riding next to moving traffic, opening doors, right turns across bike lanes, buses pulling in, plus work-zone hazards. The main source is a New York bike-mounted camera (`nyc_bike_gopro-1`), plus a dashcam and street cameras. Each scan keeps 60 five-second clips.
2. **Sense.** YOLO11 boxes every car, bus, truck, bike and person in all 150 frames of a clip. CloseCall follows each vehicle from frame to frame and uses its real size as a ruler (a car is about 1.5 m tall, a bus about 3 m) to estimate how far ahead it is and how far to the side, in metres. It also tells who was moving: a vehicle passing the rider, or the rider squeezing past slow traffic.
3. **Understand.** NVIDIA Cosmos describes each clip in words. When Cosmos itself says a vehicle passed closely, the rider was weaving between cars, or someone braked hard, that adds to the score: a second, independent signal.
4. **Score.** Danger 0.0 to 10.0; 5.0 and up is a close call. A big vehicle right alongside, too close to measure, scores 4.0 so a person takes a look. Clips with no detections go to a person instead of being guessed.
5. **Review.** In the web app a person watches the clip with the boxes drawn on it, next to a top-down view of the vehicles in metres around "you", and approves or rejects it with a reason. Every decision is saved: who, when, the score at the time and the scoring version.
6. **Measure.** Teammates rate clips 0 to 10 without seeing the AI's score. The Accuracy tab shows the average difference between the AI and people, the correlation, how often both land on the same side of 5.0, and precision and recall with 95% ranges, next to a baseline that trusts the search alone.

**Privacy:** places and patterns, never people. No face recognition, no license plates, no tracking. Raw video stays in VAST; the app keeps only scores, decisions and ratings.

**Results so far (1:15 PM):** 9 of 60 clips score 5.0 or more. On the first 16 clips a teammate judged, CloseCall landed on the same side of 5.0 as the person on 14 (88%, 95% range 64–97%); trusting the search alone got 4 of 16 (25%). It's a small sample; the final numbers are in the Accuracy tab and `pitch.md`.

**Limits:** distances are estimates from one camera (roughly ±30–50%), and long vehicles seen from the side can't be measured. The hand-rated set is small. Hazard tags (wires, holes, debris, work zones) come from Cosmos's description and aren't scored yet.

**Next:** run it live on a phone or helmet camera with sound or vibration warnings; give delivery and bike-share fleets a safety score per route; add up close calls by street into a map that shows cities where to build protected lanes.

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
app/main.py       server: VSS search, detections, scoring, API, video proxy
app/index.html    web app: Review, Label (blind), Decision log, Accuracy, Data & Limits
deploy/           deploy.sh (Kubernetes), logs.sh
pitch.md          pitch, demo click path, judge Q&A
agents/, status/, app/tabs/   the earlier multi-agent plan (not used by the live app)
```
API for the curious: `api/clips`, `api/accuracy`, `api/decisions`, `api/export` (everything as JSON).
