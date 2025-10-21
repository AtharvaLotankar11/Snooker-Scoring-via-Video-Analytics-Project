/**
 * URL Consistency Manager
 * Ensures the application behaves identically regardless of access URL
 */

(function() {
    'use strict';
    
    // Force consistent behavior on page load
    document.addEventListener('DOMContentLoaded', function() {
        console.log('🔧 URL Consistency Manager: Ensuring consistent behavior');
        
        // Log current access method
        const currentHost = window.location.host;
        const currentProtocol = window.location.protocol;
        const currentUrl = window.location.href;
        
        console.log(`📍 Accessed via: ${currentUrl}`);
        console.log(`🏠 Host: ${currentHost}`);
        
        // Force reload of any cached resources if needed
        if (performance.navigation.type === performance.navigation.TYPE_BACK_FORWARD) {
            console.log('🔄 Back/Forward navigation detected, forcing fresh load');
            window.location.reload(true);
        }
        
        // Ensure all AJAX requests use relative URLs
        const originalFetch = window.fetch;
        window.fetch = function(url, options) {
            // Convert absolute URLs to relative if they match current host
            if (typeof url === 'string' && url.startsWith('http')) {
                const urlObj = new URL(url);
                if (urlObj.host === window.location.host) {
                    url = urlObj.pathname + urlObj.search + urlObj.hash;
                    console.log(`🔗 Converted absolute URL to relative: ${url}`);
                }
            }
            return originalFetch.call(this, url, options);
        };
        
        // Add consistency marker to body
        document.body.setAttribute('data-url-consistent', 'true');
        document.body.setAttribute('data-access-host', currentHost);
        
        console.log('✅ URL Consistency Manager: Initialization complete');
    });
    
    // Handle any dynamic content loading
    window.addEventListener('load', function() {
        console.log('🎯 Page fully loaded, verifying consistency');
        
        // Check if all critical elements are present
        const criticalElements = [
            '.hero-section',
            '.navbar',
            '.feature-icon'
        ];
        
        let allPresent = true;
        criticalElements.forEach(selector => {
            const element = document.querySelector(selector);
            if (!element) {
                console.warn(`⚠️ Missing critical element: ${selector}`);
                allPresent = false;
            }
        });
        
        if (allPresent) {
            console.log('✅ All critical elements present');
        } else {
            console.warn('⚠️ Some elements missing, may need refresh');
        }
    });
    
})();