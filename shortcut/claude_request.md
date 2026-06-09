# The Claude vision call

This is the request the shortcut sends in the **Get Contents of URL** action.
It hands Claude the screenshot and asks for the bounding box of the main
content, returned as strict JSON so the shortcut can parse it without guessing.

## Endpoint

```
POST https://api.anthropic.com/v1/messages
```

## Headers

| Header | Value |
|--------|-------|
| `x-api-key` | `YOUR_ANTHROPIC_API_KEY` |
| `anthropic-version` | `2023-06-01` |
| `content-type` | `application/json` |

## Request body

`IMAGE_BASE64` is the screenshot from the **Base64 Encode** action.
`output_config.format` forces Claude to reply with exactly the JSON shape we
want — no prose, no code fences — so the shortcut's *Get Dictionary Value*
steps always find the keys.

```json
{
  "model": "claude-opus-4-8",
  "max_tokens": 1024,
  "system": "You are given a screenshot taken on an iPhone. Identify the single main content region — the primary photo, image, artwork, video frame, map, or document that the user actually cares about. EXCLUDE all interface chrome: the iOS status bar (clock, signal, battery), app navigation/title bars, toolbars, tab bars, search bars, captions, and side margins. Return the bounding box of just that content region as fractions of the full image, where 0,0 is the top-left corner and 1,1 is the bottom-right. If the whole image is already content, return x=0, y=0, width=1, height=1.",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "image",
          "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": "IMAGE_BASE64"
          }
        },
        { "type": "text", "text": "Return the bounding box of the main content." }
      ]
    }
  ],
  "output_config": {
    "format": {
      "type": "json_schema",
      "schema": {
        "type": "object",
        "properties": {
          "x":      { "type": "number" },
          "y":      { "type": "number" },
          "width":  { "type": "number" },
          "height": { "type": "number" }
        },
        "required": ["x", "y", "width", "height"],
        "additionalProperties": false
      }
    }
  }
}
```

## Response

A normal Messages API response. The JSON we want is the text of the first
content block:

```json
{
  "id": "msg_…",
  "type": "message",
  "role": "assistant",
  "content": [
    { "type": "text", "text": "{\"x\":0.0,\"y\":0.12,\"width\":1.0,\"height\":0.74}" }
  ],
  "stop_reason": "end_turn",
  "usage": { "input_tokens": 1610, "output_tokens": 33 }
}
```

In the shortcut you reach the fractions with **Get Dictionary Value**:

- `content` → it's a list → **Get Item (First)** from list → key `text`.
- That `text` is itself a JSON string → **Get Dictionary from Input** → then
  read keys `x`, `y`, `width`, `height`.

## Converting fractions → pixels for the crop

With image `W × H` (from *Get Details of Images* → Width / Height):

```
cropWidth  = width  × W
cropHeight = height × H
offsetX    = x × W      (left edge of the crop)
offsetY    = y × H      (top edge of the crop)
```

The Shortcuts **Crop Image** action with **Position = Custom** takes a custom
horizontal/vertical offset plus the width and height — feed it the four values
above. See the build guide for the exact field mapping.

## Model / cost notes

- `claude-opus-4-8` gives the most reliable region detection. For a cheaper,
  faster call you can switch `"model"` to `"claude-haiku-4-5"` — it handles
  this localization task well and costs ~5× less.
- A single screenshot is ~1.5–2K input tokens + ~30 output tokens, well under a
  cent on Opus and a fraction of that on Haiku.
