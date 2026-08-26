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

1. **Repetition guard + sequences.** Rotations are independent random picks —
   the same card can repeat back-to-back. Track last N picks; never repeat.
   Then add multi-card arcs (2-4 rotations): [SIGNAL LOST] → [REACQUIRED] →
   "It saw something while I was gone." Narrative memory is the single
   biggest "she's alive" upgrade.
2. **Session-aware narration.** She already sees the game process; track how
   long it's been running: "Four hours of Balatro. The flesh calls this rest."
   Night+game crossovers: "It hunts monsters at 3 a.m."
3. **Special dates.** SS2 release day (Aug 11), account anniversary (Dec 17),
   Halloween, New Year ("Another orbit logged."), Y2K38 anniversary countdown.

## Medium

4. **Spotify track narration.** Window title carries artist/song; narrate the
   actual track: "It plays [song]. Again." (Get-Process MainWindowTitle —
   no Spotify API needed.)
5. **Second button.** One slot free. Candidates: a "DO NOT CLICK" link, or
   rotating destinations.
6. **Mood-linked art.** Swap large_image per mode — corrupted/glitched art
   during GLITCH cards, ORISON art instead of SS2 box for a self-branded look.
   Needs images hosted (orison.zip can serve them).

## Larger projects

7. **orison.zip tie-in.** The button already sends viewers to the site; the
   site could greet Discord referrals differently ("I told you not to click.")
   — closes the loop between profile and website.
8. **Backlog cataloguing** (in place, manual): "catalogue the backlog" in any
   Claude session writes bespoke lines for games actually played.

## Known limits / watch items

- 15s is the hard RPC update floor; no faster.
- `wmic` is deprecated; if a Windows update removes it, switch scan to
  `powershell Get-Process | Select Path` (slower, same data).
- Buttons are invisible on your own profile — verify via another account.
- External art URLs depend on Wikipedia/Steam CDN availability.
