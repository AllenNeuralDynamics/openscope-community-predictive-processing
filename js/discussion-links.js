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
  const pageIdentifier = pathParts[pathParts.length - 1]; // Last segment of path
  
  console.log('Page path:', pagePath);
  console.log('Page identifier:', pageIdentifier);
  
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
  
  // Known discussions mapping - Add your known discussions here to avoid API calls
  const knownDiscussions = {
    'allen_institute_787727_2025-03-27': 22,
    'collaboration-policy': 21, // Adding direct mapping for collaboration policy to the forum
    // Add more mappings as needed
  };
  
  // Check if we have a known discussion for this page
  if (knownDiscussions[pageIdentifier]) {
    const discussionId = knownDiscussions[pageIdentifier];
    const discussionUrl = `https://github.com/allenneuraldynamics/openscope-community-predictive-processing/discussions/${discussionId}`;
    
    // Create the link
    discussionContainer.innerHTML = `
      <hr>
      <p>
        <a href="${discussionUrl}" target="_blank">
          💬 Join the discussion for this page on GitHub
        </a>
      </p>
    `;
    return;
  }
  
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
  const queries = [
    `"${pageIdentifier}" in:title is:discussion repo:allenneuraldynamics/openscope-community-predictive-processing`,
    `"${pagePath}" in:title is:discussion repo:allenneuraldynamics/openscope-community-predictive-processing`,
    `"Discussion: ${pageTitle}" in:title is:discussion repo:allenneuraldynamics/openscope-community-predictive-processing`
  ];
  
  // Try to find existing discussions through the API
  function searchWithQuery(queryIndex) {
    if (queryIndex >= queries.length) {
      // We've exhausted all queries, create a new discussion
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
            // Found an existing discussion
            const discussion = discussions[0];
            const discussionUrl = discussion.html_url;
            
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
            // Try the next query
            searchWithQuery(queryIndex + 1);
          }
        } else {
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
    // No discussion exists - create new one
    discussionContainer.innerHTML = `
      <hr>
      <p>
        <a href="https://github.com/allenneuraldynamics/openscope-community-predictive-processing/discussions/new?category=q-a&title=Discussion: ${encodeURIComponent(pagePath)}" target="_blank">
          💬 Start a discussion for this page on GitHub
        </a>
        <span class="login-note">(A GitHub account is required to create or participate in discussions)</span>
      </p>
    `;
  }
  
  // Start the search process
  searchWithQuery(0);
});
