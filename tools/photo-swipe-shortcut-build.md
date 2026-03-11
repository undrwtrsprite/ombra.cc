# Build this iPhone Shortcut: Delete rejected photos from Photo Swipe Review

This is the **smallest realistic Shortcut** for the web handoff.

## What it expects
From the website:
1. Tap **Done**
2. Tap **Copy JSON**
3. Run this Shortcut

The Shortcut reads the clipboard JSON, extracts rejected items, and helps you review before deletion.

---

## Important warning
Because the website does **not** have real Apple Photos asset IDs, this Shortcut can only try to match photos by metadata.

That means:
- it is **not perfectly reliable**
- you should **test on a tiny batch first**
- you should **review before deleting**

If you want perfect matching, the real fix is a native iPhone app.

---

## Shortcut name
**Delete Rejected Photos**

---

## Minimal version (recommended first)
This version does **review only** and prepares you for deletion safely.

### Actions

1. **Get Clipboard**
2. **Get Dictionary from Input**
3. **Get Dictionary Value**
   - Key: `rejected`
4. **If** Dictionary Value `has any value`
   - otherwise show alert: `No rejected photos found in clipboard JSON.`
5. **Repeat with Each** item in `rejected`
6. Inside the repeat:
   - **Get Dictionary Value** → `name`
   - **Get Dictionary Value** → `lastModifiedISO`
   - **Get Dictionary Value** → `sizeKB`
   - **Text** action with something like:
     ```
     Name: [name]
     Modified: [lastModifiedISO]
     Size KB: [sizeKB]
     ```
   - **Add to Variable** → `Rejected Review List`
7. After repeat:
   - **Quick Look** → `Rejected Review List`
   - **Show Alert** → `Now manually find/delete these in Photos, or build the advanced version below.`

This version is dumb but safe.

---

## Advanced version (attempt actual matching)
This is the closest thing to what you want in Shortcuts.

### Goal
For each rejected item:
- read filename + modified time
- search Photos for likely matches
- build a candidate list
- let you review
- then delete confirmed matches

### Actions

1. **Get Clipboard**
2. **Get Dictionary from Input**
3. **Get Dictionary Value**
   - Key: `rejected`
4. **If** result is empty
   - **Show Alert**: `No rejected photos found in clipboard JSON.`
   - **Stop This Shortcut**
5. **Set Variable** → `DeleteCandidates` = empty list
6. **Repeat with Each** item in `rejected`

### Inside Repeat
7. **Get Dictionary Value** from Repeat Item
   - key: `name`
   - set variable `PhotoName`
8. **Get Dictionary Value** from Repeat Item
   - key: `lastModifiedISO`
   - set variable `PhotoModified`
9. **Get Dictionary Value** from Repeat Item
   - key: `sizeKB`
   - set variable `PhotoSizeKB`

10. **Find Photos**
   - Filter: **Media Type is Image**
   - Sort by: Creation Date
   - Order: Latest First
   - Limit: maybe 20

11. Optional narrowing:
   - if your Shortcuts version allows date filtering, narrow around `PhotoModified`
   - otherwise keep the candidate pool small and review visually

12. **Choose from List**
   - Input: results from `Find Photos`
   - Prompt: `Pick matching photo for [PhotoName]`
   - Select Multiple: Off
   - This is the human safety step

13. **If** a photo was chosen
   - **Add to Variable** → `DeleteCandidates`

### After Repeat
14. **If** `DeleteCandidates` is empty
   - **Show Alert**: `No photos selected for deletion.`
   - **Stop This Shortcut**
15. **Quick Look** → `DeleteCandidates`
16. **Ask for Confirmation**
   - `Delete selected photos?`
17. **Delete Photos** → `DeleteCandidates`

That should trigger the normal Apple delete confirmation behavior.

---

## Easiest practical setup
Honestly, this is the least painful path:

### Shortcut A — Review Rejected JSON
- reads clipboard
- shows clean rejected list

### Shortcut B — Delete Chosen Photos
- launched manually from the review process
- you select the photos yourself
- then delete

It’s less magical, but way less cursed.

---

## Suggested variable names
- `RejectedItems`
- `RejectedReviewList`
- `DeleteCandidates`
- `PhotoName`
- `PhotoModified`
- `PhotoSizeKB`

---

## Best next improvement
If you want, the next step is for me to write a **super exact action-by-action version** using Shortcuts action names in order, like:
- tap this action
- set this field
- use this variable

That’ll be the fastest to recreate on your iPhone.
