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

// ── Archipelago Client ────────────────────────────────────────────────────────
(function () {
  'use strict';

  const SAVE_KEY   = 'PvZ2_PlayerProperties';
  const CFG_KEY    = 'ap_pvz2_cfg';
  const STATE_KEY  = 'ap_pvz2_state';
  const GAME_NAME  = 'PvZ2 Gardendless';
  const AP_VER     = { major: 0, minor: 5, build: 0 };

  // World enum IDs (from WorldMapSceneDisplayEnum in game source)
  const W = { egypt:1, pirate:2, cowboy:3, future:4, dark:5, beach:6,
               iceage:7, lostcity:8, epic:9, eighties:10, dino:11, modern:12, kongfu:13 };

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

  // id -> lowercase codename (save key)
  const ID_TO_CN = {};
  for (const [k,v] of Object.entries(P)) ID_TO_CN[v] = k.toLowerCase();

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
  const KEY_GATES = [
    [1,[W.pirate]],[2,[W.cowboy]],[3,[W.future]],[4,[W.dark]],[5,[W.beach]],
    [6,[W.iceage]],[7,[W.lostcity]],[8,[W.eighties,W.kongfu]],[9,[W.dino]],[10,[W.modern]]
  ];

  // Location name -> level IDs (from game source asset config)
  const LOC_LEVELS = {
    'Ancient Egypt Zomboss':['random_zomboss_egypt'],
    'Cabbage-pult Unlock':['egypt1'],'Bloomerang Unlock':['egypt2'],
    'Iceberg Lettuce Unlock':['egypt3'],'Ancient Egypt - Special Portal 1':['egypt_dangerroom'],
    'Ancient Egypt - World Key':['egypt4'],'Ice Weed Unlock':['egypt5'],
    'Grave Buster Unlock':['egypt6'],'Bonk Choy Unlock':['egypt7'],
    'Plant Food Slot Upgrade':['egypt8'],'Repeater Unlock':['egypt9'],
    'Starting Sun Upgrade':['egypt10'],'Twin Sunflower Unlock':['egypt11'],
    'Ancient Egypt - Present 1':['egypt12'],'Ancient Egypt - Present 2':['egypt13'],
    'Ancient Egypt - Present 3':['egypt14'],'Ancient Egypt - Present 4':['egypt15'],
    'Pyramid of Doom':['egypt_dangerroom2'],'Mummy Memory':['egypt_dangerroom_minigame'],
    'Pirate Seas Zomboss':['random_zomboss_pirate'],
    'Kernel-pult Unlock':['pirate1'],'Snap Dragon Unlock':['pirate2'],
    'Spikeweed Unlock':['pirate3'],'Pirate Seas - World Key':['pirate4'],
    'Spring Bean Unlock':['pirate5'],'Coconut Cannon Unlock':['pirate6'],
    'Sun Shovel Upgrade':['pirate7'],'Threepeater Unlock':['pirate8'],
    'Spikerock Unlock':['pirate9'],'Seed Slot Upgrade':['pirate10'],
    'Cherry Bomb Unlock':['pirate11'],
    'Pirate Seas - Present 1':['pirate12'],'Pirate Seas - Present 2':['pirate13'],
    'Pirate Seas - Present 3':['pirate14'],'Pirate Seas - Present 4':['pirate15'],
    "Dead Man's Booty":['pirate_dangerroom'],
    'Wild West Zomboss':['random_zomboss_cowboy'],
    'Split Pea Unlock':['cowboy1'],'Chili Bean Unlock':['cowboy2'],
    'Pea Pod Unlock':['cowboy3'],'Wild West - World Key':['cowboy4'],
    'Lightning Reed Unlock':['cowboy5'],'Sun Shovel Unlock':['cowboy6'],
    'Melon-Pult Unlock':['cowboy7'],'Wall-nut First Aid':['cowboy8'],
    'Tall-nut Unlock':['cowboy9'],'Winter Melon Unlock':['cowboy10'],
    'Wild West - Present 1':['cowboy11'],'Wild West - Present 2':['cowboy12'],
    'Wild West - Present 3':['cowboy13'],'Wild West - Present 4':['cowboy14'],
    'Plant Food Recharge':['cowboy15'],'Big Bad Butte':['cowboy_dangerroom'],
    'Far Future Zomboss':['random_zomboss_future'],
    'Laser Bean Unlock':['future1'],'Blover Unlock':['future2'],
    'Citron Unlock':['future3'],'Far Future - World Key':['future4'],
    'E.M. Peach Unlock':['future5'],'Infi-nut Unlock':['future6'],
    'Magnifying Grass Unlock':['future7'],'Star Fruit Unlock':['future8'],
    'Mower Launch':['future9'],'Tile Turnip Unlock':['future10'],
    'Far Future - Present 1':['future11'],'Far Future - Present 2':['future12'],
    'Far Future - Present 3':['future13'],'Far Future - Present 4':['future14'],
    'Terror from Tomorrow':['future_dangerroom'],
    'Dark Ages Zomboss':['random_zomboss_dark'],
    'Sun-Shroom Unlock':['dark1'],'Puff-Shroom Unlock':['dark2'],
    'Fume-Shroom Unlock':['dark3'],'Dark Ages - Special Portal 1':['dark_dangerroom'],
    'Dark Ages - Special Portal 2':['dark_dangerroom2'],'Sun Bean Unlock':['dark4'],
    'Hypno-Shroom Unlock':['dark5'],'Dark Ages - World Key':['dark6'],
    'Magnet-Shroom Unlock':['dark7'],'Peanut Unlock':['dark8'],
    'Dark Ages - Present 1':['dark9'],'Dark Ages - Present 2':['dark10'],
    'Dark Ages - Present 3':['dark11'],'Dark Ages - Present 4':['dark12'],
    "Arthur's Challenge":['dark_dangerroom_potion'],
    'Big Wave Beach Zomboss':['random_beach'],
    'Lily Pad Unlock':['beach1'],'Tangle Kelp Unlock':['beach2'],
    'Bowling Bulb Unlock':['beach3'],'Chomper Unlock':['beach4'],
    'Big Wave Beach - Special Portal 1':['beach_dangerroom'],
    'Big Wave Beach - World Key':['beach5'],'Guacodile Unlock':['beach6'],
    'Big Wave Beach - Special Portal 2':['beach_dangerroom2'],
    'Banana Launcher Unlock':['beach7'],'Homing Thistle Unlock':['beach8'],
    'Sea-Shroom Unlock':['beach9'],
    'Big Wave Beach - Present 1':['beach10'],'Big Wave Beach - Present 2':['beach11'],
    'Big Wave Beach - Present 3':['beach12'],'Big Wave Beach - Present 4':['beach13'],
    'Big Wave Beach - Present 5':['beach14'],'Big Wave Beach - Present 6':['beach15'],
    'Big Wave Beach - Present 7':['beach16'],'Big Wave Beach - Present 8':['beach17'],
    'Tiki Torch-er':['beach_dangerroom_minigame_egypt'],
    'Wall-nut Bowling':['beach_dangerroom_minigame_pirate'],
    'Frostbite Caves Zomboss':['iceage_dangerroom'],
    'Hot Potato Unlock':['iceage1'],'Pepper-pult Unlock':['iceage2'],
    'Chard Guard Unlock':['iceage3'],
    'Frostbite Caves - Special Portal 1':['iceage_dangerroom'],
    'Hurrikale Unlock':['iceage4'],'Frostbite Caves - World Key':['iceage5'],
    'Stunion Unlock':['iceage6'],
    'Frostbite Caves - Special Portal 2':['iceage_dangerroom2'],
    'Rotobaga Unlock':['iceage7'],'Fire Peashooter Unlock':['iceage8'],
    'Frostbite Caves - Present 1':['iceage9'],'Frostbite Caves - Present 2':['iceage10'],
    'Frostbite Caves - Present 3':['iceage11'],'Frostbite Caves - Present 4':['iceage12'],
    'Frostbite Caves - Present 5':['iceage13'],'Frostbite Caves - Present 6':['iceage14'],
    'Frostbite Caves - Present 7':['iceage15'],'Frostbite Caves - Present 8':['iceage16'],
    'Icebound Battleground':['iceage_dangerroom2'],
    'Lost City Zomboss':['lostcity_dangerroom'],
    'Red Stinger Unlock':['lostcity1'],'A.K.E.E. Unlock':['lostcity2'],
    'Endurian Unlock':['lostcity3'],'Lava Guava Unlock':['lostcity4'],
    'Lost City - World Key':['lostcity5'],'Stallia Unlock':['lostcity6'],
    'Gold Leaf Unlock':['lostcity7'],'Toadstool Unlock':['lostcity8'],
    'Lost City - Present 1':['lostcity9'],'Lost City - Present 2':['lostcity10'],
    'Lost City - Present 3':['lostcity11'],'Lost City - Present 4':['lostcity12'],
    'Lost City - Present 5':['lostcity13'],'Lost City - Present 6':['lostcity14'],
    'Lost City - Present 7':['lostcity15'],'Lost City - Present 8':['lostcity16'],
    'Temple of Bloom':['lostcity_dangerroom'],
    'Kongfu Temple Zomboss 1':['kongfu_dangerroom'],
    'Kongfu Temple Zomboss 2':['kongfu_dangerroom2'],
    'Fire Gourd Unlock':['kongfu1'],'Snow Pea Unlock':['kongfu2'],
    'Kongfu Temple - World Key':['kongfu3'],'Bamboo Shoot Unlock':['kongfu4'],
    'Resistant Radish Unlock':['kongfu5'],'Heavenly Peach Unlock':['kongfu6'],
    'Power Lily Unlock':['kongfu7'],'Lychee Unlock':['kongfu8'],
    'Martial Arts Contest 1':['kongfu9'],'Martial Arts Contest 2':['kongfu10'],
    'Kongfu Temple - Present 1':['kongfu11'],'Kongfu Temple - Present 2':['kongfu12'],
    'Kongfu Temple - Present 3':['kongfu13'],'Kongfu Temple - Present 4':['kongfu14'],
    'Kongfu Temple - Present 5':['kongfu15'],'Kongfu Temple - Present 6':['kongfu16'],
    'Kongfu Temple - Present 7':['kongfu17'],'Kongfu Temple - Present 8':['kongfu18'],
    'Kongfu Temple - Present 9':['kongfu19'],'Kongfu Temple - Present 10':['kongfu20'],
    'Neon Mixtape Tour Zomboss':['eighties_dangerroom'],
    'Phat Beat Unlock':['eighties1'],'Celery Stalker Unlock':['eighties2'],
    'Thyme Unlock':['eighties3'],'Cactus Unlock':['eighties4'],
    'Neon Mixtape Tour - Special Portal 1':['eighties_dangerroom'],
    'Neon Mixtape Tour - World Key':['eighties5'],'Garlic Unlock':['eighties6'],
    'Spore-Shroom Unlock':['eighties7'],'Intensive Carrot Unlock':['eighties8'],
    'Neon Mixtape Tour - Special Portal 2':['eighties_dangerroom2'],
    'Electric Blueberry Unlock':['eighties9'],
    'Neon Mixtape Tour - Present 1':['eighties10'],'Neon Mixtape Tour - Present 2':['eighties11'],
    'Neon Mixtape Tour - Present 3':['eighties12'],'Neon Mixtape Tour - Present 4':['eighties13'],
    'Greatest Hits':['eighties_dangerroom'],
    'Jurassic Marsh Zomboss':['dino_dangerroom'],
    'Primal Peashooter Unlock':['dino1'],'Grapeshot Unlock':['dino2'],
    'Primal Wall-nut Unlock':['dino3'],'Perfume-Shroom Unlock':['dino4'],
    'Jurassic Marsh - World Key':['dino5'],'Primal Sunflower Unlock':['dino6'],
    'Cold Snapdragon Unlock':['dino7'],'Primal Potato Mine Unlock':['dino8'],
    'Jurassic Marsh - Present 1':['dino9'],'Jurassic Marsh - Present 2':['dino10'],
    'Jurassic Marsh - Present 3':['dino11'],'Jurassic Marsh - Present 4':['dino12'],
    'Jurassic Marsh - Present 5':['dino13'],'Jurassic Marsh - Present 6':['dino14'],
    'La Brainza Tar Pits':['dino_dangerroom2'],
    'Modern Day Zomboss':['modern_zomboss_01_egypt'],
    'Escape Root Unlock':['modern1'],'Modern Day - Special Portal 1':['modern_dangerroom'],
    'Modern Day - Special Portal 2':['modern_dangerroom2'],
    'Moonflower Unlock':['modern2'],'Nightshade Unlock':['modern3'],
    'Shadow-shroom Unlock':['modern4'],'Shrinking Violet Unlock':['modern5'],
    'Modern Day - World Key':['modern6'],'Dusk Lobber Unlock':['modern7'],
    'Grimrose Unlock':['modern8'],
    'Modern Day - Present 1':['modern9'],'Modern Day - Present 2':['modern10'],
    'Modern Day - Present 3':['modern11'],'Modern Day - Present 4':['modern12'],
    'Modern Day - Present 5':['modern13'],'Modern Day - Present 6':['modern14'],
    'Highway to the Danger Room':['modern_dangerroom'],
  };

  const VICTORY_LOCS = [
    'Ancient Egypt Zomboss','Pirate Seas Zomboss','Wild West Zomboss',
    'Far Future Zomboss','Dark Ages Zomboss','Big Wave Beach Zomboss',
    'Frostbite Caves Zomboss','Lost City Zomboss','Kongfu Temple Zomboss 1',
    'Neon Mixtape Tour Zomboss','Jurassic Marsh Zomboss','Modern Day Zomboss'
  ];

  // ── State ─────────────────────────────────────────────────────────────────
  let cfg   = { server:'localhost:38281', slot:'', password:'' };
  let st    = { checked:[], lastIdx:0, keys:0 };

  const lsCfg  = () => { try { Object.assign(cfg, JSON.parse(localStorage.getItem(CFG_KEY)||'{}')); } catch(e){} };
  const svCfg  = () => localStorage.setItem(CFG_KEY, JSON.stringify(cfg));
  const lsSt   = () => { try { Object.assign(st,  JSON.parse(localStorage.getItem(STATE_KEY)||'{}')); } catch(e){} };
  const svSt   = () => localStorage.setItem(STATE_KEY, JSON.stringify(st));

  // ── Save data access ──────────────────────────────────────────────────────
  function readSave() {
    try { const r=localStorage.getItem(SAVE_KEY); if(!r) return null; const a=JSON.parse(r); return Array.isArray(a)?a:[a]; } catch(e){return null;}
  }
  function writeSave(arr) { localStorage.setItem(SAVE_KEY, JSON.stringify(arr)); }

  function isFinished(levelId) {
    const arr=readSave(); if(!arr) return false;
    const p=arr[0]; if(!p||!p.levelProps) return false;
    const e=p.levelProps[levelId]; return e && (e.progress||0)>=4;
  }

  function unlockPlant(plantId) {
    const arr=readSave(); if(!arr) return;
    const p=arr[0]; if(!p) return;
    if(!p.plantProps) p.plantProps={};
    const cn=ID_TO_CN[plantId]; if(!cn) return;
    const cur=p.plantProps[cn];
    if(!cur||(cur.progress||0)<1) p.plantProps[cn]={progress:1,medal:false,tutorialLevel:0,boost:0,costume:-1,costumes:[]};
    writeSave(arr);
  }

  function unlockWorld(worldId) {
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
          if(name) applyItem(name);
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
    if(name==='World Key'){
      st.keys=(st.keys||0)+1;
      for(const[req,worlds] of KEY_GATES) if(st.keys>=req) worlds.forEach(w=>unlockWorld(w));
      toast('🔑 World Key ('+st.keys+'/12)','#fa0');return;
    }
    const pid=ITEM_PLANT[name];
    if(pid!==undefined){unlockPlant(pid);toast('🌱 '+name,'#4f4');return;}
    toast('📦 '+name,'#4af');
  }

  // ── Location polling (every 2s) ───────────────────────────────────────────
  function pollChecks(){
    for(const[loc,levels] of Object.entries(LOC_LEVELS)){
      if(st.checked.includes(loc)) continue;
      if(levels.every(isFinished)) fireCheck(loc);
    }
  }

  function fireCheck(loc){
    if(st.checked.includes(loc)) return;
    st.checked.push(loc);svSt();
    const id=locIds[loc];
    if(id&&conn) send([{cmd:'LocationChecks',locations:[id]}]);
    if(VICTORY_LOCS.every(l=>st.checked.includes(l)))
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
    if(cfg.slot) connect();
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
