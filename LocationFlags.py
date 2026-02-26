"""
LocationFlags.py

Complete location flag data extracted from SS_APWorld/Locations.py
Maps location names to their checked_flag data for memory checking in SSHDClient.py

Structure: (flag_type, flag_bit, flag_value, scene_or_addr)
- flag_type: "STORY", "SCENE", or "SPECIAL"
- flag_bit: 0x0-0xF (nibble position)
- flag_value: 0x01-0x80 (bit value)
- scene_or_addr: scene name (str) for SCENE flags, story flag address (int) for STORY flags, 
                 or special index (int) for SPECIAL flags

Extracted from SS_APWorld/Locations.py containing 350 locations.
"""

# Flag type constants
FLAG_STORY = "STORY"
FLAG_SCENE = "SCENE"
FLAG_SPECIAL = "SPECIAL"

# Complete mapping of all 350 locations with their checked_flag data
LOCATION_FLAG_MAP = {
    # Upper Skyloft
    "Upper Skyloft - Fledge's Gift": (FLAG_STORY, 0xF, 0x02, 0x805A9B30),  # Flag 923
    "Upper Skyloft - Owlan's Gift": (FLAG_SCENE, 0x3, 0x10, "Skyloft"),
    "Upper Skyloft - Sparring Hall Chest": (FLAG_SCENE, 0x1, 0x04, "Skyloft"),
    "Upper Skyloft - Ring Knight Academy Bell": (FLAG_SCENE, 0x7, 0x20, "Skyloft"),
    "Upper Skyloft - Chest near Goddess Statue": (FLAG_SCENE, 0xF, 0x80, "Skyloft"),
    "Upper Skyloft - First Goddess Sword Item in Goddess Statue": (FLAG_STORY, 0x0, 0x20, 0x805A9B40),  # Flag 951
    "Upper Skyloft - Second Goddess Sword Item in Goddess Statue": (FLAG_STORY, 0x0, 0x20, 0x805A9B40),  # Flag 951
    "Upper Skyloft - In Zelda's Closet": (FLAG_SCENE, 0x5, 0x01, "Skyloft"),
    "Upper Skyloft - Owlan's Crystals": (FLAG_STORY, 0x1, 0x40, 0x805A9B10),  # Flag 482
    "Upper Skyloft - Fledge's Crystals": (FLAG_STORY, 0xC, 0x10, 0x805A9B00),  # Flag 394
    "Upper Skyloft - Item from Cawlin": (FLAG_STORY, 0xF, 0x04, 0x805A9B30),  # Flag 924
    "Upper Skyloft - Ghost/Pipit's Crystals": (FLAG_SPECIAL, 0x0, 0x0, 0x0),  # SPECIAL index 0x0
    "Upper Skyloft - Pumpkin Archery -- 600 Points": (FLAG_STORY, 0x0, 0x20, 0x805A9B00),  # Flag 359

    # Central Skyloft
    "Central Skyloft - Potion Lady's Gift": (FLAG_STORY, 0xD, 0x08, 0x805A9AD0),  # Flag 35
    "Central Skyloft - Repair Gondo's Junk": (FLAG_STORY, 0xF, 0x01, 0x805A9AF0),  # Flag 322
    "Central Skyloft - Wryna's Crystals": (FLAG_STORY, 0xF, 0x10, 0x805A9AF0),  # Flag 326
    "Central Skyloft - Waterfall Cave First Chest": (FLAG_SCENE, 0xE, 0x80, "Skyloft"),
    "Central Skyloft - Waterfall Cave Second Chest": (FLAG_SCENE, 0xE, 0x40, "Skyloft"),
    "Central Skyloft - Rupee Waterfall Cave Crawlspace": (FLAG_SCENE, 0xA, 0x01, "Skyloft"),
    "Central Skyloft - Parrow's Gift": (FLAG_STORY, 0xD, 0x01, 0x805A9B00),  # Flag 382
    "Central Skyloft - Parrow's Crystals": (FLAG_STORY, 0xD, 0x04, 0x805A9B00),  # Flag 384
    "Central Skyloft - Peater/Peatrice's Crystals": (FLAG_SPECIAL, 0x1, 0x0, 0x0),  # SPECIAL index 0x1
    "Central Skyloft - Item in Bird Nest": (FLAG_SCENE, 0x0, 0x20, "Skyloft"),
    "Central Skyloft - Shed Chest": (FLAG_SCENE, 0xF, 0x40, "Skyloft"),
    "Central Skyloft - West Cliff Goddess Chest": (FLAG_SCENE, 0xC, 0x08, "Skyloft"),
    "Central Skyloft - Bazaar Goddess Chest": (FLAG_SCENE, 0xC, 0x02, "Skyloft"),
    "Central Skyloft - Shed Goddess Chest": (FLAG_SCENE, 0xB, 0x04, "Skyloft"),
    "Central Skyloft - Floating Island Goddess Chest": (FLAG_SCENE, 0xB, 0x02, "Skyloft"),
    "Central Skyloft - Waterfall Goddess Chest": (FLAG_SCENE, 0x7, 0x01, "Skyloft"),

    # Skyloft Village
    "Skyloft Village - Mallara's Crystals": (FLAG_STORY, 0x8, 0x40, 0x805A9B10),  # Flag 575
    "Skyloft Village - Bertie's Crystals": (FLAG_STORY, 0xD, 0x20, 0x805A9B00),  # Flag 387
    "Skyloft Village - Sparrot's Crystals": (FLAG_STORY, 0x2, 0x08, 0x805A9B00),  # Flag 373

    # Batreaux's House
    "Batreaux's House - First Reward": (FLAG_SCENE, 0x9, 0x40, "Skyloft"),
    "Batreaux's House - Second Reward": (FLAG_SCENE, 0x9, 0x80, "Skyloft"),
    "Batreaux's House - Third Reward": (FLAG_SCENE, 0x8, 0x01, "Skyloft"),
    "Batreaux's House - Chest": (FLAG_SCENE, 0xA, 0x20, "Skyloft"),
    "Batreaux's House - Fourth Reward": (FLAG_SCENE, 0x8, 0x02, "Skyloft"),
    "Batreaux's House - Fifth Reward": (FLAG_SCENE, 0x8, 0x04, "Skyloft"),
    "Batreaux's House - Sixth Reward": (FLAG_SCENE, 0x8, 0x08, "Skyloft"),
    "Batreaux's House - Seventh Reward": (FLAG_SCENE, 0x8, 0x08, "Skyloft"),
    "Batreaux's House - Final Reward": (FLAG_STORY, 0x0, 0x40, 0x805A9B00),  # Flag 360

    # Beedle's Airshop
    "Beedle's Airshop - 300 Rupee Item": (FLAG_STORY, 0x3, 0x01, 0x805A9B40),  # Flag 954
    "Beedle's Airshop - 600 Rupee Item": (FLAG_STORY, 0x3, 0x02, 0x805A9B40),  # Flag 955
    "Beedle's Airshop - 1200 Rupee Item": (FLAG_STORY, 0x3, 0x04, 0x805A9B40),  # Flag 956
    "Beedle's Airshop - 800 Rupee Item": (FLAG_STORY, 0x3, 0x08, 0x805A9B40),  # Flag 957
    "Beedle's Airshop - 1600 Rupee Item": (FLAG_STORY, 0x3, 0x10, 0x805A9B40),  # Flag 958
    "Beedle's Airshop - First 100 Rupee Item": (FLAG_STORY, 0xE, 0x80, 0x805A9B30),  # Flag 937
    "Beedle's Airshop - Second 100 Rupee Item": (FLAG_STORY, 0x1, 0x01, 0x805A9B40),  # Flag 938
    "Beedle's Airshop - Third 100 Rupee Item": (FLAG_STORY, 0x1, 0x02, 0x805A9B40),  # Flag 939
    "Beedle's Airshop - 50 Rupee Item": (FLAG_STORY, 0x1, 0x04, 0x805A9B40),  # Flag 940
    "Beedle's Airshop - 1000 Rupee Item": (FLAG_STORY, 0x1, 0x08, 0x805A9B40),  # Flag 941

    # Sky
    "Sky - Lumpy Pumpkin - Chandelier": (FLAG_SCENE, 0x4, 0x80, "Sky"),
    "Sky - Lumpy Pumpkin - Harp Minigame": (FLAG_STORY, 0xD, 0x04, 0x805A9AF0),  # Flag 296
    "Sky - Kina's Crystals": (FLAG_STORY, 0xE, 0x10, 0x805A9B00),  # Flag 472
    "Sky - Orielle's Crystals": (FLAG_STORY, 0xD, 0x02, 0x805A9B00),  # Flag 383
    "Sky - Beedle's Crystals": (FLAG_STORY, 0x1, 0x02, 0x805A9B10),  # Flag 477
    "Sky - Dodoh's Crystals": (FLAG_STORY, 0xE, 0x01, 0x805A9B00),  # Flag 398
    "Sky - Fun Fun Island Minigame -- 500 Rupees": (FLAG_SCENE, 0x3, 0x08, "Sky"),
    "Sky - Chest in Breakable Boulder near Fun Fun Island": (FLAG_SCENE, 0x8, 0x08, "Sky"),
    "Sky - Chest in Breakable Boulder near Lumpy Pumpkin": (FLAG_SCENE, 0x8, 0x04, "Sky"),
    "Sky - Bamboo Island Goddess Chest": (FLAG_SCENE, 0xF, 0x08, "Sky"),
    "Sky - Goddess Chest on Island next to Bamboo Island": (FLAG_SCENE, 0xF, 0x04, "Sky"),
    "Sky - Goddess Chest in Cave on Island next to Bamboo Island": (FLAG_SCENE, 0xF, 0x02, "Sky"),
    "Sky - Beedle's Island Goddess Chest": (FLAG_SCENE, 0xF, 0x01, "Sky"),
    "Sky - Beedle's Island Cage Goddess Chest": (FLAG_SCENE, 0xE, 0x08, "Sky"),
    "Sky - Northeast Island Goddess Chest behind Bombable Rocks": (FLAG_SCENE, 0xE, 0x04, "Sky"),
    "Sky - Northeast Island Cage Goddess Chest": (FLAG_SCENE, 0xE, 0x02, "Sky"),
    "Sky - Lumpy Pumpkin - Goddess Chest on the Roof": (FLAG_SCENE, 0xE, 0x01, "Sky"),
    "Sky - Lumpy Pumpkin - Outside Goddess Chest": (FLAG_SCENE, 0xD, 0x08, "Sky"),
    "Sky - Goddess Chest on Island Closest to Faron Pillar": (FLAG_SCENE, 0xD, 0x04, "Sky"),
    "Sky - Goddess Chest outside Volcanic Island": (FLAG_SCENE, 0xD, 0x02, "Sky"),
    "Sky - Goddess Chest inside Volcanic Island": (FLAG_SCENE, 0xD, 0x01, "Sky"),
    "Sky - Goddess Chest under Fun Fun Island": (FLAG_SCENE, 0xC, 0x08, "Sky"),
    "Sky - Southwest Triple Island Upper Goddess Chest": (FLAG_SCENE, 0xC, 0x04, "Sky"),
    "Sky - Southwest Triple Island Lower Goddess Chest": (FLAG_SCENE, 0xC, 0x02, "Sky"),
    "Sky - Southwest Triple Island Cage Goddess Chest": (FLAG_SCENE, 0xC, 0x01, "Sky"),

    # Thunderhead
    "Thunderhead - Isle of Songs - Strike Crest with Goddess Sword": (FLAG_SCENE, 0x7, 0x04, "Sky"),
    "Thunderhead - Isle of Songs - Strike Crest with Longsword": (FLAG_SCENE, 0x7, 0x08, "Sky"),
    "Thunderhead - Isle of Songs - Strike Crest with White Sword": (FLAG_SCENE, 0x7, 0x10, "Sky"),
    "Thunderhead - Song from Levias": (FLAG_STORY, 0xE, 0x10, 0x805A9B30),  # Flag 934
    "Thunderhead - Bug Heaven -- 10 Bugs in 3 Minutes": (FLAG_STORY, 0xF, 0x08, 0x805A9B30),  # Flag 925
    "Thunderhead - East Island Chest": (FLAG_SCENE, 0x8, 0x02, "Sky"),
    "Thunderhead - East Island Goddess Chest": (FLAG_SCENE, 0xB, 0x08, "Sky"),
    "Thunderhead - Goddess Chest on top of Isle of Songs": (FLAG_SCENE, 0xB, 0x04, "Sky"),
    "Thunderhead - Goddess Chest outside Isle of Songs": (FLAG_SCENE, 0xB, 0x02, "Sky"),
    "Thunderhead - First Goddess Chest on Mogma Mitts Island": (FLAG_SCENE, 0xB, 0x01, "Sky"),
    "Thunderhead - Second Goddess Chest on Mogma Mitts Island": (FLAG_SCENE, 0xA, 0x08, "Sky"),
    "Thunderhead - Bug Heaven Goddess Chest": (FLAG_SCENE, 0xA, 0x04, "Sky"),

    # Sealed Grounds
    "Sealed Grounds - Chest inside Sealed Temple": (FLAG_SCENE, 0xB, 0x80, "Sealed Grounds"),
    "Sealed Grounds - Song from Impa": (FLAG_SCENE, 0x2, 0x20, "Sealed Grounds"),
    "Sealed Grounds - Gorko's Goddess Wall Reward": (FLAG_SCENE, 0xF, 0x02, "Sealed Grounds"),
    "Sealed Grounds - Zelda's Blessing": (FLAG_STORY, 0x1, 0x08, 0x805A9B00),  # Flag 349

    # Faron Woods
    "Faron Woods - Item behind Lower Bombable Rock": (FLAG_SCENE, 0x5, 0x02, "Faron Woods"),
    "Faron Woods - Item on Tree": (FLAG_SCENE, 0x9, 0x10, "Faron Woods"),
    "Faron Woods - Kikwi Elder's Reward": (FLAG_STORY, 0xC, 0x10, 0x805A9AD0),  # Flag 57
    "Faron Woods - Rupee on Hollow Tree Root": (FLAG_SCENE, 0x4, 0x04, "Faron Woods"),
    "Faron Woods - Rupee on Hollow Tree Branch": (FLAG_SCENE, 0x4, 0x02, "Faron Woods"),
    "Faron Woods - Rupee on Platform near Floria Door": (FLAG_SCENE, 0x4, 0x01, "Faron Woods"),
    "Faron Woods - Deep Woods Chest": (FLAG_SCENE, 0xF, 0x80, "Faron Woods"),
    "Faron Woods - Chest behind Upper Bombable Rock": (FLAG_SCENE, 0xF, 0x40, "Faron Woods"),
    "Faron Woods - Chest inside Great Tree": (FLAG_SCENE, 0xF, 0x20, "Faron Woods"),
    "Faron Woods - Rupee on Great Tree North Branch": (FLAG_SCENE, 0x4, 0x08, "Faron Woods"),
    "Faron Woods - Rupee on Great Tree West Branch": (FLAG_SCENE, 0x4, 0x10, "Faron Woods"),

    # Lake Floria
    "Lake Floria - Rupee under Central Boulder": (FLAG_SCENE, 0x6, 0x10, "Lake Floria"),
    "Lake Floria - Rupee behind Southwest Boulder": (FLAG_SCENE, 0x6, 0x80, "Lake Floria"),
    "Lake Floria - Left Rupee behind Northwest Boulder": (FLAG_SCENE, 0x6, 0x40, "Lake Floria"),
    "Lake Floria - Right Rupee behind Northwest Boulder": (FLAG_SCENE, 0x6, 0x20, "Lake Floria"),
    "Lake Floria - Lake Floria Chest": (FLAG_SCENE, 0xF, 0x80, "Lake Floria"),
    "Lake Floria - Dragon Lair South Chest": (FLAG_SCENE, 0xF, 0x20, "Lake Floria"),
    "Lake Floria - Dragon Lair East Chest": (FLAG_SCENE, 0xF, 0x40, "Lake Floria"),
    "Lake Floria - Rupee on High Ledge outside Ancient Cistern Entrance": (FLAG_SCENE, 0x9, 0x01, "Lake Floria"),

    # Flooded Faron Woods
    "Flooded Faron Woods - Yellow Tadtone under Lilypad": (FLAG_SCENE, 0x4, 0x01, "Flooded Faron Woods"),
    "Flooded Faron Woods - 8 Light Blue Tadtones near Viewing Platform": (FLAG_SCENE, 0x5, 0x04, "Flooded Faron Woods"),
    "Flooded Faron Woods - 4 Purple Tadtones under Viewing Platform": (FLAG_SCENE, 0x5, 0x01, "Flooded Faron Woods"),
    "Flooded Faron Woods - Red Moving Tadtone near Viewing Platform": (FLAG_SCENE, 0x2, 0x80, "Flooded Faron Woods"),
    "Flooded Faron Woods - Light Blue Tadtone under Great Tree Root": (FLAG_SCENE, 0x4, 0x08, "Flooded Faron Woods"),
    "Flooded Faron Woods - 8 Yellow Tadtones near Kikwi Elder": (FLAG_SCENE, 0x5, 0x10, "Flooded Faron Woods"),
    "Flooded Faron Woods - 4 Light Blue Moving Tadtones under Kikwi Elder": (FLAG_SCENE, 0x5, 0x40, "Flooded Faron Woods"),
    "Flooded Faron Woods - 4 Red Moving Tadtones North West of Great Tree": (FLAG_SCENE, 0x4, 0x02, "Flooded Faron Woods"),
    "Flooded Faron Woods - Green Tadtone behind Upper Bombable Rock": (FLAG_SCENE, 0x5, 0x08, "Flooded Faron Woods"),
    "Flooded Faron Woods - 2 Dark Blue Tadtones in Grass West of Great Tree": (FLAG_SCENE, 0x5, 0x02, "Flooded Faron Woods"),
    "Flooded Faron Woods - 8 Green Tadtones in West Tunnel": (FLAG_SCENE, 0x5, 0x80, "Flooded Faron Woods"),
    "Flooded Faron Woods - 2 Red Tadtones in Grass near Lower Bombable Rock": (FLAG_SCENE, 0x4, 0x20, "Flooded Faron Woods"),
    "Flooded Faron Woods - 16 Dark Blue Tadtones in the South West": (FLAG_SCENE, 0x4, 0x80, "Flooded Faron Woods"),
    "Flooded Faron Woods - 4 Purple Moving Tadtones near Floria Gate": (FLAG_SCENE, 0x4, 0x40, "Flooded Faron Woods"),
    "Flooded Faron Woods - Dark Blue Moving Tadtone inside Small Hollow Tree": (FLAG_SCENE, 0x5, 0x20, "Flooded Faron Woods"),
    "Flooded Faron Woods - 4 Yellow Tadtones under Small Hollow Tree": (FLAG_SCENE, 0x4, 0x10, "Flooded Faron Woods"),
    "Flooded Faron Woods - 8 Purple Tadtones in Clearing after Small Hollow Tree": (FLAG_SCENE, 0x4, 0x04, "Flooded Faron Woods"),
    "Flooded Faron Woods - Water Dragon's Reward": (FLAG_STORY, 0xB, 0x02, 0x805A9AD0),  # Flag 16

    # Eldin Volcano
    "Eldin Volcano - Rupee on Ledge before First Room": (FLAG_SCENE, 0x4, 0x02, "Eldin Volcano"),
    "Eldin Volcano - Chest behind Bombable Wall in First Room": (FLAG_SCENE, 0xE, 0x40, "Eldin Volcano"),
    "Eldin Volcano - Rupee behind Bombable Wall in First Room": (FLAG_SCENE, 0x0, 0x20, "Eldin Volcano"),
    "Eldin Volcano - Rupee in Crawlspace in First Room": (FLAG_SCENE, 0x3, 0x08, "Eldin Volcano"),
    "Eldin Volcano - Chest after Crawlspace": (FLAG_SCENE, 0xC, 0x40, "Eldin Volcano"),
    "Eldin Volcano - Southeast Rupee above Mogma Turf Entrance": (FLAG_SCENE, 0xE, 0x20, "Eldin Volcano"),
    "Eldin Volcano - North Rupee above Mogma Turf Entrance": (FLAG_SCENE, 0xE, 0x08, "Eldin Volcano"),
    "Eldin Volcano - Chest behind Bombable Wall near Cliff": (FLAG_SCENE, 0x3, 0x40, "Eldin Volcano"),
    "Eldin Volcano - Item on Cliff": (FLAG_SCENE, 0xD, 0x40, "Eldin Volcano"),
    "Eldin Volcano - Chest behind Bombable Wall near Volcano Ascent": (FLAG_SCENE, 0x9, 0x10, "Eldin Volcano"),
    "Eldin Volcano - Left Rupee behind Bombable Wall on First Slope": (FLAG_SCENE, 0x4, 0x20, "Eldin Volcano"),
    "Eldin Volcano - Right Rupee behind Bombable Wall on First Slope": (FLAG_SCENE, 0x0, 0x08, "Eldin Volcano"),
    "Eldin Volcano - Digging Spot in front of Earth Temple": (FLAG_SCENE, 0x0, 0x01, "Eldin Volcano"),
    "Eldin Volcano - Digging Spot below Tower": (FLAG_SCENE, 0x0, 0x02, "Eldin Volcano"),
    "Eldin Volcano - Digging Spot behind Boulder on Sandy Slope": (FLAG_SCENE, 0x0, 0x10, "Eldin Volcano"),
    "Eldin Volcano - Digging Spot after Vents": (FLAG_SCENE, 0x0, 0x04, "Eldin Volcano"),
    "Eldin Volcano - Digging Spot after Draining Lava": (FLAG_SCENE, 0x9, 0x01, "Eldin Volcano"),

    # Mogma Turf
    "Mogma Turf - Free Fall Chest": (FLAG_SCENE, 0xC, 0x10, "Eldin Volcano"),
    "Mogma Turf - Chest behind Bombable Wall at Entrance": (FLAG_SCENE, 0xF, 0x04, "Eldin Volcano"),
    "Mogma Turf - Defeat Bokoblins": (FLAG_SCENE, 0x1, 0x08, "Eldin Volcano"),
    "Mogma Turf - Sand Slide Chest": (FLAG_SCENE, 0xF, 0x02, "Eldin Volcano"),
    "Mogma Turf - Chest behind Bombable Wall in Fire Maze": (FLAG_SCENE, 0xF, 0x01, "Eldin Volcano"),

    # Volcano Summit
    "Volcano Summit - Chest behind Bombable Wall in Waterfall Area": (FLAG_SCENE, 0xE, 0x80, "Boko Base/Volcano Summit"),
    "Volcano Summit - Item behind Digging": (FLAG_SCENE, 0xC, 0x01, "Boko Base/Volcano Summit"),

    # Bokoblin Base
    "Bokoblin Base - Plats' Gift": (FLAG_STORY, 0x5, 0x01, 0x805A9AE0),  # Flag 177
    "Bokoblin Base - Chest near Bone Bridge": (FLAG_SCENE, 0x8, 0x08, "Boko Base/Volcano Summit"),
    "Bokoblin Base - Chest on Cliff": (FLAG_SCENE, 0x8, 0x10, "Boko Base/Volcano Summit"),
    "Bokoblin Base - Chest near Drawbridge": (FLAG_SCENE, 0x8, 0x20, "Boko Base/Volcano Summit"),
    "Bokoblin Base - Chest East of Earth Temple Entrance": (FLAG_SCENE, 0x8, 0x40, "Boko Base/Volcano Summit"),
    "Bokoblin Base - Chest West of Earth Temple Entrance": (FLAG_SCENE, 0x8, 0x80, "Boko Base/Volcano Summit"),
    "Bokoblin Base - First Chest in Volcano Summit": (FLAG_SCENE, 0x7, 0x40, "Boko Base/Volcano Summit"),
    "Bokoblin Base - Raised Chest in Volcano Summit": (FLAG_SCENE, 0x7, 0x80, "Boko Base/Volcano Summit"),
    "Bokoblin Base - Chest in Volcano Summit Alcove": (FLAG_SCENE, 0x6, 0x40, "Boko Base/Volcano Summit"),
    "Bokoblin Base - Fire Dragon's Reward": (FLAG_STORY, 0xB, 0x08, 0x805A9AD0),  # Flag 19

    # Lanayru Mine
    "Lanayru Mine - Chest behind First Landing": (FLAG_SCENE, 0x4, 0x80, "Lanayru Desert"),
    "Lanayru Mine - Chest near First Timeshift Stone": (FLAG_SCENE, 0x4, 0x40, "Lanayru Desert"),
    "Lanayru Mine - Chest behind Statue": (FLAG_SCENE, 0x4, 0x20, "Lanayru Desert"),
    "Lanayru Mine - Chest at the End of Mine": (FLAG_SCENE, 0x4, 0x10, "Lanayru Desert"),

    # Lanayru Desert
    "Lanayru Desert - Chest near Party Wheel": (FLAG_SCENE, 0x4, 0x08, "Lanayru Desert"),
    "Lanayru Desert - Chest near Caged Robot": (FLAG_SCENE, 0xF, 0x01, "Lanayru Desert"),
    "Lanayru Desert - Rescue Caged Robot": (FLAG_STORY, 0xF, 0x80, 0x805A9AE0),  # Flag 90
    "Lanayru Desert - Chest on Platform near Fire Node": (FLAG_SCENE, 0x4, 0x04, "Lanayru Desert"),
    "Lanayru Desert - Chest on Platform near Lightning Node": (FLAG_SCENE, 0x4, 0x02, "Lanayru Desert"),
    "Lanayru Desert - Chest near Sand Oasis": (FLAG_SCENE, 0x8, 0x01, "Lanayru Desert"),
    "Lanayru Desert - Chest on top of Lanayru Mining Facility": (FLAG_SCENE, 0x7, 0x01, "Lanayru Desert"),
    "Lanayru Desert - Secret Passageway Chest": (FLAG_SCENE, 0xA, 0x40, "Lanayru Desert"),
    "Lanayru Desert - Fire Node - Shortcut Chest": (FLAG_SCENE, 0xB, 0x04, "Lanayru Desert"),
    "Lanayru Desert - Fire Node - First Small Chest": (FLAG_SCENE, 0xB, 0x08, "Lanayru Desert"),
    "Lanayru Desert - Fire Node - Second Small Chest": (FLAG_SCENE, 0xC, 0x40, "Lanayru Desert"),
    "Lanayru Desert - Fire Node - Left Ending Chest": (FLAG_SCENE, 0xE, 0x20, "Lanayru Desert"),
    "Lanayru Desert - Fire Node - Right Ending Chest": (FLAG_SCENE, 0xC, 0x08, "Lanayru Desert"),
    "Lanayru Desert - Lightning Node - First Chest": (FLAG_SCENE, 0xB, 0x10, "Lanayru Desert"),
    "Lanayru Desert - Lightning Node - Second Chest": (FLAG_SCENE, 0xB, 0x20, "Lanayru Desert"),
    "Lanayru Desert - Lightning Node - Raised Chest near Generator": (FLAG_SCENE, 0xB, 0x40, "Lanayru Desert"),

    # Lanayru Caves
    "Lanayru Caves - Chest": (FLAG_SCENE, 0xB, 0x40, "Lanayru Gorge"),
    "Lanayru Caves - Golo's Gift": (FLAG_SCENE, 0xC, 0x10, "Lanayru Gorge"),

    # Lanayru Gorge
    "Lanayru Gorge - Thunder Dragon's Reward": (FLAG_STORY, 0xB, 0x20, 0x805A9AD0),  # Flag 21
    "Lanayru Gorge - Item on Pillar": (FLAG_SCENE, 0x0, 0x02, "Lanayru Gorge"),
    "Lanayru Gorge - Digging Spot": (FLAG_SCENE, 0x2, 0x40, "Lanayru Gorge"),

    # Lanayru Sand Sea
    "Lanayru Sand Sea - Ancient Harbour - Rupee on First Pillar": (FLAG_SCENE, 0xA, 0x10, "Lanayru Sand Sea"),
    "Lanayru Sand Sea - Ancient Harbour - Left Rupee on Entrance Crown": (FLAG_SCENE, 0xA, 0x08, "Lanayru Sand Sea"),
    "Lanayru Sand Sea - Ancient Harbour - Right Rupee on Entrance Crown": (FLAG_SCENE, 0xA, 0x20, "Lanayru Sand Sea"),
    "Lanayru Sand Sea - Skipper's Retreat - Chest after Moblin": (FLAG_SCENE, 0xF, 0x80, "Lanayru Sand Sea"),
    "Lanayru Sand Sea - Skipper's Retreat - Chest on top of Cacti Pillar": (FLAG_SCENE, 0xF, 0x40, "Lanayru Sand Sea"),
    "Lanayru Sand Sea - Skipper's Retreat - Chest in Shack": (FLAG_SCENE, 0x3, 0x02, "Lanayru Sand Sea"),
    "Lanayru Sand Sea - Skipper's Retreat - Skydive Chest": (FLAG_SCENE, 0xF, 0x20, "Lanayru Sand Sea"),
    "Lanayru Sand Sea - Rickety Coaster -- Heart Stopping Track in 1'05": (FLAG_STORY, 0xE, 0x02, 0x805A9B10),  # Flag 667
    "Lanayru Sand Sea - Pirate Stronghold - Rupee on East Sea Pillar": (FLAG_SCENE, 0x0, 0x10, "Lanayru Sand Sea"),
    "Lanayru Sand Sea - Pirate Stronghold - Rupee on West Sea Pillar": (FLAG_SCENE, 0x0, 0x08, "Lanayru Sand Sea"),
    "Lanayru Sand Sea - Pirate Stronghold - Rupee on Bird Statue Pillar or Nose": (FLAG_SCENE, 0x0, 0x20, "Lanayru Sand Sea"),
    "Lanayru Sand Sea - Pirate Stronghold - First Chest": (FLAG_SCENE, 0xF, 0x10, "Lanayru Sand Sea"),
    "Lanayru Sand Sea - Pirate Stronghold - Second Chest": (FLAG_SCENE, 0xF, 0x08, "Lanayru Sand Sea"),
    "Lanayru Sand Sea - Pirate Stronghold - Third Chest": (FLAG_SCENE, 0xF, 0x04, "Lanayru Sand Sea"),

    # Skyview
    "Skyview - Chest on Tree Branch": (FLAG_SCENE, 0x0, 0x08, "Skyview"),
    "Skyview - Digging Spot in Crawlspace": (FLAG_SCENE, 0x0, 0x80, "Skyview"),
    "Skyview - Chest behind Two Eyes": (FLAG_SCENE, 0xF, 0x20, "Skyview"),
    "Skyview - Chest after Stalfos Fight": (FLAG_SCENE, 0x5, 0x08, "Skyview"),
    "Skyview - Item behind Bars": (FLAG_SCENE, 0xD, 0x80, "Skyview"),
    "Skyview - Rupee in Southeast Tunnel": (FLAG_SCENE, 0x9, 0x02, "Skyview"),
    "Skyview - Rupee in Southwest Tunnel": (FLAG_SCENE, 0x9, 0x08, "Skyview"),
    "Skyview - Rupee in East Tunnel": (FLAG_SCENE, 0x9, 0x04, "Skyview"),
    "Skyview - Chest behind Three Eyes": (FLAG_SCENE, 0xF, 0x40, "Skyview"),
    "Skyview - Chest near Boss Door": (FLAG_SCENE, 0xB, 0x10, "Skyview"),
    "Skyview - Boss Key Chest": (FLAG_SCENE, 0x2, 0x40, "Skyview"),
    "Skyview - Heart Container": (FLAG_SCENE, 0xD, 0x40, "Skyview"),
    "Skyview - Rupee on Spring Pillar": (FLAG_SCENE, 0xC, 0x20, "Skyview"),
    "Skyview - Strike Crest": (FLAG_SCENE, 0xC, 0x02, "Skyview"),

    # Earth Temple
    "Earth Temple - Vent Chest": (FLAG_SCENE, 0x6, 0x80, "Earth Temple"),
    "Earth Temple - Rupee above Drawbridge": (FLAG_SCENE, 0x2, 0x02, "Earth Temple"),
    "Earth Temple - Chest behind Bombable Rock": (FLAG_SCENE, 0x6, 0x40, "Earth Temple"),
    "Earth Temple - Chest Left of Main Room Bridge": (FLAG_SCENE, 0x6, 0x20, "Earth Temple"),
    "Earth Temple - Chest in West Room": (FLAG_SCENE, 0x3, 0x02, "Earth Temple"),
    "Earth Temple - Chest after Double Lizalfos Fight": (FLAG_SCENE, 0x0, 0x02, "Earth Temple"),
    "Earth Temple - Ledd's Gift": (FLAG_SCENE, 0x4, 0x20, "Earth Temple"),
    "Earth Temple - Rupee in Lava Tunnel": (FLAG_SCENE, 0x3, 0x20, "Earth Temple"),
    "Earth Temple - Chest Guarded by Lizalfos": (FLAG_SCENE, 0x6, 0x10, "Earth Temple"),
    "Earth Temple - Boss Key Chest": (FLAG_SCENE, 0x3, 0x80, "Earth Temple"),
    "Earth Temple - Heart Container": (FLAG_SCENE, 0x6, 0x01, "Earth Temple"),
    "Earth Temple - Strike Crest": (FLAG_SCENE, 0x5, 0x40, "Earth Temple"),

    # Lanayru Mining Facility
    "Lanayru Mining Facility - Chest behind Bars": (FLAG_SCENE, 0x4, 0x20, "Lanayru Mining Facility"),
    "Lanayru Mining Facility - First Chest in Hub Room": (FLAG_SCENE, 0x6, 0x20, "Lanayru Mining Facility"),
    "Lanayru Mining Facility - Chest in First West Room": (FLAG_SCENE, 0x4, 0x04, "Lanayru Mining Facility"),
    "Lanayru Mining Facility - Chest after Armos Fight": (FLAG_SCENE, 0x3, 0x40, "Lanayru Mining Facility"),
    "Lanayru Mining Facility - Chest in Key Locked Room": (FLAG_SCENE, 0x4, 0x02, "Lanayru Mining Facility"),
    "Lanayru Mining Facility - Raised Chest in Hop across Boxes Room": (FLAG_SCENE, 0x6, 0x02, "Lanayru Mining Facility"),
    "Lanayru Mining Facility - Lower Chest in Hop across Boxes Room": (FLAG_SCENE, 0x7, 0x02, "Lanayru Mining Facility"),
    "Lanayru Mining Facility - Chest behind First Crawlspace": (FLAG_SCENE, 0x7, 0x80, "Lanayru Mining Facility"),
    "Lanayru Mining Facility - Chest in Spike Maze": (FLAG_SCENE, 0x7, 0x10, "Lanayru Mining Facility"),
    "Lanayru Mining Facility - Boss Key Chest": (FLAG_SCENE, 0x1, 0x40, "Lanayru Mining Facility"),
    "Lanayru Mining Facility - Shortcut Chest in Main Hub": (FLAG_SCENE, 0x7, 0x01, "Lanayru Mining Facility"),
    "Lanayru Mining Facility - Heart Container": (FLAG_SCENE, 0xE, 0x40, "Lanayru Mining Facility"),
    "Lanayru Mining Facility - Exit Hall of Ancient Robots": (FLAG_STORY, 0xE, 0x40, 0x805A9B30),  # Flag 936

    # Ancient Cistern
    "Ancient Cistern - Rupee in West Hand": (FLAG_SCENE, 0xA, 0x20, "Ancient Cistern"),
    "Ancient Cistern - Rupee in East Hand": (FLAG_SCENE, 0xA, 0x10, "Ancient Cistern"),
    "Ancient Cistern - First Rupee in East Part in Short Tunnel": (FLAG_SCENE, 0x9, 0x02, "Ancient Cistern"),
    "Ancient Cistern - Second Rupee in East Part in Short Tunnel": (FLAG_SCENE, 0x9, 0x04, "Ancient Cistern"),
    "Ancient Cistern - Third Rupee in East Part in Short Tunnel": (FLAG_SCENE, 0x9, 0x08, "Ancient Cistern"),
    "Ancient Cistern - Rupee in East Part in Cubby": (FLAG_SCENE, 0x9, 0x10, "Ancient Cistern"),
    "Ancient Cistern - Rupee in East Part in Main Tunnel": (FLAG_SCENE, 0x5, 0x04, "Ancient Cistern"),
    "Ancient Cistern - Chest in East Part": (FLAG_SCENE, 0xD, 0x04, "Ancient Cistern"),
    "Ancient Cistern - Chest after Whip Hooks": (FLAG_SCENE, 0x0, 0x08, "Ancient Cistern"),
    "Ancient Cistern - Chest near Vines": (FLAG_SCENE, 0xD, 0x02, "Ancient Cistern"),
    "Ancient Cistern - Chest behind the Waterfall": (FLAG_SCENE, 0xE, 0x01, "Ancient Cistern"),
    "Ancient Cistern - Bokoblin": (FLAG_SCENE, 0x9, 0x20, "Ancient Cistern"),
    "Ancient Cistern - Rupee under Lilypad": (FLAG_SCENE, 0x0, 0x20, "Ancient Cistern"),
    "Ancient Cistern - Chest in Key Locked Room": (FLAG_SCENE, 0xC, 0x01, "Ancient Cistern"),
    "Ancient Cistern - Boss Key Chest": (FLAG_SCENE, 0xD, 0x20, "Ancient Cistern"),
    "Ancient Cistern - Heart Container": (FLAG_SCENE, 0x8, 0x20, "Ancient Cistern"),
    "Ancient Cistern - Farore's Flame": (FLAG_SCENE, 0xB, 0x20, "Ancient Cistern"),

    # Sandship
    "Sandship - Chest at the Stern": (FLAG_SCENE, 0x3, 0x20, "Sandship"),
    "Sandship - Chest before 4-Door Corridor": (FLAG_SCENE, 0xE, 0x80, "Sandship"),
    "Sandship - Chest behind Combination Lock": (FLAG_SCENE, 0xE, 0x40, "Sandship"),
    "Sandship - Treasure Room First Chest": (FLAG_SCENE, 0xF, 0x20, "Sandship"),
    "Sandship - Treasure Room Second Chest": (FLAG_SCENE, 0xF, 0x04, "Sandship"),
    "Sandship - Treasure Room Third Chest": (FLAG_SCENE, 0xF, 0x08, "Sandship"),
    "Sandship - Treasure Room Fourth Chest": (FLAG_SCENE, 0xF, 0x10, "Sandship"),
    "Sandship - Treasure Room Fifth Chest": (FLAG_SCENE, 0xF, 0x40, "Sandship"),
    "Sandship - Robot in Brig's Reward": (FLAG_SCENE, 0xC, 0x10, "Sandship"),
    "Sandship - Chest after Scervo Fight": (FLAG_SCENE, 0xA, 0x10, "Sandship"),
    "Sandship - Boss Key Chest": (FLAG_SCENE, 0x3, 0x04, "Sandship"),
    "Sandship - Heart Container": (FLAG_SCENE, 0xB, 0x20, "Sandship"),
    "Sandship - Nayru's Flame": (FLAG_SCENE, 0xB, 0x80, "Sandship"),

    # Fire Sanctuary
    "Fire Sanctuary - Chest in First Room": (FLAG_SCENE, 0x1, 0x20, "Fire Sanctuary"),
    "Fire Sanctuary - Chest in Second Room": (FLAG_SCENE, 0xF, 0x02, "Fire Sanctuary"),
    "Fire Sanctuary - Chest on Balcony": (FLAG_SCENE, 0xE, 0x40, "Fire Sanctuary"),
    "Fire Sanctuary - Chest near First Trapped Mogma": (FLAG_SCENE, 0xE, 0x08, "Fire Sanctuary"),
    "Fire Sanctuary - First Chest in Water Fruit Room": (FLAG_SCENE, 0xE, 0x04, "Fire Sanctuary"),
    "Fire Sanctuary - Second Chest in Water Fruit Room": (FLAG_SCENE, 0xD, 0x40, "Fire Sanctuary"),
    "Fire Sanctuary - Rescue First Trapped Mogma": (FLAG_SCENE, 0xD, 0x10, "Fire Sanctuary"),
    "Fire Sanctuary - Rescue Second Trapped Mogma": (FLAG_SCENE, 0x8, 0x20, "Fire Sanctuary"),
    "Fire Sanctuary - Chest after Bombable Wall": (FLAG_SCENE, 0xD, 0x02, "Fire Sanctuary"),
    "Fire Sanctuary - Plats' Chest": (FLAG_SCENE, 0xC, 0x10, "Fire Sanctuary"),
    "Fire Sanctuary - Chest in Staircase Room": (FLAG_SCENE, 0x3, 0x02, "Fire Sanctuary"),
    "Fire Sanctuary - Boss Key Chest": (FLAG_SCENE, 0xB, 0x40, "Fire Sanctuary"),
    "Fire Sanctuary - Heart Container": (FLAG_SCENE, 0xE, 0x10, "Fire Sanctuary"),
    "Fire Sanctuary - Din's Flame": (FLAG_SCENE, 0xA, 0x80, "Fire Sanctuary"),

    # Sky Keep
    "Sky Keep - First Chest": (FLAG_SCENE, 0x3, 0x20, "Sky Keep"),
    "Sky Keep - Chest after Dreadfuse": (FLAG_SCENE, 0xA, 0x80, "Sky Keep"),
    "Sky Keep - Rupee in Fire Sanctuary Room in Alcove": (FLAG_SCENE, 0x5, 0x10, "Sky Keep"),
    "Sky Keep - Sacred Power of Din": (FLAG_SCENE, 0x6, 0x20, "Sky Keep"),
    "Sky Keep - Sacred Power of Nayru": (FLAG_SCENE, 0x6, 0x40, "Sky Keep"),
    "Sky Keep - Sacred Power of Farore": (FLAG_SCENE, 0x9, 0x01, "Sky Keep"),

    # Silent Realms
    "Skyloft Silent Realm - Trial Reward": (FLAG_STORY, 0xF, 0x01, 0x805A9B30),  # Flag 922
    "Faron Silent Realm - Trial Reward": (FLAG_STORY, 0xC, 0x20, 0x805A9B30),  # Flag 919
    "Lanayru Silent Realm - Trial Reward": (FLAG_STORY, 0xC, 0x80, 0x805A9B30),  # Flag 921
    "Eldin Silent Realm - Trial Reward": (FLAG_STORY, 0xC, 0x40, 0x805A9B30),  # Flag 920

    # Skyloft Silent Realm Relics
    "Skyloft Silent Realm - Relic 1": (FLAG_SCENE, 0xD, 0x80, "Skyloft Silent Realm"),
    "Skyloft Silent Realm - Relic 2": (FLAG_SCENE, 0xC, 0x01, "Skyloft Silent Realm"),
    "Skyloft Silent Realm - Relic 3": (FLAG_SCENE, 0xC, 0x02, "Skyloft Silent Realm"),
    "Skyloft Silent Realm - Relic 4": (FLAG_SCENE, 0xC, 0x04, "Skyloft Silent Realm"),
    "Skyloft Silent Realm - Relic 5": (FLAG_SCENE, 0xC, 0x08, "Skyloft Silent Realm"),
    "Skyloft Silent Realm - Relic 6": (FLAG_SCENE, 0xC, 0x10, "Skyloft Silent Realm"),
    "Skyloft Silent Realm - Relic 7": (FLAG_SCENE, 0xC, 0x20, "Skyloft Silent Realm"),
    "Skyloft Silent Realm - Relic 8": (FLAG_SCENE, 0xC, 0x40, "Skyloft Silent Realm"),
    "Skyloft Silent Realm - Relic 9": (FLAG_SCENE, 0xC, 0x80, "Skyloft Silent Realm"),
    "Skyloft Silent Realm - Relic 10": (FLAG_SCENE, 0xF, 0x01, "Skyloft Silent Realm"),

    # Faron Silent Realm Relics
    "Faron Silent Realm - Relic 1": (FLAG_SCENE, 0xD, 0x80, "Faron Silent Realm"),
    "Faron Silent Realm - Relic 2": (FLAG_SCENE, 0xC, 0x01, "Faron Silent Realm"),
    "Faron Silent Realm - Relic 3": (FLAG_SCENE, 0xC, 0x02, "Faron Silent Realm"),
    "Faron Silent Realm - Relic 4": (FLAG_SCENE, 0xC, 0x04, "Faron Silent Realm"),
    "Faron Silent Realm - Relic 5": (FLAG_SCENE, 0xC, 0x08, "Faron Silent Realm"),
    "Faron Silent Realm - Relic 6": (FLAG_SCENE, 0xC, 0x10, "Faron Silent Realm"),
    "Faron Silent Realm - Relic 7": (FLAG_SCENE, 0xC, 0x20, "Faron Silent Realm"),
    "Faron Silent Realm - Relic 8": (FLAG_SCENE, 0xC, 0x40, "Faron Silent Realm"),
    "Faron Silent Realm - Relic 9": (FLAG_SCENE, 0xC, 0x80, "Faron Silent Realm"),
    "Faron Silent Realm - Relic 10": (FLAG_SCENE, 0xF, 0x01, "Faron Silent Realm"),

    # Lanayru Silent Realm Relics
    "Lanayru Silent Realm - Relic 1": (FLAG_SCENE, 0xD, 0x80, "Lanayru Silent Realm"),
    "Lanayru Silent Realm - Relic 2": (FLAG_SCENE, 0xC, 0x01, "Lanayru Silent Realm"),
    "Lanayru Silent Realm - Relic 3": (FLAG_SCENE, 0xC, 0x02, "Lanayru Silent Realm"),
    "Lanayru Silent Realm - Relic 4": (FLAG_SCENE, 0xC, 0x04, "Lanayru Silent Realm"),
    "Lanayru Silent Realm - Relic 5": (FLAG_SCENE, 0xC, 0x08, "Lanayru Silent Realm"),
    "Lanayru Silent Realm - Relic 6": (FLAG_SCENE, 0xC, 0x10, "Lanayru Silent Realm"),
    "Lanayru Silent Realm - Relic 7": (FLAG_SCENE, 0xC, 0x20, "Lanayru Silent Realm"),
    "Lanayru Silent Realm - Relic 8": (FLAG_SCENE, 0xC, 0x40, "Lanayru Silent Realm"),
    "Lanayru Silent Realm - Relic 9": (FLAG_SCENE, 0xC, 0x80, "Lanayru Silent Realm"),
    "Lanayru Silent Realm - Relic 10": (FLAG_SCENE, 0xF, 0x01, "Lanayru Silent Realm"),

    # Eldin Silent Realm Relics
    "Eldin Silent Realm - Relic 1": (FLAG_SCENE, 0xD, 0x80, "Eldin Silent Realm"),
    "Eldin Silent Realm - Relic 2": (FLAG_SCENE, 0xC, 0x01, "Eldin Silent Realm"),
    "Eldin Silent Realm - Relic 3": (FLAG_SCENE, 0xC, 0x02, "Eldin Silent Realm"),
    "Eldin Silent Realm - Relic 4": (FLAG_SCENE, 0xC, 0x04, "Eldin Silent Realm"),
    "Eldin Silent Realm - Relic 5": (FLAG_SCENE, 0xC, 0x08, "Eldin Silent Realm"),
    "Eldin Silent Realm - Relic 6": (FLAG_SCENE, 0xC, 0x10, "Eldin Silent Realm"),
    "Eldin Silent Realm - Relic 7": (FLAG_SCENE, 0xC, 0x20, "Eldin Silent Realm"),
    "Eldin Silent Realm - Relic 8": (FLAG_SCENE, 0xC, 0x40, "Eldin Silent Realm"),
    "Eldin Silent Realm - Relic 9": (FLAG_SCENE, 0xC, 0x80, "Eldin Silent Realm"),
    "Eldin Silent Realm - Relic 10": (FLAG_SCENE, 0xF, 0x01, "Eldin Silent Realm"),

    # Single Gratitude Crystals
    "Upper Skyloft - Crystal in Link's Room": (FLAG_SCENE, 0xC, 0x01, "Skyloft"),
    "Upper Skyloft - Crystal in Knight Academy Plant": (FLAG_SCENE, 0xD, 0x40, "Skyloft"),
    "Upper Skyloft - Crystal in Zelda's Room": (FLAG_SCENE, 0xD, 0x80, "Skyloft"),
    "Upper Skyloft - Crystal in Sparring Hall": (FLAG_SCENE, 0xF, 0x08, "Skyloft"),
    "Central Skyloft - Crystal in Orielle and Parrow's House": (FLAG_SCENE, 0xF, 0x04, "Skyloft"),
    "Central Skyloft - Crystal on West Cliff": (FLAG_SCENE, 0xF, 0x02, "Skyloft"),
    "Central Skyloft - Crystal between Wooden Planks": (FLAG_SCENE, 0xF, 0x01, "Skyloft"),
    "Central Skyloft - Crystal after Waterfall Cave": (FLAG_SCENE, 0xC, 0x80, "Skyloft"),
    "Central Skyloft - Crystal in Loftwing Prison": (FLAG_SCENE, 0xC, 0x40, "Skyloft"),
    "Central Skyloft - Crystal on Waterfall Island": (FLAG_SCENE, 0xC, 0x20, "Skyloft"),
    "Central Skyloft - Crystal on Light Tower": (FLAG_SCENE, 0xC, 0x04, "Skyloft"),
    "Skyloft Village - Crystal near Pumpkin Patch": (FLAG_SCENE, 0xC, 0x10, "Skyloft"),
    "Sky - Crystal outside Lumpy Pumpkin": (FLAG_SCENE, 0xD, 0x10, "Sky"),
    "Sky - Crystal inside Lumpy Pumpkin": (FLAG_SCENE, 0xF, 0x10, "Sky"),
    "Sky - Crystal on Beedle's Ship": (FLAG_SCENE, 0xF, 0x80, "Sky"),

    # Victory Location
    "Hylia's Realm - Defeat Demise": (FLAG_STORY, 0x3, 0x20, 0x805A9B40),  # Flag 959
}

# Count of locations in the mapping
TOTAL_LOCATIONS = len(LOCATION_FLAG_MAP)

# Scene name to scene ID mapping (for reference - may need to be populated with actual values)
SCENE_NAME_MAP = {
    "Skyloft": "F000",
    "Sky": "F020",
    "Sealed Grounds": "F400",
    "Faron Woods": "F100",
    "Lake Floria": "F102",
    "Flooded Faron Woods": "F103",
    "Eldin Volcano": "F200",
    "Boko Base/Volcano Summit": "F202",
    "Lanayru Desert": "F300",
    "Lanayru Gorge": "F302",
    "Lanayru Sand Sea": "F301",
    "Skyview": "D100",
    "Earth Temple": "D200",
    "Lanayru Mining Facility": "D300",
    "Ancient Cistern": "D101",
    "Sandship": "D301",
    "Fire Sanctuary": "D201",
    "Sky Keep": "D003",
    "Skyloft Silent Realm": "S000",
    "Faron Silent Realm": "S100",
    "Lanayru Silent Realm": "S300",
    "Eldin Silent Realm": "S200",
}


def get_location_flag_data(location_name: str):
    """
    Get the flag checking data for a specific location.
    
    Args:
        location_name: The name of the location
        
    Returns:
        Tuple of (flag_type, flag_bit, flag_value, scene_or_addr) or None if not found
    """
    return LOCATION_FLAG_MAP.get(location_name)


def get_all_story_flag_locations():
    """
    Get all locations that use STORY flags.
    
    Returns:
        Dictionary mapping location names to their story flag data
    """
    return {
        name: data
        for name, data in LOCATION_FLAG_MAP.items()
        if data[0] == FLAG_STORY
    }


def get_all_scene_flag_locations():
    """
    Get all locations that use SCENE flags.
    
    Returns:
        Dictionary mapping location names to their scene flag data
    """
    return {
        name: data
        for name, data in LOCATION_FLAG_MAP.items()
        if data[0] == FLAG_SCENE
    }


def get_all_special_flag_locations():
    """
    Get all locations that use SPECIAL flags.
    
    Returns:
        Dictionary mapping location names to their special flag data
    """
    return {
        name: data
        for name, data in LOCATION_FLAG_MAP.items()
        if data[0] == FLAG_SPECIAL
    }


def get_locations_by_scene(scene_name: str):
    """
    Get all locations in a specific scene.
    
    Args:
        scene_name: The name of the scene
        
    Returns:
        Dictionary mapping location names to their flag data for the given scene
    """
    return {
        name: data
        for name, data in LOCATION_FLAG_MAP.items()
        if data[0] == FLAG_SCENE and data[3] == scene_name
    }
