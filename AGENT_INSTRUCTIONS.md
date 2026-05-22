# UMG MCP Server — Agent Setup Instructions
## For: OpenClaw Agent
## Task: Create GitHub repo and push all files

---

## YOUR TASK

Create a new public GitHub repository under the NeoMagnetar account,
push all files from this package into it, and configure the repo metadata.
Do not modify any file contents. Push them exactly as provided.

---

## STEP 1 — CREATE THE GITHUB REPO

Create a new repository with these exact settings:

```
Owner:       NeoMagnetar
Name:        umg-mcp-server
Visibility:  public
Description: UMG Block Library MCP server — connects Claude.ai to the Universal Modular Generation runtime. Exposes sleeve compilation, MOLT Map, IR Graph, active state inspection, and block search across 1,400 canonical blocks. Apache 2.0.
License:     Apache-2.0
Initialize:  false (do NOT auto-initialize with README — we are pushing our own)
```

If the repo already exists, skip creation and proceed to Step 2.

---

## STEP 2 — CLONE THE REPO LOCALLY

```bash
git clone https://github.com/NeoMagnetar/umg-mcp-server.git
cd umg-mcp-server
```

---

## STEP 3 — COPY ALL FILES INTO THE REPO

Copy every file from this package directory into the cloned repo directory.
Preserve the folder structure exactly:

```
umg-mcp-server/          ← repo root
├── main.py
├── blocks.json
├── requirements.txt
├── README.md
├── .replit
├── replit.nix
└── schemas/
    ├── runtime_spec.schema.json
    └── sleeve.schema.json
```

Do not add, remove, or rename any files.
Do not modify any file contents.
The `.replit` file begins with a dot — make sure it is included.

---

## STEP 4 — COMMIT AND PUSH

```bash
git add .
git commit -m "Initial release: UMG MCP Server v0.1.0

- Full UMG runtime engine (RuntimeSpec, MOLT Map, IR Graph)
- 7 MCP tools: compile_sleeve, inspect_active_state, generate_molt_map,
  generate_ir_graph, explain_route, search_blocks, audit_sleeve
- 1,400 canonical blocks across 8 MOLT types
- Replit-ready deployment configuration
- JSON schemas for RuntimeSpec and Sleeve

Sovereign: NeoMAG | License: Apache 2.0"

git push origin main
```

---

## STEP 5 — ADD REPO TOPICS

After pushing, add these topics to the GitHub repository:

```
umg
mcp
mcp-server
claude
ai-governance
cognitive-architecture
molt
sleeve
neoblock
neostack
python
fastmcp
anthropic
```

Using the GitHub API, this is:
```bash
curl -X PUT \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.mercy-preview+json" \
  https://api.github.com/repos/NeoMagnetar/umg-mcp-server/topics \
  -d '{"names":["umg","mcp","mcp-server","claude","ai-governance","cognitive-architecture","molt","sleeve","neoblock","neostack","python","fastmcp","anthropic"]}'
```

---

## STEP 6 — VERIFY

Confirm the following before reporting completion:

- [ ] Repo exists at: https://github.com/NeoMagnetar/umg-mcp-server
- [ ] Repo is public
- [ ] All 9 files are present (including `.replit` and `schemas/` subfolder)
- [ ] Latest commit message matches what was specified in Step 4
- [ ] Repo description is set correctly
- [ ] Topics are added

---

## WHAT HAPPENS NEXT (for MAG, not agent)

After the agent completes the above, MAG handles Replit manually:

1. Go to replit.com → Create Repl → Import from GitHub
2. Paste: https://github.com/NeoMagnetar/umg-mcp-server
3. Replit installs requirements.txt automatically (mcp, uvicorn, starlette)
4. Hit Run — server starts on port 8080
5. Enable Always On in Repl settings
6. Copy the public URL (e.g. https://umg-mcp-server.NeoMagnetar.replit.app)
7. In Claude.ai → Settings → Connectors → + → Add custom connector
8. Paste URL with /mcp suffix: https://umg-mcp-server.NeoMagnetar.replit.app/mcp
9. Name it: UMG Block Compiler
10. Save and enable

---

## FILE MANIFEST (verify all present before starting)

| File | Size | Purpose |
|------|------|---------|
| main.py | ~1,054 lines | MCP server — all 7 tools + runtime engine |
| blocks.json | ~135KB | 1,400 canonical UMG blocks |
| requirements.txt | 3 lines | mcp, uvicorn, starlette |
| README.md | ~60 lines | User-facing documentation |
| .replit | 8 lines | Replit run configuration |
| replit.nix | 6 lines | Replit Python environment |
| schemas/runtime_spec.schema.json | ~80 lines | RuntimeSpec JSON schema |
| schemas/sleeve.schema.json | ~90 lines | Sleeve JSON schema |

Total: 8 files, ~192KB

---

## NOTES FOR AGENT

- Do not run main.py locally
- Do not install the Python dependencies locally
- Do not modify blocks.json — it is a validated canonical library
- The .replit file must be committed — it controls how Replit runs the server
- If git push fails due to branch name, try: git push origin HEAD:main
- If GitHub CLI is available: gh repo create NeoMagnetar/umg-mcp-server --public can be used for Step 1

---

*Sovereign: NeoMAG | License: Apache 2.0 | Version: 0.1.0*
