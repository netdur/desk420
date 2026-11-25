# Contributing to Desk420

Thanks for your interest in contributing to Desk420! Desk420 is designed to be both a daily-driver native Grok client and a clean reference **C+ / `facet`** desktop application.

## Setup

1. Install or build the **C+** toolchain (`cpc`) and make sure `cpc` is on `PATH` (or symlinked as `./cpc` alongside `vendor/`).
2. Before writing or modifying any C+ code, run:

```bash
cpc skill
```

This prints the exact, compiler-matched C+ language reference together with `facet`'s retained-UI guide.

## Development Workflow

```bash
cpc fmt      # format all C+ sources canonically
cpc check    # type-check with zero warnings
cpc build    # compile and link Desk420
cpc test     # run all unit and ACP fixture tests (no network or credits needed)
```

For compiler diagnostics, run `cpc explain <CODE>` (for example, `cpc explain E0613`).

## Code Conventions

- **No `extern fn` in `src/`** — Use `stdlib` (`time::sleep`, `process`, `date`, `url`, `string_set`, `math`, etc.) and `facet` modules rather than raw C declarations.
- **No raw UI/store pointers** — Components communicate via `events::on` / `events::emit`, typed store free-function facades, and `facet` handles (`mount::find`, `component::item_index_of`, etc.).
- **Keep the main thread non-blocking** — Run filesystem, process, and network work on background workers (`facet/services::Job` via `services::run_job`, or the engine worker thread).
- **Retained, non-reactive `facet` UI** — Build the tree once in `Component::build`, then push targeted updates in signal watchers and handlers. Put shared palette tokens and reusable node builders in [src/ui/style.cplus](src/ui/style.cplus).
- **Typed enums over magic ints/strings** — Payload-free enums support `==` / `!=` directly without hand-written `is_*` predicates.
- **Tests run offline** — ACP and store tests replay local fixtures under `fixtures/acp/` via `fake_agent.py` so `cpc test` never requires live API calls or credentials.

## Pull Requests

1. Create a focused branch off `main`.
2. Ensure `cpc fmt`, `cpc check`, `cpc build`, and `cpc test` all pass with zero warnings.
3. For UI changes, verify the running app (including via its local MCP surface `describe_ui` / `click` / `journal` described in [AGENTS.md](AGENTS.md)).
4. Fill out the pull request template with a clear summary and verification steps.
