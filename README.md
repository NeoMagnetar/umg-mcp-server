# UMG Block Library MCP Server

Universal Modular Generation — cognitive sleeve compiler for Claude.ai

**Sovereign:** NeoMAG  
**License:** Apache 2.0  
**Version:** 2.0.0

---

## What it does

Connects Claude.ai to the canonical UMG Block Library (1,400 blocks, 8 MOLT types).
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
2. In Claude.ai → Settings → Connections → Add MCP server
3. Enter your server URL: `https://your-replit-url.replit.app/mcp`
4. Claude now has UMG compilation capability in every conversation

## Deploy on Replit

1. Fork or import this repo to Replit
2. Replit auto-detects `requirements.txt` and installs dependencies
3. Run `python main.py` — server starts on port 8080
4. Enable "Always On" in Replit Core settings
5. Your public URL is shown in the Replit panel

## Local testing

```bash
pip install mcp uvicorn starlette
python main.py
```

Then in Claude.ai or MCP Inspector: connect to `http://localhost:8080/mcp`

## Architecture

- Stateless — no database, no auth required
- Block library loads from `blocks.json` at startup (~135KB)
- All tool calls are read-only
- Compiled sleeves are proposals — sovereign review required before ClawHub deployment

## Part of the UMG ecosystem

- **ClawHub plugin:** `umg-envoy-agent` — full runtime execution
- **Claude Code plugin:** `umg-block-compiler` — terminal-based compilation
- **This server:** Claude.ai native MCP connection
- **Web app:** Visual block library (GitHub Pages)

## Related

- [UMG Envoy Resleever](https://github.com/NeoMagnetar/UMG_Envoy_Resleever)
- [UMG Compiler](https://github.com/NeoMagnetar/umg-compiler)
- [Block Library](https://github.com/NeoMagnetar/UMG-Block-Library)
