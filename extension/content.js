// Content script - runs on Audible library pages
// Automatically scrapes audiobook data when user visits their library

console.log('Me Feed: Content script loaded on Audible library page');

/**
 * Scrape audiobook data from Audible library page
 * @param {Document} doc - The document object to scrape (defaults to current document)
 * @returns {Array} Array of book objects
 */
function scrapeAudibleLibrary(doc = document) {
  console.log('Me Feed: Starting library scrape...');
  
  const books = [];
  const seenAsins = new Set(); // Track duplicates
  
  // Audible library uses different selectors depending on the marketplace
  // More specific: only get actual library item containers
  const bookElements = doc.querySelectorAll('li.productListItem, .adbl-library-content-row');
  
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
      
      // Skip duplicates
      if (seenAsins.has(asin)) {
        console.log(`Me Feed: Skipping duplicate ASIN ${asin}`);
        return;
      }
      
      // Extract title - be more specific to avoid buttons
      const titleElement = element.querySelector('h3, .bc-heading, .bc-size-headline3');
      const title = titleElement?.textContent?.trim();
      
      if (!title) {
        console.log(`Me Feed: Skipping ASIN ${asin} - no title found`);
        return; // Skip if no title
      }
      
      // Filter out invalid titles (buttons, UI elements)
      if (title.includes('Favoriten') || title.includes('Favorite') || title.length < 3) {
        console.log(`Me Feed: Skipping ASIN ${asin} - invalid title: "${title}"`);
        return;
      }
      
      seenAsins.add(asin); // Mark as seen
      
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
 * Scrape all pages by following pagination
 * @returns {Promise<Array>} All books from all pages
 */
async function scrapeAllPages() {
  console.log('Me Feed: Starting deep scrape of all pages...');
  
  // Keep track of unique ASINs to prevent loops
  const uniqueAsins = new Set();
  let allBooks = [];
  
  // 1. Scrape current page first
  const firstPageBooks = scrapeAudibleLibrary(document);
  
  firstPageBooks.forEach(book => {
    if (book.asin && !uniqueAsins.has(book.asin)) {
      uniqueAsins.add(book.asin);
      allBooks.push(book);
    }
  });
  
  let currentPageDoc = document;
  let pageNum = 1;
  const MAX_PAGES = 100; // Safety limit
  
  // 2. Loop through pagination
  while (pageNum < MAX_PAGES) {
    // Find "Next" button
    // Selectors cover various Audible regions/layouts
    // Added .bc-state-disabled check for button itself
    const nextBtn = currentPageDoc.querySelector('.pagingElements .nextButton a:not(.bc-state-disabled), span.nextButton > a:not(.bc-state-disabled)');
    
    // Stop if no next button or button's container is disabled
    if (!nextBtn || !nextBtn.href || nextBtn.parentElement.classList.contains('bc-state-disabled') || nextBtn.classList.contains('bc-state-disabled')) {
      console.log('Me Feed: No next page found or reached end. Finishing.');
      break;
    }
    
    const nextUrl = nextBtn.href;
    
    // Prevent circular links (e.g. next button linking to current page)
    if (nextUrl === window.location.href || nextUrl === '#' || nextUrl.includes('javascript:')) {
       console.log('Me Feed: Next button links to current page. Stopping.');
       break;
    }

    console.log(`Me Feed: Fetching page ${pageNum + 1}...`);
    
    try {
      // Add delay to be polite to Audible servers (1s)
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const response = await fetch(nextUrl);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const text = await response.text();
      const parser = new DOMParser();
      currentPageDoc = parser.parseFromString(text, 'text/html');
      
      const newBooks = scrapeAudibleLibrary(currentPageDoc);
      
      if (newBooks.length === 0) {
        console.warn(`Me Feed: Page ${pageNum + 1} loaded but no books found. Stopping.`);
        break;
      }
      
      // Deduplication check: If no NEW books are found on this page, we are likely looping
      let newUniqueCount = 0;
      newBooks.forEach(book => {
        if (book.asin && !uniqueAsins.has(book.asin)) {
          uniqueAsins.add(book.asin);
          allBooks.push(book);
          newUniqueCount++;
        }
      });
      
      console.log(`Me Feed: Found ${newBooks.length} books on page ${pageNum + 1} (${newUniqueCount} new)`);
      
      if (newUniqueCount === 0) {
        console.warn(`Me Feed: Page ${pageNum + 1} contained only duplicate books. Assuming end of list. Stopping.`);
        break;
      }
      
      pageNum++;
      
    } catch (error) {
      console.error(`Me Feed: Error fetching page ${pageNum + 1}:`, error);
      break;
    }
  }
  
  console.log(`Me Feed: Total scrape complete. Found ${allBooks.length} unique books across ${pageNum} pages.`);
  return allBooks;
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

async function performScrape() {
  console.log('Me Feed: Page loaded, starting auto-scrape...');
  
  // Wait a bit for dynamic content to render
  setTimeout(async () => {
    try {
      // Use deep scrape to get all pages
      const books = await scrapeAllPages();
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
    } catch (e) {
      console.error('Me Feed: Auto-scrape failed', e);
    }
  }, 2000); // 2 second delay for page to fully render
}

// Start auto-scrape
autoScrape();

// Listen for messages from popup or background
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'manualScrape') {
    console.log('Me Feed: Manual scrape requested');
    
    // Must return true to keep channel open for async response
    scrapeAllPages().then(books => {
      const marketplace = detectMarketplace();
      sendResponse({ books, marketplace });
    });
    
    return true; 
  }
});
