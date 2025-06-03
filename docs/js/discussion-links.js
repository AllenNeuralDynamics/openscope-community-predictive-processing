document.addEventListener('DOMContentLoaded', function() {
  // Skip if not on a content page
  if (!document.querySelector('.rst-content .document')) return;
  
  // Get the current page path (this is more reliable than the title)
  const pathname = window.location.pathname;
  const basePath = '/openscope-community-predictive-processing/';
  let pagePath = pathname.startsWith(basePath) ? pathname.substring(basePath.length) : pathname;
  // Remove trailing slash and .html extension if present
  pagePath = pagePath.replace(/\/$/, '').replace(/\.html$/, '');
  if (pagePath === '') pagePath = 'index';
  
  // Extract key identifiers from the path - this is crucial for matching discussions
  const pathParts = pagePath.split('/');
  let pageIdentifier = pathParts[pathParts.length - 1]; // Last segment of path
  
  // Also create alternative identifiers for better matching
  let alternativeIdentifiers = [];
  
  // For experiment pages, use the full experiment identifier from the path
  if (pagePath.includes('experiments/')) {
    // For paths like "experiments/allen_institute/slap2/allen_institute_787727_2025-03-27"
    // we want "allen_institute_787727_2025-03-27"
    pageIdentifier = pathParts[pathParts.length - 1];
  } else if (pagePath.includes('/')) {
    // For nested pages, also try the full path as an identifier
    alternativeIdentifiers.push(pagePath);
  }
  
  console.log('Page path:', pagePath);
  console.log('Page identifier:', pageIdentifier);
  console.log('Alternative identifiers:', alternativeIdentifiers);
  console.log('Path parts:', pathParts);
  
  // Get the page title as a fallback
  const pageTitle = document.title.replace(' - OpenScope Community Predictive Processing', '').trim();
  console.log('Page title:', pageTitle);
  
  // Create placeholder for discussion link
  const discussionContainer = document.createElement('div');
  discussionContainer.className = 'github-discussion-link';
  discussionContainer.innerHTML = '<hr><p>Loading discussion link...</p>';
  
  // Add styling
  const style = document.createElement('style');
  style.textContent = `
    .github-discussion-link {
      margin-top: 2rem;
      padding: 1rem 0;
    }
    .github-discussion-link a {
      display: inline-block;
      padding: 0.5rem 1rem;
      border: 1px solid #ddd;
      border-radius: 4px;
      text-decoration: none;
    }
    .github-discussion-link a:hover {
      background-color: #f5f5f5;
    }
    .github-discussion-link .login-note {
      font-size: 0.8rem;
      color: #666;
      margin-top: 0.5rem;
    }
    .github-discussion-link .api-limit-note {
      font-size: 0.8rem;
      color: #d73a49;
      margin-top: 0.5rem;
      font-style: italic;
    }
  `;
  document.head.appendChild(style);
  
  // Add to page
  const content = document.querySelector('.rst-content .document');
  if (content) {
    content.appendChild(discussionContainer);
  }
  
  // No hardcoded mappings - rely on API search and caching for reliability
  
  // Local storage cache keys
  const CACHE_PREFIX = 'github_discussion_';
  const CACHE_TIMESTAMP = 'github_discussion_timestamp';
  const CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
  
  // Check cache first
  function checkCacheForDiscussion() {
    try {
      // Check if cache exists and is not expired
      const timestamp = localStorage.getItem(CACHE_TIMESTAMP);
      const now = new Date().getTime();
      const cacheValid = timestamp && (now - parseInt(timestamp) < CACHE_DURATION);
      
      if (cacheValid) {
        const cachedItem = localStorage.getItem(CACHE_PREFIX + pageIdentifier);
        if (cachedItem) {
          const cache = JSON.parse(cachedItem);
          if (cache.url) {
            // Create link from cached data
            discussionContainer.innerHTML = `
              <hr>
              <p>
                <a href="${cache.url}" target="_blank">
                  💬 Join the discussion for this page on GitHub
                </a>
              </p>
            `;
            return true;
          } else if (cache.noDiscussion) {
            // No discussion found in previous search
            createNewDiscussionLink();
            return true;
          }
        }
      } else {
        // Cache expired, clear it
        clearCacheItems();
      }
    } catch (e) {
      console.error('Error checking cache:', e);
    }
    
    return false;
  }
  
  // Clear expired cache items
  function clearCacheItems() {
    try {
      // Get all localStorage keys
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith(CACHE_PREFIX)) {
          localStorage.removeItem(key);
        }
      }
      localStorage.removeItem(CACHE_TIMESTAMP);
    } catch (e) {
      console.error('Error clearing cache:', e);
    }
  }
  
  // Save to cache
  function saveToCache(url) {
    try {
      localStorage.setItem(CACHE_TIMESTAMP, new Date().getTime().toString());
      if (url) {
        localStorage.setItem(CACHE_PREFIX + pageIdentifier, JSON.stringify({ url }));
      } else {
        localStorage.setItem(CACHE_PREFIX + pageIdentifier, JSON.stringify({ noDiscussion: true }));
      }
    } catch (e) {
      console.error('Error saving to cache:', e);
    }
  }
  
  // Check cache before proceeding with API calls
  if (checkCacheForDiscussion()) {
    return;
  }
  
  // Construct search queries to find matching discussions
  // The actual discussion titles follow the pattern "Discussion: {page-identifier}"
  const queries = [
    // Try exact match with "Discussion: " prefix
    `"Discussion: ${pageIdentifier}" in:title is:discussion repo:allenneuraldynamics/openscope-community-predictive-processing`,
    // Try with full path
    `"Discussion: ${pagePath}" in:title is:discussion repo:allenneuraldynamics/openscope-community-predictive-processing`,
    // Try just the identifier without "Discussion: " prefix
    `"${pageIdentifier}" in:title is:discussion repo:allenneuraldynamics/openscope-community-predictive-processing`,
    // Try the page title
    `"${pageTitle}" in:title is:discussion repo:allenneuraldynamics/openscope-community-predictive-processing`
  ];
  
  // Add alternative identifiers to the search
  alternativeIdentifiers.forEach(altId => {
    queries.push(`"Discussion: ${altId}" in:title is:discussion repo:allenneuraldynamics/openscope-community-predictive-processing`);
    queries.push(`"${altId}" in:title is:discussion repo:allenneuraldynamics/openscope-community-predictive-processing`);
  });
  
  // Try to find existing discussions through the API
  function searchWithQuery(queryIndex) {
    if (queryIndex >= queries.length) {
      // We've exhausted all queries, create a new discussion
      console.log('All search queries exhausted. No existing discussion found. Creating new discussion link.');
      createNewDiscussionLink();
      saveToCache(null); // Cache that no discussion was found
      return;
    }
    
    const searchQuery = encodeURIComponent(queries[queryIndex]);
    console.log('Searching with query:', queries[queryIndex]);
    
    // Prepare request options
    const requestOptions = {
      method: 'GET',
      headers: {
        'Accept': 'application/vnd.github.v3+json'
        // If you want to use token-based auth, uncomment and add your token:
        // 'Authorization': 'token YOUR_GITHUB_TOKEN'
      }
    };
    
    fetch(`https://api.github.com/search/issues?q=${searchQuery}`, requestOptions)
      .then(response => {
        // Check for rate limit errors
        if (response.status === 403) {
          // Handle rate limit exceeded
          console.warn('GitHub API rate limit exceeded');
          showRateLimitMessage();
          return null;
        }
        return response.json();
      })
      .then(data => {
        if (!data) return; // Handled by the rate limit code above
        
        console.log('GitHub API Response for query', queryIndex + 1, ':', data);
        
        if (data.items && data.items.length > 0) {
          // Filter to only include actual discussions (not issues)
          const discussions = data.items.filter(item => 
            item.html_url.includes('/discussions/') && 
            !item.html_url.includes('/issues/')
          );
          
          if (discussions.length > 0) {
            // Sort by relevance - prefer exact matches
            const sortedDiscussions = discussions.sort((a, b) => {
              const aTitle = a.title.toLowerCase();
              const bTitle = b.title.toLowerCase();
              const targetLower = pageIdentifier.toLowerCase();
              
              // Prefer exact matches with "Discussion: " prefix
              const aExactMatch = aTitle === `discussion: ${targetLower}`;
              const bExactMatch = bTitle === `discussion: ${targetLower}`;
              
              if (aExactMatch && !bExactMatch) return -1;
              if (!aExactMatch && bExactMatch) return 1;
              
              // Then prefer matches that contain the identifier
              const aContains = aTitle.includes(targetLower);
              const bContains = bTitle.includes(targetLower);
              
              if (aContains && !bContains) return -1;
              if (!aContains && bContains) return 1;
              
              // Finally, sort by creation date (newest first)
              return new Date(b.created_at) - new Date(a.created_at);
            });
            
            // Found an existing discussion
            const discussion = sortedDiscussions[0];
            const discussionUrl = discussion.html_url;
            
            console.log('Found existing discussion:', discussion.title, 'at', discussionUrl);
            
            // Cache the result
            saveToCache(discussionUrl);
            
            // Create the link
            discussionContainer.innerHTML = `
              <hr>
              <p>
                <a href="${discussionUrl}" target="_blank">
                  💬 Join the discussion for this page on GitHub
                </a>
              </p>
            `;
          } else {
            console.log('No discussions found with query', queryIndex + 1, '- trying next query');
            // Try the next query
            searchWithQuery(queryIndex + 1);
          }
        } else {
          console.log('No results found with query', queryIndex + 1, '- trying next query');
          // Try the next query
          searchWithQuery(queryIndex + 1);
        }
      })
      .catch(error => {
        console.error('Error fetching discussions:', error);
        // Show fallback for errors
        createNewDiscussionLink();
      });
  }
  
  function showRateLimitMessage() {
    discussionContainer.innerHTML = `
      <hr>
      <p>
        <a href="https://github.com/allenneuraldynamics/openscope-community-predictive-processing/discussions" target="_blank">
          💬 View GitHub discussions
        </a>
        <span class="api-limit-note">GitHub API rate limit exceeded. Please try again later or browse all discussions.</span>
      </p>
    `;
  }
  
  function createNewDiscussionLink() {
    // No discussion exists - create new one with consistent title format
    const discussionTitle = `Discussion: ${pageIdentifier}`;
    discussionContainer.innerHTML = `
      <hr>
      <p>
        <a href="https://github.com/allenneuraldynamics/openscope-community-predictive-processing/discussions/new?category=q-a&title=${encodeURIComponent(discussionTitle)}" target="_blank">
          💬 Start a discussion for this page on GitHub
        </a>
        <span class="login-note">(A GitHub account is required to create or participate in discussions)</span>
      </p>
    `;
  }
  
  // Start the search process
  searchWithQuery(0);
});
