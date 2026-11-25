# Changelog

All notable changes to Desk420 are documented in this file.

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
