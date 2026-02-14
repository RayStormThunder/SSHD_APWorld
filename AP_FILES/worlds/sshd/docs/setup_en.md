# Skyward Sword HD Archipelago Setup Guide

This guide will help you set up Skyward Sword HD for Archipelago multiplayer randomizer using Ryujinx.

## System Requirements
- **Archipelago**: Version 0.5.0 or higher (Tested with 0.6.6)
- **Python**: 3.10 or higher (Tested with Python 3.13.9)
- **Emulator**: Ryujinx (Tested on 1.1.1376)
- **Game**: The Legend of Zelda: Skyward Sword HD and Update Data (Switch)

## Quick Start

### 0. Install Python and dependencies

- Install Python 3.10 or higher, 3.13.9 recommended (MAKE SURE TO ADD IT TO PATH)
- Download and install the dependencies from [requirements.txt](requirements.txt) using either `pip install -r requirements.txt` or if that doesn't work `pip install --target="C:\ProgramData\Archipelago\lib" -r requirements.txt` (change the target path if necessary)

### 1. Install the APWorld and other files

The APWorld will auto-deploy to the correct location for your OS (if building manually):
- **Windows**: `C:\ProgramData\Archipelago\custom_worlds\`
- **Linux**: `~/.local/share/Archipelago/custom_worlds/`
- **macOS**: `~/Library/Application Support/Archipelago/custom_worlds/`

Or manually place `sshd.apworld` in your platform's custom_worlds folder if running from the release.

Place `launch_sshd_wrapper.py` in the Archipelago folder

If using Windows: Place `launch_sshd.bat` in in the Archipelago folder (or somewhere else - it works from anywhere)

### 2. Extract Your Game

You'll need a legally obtained copy of Skyward Sword HD for Nintendo Switch along with the update data.

1. Extract the RomFS and ExeFS from your game using Ryujinx (MAKE SURE THE UPDATE IS INSTALLED BEFORE EXTRACTING)
2. Extract them to your platform's default location:
   - **Windows**: `C:\ProgramData\Archipelago\sshd_extract\`
   - **Linux**: `~/.local/share/Archipelago/sshd_extract/`
   - **macOS**: `~/Library/Application Support/Archipelago/sshd_extract/`
3. Create `romfs/` and `exefs/` subdirectories with your extracted files

### 3. Generate Your Seed

1. Download the [Skyward Sword HD Randomizer](https://github.com/mint-choc-chip-skyblade/sshd-rando/releases/latest)
2. Configure all of your options (don't generate)
3. Open SkywardSwordHD.yaml for use as a template
4. Use Method 1 and input the path to your `config.yaml` file (in the SSHD Rando folder)
5. Put it in `C:\ProgramData\Archipelago\Players`
6. Generate locally using all player yamls
    - Open the Archipelago Launcher and click 'Generate'
    - The outputed file should be in `C:\ProgramData\Archipelago\output`

#### From here you have 3 options
1. Upload the outputed zip to [https://archipelago.randomstuff.cc](https://archipelago.randomstuff.cc) (the official website won't work due to a 64MB file upload limit)
   - IF YOU USE THIS, THE WEBSOCKET URL IS NOT `archipelago.randomstuff.cc`, YOU NEED TO INPUT `ap.randomstuff.cc:PORT` INTO YOUR CLIENT
2. Host locally (requires port forwarding or everyone being on the same LAN)
3. Unzip the outputed zip file and remove the patch file
   - Unzip the generated `.zip` file
   - Copy the `.apsshd` file to another spot
   - Delete it from the unziped folder and rezip
   - Now extract `.apsshd` and copy `romfs` and `exefs` to your Ryujinx mod directory (located at `C:\Users\Your_Username\AppData\Roaming\Ryujinx\sdcard\atmosphere\contents\01002da013484000\Archipelago` on Windows - you will need to create the `Archipelago` folder)
   - You can now delete the patch file and upload the rezipped `.zip` file to [archipelago.gg](https://archipelago.gg)

### 4. Open Ryujinx
Make sure the mod and 1.0.1 update are enabled and open Skyward Sword HD

You should see the custom Archipelago logo - that means it's working

Get into the game far enough to where you can move Link

### 4. Launch the Client
Double click `launch_sshd.bat` if on Windows or run `python launch_sshd_wrapper.py` if on Linux/macOS

### 5. Play!
Items you find are automatically sent to other players and vice-versa!