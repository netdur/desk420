# Desk420

A native macOS desktop client for **Grok**, written in **C+** on **facet**.

Desk420 drives the `grok` CLI directly over the **Agent Client Protocol (ACP)** on stdio and presents a native AppKit interface—no Electron, no web wrapper, and no direct reads of `~/.grok/auth.json`.

## Features

- **Native macOS UI on `facet` / AppKit** — Light, Dark, and System appearances, split-pane layout, virtualized transcripts, and zero-lag window resizing.
- **Multi-project workspace** — Group conversations by project folder, pin or archive runs, jump with `⌘1`–`⌘9`, search with `⌘K`, and start runs in any folder (`⌘O`).
- **Interactive approvals & per-message rewind** — Approve or deny tool calls inline (or right from the Home view), switch between `Ask`, `Auto-approve`, and `Custom` modes, and rewind chat and/or files to any earlier prompt.
- **Built-in WebKit browser + MCP bridge (`desk420-browser`)** — Multi-tab non-persistent `WKWebView` exposed to Grok over an authenticated loopback HTTP MCP server with user take-over and per-origin approval prompts for non-localhost URLs.
- **Inspector tabs** — Live **Run** timeline, lazy **Files** tree (`@` prompt references), **Browser**, **Terminal** output, and **Changes** (colorized git diff with Stage / Discard / Commit).
- **Desktop shell** — Floating **Quick Ask** HUD (`⌥Space`), menu-bar status item with recent runs & approval count, Dock badge, native macOS notifications, and `desk420://` deep links.
- **Agent-Controlled Interface (ACI)** — Built-in local MCP surface (`src/app.cplus`) with optional consent gating so external agents can inspect or drive the UI.

## Install with Homebrew (macOS Apple Silicon)

This repository doubles as a Homebrew tap via [Casks/desk420.rb](Casks/desk420.rb):

```bash
brew tap netdur/desk420 https://github.com/netdur/desk420.git
brew install --cask netdur/desk420/desk420
```

To update later:

```bash
brew upgrade --cask desk420
```

> **Note:** Prebuilt releases are currently ad-hoc signed. If macOS Gatekeeper blocks the first launch, clear the quarantine attribute with:
> `xattr -dr com.apple.quarantine /Applications/Desk420.app`

## Prerequisites (Building from Source)

- **macOS 13.0+** (Apple Silicon or Intel)
- **C+ toolchain (`cpc`)** built from [`netdur/cplus`](https://github.com/netdur/cplus) (`main`)
  - Ensure `cpc` is on `PATH` (or symlinked as `./cpc` at the repo root) and `vendor/` resolves to your C+ `vendor/` directory.
- **[Grok CLI](https://x.ai)** (`grok`) installed on your Mac (or installable directly from Desk420's onboarding screen).

## Building & Testing

```bash
# Clone the repository
git clone https://github.com/netdur/desk420.git
cd desk420

# Type-check, build, and run all unit & ACP fixture tests
cpc check
cpc build
cpc test
```

Format all C+ source files:

```bash
cpc fmt
```

### Packaging a macOS `.app` / `.dmg`

```bash
./scripts/package_macos.sh                  # debug target/debug/Desk420.app
./scripts/package_macos.sh --release        # release target/release/Desk420.app
./scripts/package_macos.sh --release --dmg  # release .app + target/release/Desk420.dmg
```

To regenerate the macOS icon (`assets/AppIcon.icns`) using Python stdlib + macOS `sips`/`iconutil`:

```bash
python3 scripts/make_icon.py
```

## Keyboard Shortcuts

| Shortcut | Action |
| --- | --- |
| `⌥Space` | Toggle global Quick Ask floating HUD |
| `⌘N` | New run |
| `⌘O` | Add project folder |
| `⌘K` | Search conversations |
| `⌘,` | Open Settings |
| `⌘1`–`⌘9` | Jump to conversation 1–9 |
| `⌘/` | Open slash commands in composer |
| `⌘.` | Stop active run |
| `⌘⇧Z` | Rewind last turn |
| `⌘\` / `⌘⇧\` | Toggle sidebar / right inspector panel |

## Deep Links (`desk420://`)

Desk420 registers the `desk420://` URL scheme in [macos/Info.plist](macos/Info.plist):

- `desk420://chat/<session-id>` — Open an existing conversation
- `desk420://new?cwd=<path>&prompt=<text>` — Start a new run (with optional working directory and prefilled prompt)
- `desk420://browser?url=<url>` — Open a URL in the built-in Browser tab

## Architecture

```text
src/
├── main.cplus              macOS entry point
├── app.cplus               App lifecycle, menus, status item, Quick Ask hotkey, ACI MCP surface
├── agent_consent.cplus     External ACI agent consent dialog & policy
├── acp/
│   ├── wire.cplus          JSON-RPC 2.0 envelope encoder/decoder
│   ├── types.cplus         Typed ACP protocol messages & defensive decoders
│   └── client.cplus        Stdio child-process ACP client & request correlation
├── engine/
│   ├── locate.cplus        Grok CLI locator & version parser
│   ├── supervisor.cplus    Child process lifecycle & restart supervisor
│   └── runtime.cplus       Single background worker thread & main-thread state store
├── store/
│   ├── conversation.cplus  Session blocks, streaming updates, turn & load state
│   ├── sessions.cplus      Sidebar rows, projects, pins, archives, search hits
│   ├── account.cplus       Identity, plan tier, usage quota, context meter
│   ├── prefs.cplus         ~/.desk420/settings.json loader/saver
│   └── file_tree.cplus     Lazy project directory walker & @-reference formatter
├── markdown/
│   └── parser.cplus        Streaming block & inline markdown parser
├── browser/
│   └── mcp_server.cplus    Loopback HTTP MCP server (desk420-browser) & URL safety policy
└── ui/
    ├── style.cplus         Adaptive semantic palette & shared facet node helpers
    ├── main_screen.cplus   Root window shell, toolbar, onboarding, sidebar/content split
    ├── sidebar.cplus       Needs-you cards, pinned runs, grouped projects, account footer
    ├── home_view.cplus     Home composer, approval cards, 2-column project grid, usage panel
    ├── chat_screen.cplus   Virtualized transcript, composer, Run/Files/Browser/Terminal/Changes tabs
    ├── browser_pane.cplus  Multi-tab WebKit pane & origin approval bar
    ├── composer_popup.cplus Background-scanned @ mention and / slash command picker
    ├── attachments.cplus   Async file/image attachment loader & drag-and-drop strip
    ├── plan_bar.cplus      Collapsible ACP plan checklist bar
    ├── pickers.cplus       Shared Model / Effort / Approvals / Project picker logic
    ├── panels.cplus        Split-pane collapse/expand coordination
    ├── settings_screen.cplus Native facet/tabs Settings window (Grok & UI tabs)
    ├── quick_ask.cplus     Global floating Quick Ask panel
    └── about_screen.cplus  About Desk420 window
```

## Contributing & Security

- Contributions are welcome—see [CONTRIBUTING.md](CONTRIBUTING.md) for C+ / `facet` conventions and development workflow.
- To report a security issue, see [SECURITY.md](SECURITY.md).
- Release history is tracked in [CHANGELOG.md](CHANGELOG.md).

## License

MIT — see [LICENSE](LICENSE).
