# ROADMAP — shodan-presence

What exists as of 2026-08-26 and where it could go. Ideas ranked by
feel-per-effort. Nothing here is committed work; promote items deliberately.

## Current state

- "Watching ME?" card over local RPC, 15s rotation (RPC floor)
- 28 GENERIC + time pools (night/morning/Monday/Friday-night/weekend)
- ~75 bespoke game narrations; unknown-game fallback + uncatalogued.txt backlog
- Glitch, telemetry (ticking specimen counter), Y2K38 countdown modes
- Epoch timer (elapsed since 1 Jan 1970); SHED YOUR SKIN → orison.zip
- Deploy: repo is source of truth, `./deploy.sh`, PR workflow

## High value / low effort

1. ~~**Repetition guard + sequences.**~~ **SHIPPED 2026-08-26 (#3).** No card
   repeats within 6 rotations; 4 multi-rotation story arcs.
2. ~~**Session-aware narration.**~~ **SHIPPED 2026-08-26 (#3).** "Hour N of
   [game]" after 2h; small-hours crossover line.
3. ~~**Special dates.**~~ **SHIPPED 2026-08-26 (#3).** SS2 birthday, join
   anniversary, Halloween, New Year, Y2K38 day.

## Medium

4. **Spotify track narration.** REJECTED — user doesn't use Spotify.
5. **Second button.** ~~SHIPPED~~ 2026-08-26 (#3): DO NOT CLICK → the
   Year 2038 problem article (explains the countdown to whoever defies it).
   Rotating destinations still open.
6. **Mood-linked art.** DEFERRED — needs corrupted/ORISON art hosted
   somewhere (orison.zip can serve it). Swap large_image per mode once
   assets exist.

## Larger projects

7. ~~**orison.zip tie-in.**~~ **SHIPPED 2026-09-02** (orison#58 + #16 here).
   All four buttons carry `?via=presence.<clause>`; orison's boot answers
   with transient "ingress / external presence relay" residue in its own
   administrative register (never "you" — ORISON is not SHODAN), then
   scrubs the URL. Stateless on the site side.
8. **Backlog cataloguing** (in place, manual): "catalogue the backlog" in any
   Claude session writes bespoke lines for games actually played.

## Known limits / watch items

- 15s is the hard RPC update floor; no faster.
- `wmic` is deprecated; if a Windows update removes it, switch scan to
  `powershell Get-Process | Select Path` (slower, same data).
- Buttons are invisible on your own profile — verify via another account.
- External art URLs depend on Wikipedia/Steam CDN availability.
