# UMG Block Library MCP Server

> **Status — legacy public compatibility line:** This repository preserves an earlier public MCP server and its historical catalog/tool model. It is not the modern MCP convergence authority and does not prove the ancestry of any remote deployment. Current public H4 architecture starts with [compiler-vNext](https://github.com/NeoMagnetar/umg-compiler-vnext) and the seven-lane [UMG Block Library](https://github.com/NeoMagnetar/UMG-Block-Library).

Universal Modular Generation - cognitive sleeve compiler for Claude.ai

**Sovereign:** NeoMAG  
**License:** Apache 2.0  
**Version:** 2.0.0

---

## What it does

Connects Claude.ai to the bundled legacy UMG catalog used by this server line (approximately 1,400 records across its historical 8-type model).
Enables Claude to compile governed cognitive sleeves mid-conversation,
search blocks semantically, and audit existing sleeves for canonical validity.

## Tools

| Tool | What it does |
|------|-------------|
| `compile_sleeve(intent)` | Compile a governed sleeve from plain language |
| `search_blocks(query, type, limit)` | Search 1,400 canonical blocks |
| `audit_sleeve(sleeve_json)` | Validate a sleeve against the canonical registry |
| `get_block_types()` | Overview of all 8 MOLT types |

## Connect to Claude.ai

1. Deploy this server (see below)
2. In Claude.ai > Settings > Connections > Add MCP server
3. Enter your server URL: `https://your-replit-url.replit.app/mcp`
4. Claude now has UMG compilation capability in every conversation

## Deploy on Replit

1. Fork or import this repo to Replit
2. Replit auto-detects `requirements.txt` and installs dependencies
3. Run `python main.py` -> server starts on port 8080
4. Enable "Always On" in Replit Core settings
5. Your public URL is shown in the Replit panel

## Local testing

```bash
pip install mcp uvicorn starlette
python main.py
```

Then in Claude.ai or MCP Inspector: connect to `http://localhost:8080/mcp`

## Architecture

- Stateless - no database, no auth required
- Block library loads from `blocks.json` at startup (~135KB)
- All tool calls are read-only
- Compiled sleeves are proposals - sovereign review required before ClawHub deployment

## Part of the UMG ecosystem

- **OpenClaw plugin:** `umg-envoy-agent` - working legacy integration; not H4-qualified
- **Claude Code plugin:** `umg-block-compiler` - terminal-based compilation
- **This server:** Claude.ai native MCP connection
- **Web app:** Visual block library (GitHub Pages)

## Naming convention

- RuntimeSpec is the canonical type and schema concept.
- `runtime-spec.json` is the emitted artifact filename.
- Trace is the canonical type and schema concept.
- `trace.json` is the emitted artifact filename.
- NeoStack is the canonical typed structural layer above NeoBlock and below Sleeve.
- Machine-facing resolver and MCP outputs use `active_neostacks` for typed NeoStack records.
- `active_stacks` is treated as a deprecated preview alias only where backward compatibility is required.

## Related

- [UMG Envoy Resleever](https://github.com/NeoMagnetar/UMG_Envoy_Resleever)
- [UMG Compiler](https://github.com/NeoMagnetar/umg-compiler)
- [Block Library](https://github.com/NeoMagnetar/UMG-Block-Library)
