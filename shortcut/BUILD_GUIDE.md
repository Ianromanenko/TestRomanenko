# Build guide — "Clean Screenshot" shortcut

Build this by hand in the **Shortcuts** app. It's the reliable path (the
importable `.plist` is a best-effort convenience — see the bottom of this file).
Total time ≈ 5 minutes.

> Have your **Anthropic API key** ready (<https://console.anthropic.com>).

---

## The actions, in order

Open Shortcuts → **+** (new shortcut) → name it *Clean Screenshot* → add these
actions one after another (search each name in the action picker).

### 1. Take Screenshot
- Action: **Take Screenshot**.
- Output: a screenshot image. (Magic variable name it produces: *Screenshot*.)

> Want it to run on a button press? After building, open the shortcut's
> settings (ⓘ) and add it to the Home Screen / Action Button / Back Tap, or
> set up a **Personal Automation** to trigger it. See *Triggering* below.

### 2. Get Details of Images
- Action: **Get Details of Images**, set to **Width**, input = *Screenshot*.
- Rename its output to **W** (tap the variable → Rename).
- Add a **second** *Get Details of Images* set to **Height**, input =
  *Screenshot*. Rename output to **H**.

These give you the pixel dimensions to multiply the fractions by.

### 3. Base64 Encode
- Action: **Base64 Encode**, input = *Screenshot*, Line Breaks = **None**.
- This is the `IMAGE_BASE64` that goes into the request.

### 4. Text — your API key
- Action: **Text**. Type your Anthropic API key into it (nothing else).
- This keeps the key in one obvious place.

### 5. Get Contents of URL  ← the "analyse it" step
- Action: **Get Contents of URL**.
- URL: `https://api.anthropic.com/v1/messages`
- Tap **Show More**:
  - **Method:** `POST`
  - **Headers:**
    - `x-api-key` → (insert the *Text* variable from step 4)
    - `anthropic-version` → `2023-06-01`
    - `content-type` → `application/json`
  - **Request Body:** **JSON**. Build this structure (the full body is in
    [`claude_request.md`](claude_request.md) — copy it field by field). The two
    spots that use variables:
    - `messages → [0] → content → [0] → source → data` = the **Base64 Encode**
      output from step 3.
    - Everything else is literal text from `claude_request.md`.

  Tip: building deep JSON in the Shortcuts editor is fiddly. The easiest way is
  to use a single **Text** action containing the whole body with the base64
  variable inlined, then set the request body to **File** = that Text. Either
  works.

### 6. Get Dictionary from Input
- Input = the **Get Contents of URL** output. Parses the API response.

### 7. Get Dictionary Value → `content`
- **Get Dictionary Value**, key = `content`, from the dictionary in step 6.
- The value is a **list**.

### 8. Get Item from List → First Item
- **Get Item from List**, First Item, from the `content` list.

### 9. Get Dictionary Value → `text`
- **Get Dictionary Value**, key = `text`, from the first item.
- This `text` is the JSON string `{"x":…,"y":…,"width":…,"height":…}`.

### 10. Get Dictionary from Input
- Parse that `text` into a dictionary so you can read the four numbers.

### 11. Calculate the crop rectangle
Add four **Calculate** (or **Math**) actions, each reading a key via *Get
Dictionary Value* on the step-10 dictionary:

| Variable | Formula |
|----------|---------|
| `CropW`  | `width  × W`  |
| `CropH`  | `height × H`  |
| `OffX`   | `x × W`       |
| `OffY`   | `y × H`       |

(Get Dictionary Value `width`, then a Calculate `× W`, etc.)

### 12. Crop Image
- Action: **Crop Image**, input = *Screenshot*.
- **Width** = `CropW`, **Height** = `CropH`.
- **Position** = **Custom**, **Custom Position** horizontal = `OffX`,
  vertical = `OffY`.

> If your iOS version's Crop Image only offers preset positions (Center, Top…)
> and no Custom offset, see *Fallback crop* below.

### 13. Save the result
Pick one final action:
- **Save to Photo Album** — drops the clean image in Photos, or
- **Quick Look** — preview it, or
- **Share** — send it on, or
- **Set Clipboard** — paste it anywhere.

Done. Run the shortcut; after a one-second API round-trip you get the cropped
image.

---

## Triggering it

"When triggered, take a screenshot…" — wire the trigger after building:

- **Back Tap** (fastest): Settings → Accessibility → Touch → Back Tap → Double
  Tap → pick *Clean Screenshot*. Now a double-tap on the back of the phone runs
  it.
- **Action Button** (iPhone 15 Pro+): Settings → Action Button → Shortcut →
  *Clean Screenshot*.
- **Home Screen**: shortcut ⓘ → **Add to Home Screen**.
- **Automation**: Shortcuts → Automation → you can't trigger on the system
  screenshot gesture directly, but you can run this from any of the above.

---

## Fallback crop (older iOS without Custom position)

If **Crop Image** has no custom-offset option, crop in two passes using the
percentage-based crop that every version supports:

1. **Crop Image**, Position **Top**, Height = `H − OffY` (removes everything
   above the content's top edge), then
2. **Crop Image**, Position **Bottom**, Height = `CropH` (trims the chrome below
   the content).

For horizontal margins repeat with Left/Right. For most screenshots the chrome
is only top+bottom, so the two passes above are enough.

---

## Hardening (optional, for sharing the shortcut)

Embedding the API key is fine for personal use but unsafe to share. To share
safely, put a tiny proxy in front of the key so the shortcut calls *your*
endpoint instead of Anthropic directly:

- A serverless function (Cloudflare Worker / Vercel / Lambda) that holds
  `ANTHROPIC_API_KEY` in an env var, forwards the body to
  `https://api.anthropic.com/v1/messages`, and returns the response.
- The shortcut then POSTs to your proxy URL with no secret in it.

---

## About `CleanScreenshot.plist`

`CleanScreenshot.plist` is a hand-authored shortcut definition. iOS can import
unsigned shortcut plists when **Settings → Shortcuts → Allow Untrusted
Shortcuts** is on, but Apple's signed-shortcut format is finicky and an
unsigned plist may not import cleanly on every iOS version. **Treat it as a
reference / starting point, not a guaranteed one-tap install** — the
hand-built version above is what's known to work. You still paste your API key
in either way.
