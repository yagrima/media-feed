// Content script - runs on Audible library pages
// Automatically scrapes audiobook data when user visits their library

console.log('Me Feed: Content script loaded on Audible library page');

/**
 * Scrape audiobook data from Audible library page
 * @returns {Array} Array of book objects
 */
function scrapeAudibleLibrary() {
  console.log('Me Feed: Starting library scrape...');
  
  const books = [];
  
  // Audible library uses different selectors depending on the marketplace
  // This works for most Audible sites (tested on .com, .de)
  const bookElements = document.querySelectorAll('.adbl-library-content-row, [data-asin]');
  
  console.log(`Me Feed: Found ${bookElements.length} potential book elements`);
  
  bookElements.forEach((element, index) => {
    try {
      // Extract ASIN (unique Amazon ID)
      const asin = element.getAttribute('data-asin') || 
                   element.querySelector('[data-asin]')?.getAttribute('data-asin');
      
      if (!asin) {
        console.log(`Me Feed: Skipping element ${index} - no ASIN found`);
        return; // Skip if no ASIN
      }
      
      // Extract title
      const titleElement = element.querySelector('.bc-heading, .bc-size-headline3, h3, .bc-text');
      const title = titleElement?.textContent?.trim();
      
      if (!title) {
        console.log(`Me Feed: Skipping ASIN ${asin} - no title found`);
        return; // Skip if no title
      }
      
      // Extract authors
      const authorElements = element.querySelectorAll('.authorLabel a, .bc-color-secondary a');
      const authors = Array.from(authorElements).map(a => a.textContent.trim()).filter(Boolean);
      
      // Extract narrators
      const narratorElements = element.querySelectorAll('.narratorLabel a');
      const narrators = Array.from(narratorElements).map(n => n.textContent.trim()).filter(Boolean);
      
      // Extract length (runtime)
      const lengthElement = element.querySelector('.runtimeLabel, .bc-color-secondary');
      const lengthText = lengthElement?.textContent?.trim();
      let lengthMinutes = null;
      
      if (lengthText) {
        // Parse "X hrs and Y mins" or "X h Y min" format
        const hours = lengthText.match(/(\d+)\s*(hrs?|h|stunden?)/i);
        const minutes = lengthText.match(/(\d+)\s*(mins?|m|minuten?)/i);
        
        if (hours || minutes) {
          lengthMinutes = (hours ? parseInt(hours[1]) * 60 : 0) + 
                         (minutes ? parseInt(minutes[1]) : 0);
        }
      }
      
      // Extract cover image
      const coverElement = element.querySelector('img');
      const coverUrl = coverElement?.src || coverElement?.getAttribute('data-lazy');
      
      // Extract release date (if available)
      const releaseDateElement = element.querySelector('.releaseDateLabel');
      const releaseDate = releaseDateElement?.textContent?.trim();
      
      // Extract series info (if available)
      const seriesElement = element.querySelector('.seriesLabel');
      const series = seriesElement?.textContent?.trim();
      
      const book = {
        title,
        authors: authors.length > 0 ? authors : ['Unknown Author'],
        narrators,
        length_minutes: lengthMinutes,
        asin,
        cover_url: coverUrl,
        release_date: releaseDate || null,
        series: series || null
      };
      
      books.push(book);
      console.log(`Me Feed: Scraped book ${index + 1}: ${title} (${asin})`);
      
    } catch (error) {
      console.error(`Me Feed: Error scraping element ${index}:`, error);
    }
  });
  
  console.log(`Me Feed: Successfully scraped ${books.length} books`);
  return books;
}

/**
 * Detect marketplace from URL
 * @returns {string} Marketplace code (us, de, uk, etc.)
 */
function detectMarketplace() {
  const hostname = window.location.hostname;
  
  if (hostname.includes('.audible.de')) return 'de';
  if (hostname.includes('.audible.co.uk')) return 'uk';
  if (hostname.includes('.audible.fr')) return 'fr';
  if (hostname.includes('.audible.ca')) return 'ca';
  if (hostname.includes('.audible.com.au')) return 'au';
  if (hostname.includes('.audible.in')) return 'in';
  if (hostname.includes('.audible.it')) return 'it';
  if (hostname.includes('.audible.co.jp')) return 'jp';
  if (hostname.includes('.audible.es')) return 'es';
  
  return 'us'; // Default to US
}

/**
 * Auto-scrape when page is loaded
 */
function autoScrape() {
  // Wait for page to fully load
  if (document.readyState === 'complete') {
    performScrape();
  } else {
    window.addEventListener('load', performScrape);
  }
}

function performScrape() {
  console.log('Me Feed: Page loaded, starting auto-scrape...');
  
  // Wait a bit for dynamic content to render
  setTimeout(() => {
    const books = scrapeAudibleLibrary();
    const marketplace = detectMarketplace();
    
    if (books.length > 0) {
      // Send to background script for syncing
      chrome.runtime.sendMessage({
        action: 'libraryScraped',
        books,
        marketplace
      }, (response) => {
        if (chrome.runtime.lastError) {
          console.error('Me Feed: Error sending message:', chrome.runtime.lastError);
        } else {
          console.log('Me Feed: Message sent to background script', response);
        }
      });
    } else {
      console.warn('Me Feed: No books found on page');
    }
  }, 2000); // 2 second delay for page to fully render
}

// Start auto-scrape
autoScrape();

// Listen for messages from popup or background
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'manualScrape') {
    console.log('Me Feed: Manual scrape requested');
    const books = scrapeAudibleLibrary();
    const marketplace = detectMarketplace();
    sendResponse({ books, marketplace });
  }
  return true; // Keep channel open for async response
});
