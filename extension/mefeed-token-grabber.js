// Auto-grab auth token from Me Feed when user is logged in
// No more manual copy/paste needed!

console.log('Me Feed: Token auto-detection active');

// Check if user is logged into Me Feed
const token = localStorage.getItem('access_token');

if (token) {
  console.log('Me Feed: Found auth token, auto-saving to extension');
  
  // Send to extension background
  chrome.runtime.sendMessage({
    action: 'autoSaveToken',
    token: token
  }, (response) => {
    if (chrome.runtime.lastError) {
      console.error('Me Feed: Failed to save token:', chrome.runtime.lastError);
    } else {
      console.log('Me Feed: Token auto-saved successfully!');
    }
  });
} else {
  console.log('Me Feed: No token found (user not logged in)');
}

// Watch for login events (token changes)
const originalSetItem = localStorage.setItem;
localStorage.setItem = function(key, value) {
  originalSetItem.apply(this, arguments);
  
  if (key === 'access_token') {
    console.log('Me Feed: Token changed, auto-updating extension');
    chrome.runtime.sendMessage({
      action: 'autoSaveToken',
      token: value
    });
  }
};
