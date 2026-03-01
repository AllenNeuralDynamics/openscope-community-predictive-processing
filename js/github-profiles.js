// GitHub Profile Renderer - With direct avatar image loading
document.addEventListener('DOMContentLoaded', function() {
    // Track already processed usernames to avoid duplicates
    const processedHandles = new Set();
    
    // Process all GitHub handles in the document
    function processGitHubHandles() {
        // Find all elements that might contain GitHub handles
        const elements = document.querySelectorAll('p, li, h1, h2, h3, h4, h5, h6, blockquote, td');
        
        elements.forEach(function(element) {
            const text = element.innerHTML;
            if (!text) return;
            
            // Pattern to find GitHub handles but NOT email addresses
            // This matches @ only when it's either at the start of text or preceded by whitespace
            // And not when it's part of an email address
            const pattern = /(?:^|\s)@([a-zA-Z0-9-]+)\b/g;
            let match;
            const handles = [];
            
            // Find all GitHub handles in the text that haven't been processed yet
            while ((match = pattern.exec(text)) !== null) {
                const username = match[1];
                if (!processedHandles.has(username)) {
                    handles.push({
                        username: username,
                        startPos: match.index,
                        endPos: match.index + match[0].length
                    });
                    // Mark this handle as processed to avoid duplicates
                    processedHandles.add(username);
                }
            }
            
            if (handles.length === 0) return;
            
            // Create a profiles row for this element
            const profilesRow = document.createElement('div');
            profilesRow.className = 'github-profiles-row';
            
            // Create a profile card for each handle
            handles.forEach(function(handle) {
                const card = document.createElement('div');
                card.className = 'github-profile-card';
                
                // Display profile with direct avatar loading
                displayProfileWithAvatar(handle.username, card);
                
                profilesRow.appendChild(card);
            });
            
            // Insert the profiles row after the element
            element.parentNode.insertBefore(profilesRow, element.nextSibling);
        });
    }
    
    // Display a profile with direct avatar loading
    function displayProfileWithAvatar(username, cardContainer) {
        // Create profile card with avatar loading
        cardContainer.innerHTML = `
            <div class="profile-card">
                <div class="profile-image">
                    <a href="https://github.com/${username}" target="_blank">
                        <img src="https://github.com/${username}.png" 
                             alt="${username}'s avatar"
                             onerror="this.onerror=null; this.parentNode.innerHTML='<div class=\\'profile-avatar-placeholder\\'>${username.charAt(0).toUpperCase()}</div>';">
                    </a>
                </div>
                <div class="profile-info">
                    <h4><a href="https://github.com/${username}" target="_blank">${username}</a></h4>
                    <p class="username">@${username}</p>
                </div>
            </div>
        `;
    }
    
    // Add CSS for GitHub profiles
    const style = document.createElement('style');
    style.textContent = `
        .github-profiles-row {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 10px 0;
        }
        .github-profile-card {
            flex: 1 1 250px;
            min-width: 200px;
            max-width: 300px;
            margin: 5px 0;
        }
        .profile-card {
            display: flex;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 10px;
            background-color: #f6f8fa;
        }
        .profile-image img {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            margin-right: 10px;
            object-fit: cover;
        }
        .profile-avatar-placeholder {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            margin-right: 10px;
            background-color: #0366d6;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            font-weight: bold;
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
    `;
    document.head.appendChild(style);
    
    // Run processor
    processGitHubHandles();
});