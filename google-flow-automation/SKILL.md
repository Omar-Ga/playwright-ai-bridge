---
name: google-flow-automation
description: Automate image generation, configuration, and headless downloads on Google Labs Flow using playwright-cli exclusively.
---

# Google Labs Flow Automation Skill

## CRITICAL — Read This First

- **Everything is done exclusively through the Playwright CLI bridge (`pw-bridge.bat`).**
- No Python scripts, no `.js` files, no external tools. Pure CLI only.
- All commands are run from `d:\AI` using `.\pw-bridge.bat <command>`.
- **Always start from the Flow homepage and create a new project.** Never assume an existing workspace is usable.

---

## Step 0 — Check for Brave Debugging Session

Before doing anything else, check if Brave is already open with a remote debugging session:

```powershell
try {
    Invoke-WebRequest -Uri "http://localhost:9222/json/version" -TimeoutSec 3 -ErrorAction Stop
    Write-Output "Brave debug session found. Proceeding."
} catch {
    Write-Output "No Brave debug session found."
}
```

- **If it succeeds:** Proceed to attach below.
- **If it fails:** **Stop and ask the user to open Brave in debug mode.** Do not try to launch it yourself. Say: *"Please open Brave in debug mode. You can do this by running `d:\AI\launch_brave_rp.bat` or starting Brave with `--remote-debugging-port=9222`. Let me know when it's ready."*

Once the user confirms Brave is running, check the bridge server and attach:

```powershell
# Check bridge server
try {
    Invoke-WebRequest -Uri "http://127.0.0.1:8080/health" -TimeoutSec 3 -ErrorAction Stop
} catch {
    Start-Process python -ArgumentList "d:\AI\pw_bridge_server.py" -WindowStyle Hidden
    Start-Sleep -Seconds 2
}

# Attach to Brave
.\pw-bridge.bat attach --cdp=http://localhost:9222
```

---

## Step 1 — Navigate to Flow & Create a New Project

**Always navigate fresh to the Flow homepage:**
```powershell
.\pw-bridge.bat goto https://labs.google/fx/tools/flow
Start-Sleep -Seconds 3
.\pw-bridge.bat snapshot
```

From the snapshot, you will see a list of existing projects. **Always create a new one:**
```powershell
.\pw-bridge.bat click "text=New project"
Start-Sleep -Seconds 4
.\pw-bridge.bat snapshot
```

**Disable Agent Mode (if it appears):**
Google Flow sometimes opens an Agent mode dialog by default. Check the snapshot—if you see `"close Close"` and `"Agent"`, dismiss it:
```powershell
.\pw-bridge.bat click "text=Close"
Start-Sleep -Seconds 1
.\pw-bridge.bat click "text=Agent"
Start-Sleep -Seconds 1
.\pw-bridge.bat snapshot
```

After this snapshot you should see the main workspace with a prompt textbox at the bottom and an empty media grid.

---

## Step 2 — Configure Settings (Before Generating)

### Image vs Video Mode
The toolbar at the bottom shows a toggle. By default it's in **Image** mode. You can see the current mode in the snapshot — the active button will be visible. To switch:
```powershell
.\pw-bridge.bat click "image Image"    # Switch to Image mode
.\pw-bridge.bat click "play_circle Video"  # Switch to Video mode
```

### Choosing the Image Model
The current model is shown as a button in the bottom toolbar. Due to unicode prefixes like `??`, always use a robust text locator to open the model dropdown:

```powershell
.\pw-bridge.bat click "button:has-text('Nano Banana')"  # Click the active model selector button
Start-Sleep -Seconds 1
.\pw-bridge.bat snapshot  # A dropdown of model options will appear
```

**Available Image Models:**
| Model Name (in dropdown) | What it is | Best for |
|---|---|---|
| `Nano Banana Pro` | Imagen 3 Pro | Highest quality, most detailed, slowest |
| `Nano Banana 2` | Imagen 3 | Balanced — the default, great for most use |
| `Nano Banana 2 Lite` | Imagen 3 Fast | Fastest, lower detail, good for quick tests |

Click your chosen model:
```powershell
.\pw-bridge.bat click "Nano Banana 2 Lite"
```

### Aspect Ratio
The aspect ratio button is visible in the toolbar alongside the model button (e.g., `crop_16_9`). After opening the model dropdown you may also see aspect ratio options. Common choices:
```powershell
.\pw-bridge.bat click "crop_16_9"   # 16:9 landscape
.\pw-bridge.bat click "crop_9_16"   # 9:16 portrait
.\pw-bridge.bat click "crop_1_1"    # 1:1 square
```

### Batch Size (How Many Images per Generation)
The `x2` or `x4` button next to the model selector controls how many images per run:
```powershell
.\pw-bridge.bat click "x2"   # Generate 2 images at a time
.\pw-bridge.bat click "x4"   # Generate 4 images at a time
```

---

## Step 3 — Enter Prompt & Generate Images

**Enter the prompt using the Progressive Fill Algorithm (Bot Evasion):**
*Never* use the instantaneous CLI `fill` command. Use `run-code` to simulate human typing with a randomized delay (100-200ms) between characters to avoid triggering "unusual activity" blocks.

```powershell
.\pw-bridge.bat run-code "async page => { const tb = page.getByRole('textbox').last(); await tb.click({ force: true }); const text = 'A photorealistic wolf howling at a full moon over a misty forest'; let currentText = ''; for (const char of text) { currentText += char; await tb.fill(currentText); const delay = Math.floor(Math.random() * 350) + 50; await page.waitForTimeout(delay); } }"
Start-Sleep -Seconds 2
```

**Click Create:**
Make sure to target the main prompt's create button by using `nth=1` (as `nth=0` often hits the Agent's create button instead).
```powershell
.\pw-bridge.bat click "button:has-text('Create') >> nth=1"
```

**Wait for generation to complete** (typically 15–30 seconds):
Use short 5-second polling bursts to check for completion instead of one long sleep:
```powershell
Start-Sleep -Seconds 5
.\pw-bridge.bat snapshot
# If still generating (percentage visible), repeat the 5-second sleep and snapshot.
```

**How to confirm generation is done:**
In the snapshot, look for image card entries with links like `/fx/tools/flow/project/<project_id>/edit/<image_id>`. When you see those links and no percentage indicators (like `57%`), generation is complete.

**To generate more images (additional prompts):**
The prompt box automatically clears itself after you click Create. Simply type the next prompt progressively:
```powershell
.\pw-bridge.bat run-code "async page => { const tb = page.getByRole('textbox').last(); await tb.click({ force: true }); const text = 'Your next prompt here'; let currentText = ''; for (const char of text) { currentText += char; await tb.fill(currentText); const delay = Math.floor(Math.random() * 350) + 50; await page.waitForTimeout(delay); } }"
Start-Sleep -Seconds 2
.\pw-bridge.bat click "button:has-text('Create') >> nth=1"
```

## Handling Bot Detection ("Unusual Activity")
If your typing speed or behavior gets flagged by Google Flow, you will see a red error banner on the image card: `"We noticed some unusual activity."`
If this happens, the most human-like behavior is to simply click the **Retry** button on the failed card. Since `text=Retry` can sometimes be brittle due to inner spans, use the `has-text` selector on the button element:
```powershell
.\pw-bridge.bat click "button:has-text('Retry')"
Start-Sleep -Seconds 5
.\pw-bridge.bat snapshot
# If still generating, repeat the 5-second sleep and snapshot.
```

---

## Step 4 — Downloading Images (Native CLI Network Intercept)

This is the key method. **No hooks, no scripts — just Playwright's built-in network capture.**

### 4a — Download 1K Original (Already in Cache)

When an image is displayed in the grid, the browser has already downloaded it. Run:
```powershell
.\pw-bridge.bat requests --static
```

Scan the output for a `[GET]` request to `https://flow-content.google/image/...`. It will look like:
```
94. [GET] https://flow-content.google/image/d4ee01bf-403e-4973-a61f-07f64b4b67c9?Expires=...&Signature=... => [200]
```

Extract and save it:
```powershell
.\pw-bridge.bat response-body 94
```

The CLI will detect it is a binary image file and **automatically save it to `.playwright-cli\response-TIMESTAMP.jpg`** and print the path. Then move it to the workspace:
```powershell
Copy-Item "d:\AI\.playwright-cli\response-TIMESTAMP.jpg" "d:\AI\<destination>\image_1k.jpg"
```

> There will be one `flow-content.google/image/` request per image displayed on screen. If there are 6 images, there will be 6 such requests. Save each one by running `response-body` on each index.

### 4b — Download 2K Upscaled

The 2K version is generated on-demand by the server. Trigger it with a click:

```powershell
# Hover over the first image to reveal action buttons
.\pw-bridge.bat hover "img[alt='Generated image'] >> nth=0"
Start-Sleep -Seconds 1

# Click the 3-dot More menu — check snapshot for which nth index is correct
.\pw-bridge.bat click "button:has-text('More') >> nth=2"
Start-Sleep -Seconds 1

# Hover Download to expand the resolution submenu
.\pw-bridge.bat hover "text=Download"
Start-Sleep -Seconds 1

# Click 2K to trigger server-side upscaling
.\pw-bridge.bat click "text=2K"
Start-Sleep -Seconds 30
```

Then check requests for the new `upsampleImage` API call:
```powershell
.\pw-bridge.bat requests --static
```

Look for:
```
112. [POST] https://aisandbox-pa.googleapis.com/v1/flow/upsampleImage => [200]
```

Save the response (it contains the 2K image as Base64 JSON):
```powershell
.\pw-bridge.bat response-body 112 > "d:\AI\<destination>\upscale_response.json"
```

Decode it to a PNG:
```powershell
python -c "import json,base64; d=json.load(open('d:/AI/<destination>/upscale_response.json', encoding='utf-16')); open('d:/AI/<destination>/image_2k.png','wb').write(base64.b64decode(d['encodedImage']))"
```

---

## Step 5 — What to Do After Generation

**If the user did NOT specify a download preference in their prompt:**
Take a snapshot showing the image grid, report back to the user how many images were generated, and ask:
- *"All 6 images are ready. Would you like me to download them all in 1K, or would you prefer to pick specific ones? I can also download upscaled 2K versions."*

**If the user DID specify a download in their prompt (e.g., "generate 6 images and download them"):**
Download all images automatically using the 1K network intercept method above and move them to the appropriate workspace directory without asking. Report the saved file paths when done.

---

## Quick Reference — Snapshot Landmarks

Use `.\pw-bridge.bat snapshot` at any point to get your bearings. Here is what to look for:

| What you see in the snapshot | What it means |
|---|---|
| `button "add_2 New project"` | You're on the Flow homepage |
| `button "close Close"` + `button "Agent"` | Agent mode dialog is open — dismiss it |
| `textbox` with placeholder `"What do you want to create?"` | Ready to type a prompt |
| `button "add_2 Create"` is enabled | Prompt is filled, ready to generate |
| `button "arrow_forward Create" [disabled]` | Prompt box is empty |
| Image cards with `/edit/<image_id>` links | Generation is complete |
| Percentage numbers like `57%` in cards | Generation is still in progress — wait |
| `button "download Download"` | You are in the single-image editor view |

---

## Quick Reference — Common CLI Commands

```powershell
.\pw-bridge.bat snapshot                      # See everything on screen
.\pw-bridge.bat goto <url>                   # Navigate to a URL
.\pw-bridge.bat click "<text>"               # Click a button or link by text
.\pw-bridge.bat fill "textbox" "<text>"      # Fill the prompt input
.\pw-bridge.bat hover "<text>"               # Hover to reveal hidden menus
.\pw-bridge.bat requests                     # List all network requests
.\pw-bridge.bat response-body <index>        # Save a network response to disk
.\pw-bridge.bat find "<text>"                # Search snapshot for specific text
```
