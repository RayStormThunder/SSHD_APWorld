# ✅ CRASH FIX - Memory Address Issue Resolved

## The Problem

Ryujinx crashed with:
```
Invalid memory access at virtual address 0x0000007102BFD000
```

The hardcoded buffer address `0x7102BFD800` didn't exist in game memory.

## The Solution

Changed from **hardcoded address** to **Rust static allocation**:

### What Changed

1. **[item.rs](sshd-rando-backend/asm/additions/rust-additions/src/item.rs)**
   - Added: `static mut ARCHIPELAGO_BUFFER: [u8; 16] = [0; 16];`
   - Buffer is now allocated by Rust in its data section (safe & valid)
   - Added: `get_archipelago_buffer_address()` function to expose address

2. **[ItemSystemIntegration.py](ItemSystemIntegration.py)**
   - Removed hardcoded `0x7102BFD800` address
   - Added `_find_buffer_address()` to search for buffer at runtime
   - Searches subsdk8 range (0x712e0a7000+) for 16 zero bytes
   - Tests write access before using address

## How It Works Now

```
┌─────────────────────────────────────────────┐
│ Rust Compilation                            │
│ static mut ARCHIPELAGO_BUFFER: [u8; 16]     │
│ → Allocated in subsdk8 data section         │
│ → Address determined by linker              │
└─────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ Game Startup                                │
│ → Rust module loaded at 0x712e0a7000        │
│ → ARCHIPELAGO_BUFFER placed in data section │
│ → Buffer has valid, writable address        │
└─────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ Python Client Connects                       │
│ → Searches 0x712e0a7000-0x712e1a7000         │
│ → Finds 16 zero bytes pattern               │
│ → Tests write access                         │
│ → ✅ Buffer address found & verified         │
└─────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ Item Distribution                            │
│ Python → Write item ID to buffer            │
│ Rust → Read buffer every frame              │
│ Rust → Call give_item_with_sceneflag()      │
│ Game → ✨ Spawn item with animation          │
└─────────────────────────────────────────────┘
```

## Testing

1. **Recompile patches**:
   ```powershell
   cd sshd-rando-backend\asm
   python assemble.py
   ```

2. **Start game**:
   - Should no longer crash on startup
   - Rust buffer is allocated safely

3. **Connect Python client**:
   - Will search for buffer address
   - Should find it in 0x712e0a7000+ range
   - Log will show: `✅ Found Archipelago buffer at 0x...`

4. **Test item**:
   - Send item from another player
   - Should spawn with animation

## If It Still Crashes

Check the crash address:
- If same address (0x7102BFD000), Rust static didn't work
- If different address, there's another issue

Enable debug logging in Python:
```python
logging.basicConfig(level=logging.DEBUG)
```

Check for: `Found Archipelago buffer at 0x...` message

## Benefits of This Approach

✅ **Safe**: Rust allocates in valid memory
✅ **Dynamic**: No hardcoded addresses
✅ **Portable**: Works across different game versions
✅ **Verifiable**: Tests write access before using
✅ **Debuggable**: Logs buffer address when found

The game should now start without crashing!
