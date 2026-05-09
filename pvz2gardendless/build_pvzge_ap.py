"""
PvZ2 Gardendless Archipelago - Automated Builder
=================================================
Clones the game source, patches tmpPatch.js with the AP client,
and builds a ready-to-run exe — all in a folder you choose.

Requirements:
  - Python 3.8+  (you have this if you have Archipelago)
  - Node.js 18+  (https://nodejs.org)
  - Git           (https://git-scm.com)
  - Internet connection for the initial clone (~500MB)

Usage: double-click this file, or run:
  python build_pvzge_ap.py
"""

import os
import sys
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog
import queue

# ── AP client code to inject into tmpPatch.js ────────────────────────────────
# This replaces the original tmpPatch.js entirely.
TMPPATCH_CONTENT = r"""
// PvZ2 Gardendless — Archipelago Client
// Injected via automated build. See https://github.com/Twig6943/PVZGE-Electron

// ── Electron shim (original tmpPatch.js functionality) ───────────────────────
const electron = {
  isFullscreen: () => !!(document.fullscreenElement || document.mozFullScreenElement || document.webkitFullscreenElement || document.msFullscreenElement),
  enterFullscreen: (el = document.documentElement) => { (el.requestFullscreen || el.mozRequestFullScreen || el.webkitRequestFullscreen || el.msRequestFullscreen || (() => {})).call(el); },
  exitFullscreen: () => { if (electron.isFullscreen()) (document.exitFullscreen || document.mozCancelFullScreen || document.webkitExitFullscreen || document.msExitFullscreen || (() => {})).call(document); },
  ipcRenderer: {
    send(ch, ...data) {
      if (ch === 'e_fullScreen') return electron.isFullscreen() ? electron.exitFullscreen() : electron.enterFullscreen();
      if (ch === 'e_window') return electron.exitFullscreen();
      if (ch === 'e_openURL') return window.open(data[0], '_blank');
    },
    sendSync(ch) { if (ch === 'e_isFullScreen') return electron.isFullscreen(); },
    on() {}
  },
  shell: { openExternal: url => window.open(url, '_blank') }
};
window.electron = electron;

// ── Capture AllPlayerProperties from SystemJS ─────────────────────────────────
// The game uses SystemJS module loading. We intercept the module registration
// for PlayerProperties.ts to capture AllPlayerProperties before the game starts.
// This gives us a live reference to the in-memory player data object.
(function() {
  function installAPHooks(AP) {
    // Intercept ALL unlockPlant calls — block every plant the game tries to
    // unlock (tutorial rewards, level completion rewards, everything) unless
    // AP has explicitly granted it via a received item.
    const _origUnlockPlant = AP.unlockPlant.bind(AP);
    AP.unlockPlant = function(plantId) {
      const granted = window._AP_grantedPlantIds || new Set();
      if (!granted.has(plantId)) return; // not granted by AP yet — block it
      return _origUnlockPlant(plantId);
    };
    AP._ap_hooked = true;
  }

  const _origRegister = System.register.bind(System);
  System.register = function(name, deps, declare) {
    if (typeof name === 'string' && name.includes('PlayerProperties.ts')) {
      const _origDeclare = declare;
      declare = function(_export, _context) {
        const result = _origDeclare(function(exportName, value) {
          if (exportName === 'AllPlayerProperties') {
            window._AP_AllPlayerProperties = value;
            // Install hooks immediately so BASEUNLOCKLIST calls are intercepted
            installAPHooks(value);
          }
          return _export(exportName, value);
        }, _context);
        return result;
      };
    }
    return _origRegister(name, deps, declare);
  };
})();

// ── Archipelago Client ────────────────────────────────────────────────────────
(function () {
  'use strict';

  const SAVE_KEY   = 'PvZ2_PlayerProperties';
  const CFG_KEY    = 'ap_pvz2_cfg';
  const STATE_KEY  = 'ap_pvz2_state';
  const GAME_NAME  = 'PvZ2 Gardendless';
  const AP_VER     = { major: 0, minor: 5, build: 0 };

  // World enum IDs (from WorldMapSceneDisplayEnum in game source)
  // World enum IDs (WorldMapSceneDisplayEnum from game source)
  const W = { egypt:1, pirate:2, cowboy:3, future:4, dark:5, beach:6,
               iceage:7, lostcity:8, epic:9, eighties:10, dino:11, modern:12, kongfu:13, sky:26 };

  // Plant enum IDs (from PlantEnum in game source)
  const P = {
    Peashooter:0, Sunflower:1, Wallnut:2, PotatoMine:3, CabbagePult:4, Bloomerang:5,
    IcebergLettuce:6, BonkChoy:7, Repeater:8, GraveBuster:12, Pumpkin:13, PeaVine:14,
    FirePeashooter:16, ThreePeater:17, PrimalPea:18, Rotobaga:19, HomingThistle:20,
    StarFruit:21, ShootingStarfruit:22, LilyPad:23, SunShroom:24, TwinSunflower:25,
    Dragonbruit:26, Moonflower:27, SnowPea:28, LightningReed:29, KernelPult:30,
    MeteorFlower:31, SpringBean:32, UmbrellaLeaf:33, MelonPult:34, WinterMelon:35,
    Blover:36, Spikeweed:37, Spikerock:38, Chomper:39, PrimalWallnut:41, Buttercup:42,
    BananaLauncher:43, MissileToe:44, CherryBomb:45, DoomShroom:46, CranJelly:47,
    Torchwood:49, Jalapeno:50, PuffShroom:51, GloomVine:52, Vamporcini:53,
    PrimalPotatoMine:54, Cactus:55, PowerLily:56, CoconutCannon:57, PeaPod:58,
    SnapDragon:59, GatlingPea:60, SplitPea:61, ChiliBean:62, Tallnut:63,
    Hurrikale:64, Stallia:65, ElectricPeashooter:66, Squash:67, GloomShroom:68,
    MagnifyingGrass:69, CeleryStalker:70, Sapfling:71, Parsnip:72, ExplodeONut:73,
    Grapeshot:74, Plantern:75, HeavenlyPeach:76, JackOLantern:77, Dandelion:78,
    ChardGuard:79, HypnoShroom:80, ElectricCurrant:81, EscapeRoot:82, Imitater:83,
    ShadowShroom:84, MagnetShroom:85, EMPeach:87, Citron:88, LaserBean:89,
    SolarTomato:90, TileTurnip:97, AppleMortar:106, RedStinger:107, Skyshooter:108,
    SunBean:109, Peanut:110, TangleKelp:114, BowlingBulb:115, Guacodile:120,
    GhostPepper:127, SweetPotato:128, PepperPult:129, HotPotato:130, Stunion:131,
    GoldLeaf:132, AKEE:133, Endurian:134, Toadstool:135, LavaGuava:136, PhatBeet:137,
    Strawburst:138, ThymeWarp:139, SeaShroom:141, Garlic:142, ElectricBlueBerry:143,
    SporeShroom:144, IntensiveCarrot:145, PrimalSunflower:146, MoonBean:147,
    ColdSnapDragon:148, NightShade:149, DuskLobber:150, Grimrose:151, GoldBloom:152,
    BloomingHeart:153, ShrinkingViolet:154, HotDate:155, FireGourd:156, BambooShoot:157,
    Snowdrop:158, Lychee:159, PerfumeShroom:160, SolarSage:161, Bamboozle:162,
    Cantaloupe:164, Iceweed:165
  };

  // id -> actual CODENAME from PlantFeatures.json (game's save key)
  // These are the exact strings used as keys in plantProps in the save data.
  // Generated from PlantFeatures.json - do NOT use P enum key names, they differ!
  const ID_TO_CN = {
    0:'peashooter', 1:'sunflower', 2:'wallnut', 3:'potatomine',
    4:'cabbagepult', 5:'bloomerang', 6:'iceburg', 7:'bonkchoy',
    8:'repeater', 12:'gravebuster', 13:'pumpkin', 14:'pvine',
    16:'firepeashooter', 17:'threepeater', 18:'primalpeashooter',
    19:'rotobaga', 20:'homingthistle', 21:'starfruit', 22:'shootingstarfruit',
    23:'lilypad', 24:'sunshroom', 25:'twinsunflower', 26:'dragonbruit',
    27:'moonflower', 28:'snowpea', 29:'lightningreed', 30:'kernelpult',
    31:'meteorflower', 32:'springbean', 33:'umbrellaleaf',
    34:'melonpult', 35:'wintermelon', 36:'blover', 37:'spikeweed',
    38:'spikerock', 39:'chomper', 41:'primalwallnut', 42:'buttercup',
    43:'banana', 44:'missiletoe', 45:'cherry_bomb', 46:'doomshroom',
    47:'cranjelly', 49:'torchwood', 50:'jalapeno', 51:'puffshroom',
    52:'gloomvine', 53:'vamporcini', 54:'primalpotatomine',
    55:'cactus', 56:'powerlily', 57:'coconutcannon', 58:'peapod',
    59:'snapdragon', 60:'gatling', 61:'splitpea', 62:'chilibean',
    63:'tallnut', 64:'hurrikale', 65:'stallia', 66:'electricpeashooter',
    67:'squash', 68:'gloomshroom', 69:'magnifyinggrass', 70:'celerystalker',
    71:'sapfling', 72:'parsnip', 73:'explodeonut', 74:'grapeshot',
    75:'plantern', 76:'peach', 77:'jackolantern', 78:'dandelion',
    79:'chardguard', 80:'hypnoshroom', 81:'electriccurrant',
    82:'escaperoot', 83:'imitater', 84:'shadowshroom', 85:'magnetshroom',
    87:'empea', 88:'citron', 89:'laser_bean', 90:'solartomato',
    97:'powerplant', 106:'applemortar', 107:'redstinger', 108:'skyshooter',
    109:'sunbean', 110:'peanut', 114:'tanglekelp', 115:'bowlingbulb',
    120:'guacodile', 127:'ghostpepper', 128:'sweetpotato', 129:'pepperpult',
    130:'hotpotato', 131:'stunion', 132:'goldleaf', 133:'akee',
    134:'endurian', 135:'toadstool', 136:'lavaguava', 137:'phatbeet',
    138:'strawburst', 139:'thymewarp', 141:'seashroom', 142:'garlic',
    143:'electricblueberry', 144:'sporeshroom', 145:'intensivecarrot',
    146:'primalsunflower', 147:'moonbean', 148:'coldsnapdragon',
    149:'nightshade', 150:'dusklobber', 151:'grimrose', 152:'goldbloom',
    153:'bloominghearts', 154:'shrinkingviolet', 155:'hotdate',
    156:'firegourd', 157:'bambooshoot', 158:'snowdrop', 159:'lychee',
    160:'perfumeshroom', 161:'solarsage', 162:'bamboozle',
    164:'cantaloupe', 165:'iceweed',
  };

  // AP item name -> plant enum ID
  const ITEM_PLANT = {
    'Peashooter':P.Peashooter,'Sunflower':P.Sunflower,'Wall-nut':P.Wallnut,
    'Potato Mine':P.PotatoMine,'Cabbage-pult':P.CabbagePult,'Bloomerang':P.Bloomerang,
    'Iceberg Lettuce':P.IcebergLettuce,'Bonk Choy':P.BonkChoy,'Repeater':P.Repeater,
    'Grave Buster':P.GraveBuster,'Pumpkin':P.Pumpkin,'Pea Vine':P.PeaVine,
    'Fire Peashooter':P.FirePeashooter,'Threepeater':P.ThreePeater,'Rotobaga':P.Rotobaga,
    'Homing Thistle':P.HomingThistle,'Star Fruit':P.StarFruit,
    'Shooting Starfruit':P.ShootingStarfruit,'Lily Pad':P.LilyPad,
    'Sun-Shroom':P.SunShroom,'Twin Sunflower':P.TwinSunflower,'Dragon Fruit':P.Dragonbruit,
    'Moonflower':P.Moonflower,'Snow Pea':P.SnowPea,'Lightning Reed':P.LightningReed,
    'Kernel-pult':P.KernelPult,'Meteor Flower':P.MeteorFlower,'Spring Bean':P.SpringBean,
    'Umbrella Leaf':P.UmbrellaLeaf,'Melon-Pult':P.MelonPult,'Winter Melon':P.WinterMelon,
    'Blover':P.Blover,'Spikeweed':P.Spikeweed,'Spikerock':P.Spikerock,'Chomper':P.Chomper,
    'Primal Wall-nut':P.PrimalWallnut,'Buttercup':P.Buttercup,
    'Banana Launcher':P.BananaLauncher,'Missile Toe':P.MissileToe,
    'Cherry Bomb':P.CherryBomb,'Doom-shroom':P.DoomShroom,'Cran-Jelly':P.CranJelly,
    'Torchwood':P.Torchwood,'Jalapeno':P.Jalapeno,'Puff-shroom':P.PuffShroom,
    'Gloom Vine':P.GloomVine,'Vamporcini':P.Vamporcini,
    'Primal Potato Mine':P.PrimalPotatoMine,'Cactus':P.Cactus,'Power Lily':P.PowerLily,
    'Coconut Cannon':P.CoconutCannon,'Pea Pod':P.PeaPod,'Snap Dragon':P.SnapDragon,
    'Gatling Pea':P.GatlingPea,'Split Pea':P.SplitPea,'Chili Bean':P.ChiliBean,
    'Tall-nut':P.Tallnut,'Hurrikale':P.Hurrikale,'Stallia':P.Stallia,
    'Electric Peashooter':P.ElectricPeashooter,'Squash':P.Squash,
    'Gloom-shroom':P.GloomShroom,'Magnifying Grass':P.MagnifyingGrass,
    'Celery Stalker':P.CeleryStalker,'Sap-fling':P.Sapfling,'Parsnip':P.Parsnip,
    'Explode-O-Nut':P.ExplodeONut,'Grapeshot':P.Grapeshot,'Plantern':P.Plantern,
    'Heavenly Peach':P.HeavenlyPeach,"Jack O' Lantern":P.JackOLantern,
    'Dandelion':P.Dandelion,'Chard Guard':P.ChardGuard,'Hypno-shroom':P.HypnoShroom,
    'Electric Currant':P.ElectricCurrant,'Escape Root':P.EscapeRoot,
    'Imitater':P.Imitater,'Shadow-shroom':P.ShadowShroom,'Magnet-shroom':P.MagnetShroom,
    'E.M. Peach':P.EMPeach,'Citron':P.Citron,'Laser Bean':P.LaserBean,
    'Solar Tomato':P.SolarTomato,'Tile Turnip':P.TileTurnip,'Apple Mortar':P.AppleMortar,
    'Red Stinger':P.RedStinger,'Skyshooter':P.Skyshooter,'Sun Bean':P.SunBean,
    'Pea-nut':P.Peanut,'Tangle Kelp':P.TangleKelp,'Bowling Bulb':P.BowlingBulb,
    'Guacodile':P.Guacodile,'Ghost Pepper':P.GhostPepper,'Sweet Potato':P.SweetPotato,
    'Pepper-pult':P.PepperPult,'Hot Potato':P.HotPotato,'Stunion':P.Stunion,
    'Gold Leaf':P.GoldLeaf,'A.K.E.E.':P.AKEE,'Endurian':P.Endurian,
    'Toadstool':P.Toadstool,'Lava Guava':P.LavaGuava,'Phat Beet':P.PhatBeet,
    'Strawburst':P.Strawburst,'Thyme Warp':P.ThymeWarp,'Sea-shroom':P.SeaShroom,
    'Garlic':P.Garlic,'Electric Blueberry':P.ElectricBlueBerry,
    'Spore-shroom':P.SporeShroom,'Intensive Carrot':P.IntensiveCarrot,
    'Primal Sunflower':P.PrimalSunflower,'Moon Bean':P.MoonBean,
    'Cold Snapdragon':P.ColdSnapDragon,'Nightshade':P.NightShade,
    'Dusk Lobber':P.DuskLobber,'Grimrose':P.Grimrose,'Gold Bloom':P.GoldBloom,
    'Blooming Heart':P.BloomingHeart,'Shrinking Violet':P.ShrinkingViolet,
    'Hot Date':P.HotDate,'Fire Gourd':P.FireGourd,'Bamboo Shoot':P.BambooShoot,
    'Snowdrop':P.Snowdrop,'Lychee':P.Lychee,'Perfume-shroom':P.PerfumeShroom,
    'Solar Sage':P.SolarSage,'Bamboozle':P.Bamboozle,'Cantaloupe-pult':P.Cantaloupe,
    'Iceweed':P.Iceweed
  };

  // World Key gates: [keysNeeded, [worldIds]]
  // Unique world key items -> which world they unlock
  // Each key unlocks exactly one world. No progressive gating.
  const WORLD_KEY_MAP = {
    'Pirate Seas Key':      [W.pirate],
    'Wild West Key':        [W.cowboy],
    'Far Future Key':       [W.future],
    'Dark Ages Key':        [W.dark],
    'Big Wave Beach Key':   [W.beach],
    'Frostbite Caves Key':  [W.iceage],
    'Lost City Key':        [W.lostcity],
    'Kongfu Temple Key':    [W.eighties, W.kongfu],  // both unlock at same time
    'Neon Mixtape Tour Key':[W.eighties],
    'Jurassic Marsh Key':   [W.dino],
    'Modern Day Key':       [W.modern],
  };

  // Auto-generated from level_rewards.csv
  const LOC_LEVELS = {
    'Sunflower Unlock':'tutorial1',
    'Wall-nut Unlock':'tutorial2',
    'Potatomine Unlock':'tutorial3',
    'Sauce Unlock':'tutorial4',
    'random_zomboss_egypt':'random_zomboss_egypt',
    'Map Unlock':'egypt1',
    'Cabbagepult Unlock':'egypt2',
    'Bloomerang Unlock':'egypt3',
    'Powerupgadget Unlock':'egypt4',
    'Iceburg Unlock':'egypt5',
    'Branch Unlock Egypt 6':'egypt6',
    'Note Egypt Unlock':'egypt7',
    'World Key - Ancient Egypt':'egypt8',
    'Gravebuster Unlock':'egypt9',
    'egypt10':'egypt10',
    'Branch Unlock Egypt 11':'egypt11',
    'Dangerroom Egypt Unlock':'egypt12',
    'Bonkchoy Unlock':'egypt13',
    'egypt14':'egypt14',
    'Branch Unlock Egypt 15':'egypt15',
    'egypt16':'egypt16',
    'Upgrade Pf Slots Lvl1 Unlock':'egypt17',
    'egypt18':'egypt18',
    'Repeater Unlock':'egypt19',
    'egypt20':'egypt20',
    'egypt20_1':'egypt20_1',
    'Upgrade Starting Sun Lvl1 Unlock':'egypt21',
    'egypt21_1':'egypt21_1',
    'Branch Unlock Egypt 22':'egypt22',
    'egypt22_1':'egypt22_1',
    'Dangerroom Egypt Minigame Unlock':'egypt23',
    'Twinsunflower Unlock':'egypt24',
    'egypt24_1':'egypt24_1',
    'Worldtrophy Egypt Unlock':'egypt25',
    'egypt26':'egypt26',
    'Branch Unlock Egypt 27':'egypt27',
    'egypt28':'egypt28',
    'egypt29':'egypt29',
    'Branch Unlock Egypt 30':'egypt30',
    'Dangerroom Egypt2 Unlock':'egypt31',
    'egypt32':'egypt32',
    'egypt33':'egypt33',
    'Branch Unlock Egypt 34':'egypt34',
    'egypt35':'egypt35',
    'egypt_dangerroom':'egypt_dangerroom',
    'egypt_dangerroom2':'egypt_dangerroom2',
    'egypt_dangerroom_minigame':'egypt_dangerroom_minigame',
    'random_egypt':'random_egypt',
    'random_zomboss_pirate':'random_zomboss_pirate',
    'Kernelpult Unlock':'pirate1',
    'pirate2':'pirate2',
    'Snapdragon Unlock':'pirate3',
    'Dangerroom Pirate Unlock':'pirate4',
    'Branch Unlock Pirate 5':'pirate5',
    'Spikeweed Unlock':'pirate6',
    'Note Pirate Unlock':'pirate7',
    'World Key - Pirate Seas':'pirate8',
    'Springbean Unlock':'pirate9',
    'pirate10':'pirate10',
    'Coconutcannon Unlock':'pirate11',
    'Upgrade Sunshovel Lvl1 Unlock':'pirate12',
    'pirate13':'pirate13',
    'Threepeater Unlock':'pirate14',
    'pirate15':'pirate15',
    'Branch Unlock Pirate 16':'pirate16',
    'pirate17':'pirate17',
    'Spikerock Unlock':'pirate18',
    'pirate18_1':'pirate18_1',
    'Branch Unlock Pirate 19':'pirate19',
    'pirate20':'pirate20',
    'pirate20_1':'pirate20_1',
    'Upgrade 7 Slots Unlock':'pirate21',
    'pirate22':'pirate22',
    'pirate22_1':'pirate22_1',
    'Branch Unlock Pirate 23':'pirate23',
    'pirate23_1':'pirate23_1',
    'Cherry Bomb Unlock':'pirate24',
    'pirate24_1':'pirate24_1',
    'Worldtrophy Pirate Unlock':'pirate25',
    'pirate26':'pirate26',
    'Branch Unlock Pirate 27':'pirate27',
    'pirate28':'pirate28',
    'pirate29':'pirate29',
    'Branch Unlock Pirate 30':'pirate30',
    'pirate31':'pirate31',
    'pirate32':'pirate32',
    'Dangerroom Pirate2 Unlock':'pirate33',
    'pirate34':'pirate34',
    'pirate35':'pirate35',
    'pirate_dangerroom':'pirate_dangerroom',
    'pirate_dangerroom2':'pirate_dangerroom2',
    'random_pirate':'random_pirate',
    'random_zomboss_cowboy':'random_zomboss_cowboy',
    'Splitpea Unlock':'cowboy1',
    'Branch Unlock Cowboy 2':'cowboy2',
    'Dangerroom Cowboy Unlock':'cowboy3',
    'Chilibean Unlock':'cowboy4',
    'cowboy5':'cowboy5',
    'Peapod Unlock':'cowboy6',
    'Note Cowboy Unlock':'cowboy7',
    'World Key - Wild West':'cowboy8',
    'Lightningreed Unlock':'cowboy9',
    'cowboy10':'cowboy10',
    'Upgrade Sunshovel Lvl2 Unlock':'cowboy11',
    'Melonpult Unlock':'cowboy12',
    'cowboy12_1':'cowboy12_1',
    'cowboy13':'cowboy13',
    'Branch Unlock Cowboy 14':'cowboy14',
    'Upgrade Wallnut Firstaid Unlock':'cowboy15',
    'cowboy16':'cowboy16',
    'Branch Unlock Cowboy 17':'cowboy17',
    'Tallnut Unlock':'cowboy18',
    'cowboy18_1':'cowboy18_1',
    'cowboy19':'cowboy19',
    'Upgrade Pf Refresh Unlock':'cowboy20',
    'cowboy21':'cowboy21',
    'Branch Unlock Cowboy 22':'cowboy22',
    'cowboy22_1':'cowboy22_1',
    'cowboy23':'cowboy23',
    'cowboy23_1':'cowboy23_1',
    'Wintermelon Unlock':'cowboy24',
    'cowboy24_1':'cowboy24_1',
    'Worldtrophy Cowboy Unlock':'cowboy25',
    'Branch Unlock Cowboy 26':'cowboy26',
    'cowboy27':'cowboy27',
    'cowboy28':'cowboy28',
    'cowboy29':'cowboy29',
    'Branch Unlock Cowboy 30':'cowboy30',
    'cowboy31':'cowboy31',
    'cowboy32':'cowboy32',
    'Dangerroom Cowboy2 Unlock':'cowboy33',
    'Branch Unlock Cowboy 34':'cowboy34',
    'cowboy35':'cowboy35',
    'cowboy_dangerroom':'cowboy_dangerroom',
    'cowboy_dangerroom2':'cowboy_dangerroom2',
    'random_cowboy':'random_cowboy',
    'random_zomboss_future':'random_zomboss_future',
    'Laser Bean Unlock':'future1',
    'future2':'future2',
    'Blover Unlock':'future3',
    'Dangerroom Future Unlock':'future4',
    'Branch Unlock Future 5':'future5',
    'Citron Unlock':'future6',
    'Note Future Unlock':'future7',
    'World Key - Far Future':'future8',
    'Empea Unlock':'future9',
    'future10':'future10',
    'future10_1':'future10_1',
    'future10_2':'future10_2',
    'future10_3':'future10_3',
    'future10_4':'future10_4',
    'Branch Unlock Future 11':'future11',
    'future12':'future12',
    'Holonut Unlock':'future13',
    'future14':'future14',
    'Branch Unlock Future 15':'future15',
    'future16':'future16',
    'Magnifyinggrass Unlock':'future17',
    'future18':'future18',
    'future19':'future19',
    'Upgrade Manual Mowers 1 Unlock':'future20',
    'future21':'future21',
    'Branch Unlock Future 22':'future22',
    'future23':'future23',
    'Powerplant Unlock':'future24',
    'Worldtrophy Future Unlock':'future25',
    'future26':'future26',
    'Branch Unlock Future 27':'future27',
    'future28':'future28',
    'future29':'future29',
    'Branch Unlock Future 30':'future30',
    'future31':'future31',
    'Dangerroom Future2 Unlock':'future32',
    'Dangerroom Future Sunbomb Unlock':'future33',
    'Branch Unlock Future 34':'future34',
    'future35':'future35',
    'future_dangerroom':'future_dangerroom',
    'future_dangerroom2':'future_dangerroom2',
    'future_dangerroom_sunbomb':'future_dangerroom_sunbomb',
    'random_future':'random_future',
    'random_zomboss_dark':'random_zomboss_dark',
    'Sunshroom Unlock':'dark1',
    'Puffshroom Unlock':'dark2',
    'dark3':'dark3',
    'Fumeshroom Unlock':'dark4',
    'dark5':'dark5',
    'Sunbean Unlock':'dark6',
    'dark7':'dark7',
    'Branch Unlock Dark 8':'dark8',
    'Note Dark Unlock':'dark9',
    'World Key - Dark Ages':'dark10',
    'Branch Unlock Dark 11':'dark11',
    'Dangerroom Dark Unlock':'dark12',
    'Branch Unlock Dark 13':'dark13',
    'dark14':'dark14',
    'Magnetshroom Unlock':'dark15',
    'dark16':'dark16',
    'dark17':'dark17',
    'Branch Unlock Dark 18':'dark18',
    'dark18_1':'dark18_1',
    'dark19':'dark19',
    'Worldtrophy Dark Unlock':'dark20',
    'Scaredyshroom Unlock':'dark21',
    'dark22':'dark22',
    'Branch Unlock Dark 23':'dark23',
    'Branch Unlock Dark 24':'dark24',
    'Branch Unlock Dark 25':'dark25',
    'Dangerroom Dark2 Unlock':'dark26',
    'Dangerroom Dark Potion Unlock':'dark27',
    'dark28':'dark28',
    'Branch Unlock Dark 29':'dark29',
    'dark30':'dark30',
    'dark_dangerroom':'dark_dangerroom',
    'dark_dangerroom2':'dark_dangerroom2',
    'dark_dangerroom_potion':'dark_dangerroom_potion',
    'random_dark':'random_dark',
    'random_beach':'random_beach',
    'Lilypad Unlock':'beach1',
    'beach2':'beach2',
    'beach3':'beach3',
    'Branch Unlock Beach 4':'beach4',
    'beach5':'beach5',
    'Tanglekelp Unlock':'beach6',
    'beach7':'beach7',
    'Branch Unlock Beach 8':'beach8',
    'beach9':'beach9',
    'beach10':'beach10',
    'Bowlingbulb Unlock':'beach11',
    'Branch Unlock Beach 12':'beach12',
    'beach13':'beach13',
    'Branch Unlock Beach 14':'beach14',
    'Note Beach Unlock':'beach15',
    'World Key - Big Wave Beach':'beach16',
    'Branch Unlock Beach 17':'beach17',
    'beach18':'beach18',
    'Guacodile Unlock':'beach19',
    'Dangerroom Beach Unlock':'beach20',
    'beach21':'beach21',
    'Branch Unlock Beach 22':'beach22',
    'beach23':'beach23',
    'Dangerroom Beach Minigame Unlock':'beach24',
    'Branch Unlock Beach 25':'beach25',
    'beach26':'beach26',
    'Banana Unlock':'beach27',
    'beach28':'beach28',
    'beach29':'beach29',
    'Branch Unlock Beach 30':'beach30',
    'Seashroom Unlock':'beach31',
    'Worldtrophy Beach Unlock':'beach32',
    'beach33':'beach33',
    'beach34':'beach34',
    'beach35':'beach35',
    'Dangerroom Beach2 Unlock':'beach36',
    'beach37':'beach37',
    'beach38':'beach38',
    'beach39':'beach39',
    'beach40':'beach40',
    'beach41':'beach41',
    'beach42':'beach42',
    'beach_dangerroom':'beach_dangerroom',
    'beach_dangerroom2':'beach_dangerroom2',
    'beach_dangerroom_minigame_beach':'beach_dangerroom_minigame_beach',
    'beach_dangerroom_minigame_cowboy':'beach_dangerroom_minigame_cowboy',
    'beach_dangerroom_minigame_dark':'beach_dangerroom_minigame_dark',
    'beach_dangerroom_minigame_egypt':'beach_dangerroom_minigame_egypt',
    'beach_dangerroom_minigame_future':'beach_dangerroom_minigame_future',
    'beach_dangerroom_minigame_iceage':'beach_dangerroom_minigame_iceage',
    'beach_dangerroom_minigame_lostcity':'beach_dangerroom_minigame_lostcity',
    'beach_dangerroom_minigame_pirate':'beach_dangerroom_minigame_pirate',
    'iceage_dangerroom':'iceage_dangerroom',
    'Hotpotato Unlock':'iceage1',
    'iceage2':'iceage2',
    'iceage3':'iceage3',
    'Branch Unlock Iceage 4':'iceage4',
    'iceage5':'iceage5',
    'Pepperpult Unlock':'iceage6',
    'iceage7':'iceage7',
    'Branch Unlock Iceage 8':'iceage8',
    'iceage9':'iceage9',
    'iceage10':'iceage10',
    'Chardguard Unlock':'iceage11',
    'Branch Unlock Iceage 12':'iceage12',
    'iceage13':'iceage13',
    'Branch Unlock Iceage 14':'iceage14',
    'Note Iceage Unlock':'iceage15',
    'World Key - Frostbite Caves':'iceage16',
    'Branch Unlock Iceage 17':'iceage17',
    'iceage18':'iceage18',
    'Stunion Unlock':'iceage19',
    'Dangerroom Iceage Unlock':'iceage20',
    'iceage21':'iceage21',
    'Branch Unlock Iceage 22':'iceage22',
    'iceage23':'iceage23',
    'Branch Unlock Iceage 24':'iceage24',
    'iceage24_B':'iceage24_B',
    'iceage25':'iceage25',
    'Xshot Unlock':'iceage26',
    'iceage27':'iceage27',
    'iceage28':'iceage28',
    'Branch Unlock Iceage 29':'iceage29',
    'Worldtrophy Iceage Unlock':'iceage30',
    'Branch Unlock Iceage 31':'iceage31',
    'iceage32':'iceage32',
    'iceage33':'iceage33',
    'Branch Unlock Iceage 34':'iceage34',
    'Dangerroom Iceage2 Unlock':'iceage35',
    'iceage36':'iceage36',
    'iceage37':'iceage37',
    'iceage38':'iceage38',
    'iceage39':'iceage39',
    'iceage40':'iceage40',
    'iceage_dangerroom2':'iceage_dangerroom2',
    'lostcity_dangerroom':'lostcity_dangerroom',
    'Redstinger Unlock':'lostcity1',
    'lostcity2':'lostcity2',
    'lostcity3':'lostcity3',
    'Branch Unlock Lostcity 4':'lostcity4',
    'lostcity5':'lostcity5',
    'Akee Unlock':'lostcity6',
    'lostcity7':'lostcity7',
    'Branch Unlock Lostcity 8':'lostcity8',
    'lostcity9':'lostcity9',
    'Endurian Unlock':'lostcity10',
    'lostcity11':'lostcity11',
    'Branch Unlock Lostcity 12':'lostcity12',
    'lostcity13':'lostcity13',
    'Branch Unlock Lostcity 14':'lostcity14',
    'Note Lostcity Unlock':'lostcity15',
    'World Key - Lost City':'lostcity16',
    'Branch Unlock Lostcity 17':'lostcity17',
    'lostcity18':'lostcity18',
    'Stallia Unlock':'lostcity19',
    'Dangerroom Lostcity Unlock':'lostcity20',
    'lostcity21':'lostcity21',
    'lostcity22':'lostcity22',
    'Branch Unlock Lostcity 23':'lostcity23',
    'lostcity24':'lostcity24',
    'lostcity25':'lostcity25',
    'Goldleaf Unlock':'lostcity26',
    'lostcity27':'lostcity27',
    'Branch Unlock Lostcity 28':'lostcity28',
    'lostcity29':'lostcity29',
    'Branch Unlock Lostcity 30':'lostcity30',
    'lostcity31':'lostcity31',
    'Worldtrophy Lostcity Unlock':'lostcity32',
    'Branch Unlock Lostcity 33':'lostcity33',
    'Branch Unlock Lostcity 34':'lostcity34',
    'Branch Unlock Lostcity 35':'lostcity35',
    'Branch Unlock Lostcity 36':'lostcity36',
    'lostcity37':'lostcity37',
    'Branch Unlock Lostcity 38':'lostcity38',
    'Dangerroom Lostcity2 Unlock':'lostcity39',
    'Branch Unlock Lostcity 40':'lostcity40',
    'Branch Unlock Lostcity 41':'lostcity41',
    'lostcity42':'lostcity42',
    'lostcity_dangerroom2':'lostcity_dangerroom2',
    'kongfu_dangerroom':'kongfu_dangerroom',
    'Firegourd Unlock':'kongfu1',
    'kongfu2':'kongfu2',
    'kongfu3':'kongfu3',
    'kongfu4':'kongfu4',
    'kongfu5':'kongfu5',
    'Snowpea Unlock':'kongfu6',
    'kongfu7':'kongfu7',
    'World Key - Kongfu Temple':'kongfu8',
    'kongfu9':'kongfu9',
    'Bambooshoot Unlock':'kongfu10',
    'kongfu11':'kongfu11',
    'kongfu12':'kongfu12',
    'Turnip Unlock':'kongfu13',
    'Dangerroom Kongfu Unlock':'kongfu14',
    'kongfu15':'kongfu15',
    'kongfu16':'kongfu16',
    'kongfu17':'kongfu17',
    'kongfu18':'kongfu18',
    'Peach Unlock':'kongfu19',
    'kongfu20':'kongfu20',
    'kongfu21':'kongfu21',
    'kongfu22':'kongfu22',
    'kongfu23':'kongfu23',
    'kongfu24':'kongfu24',
    'kongfu25':'kongfu25',
    'kongfu26':'kongfu26',
    'kongfu27':'kongfu27',
    'kongfu28':'kongfu28',
    'Lychee Unlock':'kongfu29',
    'Dangerroom Kongfu2 Unlock':'kongfu30',
    'kongfu31':'kongfu31',
    'kongfu32':'kongfu32',
    'kongfu33':'kongfu33',
    'Solarsage Unlock':'kongfu34',
    'kongfu35':'kongfu35',
    'kongfu36':'kongfu36',
    'kongfu37':'kongfu37',
    'kongfu38':'kongfu38',
    'kongfu39':'kongfu39',
    'kongfu40':'kongfu40',
    'kongfu41':'kongfu41',
    'kongfu42':'kongfu42',
    'kongfu43':'kongfu43',
    'kongfu44':'kongfu44',
    'kongfu45':'kongfu45',
    'Cantaloupe Unlock':'kongfu46',
    'Dangerroom Kongfu3 Unlock':'kongfu47',
    'kongfu48':'kongfu48',
    'kongfu_dangerroom2':'kongfu_dangerroom2',
    'kongfu_dangerroom3':'kongfu_dangerroom3',
    'kongfu_dangerroom4':'kongfu_dangerroom4',
    'eighties_dangerroom':'eighties_dangerroom',
    'Phatbeet Unlock':'eighties1',
    'eighties2':'eighties2',
    'eighties3':'eighties3',
    'eighties4':'eighties4',
    'Celerystalker Unlock':'eighties5',
    'eighties6':'eighties6',
    'eighties7':'eighties7',
    'eighties8':'eighties8',
    'Thymewarp Unlock':'eighties9',
    'eighties10':'eighties10',
    'eighties11':'eighties11',
    'Branch Unlock Eighties 12':'eighties12',
    'eighties13':'eighties13',
    'Branch Unlock Eighties 14':'eighties14',
    'eighties15':'eighties15',
    'World Key - Neon Mixtape Tour':'eighties16',
    'Garlic Unlock':'eighties17',
    'eighties18':'eighties18',
    'eighties19':'eighties19',
    'Dangerroom Eighties Unlock':'eighties20',
    'Sporeshroom Unlock':'eighties21',
    'eighties22':'eighties22',
    'eighties23':'eighties23',
    'Branch Unlock Eighties 24':'eighties24',
    'eighties25':'eighties25',
    'Intensivecarrot Unlock':'eighties26',
    'eighties27':'eighties27',
    'eighties28':'eighties28',
    'Branch Unlock Eighties 29':'eighties29',
    'eighties30':'eighties30',
    'eighties31':'eighties31',
    'Worldtrophy Eighties Unlock':'eighties32',
    'dino_dangerroom':'dino_dangerroom',
    'Primalpeashooter Unlock':'dino1',
    'dino2':'dino2',
    'dino3':'dino3',
    'Primalwallnut Unlock':'dino4',
    'dino5':'dino5',
    'Branch Unlock Dino 6':'dino6',
    'Branch Unlock Dino 7':'dino7',
    'Perfumeshroom Unlock':'dino8',
    'dino9':'dino9',
    'dino10':'dino10',
    'dino11':'dino11',
    'Branch Unlock Dino 12':'dino12',
    'dino13':'dino13',
    'Branch Unlock Dino 14':'dino14',
    'Note Dino Unlock':'dino15',
    'World Key - Jurassic Marsh':'dino16',
    'Primalsunflower Unlock':'dino17',
    'dino18':'dino18',
    'dino19':'dino19',
    'Dangerroom Dino Unlock':'dino20',
    'dino21':'dino21',
    'dino22':'dino22',
    'Primalpotatomine Unlock':'dino23',
    'Branch Unlock Dino 24':'dino24',
    'dino25':'dino25',
    'dino26':'dino26',
    'dino27':'dino27',
    'dino28':'dino28',
    'Branch Unlock Dino 29':'dino29',
    'dino30':'dino30',
    'dino31':'dino31',
    'Worldtrophy Dino Unlock':'dino32',
    'Branch Unlock Dino 33':'dino33',
    'dino34':'dino34',
    'dino35':'dino35',
    'Dangerroom Dino2 Unlock':'dino36',
    'Branch Unlock Dino 37':'dino37',
    'dino38':'dino38',
    'dino39':'dino39',
    'dino40':'dino40',
    'Branch Unlock Dino 41':'dino41',
    'dino42':'dino42',
    'dino_dangerroom2':'dino_dangerroom2',
    'modern_zomboss_01_egypt':'modern_zomboss_01_egypt',
    'Moonflower Unlock':'modern1',
    'modern2':'modern2',
    'modern3':'modern3',
    'Nightshade Unlock':'modern4',
    'modern5':'modern5',
    'Branch Unlock Modern 6':'modern6',
    'Branch Unlock Modern 7':'modern7',
    'modern8':'modern8',
    'modern9':'modern9',
    'Shadowshroom Unlock':'modern10',
    'modern11':'modern11',
    'Branch Unlock Modern 12':'modern12',
    'modern13':'modern13',
    'Branch Unlock Modern 14':'modern14',
    'Note Modern Unlock':'modern15',
    'World Key - Modern Day':'modern16',
    'Dusklobber Unlock':'modern17',
    'modern18':'modern18',
    'modern19':'modern19',
    'Dangerroom Modern Unlock':'modern20',
    'modern21':'modern21',
    'modern22':'modern22',
    'Grimrose Unlock':'modern23',
    'modern24':'modern24',
    'Branch Unlock Modern 25':'modern25',
    'modern26':'modern26',
    'modern27':'modern27',
    'modern28':'modern28',
    'Branch Unlock Modern 29':'modern29',
    'modern30':'modern30',
    'modern31':'modern31',
    'modern35':'modern35',
    'Branch Unlock Modern 36':'modern36',
    'modern37':'modern37',
    'modern38':'modern38',
    'Branch Unlock Modern 39':'modern39',
    'Dangerroom Modern2 Unlock':'modern40',
    'modern41':'modern41',
    'modern42':'modern42',
    'Branch Unlock Modern 43':'modern43',
    'modern44':'modern44',
    'modern_dangerroom':'modern_dangerroom',
    'modern_dangerroom2':'modern_dangerroom2',
    'modern_zomboss_02_pirate':'modern_zomboss_02_pirate',
    'modern_zomboss_03_cowboy':'modern_zomboss_03_cowboy',
    'modern_zomboss_04_future':'modern_zomboss_04_future',
    'modern_zomboss_05_dark':'modern_zomboss_05_dark',
    'modern_zomboss_06_beach':'modern_zomboss_06_beach',
    'Skyshooter Unlock':'sky1',
    'sky2':'sky2',
    'Upgrade Sky Shield Unlock':'sky3',
    'sky4':'sky4',
    'sky5':'sky5',
    'Pineapple Unlock':'sky6',
    'sky7':'sky7',
    'Moonbean Unlock':'sky8',
    'sky9':'sky9',
    'sky10':'sky10',
    'Anthurium Unlock':'sky11',
    'sky12':'sky12',
    'sky13':'sky13',
    'sky14':'sky14',
    'sky15':'sky15',
    'World Key - Sky City':'sky16',
    'aloe0':'aloe0.JSON',
    'aloe3':'aloe3.JSON',
    'appease1_0':'appease1_0',
    'appease1_2':'appease1_2',
    'appease1_4':'appease1_4',
    'Pvine Unlock':'appease1_6',
    'appease2_1':'appease2_1',
    'appease2_3':'appease2_3',
    'Megagatling Unlock':'appease2_5',
    'atombomb0':'atombomb0',
    'atombomb2':'atombomb2',
    'atombomb4':'atombomb4',
    'bank_theft1':'bank_theft1',
    'bank_theft3':'bank_theft3',
    'bank_theft5':'bank_theft5',
    'bloominghearts0':'bloominghearts0',
    'bloominghearts2':'bloominghearts2',
    'bloominghearts4':'bloominghearts4',
    'buttercup0':'buttercup0',
    'buttercup2':'buttercup2',
    'buttercup4':'buttercup4',
    'conceal0':'conceal0',
    'conceal2':'conceal2',
    'conceal4':'conceal4',
    'conceal6':'conceal6',
    'conceal8':'conceal8',
    'conceal10':'conceal10',
    'doomshroom0':'doomshroom0',
    'doomshroom2':'doomshroom2',
    'doomshroom4':'doomshroom4',
    'electriccurrant0':'electriccurrant0',
    'electriccurrant2':'electriccurrant2',
    'electriccurrant4':'electriccurrant4',
    'enlighten0':'enlighten0',
    'enlighten2':'enlighten2',
    'enlighten4':'enlighten4',
    'enlighten6':'enlighten6',
    'ghostpepper0':'ghostpepper0',
    'ghostpepper2':'ghostpepper2',
    'gloomshroom0':'gloomshroom0',
    'gloomshroom2':'gloomshroom2',
    'gloomshroom4':'gloomshroom4',
    'gloomshroom6':'gloomshroom6',
    'goldbloom0':'goldbloom0',
    'goldbloom2':'goldbloom2',
    'hotdate1':'hotdate1',
    'Hotdate Unlock':'hotdate3',
    'icebloom0':'icebloom0',
    'icebloom2':'icebloom2',
    'icebloom4':'icebloom4',
    'iceshroom0':'iceshroom0',
    'iceshroom2':'iceshroom2',
    'iceshroom4':'iceshroom4',
    'meteorflower0':'meteorflower0',
    'meteorflower2':'meteorflower2',
    'parsnip0':'parsnip0',
    'parsnip2':'parsnip2',
    'parsnip4':'parsnip4',
    'plantern0':'plantern0',
    'plantern2':'plantern2',
    'plantern4':'plantern4',
    'reinforce0':'reinforce0',
    'reinforce2':'reinforce2',
    'reinforce4':'reinforce4',
    'reinforce6':'reinforce6',
    'reinforce8':'reinforce8',
    'reinforce10':'reinforce10',
    'sapfling0':'sapfling0',
    'sapfling2':'sapfling2',
    'sapfling4':'sapfling4',
    'sapfling6':'sapfling6',
    'seashooter0':'seashooter0',
    'seashooter2':'seashooter2',
    'shootingstarfruit1':'shootingstarfruit1',
    'shootingstarfruit2':'shootingstarfruit2',
    'shootingstarfruit3':'shootingstarfruit3',
    'solartomato0':'solartomato0',
    'solartomato2':'solartomato2',
    'solartomato4':'solartomato4',
    'squash0':'squash0',
    'squash2':'squash2',
    'strawburst0':'strawburst0',
    'strawburst2':'strawburst2',
    'strawburst4':'strawburst4',
    'strawburst6':'strawburst6',
    'sweetpotato0':'sweetpotato0',
    'sweetpotato2':'sweetpotato2',
    'sweetpotato4':'sweetpotato4',
    'umbrellaleaf0':'umbrellaleaf0',
    'umbrellaleaf2':'umbrellaleaf2',
    'umbrellaleaf4':'umbrellaleaf4',
    'umbrellaleaf6':'umbrellaleaf6',
    'umbrellaleaf8':'umbrellaleaf8',
    'umbrellaleaf10':'umbrellaleaf10',
    'vamporcini0':'vamporcini0',
    'vamporcini2':'vamporcini2',
  };

  // Simple region lookup for Modern Day check
  function getRegion(locName){
    const md_prefixes=['modern_zomboss','modern_dangerroom','modern','Moonflower','Nightshade',
      'Shadowshroom','Dusklobber','Grimrose','Branch Unlock Modern','Dangerroom Modern',
      'Note Modern','World Key - Modern','Worldtrophy Modern'];
    if(md_prefixes.some(p=>locName.startsWith(p)||locName===p)) return 'Modern Day';
    return null;
  }

  const VICTORY_LOCS = [
    'random_zomboss_egypt',
    'random_zomboss_pirate',
    'random_zomboss_cowboy',
    'random_zomboss_future',
    'random_zomboss_dark',
    'random_beach',
    'iceage_dangerroom',
    'lostcity_dangerroom',
    'kongfu_dangerroom',
    'eighties_dangerroom',
    'dino_dangerroom',
  ];

  // ── State ─────────────────────────────────────────────────────────────────
  let cfg   = { server:'localhost:38281', slot:'', password:'' };
  let st    = { checked:[], lastIdx:0, zombossesRequired:7, receivedKeys:[], receivedItems:[] };

  const lsCfg  = () => { try { Object.assign(cfg, JSON.parse(localStorage.getItem(CFG_KEY)||'{}')); } catch(e){} };
  const svCfg  = () => localStorage.setItem(CFG_KEY, JSON.stringify(cfg));
  const lsSt   = () => { try { Object.assign(st,  JSON.parse(localStorage.getItem(STATE_KEY)||'{}')); } catch(e){} };
  const svSt   = () => localStorage.setItem(STATE_KEY, JSON.stringify(st));

  // ── Save data access ──────────────────────────────────────────────────────
  function readSave() {
    try { const r=localStorage.getItem(SAVE_KEY); if(!r) return null; const a=JSON.parse(r); return Array.isArray(a)?a:[a]; } catch(e){return null;}
  }
  function writeSave(arr) { localStorage.setItem(SAVE_KEY, JSON.stringify(arr)); }

  // Returns true if the player has completed the tutorial (forceLevel is past tutorials)
  function isTutorialComplete() {
    const arr=readSave(); if(!arr) return false;
    const p=arr[0]; if(!p) return false;
    const fl=p.forceLevel||'';
    // Still in tutorial if forceLevel is tutorial1-4
    return !['tutorial1','tutorial2','tutorial3','tutorial4'].includes(fl);
  }

  // Lock the 4 tutorial-forced plants and re-apply only what AP has sent
  // Call this after tutorial completes and whenever items arrive
  // Rebuild _AP_grantedPlantIds from st.receivedItems and re-apply all
  // received plant unlocks. Called on connect, item receipt, and every poll.
  // The BASEUNLOCKLIST interceptor handles blocking tutorial plants at source.
  function enforcePlantLocks() {
    if(!isTutorialComplete()) return;
    if(!st.receivedItems || !st.receivedItems.length) return;

    // Rebuild the granted set from received items
    if(!window._AP_grantedPlantIds) window._AP_grantedPlantIds = new Set();
    st.receivedItems.forEach(name => {
      const pid = ITEM_PLANT[name];
      if(pid !== undefined) window._AP_grantedPlantIds.add(pid);
    });

    // Re-apply all granted plants (idempotent — game checks progress before setting)
    if(window._AP_AllPlayerProperties) {
      st.receivedItems.forEach(name => {
        const pid = ITEM_PLANT[name];
        if(pid !== undefined) {
          try { window._AP_AllPlayerProperties.unlockPlant(pid); } catch(e) {}
        }
      });
      try { window._AP_AllPlayerProperties.savePP(); } catch(e) {}
    }
  }

  // forceLevel order for tutorial progression
  const TUTORIAL_ORDER = ['tutorial1','tutorial2','tutorial3','tutorial4','egypt1'];

  function isTutorialDone(tutorialId) {
    // tutorial N is done if forceLevel has advanced past it
    const arr=readSave(); if(!arr) return false;
    const p=arr[0]; if(!p) return false;
    const forceLevel = p.forceLevel || '';
    const myIdx = TUTORIAL_ORDER.indexOf(tutorialId);
    if(myIdx < 0) return false;
    // Done if forceLevel is a later tutorial, egypt1, or empty (already on worldmap)
    if(forceLevel === '') return true;  // past all tutorials
    const forceLevelIdx = TUTORIAL_ORDER.indexOf(forceLevel);
    if(forceLevelIdx < 0) return true;  // some other world level = past tutorials
    return forceLevelIdx > myIdx;
  }

  function isFinished(levelId) {
    if(TUTORIAL_ORDER.includes(levelId)) return isTutorialDone(levelId);
    const arr=readSave(); if(!arr) return false;
    const p=arr[0]; if(!p||!p.levelProps) return false;
    // progress=3 (unlocked_willbeFinished) is set immediately on level win by victory()
    // progress=4 (finished) is set later by worldmap node animation - we don't want to wait
    const e=p.levelProps[levelId]; return e && (e.progress||0)>=3;
  }

  function unlockPlant(plantId) {
    // Register this plant as AP-granted so the BASEUNLOCKLIST interceptor
    // allows it through when the game calls unlockPlant internally
    if(!window._AP_grantedPlantIds) window._AP_grantedPlantIds = new Set();
    window._AP_grantedPlantIds.add(plantId);

    // Prefer live in-memory API (instant, no reload required)
    if(window._AP_AllPlayerProperties) {
      try {
        window._AP_AllPlayerProperties.unlockPlant(plantId);
        window._AP_AllPlayerProperties.savePP();
        return;
      } catch(e) { /* fall through to localStorage method */ }
    }
    // Fallback: write to localStorage (picked up on next game load)
    const arr=readSave(); if(!arr) return;
    const p=arr[0]; if(!p) return;
    if(!p.plantProps) p.plantProps={};
    const cn=ID_TO_CN[plantId]; if(!cn) return;
    const cur=p.plantProps[cn];
    if(!cur||(cur.progress||0)<1) p.plantProps[cn]={progress:1,medal:false,tutorialLevel:0,boost:0,costume:-1,costumes:[]};
    writeSave(arr);
  }

  function unlockWorld(worldId) {
    // Prefer live in-memory API
    if(window._AP_AllPlayerProperties) {
      try {
        window._AP_AllPlayerProperties.unlockWorld(worldId);
        window._AP_AllPlayerProperties.savePP();
        return;
      } catch(e) { /* fall through */ }
    }
    // Fallback: localStorage
    const arr=readSave(); if(!arr) return;
    const p=arr[0]; if(!p) return;
    if(!p.worldProps) p.worldProps={};
    if(!p.worldProps[worldId]) p.worldProps[worldId]={};
    p.worldProps[worldId].unlocked=true;
    writeSave(arr);
  }

  // ── WebSocket / AP Protocol ───────────────────────────────────────────────
  let ws=null, conn=false, rtimer=null, rdelay=5000;
  let locIds={}, itemNames={};

  function connect() {
    if(!cfg.slot){setStatus('Enter slot name','#fa0');return;}
    if(ws){try{ws.onclose=null;ws.close();}catch(e){}ws=null;}
    setStatus('Connecting…','#fa0');
    try {
      ws=new WebSocket(`ws://${cfg.server}`);
      ws.onmessage=e=>{try{JSON.parse(e.data).forEach(onPkt);}catch(ex){}};
      ws.onclose=()=>{
        conn=false;ws=null;setStatus('Disconnected','#f44');
        rtimer=setTimeout(()=>{rdelay=Math.min(rdelay*1.5,30000);connect();},rdelay);
      };
      ws.onerror=()=>{};
    } catch(e) { setStatus('Connection failed: '+e.message,'#f44'); }
  }

  function send(pkts){if(ws&&ws.readyState===1)ws.send(JSON.stringify(pkts));}

  function onPkt(pkt) {
    switch(pkt.cmd){
      case 'RoomInfo':
        rdelay=5000;
        send([{cmd:'GetDataPackage',games:[GAME_NAME]}]);
        send([{cmd:'Connect',game:GAME_NAME,name:cfg.slot,password:cfg.password||'',
               version:{...AP_VER,class:'Version'},tags:['AP'],items_handling:0b111,
               uuid:'pvz2ge_'+cfg.slot,slot_data:true}]);
        break;
      case 'Connected':
        conn=true;setStatus('✓ '+cfg.slot,'#4f4');
        if(pkt.slot_data && pkt.slot_data.zombosses_required !== undefined){
          st.zombossesRequired = pkt.slot_data.zombosses_required;
          svSt();
        }
        const ids=st.checked.map(n=>locIds[n]).filter(Boolean);
        if(ids.length) send([{cmd:'LocationChecks',locations:ids}]);
        send([{cmd:'Sync'}]);
        break;
      case 'ConnectionRefused':
        setStatus('Refused: '+(pkt.errors||[]).join(', '),'#f44');break;
      case 'ReceivedItems':
        (pkt.items||[]).forEach((item,i)=>{
          const gi=(pkt.index||0)+i;
          if(gi<st.lastIdx) return;
          const name=itemNames[item.item];
          if(name){
            // Track all received items for enforcePlantLocks replay
            if(!st.receivedItems) st.receivedItems=[];
            if(!st.receivedItems.includes(name)) st.receivedItems.push(name);
            applyItem(name);
          }
          st.lastIdx=gi+1;
        });
        svSt();break;
      case 'DataPackage':
        const gd=pkt.data&&pkt.data.games&&pkt.data.games[GAME_NAME];
        if(gd){
          locIds=gd.location_name_to_id||{};
          itemNames={};
          for(const[n,id] of Object.entries(gd.item_name_to_id||{})) itemNames[id]=n;
        }
        break;
    }
  }

  function applyItem(name) {
    if(WORLD_KEY_MAP[name]){
      WORLD_KEY_MAP[name].forEach(w=>unlockWorld(w));
      toast('🔑 '+name,'#fa0');
      // Track received keys for Modern Day unlock check
      if(!st.receivedKeys) st.receivedKeys=[];
      if(!st.receivedKeys.includes(name)) st.receivedKeys.push(name);
      svSt();
      return;
    }
    const pid=ITEM_PLANT[name];
    if(pid!==undefined){unlockPlant(pid);toast('🌱 '+name,'#4f4');return;}
    toast('📦 '+name,'#4af');
  }

  // ── Location polling (every 2s) ───────────────────────────────────────────
  function canAccessModernDay(){
    if(!st.receivedKeys || !st.receivedKeys.includes('Modern Day Key')) return false;
    const beaten = VICTORY_LOCS.filter(l=>st.checked.includes(l)).length;
    return beaten >= (st.zombossesRequired||7);
  }

  function pollChecks(){
    // Lock tutorial-forced plants and restore only AP-granted ones
    enforcePlantLocks();
    for(const[loc,levelId] of Object.entries(LOC_LEVELS)){
      if(st.checked.includes(loc)) continue;
      if(isFinished(levelId)) fireCheck(loc);
    }
  }

  function fireCheck(loc){
    if(st.checked.includes(loc)) return;
    // Check Modern Day accessibility before firing any Modern Day check
    const md_locs = Object.entries(LOC_LEVELS)
      .filter(([n,l])=>{ const r=getRegion(n); return r==='Modern Day'; })
      .map(([n])=>n);
    if(md_locs.includes(loc) && !canAccessModernDay()) return;
    st.checked.push(loc);svSt();
    const id=locIds[loc];
    if(id&&conn) send([{cmd:'LocationChecks',locations:[id]}]);
    // Victory: Modern Day zomboss checked
    if(loc==='modern_zomboss_01_egypt')
      send([{cmd:'StatusUpdate',status:30}]);
  }

  // ── UI ────────────────────────────────────────────────────────────────────
  let statusEl=null, logEl=null, panel=null, logs=[];

  function buildUI(){
    const s=document.createElement('style');
    s.textContent=`
      #ap-btn{position:fixed;top:8px;left:8px;z-index:99999;background:#111827;
        color:#6ee7b7;border:1px solid #059669;border-radius:6px;padding:4px 12px;
        font:bold 13px monospace;cursor:pointer;user-select:none;letter-spacing:.05em}
      #ap-btn:hover{background:#1f2937}
      #ap-panel{position:fixed;top:38px;left:8px;z-index:99999;background:#0f172a;
        color:#e2e8f0;border:1px solid #059669;border-radius:10px;padding:16px;
        font:12px monospace;width:280px;display:none;box-shadow:0 8px 32px #000c}
      #ap-panel label{display:block;margin-top:8px;color:#94a3b8;font-size:11px;text-transform:uppercase;letter-spacing:.08em}
      #ap-panel input{width:100%;box-sizing:border-box;background:#1e293b;color:#e2e8f0;
        border:1px solid #334155;border-radius:5px;padding:4px 8px;font:12px monospace;
        margin-top:3px;outline:none}
      #ap-panel input:focus{border-color:#059669}
      #ap-panel button{background:#065f46;color:#6ee7b7;border:1px solid #059669;
        border-radius:5px;padding:5px 14px;margin-top:10px;cursor:pointer;font:12px monospace}
      #ap-panel button:hover{background:#047857}
      #ap-disc{background:#1c1917!important;color:#f87171!important;border-color:#dc2626!important;margin-left:6px}
      #ap-disc:hover{background:#292524!important}
      #ap-status{margin-top:10px;font-weight:bold;font-size:12px}
      #ap-log{margin-top:8px;max-height:100px;overflow-y:auto;background:#020617;
        border-radius:5px;padding:6px;font-size:10px;color:#64748b;line-height:1.5}
      #ap-toast{position:fixed;bottom:72px;left:50%;transform:translateX(-50%);
        z-index:99999;background:#0f172a;color:#e2e8f0;border:1px solid #059669;
        border-radius:8px;padding:8px 20px;font:13px monospace;
        opacity:0;transition:opacity .3s;pointer-events:none;white-space:nowrap}
    `;
    document.head.appendChild(s);

    const btn=document.createElement('div');
    btn.id='ap-btn';btn.textContent='AP';
    btn.onclick=()=>{panel.style.display=panel.style.display==='none'?'block':'none';};
    document.body.appendChild(btn);

    panel=document.createElement('div');panel.id='ap-panel';
    panel.innerHTML=`<div style="font-weight:bold;font-size:13px;color:#6ee7b7;margin-bottom:4px">🏝 Archipelago</div>
      <label>Server<br><input id=ap-srv placeholder="localhost:38281"></label>
      <label>Slot Name<br><input id=ap-slt placeholder="Player"></label>
      <label>Password<br><input id=ap-pwd type=password placeholder="(optional)"></label>
      <button id=ap-go>Connect</button><button id=ap-disc>Disconnect</button>
      <div id=ap-status style="color:#64748b">Not connected</div>
      <div id=ap-log></div>`;
    document.body.appendChild(panel);

    statusEl=document.getElementById('ap-status');
    logEl=document.getElementById('ap-log');
    document.getElementById('ap-srv').value=cfg.server||'';
    document.getElementById('ap-slt').value=cfg.slot||'';
    document.getElementById('ap-pwd').value=cfg.password||'';

    document.getElementById('ap-go').onclick=()=>{
      cfg.server=document.getElementById('ap-srv').value.trim()||'localhost:38281';
      cfg.slot=document.getElementById('ap-slt').value.trim();
      cfg.password=document.getElementById('ap-pwd').value;
      svCfg();rdelay=5000;connect();
    };
    document.getElementById('ap-disc').onclick=()=>{
      clearTimeout(rtimer);
      if(ws){ws.onclose=null;ws.close();ws=null;}
      conn=false;setStatus('Disconnected','#f44');
    };

    const t=document.createElement('div');t.id='ap-toast';
    document.body.appendChild(t);
  }

  function setStatus(msg,color){
    if(statusEl){statusEl.textContent=msg;statusEl.style.color=color||'#64748b';}
  }

  let toastTimer=null;
  function toast(msg,color){
    const el=document.getElementById('ap-toast');if(!el)return;
    el.textContent=msg;el.style.color=color||'#e2e8f0';el.style.opacity='1';
    clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.style.opacity='0',3500);
    logs.unshift(msg);if(logs.length>40)logs.pop();
    if(logEl)logEl.innerHTML=logs.map(m=>`<div>${m}</div>`).join('');
  }

  // ── Init ──────────────────────────────────────────────────────────────────
  function init(){
    lsCfg();lsSt();
    buildUI();
    setInterval(pollChecks,2000);
    // Never auto-connect — user must click Connect manually each session
  }

  document.readyState==='loading'
    ? document.addEventListener('DOMContentLoaded',init)
    : setTimeout(init,100);
})();
""".strip()


# ── Build steps ───────────────────────────────────────────────────────────────

STEPS = [
    ("Checking requirements",        "check_requirements"),
    ("Cloning Electron wrapper",      "clone_electron"),
    ("Cloning game source",           "clone_game"),
    ("Patching tmpPatch.js",          "patch_tmpatch"),
    ("Installing Node dependencies",  "npm_install"),
    ("Building executable",           "npm_build"),
    ("Copying output",                "copy_output"),
]


def run_cmd(cmd, cwd, log):
    """Run a shell command, streaming output to log callback. Returns returncode."""
    proc = subprocess.Popen(
        cmd, cwd=cwd, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1
    )
    for line in proc.stdout:
        log(line.rstrip())
    proc.wait()
    return proc.returncode


def find_tool(name):
    return shutil.which(name)


def build(build_dir, log, done_cb, error_cb):
    """Full build sequence. Runs in a thread."""

    electron_dir = os.path.join(build_dir, "PVZGE-Electron")
    docs_dir     = os.path.join(electron_dir, "pvzge_web", "docs")
    release_dir  = os.path.join(electron_dir, "release")

    def step(msg):
        log(f"\n{'─'*50}")
        log(f"  {msg}")
        log(f"{'─'*50}")

    # ── 1. Check requirements ─────────────────────────────────────────────────
    step("Checking requirements")
    missing = []
    for tool in ("git", "node", "npm"):
        if not find_tool(tool):
            missing.append(tool)
    if missing:
        error_cb(
            f"Missing required tools: {', '.join(missing)}\n\n"
            "Please install:\n"
            + ("  • Git:    https://git-scm.com/download/win\n" if "git" in missing else "")
            + ("  • Node.js: https://nodejs.org (LTS version)\n" if "node" in missing else "")
            + "If this message continues to appear, run powershell as administrator and run\n"
            + "Set-ExecutionPolicy RemoteSigned -Scope CurrentUser\n"
            + "Then run archipelago as an administrator."
        )
        return

    node_ver = subprocess.check_output("node --version", shell=True, text=True).strip()
    npm_ver  = subprocess.check_output("npm --version",  shell=True, text=True).strip()
    git_ver  = subprocess.check_output("git --version",  shell=True, text=True).strip()
    log(f"  node {node_ver}  |  npm {npm_ver}  |  {git_ver}")

    # ── 2. Clone Electron wrapper ─────────────────────────────────────────────
    step("Cloning Electron wrapper")
    os.makedirs(build_dir, exist_ok=True)

    if os.path.isdir(electron_dir):
        log("  Already exists — pulling latest...")
        rc = run_cmd("git pull", electron_dir, log)
    else:
        rc = run_cmd(
            "git clone --depth=1 https://github.com/Twig6943/PVZGE-Electron.git",
            build_dir, log
        )
    if rc != 0:
        error_cb("Failed to clone Electron wrapper. Check your internet connection.")
        return

    # ── 3. Clone game source ──────────────────────────────────────────────────
    # Always clone pvzge_web directly from master — never use the submodule pin
    # in the Electron repo, which may point to an older version.
    step("Cloning game source (pvzge_web master) — this may take a few minutes (~300MB)")
    pvzge_web_dir = os.path.join(electron_dir, "pvzge_web")

    if os.path.isdir(os.path.join(pvzge_web_dir, "docs")):
        log("  Already exists — fetching latest from master...")
        rc = run_cmd("git fetch origin master --depth=1", pvzge_web_dir, log)
        if rc == 0:
            rc = run_cmd("git reset --hard origin/master", pvzge_web_dir, log)
        if rc != 0:
            log("  Warning: could not update pvzge_web, using existing copy")
            rc = 0  # non-fatal, proceed with what we have
    else:
        # Detach any existing submodule tracking and clone fresh
        os.makedirs(pvzge_web_dir, exist_ok=True)
        rc = run_cmd(
            "git clone --depth=1 --branch master "
            "https://github.com/Gzh0821/pvzge_web.git .",
            pvzge_web_dir, log
        )
    if rc != 0:
        error_cb("Failed to clone game source. Check your internet connection.")
        return

    if not os.path.isdir(docs_dir):
        error_cb(f"Expected docs/ folder not found at:\n{docs_dir}\n\nClone may be incomplete.")
        return

    # Log the actual game version we got
    ver_result = run_cmd("git log --oneline -1", pvzge_web_dir, log)

    # ── 4. Patch tmpPatch.js ──────────────────────────────────────────────────
    step("Patching tmpPatch.js with Archipelago client")
    tmppatch_path = os.path.join(docs_dir, "tmpPatch.js")

    bak_path = tmppatch_path + ".original"
    if not os.path.exists(bak_path) and os.path.exists(tmppatch_path):
        shutil.copy2(tmppatch_path, bak_path)
        log(f"  Backed up original to tmpPatch.js.original")

    with open(tmppatch_path, "w", encoding="utf-8") as f:
        f.write(TMPPATCH_CONTENT)
    log(f"  Written: {tmppatch_path}")
    log(f"  Size: {len(TMPPATCH_CONTENT):,} bytes")

    # Patch main.js to enable devtools (F12) so the AP overlay errors are visible
    main_js_path = os.path.join(electron_dir, "main.js")
    if os.path.isfile(main_js_path):
        with open(main_js_path, "r", encoding="utf-8") as f:
            main_js = f.read()
        main_js = main_js.replace("devTools: false", "devTools: true")
        f12_shortcut = (
            "globalShortcut.register('F12', () => {\n"
            "    win.webContents.toggleDevTools();\n"
            "  });\n\n"
            "  globalShortcut.register('F11', () => {"
        )
        if "F12" not in main_js:
            main_js = main_js.replace(
                "globalShortcut.register('F11', () => {",
                f12_shortcut
            )
        with open(main_js_path, "w", encoding="utf-8") as f:
            f.write(main_js)
        log("  Enabled F12 devtools in main.js")


    # ── 5. npm install ────────────────────────────────────────────────────────
    step("Installing Node.js dependencies (electron, electron-builder)")
    log("  This downloads ~200MB of packages the first time...")
    rc = run_cmd("npm install", electron_dir, log)
    if rc != 0:
        error_cb("npm install failed. See log above for details.")
        return

    # ── 6. Build ──────────────────────────────────────────────────────────────
    import platform as _platform
    plat = _platform.system()
    if plat == "Windows":
        build_cmd = "npm run build:win -- --publish=never"
        output_exts = [".exe"]
        output_name = "PvZ Gardendless AP.exe"
    elif plat == "Darwin":
        build_cmd = "npm run build:mac -- --publish=never"
        output_exts = [".dmg", ".app"]
        output_name = "PvZ Gardendless AP.dmg"
    else:  # Linux
        build_cmd = "npm run build:linux -- --publish=never"
        output_exts = [".AppImage", ".appimage"]
        output_name = "PvZ Gardendless AP.AppImage"

    step(f"Building {plat} application (this takes 2-5 minutes)")
    rc = run_cmd(build_cmd, electron_dir, log)
    if rc != 0:
        error_cb("Build failed. See log above for details.")
        return

    # ── 7. Find and copy output ───────────────────────────────────────────────
    step("Locating output file")
    built_path = None
    for root, dirs, files in os.walk(release_dir):
        for f in files:
            if any(f.endswith(ext) for ext in output_exts):
                built_path = os.path.join(root, f)
                break
        if built_path:
            break

    if not built_path:
        error_cb(f"Build succeeded but no output found in:\n{release_dir}\n\nExpected: {output_exts}")
        return

    final_path = os.path.join(build_dir, output_name)
    shutil.copy2(built_path, final_path)
    # Make executable on Linux/Mac
    if plat != "Windows":
        os.chmod(final_path, 0o755)
    log(f"\n  Output: {final_path}")
    log(f"  Size:   {os.path.getsize(final_path)/1024/1024:.0f} MB")

    done_cb(final_path)


# ── GUI ───────────────────────────────────────────────────────────────────────

class BuilderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PvZ2 Gardendless — Archipelago Builder")
        self.root.resizable(True, True)
        self.root.minsize(640, 480)
        self._configure_style()
        self._build_ui()
        self.q = queue.Queue()
        self.root.after(100, self._poll_queue)

    def _configure_style(self):
        self.root.configure(bg="#0f172a")

    def _build_ui(self):
        BG   = "#0f172a"
        BG2  = "#1e293b"
        ACC  = "#059669"
        ACCL = "#6ee7b7"
        TEXT = "#e2e8f0"
        MUTE = "#64748b"
        FONT = ("Consolas", 10)

        # Title
        title_frame = tk.Frame(self.root, bg=BG, pady=16)
        title_frame.pack(fill="x", padx=24)
        tk.Label(title_frame, text="🌻  PvZ2 Gardendless", font=("Consolas", 18, "bold"),
                 bg=BG, fg=ACCL).pack(anchor="w")
        tk.Label(title_frame, text="Archipelago Mod Builder",
                 font=("Consolas", 11), bg=BG, fg=MUTE).pack(anchor="w")

        # Divider
        tk.Frame(self.root, bg=ACC, height=1).pack(fill="x", padx=24)

        # Build folder picker
        dir_frame = tk.Frame(self.root, bg=BG, pady=12)
        dir_frame.pack(fill="x", padx=24)
        tk.Label(dir_frame, text="BUILD FOLDER", font=("Consolas", 9, "bold"),
                 bg=BG, fg=MUTE).pack(anchor="w")

        row = tk.Frame(dir_frame, bg=BG)
        row.pack(fill="x", pady=(4, 0))

        self.dir_var = tk.StringVar(value=os.path.normpath(os.path.expanduser("~/pvzge_ap_build")))
        self.dir_entry = tk.Entry(row, textvariable=self.dir_var, font=FONT,
                                  bg=BG2, fg=TEXT, insertbackground=TEXT,
                                  relief="flat", bd=6)
        self.dir_entry.pack(side="left", fill="x", expand=True)

        tk.Button(row, text="Browse…", font=FONT, bg=BG2, fg=ACCL,
                  activebackground="#334155", activeforeground=ACCL,
                  relief="flat", bd=0, padx=10, pady=4,
                  cursor="hand2",
                  command=self._browse).pack(side="left", padx=(6, 0))

        # Info box
        info = tk.Frame(self.root, bg=BG2, padx=12, pady=10)
        info.pack(fill="x", padx=24, pady=(0, 12))
        tk.Label(info,
                 text="The builder will:\n"
                      "  1. Clone the Electron wrapper from GitHub (~5 MB)\n"
                      "  2. Clone the game source from GitHub (~300 MB)\n"
                      "  3. Inject the Archipelago client into the game\n"
                      "  4. Build the game application for your platform via npm\n\n"
                      "Requirements: Git + Node.js (LTS) must be installed.",
                 font=("Consolas", 9), bg=BG2, fg=MUTE, justify="left"
                 ).pack(anchor="w")

        # Build button
        self.build_btn = tk.Button(
            self.root, text="▶  START BUILD", font=("Consolas", 12, "bold"),
            bg=ACC, fg="#022c22", activebackground="#047857", activeforeground="#022c22",
            relief="flat", bd=0, padx=20, pady=10, cursor="hand2",
            command=self._start_build
        )
        self.build_btn.pack(pady=(0, 12))

        # Log area
        log_frame = tk.Frame(self.root, bg=BG, padx=24, pady=0)
        log_frame.pack(fill="both", expand=True)

        tk.Label(log_frame, text="BUILD LOG", font=("Consolas", 9, "bold"),
                 bg=BG, fg=MUTE).pack(anchor="w")

        log_inner = tk.Frame(log_frame, bg="#020617")
        log_inner.pack(fill="both", expand=True, pady=(4, 16))
        scrollbar = tk.Scrollbar(log_inner)
        scrollbar.pack(side="right", fill="y")
        self.log_area = tk.Text(
            log_inner, font=("Consolas", 9), bg="#020617", fg="#94a3b8",
            insertbackground=TEXT, relief="flat", bd=4,
            state="disabled", wrap="word", yscrollcommand=scrollbar.set
        )
        self.log_area.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.log_area.yview)

        # Status bar
        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(self.root, textvariable=self.status_var, font=("Consolas", 9),
                 bg=BG2, fg=MUTE, anchor="w", padx=8, pady=4
                 ).pack(fill="x", side="bottom")

    def _browse(self):
        d = filedialog.askdirectory(title="Choose build folder",
                                    initialdir=self.dir_var.get())
        if d:
            self.dir_var.set(os.path.normpath(d))

    def _log(self, msg):
        self.q.put(("log", msg))

    def _poll_queue(self):
        try:
            while True:
                kind, data = self.q.get_nowait()
                if kind == "log":
                    self.log_area.configure(state="normal")
                    self.log_area.insert("end", data + "\n")
                    self.log_area.see("end")
                    self.log_area.configure(state="disabled")
                elif kind == "status":
                    self.status_var.set(data)
                elif kind == "done":
                    self._on_done(data)
                elif kind == "error":
                    self._on_error(data)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    def _start_build(self):
        build_dir = os.path.normpath(self.dir_var.get().strip())
        if not build_dir:
            self._on_error("Please choose a build folder first.")
            return

        self.build_btn.configure(state="disabled", text="Building…")
        self.log_area.configure(state="normal")
        self.log_area.delete("1.0", "end")
        self.log_area.configure(state="disabled")
        self.status_var.set("Building…")

        def _thread():
            build(
                build_dir,
                log=lambda m: self.q.put(("log", m)),
                done_cb=lambda exe: self.q.put(("done", exe)),
                error_cb=lambda err: self.q.put(("error", err)),
            )

        threading.Thread(target=_thread, daemon=True).start()

    def _on_done(self, exe_path):
        self.build_btn.configure(state="normal", text="▶  BUILD AGAIN")
        self.status_var.set("✓ Build complete!")
        self._log(f"\n{'='*50}")
        self._log("  BUILD COMPLETE!")
        self._log(f"{'='*50}")
        self._log(f"  Your modded game is at:")
        self._log(f"  {exe_path}")
        self._log("")
        self._log("  Launch it, then click the AP button in the")
        self._log("  top-left corner to connect to your server.")

        # Ask to open folder
        folder = os.path.dirname(exe_path)
        import tkinter.messagebox as mb
        if mb.askyesno("Build Complete",
                        f"Build successful!\n\nSaved to:\n{exe_path}\n\nOpen folder?"):
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])

    def _on_error(self, msg):
        self.build_btn.configure(state="normal", text="▶  START BUILD")
        self.status_var.set("✗ Build failed.")
        self._log(f"\n{'!'*50}")
        self._log("  ERROR")
        self._log(f"{'!'*50}")
        for line in msg.splitlines():
            self._log(f"  {line}")
        import tkinter.messagebox as mb
        mb.showerror("Build Failed", msg)


def main():
    root = tk.Tk()
    app = BuilderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
