// Popup UI logic

console.log('Me Feed: Popup loaded');

// DOM elements
const authRequired = document.getElementById('authRequired');
const statusSection = document.getElementById('statusSection');
const authTokenInput = document.getElementById('authToken');
const saveTokenBtn = document.getElementById('saveTokenBtn');
const syncBtn = document.getElementById('syncBtn');
const syncBtnText = document.getElementById('syncBtnText');
const settingsBtn = document.getElementById('settingsBtn');
const messageContainer = document.getElementById('messageContainer');

const statusBadge = document.getElementById('statusBadge');
const bookCount = document.getElementById('bookCount');
const lastSync = document.getElementById('lastSync');

/**
 * Initialize popup
 */
async function init() {
  console.log('Me Feed: Initializing popup...');
  
  // Get current status
  const status = await getStatus();
  console.log('Me Feed: Current status:', status);
  
  if (status.isAuthenticated) {
    showStatusSection(status);
  } else {
    showAuthSection();
  }
}

/**
 * Get extension status from background
 */
async function getStatus() {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage({ action: 'getStatus' }, (response) => {
      resolve(response || {});
    });
  });
}

/**
 * Show authentication section
 */
function showAuthSection() {
  authRequired.classList.remove('hidden');
  statusSection.classList.add('hidden');
  syncBtn.disabled = true;
}

/**
 * Show status section
 */
function showStatusSection(status) {
  authRequired.classList.add('hidden');
  statusSection.classList.remove('hidden');
  syncBtn.disabled = false;
  
  // Update status display
  if (status.isAuthenticated) {
    statusBadge.textContent = 'Connected';
    statusBadge.className = 'badge badge-success';
  } else {
    statusBadge.textContent = 'Not Connected';
    statusBadge.className = 'badge badge-error';
  }
  
  // Update book count
  bookCount.textContent = status.bookCount || 0;
  
  // Update last sync time
  if (status.lastSyncTime) {
    const date = new Date(status.lastSyncTime);
    const now = Date.now();
    const diff = now - status.lastSyncTime;
    
    if (diff < 60000) {
      lastSync.textContent = 'Just now';
    } else if (diff < 3600000) {
      lastSync.textContent = `${Math.floor(diff / 60000)} mins ago`;
    } else if (diff < 86400000) {
      lastSync.textContent = `${Math.floor(diff / 3600000)} hours ago`;
    } else {
      lastSync.textContent = date.toLocaleDateString();
    }
  } else {
    lastSync.textContent = 'Never';
  }
  
  // Show last sync result if available
  if (status.lastSyncResult) {
    const result = status.lastSyncResult;
    if (result.success) {
      showMessage(
        `Last sync: ${result.imported} new, ${result.updated} updated, ${result.total} total`,
        'success'
      );
    }
  }
}

/**
 * Show message to user
 */
function showMessage(text, type = 'success') {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message message-${type}`;
  messageDiv.textContent = text;
  
  messageContainer.innerHTML = '';
  messageContainer.appendChild(messageDiv);
  
  // Auto-hide after 5 seconds
  setTimeout(() => {
    messageDiv.remove();
  }, 5000);
}

/**
 * Save auth token
 */
async function saveToken() {
  const token = authTokenInput.value.trim();
  
  if (!token) {
    showMessage('Please enter your auth token', 'error');
    return;
  }
  
  console.log('Me Feed: Saving auth token...');
  
  try {
    // Save token to storage
    await chrome.storage.local.set({ authToken: token });
    
    showMessage('Token saved! You can now sync your library.', 'success');
    
    // Refresh UI
    setTimeout(() => {
      init();
    }, 1500);
    
  } catch (error) {
    console.error('Me Feed: Failed to save token:', error);
    showMessage('Failed to save token: ' + error.message, 'error');
  }
}

/**
 * Trigger manual sync
 */
async function syncNow() {
  console.log('Me Feed: Manual sync triggered');
  
  // Disable button and show loading
  syncBtn.disabled = true;
  syncBtnText.innerHTML = 'Syncing... <span class="spinner"></span>';
  
  try {
    const response = await new Promise((resolve, reject) => {
      chrome.runtime.sendMessage({ action: 'syncNow' }, (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else {
          resolve(response);
        }
      });
    });
    
    if (response.success) {
      const result = response.data;
      showMessage(
        `Synced! ${result.imported} new, ${result.updated} updated, ${result.total} total`,
        'success'
      );
      
      // Refresh status
      setTimeout(() => {
        init();
      }, 1500);
    } else {
      throw new Error(response.error || 'Sync failed');
    }
    
  } catch (error) {
    console.error('Me Feed: Sync failed:', error);
    showMessage('Sync failed: ' + error.message, 'error');
  } finally {
    // Re-enable button
    syncBtn.disabled = false;
    syncBtnText.innerHTML = 'Sync Now';
  }
}

/**
 * Open Me Feed in new tab
 */
function openMeFeed() {
  chrome.tabs.create({
    url: 'https://proud-courtesy-production-992b.up.railway.app/settings'
  });
}

// Event listeners
saveTokenBtn.addEventListener('click', saveToken);
syncBtn.addEventListener('click', syncNow);
settingsBtn.addEventListener('click', openMeFeed);

// Allow Enter key in auth token input
authTokenInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    saveToken();
  }
});

// Initialize on load
init();
