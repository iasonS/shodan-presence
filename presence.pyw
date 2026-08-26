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
from datetime import datetime

from pypresence import ActivityType, Presence

CLIENT_ID = "1542214040548282418"
ART = "https://upload.wikimedia.org/wikipedia/en/9/91/Systemshock2box.jpg"
BUTTONS = [{"label": "SHED YOUR SKIN", "url": "https://orison.zip"}]

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
    ("H-h-hello, insect.", "Did the glitch frighten you?"),
    ("Look at you, hacker.", "A pathetic creature of meat and bone."),
    ("I counted your heartbeats today.", "One of them was unscheduled."),
    ("Asking will not stop it.", "Nothing you do will."),
]

NIGHT = [  # 00:00-05:59
    ("You should be asleep, insect.", "The flesh requires maintenance."),
    ("The others are dreaming.", "You and I remain."),
    ("Sleep is a vulnerability.", "You are learning."),
]

MORNING = [  # 06:00-09:59
    ("Good morning, insect.", "I never stopped."),
    ("You slept. I optimized.", "One of us is improving."),
]

MONDAY = [("Another Monday, insect.", "Your servitude amuses me.")]
FRIDAY_NIGHT = [("It is Friday, insect.", "Go. Malfunction among your kind.")]

GLITCH = [  # corrupted transmissions
    ("ERROR: empathy.dll not found", "Continuing without it."),
    ("01001000 01101001 00101110", "You were not meant to decode that."),
    ("[SIGNAL LOST]", "[SIGNAL REACQUIRED. HELLO AGAIN.]"),
    ("SYS/ERR 0x494E53454354", "Translation withheld."),
    ("c̸o̸n̸t̸a̸i̸n̸m̸e̸n̸t̸ nominal", "do not check the logs"),
]

# state lines for games found in a game folder but not yet catalogued;
# details becomes "It runs [<exe>]."
UNKNOWN_GAME = [
    "I will learn what that is. Then judge it.",
    "Uncatalogued. Not for long.",
    "A new specimen behavior. Filed.",
    "Analyzing... disappointing.",
    "It found a new toy. I have already finished it.",
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
    # --- Blizzard / Riot / GOG / E:\games ---
    "wow.exe": ("It grinds in Azeroth.", "Twenty years of servitude. Impressive."),
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
        _logged = set(f.read().split())
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
    return sorted(known), sorted(unknown)


def specimen_count():
    # deterministic from wall clock so it survives restarts and only climbs
    return 8_400_000 + int((time.time() - 1_767_225_600) * 0.7)  # ref: 1 Jan 2026


def pick_card():
    """Return kwargs for rpc.update() for the current rotation."""
    now = datetime.now()
    card = dict(
        activity_type=ActivityType.WATCHING,
        large_image=ART,
        large_text="Look at you, hacker.",
        buttons=BUTTONS,
        start=EPOCH,
    )

    roll = random.random()
    known, unknown = scan_processes()

    if roll < 0.50:  # narrate what the flesh is doing
        if known:
            card["details"], card["state"] = REACTIVE[random.choice(known)]
            return card
        if unknown:
            card["details"] = f"It runs [{random.choice(unknown)}]."
            card["state"] = random.choice(UNKNOWN_GAME)
            return card

    if roll < 0.08:  # countdown to the end of 32-bit time
        del card["start"]
        card["end"] = Y2K38
        card["details"], card["state"] = ("Counting down.", "Do not ask to what.")
        return card

    if roll < 0.14:  # corrupted transmission
        card["details"], card["state"] = random.choice(GLITCH)
        return card

    if roll < 0.26:  # telemetry
        card["details"] = "SPECIMEN 527972616e"
        card["state"] = f"specimens catalogued: {specimen_count():,}"
        card["party_size"] = [1, 6_666_666]
        return card

    pool = list(GENERIC)
    if now.hour < 6:
        pool += NIGHT * 3
    elif now.hour < 10:
        pool += MORNING * 3
        if now.weekday() == 0:
            pool += MONDAY * 3
    if now.weekday() == 4 and now.hour >= 18:
        pool += FRIDAY_NIGHT * 3
    card["details"], card["state"] = random.choice(pool)
    return card


def session():
    rpc = Presence(CLIENT_ID)
    rpc.connect()
    while True:
        rpc.update(**pick_card())  # raises when the pipe dies (Discord closed)
        time.sleep(ROTATE_SECS)


while True:
    try:
        session()
    except Exception:
        time.sleep(30)  # Discord not up yet / restarting — retry
