/**
 * Logo Manager - Snooker Detection Pro
 * Handles theme-aware logo switching and brand asset management
 * Ensures proper logo variants are displayed based on current theme
 */

class LogoManager {
    constructor(options = {}) {
        this.options = {
            logoBasePath: '/static/assets/logos/',
            fallbackText: 'Snooker Detection Pro',
            logoVariants: {
                light: {
                    primary: 'logo-light.svg',
                    secondary: 'logo-light-secondary.svg',
                    icon: 'icon-light.svg'
                },
                dark: {
                    primary: 'logo-dark.svg',
                    secondary: 'logo-dark-secondary.svg',
                    icon: 'icon-dark.svg'
                },
                color: {
                    primary: 'logo-color.svg',
                    secondary: 'logo-color-secondary.svg',
                    icon: 'icon-color.svg'
                }
            },
            sizes: {
                small: { width: 120, height: 40 },
                medium: { width: 180, height: 60 },
                large: { width: 240, height: 80 },
                xlarge: { width: 320, height: 107 }
            },
            ...options
        };
        
        this.currentTheme = 'dark';
        this.logoElements = new Map();
        this.observers = [];
        
        this.init();
    }
    
    /**
     * Initialize the logo manager
     */
    init() {
        this.scanLogoElements();
        this.setupThemeObserver();
        this.preloadLogoAssets();
        
        console.log('🎨 LogoManager initialized with', this.logoElements.size, 'logo elements');
    }
    
    /**
     * Scan DOM for logo elements and register them
     */
    scanLogoElements() {
        // Find all logo elements with data-logo attributes
        const logoSelectors = [
            '[data-logo]',
            '.logo',
            '.navbar-brand img',
            '.brand-logo',
            '.logo-light',
            '.logo-dark',
            '.logo-color'
        ];
        
        logoSelectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(element => {
                this.registerLogoElement(element);
            });
        });
    }
    
    /**
     * Register a logo element for theme-aware switching
     * @param {HTMLElement} element - Logo element to register
     * @param {Object} config - Logo configuration
     */
    registerLogoElement(element, config = {}) {
        const logoId = element.id || `logo-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        if (!element.id) {
            element.id = logoId;
        }
        
        const logoConfig = {
            element,
            variant: element.dataset.logoVariant || config.variant || 'primary',
            size: element.dataset.logoSize || config.size || 'medium',
            theme: element.dataset.logoTheme || config.theme || 'auto',
            fallbackText: element.dataset.logoFallback || config.fallbackText || this.options.fallbackText,
            originalSrc: element.src || element.dataset.logoSrc,
            ...config
        };
        
        this.logoElements.set(logoId, logoConfig);
        
        // Apply initial logo
        this.updateLogoElement(logoId);
        
        return logoId;
    }
    
    /**
     * Update logo element based on current theme
     * @param {string} logoId - Logo element ID
     */
    updateLogoElement(logoId) {
        const config = this.logoElements.get(logoId);
        if (!config) return;
        
        const { element, variant, size, theme } = config;
        const resolvedTheme = theme === 'auto' ? this.currentTheme : theme;
        
        // Get appropriate logo source
        const logoSrc = this.getLogoSource(variant, resolvedTheme);
        const logoSize = this.options.sizes[size] || this.options.sizes.medium;
        
        if (element.tagName.toLowerCase() === 'img') {
            // Handle img elements
            this.updateImageLogo(element, logoSrc, logoSize, config);
        } else {
            // Handle other elements (divs, spans, etc.)
            this.updateElementLogo(element, logoSrc, logoSize, config);
        }
        
        // Add theme-specific classes
        element.classList.remove('logo-light', 'logo-dark', 'logo-color');
        element.classList.add(`logo-${resolvedTheme}`);
        
        // Update accessibility attributes
        element.setAttribute('aria-label', `${config.fallbackText} logo (${resolvedTheme} theme)`);
    }
    
    /**
     * Update image logo element
     * @param {HTMLImageElement} img - Image element
     * @param {string} src - Logo source URL
     * @param {Object} size - Logo dimensions
     * @param {Object} config - Logo configuration
     */
    updateImageLogo(img, src, size, config) {
        // Create a new image to preload
        const newImg = new Image();
        
        newImg.onload = () => {
            img.src = src;
            img.width = size.width;
            img.height = size.height;
            img.style.width = `${size.width}px`;
            img.style.height = `${size.height}px`;
            
            // Add smooth transition
            img.style.transition = 'opacity 0.3s ease';
            img.style.opacity = '1';
        };
        
        newImg.onerror = () => {
            console.warn(`Failed to load logo: ${src}`);
            this.handleLogoError(img, config);
        };
        
        // Start loading
        img.style.opacity = '0.7';
        newImg.src = src;
    }
    
    /**
     * Update non-image logo element
     * @param {HTMLElement} element - Element to update
     * @param {string} src - Logo source URL
     * @param {Object} size - Logo dimensions
     * @param {Object} config - Logo configuration
     */
    updateElementLogo(element, src, size, config) {
        // Set as background image
        element.style.backgroundImage = `url(${src})`;
        element.style.backgroundSize = 'contain';
        element.style.backgroundRepeat = 'no-repeat';
        element.style.backgroundPosition = 'center';
        element.style.width = `${size.width}px`;
        element.style.height = `${size.height}px`;
        
        // Add transition
        element.style.transition = 'background-image 0.3s ease';
        
        // Handle loading error
        const testImg = new Image();
        testImg.onerror = () => {
            console.warn(`Failed to load logo: ${src}`);
            this.handleLogoError(element, config);
        };
        testImg.src = src;
    }
    
    /**
     * Handle logo loading errors
     * @param {HTMLElement} element - Logo element
     * @param {Object} config - Logo configuration
     */
    handleLogoError(element, config) {
        // Fallback to text-based logo
        if (element.tagName.toLowerCase() === 'img') {
            element.style.display = 'none';
            
            // Create text fallback
            const textLogo = document.createElement('span');
            textLogo.className = 'logo-text-fallback';
            textLogo.textContent = config.fallbackText;
            textLogo.style.cssText = `
                font-weight: 800;
                font-size: 1.5rem;
                background: var(--gradient-accent);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                display: inline-block;
            `;
            
            element.parentNode.insertBefore(textLogo, element.nextSibling);
        } else {
            // For non-img elements, show text
            element.style.backgroundImage = 'none';
            element.textContent = config.fallbackText;
            element.style.cssText += `
                font-weight: 800;
                font-size: 1.5rem;
                background: var(--gradient-accent);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                display: flex;
                align-items: center;
                justify-content: center;
            `;
        }
    }
    
    /**
     * Get logo source URL for theme and variant
     * @param {string} variant - Logo variant (primary, secondary, icon)
     * @param {string} theme - Theme (light, dark, color)
     * @returns {string} Logo source URL
     */
    getLogoSource(variant, theme) {
        const logoVariants = this.options.logoVariants[theme];
        if (!logoVariants) {
            console.warn(`No logo variants found for theme: ${theme}`);
            return this.getFallbackLogoSource(variant);
        }
        
        const logoFile = logoVariants[variant];
        if (!logoFile) {
            console.warn(`No logo file found for variant: ${variant} in theme: ${theme}`);
            return this.getFallbackLogoSource(variant);
        }
        
        return this.options.logoBasePath + logoFile;
    }
    
    /**
     * Get fallback logo source
     * @param {string} variant - Logo variant
     * @returns {string} Fallback logo source
     */
    getFallbackLogoSource(variant) {
        // Try to use existing logo assets from logo-guidelines
        const fallbackMap = {
            primary: '/static/logo-guidelines/primary-logo.png',
            secondary: '/static/logo-guidelines/secondary-logo.png',
            icon: '/static/logo-guidelines/color-logo.png'
        };
        
        return fallbackMap[variant] || fallbackMap.primary;
    }
    
    /**
     * Set current theme and update all logos
     * @param {string} theme - Theme to apply
     */
    setTheme(theme) {
        if (this.currentTheme === theme) return;
        
        const previousTheme = this.currentTheme;
        this.currentTheme = theme;
        
        // Update all registered logo elements
        this.logoElements.forEach((config, logoId) => {
            this.updateLogoElement(logoId);
        });
        
        // Notify observers
        this.notifyObservers('themeChanged', {
            from: previousTheme,
            to: theme
        });
        
        console.log(`🎨 Logo theme updated: ${previousTheme} → ${theme}`);
    }
    
    /**
     * Preload logo assets for smooth switching
     */
    preloadLogoAssets() {
        const themes = Object.keys(this.options.logoVariants);
        const variants = ['primary', 'secondary', 'icon'];
        
        themes.forEach(theme => {
            variants.forEach(variant => {
                const src = this.getLogoSource(variant, theme);
                const img = new Image();
                img.src = src;
                // Preload silently - errors are expected for missing assets
            });
        });
    }
    
    /**
     * Setup theme observer to listen for theme changes
     */
    setupThemeObserver() {
        // Listen for theme changes from ThemeManager
        if (typeof window !== 'undefined') {
            window.addEventListener('themeChanged', (e) => {
                if (e.detail && e.detail.to) {
                    this.setTheme(e.detail.to);
                }
            });
            
            // Also listen for manual theme attribute changes
            const observer = new MutationObserver((mutations) => {
                mutations.forEach(mutation => {
                    if (mutation.type === 'attributes' && 
                        (mutation.attributeName === 'data-theme' || mutation.attributeName === 'class')) {
                        const newTheme = document.body.getAttribute('data-theme') || 
                                       document.documentElement.getAttribute('data-theme');
                        if (newTheme && newTheme !== this.currentTheme) {
                            this.setTheme(newTheme);
                        }
                    }
                });
            });
            
            observer.observe(document.body, { attributes: true });
            observer.observe(document.documentElement, { attributes: true });
        }
    }
    
    /**
     * Create SVG logo variants programmatically
     * @param {string} text - Logo text
     * @param {string} theme - Theme variant
     * @returns {string} SVG data URL
     */
    createSVGLogo(text, theme = 'dark') {
        const colors = {
            light: {
                primary: '#0B405B',
                secondary: '#94D82A',
                text: '#0B405B'
            },
            dark: {
                primary: '#94D82A',
                secondary: '#0B405B',
                text: '#94D82A'
            },
            color: {
                primary: '#0B405B',
                secondary: '#94D82A',
                text: '#0B405B'
            }
        };
        
        const themeColors = colors[theme] || colors.dark;
        
        const svg = `
            <svg width="240" height="80" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" style="stop-color:${themeColors.primary};stop-opacity:1" />
                        <stop offset="100%" style="stop-color:${themeColors.secondary};stop-opacity:1" />
                    </linearGradient>
                </defs>
                <circle cx="40" cy="40" r="25" fill="${themeColors.secondary}" opacity="0.8"/>
                <circle cx="35" cy="35" r="8" fill="white" opacity="0.3"/>
                <text x="80" y="50" font-family="Inter, sans-serif" font-size="24" font-weight="800" fill="url(#logoGradient)">
                    ${text}
                </text>
            </svg>
        `;
        
        return `data:image/svg+xml;base64,${btoa(svg)}`;
    }
    
    /**
     * Add observer for logo events
     * @param {Function} callback - Observer callback
     */
    addObserver(callback) {
        if (typeof callback === 'function') {
            this.observers.push(callback);
        }
    }
    
    /**
     * Remove observer
     * @param {Function} callback - Observer to remove
     */
    removeObserver(callback) {
        const index = this.observers.indexOf(callback);
        if (index > -1) {
            this.observers.splice(index, 1);
        }
    }
    
    /**
     * Notify observers of logo events
     * @param {string} event - Event type
     * @param {Object} data - Event data
     */
    notifyObservers(event, data) {
        this.observers.forEach(callback => {
            try {
                callback(event, data);
            } catch (error) {
                console.error('Logo observer error:', error);
            }
        });
    }
    
    /**
     * Get debug information
     * @returns {Object} Debug info
     */
    getDebugInfo() {
        return {
            currentTheme: this.currentTheme,
            registeredLogos: this.logoElements.size,
            logoElements: Array.from(this.logoElements.entries()).map(([id, config]) => ({
                id,
                variant: config.variant,
                size: config.size,
                theme: config.theme,
                element: config.element.tagName
            })),
            observers: this.observers.length
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LogoManager;
}

// Global access
window.LogoManager = LogoManager;