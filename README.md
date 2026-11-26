# Desk420

A fast, native macOS desktop app for **Grok Build** (`grok`).

Desk420 gives you a dedicated macOS workspace around the Grok CLI—projects, approvals, diffs, an isolated browser, Quick Ask from anywhere, and native notifications—in a ~5 MB native app with no Electron or web wrapper.

## Install

Requires **macOS 13 (Ventura) or later** on Apple Silicon.

### Homebrew (recommended)

This repository works directly as a Homebrew tap and installs the `grok` CLI (`grok-build`) alongside Desk420:

```bash
brew tap netdur/desk420 https://github.com/netdur/desk420.git
brew trust netdur/desk420   # required on Homebrew 7+
brew install --cask netdur/desk420/desk420
```

To update later:

```bash
brew upgrade --cask desk420
```

### Direct Download

Download the latest `.dmg` from [GitHub Releases](https://github.com/netdur/desk420/releases/latest) and drag **Desk420.app** into Applications.

> **First launch note:** Desk420 is currently ad-hoc signed (not Apple-notarized). If macOS Gatekeeper blocks the first launch, run:
>
> ```bash
> xattr -dr com.apple.quarantine /Applications/Desk420.app
> ```

## What Desk420 Does

- **Multi-project workspace** — Group conversations by project folder, pin active runs, archive old ones, jump with `⌘1`–`⌘9`, and search across all conversations with `⌘K`.
- **Inline approvals & modes** — Approve or deny tool calls right inside the conversation or from the Home screen, and switch between **Ask**, **Auto-approve**, and **Custom** approval modes at any time.
- **Per-message rewind** — Roll back to any earlier prompt in a thread with your choice of **Chat & files**, **Chat only**, or **Files only**.
- **Five-tab workspace inspector** — Keep context beside your chat without leaving the window:
  - **Run** — Live timeline of tool activity and edits
  - **Files** — Browse project files and insert `@` mentions directly into your prompt
  - **Browser** — Built-in isolated browser that Grok can open and preview localhost apps in, with instant user take-over and per-site approval prompts for external URLs
  - **Terminal** — Live command output from the active run
  - **Changes** — Colorized git diff with Stage, Discard, and Commit controls
- **Smart composer** — `@` file mentions, `/` slash commands, drag-and-drop files and images, model and reasoning-effort pickers, collapsible thinking notes, and a live plan checklist.
- **Always one shortcut away** — Summon the floating **Quick Ask** bar with `⌥Space` from any app, check recent runs and pending approvals from the menu bar, and get native macOS notifications and Dock badges when a run finishes or needs approval.
- **Usage & connection at a glance** — See your active Grok CLI version, plan tier, weekly usage, and context window meter directly in the app.
- **Light, Dark, and System themes** — Adapts cleanly to your macOS appearance.

## Keyboard Shortcuts

| Shortcut | Action |
| --- | --- |
| `⌥Space` | Toggle Quick Ask from any app |
| `⌘N` | New run |
| `⌘O` | Add project folder |
| `⌘K` | Search conversations |
| `⌘,` | Open Settings |
| `⌘1`–`⌘9` | Jump to conversation 1–9 |
| `⌘/` | Slash commands |
| `⌘.` | Stop active run |
| `⌘⇧Z` | Rewind last turn |
| `⌘\` / `⌘⇧\` | Toggle sidebar / right inspector |

## Deep Links (`desk420://`)

- `desk420://chat/<session-id>` — Open an existing conversation
- `desk420://new?cwd=<path>&prompt=<text>` — Start a new run with an optional folder and prefilled prompt
- `desk420://browser?url=<url>` — Open a URL in the built-in Browser tab

## Privacy & Security

- **Your Grok login stays in `grok`** — Desk420 talks to the local `grok` CLI over stdio and never reads `~/.grok/auth.json` or stores your tokens.
- **Isolated built-in browser** — Uses a separate non-persistent session so it never touches your Safari cookies, logins, or history.
- **Safe browser boundaries** — Localhost previews work automatically; external sites prompt for your approval first, and local file access is confined to the active project folder.

See [SECURITY.md](SECURITY.md) for full details and vulnerability reporting.

## Contributing & Releases

- Building from source and contribution guidelines: [CONTRIBUTING.md](CONTRIBUTING.md)
- Release history: [CHANGELOG.md](CHANGELOG.md)
- License: MIT — see [LICENSE](LICENSE)
