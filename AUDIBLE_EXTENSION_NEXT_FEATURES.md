# Audible Extension - Next Features

## Session Summary (Nov 15, 2025)
**Status:** ✅ Working! Books syncing from Audible → Me Feed
**Lives:** 1/11 (Milestone reached: +2 bonus)

## What's Working Now
- ✅ Browser extension auto-scrapes Audible library
- ✅ Auto-syncs to Me Feed backend (20 books imported)
- ✅ Auto-token detection (no manual copy/paste needed)
- ✅ Token lasts 7 days (increased from 15 minutes)
- ✅ Handles missing book data gracefully (null runtime)

## Feature Requests for Next Session

### FR-1: Add Audiobooks Category
**Request:** Add dedicated "audiobooks" category/filter
**Current:** Books imported as media type "audiobook" but no dedicated category UI
**Implementation:**
- Add category to frontend filters
- Ensure database has proper category field
- Update import logic to assign category

### FR-2: Group Audiobooks by Series
**Request:** Group books from same series together in library view
**Current:** All books displayed individually in flat list
**Implementation:**
- Detect series info from Audible (already scraped: `series: "The Lord of the Rings #0"`)
- Add series grouping to library view
- Show series title as group header
- Option to collapse/expand series
- Sort books within series by sequence number

**Technical notes:**
- Series data already in metadata: `metadata['series'] = series_info`
- Series format: `"Series Name #X"` or `"Series Name, Book X"`
- Need to parse series name and sequence number
- Group by series name, sort by sequence

### FR-3: Scrape All Pages (Pagination)
**Request:** Read all pages of Audible library, not just first page
**Current:** Extension only scrapes visible books on first page load
**Limitation:** Users with 100+ books only get first ~20 books

**Implementation Options:**

**Option A: Infinite Scroll Detection**
- Watch for scroll events
- Detect when Audible loads more books (lazy loading)
- Wait for new content to appear
- Scrape incrementally as user scrolls

**Option B: Auto-Scroll & Scrape**
- Extension auto-scrolls to bottom
- Triggers Audible's lazy loading
- Waits for all books to load
- Scrapes complete library
- More reliable but takes longer

**Option C: Pagination Detection**
- Detect "Load More" or pagination buttons
- Programmatically click them
- Wait for content load
- Repeat until all pages loaded

**Recommended:** Option B (Auto-scroll)
- Most reliable across different Audible versions
- Works with infinite scroll and pagination
- User sees progress (page scrolling)
- Can show "Loading..." indicator

**Technical Implementation:**
```javascript
async function scrapeAllPages() {
  let previousCount = 0;
  let currentCount = 0;
  let noNewBooksCount = 0;
  
  do {
    // Scroll to bottom
    window.scrollTo(0, document.body.scrollHeight);
    
    // Wait for new content
    await sleep(2000);
    
    // Count books
    currentCount = document.querySelectorAll('li.productListItem').length;
    
    // Check if new books loaded
    if (currentCount === previousCount) {
      noNewBooksCount++;
    } else {
      noNewBooksCount = 0;
      previousCount = currentCount;
    }
    
    // Stop if no new books after 3 attempts
  } while (noNewBooksCount < 3);
  
  // Scrape all loaded books
  return scrapeAudibleLibrary();
}
```

### FR-4: Better Series Detection (Enhancement)
**Related to FR-2**
**Current:** Series scraped as single string from Audible
**Improvement:**
- Parse series name and book number separately
- Handle different formats:
  - "Series Name #3"
  - "Series Name, Book 3"
  - "Series Name: Book Three"
  - "Series Name (Book 3)"
- Store as structured data:
  ```json
  {
    "series_name": "The Lord of the Rings",
    "series_sequence": 0,
    "series_display": "The Lord of the Rings #0"
  }
  ```

## Priority Order (Recommended)

1. **FR-3: Pagination** (Most impactful - users missing most of their books)
2. **FR-2: Series Grouping** (Better UX for audiobook readers)
3. **FR-1: Category** (Nice to have, may already work with existing filters)
4. **FR-4: Series Detection** (Enhancement for FR-2)

## Estimated Effort

- **FR-3 (Pagination):** 2-3 hours
  - Implement auto-scroll
  - Test with large libraries (100+ books)
  - Handle edge cases (network errors, slow loading)

- **FR-2 (Series Grouping):** 3-4 hours
  - Frontend: New grouped view component
  - Parse series data from metadata
  - Add collapse/expand functionality
  - Sorting logic

- **FR-1 (Category):** 1 hour
  - Check if already working
  - Add filter UI if needed

- **FR-4 (Series Detection):** 1-2 hours
  - Regex parsing for different formats
  - Database schema update
  - Migration for existing data

**Total:** 7-10 hours for all features

## Testing Checklist for Next Session

- [ ] Extension scrapes 100+ books (pagination test)
- [ ] Series grouping displays correctly
- [ ] Series sorting works (by sequence)
- [ ] Category filter works
- [ ] Auto-token still works after changes
- [ ] Extension badge shows correct status
- [ ] Performance: Scraping 100+ books doesn't timeout

## Known Issues to Address

- [ ] Extension icon missing (icon128.png) - causes notification errors
- [ ] Token expiration notification not user-friendly
- [ ] No progress indicator during long scrapes
- [ ] Extension popup doesn't show detailed sync stats

## Notes

**Current scraping selectors:**
```javascript
li.productListItem, .adbl-library-content-row
```

**Audible library structure:**
- Lazy loads ~20 books at a time
- Infinite scroll or "Show more" button (varies by marketplace)
- Each book has `data-asin` attribute

**Series info location:**
- Already in scraped metadata
- Format varies: "Series Name #X", "Series Name, Book X"
- Sometimes includes series URL

**User has ~156 audiobooks total** (from session summary)
**Currently synced: 20 books**
**Missing: ~136 books (need pagination!)**
