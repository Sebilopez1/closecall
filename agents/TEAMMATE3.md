# CloseCall — Teammate 3: Labels & Testing

Real-Time Video Agents Hack NYC · Friday, October 9, 2026 · build 9:30 AM–4:30 PM ET

**Your job:** you make the answer key the whole project is graded against, then you test the app like a real city traffic engineer. You don't need a build machine (only two people per team get one).

**What we're building (1 line):** CloseCall finds near misses between people and cars in dashcam video, lets a person approve or reject each one, and reports how often it's right.

---

## Before you arrive (do now)
- ✗ Confirm you're **registered and accepted** for the event (check your email or Luma). Applications closed October 2. If you're not on the list, message the hosts on Luma right away.
- ✗ Have a GitHub account. Send Sebi your username, then accept his invite to `Sebilopez1/closecall`.
- ✗ Join the Cosmos Community at community.vastdata.com. It may let you open the team's app from your laptop.
- ✗ Read the labeling rules at the bottom twice.
- ✗ Bring laptop, charger and a government photo ID. Arrive by 8:15.

## At the event
- ✗ **9:30–10:15:** Sit next to Sebi. Learn how to open a clip; his agent writes the instructions in `closecall/notes/schema.md` around 9:50. Try opening one clip from your laptop at workshop.thecosmoslabs.com. If clips only open on the build machines, you'll label at Sebi's screen.
- ✗ **~10:15, when Sebi says "LABELS READY":** you label **clips 1–40**:
  1. Open `github.com/Sebilopez1/closecall/blob/main/labels/labels_sebi.csv` and tap the **pencil (Edit)** icon.
  2. Each line looks like `7,seg_123,<how to view>,`. Watch that clip, then type the label right after the last comma: `CLOSE_CALL`, `NO_CONFLICT` or `CANT_TELL` (exact spelling, no spaces).
  3. Tap **Commit changes** every 10 clips so nothing gets lost.
  - Don't look at the AI's answers or the app while labeling, and don't discuss labels with Teammate 4 until you're both done. Your overlap (clips 21–40) is how we measure agreement.
- ✗ **By 11:00:** all 40 labeled and committed. Tell Sebi "labels done".
- ✗ **11:30–2:30, tester:** when Grant says the app is live, use it like a city engineer. Use the reviewer name **`test`** so your clicks don't count. Every 30 minutes, send Grant a short bug list: what you clicked, what happened, what you expected. Check that:
  - clips open,
  - Approve and Reject save,
  - the Decision log updates,
  - the Accuracy and Data & Limits tabs load,
  - nothing is slow or confusing.
- ✗ **~1:45:** Sebi's agent shows the 5 clips where the AI disagreed with the labels. Watch them with Sebi and say who's right.
- ✗ **3:15–4:15:** play the judge in rehearsals and ask the hard questions (see Teammate 4's list).
- ✗ **4:30–6:30, at the table:** if judges ask how we measured accuracy, say: "Two of us labeled the clips blind, without seeing the AI's answers, and we measured how often we agreed."

## Labeling rules
- **CLOSE_CALL:** a person (walking or on a bike) in or entering the road comes within about one car length of a moving vehicle, **or** someone has to react suddenly (hard braking, swerving, stopping short, jumping back).
- **NO_CONFLICT:** the person is on the sidewalk or far from the car's path, the car is stopped or parked, or the crossing is normal with plenty of room.
- **CANT_TELL:** something is hidden, too dark or blurry, or the clip ends before you can see what happens.
- When unsure between CLOSE_CALL and NO_CONFLICT, ask yourself: "Would a traffic engineer want to see this?" If you still can't decide, choose CANT_TELL.
