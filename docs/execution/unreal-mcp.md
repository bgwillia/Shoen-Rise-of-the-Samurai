# Unreal-MCP local setup — 2026-09-17

## Goal and result
Install Ivan Murzak's Unreal-MCP for live SHŌEN editor control. Installed and verified Unreal-MCP/CLI 0.17.0 and GameDev-MCP-Server 9.2.7 on macOS Apple Silicon / UE 5.8.2. Codex must restart once to load the new MCP configuration. The editor remains open on SettlementMap_01. The temporary verification server has exited; Codex owns server startup thereafter.

## Architecture and scope
The editor-only project plugin starts its bundled bridge. Codex starts the local server over stdio, with the bridge connecting to http://127.0.0.1:25202. No cloud login is used. Actual listener inspection confirmed loopback IPv4/IPv6 binding. The project entry restricts UnrealMCP to Editor targets. No simulation or gameplay source was changed by this installation.

Global Codex configuration: `~/.codex/config.toml`, server `unreal-mcp`, executable `game/Intermediate/UnrealMCP/server/osx-arm64/gamedev-mcp-server` (absolute path), arguments `port=25202 client-transport=stdio authorization=none`, environment `ASPNETCORE_URLS=http://127.0.0.1:25202`.

Project connection settings persist in ignored `game/.env` and `game/Saved/Config/UnrealMcp/ai-game-developer-config.json`: Custom mode, loopback host above, no authentication, keepConnected=true, stdio transport, startServer=false. Codex starts the server; the editor must also be open for editor tools to work.

## Installation and discoveries
Official package: https://github.com/IvanMurzak/Unreal-MCP (MIT, beta).
CLI was installed locally under ignored `game/Intermediate/UnrealMCP/cli` with npm, pinned to 0.17.0. `install-plugin game --with-server` downloaded and verified the release plugin source and managed server. Plugin lives at `game/Plugins/UnrealMCP`; its multi-platform binary payload is intentionally ignored rather than committed.

The release failed to compile on this Mac. The preserved [compatibility patch](../../artifacts/unreal-mcp/macos-0.17.0.patch) changes four plugin files only:
- Rewords three comment paths containing nested comment tokens rejected by Clang.
- Guards two Windows-only process-job calls with PLATFORM_WINDOWS; Mac process handles are integers.
- Exports IsValidKey from the runtime module for its use by the editor module.

Reinstall/update replaces these local fixes; verify a newer upstream release or reapply the preserved patch and rebuild. Generated output and unrelated pre-existing source/assets were not staged or committed.

## Validation
- Existing dirty editor packages saved successfully (Unreal returned True), then editor closed and reopened on SettlementMap_01.
- `python3 tools/dev.py core-test`: 7/7 targets passed.
- `python3 tools/dev.py build`: final success, 27.97 seconds, after the documented plugin corrections.
- Actual rendered editor log: plugin loaded, Custom mode, loopback IPC listener, bundled bridge started, IPC v2 handshake accepted.
- Exact Codex stdio command tested using MCP initialize, tools/list and tools/call: 61 tools returned; editor state identifies SettlementMap_01, idle, no PIE.
- `screenshot-viewport`: real 1024×551 PNG returned through MCP; inspected terrain, river and crossing. This validates capture, not frame rate or battle scale.
- `codex mcp get unreal-mcp`: enabled and configured for stdio. This task's already-loaded tool catalog has not refreshed, so in-session native Codex tool use after restart remains the final user-visible check.

Evidence in [artifacts/unreal-mcp](../../artifacts/unreal-mcp/): build-initial.log, build-linker.log, build-final.log, core-test.log, editor.log, initialize.json, tools.json, editor-application-get-state.json, screenshot-viewport.json, settlement-mcp.png, stdio-server.log.

## Handoff
Restart Codex once, then continue this task or another SHŌEN task. The server starts automatically and the open editor reconnects. Keep one editor process per checkout. No need to install a cloud service or run a server manually. If Intermediate is cleaned, reinstall the pinned CLI and run `install-plugin game --with-server`, restore the compatibility patch if still needed, and rebuild before relaunching.
