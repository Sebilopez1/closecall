# CloseCall — Teammate 4: Story, Submission & Timekeeper

Real-Time Video Agents Hack NYC · Friday, October 9, 2026 · build 9:30 AM–4:30 PM ET

**Your job:** make sure we submit on time and that the judges understand why CloseCall matters. You're also the team's clock. You don't need a build machine (only two people per team get one).

**What we're building (1 line):** CloseCall finds near misses between people and cars in dashcam video, lets a person approve or reject each one, and reports how often it's right.

---

## Before you arrive (do now)
- ✗ Confirm you're **registered and accepted** for the event (check your email or Luma). Applications closed October 2. If you're not on the list, message the hosts on Luma right away.
- ✗ Have a GitHub account. Send Sebi your username, then accept his invite to `Sebilopez1/closecall`.
- ✗ Install Loom (or know your screen recorder) and test a 30-second recording with your voice.
- ✗ Read the pitch and the demo script below.
- ✗ Bring laptop, charger and a government photo ID. Arrive by 8:15.

## At the event
- ✗ **9:00 keynote:** take notes on the judging criteria, demo length, submission timing (is 4:30 the **deadline**, or when submissions **open**?), and any rule changes. Tell the team.
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

- ✗ **~10:15, when Sebi says "LABELS READY":** you label **clips 21–60**:
  1. Open `github.com/Sebilopez1/closecall/blob/main/labels/labels_grant.csv` and tap the **pencil (Edit)** icon.
  2. After each line's last comma, type `CLOSE_CALL`, `NO_CONFLICT` or `CANT_TELL` (rules below).
  3. Tap **Commit changes** every 10 clips.
  - Don't look at the AI's answers, and don't discuss labels with Teammate 3 until you're both done. Your overlap (clips 21–40) measures agreement.
  - If clips only open on the build machines, label at Grant's screen.
- ✗ **11:00–3:00, story:**
  - Write the submission text in your notes: project name, description (the pitch below), tools used (list below), repo link, all four names and emails.
  - Practice the 60-second table pitch and the 3-minute demo with Sebi at lunch.
  - When Sebi says "RESULTS READY", fill the X and Y in the pitch, plus the demo numbers (N, P0, P, R, C).
  - Prepare answers to the judge questions below.
- ✗ **3:15, record the demo video** (3 minutes max). Grant clicks through the app while you record, following the demo script. Upload it (Loom, or YouTube as unlisted), then check the link works in a private browser window.
- ✗ **3:45, submit** at tokensand.com/vastnyc → **Submit your project**:
  - repo link: github.com/Sebilopez1/closecall
  - demo video link
  - description and tools used
  - all four names and emails

  Screenshot the confirmation and post it in the team chat.
- ✗ **4:30–6:30:** lead the 60-second pitch at the table while Grant shows the app.
- ✗ **After:** post on LinkedIn and X with the video and the real numbers, and thank the sponsors and judges by name.

## Pitch (the submission description)
Cities usually redesign a dangerous street only after someone is injured, because crash reports are their main warning sign and they arrive too late. Near misses happen far more often and tend to cluster at the same dangerous spots, so they are the earliest warning a city can get. The footage already exists in bus and fleet dashcams, but no one can watch thousands of hours of it. CloseCall watches it, gives a city traffic engineer a short list of close calls with the clip as proof, and lets the engineer approve or reject each one; every decision is saved with its evidence. It keeps a person in charge, says "can't tell" when the video is unclear instead of guessing, and measures how often it's right: correct X% of the time, give or take Y, on clips we labeled by hand. It looks at places and patterns, never people: no face recognition, no license plates, no tracking.

**Tools used:** NVIDIA Cosmos Reason (via the VAST video pipeline) to check each clip · Cosmos Embed + VAST semantic search to find moments · YOLO11 for person and vehicle detection · VAST DataEngine and VastDB as the system of record · W&B Weave for evaluation and tracing · CoreWeave GPUs hosting the models and our app · Cursor.

## Demo script (3 minutes)
- 0:00 **Sebi:** "Cities fix dangerous streets after someone gets hurt. Near misses are the early warning, but nobody can watch thousands of hours of fleet video. CloseCall does."
- 0:30 **Grant:** Review tab → open a real clip → Cosmos's verdict and reason → type a reason → **Approve** → Decision log shows the saved record: who, when, which prompt version.
- 1:20 **Grant:** an "Unclear — needs a person" clip: "When the video can't settle it, CloseCall says so instead of guessing."
- 1:40 **Sebi:** Accuracy tab: "On N clips we labeled by hand, search alone was right P0% of the time. With our checks it's P%, give or take R, and it says can't tell on C%."
- 2:20 **Sebi:** Data & Limits tab: "No faces, no plates, no tracking. Places and patterns, not people."
- 2:40 **Grant:** "Next: a pilot with one city fleet. The same engine helps delivery fleets coach drivers."

## Judge questions and answers
- **How accurate is it?** "On N clips two of us labeled blind, precision is P with this range, and it says 'can't tell' on C% and sends those to a person."
- **Why not just trust the AI?** "We measured it: our checks raised precision from P0 to P. When it's unsure, a human decides."
- **Do near misses matter?** "Bellevue, Washington analyzed about 5,000 hours of intersection video and found near-crashes accurately predict where future crashes happen."
- **Who would use it?** "City traffic-safety teams, using cameras already on buses and city fleets. Fleets can also use it to coach drivers."
- **What did you build versus what was provided?** "The event provided the video pipeline and models. We built the candidate finder, the Cosmos check and decision rule, the approval app with decision history, and the accuracy test."
- **Privacy?** "No faces, no plates, no tracking people. Only places and patterns."
- **What happens when it's wrong?** "A person rejects it, the rejection is logged, and it becomes a new test case."
- **What's next?** "Test on a public near-miss dataset, add night analysis (77% of US pedestrian deaths in 2023 happened in the dark), then pilot with one fleet."

## Labeling rules
- **CLOSE_CALL:** a person in or entering the road comes within about one car length of a moving vehicle, or someone has to react suddenly.
- **NO_CONFLICT:** on the sidewalk or far away, the car is stopped, or there's plenty of room.
- **CANT_TELL:** hidden, too dark or blurry, or the clip ends too soon.
