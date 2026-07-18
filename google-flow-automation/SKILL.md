---
name: google-flow-automation
description: Automate image generation, configuration, and headless downloads on Google Labs Flow using playwright-cli exclusively.
allowed-tools: Bash(playwright-cli:*)
---

# Google Labs Flow Automation Skill

Complete operational reference for automating **Google Labs Flow** (`https://labs.google/fx/tools/flow`) using `playwright-cli` exclusively. No manual Playwright code injection needed for standard workflows.

> **CRITICAL:** Always use `pw-bridge.bat` (or `pw-bridge.ps1`) commands via `playwright-cli`. Never attempt to run automation code locally or outside the bridge. Prefer `pw-bridge.bat <command>` or ref-based clicks over scripted code blocks wherever possible.

---

## 0. Bridge Setup (Prerequisites)

Before any automation, **always check first** whether a compatible browser session is already running before prompting the user to do anything.

### Step 0a — Check if Browser with CDP is Already Running

First, silently probe the CDP endpoint:
```powershell
try {
    $r = Invoke-WebRequest -Uri "http://localhost:9222/json/version" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "Browser already running with CDP. Proceeding."
} catch {
    Write-Host "No browser with CDP found. Must launch one."
}
```
- **If the request succeeds (HTTP 200):** A browser is already running with remote debugging on port `9222`. Skip to Step 0b immediately — do NOT ask the user to launch a browser.
- **If the request fails/times out:** No compatible browser is running. Proceed to launch one.

### Step 0a (Fallback) — Launch Browser if NOT Running

Only run this if the CDP check above failed:
```powershell
taskkill /f /im brave.exe 2>$null
schtasks /create /tn "LaunchBraveDebug" /tr "cmd.exe /c d:\AI\launch_brave_rp.bat" /sc once /sd "01/01/2099" /st "00:00" /f
schtasks /run /tn "LaunchBraveDebug"
Start-Sleep -Seconds 2
schtasks /delete /tn "LaunchBraveDebug" /f
```
> **IMPORTANT:** The launch scripts open the browser without forcing a specific profile. After launching, **ask the user to select their preferred profile** from the profile picker and confirm before proceeding.

### Step 0b — Ensure Bridge Server is Running

Check if the bridge server is already listening on port `8080`:
```powershell
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:8080/health" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "Bridge server already running."
} catch {
    Write-Host "Starting bridge server..."
    Start-Process python -ArgumentList "d:\AI\pw_bridge_server.py" -WindowStyle Hidden
    Start-Sleep -Seconds 2
}
```

### Step 0c — Attach the Session
```powershell
.\pw-bridge.bat attach --cdp=http://localhost:9222
```

All subsequent commands use `.\pw-bridge.bat <command>` from `d:\AI`.

---

## 1. Initial Project Setup

### Navigate & Create New Project
```powershell
.\pw-bridge.bat goto https://labs.google/fx/tools/flow
# Wait for page to load, then click New Project:
.\pw-bridge.bat click "add_2 New project"
# Wait 3-4 seconds for the project workspace to initialize
```

**Key selector:** `getByRole('button', { name: 'add_2 New project' })`

### Disable Agent Mode (Always Do This First)
By default every new project opens in Agent mode. This must be closed:
```powershell
# Step 1: Close the Agent chat panel
.\pw-bridge.bat click "close Close"
# Step 2: Untick the Agent toggle button
.\pw-bridge.bat click "Agent"
```

**Selectors:**
- Close button: `getByRole('button', { name: 'close Close' })`
- Agent toggle: `getByRole('button', { name: 'Agent', exact: true })`

### Snapshot to Confirm State
```powershell
.\pw-bridge.bat snapshot
```
Confirm the page shows the prompt textbox with placeholder `"What do you want to create?"` and the settings preset button in the toolbar.

---

## 2. Settings Preset Popover

The toolbar contains a dynamic preset button showing the current mode and settings (e.g., `"Video 🎬 8s crop_16_9 x2"` or `"Banana 2 crop_16_9 x2"`). Click it to open the quick settings popover:

```powershell
# The button text changes dynamically. Use snapshot to find the exact ref, then:
.\pw-bridge.bat click <ref>
# Example: .\pw-bridge.bat click f21e85
```

After clicking, take a snapshot to see the full settings menu. Close with:
```powershell
.\pw-bridge.bat press Escape
```

---

## 3. Image Generation

### Switch to Image Mode
```powershell
.\pw-bridge.bat click "image Image"
```
**Selector:** `getByRole('tab', { name: 'image Image' })`

### Image Settings
| Setting | CLI Command | Options |
|---|---|---|
| Aspect Ratio 16:9 | `.\pw-bridge.bat click "crop_16_9 16:9"` | Also: 4:3, 1:1, 3:4, 9:16 |
| Aspect Ratio 4:3 | `.\pw-bridge.bat click "crop_landscape 4:3"` | |
| Aspect Ratio 1:1 | `.\pw-bridge.bat click "crop_square 1:1"` | |
| Aspect Ratio 3:4 | `.\pw-bridge.bat click "crop_portrait 3:4"` | |
| Aspect Ratio 9:16 | `.\pw-bridge.bat click "crop_9_16 9:16"` | |
| Batch Count | `.\pw-bridge.bat click "1x"` / `"x2"` / `"x3"` / `"x4"` | Default: x2 |
| Model | `.\pw-bridge.bat click "<model_button_ref>"` | See models below |

### Image Models (Click the Model Dropdown First)
- `Banana Pro` → **Imagen 3 Pro** (highest quality, slowest)
- `Banana 2` → **Imagen 3** (balanced)
- `Banana 2 Lite` → **Imagen 3 Fast** (fastest, lower quality)

### Generating an Image
```powershell
# Close settings popover first
.\pw-bridge.bat press Escape

# Fill the prompt textbox
.\pw-bridge.bat fill f<ref> "Your creative prompt here"

# Press Enter to trigger generation
.\pw-bridge.bat press Enter
```
**Prompt textbox selector:** `getByRole('textbox')` (the one with placeholder `"What do you want to create?"`)

### Monitoring Image Generation Progress
After pressing Enter, cards appear in the media grid with percentage indicators (e.g., `57%`, `70%`). Poll with snapshots until the percentages are gone:
```powershell
.\pw-bridge.bat snapshot
# Look for absence of "57%" / "70%" etc. and presence of image card links
# Typical wait: 30-90 seconds for images
```
**Completion indicator:** Cards become `link` elements with `/fx/tools/flow/project/<id>/edit/<image_id>` URLs.

### Downloading Images (Headless — No OS Dialog)
Images require a DOM hook because Flow dynamically creates `<a>` download tags. Inject the hook via a `.js` script file:

**Step 1:** Create the hook script (save to a local `.js` file):
```js
async page => {
  await page.evaluate(() => {
    window.capturedDownload = null;
    const originalCreateElement = document.createElement;
    document.createElement = function(tagName, options) {
      const el = originalCreateElement.call(document, tagName, options);
      if (tagName.toLowerCase() === 'a') {
        const originalClick = el.click;
        el.click = function() {
          if (el.href) {
            fetch(el.href)
              .then(res => res.blob())
              .then(blob => {
                const reader = new FileReader();
                reader.onloadend = () => {
                  window.capturedDownload = {
                    filename: el.download || "download.jpeg",
                    base64: reader.result.split(';base64,').pop()
                  };
                };
                reader.readAsDataURL(blob);
              })
              .catch(err => { window.capturedDownload = { error: err.toString() }; });
            return; // Block OS dialog
          }
          return originalClick.apply(this, arguments);
        };
      }
      return el;
    };
  });
}
```

**Step 2:** Navigate to the image edit URL and run the hook:
```powershell
.\pw-bridge.bat goto https://labs.google/fx/tools/flow/project/<project_id>/edit/<image_id>
.\pw-bridge.bat run-code --filename="path\to\hook.js"
```

**Step 3:** Click the Download button and select resolution:
```powershell
.\pw-bridge.bat click "download Download"
# For 1K original:
.\pw-bridge.bat click "1K Original size"
# For 2K upscaled (triggers backend upscaling — wait up to 60s):
.\pw-bridge.bat click "2K Upscaled"
```

**Step 4:** Poll `window.capturedDownload` until populated, then decode base64 and save to disk using a Python wrapper script.

---

## 4. Video Generation

### Switch to Video Mode
```powershell
.\pw-bridge.bat click "play_circle Video"
```
**Selector:** `getByRole('tab', { name: 'play_circle Video' })`

### Video Settings
| Setting | CLI Command | Options |
|---|---|---|
| Aspect Ratio 16:9 | `.\pw-bridge.bat click "crop_16_9 16:9"` | Only 16:9 and 9:16 available for video |
| Aspect Ratio 9:16 | `.\pw-bridge.bat click "crop_9_16 9:16"` | |
| Batch Count | `.\pw-bridge.bat click "1x"` / `"x2"` / `"x3"` / `"x4"` | Default: x2 |
| Duration | `.\pw-bridge.bat click "4s"` / `"6s"` / `"8s"` / `"10s"` | Default: 8s |
| Sub-tab Frames | `.\pw-bridge.bat click "crop_free Frames"` | For keyframe storyboarding |
| Sub-tab Ingredients | `.\pw-bridge.bat click "chrome_extension Ingredients"` | For reference assets/characters |
| Model | See models below | |

### Video Sub-Tabs
- **Frames** (`crop_free Frames`): Storyboard/keyframe-based generation.
- **Ingredients** (`chrome_extension Ingredients`): Attach characters, reference images, or assets to influence the video.

### Video Models
Open the model dropdown (the button showing current model, e.g., `"Omni Flash arrow_drop_down"`):
```powershell
.\pw-bridge.bat click "Omni Flash arrow_drop_down"
```

Available models:
| Model | Use Case |
|---|---|
| `Omni Flash` | Fastest, good quality (default) |
| `Veo 3.1 - Lite` | Lighter Veo model |
| `Veo 3.1 - Fast` | Fast Veo generation |
| `Veo 3.1 - Quality` | Best quality, slowest |

Select a model:
```powershell
.\pw-bridge.bat click "volume_up Veo 3.1 - Quality"
# Or:
.\pw-bridge.bat click "volume_up Omni Flash"
```

### Generating a Video
```powershell
# Close settings popover
.\pw-bridge.bat press Escape

# Fill the prompt
.\pw-bridge.bat fill f<textbox_ref> "Your video prompt here"

# Submit
.\pw-bridge.bat press Enter
```

### Monitoring Video Generation Progress
After triggering, video cards appear in the media grid:
```powershell
.\pw-bridge.bat snapshot
# Look for percentage indicators like "27%", "65%" next to play_circle icons
# Typical wait: 3-6 minutes for 8s Omni Flash clips
```
**Completion indicator:** Percentage text disappears. Cards show `img "Video thumbnail"` inside a link to the edit URL. There is NO download button on the project page — you must click into the video editor URL.

### Downloading Videos (CLI Native — No DOM Hook Needed!)

Videos use **signed CDN URLs** that do NOT require cookies or auth headers. This is the cleanest download method:

**Step 1:** Navigate to the video edit URL (found in the link `href` from the snapshot):
```powershell
.\pw-bridge.bat goto https://labs.google/fx/tools/flow/project/<project_id>/edit/<video_id>
```
This causes the browser to request the video stream, which gets logged in the network request list.

**Step 2:** Dump the network requests:
```powershell
.\pw-bridge.bat requests > requests.txt
```

**Step 3:** Search for the CDN video URL — it looks like:
```
[GET] https://flow-content.google/video/<uuid>?Expires=<timestamp>&KeyName=labs-flow-prod-cdn-key&Signature=<sig> => [206]
```

**Step 4:** Download directly using PowerShell (no browser session needed):
```powershell
Invoke-WebRequest -Uri "<full_signed_cdn_url>" -OutFile "d:\AI\output_video.mp4"
```

**Why this works:** Flow pre-signs the CDN URL with `Expires`, `KeyName`, and `Signature` query parameters. The signed URL is self-authenticating — any HTTP client can fetch it without cookies. The URL remains valid until the `Expires` timestamp (typically ~8 hours).

### Full Video Download Automation Script
```powershell
# 1. Navigate to video editor to trigger stream request
.\pw-bridge.bat goto https://labs.google/fx/tools/flow/project/<project_id>/edit/<video_id>

# 2. Dump requests
.\pw-bridge.bat requests > C:\tmp\flow_requests.txt

# 3. Extract the CDN URL (PowerShell)
$videoUrl = (Get-Content C:\tmp\flow_requests.txt | Select-String "flow-content.google/video" | Select-Object -First 1) -replace '.*\[GET\] (https://flow-content\.google/video/[^\s]+) =>.*', '$1'

# 4. Download
Invoke-WebRequest -Uri $videoUrl -OutFile "d:\AI\generated_video.mp4"

# 5. Confirm
Get-Item "d:\AI\generated_video.mp4" | Select-Object Name, Length
```

---

## 5. Navigation & Project Management

### Useful CLI Ref Patterns from Snapshots
| Element | Selector Pattern |
|---|---|
| Go Back to projects | `getByRole('button', { name: 'arrow_back Go Back' })` |
| All Media (sidebar) | `getByRole('button', { name: 'dashboard All Media' })` |
| Videos (sidebar) | `getByRole('button', { name: 'videocam View videos' })` |
| Characters (sidebar) | `getByRole('button', { name: 'accessibility_new Characters' })` |
| Scenes (sidebar) | `getByRole('button', { name: 'movie View scenes' })` |
| Trash (sidebar) | `getByRole('button', { name: 'delete View Trash' })` |
| Collapse sidebar | `getByRole('button', { name: 'left_panel_close Collapse' })` |
| Project title textbox | `getByRole('textbox', { name: 'Editable text' })` |

### Key URL Patterns
| URL Pattern | Description |
|---|---|
| `/fx/tools/flow` | Flow home, shows all projects |
| `/fx/tools/flow/project/<project_id>` | Project media grid |
| `/fx/tools/flow/project/<project_id>/edit/<media_id>` | Individual image/video editor |

---

## 6. Important Notes & Gotchas

- **`run-code` with file paths:** Always use `--filename=` flag. Absolute Windows paths work.
- **Ref IDs are session-scoped:** Refs like `f21e85` change per page load. Always take a fresh `snapshot` to get current refs before clicking.
- **Video generation is slow:** Expect 3–6 minutes for an 8s clip. The progress percentage (`27%`) stays in that range for most of the wait time before suddenly jumping to completion.
- **Video CDN URLs expire:** The signed `flow-content.google` URL typically has an 8-hour TTL from the `Expires` parameter. Download immediately after generation to avoid expiry.
- **Image downloads require DOM hook:** Unlike videos, images use dynamically created anchor tags. The DOM interception hook (Section 3) is required for headless image downloads.
- **Credit cost for videos:** The settings popover shows credit cost (e.g., `"Generating will use 24 credits"`). 2K image upscaling also consumes additional credits.
- **Agent Mode:** ALWAYS disable Agent Mode after creating a new project. It interferes with direct prompt input and automated workflows.
