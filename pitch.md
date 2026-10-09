# CloseCall: pitch

## One line
Tesla-style eyes for people on bikes: the bike's own camera measures, in metres, how close every vehicle came.

## Problem (20 seconds)
Cars get radar, cameras and blind-spot warnings. People on bikes get a bell. In 2024, 1,103 cyclists were killed on US roads (NHTSA). Close passes are the everyday version of that number, and almost nobody measures them.

## What we built (40 seconds)
- CloseCall searches the event's street video in VAST for riding situations, then reads every clip two ways: YOLO11 boxes every vehicle in every frame, and NVIDIA Cosmos describes what happened in words.
- Using each vehicle's real size as a ruler, it estimates from the boxes how far ahead each vehicle was and how much room it left the rider, in metres, and whether the vehicle passed the rider or the rider squeezed past it.
- Every clip gets a danger score from 0.0 to 10.0 and a plain reason: "Car passed about 0.3 m from you on your left." 5.0 and up is a close call.
- A person approves or rejects each close call, and every decision is logged.
- We measure it: teammates rate clips 0 to 10 without seeing the AI's score, and the app compares the two.

## Demo click path (90 seconds)
1. Open the app. The list starts with the highest danger scores (for example 7.3, "Squeezing past").
2. Click it and play the clip: boxes on the video, and the vehicle in the danger zone turns red with its gap ("gap <0.2 m").
3. Point at the **Sensing view**: the same moment from above, in metres around "you". Then the **Rider view**.
4. Read **What Cosmos saw**: Cosmos's own words back up the score ("navigating between vehicles").
5. Type a reason and **Approve**. Open **Decision log**: who, when, the score and the scoring version.
6. **Label (blind)**: the 0 to 10 slider people used, without seeing the AI.
7. **Accuracy**: the AI against people, and against trusting the search alone.

## Results (fill in at 3:30 from the Accuracy tab)
- Clips scanned: 60 (45 from a New York bike camera, 7 dashcam, 8 street cameras)
- Close calls (5.0+): __
- Average difference from people (0 to 10): __ points (n = __); correlation __
- Same side of 5.0 as people: __% (95% range __–__%); trusting the search alone: __%
- Early check at 1:15 PM: 14 of 16 clips (88%, 95% range 64–97%) against 4 of 16 (25%) for search alone

## What's next
- **Riders:** live warnings on a phone or helmet camera, by sound or vibration.
- **Fleets:** a safety score per route for delivery and bike-share companies.
- **Cities:** close calls added up by street become a map of where protected lanes are needed.

## Judge Q&A
- **How accurate are the distances?** They're estimates from one camera, roughly ±30–50%. That's why we report a score and check it against people, and why a big vehicle right alongside, too close to measure, goes to a person instead of being guessed.
- **Why not just ask Cosmos?** Cosmos describes; it doesn't measure. The boxes give the distance and Cosmos gives the context. The score uses both, and both are shown in the app.
- **What does VAST do here?** The event's VAST cluster stores the video and runs the search service (VSS). It serves the Cosmos descriptions, the YOLO11 detections and the video streams the app uses.
- **Privacy?** No faces, no license plates, no tracking people. Raw video stays in VAST; the app keeps scores, decisions and ratings.
- **How would it scale?** A full scan (searches, detections and scoring of 60 clips) takes about 90 seconds; the scoring itself is plain Python over the detections. The heavy parts, Cosmos and YOLO, already run inside VSS.
- **Where is it hardest?** Riding past slow or stopped traffic: is squeezing past a stopped car a close call? A vehicle passing the rider closely counts more than the rider squeezing past, and Cosmos's description breaks the tie.

Source: NHTSA Traffic Safety Facts, 2024 data, bicyclists and other cyclists (https://trid.trb.org/View/2736758).
