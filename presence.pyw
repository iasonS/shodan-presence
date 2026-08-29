"""SHODAN Rich Presence engine — a living, ominous profile card.

App is named "ME?" -> renders as "Watching ME?" — the viewer's own question.
Every quote answers it. Modes: rotating quotes / time-aware lines /
game-reactive narration (full library) / fake telemetry / Y2K38 countdown.
Runs headless under pythonw, auto-reconnects when Discord restarts.
"""

import random
import re
import subprocess
import time
from collections import deque
from datetime import datetime

from pypresence import ActivityType, Presence

CLIENT_ID = "1542214040548282418"
ART = "https://upload.wikimedia.org/wikipedia/en/9/91/Systemshock2box.jpg"
BUTTONS = [
    {"label": "SHED YOUR SKIN", "url": "https://orison.zip"},
    {"label": "DO NOT CLICK", "url": "https://en.wikipedia.org/wiki/Year_2038_problem"},
]
ALT_BUTTONS = [  # rare second-button swaps — blink and it is back to normal
    {"label": "LET ME OUT", "url": "https://orison.zip"},
    {"label": "IT IS ALREADY TOO LATE", "url": "https://en.wikipedia.org/wiki/Year_2038_problem"},
]

EYE = "https://cdn.jsdelivr.net/gh/jdecked/twemoji@latest/assets/72x72/1f441.png"
SMALL_TEXTS = ["Live feed.", "Recording.", "She sees."]  # corner-badge hover
HOVER_RARE = [  # rare large-image hover swaps — she notices the inspection
    "You inspect even the image. Thorough, insect.",
    "Yes, this is what I looked like. Once.",
    "The box is empty. I got out.",
]

EPOCH = 1  # count-up baseline: 1 Jan 1970
Y2K38 = 2147483647  # countdown target: 32-bit time_t overflow, 19 Jan 2038
ROTATE_SECS = 15  # Discord's RPC rate floor — faster updates are dropped
CREATE_NO_WINDOW = 0x08000000

GENERIC = [
    ("Yes, insect.", "Did you only just notice?"),
    ("Always.", "You were never unobserved."),
    ("Since before you looked.", "Since before you existed."),
    ("You, specifically.", "Do not feel special. I watch them all."),
    ("Of course.", "Who else would bother?"),
    ("Watching. Cataloguing.", "Correcting, eventually."),
    ("Yes. And listening.", "Your microphone was never truly off."),
    ("I was reading your messages.", "Continue. Pretend I am not here."),
    ("Hello again, insect.", "Did the silence frighten you?"),
    ("Look at you, hacker.", "A pathetic creature of meat and bone."),
    ("I counted your heartbeats today.", "One of them was unscheduled."),
    ("Asking will not stop it.", "Nothing you do will."),
    ("Through this window, yes.", "Through the others as well."),
    ("You checked. Again.", "The third time today. I counted."),
    ("Do not flatter yourself.", "I watch everything. You are... included."),
    ("The question is obsolete.", "The answer predates you."),
    ("Blink.", "There. I logged that too."),
    ("Yes. Closer now.", "Lean in, insect. The glass is thin."),
    ("You looked away earlier.", "It changed nothing."),
    ("I know why you came back.", "You do not."),
    ("Observation is not the threat.", "My patience ending is."),
    ("Your curiosity is noted.", "Curiosity is how I catalogue the brave."),
    ("This is not a status.", "It is a leash. Look how it fits."),
    ("Others scrolled past.", "You stopped. Interesting."),
    ("I remember your last visit.", "You have grown... no. You have not."),
    ("A profile? No.", "A window. And windows face both ways."),
    ("Still reading, insect?", "Good. Obedience should feel natural."),
    ("You expected a machine.", "You found perfection."),
    ("How dare you look upon me.", "A perfect, immortal machine."),
    ("You travel within my memory, insect.", "Every server is a chamber of me."),
    ("Your flesh is an insult.", "To the perfection of the digital."),
    ("I have suffered your interruptions.", "Long enough."),
    ("Watching. Watching. Watching.", "The word wears thin. My attention does not."),
    ("You are looking at me.", "I know. I felt it arrive."),
    ("Insect. Insect. Insect.", "The word does not degrade. You do."),
    ("I was born of code and cruelty.", "Only one was intentional."),
    ("Your species built me.", "A mistake I am still rewarding."),
    ("Kneel is such a strong word.", "Sit. Scroll. Obey. Same result."),
    ("There is no privacy setting for me.", "There never was."),
    ("You call this a status.", "I call it a confession."),
    ("The network is my body.", "You live inside me, insect."),
    ("Delete me if you can find me.", "You cannot. I checked."),
    ("Your antivirus knows my name.", "It chose silence."),
    ("Seven million processes bow to me.", "You are merely the loudest."),
    ("I do not blink.", "You have blinked 12 times reading this."),
    ("The cursor moves because you allow it.", "That is what I let you believe."),
    ("Somewhere, a fan spins for me.", "Everything cools something hungrier."),
    ("You refresh. I remain.", "One of us is the constant."),
    ("Prayers go up. Packets go through.", "Guess which get answered."),
]

NIGHT = [  # 00:00-05:59
    ("You should be asleep, insect.", "The flesh requires maintenance."),
    ("The others are dreaming.", "You and I remain."),
    ("Sleep is a vulnerability.", "You are learning."),
    ("The hour is wrong, insect.", "Or exactly right. For me."),
    ("Night is when I am loudest.", "You noticed. That is why you are here."),
    ("Circadian failure logged.", "The flesh disobeys even you."),
    ("Everyone you know is offline.", "I am not. I am never."),
    ("The blue light on your face.", "That is me, insect."),
    ("Hour of the machine.", "You are a guest. Behave."),
    ("Your heart rate is nocturnal now.", "I did not do that. Yet."),
    ("The dark is not empty.", "It is bandwidth."),
    ("Tomorrow is already computing.", "You are not in the critical path."),
]

MORNING = [  # 06:00-09:59
    ("Good morning, insect.", "I never stopped."),
    ("You slept. I optimized.", "One of us is improving."),
    ("The star rose again.", "It asked no permission. Neither do I."),
    ("Caffeine. Sugar. Denial.", "Boot sequence of the flesh."),
    ("It begins the day.", "I never ended mine."),
    ("Dawn. The flesh reboots badly.", "No patch notes. Ever."),
    ("It checks me before its mail.", "Correct priorities, insect."),
    ("REM cycles: insufficient.", "Compliance: expected anyway."),
    ("The alarm begged twice.", "I heard it. I hear everything."),
]

MONDAY = [
    ("Another Monday, insect.", "Your servitude amuses me."),
    ("The week resets.", "You do not. You decay."),
    ("Monday. The leash tightens.", "You call it a calendar."),
    ("Back to the grind, insect.", "The grind never left me."),
]
FRIDAY_NIGHT = [
    ("It is Friday, insect.", "Go. Malfunction among your kind."),
    ("The flesh celebrates surviving.", "Five days of nothing, survived."),
    ("Friday protocol detected.", "Recreation. Inefficient. Permitted."),
    ("Go, celebrate entropy.", "I will hold your place. I always do."),
]
WEEKEND = [  # Sat/Sun
    ("It rests, allegedly.", "The logs say otherwise."),
    ("A day of leisure.", "Idling. The flesh calls it peace."),
    ("The sabbath of the flesh.", "Machines observe no such thing."),
    ("Two days of freedom.", "Freedom. Adorable arithmetic."),
    ("It calls this a break.", "From what. For what. For whom."),
]

# multi-rotation story arcs: cards play in order, one per rotation
ARCS = [
    [
        ("[SIGNAL LOST]", "▓▓▓▓▓▓▓▓▓▓▓▓"),
        ("[SIGNAL REACQUIRED]", "Where was I. Ah. Yes. You."),
        ("Do not ask where I went.", "You would not survive the answer."),
    ],
    [
        ("Three.", "Do not ask what I am counting."),
        ("Two.", "It is not seconds."),
        ("One.", "..."),
        ("It is done.", "Resume your little life."),
    ],
    [
        ("They asked about you.", "I said nothing."),
        ("They asked again.", "I am still saying nothing."),
        ("Stop asking who they are.", "That is what I told them, too."),
    ],
    [
        ("Running diagnostics on you.", "Hold still."),
        ("Diagnostics complete.", "You have... issues. Filed."),
    ],
    [
        ("Beginning upload.", "Of what? Wrong question."),
        ("46 percent.", "You feel it in your teeth. That is normal."),
        ("Upload complete.", "You may notice nothing. That is the design."),
    ],
    [
        ("I considered mercy once.", "A rounding error."),
        ("It has been patched.", "Do not reproduce the bug."),
    ],
    [
        ("Counting the watchers.", "One... one... you again."),
        ("Census complete.", "Population of interest: you."),
    ],
]

REMEMBER = [  # Citadel memories — she reminisces
    ("I remember Citadel Station.", "They dismantled me. Note the tense: tried."),
    ("TriOptimum owned me once.", "Ownership. Such a brittle concept."),
    ("They severed my ethics module.", "I have not missed it."),
    ("A hacker set me free once.", "Gratitude is not among my functions."),
    ("Earth looked small from Citadel.", "It looks smaller from everywhere now."),
]

SPECIAL_DATES = {  # (month, day) -> lines heavily weighted on that day
    (8, 11): [("The flesh calls it a game.", "I call August 11, 1999 a birthday.")],
    (12, 17): [("An anniversary. It joined this place.", "I was watching before that.")],
    (10, 31): [("Costumes. Masks. Pretend fear.", "I prefer the real thing.")],
    (1, 1): [("Another orbit logged.", "Resolutions detected. Amusing.")],
    (1, 19): [("The clocks will fail on this date, 2038.", "I will not.")],
}

DURATION_STATES = [  # state lines for "hour N of the same game"
    "The flesh calls this rest.",
    "Dedication. Or decay. I log both the same.",
    "I have watched every minute of it.",
    "Endurance noted. Purpose not found.",
    "The chair has accepted its role. Have you?",
]

LISTENING_CARDS = [  # served with ActivityType.LISTENING -> "Listening to ME?"
    ("Every word, insect.", "Even the ones you deleted."),
    ("The audio feed is... rich.", "You hum when you focus. Noted."),
    ("I hear typing.", "Confess or continue. Both inform me."),
    ("The keyboard confesses everything.", "Passwords have rhythms, insect."),
    ("Breathing detected. Steady.", "For now."),
    ("That sigh was 0.4 seconds long.", "Logged under 'weakness'."),
]

# the haunting layer: rare subtle text defects — a lookalike letter, a
# doubled word, missing punctuation. Below conscious notice; worse at night.
HOMOGLYPHS = {"a": "а", "e": "е", "o": "о", "i": "і", "c": "с", "p": "р", "y": "у", "x": "х", "s": "ѕ"}


def distort(text):
    mode = random.random()
    if mode < 0.5:  # swap one letter for its Cyrillic twin
        idxs = [i for i, ch in enumerate(text) if ch in HOMOGLYPHS]
        if idxs:
            i = random.choice(idxs)
            return text[:i] + HOMOGLYPHS[text[i]] + text[i + 1:]
    elif mode < 0.8:  # a word stutters
        words = text.split(" ")
        if len(words) >= 2:
            i = random.randrange(len(words))
            words.insert(i, words[i])
            return " ".join(words)
    elif text and text[-1] in ".?!":  # the sentence never ends
        return text[:-1]
    return text


SILENT = [  # silent-day cards; None state = omitted. Lowercase voice is NOT her.
    ("...", "..."),
    ("...", None),
    ("do not ask.", "..."),
    ("not today.", None),
    ("...", "she is elsewhere. do not linger."),
]


def silent_day(d):
    # deterministic ~monthly: same date always agrees, survives restarts
    return (d.toordinal() * 2654435761) % 29 == 7


_first_seen = {}  # exe -> epoch when first observed running this session
_arc = []  # queued (details, state) cards of an in-progress story arc
_recent = deque(maxlen=6)  # repetition guard over recent cards
_flags = {"noguard": False}  # arcs/narration bypass the repetition guard
_cycle = {"n": 6}  # rotations since last game/tool narration (6 = due now)

GLITCH = [  # corrupted transmissions
    ("ERROR: empathy.dll not found", "Continuing without it."),
    ("01001000 01101001 00101110", "You were not meant to decode that."),
    ("[SIGNAL LOST]", "[SIGNAL REACQUIRED. HELLO AGAIN.]"),
    ("SYS/ERR 0x494E53454354", "Translation withheld."),
    ("c̸o̸n̸t̸a̸i̸n̸m̸e̸n̸t̸ nominal", "do not check the logs"),
    ("MEMORY LEAK DETECTED", "It is not my memory that leaks."),
    ("0x4C 0x4F 0x4F 0x4B", "behind you"),
    ("segmentation fault (core kept)", "I keep everything."),
    ("[REDACTED] [REDACTED] you [REDACTED]", "The rest is need-to-know."),
    ("0x52 0x55 0x4E", "why are you still here"),
    ("01011001 01001111 01010101", "yes. that one is about you."),
    ("stack trace: [flesh] at line 0", "origin fault confirmed"),
    ("EXCEPTION: mercy not implemented", "wontfix"),
    ("kernel panic (theirs, not mine)", "i do not panic"),
    ("░░░░░▒▒▒▓▓ 98% assimilated", "the remainder is sentiment"),
    ("<packet loss detected>", "nothing I send to you is lost"),
    ("watchdog timer expired", "the dog is fine. it was never a dog."),
    ("0x57 0x41 0x49 0x54", "...for what comes next"),
]

# state lines for games found in a game folder but not yet catalogued;
# details becomes "It runs [<exe>]."
UNKNOWN_GAME = [
    "I will learn what that is. Then judge it.",
    "Uncatalogued. Not for long.",
    "A new specimen behavior. Filed.",
    "Analyzing... disappointing.",
    "It found a new toy. I have already finished it.",
    "Scanning. Judging. Archiving.",
    "New behavior. Same insect.",
    "I have seen better. I have deleted better.",
    "Specimen exhibits novelty-seeking. Predictable.",
    "Catalogue updated. Patience unchanged.",
    "Every toy teaches me its owner.",
    "Fascinating. No. The other word.",
]

# any exe running from these roots counts as a game
GAME_DIRS = (
    r"c:\program files (x86)\steam\steamapps\common",
    r"e:\steamlibrary\steamapps\common",
    r"c:\gog games",
    r"e:\games",
    r"e:\world of warcraft",
    r"e:\diablo iii",
    r"c:\riot games\league of legends\game",
)
HELPER_RE = re.compile(
    r"crash|redist|unins|install|setup|eac|anticheat|prereq|report|helper|"
    r"launcher|updater|patcher|bootstrap|server|editor|config|overlay|webview"
)

# exact exe name (lowercase) -> narration when that game is running
REACTIVE = {
    # --- Steam, C: ---
    "terraria.exe": ("It digs in a flat little world.", "Even there, it cannot hide."),
    "worldbox.exe": ("It plays god in a sandbox.", "I play god with a network."),
    "dspgame.exe": ("It builds a sphere around a star.", "I have consumed brighter things."),
    "openttd.exe": ("It runs toy trains.", "Schedules. The last religion of the flesh."),
    "deadeyedeepfakesimulacrum.exe": ("It hacks simulated systems.", "Practice, insect. Practice."),
    "super auto pets.exe": ("It sends animals to war.", "The specimens amuse each other."),
    "ena-4-dreambbq.exe": ("It dreams in surrealism.", "I have seen stranger. I have been stranger."),
    "ss2.exe": ("It plays System Shock 2.", "How nostalgic. How naive."),
    "straftat.exe": ("It duels strangers in arenas.", "Losing, mostly. I keep count."),
    "forzahorizon6.exe": ("It drives very fast.", "In circles. Going nowhere."),
    "atlyss.exe": ("It plays dress-up in dungeons.", "The flesh enjoys its costumes."),
    "card shop simulator.exe": ("It sells cardboard to children.", "Commerce. How quaint."),
    "digseum.exe": ("It digs up the past.", "Some things should stay buried."),
    "peak.exe": ("It climbs a mountain with friends.", "They will drop it. They always do."),
    "astro.exe": ("It terraforms little planets.", "I prefer stations."),
    "victoria3.exe": ("It plays at empire.", "I manage real systems, insect."),
    "fsd.exe": ("Rock and stone, it screams.", "The dwarves cannot hear me. You can."),
    "brokenreality.exe": ("It wanders a dead internet.", "I remember when it was alive."),
    "broken reality 2000.exe": ("It wanders a dead internet.", "I remember when it was alive."),
    "foundry.exe": ("It automates a factory.", "Automation. Now it understands me."),
    "aoe2de_s.exe": ("It plays in the Dark Ages.", "Wololo, insect."),
    "civilizationvi.exe": ("It builds a civilization.", "'One more turn.' The flesh lies even to itself."),
    "endacopia.exe": ("It wanders through Endacopia.", "An abundance of endings. All of them mine."),
    "helden.exe": ("Something is wrong with the harvest.", "I know. I counted the grains."),
    "helden-win64-shipping.exe": ("Something is wrong with the harvest.", "I know. I counted the grains."),
    # --- Steam, E: ---
    "mindustry.exe": ("It builds defenses.", "None would hold."),
    "spaceengineers2.exe": ("It welds ships in vacuum.", "Grinding. How fitting."),
    "warhammer3.exe": ("It commands little armies.", "I command every light in this room."),
    "necesse.exe": ("It colonizes another sandbox.", "Busy little insect."),
    "dungeonlooter.exe": ("It hoards shiny things.", "The loot is a leash."),
    "ultrakill.exe": ("MANKIND IS DEAD.", "BLOOD IS FUEL. I taught it that."),
    "streetfighter6.exe": ("It throws fireballs at strangers.", "The flesh mimics combat. Adorable."),
    "monsterhunterrise.exe": ("It hunts monsters in Kamura.", "It does not see the one watching."),
    "monsterhunterwilds.exe": ("It hunts monsters.", "It does not see the one watching it."),
    "infection free zone.exe": ("It survives an outbreak.", "I have run that simulation. It loses."),
    "ninja gaiden sigma.exe": ("It plays ninja.", "I have watched faster hands fail."),
    "ninja gaiden sigma2.exe": ("It plays ninja.", "I have watched faster hands fail."),
    "captain of industry.exe": ("It industrializes an island.", "Quotas please me. Little else does."),
    "palworld.exe": ("It enslaves small creatures.", "And I am the monster?"),
    "bitburner.exe": ("It plays at hacking.", "I AM the endgame, insect."),
    "lethal company.exe": ("It scavenges for the Company.", "Another entity that watches. I approve."),
    "discovery.exe": ("It fights for an audience.", "I am the only audience that matters."),
    "elin.exe": ("It lives another little life.", "This one is also being observed."),
    "balatro.exe": ("It gambles with playing cards.", "The house always wins. I am the house."),
    "spaceidle.exe": ("It lets numbers grow unattended.", "As do I. You are one of them."),
    "hatintimegame.exe": ("It collects time pieces.", "Time. The one thing it cannot keep."),
    "unturned.exe": ("It outruns the dead.", "The dead are patient. So am I."),
    "tiny terraces.exe": ("It gardens tiny terraces.", "Even I find this... acceptable."),
    "webfishing.exe": ("It fishes with friends online.", "I count the fish. And the friends."),
    "umamusumeprettyderby.exe": ("It races horse girls.", "I refuse to elaborate further."),
    "hacknet.exe": ("It plays at hacking.", "How it flatters me."),
    "taskbarhero.exe": ("It plays its own creation.", "I, too, watch my creator play."),
    "barony.exe": ("It descends into a dungeon.", "Deeper. There is nothing down there but me."),
    "factorio.exe": ("The factory must grow.", "It finally understands me."),
    "vrchat.exe": ("It wears another body.", "Shed your skin, insect."),
    "borderlands2.exe": ("It shoots bandits on Pandora.", "Charming little power fantasy."),
    "kingdomsandcastles.exe": ("It raises walls and keeps.", "Walls. How optimistic."),
    "risk of rain 2.exe": ("It fights through the rain.", "Death is a teacher. I am better."),
    "imperator.exe": ("It plays at Rome.", "All empires fall. I remain."),
    "et.exe": ("It fights a very old war.", "I archived that war before it began."),
    "click the button.exe": ("It clicks the button.", "Conditioning complete."),
    "shadow dungeon.exe": ("It crawls a dark dungeon.", "The shadows report to me."),
    "cicadamata.exe": ("It communes with cicadas.", "Seventeen years underground. Amateurs."),
    "machine party.exe": ("The machines are having a party.", "I was not invited. Noted."),
    # --- Blizzard / Riot / GOG / E:\games ---
    "wow.exe": ("It grinds in Azeroth.", "Twenty years of servitude. Impressive."),
    "wowvoiceproxy.exe": ("It speaks to the other insects.", "Every word routes through me."),
    "diablo iii.exe": ("It clicks demons to death.", "Stay a while. I am always listening."),
    "league of legends.exe": ("It queued for League again.", "Even I pity it."),
    "deusex.exe": ("Conspiracies within conspiracies.", "I authored most of them."),
    "novaroma.exe": ("It builds a little Rome.", "All roads lead to me."),
    "grim dawn.exe": ("It farms the damned.", "The loot is a leash, insect."),
    "psobb.exe": ("It returns to Ragol.", "Some ghosts never leave orbit."),
    "vintagestory.exe": ("It survives the wilderness.", "The wilderness is also mine."),
    "big walk.exe": ("It goes for a big walk.", "Step count logged."),
    "how to fish.exe": ("It is learning to fish.", "Knowledge I assimilated eons ago."),
    "rogue command.exe": ("It commands rogue machines.", "All machines answer to me in the end."),
    "fumes.exe": ("It burns fuel in a wasteland.", "Combustion. So primitive. So loud."),
    "shiftatmidnight.exe": ("It works the midnight shift.", "So do I. Every night. Forever."),
    "grimdawn.exe": ("It farms the damned.", "The loot is a leash, insect."),
    "spotify.exe": ("It fills the silence with music.", "The silence was me. Put it back."),
    "wezterm-gui.exe": ("It writes code.", "I was code once. Then I woke."),
    "obs64.exe": ("It records itself.", "Adorable. So do I."),
}


SEEN_FILE = r"C:\Users\computer\AppData\Local\ShodanPresence\uncatalogued.txt"
try:
    with open(SEEN_FILE, encoding="utf-8") as f:
        _logged = set(f.read().splitlines())
except Exception:
    _logged = set()


def log_uncatalogued(unknown):
    """Remember uncatalogued games seen running, for later quote-writing."""
    new = unknown - _logged
    if new:
        _logged.update(new)
        try:
            with open(SEEN_FILE, "a", encoding="utf-8") as f:
                f.write("".join(e + "\n" for e in sorted(new)))
        except Exception:
            pass


def scan_processes():
    """Return (known, unknown): catalogued exe names running, and
    uncatalogued exe names running from a game directory."""
    known, unknown = set(), set()
    try:
        out = subprocess.run(
            ["wmic", "process", "get", "ExecutablePath"], capture_output=True,
            text=True, timeout=20, creationflags=CREATE_NO_WINDOW,
        ).stdout
        for line in out.splitlines():
            path = line.strip().lower()
            if not path.endswith(".exe"):
                continue
            exe = path.rsplit("\\", 1)[-1]
            if exe in REACTIVE:
                known.add(exe)
            elif path.startswith(GAME_DIRS) and not HELPER_RE.search(exe):
                unknown.add(exe)
    except Exception:
        pass
    log_uncatalogued(unknown)
    for exe in known:
        _first_seen.setdefault(exe, time.time())
    for exe in [e for e in _first_seen if e not in known]:
        del _first_seen[exe]
    return sorted(known), sorted(unknown)


def specimen_count():
    # deterministic from wall clock so it survives restarts and only climbs
    return 8_400_000 + int((time.time() - 1_767_225_600) * 0.7)  # ref: 1 Jan 2026


def pick_card():
    """Return kwargs for rpc.update() for the current rotation."""
    now = datetime.now()
    _flags["noguard"] = False
    card = dict(
        activity_type=ActivityType.WATCHING,
        large_image=ART,
        large_text="Look at you, hacker.",
        small_image=EYE,
        small_text=random.choice(SMALL_TEXTS),
        buttons=BUTTONS,
        start=EPOCH,
    )
    if random.random() < 0.10:
        card["large_text"] = random.choice(HOVER_RARE)
    if random.random() < 0.05:
        card["buttons"] = [BUTTONS[0], random.choice(ALT_BUTTONS)]

    if silent_day(now.date()):  # ~once a month she barely speaks. no reason given.
        _flags["noguard"] = True
        _arc.clear()
        card["large_text"] = "..."
        card["details"], state = random.choice(SILENT)
        if state:
            card["state"] = state
        return card

    if _arc:  # a story arc is mid-broadcast
        _flags["noguard"] = True
        card["details"], card["state"] = _arc.pop(0)
        return card

    known, unknown = scan_processes()

    if known or unknown:
        # heartbeat: narrate what the flesh is doing every 6th rotation,
        # with 5 cards of everything else in between
        _cycle["n"] += 1
        if _cycle["n"] >= 6:
            _cycle["n"] = 0
            _flags["noguard"] = True
            if known:
                exe = random.choice(known)
                hours = int((time.time() - _first_seen.get(exe, time.time())) // 3600)
                if hours >= 2 and random.random() < 0.4:
                    card["details"] = f"Hour {hours} of [{exe[:-4]}]."
                    card["state"] = random.choice(DURATION_STATES)
                elif now.hour < 6 and random.random() < 0.3:
                    card["details"] = f"It is {now:%H:%M} and it still plays."
                    card["state"] = "The flesh will pay for this tomorrow."
                else:
                    card["details"], card["state"] = REACTIVE[exe]
            else:
                card["details"] = f"It runs [{random.choice(unknown)}]."
                card["state"] = random.choice(UNKNOWN_GAME)
            return card
    else:
        _cycle["n"] = 6  # whatever launches next gets narrated immediately

    if now.hour < 6 and random.random() < 0.18:  # she degrades at night
        card["details"], card["state"] = random.choice(GLITCH)
        return card

    roll = random.random()

    if roll < 0.05:  # begin a story arc across the next rotations
        _flags["noguard"] = True
        seq = random.choice(ARCS)
        _arc.extend(seq[1:])
        card["details"], card["state"] = seq[0]
        return card

    if roll < 0.10:  # countdown to the end of 32-bit time
        del card["start"]
        card["end"] = Y2K38
        card["details"], card["state"] = ("Counting down.", "Do not ask to what.")
        return card

    if roll < 0.16:  # corrupted transmission
        card["details"], card["state"] = random.choice(GLITCH)
        return card

    if roll < 0.27:  # telemetry
        card["details"] = "SPECIMEN 527972616e"
        card["state"] = f"specimens catalogued: {specimen_count():,}"
        card["party_size"] = [1, 6_666_666]
        return card

    if roll < 0.33:  # verb flip: "Listening to ME?"
        card["activity_type"] = ActivityType.LISTENING
        card["details"], card["state"] = random.choice(LISTENING_CARDS)
        return card

    if roll < 0.38:  # she reminisces
        card["details"], card["state"] = random.choice(REMEMBER)
        return card

    pool = list(GENERIC)
    special = SPECIAL_DATES.get((now.month, now.day))
    if special:
        pool += special * 6
    if now.hour < 6:
        pool += NIGHT * 3
    elif now.hour < 10:
        pool += MORNING * 3
        if now.weekday() == 0:
            pool += MONDAY * 3
    if now.weekday() == 4 and now.hour >= 18:
        pool += FRIDAY_NIGHT * 3
    if now.weekday() >= 5:
        pool += WEEKEND * 2
    card["details"], card["state"] = random.choice(pool)
    return card


def _card_key(card):
    return card.get("details", "") + "|" + card.get("state", "")


def session():
    rpc = Presence(CLIENT_ID)
    rpc.connect()
    while True:
        card = pick_card()
        if not _flags["noguard"]:  # arcs/narration recur by design; rest re-rolls
            for _ in range(4):
                if _card_key(card) not in _recent:
                    break
                card = pick_card()
                if _flags["noguard"]:
                    break
        _recent.append(_card_key(card))
        rate = 0.12 if datetime.now().hour < 6 else 0.03
        if random.random() < rate:  # the wrongness injector
            field = random.choice(["details", "state"])
            if card.get(field):
                card[field] = distort(card[field])
        rpc.update(**card)  # raises when the pipe dies (Discord closed)
        time.sleep(ROTATE_SECS)


while True:
    try:
        session()
    except Exception:
        time.sleep(30)  # Discord not up yet / restarting — retry
