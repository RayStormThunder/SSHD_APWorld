"""
SSHD Archipelago - Game Item System Integration

This module provides integration with the sshd-rando backend's item spawning system
to enable proper item-get animations and models instead of direct memory writes.

Key Features:
- Uses game's native give_item() function
- Shows item-get animations (Link holding up item)
- Displays 3D item models
- Plays appropriate jingles/fanfares
- Items appear immediately without stage reload

Architecture:
- Python client writes item ID to memory buffer
- Patched game code monitors buffer via ASM hook
- When item detected, game calls Rust give_item() function
- Buffer cleared when complete, signaling Python to continue
"""

import logging
import time
from typing import Optional

logger = logging.getLogger("ItemSystem")


# Memory addresses from sshd-rando-backend/asm/symbols.yaml
class GameAddresses:
    """Memory addresses for game item system."""
    
    # Item system
    NUMBER_OF_ITEMS = 0x71018265fc
    ITEM_GET_BOTTLE_POUCH_SLOT = 0x71015904e8
    EQUIPPED_SWORD = 0x7101675c6c
    
    # Room/Stage management
    ROOM_MGR = 0x7102bfdd90
    STAGE_MGR = 0x7102bfdda8
    CURRENT_STAGE_NAME = 0x7102bfd8d8
    
    # Player
    PLAYER_PTR = 0x7102bfd940
    
    # Archipelago integration
    # Buffer is allocated as a Rust static variable in item.rs
    # To find the address: Search game memory for 16 bytes of zeros in 0x712e0a7000+ range
    # Or compile and check linker output for ARCHIPELAGO_BUFFER symbol
    # Default: Will be set after first compilation
    ARCHIPELAGO_ITEM_BUFFER = None  # Set this after finding the Rust static buffer address
    ARCHIPELAGO_BUFFER_SIZE = 16
    
    # Buffer structure (per entry):
    # Byte 0: Item ID (0 = empty slot)
    # Byte 1: Flags (0x01 = show animation, 0x02 = play jingle)
    # Bytes 2-3: Reserved


class GameItemSystem:
    """
    Interface to the game's built-in item spawning system.
    
    Requires ASM patch to monitor buffer and call give_item().
    """
    
    def __init__(self, memory_accessor):
        """
        Initialize the item system.
        
        Args:
            memory_accessor: MemoryAccessor instance for reading/writing game memory
        """
        self.memory = memory_accessor
        self.buffer_addr = None  # Will be found dynamically
        self.timeout_frames = 300  # 5 seconds at 60 FPS
        
    def _find_buffer_address(self) -> Optional[int]:
        """
        Find the Archipelago buffer address by searching for the Rust static allocation.
        
        The buffer is allocated in subsdk8 (0x712e0a7000+ range) as ARCHIPELAGO_BUFFER.
        We search for 16 bytes of zeros in writable memory near other Rust additions.
        
        Returns:
            Buffer address if found, None otherwise
        """
        # subsdk8 is loaded at 0x712e0a7000 based on loader output
        # Rust additions are compiled into this module
        # Search in a reasonable range (first 1MB of subsdk8)
        search_start = 0x712e0a7000
        search_end = search_start + 0x100000  # 1MB range
        
        logger.info(f"Searching for Archipelago buffer in range 0x{search_start:x}-0x{search_end:x}")
        
        # Search in 1KB chunks for efficiency
        chunk_size = 1024
        target_pattern = bytes([0] * 16)  # Looking for 16 zero bytes
        
        for addr in range(search_start, search_end, chunk_size):
            try:
                data = self.memory.read_bytes(addr, chunk_size)
                if data:
                    # Search for our 16-byte zero pattern
                    idx = data.find(target_pattern)
                    if idx != -1:
                        buffer_addr = addr + idx
                        # Verify it's writable by attempting a write/read test
                        if self._test_buffer_access(buffer_addr):
                            logger.info(f"✅ Found Archipelago buffer at 0x{buffer_addr:x}")
                            return buffer_addr
            except:
                continue
        
        logger.error("❌ Could not find Archipelago buffer address")
        return None
    
    def _test_buffer_access(self, addr: int) -> bool:
        """Test if we can write to the buffer address."""
        try:
            # Write test byte
            self.memory.write_byte(addr, 0x42)
            # Read it back
            val = self.memory.read_byte(addr)
            # Restore zero
            self.memory.write_byte(addr, 0x00)
            return val == 0x42
        except:
            return False
        
    def give_item(self, item_id: int, show_animation: bool = True, 
                  play_jingle: bool = True) -> bool:
        """
        Give an item to the player using the game's built-in system.
        
        This will:
        - Spawn an item actor
        - Show Link holding up the item (if show_animation=True)
        - Play the item-get jingle (if play_jingle=True)
        - Add the item to inventory
        - No stage reload required
        
        Args:
            item_id: Game item ID (0-255)
            show_animation: Whether to show item-get animation
            play_jingle: Whether to play jingle/fanfare
            
        Returns:
            True if item was given successfully, False otherwise
        """
        if not self.memory.connected:
            logger.error("Cannot give item: not connected to game")
            return False
        
        # Find buffer address on first use
        if self.buffer_addr is None:
            self.buffer_addr = self._find_buffer_address()
            if self.buffer_addr is None:
                logger.error("Cannot give item: buffer address not found")
                return False
        
        # Check if player is in valid state for receiving items
        if not self._is_player_ready():
            logger.warning("Player not ready to receive items")
            return False
        
        # Find empty slot in buffer
        slot = self._find_empty_buffer_slot()
        if slot is None:
            logger.error("Item buffer full - cannot queue item")
            return False
        
        # Prepare flags
        flags = 0
        if show_animation:
            flags |= 0x01
        if play_jingle:
            flags |= 0x02
        
        # Write to buffer
        buffer_offset = self.buffer_addr + (slot * 4)
        if not self.memory.write_byte(buffer_offset, item_id):
            logger.error(f"Failed to write item ID to buffer slot {slot}")
            return False
        
        if not self.memory.write_byte(buffer_offset + 1, flags):
            logger.error(f"Failed to write flags to buffer slot {slot}")
            return False
        
        logger.debug(f"Wrote item {item_id} to buffer slot {slot}")
        
        # Wait for game to process (buffer cleared when done)
        return self._wait_for_item_processed(buffer_offset)
    
    def give_item_by_name(self, item_name: str) -> bool:
        """
        Give an item by its name (from ITEM_TABLE).
        
        Args:
            item_name: Name of item (e.g., "Progressive Sword", "Clawshots")
            
        Returns:
            True if successful, False otherwise
        """
        # Import here to avoid circular dependency
        try:
            from Items import ITEM_TABLE
        except ImportError:
            logger.error("Failed to import ITEM_TABLE")
            return False
        
        if item_name not in ITEM_TABLE:
            logger.error(f"Unknown item: {item_name}")
            return False
        
        item_data = ITEM_TABLE[item_name]
        
        # Convert AP item ID to game item ID
        # This mapping depends on how your randomizer assigns IDs
        game_item_id = self._ap_id_to_game_id(item_data.code)
        
        if game_item_id is None:
            logger.error(f"No game ID mapping for {item_name}")
            return False
        
        return self.give_item(game_item_id)
    
    def _find_empty_buffer_slot(self) -> Optional[int]:
        """Find first empty slot in item buffer."""
        for slot in range(GameAddresses.ARCHIPELAGO_BUFFER_SIZE // 4):
            buffer_offset = self.buffer_addr + (slot * 4)
            item_id = self.memory.read_byte(buffer_offset)
            if item_id == 0:
                return slot
        return None
    
    def _wait_for_item_processed(self, buffer_offset: int) -> bool:
        """Wait for game to process item (clear buffer slot)."""
        for frame in range(self.timeout_frames):
            time.sleep(1.0 / 60.0)  # ~60 FPS
            
            item_id = self.memory.read_byte(buffer_offset)
            if item_id == 0:
                # Buffer cleared - item was processed
                logger.debug(f"Item processed after {frame} frames")
                return True
        
        logger.error(f"Item processing timeout after {self.timeout_frames} frames")
        # Clear buffer to prevent stuck state
        self.memory.write_byte(buffer_offset, 0)
        return False
    
    def _is_player_ready(self) -> bool:
        """Check if player is in valid state to receive items."""
        # Read player pointer
        player_ptr = self.memory.read_ptr(GameAddresses.PLAYER_PTR)
        if not player_ptr:
            return False
        
        # TODO: Add checks for:
        # - Player not in cutscene
        # - Player not in menu
        # - Player not in special action
        # - Stage is loaded
        
        # For now, just check if stage name is valid
        stage_name = self.memory.read_string(GameAddresses.CURRENT_STAGE_NAME, 8)
        if not stage_name or len(stage_name) == 0:
            return False
        
        return True
    
    def _ap_id_to_game_id(self, ap_item_id: int) -> Optional[int]:
        """
        Convert Archipelago item ID to game item ID.
        
        This mapping depends on your randomizer's item ID scheme.
        You'll need to create a proper mapping based on:
        - Items.py ITEM_TABLE codes
        - sshd-rando-backend/constants/itemnames.py IDs
        
        Args:
            ap_item_id: Archipelago item code
            
        Returns:
            Game item ID (0-255) or None if no mapping
        """
        # Base ID for SSHD items in Archipelago
        BASE_AP_ID = 2773000
        
        if ap_item_id < BASE_AP_ID:
            return None
        
        # Calculate offset from base
        offset = ap_item_id - BASE_AP_ID
        
        # For now, assume 1:1 mapping
        # TODO: Create proper mapping table for progressive items
        if 0 <= offset <= 255:
            return offset
        
        return None
    
    def clear_buffer(self):
        """Clear all slots in item buffer."""
        for slot in range(GameAddresses.ARCHIPELAGO_BUFFER_SIZE // 4):
            buffer_offset = self.buffer_addr + (slot * 4)
            self.memory.write_bytes(buffer_offset, bytes(4))
        logger.info("Cleared item buffer")


# ASM PATCH REQUIRED
# ====================
# Add this to sshd-rando-backend/asm/patches/archipelago-integration.asm:
#
# ; Archipelago Item Buffer Check
# ; Hook into main game loop to check for items to give
# .offset 0x71XXXXXXXX  ; Find suitable hook point in main loop
# 
# archipelago_check_item_buffer:
#     ; Save registers
#     stp x0, x1, [sp, #-16]!
#     stp x2, x3, [sp, #-16]!
#     
#     ; Load buffer address
#     ldr x0, =ARCHIPELAGO_ITEM_BUFFER
#     
#     ; Check first slot
#     ldrb w1, [x0]       ; Load item ID
#     cbz w1, buffer_empty ; Skip if 0
#     
#     ; Item found - call give_item
#     ldrb w2, [x0, #1]   ; Load flags
#     mov w8, #XX         ; Additions jumptable index for give_item
#     bl additions_jumptable
#     
#     ; Clear buffer slot
#     ldr x0, =ARCHIPELAGO_ITEM_BUFFER
#     str wzr, [x0]       ; Write 0 to clear (4 bytes)
#     
# buffer_empty:
#     ; Restore registers
#     ldp x2, x3, [sp], #16
#     ldp x0, x1, [sp], #16
#     
#     ; Continue normal execution
#     ret
#
# ARCHIPELAGO_ITEM_BUFFER:
#     .skip 16  ; Reserve 16 bytes for buffer
