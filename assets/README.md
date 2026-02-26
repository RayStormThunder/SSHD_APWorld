# Archipelago SSHD Assets

This folder contains custom assets for Archipelago SSHD patches.

## Custom Logo Files

To replace the title screen and credits logos with Archipelago branding, place the following TPL files in this folder:

1. **archipelago-logo.tpl** - Main logo for title screen and credits
   - Replaces `tr_wiiKing2Logo_00.tpl` (title) and `th_zeldaRogoEnd_02.tpl` (credits)
   - Should be created using BrawlCrate or wimgt from a PNG image
   
2. **archipelago-rogo_03.tpl** - Shiny effect layer 1
   - Used for the shiny animation overlay on the logo
   
3. **archipelago-rogo_04.tpl** - Shiny effect layer 2
   - Used for the shiny animation overlay on the logo

## Creating TPL Files

### Method 1: Using BrawlCrate (Recommended)
1. Open BrawlCrate
2. Create/import your logo PNG image
3. Export as TPL with proper settings (CMPR compression recommended)
4. Save with the appropriate filename

### Method 2: Using Wiimms Image Tool (wimgt)
1. Download wimgt from https://szs.wiimm.de/
2. Convert your PNG to TPL:
   ```bash
   wimgt encode your_logo.png -d . -o archipelago-logo.tpl --transform CMPR
   ```

## Image Specifications

- **Dimensions**: Match the original SSHD logo dimensions
- **Format**: CMPR (DXT1) compression is recommended for compatibility
- **Transparency**: Supported via RGB5A3 format if needed

## How It Works

When generating an Archipelago patch (`.apsshd` file):
1. The patch generation calls `patch_archipelago_logo()` from `rando/ArcPatcher.py`
2. It reads the three TPL files from this assets folder
3. It patches both `Title2D.arc` (title screen) and `EndRoll.arc` (credits)
4. The patched arc files are included in the romfs folder of the patch
5. When Ryujinx loads the mod, it displays your custom Archipelago logo!

## Original Randomizer Logo

For reference, the original sshd-rando logo files can be found in:
`sshd-rando-backend/assets/sshdr-logo.tpl`

You can use these as a template for dimensions and format.
