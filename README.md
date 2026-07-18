# Playwright AI Bridge for Brave

A persistent, lock-free bridge for autonomous AI agents (like Claude Code, Cursor, or Gemini CLI) to securely automate the Brave browser on Windows without tripping over session isolation or profile locks.

## The Problem
When sandboxed AI agents (like Gemini CLI or Antigravity) spawn `playwright-cli`, they often run in a hidden session (Session 0) and the background processes are forcefully reaped when the tool turn ends. Furthermore, if the user already has their Chromium browser (Chrome/Brave) open, Playwright cannot launch a new debug session without closing the user's browser, leading to lock conflicts.

## The Solution
This repository provides:
1. **Persistent Bridge Server (`pw_bridge_server.py`)**: A local Python HTTP server that keeps the `playwright-cli` daemon alive outside the AI's sandbox constraints.
2. **Client Wrappers (`pw-bridge.bat` / `pw-bridge.ps1`)**: Drop-in replacements for `playwright-cli` that forward commands to the bridge server.
3. **Lock-Free Browser Launcher (`launch_brave_rp.bat`)**: A script that launches Brave with remote debugging enabled (`--remote-debugging-port=9222`) but crucially *without* forcing a specific profile. This allows the browser to open the Profile Picker so the user can manually select their logged-in profile, completely sidestepping Chrome/Brave's aggressive background locks.
4. **AI Skill (`playwright-cli-skill`)**: The custom skill instructions for the AI to understand how to use this persistent bridge mode.

## How to Use

1. Start the bridge server in the background:
   ```cmd
   python pw_bridge_server.py
   ```
2. Double-click `launch_brave_rp.bat` to open Brave in debugging mode.
3. **Important:** Select your preferred profile from the Brave Profile Picker screen.
4. Have your AI agent attach to the browser:
   ```cmd
   pw-bridge attach --cdp=http://localhost:9222
   ```
5. The AI can now run commands natively:
   ```cmd
   pw-bridge goto https://example.com
   pw-bridge click e15
   ```
