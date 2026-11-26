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
- **Authenticated loopback-only browser MCP**: `desk420-browser` binds strictly to `127.0.0.1` on an ephemeral port and requires a cryptographically random per-launch Bearer token verified with constant-time comparison (`crypto::bytes_equal`). If cryptographic randomness fails, the server refuses to start rather than falling back to a guessable token.
- **Scheme & file-URL confinement**: Automated browser navigation allows standard `http://` and `https://` URLs inside the isolated non-persistent browser, blocks dangerous schemes (`javascript:`, `data:`, etc.), and confines `file://` URLs strictly to the active project directory (rejecting path traversal).
- **External ACI consent gate**: External agents connecting to Desk420's local Agent-Controlled Interface MCP server can be restricted or gated behind an explicit user consent prompt in Settings (**Grok → Agent Access**) or via `--require-consent`.
