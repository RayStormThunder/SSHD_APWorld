"""
Skyward Sword HD Client for Archipelago with Ryujinx support.

This client connects to Ryujinx via direct memory access and communicates
with the Archipelago server to enable multiworld randomizer support.
"""

import asyncio
import json
import logging
import os
import struct
import sys
import time
from typing import Optional, Set, Dict, Any

# Add parent directory to path to find Archipelago modules when running as exe
if getattr(sys, 'frozen', False):
    # Running as compiled exe
    bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    # Add Archipelago install directory to path (cross-platform)
    try:
        from platform_utils import get_archipelago_dir
        archipelago_dir = str(get_archipelago_dir())
    except ImportError:
        # Fallback if platform_utils not available
        if sys.platform == "win32":
            archipelago_dir = os.path.join(os.environ.get('PROGRAMDATA', 'C:\\ProgramData'), 'Archipelago')
        elif sys.platform == "linux":
            archipelago_dir = os.path.expanduser("~/.local/share/Archipelago")
        else:  # macOS and other
            archipelago_dir = os.path.expanduser("~/Library/Application Support/Archipelago")
    if os.path.exists(archipelago_dir):
        sys.path.insert(0, archipelago_dir)
else:
    # Running as script - add current directory to find bundled modules
    bundle_dir = os.path.dirname(os.path.abspath(__file__))
    # Add current directory first (for bundled core files in .apworld)
    sys.path.insert(0, bundle_dir)
    # Also try Archipelago folder if available
    archipelago_parent = os.path.dirname(bundle_dir)
    archipelago_dir = os.path.join(archipelago_parent, 'Archipelago')
    if os.path.exists(archipelago_dir):
        sys.path.insert(0, archipelago_dir)

# Disable ModuleUpdate (prevents unnecessary dependency checks)
class DummyModuleUpdate:
    @staticmethod
    def update(*args, **kwargs):
        pass
sys.modules['ModuleUpdate'] = DummyModuleUpdate()

import psutil
import pymem
import pymem.process

# Try to import from bundled modules first, then fall back to system Archipelago
try:
    # First try relative imports (when running from .apworld)
    try:
        from .CommonClient import CommonContext, server_loop, gui_enabled, \
            ClientCommandProcessor, logger, get_base_parser
        from .NetUtils import ClientStatus
    except ImportError:
        # Fall back to absolute imports (when running from Archipelago install)
        from CommonClient import CommonContext, server_loop, gui_enabled, \
            ClientCommandProcessor, logger, get_base_parser
        from NetUtils import ClientStatus
except ImportError as e:
    print(f"ERROR: Cannot import Archipelago modules. Make sure Archipelago is installed.")
    print(f"Import error: {e}")
    print(f"\nTo fix this:")
    print(f"1. Install Archipelago from https://github.com/ArchipelagoMW/Archipelago/releases")
    print(f"2. Or run this script from within the Archipelago folder")
    input("Press Enter to exit...")
    sys.exit(1)

try:
    from .LocationFlags import LOCATION_FLAG_MAP, FLAG_STORY, FLAG_SCENE, FLAG_SPECIAL
    print(f"[Import] Successfully imported LocationFlags from package (.LocationFlags)")
    print(f"[Import] LOCATION_FLAG_MAP has {len(LOCATION_FLAG_MAP)} entries")
except ImportError as e:
    print(f"[Import] Failed to import .LocationFlags: {e}")
    # Fallback if running as standalone
    try:
        from LocationFlags import LOCATION_FLAG_MAP, FLAG_STORY, FLAG_SCENE, FLAG_SPECIAL
        print(f"[Import] Successfully imported LocationFlags from standalone (LocationFlags)")
        print(f"[Import] LOCATION_FLAG_MAP has {len(LOCATION_FLAG_MAP)} entries")
    except ImportError as e2:
        print(f"[Import] Failed to import LocationFlags: {e2}")
        print(f"[Import] LOCATION_FLAG_MAP will be empty - location checking DISABLED")
        LOCATION_FLAG_MAP = {}
        FLAG_STORY = "STORY"
        FLAG_SCENE = "SCENE"
        FLAG_SPECIAL = "SPECIAL"

# Import location table for proper location IDs
try:
    from .Locations import LOCATION_TABLE
except ImportError:
    try:
        from Locations import LOCATION_TABLE
    except ImportError:
        LOCATION_TABLE = {}

# Import item table for item code lookup
try:
    from .Items import ITEM_TABLE
except ImportError:
    try:
        from Items import ITEM_TABLE
    except ImportError:
        ITEM_TABLE = {}

# Import hint system
try:
    from .Hints import HintSystem
except ImportError:
    try:
        from Hints import HintSystem
    except ImportError:
        HintSystem = None

# Import Archipelago item system integration
try:
    from .ItemSystemIntegration import GameItemSystem
except ImportError:
    try:
        from ItemSystemIntegration import GameItemSystem
    except ImportError:
        GameItemSystem = None
        logger.warning("ItemSystemIntegration not found - falling back to direct memory writes")


# Memory signature to find SSHD base address
MEMORY_SIGNATURE = bytes.fromhex("00000000080000004D4F443088BD8101")

# Memory offsets (relative to base address)
# All addresses verified from sshd-cheat-table.CT

# Main pointers
OFFSET_PLAYER = 0x623E680          # Player structure base
OFFSET_FILE_MANAGER = 0x6288408    # Save file manager (actually at 0x5AEAD44 in cheat table)
OFFSET_CURRENT_STAGE = 0x2BF98D8   # Current stage info
OFFSET_NEXT_STAGE = 0x2BF9904      # Next stage info

# Static flag addresses (absolute, not relative to player)
OFFSET_STORY_FLAGS_STATIC = 0x182E1F8   # Static story flags (256 bytes)
OFFSET_SCENE_FLAGS_STATIC = 0x13B100    # Static scene flags (16 bytes)
OFFSET_SCENE_FLAGS = 0x9E4              # Scene flags within player structure
OFFSET_TEMP_FLAGS_STATIC = 0x13B110     # Static temp flags (8 bytes)
OFFSET_ZONE_FLAGS_STATIC = 0x13B118     # Static zone flags (504 bytes)
OFFSET_ITEM_FLAGS_STATIC = 0x12E170     # Static item flags (128 bytes)
OFFSET_DUNGEON_FLAGS_STATIC = 0x12E128  # Static dungeon flags (16 bytes)

# File Manager structure (cheat table shows this at +5AEAD44)
OFFSET_FILE_MANAGER_ACTUAL = 0x5AEAD44  # Actual File Mgr base
OFFSET_FILE_A_FROM_MANAGER = 0x10       # Offset to File A pointer from File Manager
OFFSET_FA_STORY_FLAGS = 0x0             # Story flags in save file (File A)

# Player structure offsets (relative to OFFSET_PLAYER)
OFFSET_POS_X = 0x144               # Player X position
OFFSET_POS_Y = 0x148               # Player Y position
OFFSET_POS_Z = 0x14C               # Player Z position
OFFSET_VELOCITY_X = 0x1E8          # Velocity X
OFFSET_VELOCITY_Y = 0x1EC          # Velocity Y
OFFSET_VELOCITY_Z = 0x1F0          # Velocity Z
OFFSET_ACTION_FLAGS = 0x460        # Action flags
OFFSET_ACTION_FLAGS_MORE = 0x464   # More action flags
OFFSET_GAME_STATE = 0x2BF98A0      # Game state flags (dialogue, cutscene, etc.)
OFFSET_B_WHEEL_EQUIPPED = 0x6408   # B-wheel equipped item
OFFSET_CURRENT_HEALTH = 0x5AF005A  # Current hearts (2 bytes) - from File Mgr->FA structure (CE: base+0x5AF005A)
OFFSET_HEALTH_CAPACITY = 0x5302    # Max hearts (2 bytes)
OFFSET_STAMINA = 0x64D8            # Stamina gauge

# Current Stage Info offsets (relative to OFFSET_CURRENT_STAGE)
OFFSET_STAGE_NAME = 0x0            # Stage name (8 byte string)
OFFSET_STAGE_LAYER = 0x23          # Layer ID
OFFSET_STAGE_ROOM = 0x22           # Room ID
OFFSET_STAGE_ENTRANCE = 0x24       # Entrance ID
OFFSET_STAGE_NIGHT = 0x25          # Night flag

# Scene name to scene flag base address mapping (base-relative offsets for SSHD)
# These are the offsets from base_address where scene flags are stored
# Scene flags are organized by scene in the static scene flag array
SCENE_FLAG_ADDRESSES = {
    "Skyloft": 0x182DF00,              # Skyloft scene flags (base-relative)
    "Sky": 0x182DF10,                  # Sky scene flags
    "Sealed Grounds": 0x182DF20,       # Sealed Grounds
    "Faron Woods": 0x182DF30,          # Faron Woods
    "Lake Floria": 0x182DF40,          # Lake Floria
    "Skyview": 0x182DF50,              # Skyview Temple
    "Eldin Volcano": 0x182DF60,        # Eldin Volcano
    "Earth Temple": 0x182DF70,         # Earth Temple
    "Lanayru Desert": 0x182DF80,       # Lanayru Desert
    "Lanayru Mining Facility": 0x182DF90,  # Lanayru Mining Facility
    "Ancient Cistern": 0x182DFA0,      # Ancient Cistern
    "Sandship": 0x182DFB0,             # Sandship
    "Fire Sanctuary": 0x182DFC0,       # Fire Sanctuary
    "Sky Keep": 0x182DFD0,             # Sky Keep
}

# Story flags base address (base-relative)
STORY_FLAGS_BASE = OFFSET_STORY_FLAGS_STATIC

# Scene flags base address (base-relative)
SCENE_FLAGS_BASE = OFFSET_SCENE_FLAGS_STATIC

# Stage name mapping (internal codes to friendly names)
STAGE_NAMES = {
    "F000": "Skyloft",
    "F001r": "Knight Academy",
    "F002r": "Bazaar",
    "F004r": "Sparring Hall",
    "F005r": "Isle of Songs",
    "F006r": "Lumpy Pumpkin",
    "F007r": "Batreaux's House",
    "F008r": "Bamboo Island",
    "F009r": "Beedle's Airshop",
    "F010r": "Peatrice's House",
    "F012r": "Orielle & Parrow's House",
    "F013r": "Pippit's House",
    "F014r": "Kukiel's House",
    "F015r": "Potion Shop",
    "F016r": "Scrap Shop",
    "F017r": "Fortune Teller",
    "F018r": "Gear Shop",
    "F019r": "Item Check",
    "F020": "The Sky",
    "F021": "Thunderhead",
    "F023": "Inside the Thunderhead",
    "F100": "Faron Woods",
    "F101": "Deep Woods",
    "F102": "Lake Floria",
    "F103": "Flooded Faron Woods",
    "F200": "Eldin Volcano",
    "F201": "Volcano Summit",
    "F210": "Mogma Turf",
    "F211": "Thrill Digger",
    "F300": "Lanayru Desert",
    "F301": "Lanayru Sand Sea",
    "F302": "Lanayru Gorge",
    "F303": "Lanayru Caves",
    "D000": "Skyview Temple",
    "D100": "Earth Temple",
    "D200": "Lanayru Mining Facility",
    "D201": "Temple of Time",
    "D300": "Ancient Cistern",
    "D301": "Sandship",
    "D302": "Pirate Stronghold",
    "D003": "Fire Sanctuary",
    "D003_1": "Fire Sanctuary (Underwater)",
    "S000": "Sealed Grounds",
    "S100": "Hylia's Temple",
    "S200": "Sealed Temple",
    "B000": "Sky Keep",
    "B100": "Lanayru Gorge Silent Realm",
    "B101": "Faron Silent Realm",
    "B102": "Eldin Silent Realm",
    "B103": "Skyloft Silent Realm",
}


class RyujinxMemoryError(Exception):
    """Exception raised for Ryujinx memory access errors."""
    pass


class RyujinxMemoryReader:
    """
    Class to handle memory reading/writing for Ryujinx emulator.
    
    This provides direct access to SSHD's memory through Ryujinx's process.
    """
    
    def __init__(self):
        self.pm: Optional[pymem.Pymem] = None
        self.base_address: Optional[int] = None
        self.connected = False
        
    def connect(self) -> bool:
        """
        Connect to the Ryujinx process.
        
        Returns:
            True if successfully connected, False otherwise
        """
        try:
            # Find Ryujinx process (cross-platform)
            ryujinx_process = None
            
            # Process names by OS
            if sys.platform == "win32":
                process_names = ["Ryujinx.exe"]
            elif sys.platform == "linux":
                process_names = ["Ryujinx"]
            elif sys.platform == "darwin":  # macOS
                process_names = ["Ryujinx"]
            else:
                process_names = ["Ryujinx.exe", "Ryujinx"]  # Try both as fallback
            
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] in process_names:
                    ryujinx_process = proc
                    break
            
            if not ryujinx_process:
                expected_names = " or ".join(f"'{name}'" for name in process_names)
                logger.info(f"Ryujinx process ({expected_names}) not found. Please start Ryujinx.")
                return False
            
            # Open process
            self.pm = pymem.Pymem()
            self.pm.open_process_from_id(ryujinx_process.pid)
            
            logger.info(f"Connected to Ryujinx (PID: {ryujinx_process.pid})")
            self.connected = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Ryujinx: {e}")
            return False
    
    async def find_base_address(self) -> bool:
        """
        Find the SSHD base address by scanning memory for the signature.
        
        This can take several seconds as it scans the entire process memory.
        Runs in a thread pool to avoid blocking the GUI.
        
        Returns:
            True if base address found, False otherwise
        """
        if not self.connected or not self.pm:
            logger.error("Not connected to Ryujinx")
            return False
        
        logger.info("Scanning memory for SSHD signature... (this may take 8-10 seconds)")
        
        try:
            # Run the heavy scanning in a thread pool to not block the GUI
            loop = asyncio.get_event_loop()
            logger.debug("Starting memory scan in thread pool...")
            result = await loop.run_in_executor(None, self._scan_memory_sync)
            logger.debug(f"Memory scan completed with result: {result}")
            
            if result:
                logger.info(f"Scan successful - base address: 0x{self.base_address:X}")
            else:
                logger.error("Scan failed - signature not found")
            
            return result
        except Exception as e:
            logger.error(f"Exception during memory scan: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _scan_memory_sync(self) -> bool:
        """Synchronous memory scanning using VirtualQueryEx for precise region enumeration."""
        try:
            import ctypes
            
            start_time = time.time()
            print(f"[DEBUG] Starting VirtualQueryEx-based memory scan")
            
            # Windows memory constants
            MEM_COMMIT = 0x1000
            # Readable page protections (excludes PAGE_NOACCESS=0x01, PAGE_EXECUTE=0x10)
            READABLE_PROTECTIONS = {0x02, 0x04, 0x08, 0x20, 0x40, 0x80}
            PAGE_GUARD = 0x100

            # 64-bit MEMORY_BASIC_INFORMATION (48 bytes on Windows 10 x64)
            class MEMORY_BASIC_INFORMATION(ctypes.Structure):
                _fields_ = [
                    ("BaseAddress",      ctypes.c_uint64),
                    ("AllocationBase",   ctypes.c_uint64),
                    ("AllocationProtect",ctypes.c_uint32),
                    ("__alignment1",     ctypes.c_uint32),  # PartitionId+pad on Win10 1703+
                    ("RegionSize",       ctypes.c_uint64),
                    ("State",            ctypes.c_uint32),
                    ("Protect",          ctypes.c_uint32),
                    ("Type",             ctypes.c_uint32),
                    ("__alignment2",     ctypes.c_uint32),
                ]

            kernel32 = ctypes.windll.kernel32
            process_handle = self.pm.process_handle
            chunk_size = 1024 * 1024  # 1 MB
            max_address = 0x7FFFFFFFFFFF
            address = 0x10000
            chunks_scanned = 0
            regions_scanned = 0
            mbi = MEMORY_BASIC_INFORMATION()

            while address < max_address:
                # Query exact boundaries and attributes of the region at 'address'
                result = kernel32.VirtualQueryEx(
                    process_handle,
                    ctypes.c_uint64(address),
                    ctypes.byref(mbi),
                    ctypes.sizeof(mbi)
                )

                if result == 0:
                    address += 0x1000  # query failed, advance one page
                    continue

                region_base = mbi.BaseAddress
                region_size = mbi.RegionSize

                if region_size == 0:
                    address += 0x1000
                    continue

                # Only read committed, readable pages
                base_protect = mbi.Protect & 0xFF  # strip modifier flags
                is_committed = (mbi.State == MEM_COMMIT)
                is_readable  = (base_protect in READABLE_PROTECTIONS) and not (mbi.Protect & PAGE_GUARD)

                if is_committed and is_readable:
                    regions_scanned += 1
                    region_end = region_base + region_size
                    scan_pos   = region_base

                    while scan_pos < region_end:
                        to_read = min(chunk_size, region_end - scan_pos)
                        try:
                            data = self.pm.read_bytes(scan_pos, to_read)
                            chunks_scanned += 1

                            if chunks_scanned % 10 == 0:
                                print(f"[DEBUG] Scanned {chunks_scanned} chunks, address: 0x{scan_pos:X}")

                            sig_offset = data.find(MEMORY_SIGNATURE)
                            if sig_offset != -1:
                                signature_address = scan_pos + sig_offset
                                # Base address IS where the signature starts
                                # (matches Lua: baseAddress = foundList.Address[0])
                                potential_base = signature_address
                                elapsed = time.time() - start_time
                                print(f"[SUCCESS] Found SSHD base address: 0x{potential_base:X}")
                                print(f"[INFO] Signature at 0x{signature_address:X}, region protect={mbi.Protect:#x} type={mbi.Type:#x}")
                                print(f"[SCAN] Took {elapsed:.1f}s, {chunks_scanned} chunks in {regions_scanned} regions")
                                self.base_address = potential_base
                                logger.info(f"Found SSHD base address: 0x{self.base_address:X} (took {elapsed:.1f}s)")
                                return True
                        except Exception:
                            pass  # skip unreadable sub-chunks within this region

                        scan_pos += to_read

                # Advance precisely to next region — no large arbitrary jumps
                address = region_base + region_size

            print(f"[FAIL] Signature not found after {chunks_scanned} chunks in {regions_scanned} regions")
            logger.error("Could not find SSHD signature in memory")
            return False

        except Exception as e:
            print(f"[ERROR] Exception during scan: {e}")
            logger.error(f"Error scanning memory: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def read_float(self, offset: int) -> Optional[float]:
        """Read a float from memory at base_address + offset."""
        if not self.base_address or not self.pm:
            return None
        try:
            data = self.pm.read_bytes(self.base_address + offset, 4)
            return struct.unpack('<f', data)[0]
        except Exception as e:
            # Suppress repetitive error logging - normal when memory isn't loaded yet
            return None
    
    def read_int(self, offset: int) -> Optional[int]:
        """Read a 32-bit integer from memory at base_address + offset."""
        if not self.base_address or not self.pm:
            return None
        try:
            data = self.pm.read_bytes(self.base_address + offset, 4)
            return struct.unpack('<I', data)[0]
        except Exception as e:
            logger.debug(f"Error reading int at 0x{offset:X}: {e}")
            return None
    
    def read_short(self, offset: int) -> Optional[int]:
        """Read a 16-bit integer from memory at base_address + offset."""
        if not self.base_address or not self.pm:
            return None
        try:
            data = self.pm.read_bytes(self.base_address + offset, 2)
            return struct.unpack('<H', data)[0]
        except Exception as e:
            logger.debug(f"Error reading short at 0x{offset:X}: {e}")
            return None
    
    def read_byte(self, offset: int) -> Optional[int]:
        """Read a single byte from memory at base_address + offset."""
        if not self.base_address or not self.pm:
            return None
        try:
            return self.pm.read_uchar(self.base_address + offset)
        except Exception as e:
            # Suppress repetitive error logging - these are normal when memory isn't loaded yet
            return None
    
    def read_string(self, offset: int, length: int = 32) -> Optional[str]:
        """Read a null-terminated string from memory."""
        if not self.base_address or not self.pm:
            return None
        try:
            data = self.pm.read_bytes(self.base_address + offset, length)
            # Find null terminator
            null_pos = data.find(b'\x00')
            if null_pos != -1:
                data = data[:null_pos]
            return data.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.debug(f"Error reading string at 0x{offset:X}: {e}")
            return None
    
    def read_pointer(self, offset: int) -> Optional[int]:
        """Read a pointer (64-bit address) from memory."""
        if not self.base_address or not self.pm:
            return None
        try:
            data = self.pm.read_bytes(self.base_address + offset, 8)
            return struct.unpack('<Q', data)[0]  # Little-endian 64-bit
        except Exception as e:
            # Suppress repetitive error logging - normal when memory isn't loaded yet
            return None
    
    def read_bytes(self, offset: int, length: int) -> Optional[bytes]:
        """Read raw bytes from memory at base_address + offset."""
        if not self.base_address or not self.pm:
            return None
        try:
            return self.pm.read_bytes(self.base_address + offset, length)
        except Exception as e:
            logger.debug(f"Error reading {length} bytes at 0x{offset:X}: {e}")
            return None
    
    def write_float(self, offset: int, value: float) -> bool:
        """Write a float to memory at base_address + offset."""
        if not self.base_address or not self.pm:
            return False
        try:
            data = struct.pack('<f', value)
            self.pm.write_bytes(self.base_address + offset, data, len(data))
            return True
        except Exception as e:
            logger.debug(f"Error writing float at 0x{offset:X}: {e}")
            return False
    
    def write_int(self, offset: int, value: int) -> bool:
        """Write a 32-bit integer to memory at base_address + offset."""
        if not self.base_address or not self.pm:
            return False
        try:
            data = struct.pack('<I', value)
            self.pm.write_bytes(self.base_address + offset, data, len(data))
            return True
        except Exception as e:
            logger.debug(f"Error writing int at 0x{offset:X}: {e}")
            return False
    
    def write_byte(self, offset: int, value: int) -> bool:
        """Write a single byte to memory at base_address + offset."""
        if not self.base_address or not self.pm:
            return False
        try:
            self.pm.write_uchar(self.base_address + offset, value)
            return True
        except Exception as e:
            logger.debug(f"Error writing byte at 0x{offset:X}: {e}")
            return False
    
    def write_short(self, offset: int, value: int) -> bool:
        """Write a 16-bit short to memory at base_address + offset."""
        if not self.base_address or not self.pm:
            return False
        try:
            data = struct.pack('<H', value)
            self.pm.write_bytes(self.base_address + offset, data, len(data))
            return True
        except Exception as e:
            logger.debug(f"Error writing short at 0x{offset:X}: {e}")
            return False


class SSHDClientCommandProcessor(ClientCommandProcessor):
    """Command processor for SSHD-specific commands."""
    
    def __init__(self, ctx: CommonContext):
        super().__init__(ctx)
    
    def _cmd_sshd(self):
        """Show SSHD client status."""
        if isinstance(self.ctx, SSHDContext):
            logger.info(f"Connected to Ryujinx: {self.ctx.memory.connected}")
            if self.ctx.memory.base_address:
                logger.info(f"Base address: 0x{self.ctx.memory.base_address:X}")
            logger.info(f"Locations checked: {len(self.ctx.checked_locations)}")
        else:
            logger.warning("Not connected to SSHD context")
    
    def _cmd_hints(self):
        """Show all received hints."""
        if isinstance(self.ctx, SSHDContext) and self.ctx.hints:
            hints = self.ctx.hints.get_all_hints()
            if hints:
                logger.info(f"\n=== Hints ({len(hints)}) ===")
                for location_id, hint_text in hints:
                    revealed = "[READ]" if self.ctx.hints.is_revealed(location_id) else "[NEW]"
                    logger.info(f"{revealed} {hint_text}")
            else:
                logger.info("No hints received yet.")
        else:
            logger.warning("Hint system not available")


class SSHDContext(CommonContext):
    """
    Main context for SSHD client.
    
    Handles connection to both Archipelago server and Ryujinx emulator.
    """
    
    command_processor = SSHDClientCommandProcessor
    tags = {"AP"}  # Game client tags (not TextOnly)
    game = "Skyward Sword HD"
    items_handling = 0b111  # Full remote item handling
    
    def __init__(self, server_address: Optional[str], password: Optional[str]):
        super().__init__(server_address, password)
        
        self.memory = RyujinxMemoryReader()
        self.checked_locations: Set[int] = set()
        self.item_queue: list = []  # Items waiting to be given
        self.location_to_item: Dict[str, Dict] = {}  # Maps location names to item info from patch
        self.item_to_location: Dict[int, int] = {}  # Maps item code -> location code for tracking
        self.slot_data: dict = {}  # Slot data from server containing location-to-item mapping
        
        # Debug: Verify tags are set correctly
        logger.info(f"SSHDContext initialized with tags: {self.tags}")
        logger.info(f"Game: {self.game}")
        logger.info(f"Items handling: {self.items_handling}")
        
        # Initialize hint system
        self.hints = HintSystem() if HintSystem else None
        
        # Initialize Archipelago item system (buffer-based with animations)
        self.game_item_system = None
        
        # Progressive item counters
        self.progressive_counts = {
            "Progressive Sword": 0,
            "Progressive Bow": 0,
            "Progressive Slingshot": 0,
            "Progressive Beetle": 0,
            "Progressive Mitts": 0,
            "Progressive Bug Net": 0,
            "Progressive Wallet": 0,
            "Progressive Pouch": 0,
        }
        
        # Game state tracking
        self.current_stage: Optional[str] = None
        self.last_stage: Optional[str] = None
        self.last_hearts: Optional[int] = None
        self.last_death_link: float = 0.0   # For DeathLink echo prevention
        self.delivered_item_count: int = 0  # Items actually given (persisted across restarts)
        self.connection_time: float = 0.0   # When we connected (to avoid false death on startup)
        self.slot_options: Dict[str, Any] = {}  # Player options from slot data
        self.killed_by_deathlink: bool = False  # Flag to prevent sending death when killed by death link
        
        # Location checking via custom flags
        self.previous_custom_flags: Dict[int, int] = {}  # custom_flag_id -> last_state (0 or 1)
        self.custom_flag_to_location: Dict[int, int] = {}  # custom_flag_id -> location_code
        self.location_to_custom_flag: Dict[int, int] = {}  # location_code -> custom_flag_id (for vanilla pickups)
        
    async def server_auth(self, password_requested: bool = False):
        """Authenticate with the Archipelago server."""
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        await self.get_username()
        await self.send_connect()
    
    async def connection_closed(self):
        """Handle disconnection from server."""
        await super().connection_closed()
        logger.info("Connection to Archipelago server closed")

    # Progress persistence (prevents re-giving items on client restart)
    def _get_save_file(self) -> str:
        import os
        return os.path.join(os.path.expanduser("~"), "sshd_ap_progress.json")

    def load_progress(self):
        """Load persisted item delivery count for the current slot."""
        import json, os
        save_file = self._get_save_file()
        try:
            if os.path.exists(save_file) and self.auth:
                with open(save_file, "r") as f:
                    data = json.load(f)
                count = data.get(self.auth, 0)
                if count > self.delivered_item_count:
                    self.delivered_item_count = count
                    logger.info(f"[Progress] Restored delivery count: {self.delivered_item_count} items already given for {self.auth}")
        except Exception as e:
            logger.debug(f"[Progress] Could not load progress file: {e}")

    def save_progress(self):
        """Persist item delivery count so restarts don't re-give items."""
        import json, os
        save_file = self._get_save_file()
        try:
            existing: dict = {}
            if os.path.exists(save_file):
                with open(save_file, "r") as f:
                    existing = json.load(f)
            if self.auth:
                existing[self.auth] = self.delivered_item_count
            with open(save_file, "w") as f:
                json.dump(existing, f)
        except Exception as e:
            logger.debug(f"[Progress] Could not save progress: {e}")

    
    def on_package(self, cmd: str, args: dict):
        """Handle incoming packages from the server."""
        # IMPORTANT: Call parent first so CommonContext sets up multiworld and other attributes
        super().on_package(cmd, args)
        
        if cmd == "Connected":
            # Server confirmed connection - validate slot data and build location mapping
            slot_data = args.get("slot_data", {})
            
            # Store slot_data for use in building the item-to-location mapping
            self.slot_data = slot_data
            
            # Check world version compatibility
            server_version = slot_data.get("world_version", [0, 0, 0])
            if server_version[0] != 0 or server_version[1] != 1:
                logger.warning(f"World version mismatch! Client expects 0.1.x, server has {server_version}")
                logger.warning("The game may not work correctly. Please update your client or regenerate your seed.")
            
            # Store slot options for reference
            self.slot_options = {}
            for key, value in slot_data.items():
                if key.startswith("option_"):
                    option_name = key[7:]  # Remove "option_" prefix
                    self.slot_options[option_name] = value
            
            logger.info(f"Connected to Archipelago as {self.auth}")
            logger.info(f"Loaded {len(self.slot_options)} player options from slot data")
            
            # Build the item-to-location mapping now that we have slot_data
            self.item_to_location = self.build_item_to_location_map()
            
            # Load custom flag to location mapping for location detection
            custom_flag_mapping = slot_data.get("custom_flag_to_location", {})
            if custom_flag_mapping:
                # Convert string keys back to integers (JSON serialization converts int keys to strings)
                self.custom_flag_to_location = {int(k): v for k, v in custom_flag_mapping.items()}
                logger.info(f"Loaded custom flag mapping with {len(self.custom_flag_to_location)} flags")
            else:
                logger.warning("No custom flag mapping found in slot data - location detection disabled")
            
            # Load location to custom flag mapping for vanilla item pickups
            location_to_flag_mapping = slot_data.get("location_to_custom_flag", {})
            if location_to_flag_mapping:
                # Convert string keys back to integers
                self.location_to_custom_flag = {int(k): v for k, v in location_to_flag_mapping.items()}
                logger.info(f"Loaded {len(self.location_to_custom_flag)} location -> flag mappings for vanilla pickups")
            else:
                logger.warning("No location→flag mapping found - vanilla pickups disabled")

            # Enable DeathLink if the player configured it
            death_link_enabled = slot_data.get("option_death_link", 0)  # Options use "option_" prefix
            if death_link_enabled:
                self.tags.add("DeathLink")
                logger.info("DeathLink enabled! Deaths will be shared with other players.")
                # Send ConnectUpdate to notify server of new tags
                asyncio.create_task(self.send_msgs([{"cmd": "ConnectUpdate", "tags": list(self.tags)}]))
                logger.debug(f"Sent ConnectUpdate with tags: {list(self.tags)}")
            else:
                self.tags.discard("DeathLink")
                logger.info("DeathLink disabled.")

            # Load persisted delivery count so we don't re-give items on reconnect
            self.load_progress()
            
        elif cmd == "ReceivedItems":
            # Received items from other players
            start_index = args.get("index", 0)
            items_list = args.get("items", [])
            for i, network_item in enumerate(items_list):
                item_global_index = start_index + i

                # Skip items already delivered in a previous session
                if item_global_index < self.delivered_item_count:
                    logger.debug(f"[ReceivedItems] Skipping already-delivered item at index {item_global_index}")
                    continue

                item_id = network_item.item
                location_id = network_item.location
                location_player = network_item.player  # Player whose location was checked
                
                # Look up names - item is from OUR game (SSHD), location is from sender's game
                item_name = self.item_names.lookup_in_slot(item_id, self.slot)
                location_name = self.location_names.lookup_in_slot(location_id, location_player)
                try:
                    sender_name = self.player_names[location_player]
                except (KeyError, TypeError):
                    sender_name = f"Player {location_player}"
                
                logger.debug(f"[ReceivedItems] item_id={item_id}, item_name='{item_name}', location='{location_name}', from={sender_name}")
                
                # Add to queue to be given in-game
                self.item_queue.append({
                    "id": item_id,
                    "name": item_name,
                    "location": location_name,
                    "location_player": location_player,  # Who found it
                    "player_name": sender_name,
                    "index": start_index + i,
                })
        
        elif cmd == "LocationInfo":
            # Information about locations - used for hints
            if self.hints:
                for location_info in args.get("locations", []):
                    location_id = location_info.get("location")
                    item_id = location_info.get("item")
                    player_id = location_info.get("player")
                    
                    # Get names using lookup_in_slot helpers
                    location_name = self.location_names.lookup_in_slot(location_id, player_id)
                    item_name = self.item_names.lookup_in_slot(item_id, player_id)
                    try:
                        player_name = self.player_names[player_id]
                    except (KeyError, TypeError):
                        player_name = f"Player {player_id}"
                    
                    # Format and store hint
                    is_local = (player_id == self.slot)
                    hint_text = self.hints.format_hint(location_name, item_name, player_name, is_local)
                    self.hints.add_hint(location_id, hint_text)
                    
                    logger.info(f"Received hint: {hint_text}")
        
        elif cmd == "Bounced":
            # Bounced packet - used for DeathLink
            logger.debug(f"[Bounced] Received bounced packet: {args}")
            tags = args.get("tags", [])
            logger.debug(f"[Bounced] Tags: {tags}, DeathLink in tags: {'DeathLink' in tags}")
            if "DeathLink" in tags:
                data = args.get("data", {})
                logger.debug(f"[Bounced] DeathLink data: {data}")
                # Prevent echo: ignore if this bounce came from our own death
                if data.get("time", 0) != self.last_death_link:
                    logger.info(f"[Bounced] Triggering on_deathlink with data: {data}")
                    self.on_deathlink(data)
                else:
                    logger.debug(f"[Bounced] Ignoring echo (time={data.get('time')} == last_death_link={self.last_death_link})")
    
    def give_item_to_player(self, item_name: str, item_id: int) -> bool:
        """
        Give an item to the player using the game's native item system.
        
        Uses a memory buffer that the game monitors every frame. When items are written
        to the buffer, the game spawns them with proper animations, models, and sound effects.
        
        Returns True if successful, False if failed.
        """
        if not self.memory.connected or not self.memory.base_address:
            logger.debug(f"Cannot give item: not connected to game")
            return False
        
        logger.debug(f"[give_item_to_player] Received item_name='{item_name}', item_id={item_id}")
        
        # Handle progressive items - compute target tier WITHOUT incrementing yet.
        # Counter only advances on a successful give to prevent wrong-tier retries.
        actual_item_name = item_name
        is_progressive = item_name in self.progressive_counts
        next_count = (self.progressive_counts.get(item_name, 0) + 1) if is_progressive else 0
        
        if is_progressive:
            count = next_count
            if item_name == "Progressive Sword":
                # Tier 1-4: Goddess Longsword → White Sword → Master Sword → True Master Sword
                sword_tiers = ["Goddess Longsword", "Goddess White Sword", "Master Sword", "True Master Sword"]
                actual_item_name = sword_tiers[min(count - 1, 3)]
                logger.info(f"Progressive Sword #{count} -> {actual_item_name}")
            elif item_name == "Progressive Bow":
                # Tier 1: base Bow (game item 19), 2: Iron Bow, 3: Sacred Bow
                bow_tiers = ["Progressive Bow", "Iron Bow", "Sacred Bow"]
                actual_item_name = bow_tiers[min(count - 1, 2)]
                logger.info(f"Progressive Bow #{count} -> {actual_item_name}")
            elif item_name == "Progressive Slingshot":
                # Tier 1: base Slingshot (game item 52), 2: Scattershot
                slingshot_tiers = ["Progressive Slingshot", "Scattershot"]
                actual_item_name = slingshot_tiers[min(count - 1, 1)]
                logger.info(f"Progressive Slingshot #{count} -> {actual_item_name}")
            elif item_name == "Progressive Beetle":
                # Tier 1: base Beetle (game item 53), 2: Hook, 3: Quick, 4: Tough
                beetle_tiers = ["Progressive Beetle", "Hook Beetle", "Quick Beetle", "Tough Beetle"]
                actual_item_name = beetle_tiers[min(count - 1, 3)]
                logger.info(f"Progressive Beetle #{count} -> {actual_item_name}")
            elif item_name == "Progressive Mitts":
                # Tier 1: base Mitts (game item 56), 2: Mogma Mitts
                mitts_tiers = ["Progressive Mitts", "Mogma Mitts"]
                actual_item_name = mitts_tiers[min(count - 1, 1)]
                logger.info(f"Progressive Mitts #{count} -> {actual_item_name}")
            elif item_name == "Progressive Bug Net":
                # Tier 1: base Bug Net (game item 71), 2: Big Bug Net
                net_tiers = ["Progressive Bug Net", "Big Bug Net"]
                actual_item_name = net_tiers[min(count - 1, 1)]
                logger.info(f"Progressive Bug Net #{count} -> {actual_item_name}")
            elif item_name == "Progressive Wallet":
                # Tier 1: Medium Wallet (game item 108), 2: Big, 3: Giant, 4: Tycoon
                wallet_tiers = ["Progressive Wallet", "Big Wallet", "Giant Wallet", "Tycoon Wallet"]
                actual_item_name = wallet_tiers[min(count - 1, 3)]
                logger.info(f"Progressive Wallet #{count} -> {actual_item_name}")
            elif item_name == "Progressive Pouch":
                # All tiers give a Pouch Expansion (game item 113)
                actual_item_name = "Pouch Expansion"
                logger.info(f"Progressive Pouch #{count} -> {actual_item_name}")
        
        # Try using the new item system with animations
        if GameItemSystem:
            try:
                # Initialize on first use
                if not self.game_item_system:
                    self.game_item_system = GameItemSystem(self.memory)
                
                # Use the integrated system (spawns items with animations)
                success = self.game_item_system.give_item_by_name(actual_item_name)
                if success:
                    # Only commit the progressive counter increment on success
                    # so retries don't skip tiers
                    if is_progressive:
                        self.progressive_counts[item_name] = next_count
                    logger.info(f"Gave {actual_item_name} with animation!")
                else:
                    logger.warning(f"Failed to give {actual_item_name} via item system")
                return success
            except Exception as e:
                logger.warning(f"Item system error for {actual_item_name}: {e}")
                return False
        else:
            logger.error("GameItemSystem not available. Cannot give item.")
            return False

    async def ryujinx_connection_task(self):
        """Background task to maintain connection to Ryujinx."""
        while not self.exit_event.is_set():
            try:
                # Try to connect if not connected
                if not self.memory.connected:
                    if self.memory.connect():
                        # Connection successful, find base address
                        if not await self.memory.find_base_address():
                            logger.error("Failed to find SSHD in memory. Is the game running?")
                            self.memory.connected = False
                        else:
                            # Set connection time to prevent false death detection on startup
                            self.connection_time = time.time()
                            logger.debug(f"Connection time set to {self.connection_time}")
                    
                    # Wait before retrying
                    await asyncio.sleep(5)
                    continue
                
                # Connection established, update game state
                await self.update_game_state()
                await asyncio.sleep(0.1)  # Update 10 times per second
                
            except Exception as e:
                logger.error(f"Error in Ryujinx connection task: {e}")
                self.memory.connected = False
                await asyncio.sleep(5)
    
    async def update_game_state(self):
        """
        Read game state from memory and check for location completions.
        
        This is called frequently to monitor game progress.
        """
        if not self.memory.connected or not self.memory.base_address:
            return
        
        try:
            # Verify game is loaded by reading stage name
            stage_name = self.memory.read_string(OFFSET_CURRENT_STAGE + OFFSET_STAGE_NAME, 16)
            if not stage_name or len(stage_name) == 0:
                # Game not loaded yet (title screen, loading, etc.)
                return
            
            # Update current stage
            if stage_name != self.current_stage:
                logger.info(f"Entered stage: {stage_name}")
                self.current_stage = stage_name
            
            # Give queued items to player
            if self.item_queue:
                item_data = self.item_queue[0]
                if self.give_item_to_player(item_data["name"], item_data["id"]):
                    # Successfully gave item
                    player_name = item_data.get("player_name", "another player")
                    location_name = item_data.get("location", "unknown location")
                    is_own_item = (item_data.get("location_player") == self.slot)
                    
                    if not is_own_item:
                        # Received item from another player
                        logger.info(f"Received {item_data['name']} from {player_name} ({location_name})")
                    else:
                        # Received own item
                        logger.info(f"Received {item_data['name']} ({location_name})")
                    
                    # Remove from queue and persist delivery count
                    self.item_queue.pop(0)
                    self.delivered_item_count += 1
                    self.save_progress()
            
            # Check for death (for death link)
            current_health = self.memory.read_short(OFFSET_CURRENT_HEALTH)
            if current_health is not None:
                # Skip death detection for 10 seconds after connection to avoid false positives
                time_since_connect = time.time() - self.connection_time
                if time_since_connect > 10.0:
                    # Player just died if health went to 0 (from any positive value OR if we had None before)
                    if current_health == 0 and (self.last_hearts is None or self.last_hearts > 0):
                        # Player just died - but skip sending if we killed them via death link
                        if self.killed_by_deathlink:
                            logger.debug("Death detected, but caused by receiving death link - not sending")
                            self.killed_by_deathlink = False  # Clear flag
                        elif "DeathLink" in self.tags:
                            stage_name = STAGE_NAMES.get(self.current_stage, self.current_stage or "Skyloft")
                            await self.send_death(f"{self.auth} died in {stage_name}")
                self.last_hearts = current_health
            
            # Check for completed locations using custom flags or LocationFlags.py data
            if self.custom_flag_to_location:
                # Use custom flag system (preferred for SSHD)
                await self.check_custom_flags()
            elif LOCATION_FLAG_MAP:
                # Fallback to LocationFlags.py - but only if static memory is accessible
                # Test if we can read the first static flag address to avoid error spam
                test_read = self.memory.read_byte(OFFSET_SCENE_FLAGS_STATIC)
                if test_read is not None:
                    # NOTE: FLAG_SCENE should work (uses SSHD addresses), but FLAG_STORY has Wii addresses
                    await self.check_all_locations()
            
            # Send any newly checked locations to server
            new_locations = self.checked_locations.difference(self.missing_locations)
            if new_locations:
                await self.send_msgs([{
                    "cmd": "LocationChecks",
                    "locations": list(new_locations)
                }])
                
                # Check if "Defeat Demise" location (2773238) was just checked - this means victory!
                DEFEAT_DEMISE_LOCATION = 2773238
                if DEFEAT_DEMISE_LOCATION in new_locations:
                    logger.info("=== 🎉 VICTORY! Demise defeated - sending goal completion to server ===")
                    await self.send_msgs([{
                        "cmd": "StatusUpdate",
                        "status": ClientStatus.CLIENT_GOAL
                    }])
                    # Server will automatically release all remaining items if auto-release is enabled
                    
        except Exception as e:
            logger.error(f"Error updating game state: {e}")
    
    async def check_custom_flags(self):
        """Check custom flags for location completion (SSHD-specific)."""
        if not self.memory.connected or not self.memory.base_address:
            return
        
        # Custom flags use the game's sceneflag/dungeonflag system
        # Each flag is a single bit that gets set when a location is checked
        # The mapping from flag ID to location code is provided in slot_data
        
        # Get FILE_MGR pointer to access sceneflags/dungeonflags
        file_mgr_ptr = self.memory.read_pointer(OFFSET_FILE_MANAGER)
        if not file_mgr_ptr:
            return
        
        # FILE_MGR.FA is at offset 0x10 from FILE_MGR base
        # sceneflags are at FILE_MGR.FA + 0x0
        # dungeonflags are at FILE_MGR.FA + some offset (need to determine exact)
        # For now, use the OFFSET_SCENE_FLAGS_STATIC which points to static sceneflags
        
        for flag_id, location_code in self.custom_flag_to_location.items():
            # Skip if already checked
            if location_code in self.checked_locations:
                continue
            
            # Unpack the custom flag from item.rs unpacking logic
            # Custom flags in sshd-rando use sceneindex and flag number
            # The flag_id itself encodes both: upper bits = scene, lower bits = flag
            # Based on item.rs: flag_space_trigger determines if it's sceneflag (0) or dungeonflag (1)
            
            # For custom flags, the encoding is:
            # - Bits 0-6 (0x7F): flag number within the scene
            # - Bits 7-8: scene index (transformed to one of 6, 13, 16, 19)
            # - Bit 9: flag_space_trigger (0=sceneflag, 1=dungeonflag)
            
            flag_num = flag_id & 0x7F  # Lower 7 bits
            scene_idx_raw = (flag_id >> 7) & 0x03  # Bits 7-8
            flag_space_trigger = (flag_id >> 9) & 0x01  # Bit 9
            
            # Transform scene index like in item.rs
            scene_idx_map = {0: 6, 1: 13, 2: 16, 3: 19}
            sceneindex = scene_idx_map.get(scene_idx_raw, 6)
            
            # Calculate bit position within flag storage
            # Flags are stored as array[sceneindex][upper_flag] with bits in lower_flag
            upper_flag = (flag_num & 0xF0) >> 4  # Nibble position (0-15)
            lower_flag = flag_num & 0x0F  # Bit position within nibble (0-15)
            
            try:
                # Read the appropriate flag byte (need to add base_address!)
                if flag_space_trigger == 0:
                    # Scene flag - stored at base + OFFSET_SCENE_FLAGS_STATIC + (sceneindex * 16) + upper_flag
                    flag_addr = self.memory.base_address + OFFSET_SCENE_FLAGS_STATIC + (sceneindex * 16) + upper_flag
                    current_byte = self.memory.read_byte(flag_addr)
                else:
                    # Dungeon flag - stored at base + OFFSET_DUNGEON_FLAGS_STATIC + (sceneindex * 16) + upper_flag  
                    flag_addr = self.memory.base_address + OFFSET_DUNGEON_FLAGS_STATIC + (sceneindex * 16) + upper_flag
                    current_byte = self.memory.read_byte(flag_addr)
                
                if current_byte is not None:
                    # Check if the specific bit is set
                    flag_state = (current_byte >> lower_flag) & 0x1
                    previous_state = self.previous_custom_flags.get(flag_id, 0)
                    
                    if flag_state == 1 and previous_state == 0:
                        # Flag was just set - location completed!
                        self.checked_locations.add(location_code)
                        # Get location name for logging
                        location_name = self.location_names.lookup_in_slot(location_code, self.slot)
                        logger.info(f"Checked {location_name}")
                    
                    self.previous_custom_flags[flag_id] = flag_state
                    
            except Exception as e:
                logger.debug(f"Error checking custom flag {flag_id}: {e}")
    
    async def check_all_locations(self):
        """Check all locations using LocationFlags.py data (Wii addresses - may not work on Switch)."""
        if not self.memory.connected or not self.memory.base_address:
            return
        
        for location_name, (flag_type, flag_bit, flag_value, scene_or_addr) in LOCATION_FLAG_MAP.items():
            # Get proper location ID from LOCATION_TABLE
            if location_name in LOCATION_TABLE:
                location_id = LOCATION_TABLE[location_name].code
            else:
                # Skip locations not in table
                continue
            
            # Skip if already checked
            if location_id in self.checked_locations:
                continue
            
            try:
                is_checked = False
                
                if flag_type == FLAG_STORY:
                    # Story flags use static addresses (base-relative)
                    story_addr = scene_or_addr
                    if isinstance(story_addr, int):
                        byte_val = self.memory.read_byte(story_addr)
                        if byte_val is not None:
                            is_checked = bool(byte_val & (1 << flag_bit))
                
                elif flag_type == FLAG_SCENE:
                    # Scene flags use scene name and are stored in static scene flag array
                    scene_name = scene_or_addr
                    if scene_name in SCENE_FLAG_ADDRESSES:
                        # SCENE_FLAG_ADDRESSES contains base-relative offsets, not absolute addresses
                        scene_base = SCENE_FLAG_ADDRESSES[scene_name]
                        flag_addr = scene_base + flag_bit
                        byte_val = self.memory.read_byte(flag_addr)
                        if byte_val is not None:
                            is_checked = bool(byte_val & flag_value)
                
                if is_checked:
                    self.checked_locations.add(location_id)
                    location_name_display = location_name[:50]  # Truncate long names
                    logger.info(f"✅ Location checked: {location_name_display}")
                    
            except Exception as e:
                logger.debug(f"Error checking location {location_name}: {e}")
    
    def build_item_to_location_map(self) -> Dict[int, int]:
        """
        Build a mapping from item codes to location codes.
        
        This is built from slot_data which contains the randomized item placements.
        Each location has an item placed at it, creating the item->location relationship.
        
        Returns:
            Dictionary mapping item code -> location code
        """
        item_to_loc = {}
        
        # Check if slot_data has location placements
        if not self.slot_data:
            logger.warning("No slot_data available yet - cannot build item_to_location map")
            return item_to_loc
        
        # Try to build from location_to_item mapping in patch data
        if hasattr(self, 'location_to_item') and self.location_to_item:
            for loc_name, item_info in self.location_to_item.items():
                # Get location code from LOCATION_TABLE
                if loc_name in LOCATION_TABLE:
                    location_code = LOCATION_TABLE[loc_name].code
                    item_code = item_info.get('id') or item_info.get('code')
                    if location_code and item_code:
                        item_to_loc[item_code] = location_code
            
            if item_to_loc:
                logger.info(f"Built item_to_location map with {len(item_to_loc)} entries from patch data")
                return item_to_loc
        
        # Alternative: Build from slot_data if it has item placements
        item_placements = self.slot_data.get('item_placements', {})
        if item_placements:
            for loc_code_str, item_code in item_placements.items():
                try:
                    loc_code = int(loc_code_str) if isinstance(loc_code_str, str) else loc_code_str
                    item_to_loc[item_code] = loc_code
                except (ValueError, TypeError):
                    continue
            
            if item_to_loc:
                logger.info(f"Built item_to_location map with {len(item_to_loc)} entries from slot_data")
                return item_to_loc
        
        logger.debug("No item placement data found - item_to_location map is empty")
        return item_to_loc

    def check_locations(self):
        """
        Check for completed locations.
        
        NOTE: Location checking is now item-based instead of memory-based.
        When an item is given to the player via give_item_to_player(),
        the corresponding location is automatically marked as checked.
        
        This function is kept for compatibility but no longer reads memory flags
        (LocationFlags.py addresses are from Wii game and incompatible with SSHD).
        """
        # Item-based location checking is handled in give_item_to_player()
        # No additional memory-based checking needed
        pass
    
    def on_deathlink(self, data: dict):
        """
        Handle death link - kill the player when someone else dies.
        """
        self.last_death_link = max(data.get("time", 0.0), self.last_death_link)

        if not self.memory.connected or not self.memory.base_address:
            logger.warning("DeathLink: Cannot kill player - not connected to game")
            return

        source = data.get('source', 'Unknown')
        cause = data.get('cause', '') or f"{source} died"
        logger.info(f"DeathLink: {cause}")

        # Write 0 to current health to kill the player
        health_offset = OFFSET_CURRENT_HEALTH
        success = self.memory.write_short(health_offset, 0)
        if success:
            logger.info(f"DeathLink: Set health to 0 at offset 0x{health_offset:X}")
            # Set flag to prevent sending death link for this death
            self.killed_by_deathlink = True
        else:
            logger.error(f"DeathLink: Failed to write health at offset 0x{health_offset:X}")
    
    async def send_death(self, death_text: str = ""):
        """
        Send a death link notification to other players.
        """
        if "DeathLink" not in self.tags:
            return

        if self.server and self.server.socket:
            self.last_death_link = time.time()
            logger.info("DeathLink: Sending death to your friends...")
            await self.send_msgs([{
                "cmd": "Bounce",
                "tags": ["DeathLink"],
                "data": {
                    "time": self.last_death_link,
                    "source": self.auth,
                    "cause": death_text or f"{self.auth} died"
                }
            }])
    
    def run_gui(self):
        """Run the GUI for the client."""
        from kvui import GameManager
        
        class SSHDManager(GameManager):
            logging_pairs = [
                ("Client", "Archipelago"),
            ]
            base_title = "Archipelago Skyward Sword HD Client"
        
        self.ui = SSHDManager(self)
        self.ui_task = asyncio.create_task(self.ui.async_run(), name="UI")
        
        # Log task creation
        logging.info(f"GUI task created: {self.ui_task}")
        logging.info(f"UI object: {self.ui}")


def install_patch(patch_file_path: str) -> tuple[bool, dict]:
    """
    Extract and install .apsshd patch to Ryujinx mod directory.
    
    Returns (success: bool, location_to_item: dict).
    """
    import zipfile
    import json
    from pathlib import Path
    import shutil
    
    print(f"\n{'='*60}")
    print(f"Installing SSHD Archipelago Patch")
    print(f"{'='*60}")
    print(f"Patch file: {patch_file_path}")
    
    patch_path = Path(patch_file_path)
    if not patch_path.exists():
        print(f"ERROR: Patch file not found: {patch_file_path}")
        return False, {}
    
    try:
        # Extract patch file
        print(f"\nExtracting patch file...")
        with zipfile.ZipFile(patch_path, 'r') as zip_file:
            # Read manifest
            manifest = json.loads(zip_file.read("manifest.json"))
            print(f"  Game: {manifest.get('game')}")
            print(f"  Player: {manifest.get('player')}")
            print(f"  Seed: {manifest.get('seed')}")
            
            # Load patch data with location-to-item mapping
            location_to_item = {}
            if 'patch_data.json' in zip_file.namelist():
                patch_data = json.loads(zip_file.read("patch_data.json"))
                location_to_item = patch_data.get('locations', {})
                print(f"\n  Loaded {len(location_to_item)} location-to-item mappings")
            
            # Check if romfs/exefs exist
            file_list = zip_file.namelist()
            has_romfs = any(f.startswith('romfs/') for f in file_list)
            has_exefs = any(f.startswith('exefs/') for f in file_list)
            
            print(f"\nPatch contents:")
            print(f"  - manifest.json: YES")
            print(f"  - patch_data.json: YES")
            print(f"  - romfs/: {'YES' if has_romfs else 'NO'}")
            print(f"  - exefs/: {'YES' if has_exefs else 'NO'}")
            
            if not has_romfs and not has_exefs:
                print(f"\nWARNING: No game mod files found in patch!")
                print(f"This patch only contains item/location data.")
                print(f"You may need to apply the base randomizer mod manually.")
                return False
            
            # Find Ryujinx atmosphere directory for LayeredFS mods
            try:
                from platform_utils import get_ryujinx_mod_dirs
                ryujinx_paths = get_ryujinx_mod_dirs()
            except ImportError:
                # Fallback if platform_utils not available - use OS-specific paths
                if sys.platform == "win32":
                    ryujinx_paths = [
                        Path.home() / "AppData" / "Roaming" / "Ryujinx" / "sdcard" / "atmosphere" / "contents" / "01002da013484000",
                        Path(os.environ.get('APPDATA', '')) / "Ryujinx" / "sdcard" / "atmosphere" / "contents" / "01002da013484000",
                    ]
                elif sys.platform == "linux":
                    ryujinx_paths = [
                        Path.home() / ".config" / "Ryujinx" / "sdcard" / "atmosphere" / "contents" / "01002da013484000",
                    ]
                else:  # macOS
                    ryujinx_paths = [
                        Path.home() / "Library" / "Application Support" / "Ryujinx" / "sdcard" / "atmosphere" / "contents" / "01002da013484000",
                    ]
            
            ryujinx_mod_dir = None
            for path in ryujinx_paths:
                if path.parent.parent.parent.exists():  # Check if sdcard/atmosphere folder exists
                    ryujinx_mod_dir = path
                    ryujinx_mod_dir.mkdir(parents=True, exist_ok=True)
                    break
            
            if ryujinx_mod_dir:
                print(f"\nFound Ryujinx atmosphere directory: {ryujinx_mod_dir}")
                
                # Install to Archipelago folder (LayeredFS will merge with game files)
                mod_install_dir = ryujinx_mod_dir / "Archipelago"
                
                print(f"Installing to: {mod_install_dir}")
                
                # Remove existing mod if present
                if mod_install_dir.exists():
                    print(f"  Removing existing mod...")
                    shutil.rmtree(mod_install_dir)
                
                # Extract romfs and exefs
                mod_install_dir.mkdir(parents=True, exist_ok=True)
                
                for file_name in file_list:
                    if file_name.startswith('romfs/') or file_name.startswith('exefs/'):
                        # Extract to mod directory
                        target_path = mod_install_dir / file_name
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        with zip_file.open(file_name) as source:
                            with open(target_path, 'wb') as target:
                                target.write(source.read())
                
                print(f"\n✓ Patch installed successfully!")
                print(f"\nNext steps:")
                print(f"  1. Launch Skyward Sword HD in Ryujinx")
                print(f"  2. The LayeredFS mod will be automatically applied")
                print(f"  3. Connect to the Archipelago server")
                return True, location_to_item
            else:
                # No Ryujinx found - extract to temp for manual install
                print(f"\nWARNING: Ryujinx installation not found automatically.")
                print(f"Extracting patch files for manual installation...")
                
                # Extract to a folder next to the patch file
                extract_dir = patch_path.parent / f"{patch_path.stem}_extracted"
                if extract_dir.exists():
                    shutil.rmtree(extract_dir)
                extract_dir.mkdir(parents=True, exist_ok=True)
                
                zip_file.extractall(extract_dir)
                
                print(f"\nExtracted to: {extract_dir}")
                print(f"\nManual installation:")
                print(f"  1. Copy the romfs/ and exefs/ folders to:")
                try:
                    from platform_utils import get_ryujinx_dir
                    ryujinx_manual_path = get_ryujinx_dir() / "sdcard" / "atmosphere" / "contents" / "01002da013484000" / "Archipelago"
                    print(f"     {ryujinx_manual_path}")
                except ImportError:
                    print(f"     %APPDATA%\\Ryujinx\\sdcard\\atmosphere\\contents\\01002da013484000\\Archipelago\\")
                print(f"  2. Launch Skyward Sword HD in Ryujinx")
                print(f"  3. The LayeredFS mod will be automatically applied")
                return False, location_to_item
                
    except Exception as e:
        print(f"\nERROR: Failed to install patch: {e}")
        import traceback
        traceback.print_exc()
        return False, {}


async def main(args=None):
    """
    Main entry point for the SSHD client.
    """
    import colorama
    
    print("="*60)
    print("Skyward Sword HD Archipelago Client")
    print("="*60)
    print(f"Starting client...")
    print(f"Arguments: {args}")
    
    parser = get_base_parser(description="Skyward Sword HD Client for Archipelago with Ryujinx support.")
    parser.add_argument('diff_file', default="", type=str, nargs="?",
                        help='Path to an Archipelago Binary Patch file (.apsshd)')
    parsed_args = parser.parse_args(args)
    
    # Install patch if provided and get location mapping
    location_to_item = {}
    if parsed_args.diff_file:
        patch_file = parsed_args.diff_file
        print(f"\nPatch file provided: {patch_file}")
        if patch_file.endswith('.apsshd'):
            success, location_to_item = install_patch(patch_file)
            if not success:
                print("ERROR: Failed to install patch")
                return
            print(f"\n" + "="*60)
            print(f"Continuing to launch client...")
            print(f"="*60 + "\n")
        else:
            print(f"WARNING: Expected .apsshd file, got {patch_file}")
    
    print(f"Parsed arguments: {parsed_args}")
    
    # Enable GUI when available (Archipelago launcher has all GUI dependencies)
    use_gui = gui_enabled
    print(f"GUI enabled: {use_gui}")
    
    colorama.init()
    
    # Create context (requires event loop to already be running)
    ctx = SSHDContext(parsed_args.connect, parsed_args.password)
    ctx.location_to_item = location_to_item  # Set mapping loaded from patch
    
    ctx.server_task = asyncio.create_task(server_loop(ctx), name="ServerLoop")
    
    # Add Ryujinx connection task
    ctx.ryujinx_task = asyncio.create_task(ctx.ryujinx_connection_task(), name="Ryujinx Connection")
    
    if use_gui:
        print("Launching GUI...")
        ctx.run_gui()
        # Give the GUI task a chance to start and build the interface
        await asyncio.sleep(0.1)
    else:
        ctx.run_cli()
    
    print("Client initialized. Waiting for connection...")
    
    # Wait for exit event (set when GUI window closes or user exits)
    await ctx.exit_event.wait()
    
    print("Exit event received, shutting down...")
    
    # Cleanup
    ctx.server_address = None


if __name__ == "__main__":
    import colorama
    logging.basicConfig(
        format="[%(name)s]: %(message)s",
        level=logging.INFO
    )
    colorama.just_fix_windows_console()
    asyncio.run(main())
    colorama.deinit()
