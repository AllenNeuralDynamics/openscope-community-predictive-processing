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
    // For nested pages (meetings, hardware, etc.), use the full path as primary identifier
    // This handles cases like "meetings/2025-05-13" -> "meetings/2025-05-13" 
    pageIdentifier = pagePath;
    // Also add the last segment as an alternative
    alternativeIdentifiers.push(pathParts[pathParts.length - 1]);
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
  
  // Add debugging function (console only)
  function addDebugInfo(message) {
    console.log('DEBUG:', message);
  }
  
  addDebugInfo(`Page identifier: "${pageIdentifier}"`);
  addDebugInfo(`Alternative identifiers: [${alternativeIdentifiers.join(', ')}]`);
  
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
  
  // Try to find existing discussions using GraphQL API (more reliable than search)
  function findDiscussionByTitle() {
    addDebugInfo('Trying GraphQL API to find discussions...');
    
    // Use GitHub GraphQL API to list recent discussions
    const graphqlQuery = {
      query: `
        query($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) {
            discussions(first: 100, orderBy: {field: UPDATED_AT, direction: DESC}) {
              nodes {
                title
                number
                url
                updatedAt
                category {
                  name
                }
              }
            }
          }
        }
      `,
      variables: {
        owner: "allenneuraldynamics",
        repo: "openscope-community-predictive-processing"
      }
    };
    
    fetch('https://api.github.com/graphql', {
      method: 'POST',
      headers: {
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
        // Note: GraphQL API requires authentication for better rate limits
        // For public repos, we can still access some data without auth
      },
      body: JSON.stringify(graphqlQuery)
    })
    .then(response => {
      addDebugInfo(`GraphQL response status: ${response.status}`);
      if (response.status === 403) {
        addDebugInfo('GraphQL API rate limit or auth required, falling back to REST API');
        fallbackToRestAPI();
        return null;
      }
      if (!response.ok) {
        addDebugInfo(`GraphQL API failed with status ${response.status}, falling back to REST API`);
        fallbackToRestAPI();
        return null;
      }
      return response.json();
    })
    .then(data => {
      if (!data || data.errors) {
        addDebugInfo(`GraphQL errors or no data: ${JSON.stringify(data?.errors)}`);
        fallbackToRestAPI();
        return;
      }
      
      const discussions = data.data?.repository?.discussions?.nodes || [];
      addDebugInfo(`Found ${discussions.length} discussions via GraphQL`);
      
      // Log the first few discussion titles for debugging
      discussions.slice(0, 5).forEach((d, i) => {
        addDebugInfo(`Discussion ${i+1}: "${d.title}"`);
      });
      
      // Look for exact matches first
      const targetTitle = `Discussion: ${pageIdentifier}`;
      addDebugInfo(`Looking for exact match: "${targetTitle}"`);
      let matchedDiscussion = discussions.find(d => 
        d.title.toLowerCase() === targetTitle.toLowerCase()
      );
      
      // Try alternative identifiers if no exact match
      if (!matchedDiscussion) {
        for (const altId of alternativeIdentifiers) {
          const altTitle = `Discussion: ${altId}`;
          matchedDiscussion = discussions.find(d => 
            d.title.toLowerCase() === altTitle.toLowerCase()
          );
          if (matchedDiscussion) break;
        }
      }
      
      if (matchedDiscussion) {
        addDebugInfo(`✅ FOUND DISCUSSION VIA GRAPHQL: "${matchedDiscussion.title}"`);
        
        // Cache and display the found discussion
        saveToCache(matchedDiscussion.url);
        discussionContainer.innerHTML = `
          <hr>
          <p>
            <a href="${matchedDiscussion.url}" target="_blank">
              💬 Join the discussion for this page on GitHub
            </a>
          </p>
        `;
      } else {
        addDebugInfo('No matching discussion found via GraphQL, trying REST API fallback...');
        fallbackToRestAPI();
      }
    })
    .catch(error => {
      console.error('GraphQL API error, falling back to REST API:', error);
      fallbackToRestAPI();
    });
  }
  
  // Fallback to REST API approach when GraphQL fails
  function fallbackToRestAPI() {
    addDebugInfo('Fallback: Using REST API to check individual discussions...');
    
    // Try to fetch recent discussions using REST API
    // Check recent discussion numbers to find matches (including known discussion #87)
    const recentNumbers = [87, 88, 89, 86, 85, 84, 83, 82, 81, 80, 79, 78, 77, 76, 75];
    checkDiscussionNumbers(recentNumbers, 0);
  }
  
  function checkDiscussionNumbers(numbers, index) {
    if (index >= numbers.length) {
      addDebugInfo('❌ No matching discussion found, creating new discussion link');
      createNewDiscussionLink();
      saveToCache(null);
      return;
    }
    
    const discussionNumber = numbers[index];
    addDebugInfo(`Checking discussion #${discussionNumber}...`);
    const url = `https://api.github.com/repos/allenneuraldynamics/openscope-community-predictive-processing/issues/${discussionNumber}`;
    
    fetch(url, {
      headers: {
        'Accept': 'application/vnd.github.v3+json'
      }
    })
    .then(response => {
      if (response.status === 404) {
        addDebugInfo(`Discussion #${discussionNumber} doesn't exist, trying next...`);
        checkDiscussionNumbers(numbers, index + 1);
        return null;
      }
      if (response.status === 403) {
        addDebugInfo('⚠️ REST API rate limit exceeded');
        showRateLimitMessage();
        return null;
      }
      return response.json();
    })
    .then(data => {
      if (!data) return;
      
      addDebugInfo(`Discussion #${discussionNumber} title: "${data.title}"`);
      
      // Check if this is a discussion (not an issue) and matches our page
      if (data.html_url && data.html_url.includes('/discussions/')) {
        const title = data.title.toLowerCase();
        const targetLower = pageIdentifier.toLowerCase();
        
        // Check for exact match
        if (title === `discussion: ${targetLower}`) {
          addDebugInfo(`✅ FOUND DISCUSSION VIA REST API: "${data.title}"`);
          
          saveToCache(data.html_url);
          discussionContainer.innerHTML = `
            <hr>
            <p>
              <a href="${data.html_url}" target="_blank">
                💬 Join the discussion for this page on GitHub
              </a>
            </p>
          `;
          return;
        }
        
        // Check alternative identifiers
        for (const altId of alternativeIdentifiers) {
          if (title === `discussion: ${altId.toLowerCase()}`) {
            addDebugInfo(`✅ FOUND DISCUSSION VIA REST API (ALTERNATIVE): "${data.title}"`);
            
            saveToCache(data.html_url);
            discussionContainer.innerHTML = `
              <hr>
              <p>
                <a href="${data.html_url}" target="_blank">
                  💬 Join the discussion for this page on GitHub
                </a>
              </p>
            `;
            return;
          }
        }
        
        addDebugInfo(`No match for discussion #${discussionNumber}`);
      } else {
        addDebugInfo(`#${discussionNumber} is not a discussion or doesn't have discussion URL`);
      }
      
      // No match, try next number
      checkDiscussionNumbers(numbers, index + 1);
    })
    .catch(error => {
      addDebugInfo(`Error checking discussion #${discussionNumber}: ${error.message}`);
      // Try next number
      checkDiscussionNumbers(numbers, index + 1);
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
  
  // Start the search process using GraphQL API
  findDiscussionByTitle();
});
