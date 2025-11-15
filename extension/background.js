// Background service worker - handles syncing data to Me Feed backend

console.log('Me Feed: Background service worker loaded');

// Configuration
const BACKEND_URL = 'https://media-feed-production.up.railway.app';
// const BACKEND_URL = 'http://localhost:8000'; // Uncomment for local development

/**
 * Handle messages from content script
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Me Feed: Background received message:', message.action);
  
  if (message.action === 'libraryScraped') {
    handleLibraryScraped(message.books, message.marketplace)
      .then(response => {
        sendResponse({ success: true, data: response });
      })
      .catch(error => {
        console.error('Me Feed: Sync failed:', error);
        sendResponse({ success: false, error: error.message });
      });
    return true; // Keep channel open for async response
  }
  
  if (message.action === 'getStatus') {
    getExtensionStatus()
      .then(status => sendResponse(status))
      .catch(error => sendResponse({ error: error.message }));
    return true;
  }
  
  if (message.action === 'syncNow') {
    // Trigger manual sync from popup
    handleManualSync()
      .then(response => sendResponse({ success: true, data: response }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true;
  }
});

/**
 * Handle library data scraped from Audible
 */
async function handleLibraryScraped(books, marketplace) {
  console.log(`Me Feed: Processing ${books.length} books from ${marketplace} marketplace`);
  
  // Get stored data to compare
  const stored = await chrome.storage.local.get(['lastBookCount', 'lastSyncTime', 'authToken']);
  const lastCount = stored.lastBookCount || 0;
  const newCount = books.length;
  
  console.log(`Me Feed: Last count: ${lastCount}, New count: ${newCount}`);
  
  // Check if Me Feed auth token exists
  if (!stored.authToken) {
    console.warn('Me Feed: No auth token found - user needs to login first');
    
    // Show badge to indicate action needed
    await chrome.action.setBadgeText({ text: '!' });
    await chrome.action.setBadgeBackgroundColor({ color: '#FF5722' });
    
    return {
      status: 'auth_required',
      message: 'Please login to Me Feed first'
    };
  }
  
  // Check if library changed
  if (newCount !== lastCount) {
    const diff = newCount - lastCount;
    console.log(`Me Feed: Library changed by ${diff} books`);
    
    // Update badge
    if (diff > 0) {
      await chrome.action.setBadgeText({ text: `+${diff}` });
      await chrome.action.setBadgeBackgroundColor({ color: '#4CAF50' });
    }
    
    // Auto-sync to backend (if enabled)
    const settings = await chrome.storage.local.get(['autoSync']);
    if (settings.autoSync !== false) { // Default to true
      console.log('Me Feed: Auto-syncing to backend...');
      
      try {
        const result = await syncToBackend(books, marketplace, stored.authToken);
        
        // Update stored data
        await chrome.storage.local.set({
          lastBookCount: newCount,
          lastSyncTime: Date.now(),
          lastSyncResult: result
        });
        
        // Show success notification
        await chrome.notifications.create({
          type: 'basic',
          iconUrl: 'icon128.png',
          title: 'Audible Synced!',
          message: `${result.imported} new, ${result.updated} updated, ${result.total} total audiobooks`
        });
        
        // Update badge to show success
        await chrome.action.setBadgeText({ text: '✓' });
        await chrome.action.setBadgeBackgroundColor({ color: '#4CAF50' });
        
        // Clear badge after 5 seconds
        setTimeout(async () => {
          await chrome.action.setBadgeText({ text: '' });
        }, 5000);
        
        return result;
        
      } catch (error) {
        console.error('Me Feed: Sync to backend failed:', error);
        
        // Show error badge
        await chrome.action.setBadgeText({ text: '✗' });
        await chrome.action.setBadgeBackgroundColor({ color: '#F44336' });
        
        throw error;
      }
    }
  } else {
    console.log('Me Feed: No changes detected, skipping sync');
  }
  
  return {
    status: 'no_changes',
    bookCount: newCount
  };
}

/**
 * Sync books to Me Feed backend
 */
async function syncToBackend(books, marketplace, authToken) {
  console.log(`Me Feed: Syncing ${books.length} books to backend...`);
  
  const response = await fetch(`${BACKEND_URL}/api/audible/import-from-extension`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`
    },
    body: JSON.stringify({
      books,
      marketplace
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
  }
  
  const result = await response.json();
  console.log('Me Feed: Sync successful:', result);
  
  return result;
}

/**
 * Get extension status
 */
async function getExtensionStatus() {
  const stored = await chrome.storage.local.get([
    'lastBookCount',
    'lastSyncTime',
    'lastSyncResult',
    'authToken',
    'autoSync'
  ]);
  
  return {
    isAuthenticated: !!stored.authToken,
    bookCount: stored.lastBookCount || 0,
    lastSyncTime: stored.lastSyncTime || null,
    lastSyncResult: stored.lastSyncResult || null,
    autoSync: stored.autoSync !== false
  };
}

/**
 * Handle manual sync triggered from popup
 */
async function handleManualSync() {
  console.log('Me Feed: Manual sync requested');
  
  // Get active tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  if (!tab || !tab.url.includes('audible.')) {
    throw new Error('Please navigate to your Audible library page first');
  }
  
  // Request scrape from content script
  const response = await chrome.tabs.sendMessage(tab.id, { action: 'manualScrape' });
  
  if (response && response.books) {
    const stored = await chrome.storage.local.get(['authToken']);
    
    if (!stored.authToken) {
      throw new Error('Please login to Me Feed first');
    }
    
    const result = await syncToBackend(response.books, response.marketplace, stored.authToken);
    
    // Update stored data
    await chrome.storage.local.set({
      lastBookCount: response.books.length,
      lastSyncTime: Date.now(),
      lastSyncResult: result
    });
    
    return result;
  }
  
  throw new Error('Failed to scrape library data');
}

// Listen for extension installation
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('Me Feed: Extension installed');
    // Set default settings
    chrome.storage.local.set({
      autoSync: true
    });
  }
});
