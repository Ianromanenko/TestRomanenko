# Clean Screenshot — iPhone Shortcut

An iOS Shortcut that, when triggered, **takes a screenshot, sends it to Claude's
vision model to locate the real content**, and **crops away the iOS status bar,
app navigation bars, tab bars, and other chrome** — leaving just the main
photo / image / artwork / map / etc.

```
 ┌─────────────────────────┐          ┌───────────────────┐
 │  9:41        ▢ ▢ ▢  100% │  ← iOS   │                   │
 ├─────────────────────────┤          │                   │
 │  ‹  Photo            ⋯   │  ← app   │      THE          │
 ├─────────────────────────┤   crop   │      ACTUAL       │
 │                         │  ──────► │      IMAGE        │
 │      THE ACTUAL         │          │                   │
 │        IMAGE            │          │                   │
 ├─────────────────────────┤          └───────────────────┘
 │  ▢   ▢   ▢   ▢   ▢      │  ← tabs
 └─────────────────────────┘
```

## How it works

The hard part is *"analyse it and remove the interface."* Status bars, nav
bars, and tab bars sit at different positions in every app, so a fixed crop
won't work. Instead the shortcut asks **Claude (vision)** to look at the
screenshot and return the bounding box of the real content as four numbers
(`x, y, width, height` as fractions `0–1`). The shortcut then converts those
fractions to pixels and crops.

```
Take Screenshot ─► Base64 ─► POST to Claude API ─► parse {x,y,w,h}
        └─────────────────────────────────────────────► Crop Image ─► Save / Share
```

## What's in here

| File | Purpose |
|------|---------|
| [`shortcut/BUILD_GUIDE.md`](shortcut/BUILD_GUIDE.md) | **Start here.** Step-by-step to build the shortcut by hand in the Shortcuts app. This is the reliable path. |
| [`shortcut/claude_request.md`](shortcut/claude_request.md) | The exact Claude API request/response the shortcut uses, with the prompt and JSON schema. |
| [`shortcut/CleanScreenshot.plist`](shortcut/CleanScreenshot.plist) | A best-effort importable shortcut file (see caveats in the build guide). |

## Requirements

- iPhone/iPad on iOS/iPadOS 15 or later (Shortcuts app, built in).
- An **Anthropic API key** — get one at <https://console.anthropic.com>. The
  vision call costs a fraction of a cent per screenshot.

## Quick start

1. Read [`shortcut/BUILD_GUIDE.md`](shortcut/BUILD_GUIDE.md) and build the
   shortcut (≈ 10 actions, ~5 minutes).
2. Paste your Anthropic API key into the one **Text** action.
3. Run it. The cropped image lands in Photos (or wherever you point the last
   action).

> Security note: the API key lives inside the shortcut on your device. That's
> fine for a personal shortcut. Don't share the shortcut with the key embedded.
> For sharing, swap the direct API call for a small proxy that holds the key
> server-side (see the build guide's "Hardening" section).
