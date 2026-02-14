"""
Launcher wrapper for SSHD Archipelago Client (Cross-platform)
"""
import zipfile
import sys
import os
from pathlib import Path

# Find .apworld file (cross-platform)
try:
    from platform_utils import get_custom_worlds_dir
    apworld_dir = get_custom_worlds_dir()
except ImportError:
    if sys.platform == "win32":
        apworld_dir = Path("C:/ProgramData/Archipelago/custom_worlds")
    elif sys.platform == "linux":
        apworld_dir = Path.home() / ".local" / "share" / "Archipelago" / "custom_worlds"
    else:
        apworld_dir = Path.home() / "Library" / "Application Support" / "Archipelago" / "custom_worlds"

APWORLD_PATH = apworld_dir / "sshd.apworld"

if not APWORLD_PATH.exists():
    print(f"ERROR: sshd.apworld not found at {APWORLD_PATH}")
    print(f"Expected location: {apworld_dir}")
    sys.exit(1)

# Add Archipelago lib directory to sys.path for dependencies
if sys.platform == "win32":
    lib_dir = Path("C:/ProgramData/Archipelago/lib")
elif sys.platform == "linux":
    lib_dir = Path.home() / ".local" / "share" / "Archipelago" / "lib"
else:
    lib_dir = Path.home() / "Library" / "Application Support" / "Archipelago" / "lib"

if lib_dir.exists():
    sys.path.insert(0, str(lib_dir))
    
    # Add kivy-deps DLL directories to PATH (Windows only)
    if sys.platform == "win32":
        # Try multiple possible locations for kivy-deps DLLs in lib directory
        possible_paths = [
            lib_dir / 'kivy_deps' / 'sdl2' / 'bin',
            lib_dir / 'kivy_deps.sdl2' / 'share' / 'kivy_deps-sdl2' / 'bin',
            lib_dir / 'share' / 'sdl2' / 'bin',
            lib_dir / 'kivy_deps' / 'glew' / 'bin',
            lib_dir / 'kivy_deps.glew' / 'share' / 'kivy_deps-glew' / 'bin',
            lib_dir / 'share' / 'glew' / 'bin',
        ]
        
        # Also check system Python site-packages for kivy-deps (if installed globally)
        try:
            import site
            for site_pkg in site.getsitepackages():
                site_path = Path(site_pkg)
                possible_paths.extend([
                    site_path / 'kivy_deps' / 'sdl2' / 'bin',
                    site_path / 'share' / 'sdl2' / 'bin',
                    site_path / 'kivy_deps' / 'glew' / 'bin',
                    site_path / 'share' / 'glew' / 'bin',
                ])
        except:
            pass
        
        for dep_path in possible_paths:
            if dep_path.exists():
                os.environ['PATH'] = str(dep_path) + os.pathsep + os.environ.get('PATH', '')

sys.path.insert(0, str(APWORLD_PATH))

# Extract and execute SSHDClient
zf = zipfile.ZipFile(str(APWORLD_PATH))
code = zf.read('sshd/SSHDClient.py').decode('utf-8')

# Execute with proper context
exec(code, {
    '__name__': '__main__',
    '__file__': f'{APWORLD_PATH}/sshd/SSHDClient.py',
    '__package__': 'sshd'
})
