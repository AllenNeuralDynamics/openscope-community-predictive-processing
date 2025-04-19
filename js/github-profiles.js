// GitHub Profile Renderer - Site-wide version
document.addEventListener('DOMContentLoaded', function() {
    // Process all GitHub handles in the document with context awareness
    const processGitHubHandles = function() {
        // Detect the current page type based on content
        const pageType = detectPageType();
        
        // Process the page according to its type
        switch(pageType) {
            case 'project-tracking':
                processProjectTrackingPage();
                break;
            case 'team':
                processTeamPage();
                break;
            case 'meeting':
                processMeetingPage();
                break;
            case 'experiment':
                processExperimentPage();
                break;
            default:
                processDefaultPage();
                break;
        }
    };
    
    // Detect the page type based on content structure
    const detectPageType = function() {
        // Check for project tracking page
        if (document.querySelector('h1') && document.querySelector('h1').textContent.includes('Project Tracking')) {
            return 'project-tracking';
        }
        
        // Check for team page
        if (document.querySelector('h1') && document.querySelector('h1').textContent.includes('Team Members')) {
            return 'team';
        }
        
        // Check for meeting page
        if (document.querySelector('h1') && document.querySelector('h1').textContent.includes('Meeting Notes')) {
            return 'meeting';
        }

        // Check for experiment page
        if (document.querySelector('h1') && document.querySelector('h1').textContent.includes('Experiment Session Notes')) {
            return 'experiment';
        }
        
        // Default handling
        return 'default';
    };
    
    // Process the project tracking page (sectioned by project)
    const processProjectTrackingPage = function() {
        // Find all project sections (they start with h2 elements)
        const projectSections = document.querySelectorAll('h2');
        
        projectSections.forEach(function(sectionHeading) {
            // For each section, find the contributors section
            let nextElement = sectionHeading.nextElementSibling;
            let contributorsElement = null;
            
            // Look through the next several elements after the heading
            // until we find the contributors section or hit the next h2
            while (nextElement && nextElement.tagName !== 'H2') {
                // Look for elements that contain "Contributors:"
                if (nextElement.textContent && 
                    (nextElement.textContent.includes('Contributors:') || 
                     nextElement.textContent.includes('👥 Contributors'))) {
                    contributorsElement = nextElement;
                    break;
                }
                nextElement = nextElement.nextElementSibling;
            }
            
            if (!contributorsElement) return;
            
            // Look for GitHub handles in the text
            const text = contributorsElement.innerHTML;
            if (!text) return;
            
            // Pattern to match GitHub handles
            const pattern = /@([a-zA-Z0-9-]+)\b/g;
            let match;
            const usernames = [];
            
            // Find all GitHub handles in the text
            while ((match = pattern.exec(text)) !== null) {
                usernames.push(match[1]);
            }
            
            if (usernames.length === 0) return;
            
            // Create a container for the profiles
            const container = document.createElement('div');
            container.className = 'github-profiles-container';
            
            let row = document.createElement('div');
            row.className = 'github-profiles-row';
            container.appendChild(row);
            
            // Create profile cards for each username
            usernames.forEach(function(username, index) {
                // Create a new row every 3 profiles
                if (index > 0 && index % 3 === 0) {
                    row = document.createElement('div');
                    row.className = 'github-profiles-row';
                    container.appendChild(row);
                }
                
                // Create profile card
                const card = document.createElement('div');
                card.className = 'github-profile-card';
                card.innerHTML = `<div class="loading">Loading GitHub profile...</div>`;
                row.appendChild(card);
                
                // Fetch and display profile
                fetchAndDisplayProfile(username, card);
            });
            
            // Insert profiles container after the contributors element
            contributorsElement.parentNode.insertBefore(container, contributorsElement.nextSibling);
        });
    };
    
    // Process the team page (handles inside tables)
    const processTeamPage = function() {
        // Find all table cells that might contain GitHub handles
        const tableCells = document.querySelectorAll('td');
        
        tableCells.forEach(function(cell) {
            const text = cell.textContent.trim();
            // Check if the cell contains a GitHub handle (starts with @)
            if (text.startsWith('@')) {
                const username = text.substring(1);
                if (username && username.length > 0) {
                    // Create profile element directly in the cell
                    fetchAndDisplayProfileInline(username, cell);
                }
            }
        });
    };
    
    // Process meeting pages
    const processMeetingPage = function() {
        // Find potential lines with facilitators or attendees
        const lines = document.querySelectorAll('li, p');
        
        lines.forEach(function(line) {
            const text = line.innerHTML;
            if (!text) return;
            
            // Only process lines that might contain facilitator or attendee info
            if (text.includes('Facilitator:') || 
                text.includes('Attendees:') || 
                text.includes('Present:')) {
                
                // Find GitHub handles in this line
                processGitHubHandlesInText(line);
            }
        });
    };
    
    // Process experiment pages
    const processExperimentPage = function() {
        // On experiment pages, look for the experimenter line
        const listItems = document.querySelectorAll('li');
        
        listItems.forEach(function(item) {
            const text = item.textContent.trim();
            if (text.startsWith('Experimenter:')) {
                // This is the experimenter line, process GitHub handles here
                processGitHubHandlesInText(item);
            }
        });
    };
    
    // Default page processing (generic handling)
    const processDefaultPage = function() {
        // Find all elements that might contain GitHub handles
        const elements = document.querySelectorAll('p, li, h1, h2, h3, h4, h5, h6, span, div');
        
        elements.forEach(function(element) {
            // Skip elements that are within profile cards (to avoid reprocessing)
            if (element.closest('.github-profile-card') || 
                element.closest('.profile-card') ||
                element.closest('.github-handle-wrapper') ||
                element.closest('.github-profiles-container')) {
                return;
            }
            
            processGitHubHandlesInText(element);
        });
    };
    
    // Helper: Get content until the next heading
    const getContentUntilNextHeading = function(heading) {
        const sectionContent = document.createElement('div');
        let currentElement = heading.nextElementSibling;
        
        while (currentElement && currentElement.tagName !== 'H2') {
            sectionContent.appendChild(currentElement.cloneNode(true));
            currentElement = currentElement.nextElementSibling;
        }
        
        return sectionContent;
    };
    
    // Helper: Find GitHub handles in an element
    const findGitHubHandlesInElement = function(element) {
        const handleElements = [];
        const text = element.innerHTML;
        if (!text) return handleElements;
        
        // Pattern: space or start of string, followed by @, followed by letters/numbers/hyphens
        const pattern = /(^|\s)@([a-zA-Z0-9-]+)(?!\S*@)/g;
        
        // Temporarily replace handles with markers to find them
        const markedText = text.replace(pattern, function(match, prefix, username) {
            return `${prefix}<span class="github-handle-marker" data-username="${username}">@${username}</span>`;
        });
        
        if (markedText !== text) {
            element.innerHTML = markedText;
            const markers = element.querySelectorAll('.github-handle-marker');
            markers.forEach(marker => {
                handleElements.push({
                    element: marker,
                    username: marker.getAttribute('data-username')
                });
            });
        }
        
        return handleElements;
    };
    
    // Helper: Process GitHub handles in text
    const processGitHubHandlesInText = function(element) {
        const handleElements = findGitHubHandlesInElement(element);
        
        if (handleElements.length > 0) {
            // Create profiles container
            const profilesContainer = createProfilesContainer(handleElements);
            
            // Insert after the element
            element.parentNode.insertBefore(profilesContainer, element.nextSibling);
            
            // Hide the original handles
            handleElements.forEach(handle => {
                handle.element.style.display = 'none';
            });
        }
    };
    
    // Helper: Create profiles container for a set of handles
    const createProfilesContainer = function(handleElements) {
        const container = document.createElement('div');
        container.className = 'github-profiles-container';
        
        let row = document.createElement('div');
        row.className = 'github-profiles-row';
        container.appendChild(row);
        
        handleElements.forEach(function(handle, index) {
            // Create a new row every 3 profiles
            if (index > 0 && index % 3 === 0) {
                const newRow = document.createElement('div');
                newRow.className = 'github-profiles-row';
                container.appendChild(newRow);
                row = newRow;
            }
            
            // Create profile card
            const card = document.createElement('div');
            card.className = 'github-profile-card';
            card.innerHTML = `<div class="loading">Loading GitHub profile...</div>`;
            row.appendChild(card);
            
            // Fetch and display profile
            fetchAndDisplayProfile(handle.username, card);
        });
        
        return container;
    };
    
    // Helper: Fetch and display a GitHub profile in a table cell
    const fetchAndDisplayProfileInline = function(username, cell) {
        // Clear the cell content first
        cell.innerHTML = `<div class="loading">Loading...</div>`;
        
        // Fetch GitHub profile data
        const headers = {
            'Accept': 'application/vnd.github.v3+json'
        };
        
        fetch(`https://api.github.com/users/${username}`, { headers })
            .then(response => {
                if (response.status === 403) {
                    throw new Error('GitHub API rate limit exceeded');
                }
                if (!response.ok) {
                    throw new Error('GitHub profile not found');
                }
                return response.json();
            })
            .then(data => {
                // Create compact inline profile
                const displayName = data.name || username;
                
                cell.innerHTML = `
                    <div class="inline-profile">
                        <a href="${data.html_url}" target="_blank" class="profile-link">
                            <img src="${data.avatar_url}" alt="${displayName}'s avatar" class="profile-avatar">
                            <span class="profile-name">${displayName}</span>
                        </a>
                    </div>
                `;
            })
            .catch(error => {
                // If fetching fails, just show the username
                cell.innerHTML = `<a href="https://github.com/${username}" target="_blank">@${username}</a>`;
                console.error('Error fetching GitHub profile:', error);
            });
    };
    
    // Helper: Fetch and display a GitHub profile
    const fetchAndDisplayProfile = function(username, cardContainer) {
        // Fetch GitHub profile data
        const headers = {
            'Accept': 'application/vnd.github.v3+json'
        };
        
        fetch(`https://api.github.com/users/${username}`, { headers })
            .then(response => {
                if (response.status === 403) {
                    throw new Error('GitHub API rate limit exceeded');
                }
                if (!response.ok) {
                    throw new Error('GitHub profile not found');
                }
                return response.json();
            })
            .then(data => {
                // Create profile card with GitHub data
                const displayName = data.name || username;
                
                cardContainer.innerHTML = `
                    <div class="profile-card">
                        <div class="profile-image">
                            <a href="${data.html_url}" target="_blank">
                                <img src="${data.avatar_url}" alt="${displayName}'s avatar">
                            </a>
                        </div>
                        <div class="profile-info">
                            <h4><a href="${data.html_url}" target="_blank">${displayName}</a></h4>
                            <p class="username">@${username}</p>
                            ${data.bio ? `<p class="bio">${data.bio}</p>` : ''}
                        </div>
                    </div>
                `;
            })
            .catch(error => {
                // If fetching fails, just show a simple link
                cardContainer.innerHTML = `<a href="https://github.com/${username}" target="_blank">@${username}</a>`;
                console.error('Error fetching GitHub profile:', error);
            });
    };
    
    // Add CSS for GitHub profiles
    const style = document.createElement('style');
    style.textContent = `
        /* Shared container styles */
        .github-profiles-container {
            margin: 10px 0 20px 0;
            max-width: 100%;
        }
        .github-profiles-row {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 10px;
        }
        .github-profile-card {
            margin: 5px 0;
            flex: 1 1 calc(33.333% - 10px);
            min-width: 200px;
            max-width: calc(33.333% - 10px);
        }
        
        /* Card styles */
        .profile-card {
            display: flex;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 10px;
            background-color: #f6f8fa;
            height: 100%;
        }
        .profile-image img {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            margin-right: 10px;
        }
        .profile-info h4 {
            margin: 0 0 5px 0;
            font-size: 0.95em;
        }
        .profile-info .username {
            margin: 0 0 5px 0;
            font-size: 0.8em;
            color: #586069;
        }
        .profile-info .bio {
            margin: 5px 0 0 0;
            font-size: 0.85em;
            color: #586069;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        /* Inline profile for tables */
        .inline-profile {
            display: flex;
            align-items: center;
        }
        .profile-link {
            display: flex;
            align-items: center;
            text-decoration: none;
            color: #0366d6;
        }
        .profile-avatar {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .profile-name {
            font-size: 14px;
        }
        
        /* Loading state */
        .loading {
            font-style: italic;
            color: #586069;
            font-size: 0.9em;
        }
        
        /* Responsive adjustments */
        @media (max-width: 768px) {
            .github-profile-card {
                flex: 1 1 calc(50% - 10px);
                max-width: calc(50% - 10px);
            }
        }
        @media (max-width: 480px) {
            .github-profile-card {
                flex: 1 1 100%;
                max-width: 100%;
            }
        }
    `;
    document.head.appendChild(style);
    
    // Run processor
    processGitHubHandles();
});