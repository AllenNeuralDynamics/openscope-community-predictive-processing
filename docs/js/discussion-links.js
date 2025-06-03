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
  
  // For experiment pages, use the full experiment identifier from the path
  if (pagePath.includes('experiments/')) {
    // For paths like "experiments/allen_institute/slap2/allen_institute_787727_2025-03-27"
    // we want "allen_institute_787727_2025-03-27"
    pageIdentifier = pathParts[pathParts.length - 1];
  } else if (pagePath.includes('/')) {
    // For nested pages (meetings, hardware, etc.), use the full path as primary identifier
    // This handles cases like "meetings/2025-05-13" -> "meetings/2025-05-13" 
    pageIdentifier = pagePath;
  }
  
  console.log('Page path:', pagePath);
  console.log('Page identifier:', pageIdentifier);
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
  
  // No hardcoded mappings - rely on GraphQL API search for finding discussions
  
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
        addDebugInfo('GraphQL API rate limit or auth required, sending to discussions page');
        createDiscussionsPageLink();
        return null;
      }
      if (!response.ok) {
        addDebugInfo(`GraphQL API failed with status ${response.status}, sending to discussions page`);
        createDiscussionsPageLink();
        return null;
      }
      return response.json();
    })
    .then(data => {
      if (!data || data.errors) {
        addDebugInfo(`GraphQL errors or no data: ${JSON.stringify(data?.errors)}`);
        createDiscussionsPageLink();
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
      
      if (matchedDiscussion) {
        addDebugInfo(`✅ FOUND DISCUSSION VIA GRAPHQL: "${matchedDiscussion.title}"`);
        
        // Display the found discussion
        discussionContainer.innerHTML = `
          <hr>
          <p>
            <a href="${matchedDiscussion.url}" target="_blank">
              💬 Join the discussion for this page on GitHub
            </a>
          </p>
        `;
      } else {
        addDebugInfo('No matching discussion found via GraphQL, creating new discussion link');
        createNewDiscussionLink();
      }
    })
    .catch(error => {
      addDebugInfo('GraphQL API error, sending to discussions page');
      console.error('GraphQL API error:', error);
      createDiscussionsPageLink();
    });
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
  
  function createDiscussionsPageLink() {
    // Rate limit hit or API unavailable - send to general discussions page
    discussionContainer.innerHTML = `
      <hr>
      <p>
        <a href="https://github.com/allenneuraldynamics/openscope-community-predictive-processing/discussions" target="_blank">
          💬 Browse discussions for this project on GitHub
        </a>
        <span class="login-note">(You can search for existing discussions or start a new one)</span>
      </p>
    `;
  }
  
  // Start the search process using GraphQL API
  findDiscussionByTitle();
});
