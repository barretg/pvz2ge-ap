"""
PvZ2 Gardendless — Archipelago World
A complete Archipelago world integration for PvZ2 Gardendless.

Installing this apworld adds a "PvZ2 Gardendless Installer" button to the
Archipelago Launcher. Click it to build a ready-to-play modded game exe.
"""

from worlds.AutoWorld import World, WebWorld
from BaseClasses import Region, Location, Item, ItemClassification, Tutorial
from typing import Dict, List, Optional, Any
from Options import PerGameCommonOptions
import dataclasses

# ── Launcher component registration ───────────────────────────────────────────
# Adds the installer button to the Archipelago Launcher GUI.

def _run_builder_gui(*args) -> None:
    """
    Runs inside a multiprocessing.Process (spawned by LauncherComponents.launch).
    Extracts build_pvzge_ap.py from the apworld zip, loads its main() function,
    and calls it — all within this process, no subprocess needed.
    """
    import os
    import sys
    import importlib.util
    import tempfile
    import zipfile

    module_file = __file__

    # Walk up the path to find the .apworld zip that contains this module
    apworld_zip = None
    path = module_file
    while True:
        parent = os.path.dirname(path)
        if parent == path:
            break
        if path.endswith(".apworld") and os.path.isfile(path):
            apworld_zip = path
            break
        path = parent

    if apworld_zip is None:
        # Loose-file install: build_pvzge_ap.py is a sibling of __init__.py
        sibling = os.path.join(os.path.dirname(module_file), "build_pvzge_ap.py")
        if os.path.isfile(sibling):
            apworld_zip = None  # signal to use sibling directly
            extracted = sibling
        else:
            import tkinter.messagebox as mb
            mb.showerror("Error", "Could not locate pvz2gardendless.apworld.")
            return
    
    if apworld_zip is not None:
        # Extract build_pvzge_ap.py from inside the apworld to a temp dir
        tmp_dir = tempfile.mkdtemp(prefix="pvz2ge_ap_")
        try:
            with zipfile.ZipFile(apworld_zip, "r") as zf:
                names = zf.namelist()
                entry = next((n for n in names if n.endswith("build_pvzge_ap.py")), None)
                if entry is None:
                    import tkinter.messagebox as mb
                    mb.showerror("Error", "build_pvzge_ap.py not found inside the apworld.")
                    return
                extracted = os.path.join(tmp_dir, "build_pvzge_ap.py")
                with zf.open(entry) as src_f, open(extracted, "wb") as dst_f:
                    dst_f.write(src_f.read())
        except Exception as e:
            import tkinter.messagebox as mb
            mb.showerror("Error", f"Failed to extract installer: {e}")
            return

    # Import the extracted script as a module and call its main()
    spec = importlib.util.spec_from_file_location("build_pvzge_ap", extracted)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.main()


def _launch_installer(*args) -> None:
    """Called by the Launcher when the user clicks the button."""
    from worlds.LauncherComponents import launch
    launch(_run_builder_gui, name="PvZ2GE AP Installer")


try:
    from worlds.LauncherComponents import components, Component, Type
    components.append(Component(
        "PvZ2 Gardendless Installer",
        func=_launch_installer,
        component_type=Type.CLIENT,
        description="Build and install the PvZ2 Gardendless Archipelago mod."
    ))
except Exception:
    pass  # Launcher not available in this context (e.g. during generation)


GAME_NAME = "PvZ2 Gardendless"
BASE_ID   = 0xD1A2B3C4    # unique base ID for this game


# ── Items ─────────────────────────────────────────────────────────────────────

@dataclasses.dataclass
class PvZ2Item:
    name: str
    classification: ItemClassification
    code: int


# All plant items (received → unlocked in game)
PLANT_ITEMS: List[PvZ2Item] = []
_plants = [
    # Starting plants (progression — required for logic)
    ("Peashooter",         ItemClassification.progression),
    ("Sunflower",          ItemClassification.progression),
    ("Wall-nut",           ItemClassification.progression),
    ("Potato Mine",        ItemClassification.progression),
    # World-specific plants
    ("Cabbage-pult",       ItemClassification.useful),
    ("Bloomerang",         ItemClassification.useful),
    ("Iceberg Lettuce",    ItemClassification.useful),
    ("Grave Buster",       ItemClassification.progression),  # needed for Egypt locks
    ("Twin Sunflower",     ItemClassification.useful),
    ("Bonk Choy",          ItemClassification.useful),
    ("Repeater",           ItemClassification.useful),
    ("Iceweed",            ItemClassification.useful),
    ("Snowdrop",           ItemClassification.useful),
    ("Squash",             ItemClassification.useful),
    ("Dandelion",          ItemClassification.useful),
    ("Pea Vine",           ItemClassification.useful),
    ("Kernel-pult",        ItemClassification.useful),
    ("Snap Dragon",        ItemClassification.useful),
    ("Spikeweed",          ItemClassification.useful),
    ("Coconut Cannon",     ItemClassification.useful),
    ("Cherry Bomb",        ItemClassification.useful),
    ("Spring Bean",        ItemClassification.useful),
    ("Spikerock",          ItemClassification.useful),
    ("Threepeater",        ItemClassification.useful),
    ("Buttercup",          ItemClassification.useful),
    ("Split Pea",          ItemClassification.useful),
    ("Chili Bean",         ItemClassification.useful),
    ("Lightning Reed",     ItemClassification.useful),
    ("Pea Pod",            ItemClassification.useful),
    ("Tall-nut",           ItemClassification.useful),
    ("Jalapeno",           ItemClassification.useful),
    ("Melon-Pult",         ItemClassification.useful),
    ("Winter Melon",       ItemClassification.useful),
    ("Imitater",           ItemClassification.useful),
    ("Electric Peashooter",ItemClassification.useful),
    ("Sap-fling",          ItemClassification.useful),
    ("Electric Currant",   ItemClassification.useful),
    ("Marigold",           ItemClassification.filler),
    ("Laser Bean",         ItemClassification.useful),
    ("Blover",             ItemClassification.progression),  # needed for Frostbite
    ("Citron",             ItemClassification.useful),
    ("E.M. Peach",         ItemClassification.useful),
    ("Star Fruit",         ItemClassification.useful),
    ("Shooting Starfruit", ItemClassification.useful),
    ("Infi-nut",           ItemClassification.useful),
    ("Magnifying Grass",   ItemClassification.useful),
    ("Tile Turnip",        ItemClassification.useful),
    ("Apple Mortar",       ItemClassification.useful),
    ("Solar Tomato",       ItemClassification.useful),
    ("Hypno-shroom",       ItemClassification.useful),
    ("Sun-Shroom",         ItemClassification.useful),
    ("Puff-shroom",        ItemClassification.useful),
    ("Fume-Shroom",        ItemClassification.useful),
    ("Sun Bean",           ItemClassification.useful),
    ("Pea-nut",            ItemClassification.useful),
    ("Magnet-shroom",      ItemClassification.useful),
    ("Scaredy-shroom",     ItemClassification.filler),
    ("Plantern",           ItemClassification.useful),
    ("Vamporcini",         ItemClassification.useful),
    ("Ice-shroom",         ItemClassification.progression),  # needed for Frostbite
    ("Doom-shroom",        ItemClassification.useful),
    ("Lily Pad",           ItemClassification.progression),  # needed for Big Wave Beach
    ("Tangle Kelp",        ItemClassification.useful),
    ("Bowling Bulb",       ItemClassification.useful),
    ("Homing Thistle",     ItemClassification.useful),
    ("Guacodile",          ItemClassification.useful),
    ("Banana Launcher",    ItemClassification.useful),
    ("Sea-shroom",         ItemClassification.useful),
    ("Chomper",            ItemClassification.useful),
    ("Missile Toe",        ItemClassification.useful),
    ("Ghost Pepper",       ItemClassification.useful),
    ("Parsnip",            ItemClassification.useful),
    ("Hurrikale",          ItemClassification.useful),
    ("Hot Potato",         ItemClassification.progression),  # needed for Frostbite
    ("Pepper-pult",        ItemClassification.useful),
    ("Chard Guard",        ItemClassification.useful),
    ("Fire Peashooter",    ItemClassification.useful),
    ("Stunion",            ItemClassification.useful),
    ("Rotobaga",           ItemClassification.useful),
    ("Jack O' Lantern",    ItemClassification.useful),
    ("Sweet Potato",       ItemClassification.useful),
    ("Hot Date",           ItemClassification.useful),
    ("Gatling Pea",        ItemClassification.useful),
    ("Torchwood",          ItemClassification.useful),
    ("Flower Pot",         ItemClassification.filler),
    ("Lava Guava",         ItemClassification.useful),
    ("Red Stinger",        ItemClassification.useful),
    ("A.K.E.E.",           ItemClassification.useful),
    ("Endurian",           ItemClassification.useful),
    ("Toadstool",          ItemClassification.useful),
    ("Stallia",            ItemClassification.useful),
    ("Gold Leaf",          ItemClassification.useful),
    ("Skyshooter",         ItemClassification.filler),
    ("Moon Bean",          ItemClassification.filler),
    ("Strawburst",         ItemClassification.useful),
    ("Fire Gourd",         ItemClassification.useful),
    ("Snow Pea",           ItemClassification.useful),
    ("Bamboo Shoot",       ItemClassification.useful),
    ("Resistant Radish",   ItemClassification.useful),
    ("Heavenly Peach",     ItemClassification.useful),
    ("Power Lily",         ItemClassification.useful),
    ("Lychee",             ItemClassification.useful),
    ("Solar Sage",         ItemClassification.useful),
    ("Cantaloupe-pult",    ItemClassification.useful),
    ("Bamboozle",          ItemClassification.useful),
    ("Phat Beet",          ItemClassification.useful),
    ("Cactus",             ItemClassification.useful),
    ("Celery Stalker",     ItemClassification.useful),
    ("Thyme Warp",         ItemClassification.useful),
    ("Electric Blueberry", ItemClassification.useful),
    ("Garlic",             ItemClassification.useful),
    ("Spore-shroom",       ItemClassification.useful),
    ("Intensive Carrot",   ItemClassification.useful),
    ("Blooming Heart",     ItemClassification.useful),
    ("Grapeshot",          ItemClassification.useful),
    ("Primal Peashooter",  ItemClassification.useful),
    ("Primal Wall-nut",    ItemClassification.useful),
    ("Perfume-shroom",     ItemClassification.progression),  # needed for Jurassic
    ("Cold Snapdragon",    ItemClassification.useful),
    ("Primal Sunflower",   ItemClassification.useful),
    ("Primal Potato Mine", ItemClassification.useful),
    ("Meteor Flower",      ItemClassification.useful),
    ("Explode-O-Nut",      ItemClassification.useful),
    ("Shrinking Violet",   ItemClassification.useful),
    ("Moonflower",         ItemClassification.useful),
    ("Nightshade",         ItemClassification.useful),
    ("Shadow-shroom",      ItemClassification.useful),
    ("Dusk Lobber",        ItemClassification.useful),
    ("Grimrose",           ItemClassification.useful),
    ("Gold Bloom",         ItemClassification.useful),
    ("Escape Root",        ItemClassification.useful),
    ("Gloom Vine",         ItemClassification.useful),
    ("Gloom-shroom",       ItemClassification.useful),
    ("Umbrella Leaf",      ItemClassification.useful),
    ("Pumpkin",            ItemClassification.useful),
    ("Dragon Fruit",       ItemClassification.filler),
    ("Cran-Jelly",         ItemClassification.useful),
]

for i, (name, cls) in enumerate(_plants):
    PLANT_ITEMS.append(PvZ2Item(name, cls, BASE_ID + i))

# Non-plant items
OTHER_ITEMS: List[PvZ2Item] = []
_others = [
    ("World Key",        ItemClassification.progression, 12),
    ("Sun Bonus",        ItemClassification.useful,       2),
    ("Plantfood Slot",   ItemClassification.useful,       2),
    ("Seed Slot",        ItemClassification.useful,       2),
    ("Sun Shovel",       ItemClassification.useful,       3),
    ("Mower Launch",     ItemClassification.useful,       2),
    ("Lower Difficulty", ItemClassification.useful,       3),
    ("Wall-nut First Aid", ItemClassification.useful,     1),
    ("Instant Recharge", ItemClassification.useful,       1),
    ("10 Gems",          ItemClassification.filler,       1),
    ("20 Gems",          ItemClassification.filler,       1),
    ("50 Gems",          ItemClassification.filler,       1),
]

_other_base = BASE_ID + len(PLANT_ITEMS)
_oi = 0
for name, cls, count in _others:
    for _ in range(count):
        OTHER_ITEMS.append(PvZ2Item(name, cls, _other_base + _oi))
        _oi += 1

ALL_ITEMS: List[PvZ2Item] = PLANT_ITEMS + OTHER_ITEMS

ITEM_NAME_TO_ITEM: Dict[str, PvZ2Item] = {}
ITEM_NAME_TO_ID: Dict[str, int] = {}
for item in ALL_ITEMS:
    ITEM_NAME_TO_ITEM[item.name] = item
    ITEM_NAME_TO_ID[item.name] = item.code


# ── Locations ─────────────────────────────────────────────────────────────────

@dataclasses.dataclass
class PvZ2LocationData:
    name: str
    region: str
    code: int
    is_victory: bool = False


def _make_locs() -> List[PvZ2LocationData]:
    locs = []
    id_ = BASE_ID + 0x10000  # separate namespace from items

    def add(name, region, victory=False):
        nonlocal id_
        locs.append(PvZ2LocationData(name, region, id_, victory))
        id_ += 1

    # ── Ancient Egypt ──
    add("Ancient Egypt Zomboss",           "Ancient Egypt", victory=True)
    add("Cabbage-pult Unlock",             "Ancient Egypt")
    add("Bloomerang Unlock",               "Ancient Egypt")
    add("Iceberg Lettuce Unlock",          "Ancient Egypt")
    add("Ancient Egypt - Special Portal 1","Ancient Egypt")
    add("Ancient Egypt - World Key",       "Ancient Egypt")
    add("Ice Weed Unlock",                 "Ancient Egypt")
    add("Grave Buster Unlock",             "Ancient Egypt")
    add("Bonk Choy Unlock",               "Ancient Egypt")
    add("Plant Food Slot Upgrade",         "Ancient Egypt")
    add("Repeater Unlock",                 "Ancient Egypt")
    add("Starting Sun Upgrade",            "Ancient Egypt")
    add("Twin Sunflower Unlock",           "Ancient Egypt")
    for i in range(1, 5):
        add(f"Ancient Egypt - Present {i}", "Ancient Egypt")
    add("Pyramid of Doom",                 "Ancient Egypt")
    add("Mummy Memory",                    "Ancient Egypt")

    # ── Pirate Seas ──
    add("Pirate Seas Zomboss",             "Pirate Seas", victory=True)
    add("Kernel-pult Unlock",              "Pirate Seas")
    add("Snap Dragon Unlock",              "Pirate Seas")
    add("Spikeweed Unlock",               "Pirate Seas")
    add("Pirate Seas - World Key",         "Pirate Seas")
    add("Spring Bean Unlock",             "Pirate Seas")
    add("Coconut Cannon Unlock",           "Pirate Seas")
    add("Sun Shovel Upgrade",              "Pirate Seas")
    add("Threepeater Unlock",              "Pirate Seas")
    add("Spikerock Unlock",               "Pirate Seas")
    add("Seed Slot Upgrade",               "Pirate Seas")
    add("Cherry Bomb Unlock",              "Pirate Seas")
    for i in range(1, 5):
        add(f"Pirate Seas - Present {i}",  "Pirate Seas")
    add("Dead Man's Booty",                "Pirate Seas")

    # ── Wild West ──
    add("Wild West Zomboss",               "Wild West", victory=True)
    add("Split Pea Unlock",                "Wild West")
    add("Chili Bean Unlock",               "Wild West")
    add("Pea Pod Unlock",                  "Wild West")
    add("Wild West - World Key",           "Wild West")
    add("Lightning Reed Unlock",           "Wild West")
    add("Sun Shovel Unlock",               "Wild West")
    add("Melon-Pult Unlock",               "Wild West")
    add("Wall-nut First Aid",              "Wild West")
    add("Tall-nut Unlock",                 "Wild West")
    add("Winter Melon Unlock",             "Wild West")
    for i in range(1, 5):
        add(f"Wild West - Present {i}",    "Wild West")
    add("Plant Food Recharge",             "Wild West")
    add("Big Bad Butte",                   "Wild West")

    # ── Far Future ──
    add("Far Future Zomboss",              "Far Future", victory=True)
    add("Laser Bean Unlock",               "Far Future")
    add("Blover Unlock",                   "Far Future")
    add("Citron Unlock",                   "Far Future")
    add("Far Future - World Key",          "Far Future")
    add("E.M. Peach Unlock",               "Far Future")
    add("Infi-nut Unlock",                 "Far Future")
    add("Magnifying Grass Unlock",         "Far Future")
    add("Star Fruit Unlock",               "Far Future")
    add("Mower Launch",                    "Far Future")
    add("Tile Turnip Unlock",              "Far Future")
    for i in range(1, 5):
        add(f"Far Future - Present {i}",   "Far Future")
    add("Terror from Tomorrow",            "Far Future")

    # ── Dark Ages ──
    add("Dark Ages Zomboss",               "Dark Ages", victory=True)
    add("Sun-Shroom Unlock",               "Dark Ages")
    add("Puff-Shroom Unlock",              "Dark Ages")
    add("Fume-Shroom Unlock",              "Dark Ages")
    add("Dark Ages - Special Portal 1",    "Dark Ages")
    add("Dark Ages - Special Portal 2",    "Dark Ages")
    add("Sun Bean Unlock",                 "Dark Ages")
    add("Hypno-Shroom Unlock",             "Dark Ages")
    add("Dark Ages - World Key",           "Dark Ages")
    add("Magnet-Shroom Unlock",            "Dark Ages")
    add("Peanut Unlock",                   "Dark Ages")
    for i in range(1, 5):
        add(f"Dark Ages - Present {i}",    "Dark Ages")
    add("Arthur's Challenge",              "Dark Ages")

    # ── Big Wave Beach ──
    add("Big Wave Beach Zomboss",          "Big Wave Beach", victory=True)
    add("Lily Pad Unlock",                 "Big Wave Beach")
    add("Tangle Kelp Unlock",              "Big Wave Beach")
    add("Bowling Bulb Unlock",             "Big Wave Beach")
    add("Chomper Unlock",                  "Big Wave Beach")
    add("Big Wave Beach - Special Portal 1","Big Wave Beach")
    add("Big Wave Beach - World Key",      "Big Wave Beach")
    add("Guacodile Unlock",                "Big Wave Beach")
    add("Big Wave Beach - Special Portal 2","Big Wave Beach")
    add("Banana Launcher Unlock",          "Big Wave Beach")
    add("Homing Thistle Unlock",           "Big Wave Beach")
    add("Sea-Shroom Unlock",               "Big Wave Beach")
    for i in range(1, 9):
        add(f"Big Wave Beach - Present {i}","Big Wave Beach")
    add("Tiki Torch-er",                   "Big Wave Beach")
    add("Wall-nut Bowling",                "Big Wave Beach")

    # ── Frostbite Caves ──
    add("Frostbite Caves Zomboss",         "Frostbite Caves", victory=True)
    add("Hot Potato Unlock",               "Frostbite Caves")
    add("Pepper-pult Unlock",              "Frostbite Caves")
    add("Chard Guard Unlock",              "Frostbite Caves")
    add("Frostbite Caves - Special Portal 1","Frostbite Caves")
    add("Hurrikale Unlock",                "Frostbite Caves")
    add("Frostbite Caves - World Key",     "Frostbite Caves")
    add("Stunion Unlock",                  "Frostbite Caves")
    add("Frostbite Caves - Special Portal 2","Frostbite Caves")
    add("Rotobaga Unlock",                 "Frostbite Caves")
    add("Fire Peashooter Unlock",          "Frostbite Caves")
    for i in range(1, 9):
        add(f"Frostbite Caves - Present {i}","Frostbite Caves")
    add("Icebound Battleground",           "Frostbite Caves")

    # ── Lost City ──
    add("Lost City Zomboss",               "Lost City", victory=True)
    add("Red Stinger Unlock",              "Lost City")
    add("A.K.E.E. Unlock",                 "Lost City")
    add("Endurian Unlock",                 "Lost City")
    add("Lava Guava Unlock",               "Lost City")
    add("Lost City - World Key",           "Lost City")
    add("Stallia Unlock",                  "Lost City")
    add("Gold Leaf Unlock",                "Lost City")
    add("Toadstool Unlock",                "Lost City")
    for i in range(1, 9):
        add(f"Lost City - Present {i}",    "Lost City")
    add("Temple of Bloom",                 "Lost City")

    # ── Kongfu Temple ──
    add("Kongfu Temple Zomboss 1",         "Kongfu Temple", victory=True)
    add("Kongfu Temple Zomboss 2",         "Kongfu Temple", victory=True)
    add("Fire Gourd Unlock",               "Kongfu Temple")
    add("Snow Pea Unlock",                 "Kongfu Temple")
    add("Kongfu Temple - World Key",       "Kongfu Temple")
    add("Bamboo Shoot Unlock",             "Kongfu Temple")
    add("Resistant Radish Unlock",         "Kongfu Temple")
    add("Heavenly Peach Unlock",           "Kongfu Temple")
    add("Power Lily Unlock",               "Kongfu Temple")
    add("Lychee Unlock",                   "Kongfu Temple")
    add("Martial Arts Contest 1",          "Kongfu Temple")
    add("Martial Arts Contest 2",          "Kongfu Temple")
    for i in range(1, 11):
        add(f"Kongfu Temple - Present {i}","Kongfu Temple")

    # ── Neon Mixtape Tour ──
    add("Neon Mixtape Tour Zomboss",       "Neon Mixtape Tour", victory=True)
    add("Phat Beat Unlock",                "Neon Mixtape Tour")
    add("Celery Stalker Unlock",           "Neon Mixtape Tour")
    add("Thyme Unlock",                    "Neon Mixtape Tour")
    add("Cactus Unlock",                   "Neon Mixtape Tour")
    add("Neon Mixtape Tour - Special Portal 1","Neon Mixtape Tour")
    add("Neon Mixtape Tour - World Key",   "Neon Mixtape Tour")
    add("Garlic Unlock",                   "Neon Mixtape Tour")
    add("Spore-Shroom Unlock",             "Neon Mixtape Tour")
    add("Intensive Carrot Unlock",         "Neon Mixtape Tour")
    add("Neon Mixtape Tour - Special Portal 2","Neon Mixtape Tour")
    add("Electric Blueberry Unlock",       "Neon Mixtape Tour")
    for i in range(1, 5):
        add(f"Neon Mixtape Tour - Present {i}","Neon Mixtape Tour")
    add("Greatest Hits",                   "Neon Mixtape Tour")

    # ── Jurassic Marsh ──
    add("Jurassic Marsh Zomboss",          "Jurassic Marsh", victory=True)
    add("Primal Peashooter Unlock",        "Jurassic Marsh")
    add("Grapeshot Unlock",                "Jurassic Marsh")
    add("Primal Wall-nut Unlock",          "Jurassic Marsh")
    add("Perfume-Shroom Unlock",           "Jurassic Marsh")
    add("Jurassic Marsh - World Key",      "Jurassic Marsh")
    add("Primal Sunflower Unlock",         "Jurassic Marsh")
    add("Cold Snapdragon Unlock",          "Jurassic Marsh")
    add("Primal Potato Mine Unlock",       "Jurassic Marsh")
    for i in range(1, 7):
        add(f"Jurassic Marsh - Present {i}","Jurassic Marsh")
    add("La Brainza Tar Pits",             "Jurassic Marsh")

    # ── Modern Day ──
    add("Modern Day Zomboss",              "Modern Day", victory=True)
    add("Escape Root Unlock",              "Modern Day")
    add("Modern Day - Special Portal 1",   "Modern Day")
    add("Modern Day - Special Portal 2",   "Modern Day")
    add("Moonflower Unlock",               "Modern Day")
    add("Nightshade Unlock",               "Modern Day")
    add("Shadow-shroom Unlock",            "Modern Day")
    add("Shrinking Violet Unlock",         "Modern Day")
    add("Modern Day - World Key",          "Modern Day")
    add("Dusk Lobber Unlock",              "Modern Day")
    add("Grimrose Unlock",                 "Modern Day")
    for i in range(1, 7):
        add(f"Modern Day - Present {i}",   "Modern Day")
    add("Highway to the Danger Room",      "Modern Day")

    return locs


ALL_LOCATIONS = _make_locs()
LOC_NAME_TO_DATA: Dict[str, PvZ2LocationData] = {l.name: l for l in ALL_LOCATIONS}
LOC_NAME_TO_ID: Dict[str, int] = {l.name: l.code for l in ALL_LOCATIONS}


# ── World key requirements per region ─────────────────────────────────────────
KEY_REQS: Dict[str, int] = {
    "Pirate Seas": 1, "Wild West": 2, "Far Future": 3, "Dark Ages": 4,
    "Big Wave Beach": 5, "Frostbite Caves": 6, "Lost City": 7,
    "Kongfu Temple": 8, "Neon Mixtape Tour": 8,
    "Jurassic Marsh": 9, "Modern Day": 10,
}


# ── World class ───────────────────────────────────────────────────────────────

class PvZ2Web(WebWorld):
    theme = "grass"
    tutorials = [Tutorial(
        "Mod Setup Guide",
        "How to set up the PvZ2 Gardendless Archipelago mod",
        "English",
        "setup.md",
        "setup/en",
        ["Trikehard"]
    )]


class PvZ2GardendlessWorld(World):
    """
    PvZ2 Gardendless — A web-based reimagining of Plants vs. Zombies 2.
    Collect World Keys to unlock new worlds and receive plants as items
    from the multiworld. Complete levels and defeat Zomboss in each world
    to send checks to other players.
    """

    game = GAME_NAME
    web = PvZ2Web()
    topology_present = True

    item_name_to_id = ITEM_NAME_TO_ID
    location_name_to_id = LOC_NAME_TO_ID

    # Required for AP 0.5+
    item_name_groups: Dict[str, set] = {
        "Plants": {i.name for i in PLANT_ITEMS},
        "World Keys": {"World Key"},
        "Upgrades": {"Sun Bonus", "Plantfood Slot", "Seed Slot", "Sun Shovel",
                     "Mower Launch", "Lower Difficulty", "Wall-nut First Aid", "Instant Recharge"},
    }

    def create_item(self, name: str) -> Item:
        item_data = ITEM_NAME_TO_ITEM.get(name)
        if item_data:
            return Item(name, item_data.classification, item_data.code, self.player)
        # Filler fallback
        return Item(name, ItemClassification.filler, None, self.player)

    def create_items(self) -> None:
        # Pool size = non-victory locations only (victory slots hold locked events)
        pool_size = len(ALL_LOCATIONS)  # all 218 locations need items; Victory event is locked separately

        # 1. Always include all 12 World Keys
        for _ in range(12):
            self.multiworld.itempool.append(self.create_item("World Key"))

        # 2. All progression + useful plants
        for plant in PLANT_ITEMS:
            if plant.classification in (ItemClassification.progression,
                                        ItemClassification.useful):
                self.multiworld.itempool.append(self.create_item(plant.name))

        # 3. Fill remaining with upgrades, then filler plants, then gems
        remaining = pool_size - len(self.multiworld.itempool)

        upgrades = [
            ("Sun Bonus", 2), ("Plantfood Slot", 2), ("Seed Slot", 2),
            ("Sun Shovel", 3), ("Mower Launch", 2), ("Lower Difficulty", 3),
            ("Wall-nut First Aid", 1), ("Instant Recharge", 1),
        ]
        for name, count in upgrades:
            for _ in range(count):
                if remaining <= 0:
                    break
                self.multiworld.itempool.append(
                    Item(name, ItemClassification.useful,
                         ITEM_NAME_TO_ID.get(name), self.player))
                remaining -= 1

        for plant in PLANT_ITEMS:
            if remaining <= 0:
                break
            if plant.classification == ItemClassification.filler:
                self.multiworld.itempool.append(self.create_item(plant.name))
                remaining -= 1

        gem_names = ["10 Gems", "20 Gems", "50 Gems"]
        gi = 0
        while remaining > 0:
            n = gem_names[gi % 3]
            self.multiworld.itempool.append(
                Item(n, ItemClassification.filler, ITEM_NAME_TO_ID.get(n), self.player))
            gi += 1
            remaining -= 1

    def create_regions(self) -> None:
        menu = Region("Menu", self.player, self.multiworld)

        # Ancient Egypt is always reachable (starting region)
        egypt = Region("Ancient Egypt", self.player, self.multiworld)
        menu.connect(egypt)

        regions: Dict[str, Region] = {"Ancient Egypt": egypt, "Menu": menu}

        # Create all other regions
        region_names = list(KEY_REQS.keys())
        for rname in region_names:
            r = Region(rname, self.player, self.multiworld)
            regions[rname] = r

        # Connect regions with World Key rules
        connections = {
            "Ancient Egypt": ["Pirate Seas"],
            "Pirate Seas":   ["Wild West"],
            "Wild West":     ["Far Future"],
            "Far Future":    ["Dark Ages"],
            "Dark Ages":     ["Big Wave Beach"],
            "Big Wave Beach":["Frostbite Caves"],
            "Frostbite Caves":["Lost City"],
            "Lost City":     ["Kongfu Temple", "Neon Mixtape Tour"],
            "Kongfu Temple": ["Neon Mixtape Tour"],
            "Neon Mixtape Tour":["Jurassic Marsh"],
            "Jurassic Marsh":["Modern Day"],
        }

        for src, dests in connections.items():
            for dest in dests:
                req = KEY_REQS.get(dest, 0)
                if req > 0:
                    regions[src].connect(
                        regions[dest],
                        f"{src} → {dest}",
                        lambda state, r=req: state.count("World Key", self.player) >= r
                    )
                else:
                    regions[src].connect(regions[dest])

        # Add locations to their regions
        for loc_data in ALL_LOCATIONS:
            region = regions.get(loc_data.region)
            if region is None:
                region = egypt  # fallback
            loc = Location(self.player, loc_data.name, loc_data.code, region)
            region.locations.append(loc)

        # Victory condition: defeat all Zomboss fights
        # Place a "Victory" event at Modern Day Zomboss
        victory_region = regions["Modern Day"]
        victory_loc = Location(self.player, "Victory", None, victory_region)
        victory_loc.place_locked_item(
            Item("Victory", ItemClassification.progression, None, self.player)
        )
        victory_region.locations.append(victory_loc)
        self.multiworld.completion_condition[self.player] = \
            lambda state: state.has("Victory", self.player)

        # Register all regions
        for r in regions.values():
            self.multiworld.regions.append(r)

    def set_rules(self) -> None:
        # Frostbite Caves requires Hot Potato (to thaw frozen plants)
        fc_locs = [l for l in ALL_LOCATIONS if l.region == "Frostbite Caves"]
        for loc_data in fc_locs:
            loc = self.multiworld.get_location(loc_data.name, self.player)
            loc.access_rule = lambda state: (
                state.has("Hot Potato", self.player) or
                state.has("Pepper-pult", self.player) or
                state.has("Fire Peashooter", self.player)
            )

        # Big Wave Beach requires Lily Pad
        bwb_locs = [l for l in ALL_LOCATIONS if l.region == "Big Wave Beach"]
        for loc_data in bwb_locs:
            loc = self.multiworld.get_location(loc_data.name, self.player)
            loc.access_rule = lambda state: state.has("Lily Pad", self.player)

        # Jurassic Marsh requires Perfume-shroom (to stop dinos)
        jm_locs = [l for l in ALL_LOCATIONS if l.region == "Jurassic Marsh"]
        for loc_data in jm_locs:
            loc = self.multiworld.get_location(loc_data.name, self.player)
            loc.access_rule = lambda state: state.has("Perfume-shroom", self.player)

    def fill_slot_data(self) -> Dict[str, Any]:
        return {
            "death_link": False,
            "game_version": "0.8.x",
        }
