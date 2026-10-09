# CloseCall: pitch

## One line
Vision Zero evidence from the cameras cities already have: every near miss, measured and on video, so a city fixes the right street and can prove the fix worked.

## Problem (20 seconds)
Cities decide which streets to fix from crash reports. Those arrive months late and only count the crashes, not the near misses that come first. The federal Safe Streets and Roads for All program ($5B for 2022–26, $3.9B already awarded to 2,000+ communities) asks cities for data-driven safety plans, and USDOT lists AI video analysis of traffic conflicts as an eligible use. Today that analysis means installing new sensors at each intersection.

## What we built (40 seconds)
- CloseCall searches the street video a city already has (VAST and NVIDIA VSS, here 3,537 clips from 13 cameras) for the moments a safety team acts on: work zones, crossings, curb problems, close passes on cyclists.
- YOLO11 finds every vehicle and person in every frame; using each one's real size as a ruler, CloseCall measures how close vehicles came, in metres.
- NVIDIA Cosmos describes each clip in words; CloseCall turns that into specific findings: a flagger in the street, a car stopped in the crosswalk, a door opened into traffic, a delivery truck blocking a lane.
- Every clip gets a danger score from 0.0 to 10.0 (5.0 and up is a close call), and every place gets a row on the Hotspots page: close calls, what we see most, the closest measured gap, the worst clip.
- A person approves or rejects each finding; every decision is logged. We check the score against people who rated clips 0 to 10 without seeing it.

## Demo click path (90 seconds)
1. **Hotspots:** every place scanned, worst first. Point at **Walker St, New York (work zone)**: a flagger working in the street.
2. Click **Open** on its worst clip. Play it: the boxes, and the vehicle closest to the person, with its gap in metres.
3. **What CloseCall found:** the measured finding with its time (click it to jump there) and Cosmos's findings below it.
4. Type a reason and **Approve**; show the **Decision log**.
5. Filters: **Work zones**, **Crossings**, **Curb & lanes**: the same engine across five San Francisco intersections.
6. **Accuracy:** the score against people's blind ratings, and against trusting the search alone.

## Results (fill in at 3:30 from the app)
- Places scanned: __ (clips: __)
- Close calls (5.0+): __; closest measured gap: __ m at __
- Average difference from people (0 to 10): __ points (n = __); correlation __
- Same side of 5.0 as people: __% (95% range __–__%); trusting the search alone: __%

## Who pays
- **City transportation and Vision Zero teams**, through Safe Streets for All planning grants and their consultants: a near-miss study per corridor or work zone, then before/after tracking per camera.
- **Work-zone offices, utilities and contractors**: how close traffic comes to flaggers and crews (850 people died in US work zones in 2024).
- **Transit and curb managers**: blocked lanes and stops, and where loading zones are needed.

## Why us
Derq, Miovision, VivaCity and Ouster BlueCity sell near-miss analytics on their own sensors, installed per intersection (Chattanooga paid BlueCity $2M for 120 intersections). CloseCall is software on video cities already have, including bus, bike and dashcam footage; anyone can ask a new question in plain English, and every finding comes with its clip.

## Judge Q&A
- **How accurate are the distances?** Estimates from one camera, roughly ±30–50% until a camera is calibrated (one known lane width does it). That's why each finding links to its clip and we check the score against people.
- **Is this enforcement?** No. No plates, no faces, no tracking people: it's planning evidence. Tickets need plate reads and legal authority.
- **What does VAST do here?** The event's VAST cluster stores the video and runs the search service (VSS), which serves the Cosmos descriptions, the YOLO11 detections and the video streams the app uses.
- **Why not just ask Cosmos?** Cosmos describes; it doesn't measure. The boxes give the distance and Cosmos gives the context; findings show which is which.
- **How would it scale?** A scan searches each place and scores up to 100 clips in a few minutes; the heavy work (Cosmos, YOLO) already runs inside VSS. Next: close calls per hour by place and time of day, and before/after reports.

Sources: SS4A https://www.transportation.gov/grants/SS4A · eligible uses https://www.transportation.gov/grants/ss4a/ITS-use-cases · work zones https://ops-dr.fhwa.dot.gov/publications/HOP-26-060_FHWA_NWZAW_Factsheet.pdf · Chattanooga https://www.tipranks.com/news/the-fly/ouster-awarded-2m-contract-to-deploy-traffic-solution-in-chattanooga
