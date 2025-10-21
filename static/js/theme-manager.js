/**
 * ThemeManager - Snooker Detection Pro
 * Central theme management system with brand compliance
 * Handles theme switching, persistence, and system preference detection
 */

class ThemeManager {
    constructor(options = {}) {
        this.options = {
            defaultTheme: 'dark',
            storageKey: 'snooker-theme-preference',
            transitionDuration: 300,
            brandColors: {
                primary: '#0B405B',
                secondary: '#94D82A'
            },
            ...options
        };
        
        this.currentTheme = null;
        this.systemPreference = null;
        this.observers = [];
        this.isTransitioning = false;
        
        this.init();
    }
    
    /**
     * Initialize the theme manager
     */
    init() {
        this.detectSystemPreference();
        this.loadPersistedTheme();
        this.setupSystemPreferenceListener();
        this.validateBrandCompliance();
        
        // Apply initial theme
        const initialTheme = this.determineInitialTheme();
        this.applyTheme(initialTheme, false); // No transition on initial load
        
        console.log('🎨 ThemeManager initialized:', {
            currentTheme: this.currentTheme,
            systemPreference: this.systemPreference,
            brandCompliance: this.validateBrandCompliance(),
            documentTheme: document.documentElement.getAttribute('data-theme'),
            bodyTheme: document.body.getAttribute('data-theme')
        });
    }
    
    /**
     * Get the current active theme
     * @returns {string} Current theme name
     */
    getCurrentTheme() {
        return this.currentTheme;
    }
    
    /**
     * Set a specific theme
     * @param {string} themeName - Theme to apply ('light', 'dark', 'auto')
     * @param {boolean} persist - Whether to save preference
     */
    setTheme(themeName, persist = true) {
        if (!this.isValidTheme(themeName)) {
            console.warn(`Invalid theme: ${themeName}. Using default.`);
            themeName = this.options.defaultTheme;
        }
        
        const resolvedTheme = this.resolveTheme(themeName);
        
        if (resolvedTheme === this.currentTheme) {
            return; // No change needed
        }
        
        this.applyTheme(resolvedTheme, true);
        
        if (persist) {
            this.persistTheme(themeName);
        }
        
        this.notifyObservers('themeChanged', {
            from: this.currentTheme,
            to: resolvedTheme,
            preference: themeName
        });
    }
    
    /**
     * Toggle between light and dark themes
     */
    toggleTheme() {
        const currentResolved = this.resolveTheme(this.currentTheme);
        const newTheme = currentResolved === 'light' ? 'dark' : 'light';
        
        console.log('🔄 Toggling theme:', {
            from: currentResolved,
            to: newTheme,
            currentTheme: this.currentTheme
        });
        
        this.setTheme(newTheme);
    }
    
    /**
     * Detect system color scheme preference
     * @returns {string} System preference ('light' or 'dark')
     */
    detectSystemPreference() {
        if (typeof window === 'undefined' || !window.matchMedia) {
            this.systemPreference = 'dark';
            return this.systemPreference;
        }
        
        const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
        this.systemPreference = darkModeQuery.matches ? 'dark' : 'light';
        
        return this.systemPreference;
    }
    
    /**
     * Persist theme preference to localStorage
     * @param {string} themeName - Theme preference to save
     */
    persistTheme(themeName) {
        try {
            localStorage.setItem(this.options.storageKey, themeName);
        } catch (error) {
            console.warn('Failed to persist theme preference:', error);
        }
    }
    
    /**
     * Load persisted theme preference from localStorage
     * @returns {string|null} Persisted theme or null
     */
    loadPersistedTheme() {
        try {
            const stored = localStorage.getItem(this.options.storageKey);
            return this.isValidTheme(stored) ? stored : null;
        } catch (error) {
            console.warn('Failed to load theme preference:', error);
            return null;
        }
    }
    
    /**
     * Apply theme to the document
     * @param {string} themeName - Theme to apply
     * @param {boolean} withTransition - Whether to use transition
     */
    applyTheme(themeName, withTransition = true) {
        if (this.isTransitioning && withTransition) {
            return; // Prevent concurrent theme changes only if transition is requested
        }
        
        const resolvedTheme = this.resolveTheme(themeName);
        const previousTheme = this.currentTheme;
        
        // Skip if no change needed
        if (resolvedTheme === previousTheme && this.currentTheme) {
            return;
        }
        
        if (withTransition) {
            this.startThemeTransition();
        }
        
        // Update document attributes immediately
        document.documentElement.setAttribute('data-theme', resolvedTheme);
        document.body.setAttribute('data-theme', resolvedTheme);
        
        // Update color-scheme for browser UI
        document.documentElement.style.colorScheme = resolvedTheme;
        
        // Force immediate style recalculation
        this.forceStyleRecalculation();
        
        // Update current theme
        this.currentTheme = resolvedTheme;
        
        // Update theme-specific assets (logos, icons)
        this.updateThemeAssets(resolvedTheme);
        
        // Update meta theme-color for mobile browsers
        this.updateMetaThemeColor(resolvedTheme);
        
        // Apply additional theme-specific styling
        this.applyThemeSpecificStyles(resolvedTheme);
        
        // Force a repaint to ensure theme is applied immediately
        if (!withTransition) {
            document.body.offsetHeight; // Trigger reflow
        }
        
        if (withTransition) {
            setTimeout(() => {
                this.endThemeTransition();
            }, this.options.transitionDuration);
        }
        
        // Announce theme change for screen readers
        if (previousTheme && previousTheme !== resolvedTheme) {
            this.announceThemeChange(previousTheme, resolvedTheme);
        }
        
        console.log(`🎨 Theme applied: ${resolvedTheme}`);
    }
    
    /**
     * Validate brand compliance of current theme
     * @returns {boolean} Whether theme is brand compliant
     */
    validateBrandCompliance() {
        const compliance = {
            isValid: true,
            violations: []
        };
        
        // Check if brand colors are properly defined
        const rootStyles = getComputedStyle(document.documentElement);
        const primaryColor = rootStyles.getPropertyValue('--brand-blue-primary').trim();
        const secondaryColor = rootStyles.getPropertyValue('--brand-green-secondary').trim();
        
        if (primaryColor !== this.options.brandColors.primary) {
            compliance.violations.push({
                type: 'color',
                expected: this.options.brandColors.primary,
                actual: primaryColor,
                property: '--brand-blue-primary'
            });
            compliance.isValid = false;
        }
        
        if (secondaryColor !== this.options.brandColors.secondary) {
            compliance.violations.push({
                type: 'color',
                expected: this.options.brandColors.secondary,
                actual: secondaryColor,
                property: '--brand-green-secondary'
            });
            compliance.isValid = false;
        }
        
        if (!compliance.isValid) {
            console.warn('🚨 Brand compliance violations detected:', compliance.violations);
        }
        
        return compliance.isValid;
    }
    
    /**
     * Add observer for theme changes
     * @param {Function} callback - Function to call on theme change
     */
    addObserver(callback) {
        if (typeof callback === 'function') {
            this.observers.push(callback);
        }
    }
    
    /**
     * Remove observer
     * @param {Function} callback - Function to remove
     */
    removeObserver(callback) {
        const index = this.observers.indexOf(callback);
        if (index > -1) {
            this.observers.splice(index, 1);
        }
    }
    
    /**
     * Get theme information for debugging
     * @returns {Object} Theme debug information
     */
    getDebugInfo() {
        return {
            currentTheme: this.currentTheme,
            systemPreference: this.systemPreference,
            persistedTheme: this.loadPersistedTheme(),
            isTransitioning: this.isTransitioning,
            brandCompliance: this.validateBrandCompliance(),
            observers: this.observers.length
        };
    }
    
    // Private methods
    
    /**
     * Determine initial theme based on preferences
     * @returns {string} Initial theme to apply
     */
    determineInitialTheme() {
        const persisted = this.loadPersistedTheme();
        
        if (persisted === 'auto' || !persisted) {
            return this.systemPreference || this.options.defaultTheme;
        }
        
        return this.resolveTheme(persisted);
    }
    
    /**
     * Resolve theme preference to actual theme
     * @param {string} preference - Theme preference
     * @returns {string} Resolved theme
     */
    resolveTheme(preference) {
        if (preference === 'auto') {
            return this.systemPreference || this.options.defaultTheme;
        }
        return preference;
    }
    
    /**
     * Check if theme name is valid
     * @param {string} themeName - Theme to validate
     * @returns {boolean} Whether theme is valid
     */
    isValidTheme(themeName) {
        const validThemes = ['light', 'dark', 'auto'];
        return validThemes.includes(themeName);
    }
    
    /**
     * Setup listener for system preference changes
     */
    setupSystemPreferenceListener() {
        if (typeof window === 'undefined' || !window.matchMedia) {
            return;
        }
        
        const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
        
        const handleSystemChange = (e) => {
            const newSystemPreference = e.matches ? 'dark' : 'light';
            const oldSystemPreference = this.systemPreference;
            this.systemPreference = newSystemPreference;
            
            // If user has 'auto' preference, update theme
            const persistedTheme = this.loadPersistedTheme();
            if (persistedTheme === 'auto' || !persistedTheme) {
                this.applyTheme(newSystemPreference, true);
                
                this.notifyObservers('systemPreferenceChanged', {
                    from: oldSystemPreference,
                    to: newSystemPreference
                });
            }
        };
        
        // Modern browsers
        if (darkModeQuery.addEventListener) {
            darkModeQuery.addEventListener('change', handleSystemChange);
        } else {
            // Legacy browsers
            darkModeQuery.addListener(handleSystemChange);
        }
    }
    
    /**
     * Start theme transition
     */
    startThemeTransition() {
        this.isTransitioning = true;
        document.body.classList.add('theme-transitioning');
    }
    
    /**
     * End theme transition
     */
    endThemeTransition() {
        this.isTransitioning = false;
        document.body.classList.remove('theme-transitioning');
        document.body.classList.add('theme-transition-complete');
        
        // Remove completion class after a short delay
        setTimeout(() => {
            document.body.classList.remove('theme-transition-complete');
        }, 100);
    }
    
    /**
     * Update theme-specific assets
     * @param {string} theme - Current theme
     */
    updateThemeAssets(theme) {
        // Update logo variants
        const lightLogos = document.querySelectorAll('.logo-light, [data-logo="light"]');
        const darkLogos = document.querySelectorAll('.logo-dark, [data-logo="dark"]');
        
        lightLogos.forEach(logo => {
            logo.style.display = theme === 'light' ? 'block' : 'none';
        });
        
        darkLogos.forEach(logo => {
            logo.style.display = theme === 'dark' ? 'block' : 'none';
        });
        
        // Update theme toggle icon
        const themeIcon = document.getElementById('themeIcon');
        if (themeIcon) {
            themeIcon.className = theme === 'light' 
                ? 'fas fa-moon theme-icon' 
                : 'fas fa-sun theme-icon';
        }
    }
    
    /**
     * Update meta theme-color for mobile browsers
     * @param {string} theme - Current theme
     */
    updateMetaThemeColor(theme) {
        let metaThemeColor = document.querySelector('meta[name="theme-color"]');
        
        if (!metaThemeColor) {
            metaThemeColor = document.createElement('meta');
            metaThemeColor.name = 'theme-color';
            document.head.appendChild(metaThemeColor);
        }
        
        const themeColors = {
            light: '#ffffff',
            dark: '#0f172a'
        };
        
        metaThemeColor.content = themeColors[theme] || themeColors.dark;
    }
    
    /**
     * Announce theme change for screen readers
     * @param {string} from - Previous theme
     * @param {string} to - New theme
     */
    announceThemeChange(from, to) {
        if (from === to) return;
        
        const announcer = document.getElementById('theme-announcer') || this.createAnnouncer();
        const message = `Theme changed to ${to} mode`;
        
        announcer.textContent = message;
        
        // Clear after announcement
        setTimeout(() => {
            announcer.textContent = '';
        }, 1000);
    }
    
    /**
     * Create screen reader announcer element
     * @returns {HTMLElement} Announcer element
     */
    createAnnouncer() {
        const announcer = document.createElement('div');
        announcer.id = 'theme-announcer';
        announcer.setAttribute('aria-live', 'polite');
        announcer.setAttribute('aria-atomic', 'true');
        announcer.className = 'sr-only';
        document.body.appendChild(announcer);
        return announcer;
    }
    
    /**
     * Force style recalculation to ensure theme changes are applied
     */
    forceStyleRecalculation() {
        // Force browser to recalculate styles
        document.body.style.display = 'none';
        document.body.offsetHeight; // Trigger reflow
        document.body.style.display = '';
        
        // Alternative method for better performance
        const tempElement = document.createElement('div');
        tempElement.style.cssText = 'position:absolute;top:-9999px;left:-9999px;width:1px;height:1px;';
        document.body.appendChild(tempElement);
        tempElement.offsetHeight; // Trigger reflow
        document.body.removeChild(tempElement);
    }
    
    /**
     * Apply theme-specific styles that might not be handled by CSS
     * @param {string} theme - Current theme
     */
    applyThemeSpecificStyles(theme) {
        // Update all elements with theme-dependent styling
        const elementsToUpdate = [
            { selector: '.navbar', property: 'background-color' },
            { selector: '.card', property: 'background-color' },
            { selector: '.modal-content', property: 'background-color' },
            { selector: '.bg-dark', property: 'background-color' }
        ];
        
        elementsToUpdate.forEach(({ selector, property }) => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                // Let CSS handle the styling, just trigger a repaint
                element.style.transition = 'all 0.3s ease';
                
                // Force style recalculation
                const computedStyle = getComputedStyle(element);
                element.style.backgroundColor = computedStyle.backgroundColor;
                
                // Remove inline style to let CSS take over
                setTimeout(() => {
                    element.style.backgroundColor = '';
                }, 50);
            });
        });
        
        // Update text colors
        const textElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, span, div');
        textElements.forEach(element => {
            // Force color recalculation
            const computedStyle = getComputedStyle(element);
            element.style.color = computedStyle.color;
            
            // Remove inline style to let CSS take over
            setTimeout(() => {
                element.style.color = '';
            }, 50);
        });
    }
    
    /**
     * Notify all observers of theme events
     * @param {string} event - Event type
     * @param {Object} data - Event data
     */
    notifyObservers(event, data) {
        this.observers.forEach(callback => {
            try {
                callback(event, data);
            } catch (error) {
                console.error('Theme observer error:', error);
            }
        });
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}

// Global instance for immediate use
window.ThemeManager = ThemeManager;