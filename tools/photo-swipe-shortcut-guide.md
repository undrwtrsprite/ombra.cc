# Photo Swipe Review → iPhone Shortcuts guide

This is the safest possible web-first workaround.

## Important limitation
`Photo Swipe Review` runs in Safari/PWA, so it **does not get real Apple Photos asset IDs**.
That means the exported JSON contains only metadata such as:
- filename
- file size
- MIME type
- last modified time
- rejected timestamp

A Shortcut must use that metadata to find likely matches in the Photos library.
Because of that, you should always **review matches before deleting**.

## Recommended flow
1. Open `Photo Swipe Review` on iPhone.
2. Choose a batch of photos.
3. Swipe through them.
4. Tap **Done**.
5. Tap **Copy JSON** or **Download JSON**.
6. Run a Shortcut that:
   - reads the JSON
   - loops over rejected items
   - finds likely Photos matches
   - shows a review list
   - asks for confirmation
   - deletes only the confirmed matches

## Shortcut outline

### Option A — JSON from clipboard
Use this if you tap **Copy JSON** in the tool.

Suggested Shortcut actions:
1. **Get Clipboard**
2. **Get Dictionary from Input**
3. **Get Dictionary Value** → key: `rejected`
4. **Repeat with Each** item in rejected list
5. For each item:
   - get `name`
   - get `lastModifiedISO`
   - get `size`
   - use **Find Photos** with a date filter close to the modified date if possible
   - narrow the candidates manually/review step
6. Build a candidate list
7. **Choose from List** or **Quick Look**
8. **Ask for Input / Ask for Confirmation**
9. **Delete Photos**

### Option B — JSON file from share sheet / Files
Use this if you tap **Download JSON**.

Suggested Shortcut actions:
1. **Receive File** or **Get File**
2. **Get Contents of File**
3. **Get Dictionary from Input**
4. Then the same matching/review flow as above

## Matching strategy
Best available fields from the website export:
- `name`
- `size`
- `type`
- `lastModified`
- `lastModifiedISO`

Practical advice:
- use filename first
- narrow by date/time window second
- preview the candidate photo before delete
- test with a tiny batch first

## Safety advice
- Start with 3–5 photos, not 500
- Expect duplicate filenames sometimes
- Edited copies and Live Photos can be weird
- Always review the final match list before delete

## If you want the clean version
A native SwiftUI app with PhotoKit is the proper route.
That gives real asset references and the normal iPhone delete confirmation flow.
