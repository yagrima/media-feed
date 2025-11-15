# Me Feed - Audible Library Sync Extension

## Installation Guide (Opera / Chrome / Edge)

### Prerequisites
- Opera, Chrome, Edge, or any Chromium-based browser
- Active Me Feed account
- Audible account

### Step 1: Install the Extension

1. **Download the extension folder** (this `extension` directory)

2. **Open your browser's extension page:**
   - **Opera:** `opera://extensions`
   - **Chrome:** `chrome://extensions`
   - **Edge:** `edge://extensions`

3. **Enable Developer Mode:**
   - Toggle the "Developer mode" switch in the top-right corner

4. **Load the extension:**
   - Click "Load unpacked" button
   - Select the `extension` folder from your computer
   - The extension should now appear in your extensions list

### Step 2: Get Your Auth Token

1. Open **Me Feed** in your browser: https://proud-courtesy-production-992b.up.railway.app

2. **Login** to your account

3. Go to **Settings** (top-right menu)

4. Find the **Developer** section

5. Click **"Show Auth Token"** or **"Generate Token"**

6. **Copy** the token (it starts with `ey...`)

### Step 3: Configure the Extension

1. **Click the extension icon** in your browser toolbar (📚 icon)

2. The popup will show "Login to Me Feed to enable sync"

3. **Paste your auth token** into the input field

4. Click **"Save Token"**

5. The extension will confirm "Token saved!"

### Step 4: Sync Your Library

#### Automatic Sync (Recommended):
1. Simply **visit your Audible library page:**
   - US: https://www.audible.com/library
   - DE: https://www.audible.de/library
   - UK: https://www.audible.co.uk/library
   - (Other marketplaces work too!)

2. The extension will **automatically scrape** your library

3. Within 2-3 seconds, books will **auto-sync** to Me Feed

4. You'll see a **desktop notification** when sync completes

5. The extension badge will show: ✓ (success) or +X (X new books)

#### Manual Sync:
1. Navigate to your **Audible library page**

2. Click the **extension icon** in toolbar

3. Click **"Sync Now"** button

4. Wait for sync to complete (shows progress spinner)

5. Success message will show imported/updated counts

### Step 5: Verify in Me Feed

1. Go back to **Me Feed**: https://proud-courtesy-production-992b.up.railway.app

2. Navigate to **Library** page

3. Filter by **Audiobooks** (if needed)

4. Your Audible library should now be visible!

## Supported Audible Marketplaces

- 🇺🇸 US: audible.com
- 🇩🇪 DE: audible.de
- 🇬🇧 UK: audible.co.uk
- 🇫🇷 FR: audible.fr
- 🇨🇦 CA: audible.ca
- 🇦🇺 AU: audible.com.au
- 🇮🇳 IN: audible.in
- 🇮🇹 IT: audible.it
- 🇯🇵 JP: audible.co.jp
- 🇪🇸 ES: audible.es

## How It Works

1. **No credentials needed** - Extension scrapes your library while you're logged into Audible in your browser

2. **Auto-detects changes** - Compares book count each time you visit library

3. **Smart syncing** - Only syncs when library changes detected

4. **Privacy-focused** - Your Audible credentials never leave your browser

5. **Rate-limited** - Backend limits imports to 20/hour to prevent abuse

## Troubleshooting

### Extension doesn't appear after installation
- Make sure "Developer mode" is enabled
- Try reloading the extension page (F5)
- Check browser console for errors

### "Please login to Me Feed first" error
- Make sure you've pasted a valid auth token
- Token should start with `ey...`
- Generate a new token from Me Feed Settings if expired

### "Please navigate to your Audible library page first"
- Extension only works on library pages (not home page, not book details)
- URL must contain `/library` path
- Make sure you're logged into Audible

### No books detected / Library empty
- Make sure your Audible library loaded completely (wait 3-5 seconds)
- Try scrolling down to load more books (if you have 100+ books)
- Try manual sync from extension popup
- Check browser console (F12) for scraping errors

### Sync fails with 401 error
- Your auth token expired or is invalid
- Generate a new token from Me Feed Settings
- Paste the new token in extension popup

### Sync fails with 429 error
- Rate limit exceeded (20 imports/hour)
- Wait 1 hour and try again
- This is a backend protection to prevent abuse

## Uninstallation

1. Go to browser extensions page
2. Find "Me Feed - Audible Sync"
3. Click "Remove" button
4. Your synced data in Me Feed will remain intact

## Privacy & Security

- ✅ Extension runs **locally in your browser**
- ✅ **No credentials** are stored or transmitted
- ✅ Only scrapes **publicly visible** data (what you already see on screen)
- ✅ Uses **your Me Feed auth token** (same as logging into the website)
- ✅ **Open source** - you can review all code in this folder
- ✅ **No tracking** or analytics

## Support

If you encounter issues:

1. Check browser console (F12 → Console tab)
2. Look for "Me Feed:" log messages
3. Report issues with console logs + screenshots

## Future Enhancements

Planned features:
- [ ] Periodic background sync (every 24 hours)
- [ ] Sync progress indicator
- [ ] Support for wish list
- [ ] Support for listening progress/bookmarks
- [ ] Settings page for customization
