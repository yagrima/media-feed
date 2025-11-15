# Extension Icons

The extension requires 3 icon sizes:
- `icon16.png` - 16x16 pixels (toolbar)
- `icon48.png` - 48x48 pixels (extensions page)
- `icon128.png` - 128x128 pixels (Chrome Web Store)

## Quick Solution: Use Placeholder Icons

You can create simple colored square placeholders:

### Option 1: Online Icon Generator
1. Go to: https://www.favicon-generator.org/
2. Upload any image (or create a simple colored square)
3. Download generated icons
4. Rename them to `icon16.png`, `icon48.png`, `icon128.png`
5. Place in this `extension` folder

### Option 2: Use PowerShell to Generate Simple Placeholders

Run this PowerShell script in the extension folder:

```powershell
# This creates simple colored PNG files as placeholders
# You'll need ImageMagick installed, or use an online tool instead

# Or just use any PNG image you have and resize it:
# - Copy any PNG file as icon16.png, icon48.png, icon128.png
# - The extension will work fine with these
```

### Option 3: Use the Me Feed Logo

If Me Feed has a logo, convert it to these 3 sizes.

### Option 4: Simple Unicode Icon (Quickest!)

For testing, you can even use a simple emoji or text:
1. Create a 128x128 canvas
2. Add the 📚 emoji or "MF" text
3. Export as PNG
4. Resize to 16x16 and 48x48 for other sizes

## Current Status

**The extension will work without icons during development**, but you'll see broken image placeholders in the browser toolbar and extensions page.

To test the extension immediately:
1. Comment out the `icons` and `default_icon` sections in `manifest.json`
2. Load the extension
3. It will work but show a generic puzzle piece icon

## For Production

For a production release (Chrome Web Store, etc.), proper icons are required.

Design guidelines:
- Use Me Feed brand colors
- Make it recognizable at 16x16 size
- Keep it simple (avoid detailed graphics)
- Consider using book/audiobook imagery (📚 🎧)
- Purple gradient matches the popup UI

## Quick Temporary Fix

Just create 3 copies of any small PNG image you have:
```bash
# Copy any PNG file 3 times with different names
copy someimage.png icon16.png
copy someimage.png icon48.png
copy someimage.png icon128.png
```

The extension will work perfectly with these placeholders!
