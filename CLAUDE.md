# CLAUDE.md — shodan-presence

SHODAN-themed Discord Rich Presence engine for Iason's profile. The Discord app
is named `ME?`, rendering as **"Watching ME?"** — every quote answers that question.

## Architecture

One file: `presence.pyw`. Connects to the Discord desktop client's local RPC
pipe via `pypresence` and rotates the profile card every 15s (Discord's RPC
rate floor — faster updates are silently dropped).

Card modes, picked per rotation by weighted roll:
- **Game narration** (50% while a game runs): `REACTIVE` maps exact lowercase
  exe names → (details, state). Detection via `wmic process get ExecutablePath`.
- **Unknown-game fallback**: any exe under `GAME_DIRS` not in `REACTIVE` →
  `It runs [exe].` + a random `UNKNOWN_GAME` line; the exe is also appended to
  `uncatalogued.txt` for later quote-writing ("catalogue the backlog").
- **Quotes**: `GENERIC` pool + time-aware pools (`NIGHT`, `MORNING`, `MONDAY`,
  `FRIDAY_NIGHT`).
- **Glitch** (~6%), **telemetry** (~12%, ticking specimen counter, party
  1 of 6,666,666), **Y2K38 countdown** (~8%, `end=2147483647`).
- Timer gag: `start=1` (Unix epoch) → ~496,000-hour elapsed counter.

## Runtime (Windows)

- Live copy: `C:\Users\computer\AppData\Local\ShodanPresence\presence.pyw`
- Runs headless under `pythonw` (Python 3.11, pypresence 4.6.2 installed there)
- Autostart: `ShodanPresence.lnk` in the user Startup folder
- State: `uncatalogued.txt` next to the live script (runtime-only, not tracked)
- Discord application: "ME?", ID `1542214040548282418` (owned in Dev Portal)
- WSL cannot reach Discord's named pipe — the script must run Windows-side.
- Subprocess calls under `pythonw` need `CREATE_NO_WINDOW` or consoles flash.

## Deploy

Edit `presence.pyw` here, then:

```bash
./deploy.sh   # syntax-check → copy to AppData → kill pythonw → relaunch hidden
```

## Tone rule (binding)

No line may sound like something a coworker could say. SHODAN register only:
contempt for flesh, god-complex, cold surveillance, occasional glitches.
Deliberate exceptions exist (Umamusume, Tiny Terraces) where the god being
charmed against her will is the joke. Test: if a human could plausibly say it
in a stand-up, rewrite it.
