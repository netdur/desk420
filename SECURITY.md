# Security Policy

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Instead, report vulnerabilities privately via [GitHub Security Advisories](https://github.com/netdur/desk420/security/advisories/new) on `netdur/desk420`. Please include:

- A clear description of the issue and its impact
- Reproduction steps or a minimal proof of concept
- Any affected macOS / `grok` CLI / Desk420 version details

## Desk420 Security Model

Desk420 enforces several local security boundaries by design:

- **No credential file access**: Desk420 never opens `~/.grok/auth.json` or logs OAuth/bearer tokens. Authentication and billing queries go strictly through the `grok` CLI over ACP stdio.
- **Isolated built-in browser**: The embedded `WKWebView` uses a non-persistent `WKWebsiteDataStore` so it never shares Safari cookies, logins, or browsing history.
- **Per-session authenticated loopback browser MCP**: `desk420-browser` binds strictly to `127.0.0.1` on a PID-derived loopback port (`42100 + pid % 8000`, probing sequentially if busy) and mints a separate cryptographically random 192-bit Bearer token per conversation, verified with constant-time comparison (`crypto::bytes_equal`). Each token is bound to its originating conversation's project directory so background chats never inherit the foreground conversation's permissions. If cryptographic randomness fails, the server refuses to start rather than falling back to a guessable token.
- **Canonical scheme & `file://` confinement**: Browser MCP calls, post-navigation tool reads/evaluations, and `desk420://browser` deep links allow standard `http://` and `https://` URLs inside the isolated non-persistent browser, block dangerous schemes (`javascript:`, `data:`, etc.), and confine `file://` URLs strictly to the conversation's canonical project directory (resolving symlinks and checking exact directory boundaries).
- **Per-conversation approval isolation & read-only Custom allowlist**: Tool approval modes (`Ask`, `Auto-approve`, `Custom`) are tracked per conversation rather than globally. `Custom` mode uses an explicit allowlist of read-only tools (`Read`, `Search`) and shell-metacharacter-free read-only commands; file edits and all other commands require user confirmation.
- **External ACI consent gate (default: Ask)**: External agents connecting to Desk420's local Agent-Controlled Interface MCP server are gated behind an explicit user consent prompt by default (**Settings → Grok → Agent Access**), and can be disabled completely (`Off`) or opened only when explicitly chosen.
