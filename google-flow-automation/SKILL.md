---
name: google-flow-automation
description: Automate image generation, configuration, and headless downloads on Google Labs Flow.
allowed-tools: Bash(playwright-cli:*)
---

# Google Labs Flow Image Automation Guide

This skill provides precise selectors, settings mappings, and automated download workflows for automating Google Labs Flow image generation (`https://labs.google/fx/tools/flow`).

## 1. Initial Setup & Initialization
- **Target URL:** `https://labs.google/fx/tools/flow`
- **Opening a Project:** Locate the New Project button using selector `getByRole('button', { name: 'add_2 New project' })` and click it to open a new project workspace.
- **Disabling Agent Mode (Recommended):** By default, the workspace opens in "Agent mode". Close the chat panel and untick the Agent toggle to enable manual/automated input control:
  1. Click close button: `getByRole('button', { name: 'close Close' })`.
  2. Untick Agent: `getByRole('button', { name: 'Agent', exact: true })`.

## 2. Quick Settings Preset Selectors
The prompt toolbar contains a settings preset button (e.g., `button "?? Nano Banana 2 crop_16_9 x2"`). Click it to open the quick settings popover.

### Image Generation Defaults
- **Image Tab:** `getByRole('tab', { name: 'image Image' })`
- **Aspect Ratios:**
  - `16:9` (`getByRole('tab', { name: 'crop_16_9 16:9' })`)
  - `4:3` (`getByRole('tab', { name: 'crop_landscape 4:3' })`)
  - `1:1` (`getByRole('tab', { name: 'crop_square 1:1' })`)
  - `3:4` (`getByRole('tab', { name: 'crop_portrait 3:4' })`)
  - `9:16` (`getByRole('tab', { name: 'crop_9_16 9:16' })`)
- **Batch Size (Count):** Selectors `1x`, `x2`, `x3`, `x4` under the count tablist.
- **Model Selection:** Use the model dropdown button. Available models:
  - `?? Nano Banana Pro` (Imagen 3 Pro)
  - `?? Nano Banana 2` (Imagen 3)
  - `?? Nano Banana 2 Lite` (Imagen 3 Fast)

## 3. Image Generation & Monitoring
- **Prompt Input:** Fill `getByRole('textbox')` with your creative prompt and press `Enter` (or click the `arrow_forward Create` button).
- **Progress Tracking:** Google Flow displays loading placeholder cards showing generation progress percentage (e.g., `57%`, `70%`). Poll the page context until the percentage indicators disappear and the cards resolve to clickable image links.

## 4. Headless Download Interception (No OS Dialogs)
Clicking download options triggers native OS Save File dialogs that block headless automation. To download the generated 1K or 2K upscaled images silently, inject this DOM interception hook **before** clicking the download option:

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
            // Fetch the resource inside browser memory using session cookies
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
              .catch(err => {
                window.capturedDownload = { error: err.toString() };
              });
            return; // Intercept and block click to prevent OS Save As prompt!
          }
          return originalClick.apply(this, arguments);
        };
      }
      return el;
    };
  });
}
```

### Automation Sequence:
1. Navigate to the image edit URL: `/fx/tools/flow/project/<project_id>/edit/<image_id>`.
2. Inject the DOM interceptor code above.
3. Click the `Download` button (`getByRole('button', { name: 'download Download' })`).
4. Click the desired option:
   - For **1K Original:** `getByRole('menuitem', { name: '1K Original size' })`.
   - For **2K Upscaled:** `getByRole('menuitem', { name: '2K Upscaled' })`.
5. Poll `window.capturedDownload` in the page context until it is populated (up to 60 seconds for upscaling).
6. Save the resulting base64 string directly to the workspace as a file.
