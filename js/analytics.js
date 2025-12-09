// Google Analytics 4 Implementation
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());

// GA4 measurement ID
gtag('config', 'G-DT93KEXV5Q');

// Track page views when navigating between pages without full page reload
document.addEventListener('DOMContentLoaded', function() {
  // Track initial page view
  logPageView();
  
  // For SPA-like navigation in MkDocs
  const observer = new MutationObserver(function(mutations) {
    for (const mutation of mutations) {
      if (mutation.type === 'childList' && document.title) {
        logPageView();
        break;
      }
    }
  });
  
  // Observe the document title for changes
  observer.observe(document.querySelector('title'), {
    subtree: true,
    characterData: true,
    childList: true
  });
});

// Function to log page views
function logPageView() {
  gtag('event', 'page_view', {
    page_title: document.title,
    page_location: window.location.href,
    page_path: window.location.pathname
  });
}