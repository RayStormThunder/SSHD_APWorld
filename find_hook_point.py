#!/usr/bin/env python3
"""
Hook Point Finder for Archipelago Integration

This script helps find suitable locations in the sshd-rando codebase
to hook the Archipelago item buffer check.

Usage:
    python find_hook_point.py
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def find_asm_files(base_dir: str = "sshd-rando-backend/asm") -> List[Path]:
    """Find all .asm files in the ASM directory."""
    asm_dir = Path(base_dir)
    if not asm_dir.exists():
        print(f"{Colors.FAIL}Error: {asm_dir} not found!{Colors.ENDC}")
        return []
    
    return list(asm_dir.rglob("*.asm"))


def search_for_patterns(files: List[Path], patterns: List[str]) -> List[Tuple[Path, int, str]]:
    """Search for specific patterns in ASM files."""
    results = []
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    for pattern in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            results.append((file_path, line_num, line.strip()))
        except Exception as e:
            print(f"{Colors.WARNING}Warning: Could not read {file_path}: {e}{Colors.ENDC}")
    
    return results


def find_existing_hooks() -> List[Tuple[Path, int, str]]:
    """Find existing hook points in the codebase."""
    print(f"\n{Colors.HEADER}=== Searching for existing hooks ==={Colors.ENDC}")
    
    patterns = [
        r'\.offset\s+0x[0-9a-fA-F]+',  # Any offset directive
        r'bl\s+additions_jumptable',    # Calls to additions
        r'main.*loop',                  # Main loop references
        r'update',                      # Update functions
        r'per.*frame',                  # Per-frame execution
    ]
    
    files = find_asm_files()
    results = search_for_patterns(files, patterns)
    
    return results


def find_suitable_locations():
    """Find suitable locations for the Archipelago hook."""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}Archipelago Hook Point Finder{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Looking for suitable hook locations...{Colors.ENDC}\n")
    
    # Find existing hooks
    hooks = find_existing_hooks()
    
    if not hooks:
        print(f"{Colors.FAIL}No hooks found! Make sure sshd-rando-backend/ is in the current directory.{Colors.ENDC}")
        return
    
    # Organize by file
    by_file = {}
    for file_path, line_num, line in hooks:
        if file_path not in by_file:
            by_file[file_path] = []
        by_file[file_path].append((line_num, line))
    
    # Display results
    print(f"{Colors.OKGREEN}Found {len(hooks)} potential hook points:{Colors.ENDC}\n")
    
    for file_path, lines in sorted(by_file.items()):
        print(f"{Colors.BOLD}{file_path.relative_to('sshd-rando-backend/asm')}:{Colors.ENDC}")
        for line_num, line in lines[:5]:  # Show first 5 per file
            print(f"  Line {line_num}: {line[:80]}")
        if len(lines) > 5:
            print(f"  ... and {len(lines) - 5} more")
        print()
    
    # Recommendations
    print(f"\n{Colors.HEADER}=== Recommendations ==={Colors.ENDC}")
    print("""
Good candidates for hooking:
1. Look for patches that run every frame
2. Avoid critical timing paths (collision, physics)
3. Prefer after input processing
4. Should be in 'patches/' directory

Suggested search in patches:
    - patches/mainloop-*.asm (if exists)
    - patches/player-*.asm (player update)
    - patches/game-*.asm (game state update)

Next steps:
1. Choose a patch file that runs frequently
2. Find an .offset with available space
3. Add your hook at that offset
4. Test thoroughly!
""")


def analyze_additions_jumptable():
    """Analyze the additions jumptable to find next available slot."""
    print(f"\n{Colors.HEADER}=== Analyzing Additions Jumptable ==={Colors.ENDC}")
    
    landingpad_file = Path("sshd-rando-backend/asm/additions/additions-landingpad.asm")
    
    if not landingpad_file.exists():
        print(f"{Colors.FAIL}Error: {landingpad_file} not found!{Colors.ENDC}")
        return
    
    try:
        with open(landingpad_file, 'r') as f:
            content = f.read()
        
        # Find all cmp instructions
        cmp_pattern = r'cmp\s+w8,\s*#(\d+)'
        matches = re.findall(cmp_pattern, content)
        
        if matches:
            numbers = [int(m) for m in matches]
            max_num = max(numbers)
            print(f"Found {len(numbers)} jumptable entries")
            print(f"Highest index used: #{max_num}")
            print(f"{Colors.OKGREEN}Use index #{max_num + 1} for your Archipelago hook{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}Could not parse jumptable entries{Colors.ENDC}")
            
    except Exception as e:
        print(f"{Colors.FAIL}Error reading jumptable: {e}{Colors.ENDC}")


def check_memory_addresses():
    """Check if proposed memory addresses are safe to use."""
    print(f"\n{Colors.HEADER}=== Checking Memory Addresses ==={Colors.ENDC}")
    
    symbols_file = Path("sshd-rando-backend/asm/symbols.yaml")
    
    if not symbols_file.exists():
        print(f"{Colors.FAIL}Error: {symbols_file} not found!{Colors.ENDC}")
        return
    
    # Proposed address for buffer
    proposed_addr = 0x7102BFD800
    
    print(f"Proposed buffer address: 0x{proposed_addr:X}")
    
    try:
        with open(symbols_file, 'r') as f:
            content = f.read()
        
        # Find addresses in the same range
        nearby_pattern = r'0x7102BFD[0-9A-Fa-f]{3}'
        nearby = re.findall(nearby_pattern, content)
        
        if nearby:
            print(f"\nNearby addresses in use:")
            for addr in sorted(set(nearby)):
                addr_val = int(addr, 16)
                # Check if within 256 bytes
                if abs(addr_val - proposed_addr) < 256:
                    distance = addr_val - proposed_addr
                    print(f"  {addr} (offset: {distance:+d} bytes)")
        
        print(f"\n{Colors.OKGREEN}Address 0x{proposed_addr:X} appears safe to use{Colors.ENDC}")
        print(f"Buffer size: 16 bytes (0x7102BFD800 - 0x7102BFD80F)")
        
    except Exception as e:
        print(f"{Colors.FAIL}Error checking addresses: {e}{Colors.ENDC}")


if __name__ == "__main__":
    print(f"{Colors.BOLD}Archipelago Integration - Hook Point Finder{Colors.ENDC}")
    print("=" * 60)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Run analysis
    find_suitable_locations()
    analyze_additions_jumptable()
    check_memory_addresses()
    
    print(f"\n{Colors.OKGREEN}Analysis complete!{Colors.ENDC}")
    print(f"\nNext steps:")
    print(f"1. Review the recommendations above")
    print(f"2. Edit {Colors.BOLD}archipelago-integration.asm{Colors.ENDC} with your chosen offset")
    print(f"3. Add entry to {Colors.BOLD}additions-landingpad.asm{Colors.ENDC}")
    print(f"4. Compile with: cd sshd-rando-backend/asm && python assemble.py")
    print(f"5. Test with your patched game!")
