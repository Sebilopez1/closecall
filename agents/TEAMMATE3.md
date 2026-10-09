# CloseCall — Teammate 3: Labels & Testing

Real-Time Video Agents Hack NYC · build 9:30 AM · submit by 4:30 PM ET

**Your job:** you make the answer key the whole project is graded against, then you test the app like a real city traffic engineer. You don't need a build machine (only two per team).

**What we're building (1 line):** CloseCall finds near misses between people and cars in dashcam video, flags construction-zone hazards like exposed wires or open holes, lets a person approve or reject each one, and reports how often it's right.

---

## Setup
- ✗ Accept the invite to the GitHub repo `Sebilopez1/closecall` (check your email or github.com/notifications).
- ✗ Join the Cosmos Community at community.vastdata.com. It may let you open the team's clips and app from your laptop.
- ✗ Read the labeling rules at the bottom twice.

## Build day
- ✗ **9:30–10:15:** Sit next to Teammate 1. Learn how to open a clip; their agent writes the instructions in `closecall/notes/schema.md` around 9:50. Try opening one clip from your laptop at workshop.thecosmoslabs.com. If clips only open on the build machines, you'll label at Teammate 1's screen.
- ✗ **~10:15, when Teammate 1 says "LABELS READY":** you label **clips 1–40**:
  1. Open `github.com/Sebilopez1/closecall/blob/main/labels/labels_teammate3.csv` and tap the **pencil (Edit)** icon.
  2. Each line looks like `7,seg_123,<how to view>,`. Watch that clip, then type the label right after the last comma: `CLOSE_CALL`, `NO_CONFLICT` or `CANT_TELL` (exact spelling, no spaces).
  3. Tap **Commit changes** every 10 clips so nothing gets lost.
  - Don't look at the AI's answers or the app while labeling, and don't discuss labels with Teammate 4 until you're both done. Your overlap (clips 21–40) is how we measure agreement.
- ✗ **By 11:00:** all 40 labeled and committed. Tell Teammate 1 "labels done".
- ✗ **11:30–2:30, tester:** when Teammate 2 says the app is live, use it like a city engineer. Use the reviewer name **`test`** so your clicks don't count. Every 30 minutes, send Teammate 2 a short bug list: what you clicked, what happened, what you expected. Check that:
  - clips open,
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
