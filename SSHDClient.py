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
OFFSET_SCENE_FLAGS_STATIC = 0x182DF00   # Static scene flags (16 bytes)
OFFSET_SCENE_FLAGS = 0x9E4              # Scene flags within player structure
OFFSET_TEMP_FLAGS_STATIC = 0x182DF10    # Static temp flags (8 bytes)
OFFSET_ZONE_FLAGS_STATIC = 0x182DF18    # Static zone flags (504 bytes)
OFFSET_ITEM_FLAGS_STATIC = 0x182E170    # Static item flags (128 bytes)
OFFSET_DUNGEON_FLAGS_STATIC = 0x182E128 # Static dungeon flags (16 bytes)

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
OFFSET_CURRENT_HEALTH = 0x5306     # Current hearts (2 bytes)
OFFSET_HEALTH_CAPACITY = 0x5302    # Max hearts (2 bytes)
OFFSET_STAMINA = 0x64D8            # Stamina gauge

# Current Stage Info offsets (relative to OFFSET_CURRENT_STAGE)
OFFSET_STAGE_NAME = 0x0            # Stage name (8 byte string)
OFFSET_STAGE_LAYER = 0x23          # Layer ID
OFFSET_STAGE_ROOM = 0x22           # Room ID
OFFSET_STAGE_ENTRANCE = 0x24       # Entrance ID
OFFSET_STAGE_NIGHT = 0x25          # Night flag

# Scene name to scene flag base address mapping (absolute addresses in SSHD memory)
# These are the absolute memory addresses where scene flags are stored
# Scene flags start at 0x805A9F00 and are organized by scene
SCENE_FLAG_ADDRESSES = {
    "Skyloft": 0x805A9F00,              # Skyloft scene flags
    "Sky": 0x805AA000,                  # Sky scene flags
    "Sealed Grounds": 0x805AA100,       # Sealed Grounds
    "Faron Woods": 0x805AA200,          # Faron Woods
    "Lake Floria": 0x805AA300,          # Lake Floria
    "Skyview": 0x805AA400,              # Skyview Temple
    "Eldin Volcano": 0x805AA500,        # Eldin Volcano
    "Earth Temple": 0x805AA600,         # Earth Temple
    "Lanayru Desert": 0x805AA700,       # Lanayru Desert
    "Lanayru Mining Facility": 0x805AA800,  # Lanayru Mining Facility
    "Ancient Cistern": 0x805AA900,      # Ancient Cistern
    "Sandship": 0x805AAA00,             # Sandship
    "Fire Sanctuary": 0x805AAB00,       # Fire Sanctuary
    "Sky Keep": 0x805AAC00,             # Sky Keep
}

# Story flags base address (absolute)
STORY_FLAGS_BASE = 0x805A9AD0

# Scene flags base address (absolute)
SCENE_FLAGS_BASE = 0x805A9F00


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
        """Synchronous memory scanning (runs in thread pool)."""
        try:
            start_time = time.time()
            print(f"[DEBUG] Starting memory scan at address 0x10000")
            
            # Scan memory regions
            address = 0x10000
            max_address = 0x7FFFFFFFFFFF
            chunk_size = 1024 * 1024  # 1 MB chunks (same as test script - much faster!)
            chunks_scanned = 0
            
            while address < max_address:
                try:
                    # Read a chunk of memory
                    # print(f"[DEBUG] Attempting to read chunk at 0x{address:X}, size: {min(chunk_size, max_address - address):,} bytes")
                    data = self.pm.read_bytes(address, min(chunk_size, max_address - address))
                    # print(f"[DEBUG] Successfully read chunk, searching for signature...")
                    chunks_scanned += 1
                    
                    # Log progress every 10 chunks
                    if chunks_scanned % 10 == 0:
                        print(f"[DEBUG] Scanned {chunks_scanned} chunks, current address: 0x{address:X}")
                    
                    # Search for signature
                    offset = data.find(MEMORY_SIGNATURE)
                    if offset != -1:
                        self.base_address = address + offset
                        elapsed = time.time() - start_time
                        print(f"[SUCCESS] Found SSHD base address: 0x{self.base_address:X} (took {elapsed:.1f}s, scanned {chunks_scanned} chunks)")
                        logger.info(f"Found SSHD base address: 0x{self.base_address:X} (took {elapsed:.1f}s)")
                        return True
                    
                    address += chunk_size
                    
                except pymem.exception.MemoryReadError as e:
                    # Skip inaccessible memory regions - jump ahead to find next readable region
                    # print(f"[DEBUG] MemoryReadError at 0x{address:X}, skipping ahead 64 MB")
                    address += chunk_size * 64  # Skip 64 MB ahead like test script
                    continue
                except Exception as e:
                    print(f"[DEBUG] Unexpected error at 0x{address:X}: {e}, skipping ahead")
                    address += chunk_size * 64
                    continue
            
            print(f"[FAIL] Signature not found after scanning {chunks_scanned} chunks")
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
            logger.debug(f"Error reading float at 0x{offset:X}: {e}")
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
            logger.debug(f"Error reading byte at 0x{offset:X}: {e}")
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
            logger.debug(f"Error reading pointer at 0x{offset:X}: {e}")
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
        self.slot_options: Dict[str, Any] = {}  # Player options from slot data
        
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
                logger.info(f"✅ Loaded custom flag mapping with {len(self.custom_flag_to_location)} flags")
            else:
                logger.warning("No custom flag mapping found in slot data - location detection disabled")
            
            # Load location to custom flag mapping for vanilla item pickups
            location_to_flag_mapping = slot_data.get("location_to_custom_flag", {})
            if location_to_flag_mapping:
                # Convert string keys back to integers
                self.location_to_custom_flag = {int(k): v for k, v in location_to_flag_mapping.items()}
                logger.info(f"✅ Loaded {len(self.location_to_custom_flag)} location→flag mappings for vanilla pickups")
            else:
                logger.warning("No location→flag mapping found - vanilla pickups disabled")
            
        elif cmd == "ReceivedItems":
            # Received items from other players
            start_index = args.get("index", 0)
            items_list = args.get("items", [])
            for i, network_item in enumerate(items_list):
                item_id = network_item.item
                location_player = network_item.player  # Player whose location was checked
                
                # Look up item name in OUR slot (SSHD) since we're receiving SSHD items
                item_name = self.item_names.lookup_in_slot(item_id, self.slot)
                try:
                    sender_name = self.player_names[location_player]
                except (KeyError, TypeError):
                    sender_name = f"Player {location_player}"
                
                # Add to queue to be given in-game
                self.item_queue.append({
                    "id": item_id,
                    "name": item_name,
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
    
    def give_item_to_player(self, item_name: str, item_id: int) -> bool:
        """
        Give an item to the player using the game's native item system.
        
        Uses a memory buffer that the game monitors every frame. When items are written
        to the buffer, the game spawns them with proper animations, models, and sound effects.
        
        Falls back to direct memory writes if GameItemSystem is not available.
        
        Returns True if successful, False if failed.
        """
        if not self.memory.connected or not self.memory.base_address:
            logger.debug(f"Cannot give item: not connected to game")
            return False
        
        # Try using the new item system with animations
        if GameItemSystem:
            try:
                # Initialize on first use
                if not self.game_item_system:
                    self.game_item_system = GameItemSystem(self.memory)
                
                # Use the integrated system (spawns items with animations)
                success = self.game_item_system.give_item_by_name(item_name)
                if success:
                    logger.info(f"Gave {item_name} with animation!")
                else:
                    logger.warning(f"Failed to give {item_name} via item system")
                return success
            except Exception as e:
                logger.warning(f"Item system error for {item_name}: {e}, falling back to direct write")
                # Fall through to legacy system
        
        # Fallback: Legacy direct memory write system (no animations)
        logger.debug(f"Using legacy direct memory write for {item_name}")
        
        try:
            if item_name not in ITEM_TABLE:
                logger.warning(f"Item '{item_name}' not found in ITEM_TABLE")
                return False
            
            try:
                from ALL_ITEM_MEMORY_ADDRESSES import (
                    get_item_memory_address,
                    is_progressive_item,
                    is_trap_item,
                    is_special_item,
                )
            except ImportError:
                logger.error("Failed to import item memory addresses")
                return False
            
            success = False
            
            # Check if it's a consumable counter item
            if item_name in ["Green Rupee", "Blue Rupee", "Red Rupee", "Silver Rupee", "Gold Rupee"]:
                success = self._give_rupees_dual(item_name)
            elif item_name.endswith("Bombs") or item_name == "Bomb":
                success = self._give_bombs_dual(item_name)
            elif item_name.endswith("Arrows") or item_name == "Arrow":
                success = self._give_arrows_dual(item_name)
            elif "Seed" in item_name and "Slingshot" not in item_name:
                success = self._give_seeds_dual(item_name)
            elif "Crystal" in item_name:
                success = self._give_crystals_dual(item_name)
            elif "Heart" in item_name and item_name not in [
                "Heart Potion",
                "Heart Potion Plus",
                "Heart Potion Plus Plus",
                "Heart Medal",
                "Heart Container",
                "Heart Piece",
            ]:
                success = self._give_hearts(item_name)
            # Progressive items (handled by sshd-rando patches)
            elif is_progressive_item(item_name):
                logger.debug(f"Progressive item '{item_name}' - handled by randomizer")
                logger.info(f"✅ Accepted progressive: {item_name}")
                return True
            # Trap items (don't need memory implementation)
            elif is_trap_item(item_name):
                logger.debug(f"Trap item '{item_name}' - handled by archipelago")
                logger.info(f"✅ Accepted trap: {item_name}")
                return True
            # Special items that don't need memory flags
            elif is_special_item(item_name):
                logger.debug(f"Special item '{item_name}' - no memory implementation needed")
                logger.info(f"✅ Accepted special: {item_name}")
                return True
            # Try comprehensive item memory mapping
            else:
                address = get_item_memory_address(item_name)
                if address is not None:
                    byte_offset, bit_position = address
                    success = self._set_item_flag_dual(byte_offset, bit_position)
                else:
                    # Unknown item - log and accept
                    logger.warning(f"⚠️ Unknown item: {item_name} - no memory address found")
                    logger.info(f"✅ Accepted unknown item: {item_name}")
                    return True
            
            if success:
                logger.info(f"Gave item: {item_name}")
            else:
                logger.warning(f"Failed to give item: {item_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error giving item '{item_name}': {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
    
    def _set_item_flag(self, base_offset: int, byte_offset: int, bit_position: int) -> bool:
        """Set a single bit flag for a major item."""
        try:
            address = base_offset + byte_offset
            current_byte = self.memory.read_byte(address)
            if current_byte is None:
                return False
            
            # Set the bit
            new_byte = current_byte | (1 << bit_position)
            return self.memory.write_byte(address, new_byte)
        except Exception as e:
            logger.debug(f"Error setting flag: {e}")
            return False
    
    def _set_item_flag_dual(self, byte_offset: int, bit_position: int) -> bool:
        """Set bit flag in both uncommitted and committed memory regions."""
        ITEMFLAGS_UNCOMMITTED_OFFSET = 0x182E170
        FILE_MANAGER_OFFSET = 0x5AEAD44
        FILE_A_POINTER_OFFSET = 0x10
        ITEMFLAGS_IN_FILE_OFFSET = 0x9E4
        
        try:
            # Write to uncommitted (runtime) - use offset from base
            address_offset = ITEMFLAGS_UNCOMMITTED_OFFSET + byte_offset
            byte_val = self.memory.read_byte(address_offset)
            if byte_val is None:
                logger.warning(f"Could not read byte at offset 0x{address_offset:X}")
                return False
            
            new_byte = byte_val | (1 << bit_position)
            if not self.memory.write_byte(address_offset, new_byte):
                logger.warning(f"Failed to write to offset 0x{address_offset:X}")
                return False
            
            logger.debug(f"Wrote flag to uncommitted at 0x{address_offset:X}: 0x{byte_val:02X} → 0x{new_byte:02X}")
            
            # Also write to committed (save file) via File Manager structure (direct offset, not pointer chain)
            try:
                # File Manager is a structure at base + 0x5AEAD44
                # File A is embedded at +0x10, Itemflags at +0x9E4
                itemflags_committed_offset = FILE_MANAGER_OFFSET + FILE_A_POINTER_OFFSET + ITEMFLAGS_IN_FILE_OFFSET + byte_offset
                logger.info(f"[FlagsDebug] Writing directly to committed offset: 0x{itemflags_committed_offset:X}")
                
                # Read current byte, set bit, write back
                committed_byte = self.memory.read_byte(itemflags_committed_offset)
                if committed_byte is not None:
                    new_committed = committed_byte | (1 << bit_position)
                    if self.memory.write_byte(itemflags_committed_offset, new_committed):
                        logger.info(f"✅ Wrote flag to committed at offset 0x{itemflags_committed_offset:X}")
            except Exception as e:
                logger.debug(f"Could not write to committed: {e}")
            
            return True
        except Exception as e:
            logger.warning(f"Error in flag write: {e}")
            return False
    
    def _give_rupees_dual(self, item_name: str) -> bool:
        """Add rupees to both uncommitted and committed memory."""
        rupee_values = {
            "Green Rupee": 1,
            "Blue Rupee": 5,
            "Red Rupee": 20,
            "Silver Rupee": 100,
            "Gold Rupee": 300
        }
        amount = rupee_values.get(item_name, 0)
        if amount == 0:
            return False
        
        OFFSET_UNCOMMITTED = 0x182E170 + 0x70 + 0xA
        FILE_MANAGER_OFFSET = 0x5AEAD44
        FILE_A_POINTER_OFFSET = 0x10
        ITEMFLAGS_IN_FILE_OFFSET = 0x9E4
        
        try:
            # Write to uncommitted
            data = self.memory.read_bytes(OFFSET_UNCOMMITTED, 3)
            if not data:
                logger.warning(f"Could not read rupees at offset 0x{OFFSET_UNCOMMITTED:X}")
                return False
            
            current = int.from_bytes(data, 'little') & 0xFFFFF
            new_value = min(current + amount, 9999)
            logger.info(f"Rupees: {current} + {amount} = {new_value}")
            
            original_full = int.from_bytes(data, 'little')
            new_full = (original_full & 0xFFF00000) | new_value
            new_bytes = new_full.to_bytes(3, 'little')
            
            for i, byte_val in enumerate(new_bytes):
                if not self.memory.write_byte(OFFSET_UNCOMMITTED + i, byte_val):
                    logger.warning(f"Failed to write rupee byte {i}")
                    return False
            
            # Write to committed via File Manager structure (direct offset, not pointer chain)
            try:
                # File Manager is a structure at base + 0x5AEAD44
                # File A is embedded at +0x10, Itemflags at +0x9E4, Rupees at +0x70+0xA
                rupees_committed_offset = FILE_MANAGER_OFFSET + FILE_A_POINTER_OFFSET + ITEMFLAGS_IN_FILE_OFFSET + 0x70 + 0xA
                logger.info(f"[RupeesDebug] Writing directly to committed offset: 0x{rupees_committed_offset:X}")
                
                for i, byte_val in enumerate(new_bytes):
                    if not self.memory.write_byte(rupees_committed_offset + i, byte_val):
                        logger.warning(f"Failed to write committed rupee byte {i}")
                        break
                else:
                    logger.info(f"✅ Wrote rupees to committed at offset 0x{rupees_committed_offset:X}")
            except Exception as e:
                logger.debug(f"Could not write rupees to committed: {e}")
            
            return True
        except Exception as e:
            logger.error(f"Error giving rupees: {e}")
            return False
    
    def _give_bombs_dual(self, item_name: str) -> bool:
        """Add bombs to memory."""
        bomb_amounts = {"Bomb": 1, "5 Bombs": 5, "10 Bombs": 10}
        amount = bomb_amounts.get(item_name, 5)
        
        OFFSET_UNCOMMITTED = 0x182E170 + 0x70 + 0xE
        try:
            data = self.memory.read_bytes(OFFSET_UNCOMMITTED, 2)
            if not data:
                return False
            
            value = int.from_bytes(data, 'little')
            current = (value >> 7) & 0x7F
            new_count = min(current + amount, 99)
            
            value = (value & ~(0x7F << 7)) | (new_count << 7)
            new_bytes = value.to_bytes(2, 'little')
            
            for i, byte_val in enumerate(new_bytes):
                if not self.memory.write_byte(OFFSET_UNCOMMITTED + i, byte_val):
                    return False
            return True
        except:
            return False
    
    def _give_arrows_dual(self, item_name: str) -> bool:
        """Add arrows to memory."""
        arrow_amounts = {"Arrow": 1, "5 Arrows": 5, "10 Arrows": 10}
        amount = arrow_amounts.get(item_name, 10)
        
        OFFSET_UNCOMMITTED = 0x182E170 + 0x70 + 0xE
        try:
            data = self.memory.read_bytes(OFFSET_UNCOMMITTED, 2)
            if not data:
                return False
            
            value = int.from_bytes(data, 'little')
            current = value & 0x7F
            new_count = min(current + amount, 99)
            
            value = (value & ~0x7F) | new_count
            new_bytes = value.to_bytes(2, 'little')
            
            for i, byte_val in enumerate(new_bytes):
                if not self.memory.write_byte(OFFSET_UNCOMMITTED + i, byte_val):
                    return False
            return True
        except:
            return False
    
    def _give_seeds_dual(self, item_name: str) -> bool:
        """Add Deku seeds to memory."""
        seed_amounts = {"Deku Seed": 1, "5 Deku Seeds": 5, "10 Deku Seeds": 10}
        amount = seed_amounts.get(item_name, 5)
        
        OFFSET_UNCOMMITTED = 0x182E170 + 0x70 + 0xC
        try:
            data = self.memory.read_bytes(OFFSET_UNCOMMITTED, 2)
            if not data:
                return False
            
            value = int.from_bytes(data, 'little')
            current = (value >> 7) & 0x7F
            new_count = min(current + amount, 99)
            
            value = (value & ~(0x7F << 7)) | (new_count << 7)
            new_bytes = value.to_bytes(2, 'little')
            
            for i, byte_val in enumerate(new_bytes):
                if not self.memory.write_byte(OFFSET_UNCOMMITTED + i, byte_val):
                    return False
            return True
        except:
            return False
    
    def _give_crystals_dual(self, item_name: str) -> bool:
        """Add gratitude crystals to memory."""
        crystal_amounts = {"Gratitude Crystal": 1, "5 Gratitude Crystals": 5}
        amount = crystal_amounts.get(item_name, 1)
        
        OFFSET_UNCOMMITTED = 0x182E170 + 0x60 + 0xC
        try:
            data = self.memory.read_bytes(OFFSET_UNCOMMITTED, 2)
            if not data:
                return False
            
            value = int.from_bytes(data, 'little')
            current = (value >> 3) & 0x7F
            new_count = min(current + amount, 80)
            
            value = (value & ~(0x7F << 3)) | (new_count << 3)
            new_bytes = value.to_bytes(2, 'little')
            
            for i, byte_val in enumerate(new_bytes):
                if not self.memory.write_byte(OFFSET_UNCOMMITTED + i, byte_val):
                    return False
            return True
        except:
            return False
    
    def _give_hearts(self, item_name: str) -> bool:
        """Restore hearts (temporary health boost)."""
        logger.debug(f"Heart item '{item_name}' received")
        return True
    
    def get_progressive_item_id(self, progressive_name: str, count: int) -> Optional[int]:
        """
        Convert progressive item name + count to actual item ID.
        
        For example: "Progressive Sword" with count 1 = Goddess Sword
                     "Progressive Sword" with count 2 = Goddess Longsword
                     etc.
        """
        # Progressive item mappings (item IDs from sshd-rando)
        progressive_maps = {
            "Progressive Sword": [2773023, 2773031, 2773032, 2773033, 2773034],  # Practice -> Goddess -> Longsword -> White -> Master
            "Progressive Bow": [2773050, 2773120],  # Wooden Bow -> Iron Bow
            "Progressive Slingshot": [2773055, 2773285],  # Slingshot -> Scattershot
            "Progressive Beetle": [2773056, 2773295, 2773296],  # Beetle -> Hook Beetle -> Quick Beetle
            "Progressive Mitts": [2773058, 2773325],  # Digging Mitts -> Mogma Mitts
            "Progressive Bug Net": [2773071, 2773140],  # Bug Net -> Big Bug Net
            "Progressive Wallet": [2773082, 2773672, 2773673, 2773674],  # Medium -> Big -> Giant -> Tycoon
            "Progressive Pouch": [2773084, 2773710, 2773711, 2773712, 2773713],  # 5 levels of pouch
            "Progressive Bomb Bag": [2773051, 2773121, 2773122],  # Regular -> Big -> Bigger
        }
        
        if progressive_name not in progressive_maps:
            return None
        
        item_list = progressive_maps[progressive_name]
        
        # Return the item for this level (1-indexed)
        if 1 <= count <= len(item_list):
            return item_list[count - 1]
        
        # Already at max level, give last level again
        return item_list[-1] if item_list else None
    
    def build_item_to_location_map(self) -> dict[int, int]:
        """
        Build a mapping of item code -> location code from slot_data.
        
        This mapping comes from the world generation and tells us which location
        each item code should check when it is given to the player.
        
        Returns:
            Dict[item_code: int] = location_code: int
        """
        item_to_location = {}
        
        # Check if we have slot_data with the location_to_item_map
        if not hasattr(self, 'slot_data') or not self.slot_data:
            logger.debug("build_item_to_location_map: slot_data not available yet")
            return item_to_location
        
        # Get the location_to_item mapping from slot_data
        location_to_item_map = self.slot_data.get("location_to_item_map", {})
        if not location_to_item_map:
            logger.debug("build_item_to_location_map: location_to_item_map not in slot_data")
            return item_to_location
        
        # Reverse the mapping: location_code -> item_code becomes item_code -> location_code
        # location_to_item_map is {location_code: item_code}
        # We need {item_code: location_code}
        for location_code, item_code in location_to_item_map.items():
            item_to_location[item_code] = location_code
        
        logger.info(f"✓ Built item-to-location mapping from slot_data: {len(item_to_location)} items")
        return item_to_location
    
    async def ryujinx_connection_task(self):
        """Background task to maintain connection to Ryujinx."""
        while not self.exit_event.is_set():
            try:
                # Try to connect if not connected
                if not self.memory.connected:
                    if self.memory.connect():
                        # Connection successful, find base address
                        try:
                            result = await self.memory.find_base_address()
                            if result:
                                # Base address found - log it to the user
                                logger.info(f"Found SSHD base address: 0x{self.memory.base_address:X}")
                                # Try to build item mapping now if server is connected
                                # Otherwise it will be built lazily when items are received
                                if hasattr(self, 'slot') and self.slot and hasattr(self, 'worlds') and self.worlds:
                                    self.item_to_location = self.build_item_to_location_map()
                                # Don't set connected = False, keep scanning for updates
                            else:
                                logger.error("Failed to find SSHD in memory. Is the game running?")
                                self.memory.connected = False
                        except Exception as e:
                            logger.error(f"Error finding base address: {e}")
                            self.memory.connected = False
                    
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
    
    async def scan_custom_flags(self):
        """
        Scan memory for custom flag changes to detect checked locations.
        
        sshd-rando assigns custom flags (10-bit encoded) to locations:
        - Bit 9: 0=scene flags, 1=dungeon flags
        - Bits 8-7: Index (0-3) within that flag space
        - Bits 6-0: Flag bit (0-127) within the 16-byte index
        
        Each index is 16 bytes = 128 bits
        Total: 512 scene + 512 dungeon = 1024 custom flags
        """
        if not self.memory.connected or not self.memory.base_address:
            return
        
        # Only scan if we have the mapping
        if not self.custom_flag_to_location:
            return
        
        try:
            # Read scene flag space (16 bytes = 128 bits)
            scene_flag_bytes = self.memory.read_bytes(OFFSET_SCENE_FLAGS_STATIC, 16)
            
            # Read dungeon flag space (16 bytes = 128 bits)
            dungeon_flag_bytes = self.memory.read_bytes(OFFSET_DUNGEON_FLAGS_STATIC, 16)
            
            if scene_flag_bytes is None or dungeon_flag_bytes is None:
                return
            
            # Initialize previous state on first scan (prevents detecting existing flags as "new")
            # We only want to detect flags that change from 0→1 after we start monitoring
            first_scan = not hasattr(self, '_custom_flags_initialized')
            if first_scan:
                logger.debug("First custom flag scan - initializing baseline state")
                self._custom_flags_initialized = True
            
            newly_checked_locations = []
            
            # Check each custom flag we're tracking
            for custom_flag_id, location_code in self.custom_flag_to_location.items():
                # Decode the custom flag ID
                flag_space_trigger = (custom_flag_id >> 9) & 1  # Bit 9
                index = (custom_flag_id >> 7) & 3  # Bits 8-7
                flag_bit = custom_flag_id & 0x7F  # Bits 6-0
                
                # Select the appropriate flag bytes
                flag_bytes = dungeon_flag_bytes if flag_space_trigger else scene_flag_bytes
                
                # Calculate byte and bit position
                byte_index = flag_bit // 8
                bit_index = flag_bit % 8
                
                # Check if flag is set
                is_set = (flag_bytes[byte_index] >> bit_index) & 1
                
                # On first scan, just record current state without checking locations
                if first_scan:
                    self.previous_custom_flags[custom_flag_id] = is_set
                    continue
                
                # Compare with previous state
                prev_state = self.previous_custom_flags.get(custom_flag_id, 0)
                
                if is_set and not prev_state:
                    # Flag just changed from 0→1, location was checked!
                    if location_code not in self.checked_locations:
                        self.checked_locations.add(location_code)
                        newly_checked_locations.append(location_code)
                        logger.info(f"Location checked in-game: {location_code} (flag {custom_flag_id})")
                
                # Update previous state
                self.previous_custom_flags[custom_flag_id] = is_set
            
            # Send newly checked locations to server
            if newly_checked_locations:
                await self.send_msgs([{
                    "cmd": "LocationChecks",
                    "locations": newly_checked_locations
                }])
                logger.info(f"Sent {len(newly_checked_locations)} location checks to server")
                
                # Check if "Defeat Demise" location (2773238) was just checked - this means victory!
                DEFEAT_DEMISE_LOCATION = 2773238
                if DEFEAT_DEMISE_LOCATION in newly_checked_locations:
                    logger.info("=== VICTORY! Demise defeated - sending goal completion to server ===")
                    await self.send_msgs([{
                        "cmd": "StatusUpdate",
                        "status": ClientStatus.CLIENT_GOAL
                    }])
                    # Server will automatically release all remaining items if auto-release is enabled
                
        except Exception as e:
            logger.error(f"Error scanning custom flags: {e}")
    
    async def update_game_state(self):
        """
        Read game state from memory and check for location completions.
        
        This is called frequently to monitor game progress.
        """
        # Log first call
        if not hasattr(self, '_update_logged'):
            logger.info(f"[GameState] update_game_state() is being called, LOCATION_FLAG_MAP has {len(LOCATION_FLAG_MAP) if LOCATION_FLAG_MAP else 0} entries")
            self._update_logged = True
            logger.info(f"[DEBUG] Available attributes: {[a for a in dir(self) if not a.startswith('_')][:20]}")

        
        # Log item queue status periodically
        if not hasattr(self, '_queue_log_counter'):
            self._queue_log_counter = 0
        self._queue_log_counter += 1
        if self._queue_log_counter >= 300:  # Log every ~5 seconds (60 calls/sec * 5)
            self._queue_log_counter = 0
            logger.debug(f"[DEBUG] Queue status: {len(self.item_queue)} items pending, {len(self.item_to_location)} items in mapping")
        
        if not self.memory.connected or not self.memory.base_address:
            # Log connection status periodically
            if not hasattr(self, '_last_disconnect_log'):
                self._last_disconnect_log = 0
            
            if self._last_disconnect_log == 0:
                logger.warning("Memory not connected to game - waiting for Ryujinx connection")
                self._last_disconnect_log = 300  # Log every 5 seconds (300 frames at 60fps)
            else:
                self._last_disconnect_log -= 1
            return
        
        # Reset disconnect counter when connected
        if hasattr(self, '_last_disconnect_log'):
            if self._last_disconnect_log != 300:
                logger.info(f"Memory connected! Base address: {hex(self.memory.base_address)}")
            self._last_disconnect_log = 300
        
        # Initialize location checking if not already done
        if LOCATION_FLAG_MAP and not hasattr(self, 'location_check_counter'):
            logger.info(f"Location checking enabled with {len(LOCATION_FLAG_MAP)} locations")
            self.location_check_counter = 0
        
        try:
            # Verify game is loaded by reading stage name
            # This is more reliable than checking game state flags
            stage_name = self.memory.read_string(OFFSET_CURRENT_STAGE + OFFSET_STAGE_NAME, 16)
            if not stage_name or len(stage_name) == 0:
                # Game not loaded yet (title screen, loading, etc.)
                if not hasattr(self, '_no_stage_logged'):
                    logger.debug("No stage loaded yet")
                    self._no_stage_logged = True
                return
            else:
                # Clear the flag when stage is loaded
                if hasattr(self, '_no_stage_logged'):
                    logger.debug(f"Stage loaded: {stage_name}")
                    delattr(self, '_no_stage_logged')
            
            # Update current stage
            if stage_name != self.current_stage:
                logger.info(f"Entered stage: {stage_name}")
                self.current_stage = stage_name
            
            # Scan memory for checked locations (custom flags)
            await self.scan_custom_flags()
            
            # Give queued items to player
            if self.item_queue:
                item_data = self.item_queue[0]
                logger.debug(f"Processing item from queue: {item_data['name']} (ID: {item_data['id']})")
                
                if self.give_item_to_player(item_data["name"], item_data["id"]):
                    # Successfully gave SSHD item to player's inventory
                    
                    # NOTE: We do NOT check locations here!
                    # Location checking happens when the player picks up items IN-GAME
                    # via scan_custom_flags() detecting custom flag changes.
                    # 
                    # This queue is for items received FROM THE SERVER (cross-world items)
                    # which should only be given to the player's inventory, not check locations.
                    
                    self.item_queue.pop(0)
                else:
                    # Failed to give item, will retry next frame
                    pass
            
            # Check for death (for death link)
            current_health = self.memory.read_short(OFFSET_PLAYER + OFFSET_CURRENT_HEALTH)
            if current_health is not None:
                # Player just died if health went to 0 (from any positive value OR if we had None before)
                if current_health == 0 and (self.last_hearts is None or self.last_hearts > 0):
                    # Player just died
                    if "DeathLink" in self.tags:
                        await self.send_death(f"{self.auth} died in {self.current_stage or 'Skyloft'}")
                self.last_hearts = current_health
            
            # Location checking is now handled by scan_custom_flags()
            # which detects custom flag changes when items are picked up in-game.
            # No additional location checking needed here.
            
        except Exception as e:
            logger.error(f"Error updating game state: {e}")
    
    async def check_all_locations(self):
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
    
    def mark_location_checked(self, location_name: str):
        """Mark a location as checked (legacy helper method)."""
        if location_name in LOCATION_TABLE:
            location_id = LOCATION_TABLE[location_name].code
        else:
            location_id = 2773000 + (hash(location_name) % 900)
        
        if location_id not in self.checked_locations:
            self.checked_locations.add(location_id)
            logger.info(f"Marked location checked: {location_name} (ID: {location_id})")
    
    async def on_deathlink(self, data: dict):
        """
        Handle death link - kill the player when someone else dies.
        """
        if not self.memory.connected or not self.memory.base_address:
            return
        
        logger.info(f"Death link received from {data.get('source', 'Unknown')}: {data.get('cause', 'died')}")
        
        # Set player hearts to 0 to trigger death
        self.memory.write_short(OFFSET_PLAYER + OFFSET_CURRENT_HEALTH, 0)
    
    async def send_death(self, death_text: str = ""):
        """
        Send a death link notification to other players.
        """
        if "DeathLink" not in self.tags:
            return
        
        await self.send_msgs([{
            "cmd": "Deathlink",
            "time": time.time(),
            "source": self.auth,
            "cause": death_text or f"{self.auth} died"
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
