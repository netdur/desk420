# Changelog

All notable changes to Desk420 are documented in this file.

## [0.1.1] - 2026-11-26

### Added
- **Single & bulk conversation/project deletion**:
  - Hover delete icons on conversations and project folders in the sidebar (matching `style::circle_icon` Material Symbols).
  - Multi-select mode (`Select` in the Projects header) with checkboxes on folders and conversations, `All`/`None`, and batch deletion—always removing only from Grok/Desk420 and never touching files on disk.
  - Deleting the last conversation in a saved project offers **Delete & remove project**, **Delete conversation only**, or **Cancel** in one confirmation sheet.
- **GFM Markdown table rendering** in the chat transcript: parses pipe tables with column alignment (`:---`, `:---:`, `---:`), inline formatting, and empty cells, and renders them as bordered cards with header shading, row dividers, and accurate wrapped height measurement.
- **Direct `http://`/`https://` navigation** in the isolated built-in browser without per-origin confirmation prompts (while still blocking dangerous schemes and confining `file://` URLs to the active project folder).

### Fixed
- **100% idle CPU layout loop**: keyed `HomeView` project tile wrappers so multi-column `collection` layout no longer triggers a `touch_all` feedback loop, and filtered `EngineChange` events in `HomeView`, `Sidebar`, `MainScreen`, and `ChatScreen`.
- **Hover state after sheet dismissal**: cleared stale sidebar hover indices and refocused the main window after closing confirmation sheets so hover controls work immediately without requiring a click.
- **Multi-line user prompt clipping**: measured wrapped user prompt bubble width and height accurately so multi-line prompts never clip while short prompts stay snug.

## [0.1.0] - 2026-11-25

Initial public release of Desk420, a native macOS desktop client for Grok written in C+ on `facet`.

### Added
- Native macOS AppKit UI (`facet`) with System, Light, and Dark appearances.
- Full Grok CLI ACP stdio client, child-process supervisor, and single background worker engine.
- Multi-project sidebar with Needs You approval cards, pinned runs, grouped project folders, archive, and search (`⌘K`).
- Home view with composer, inline approval cards, 2-column project grid (`facet/collection`), and Engine/Usage panel.
- Virtualized conversation transcript with streaming markdown rendering, code copy, per-message rewind (`Chat & files`, `Chat only`, `Files only`), collapsible ACP plan bar, and async `@` mention / `/` slash command popups & file/image drag-and-drop attachments.
- Five-tab Conversation inspector: **Run** timeline, lazy background-loaded **Files** tree, isolated multi-tab **Browser** pane with `desk420-browser` loopback HTTP MCP server, **Terminal** output, and **Changes** git diff/stage/discard/commit view.
- Desktop shell integrations: global Quick Ask HUD (`⌥Space`), menu-bar status item, Dock badge, native macOS notifications, `desk420://` deep links, native `facet/tabs` Settings window, About window, and macOS `.app` / `.dmg` packaging script.
- Agent-Controlled Interface (ACI) MCP surface with configurable consent policies.
