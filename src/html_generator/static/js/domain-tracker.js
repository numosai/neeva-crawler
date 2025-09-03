/**
 * Domain Change Tracker for Neeva Crawler
 * Detects domain navigation and sends PostMessage events to parent window
 */

(function() {
    'use strict';
    
    let currentDomain = null;
    let isInitialized = false;
    
    /**
     * Extract domain from URL path
     * Expected format: /output/DOMAIN/html/... or https://numosai.github.io/neeva-crawler/output/DOMAIN/html/...
     */
    function extractDomainFromURL(url = window.location.href) {
        try {
            // Handle both local paths and full URLs
            let path = url;
            if (url.startsWith('http')) {
                const urlObj = new URL(url);
                path = urlObj.pathname;
            }
            
            // Match pattern: /output/DOMAIN/html or neeva-crawler/output/DOMAIN/html
            const match = path.match(/\/output\/([^\/]+)\/html/);
            return match ? match[1] : null;
        } catch (error) {
            console.warn('Error extracting domain from URL:', error);
            return null;
        }
    }
    
    /**
     * Send domain change message to parent window
     */
    function notifyDomainChange(domain) {
        if (!domain) return;
        
        const message = {
            type: 'DOMAIN_CHANGE',
            domain: domain,
            timestamp: new Date().toISOString(),
            url: window.location.href
        };
        
        try {
            // Send to parent window (if embedded in iframe)
            if (window.parent && window.parent !== window) {
                window.parent.postMessage(message, '*');
                console.log('Domain change notification sent:', message);
            }
            
            // Also send to top window (if nested)
            if (window.top && window.top !== window) {
                window.top.postMessage(message, '*');
            }
        } catch (error) {
            console.warn('Error sending domain change notification:', error);
        }
    }
    
    /**
     * Initialize domain tracking
     */
    function initializeDomainTracking() {
        if (isInitialized) return;
        
        const domain = extractDomainFromURL();
        if (domain && domain !== currentDomain) {
            currentDomain = domain;
            notifyDomainChange(domain);
        }
        
        isInitialized = true;
    }
    
    /**
     * Handle navigation events (for SPA-like behavior if added later)
     */
    function handleNavigation() {
        const newDomain = extractDomainFromURL();
        if (newDomain && newDomain !== currentDomain) {
            currentDomain = newDomain;
            notifyDomainChange(newDomain);
        }
    }
    
    /**
     * Monitor for URL changes
     */
    function setupNavigationMonitoring() {
        // Listen for popstate (browser back/forward)
        window.addEventListener('popstate', handleNavigation);
        
        // Listen for hash changes
        window.addEventListener('hashchange', handleNavigation);
        
        // Monitor for programmatic navigation (if needed)
        const originalPushState = history.pushState;
        const originalReplaceState = history.replaceState;
        
        history.pushState = function() {
            originalPushState.apply(history, arguments);
            setTimeout(handleNavigation, 0);
        };
        
        history.replaceState = function() {
            originalReplaceState.apply(history, arguments);
            setTimeout(handleNavigation, 0);
        };
        
        // Monitor for clicks on domain navigation links
        document.addEventListener('click', function(event) {
            const link = event.target.closest('a');
            if (link && link.href) {
                const targetDomain = extractDomainFromURL(link.href);
                if (targetDomain && targetDomain !== currentDomain) {
                    // Slight delay to allow navigation to complete
                    setTimeout(() => {
                        const actualDomain = extractDomainFromURL();
                        if (actualDomain && actualDomain !== currentDomain) {
                            currentDomain = actualDomain;
                            notifyDomainChange(actualDomain);
                        }
                    }, 100);
                }
            }
        });
    }
    
    /**
     * Initialize when DOM is ready
     */
    function initialize() {
        initializeDomainTracking();
        setupNavigationMonitoring();
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
    
    // Also initialize on window load as fallback
    window.addEventListener('load', initialize);
    
    // Expose functions for debugging
    if (typeof window !== 'undefined') {
        window.neevaTracker = {
            getCurrentDomain: () => currentDomain,
            extractDomain: extractDomainFromURL,
            notifyChange: notifyDomainChange
        };
    }
    
})();