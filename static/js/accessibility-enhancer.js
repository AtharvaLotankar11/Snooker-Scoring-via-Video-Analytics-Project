/**
 * Accessibility Enhancer - Snooker Detection Pro
 * Comprehensive accessibility features including high contrast, reduced motion,
 * keyboard navigation, and screen reader support
 */

class AccessibilityEnhancer {
    constructor(options = {}) {
        this.options = {
            highContrastStorageKey: 'snooker-high-contrast',
            reducedMotionStorageKey: 'snooker-reduced-motion',
            fontSizeStorageKey: 'snooker-font-size',
            keyboardNavStorageKey: 'snooker-keyboard-nav',
            announceChanges: true,
            enableKeyboardShortcuts: true,
            ...options
        };
        
        this.state = {
            highContrast: false,
            reducedMotion: false,
            fontSize: 'medium',
            keyboardNavigation: false,
            screenReaderActive: false
        };
        
        this.observers = [];
        this.keyboardTrapStack = [];
        this.focusHistory = [];
        
        this.init();
    }
    
    /**
     * Initialize accessibility enhancer
     */
    init() {
        this.detectSystemPreferences();
        this.loadUserPreferences();
        this.setupEventListeners();
        this.createAccessibilityControls();
        this.enhanceExistingElements();
        this.setupKeyboardShortcuts();
        
        console.log('♿ AccessibilityEnhancer initialized:', this.state);
    }
    
    /**
     * Detect system accessibility preferences
     */
    detectSystemPreferences() {
        if (typeof window === 'undefined') return;
        
        // Detect reduced motion preference
        if (window.matchMedia) {
            const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
            this.state.reducedMotion = reducedMotionQuery.matches;
            
            // Listen for changes
            reducedMotionQuery.addEventListener('change', (e) => {
                this.setReducedMotion(e.matches, false); // Don't persist system changes
            });
            
            // Detect high contrast preference
            const highContrastQuery = window.matchMedia('(prefers-contrast: high)');
            this.state.highContrast = highContrastQuery.matches;
            
            highContrastQuery.addEventListener('change', (e) => {
                this.setHighContrast(e.matches, false);
            });
        }
        
        // Detect screen reader
        this.detectScreenReader();
    }
    
    /**
     * Detect if screen reader is active
     */
    detectScreenReader() {
        // Check for common screen reader indicators
        const indicators = [
            () => navigator.userAgent.includes('NVDA'),
            () => navigator.userAgent.includes('JAWS'),
            () => navigator.userAgent.includes('VoiceOver'),
            () => window.speechSynthesis && window.speechSynthesis.getVoices().length > 0,
            () => 'speechSynthesis' in window
        ];
        
        this.state.screenReaderActive = indicators.some(check => {
            try {
                return check();
            } catch {
                return false;
            }
        });
        
        if (this.state.screenReaderActive) {
            document.body.classList.add('screen-reader-active');
        }
    }
    
    /**
     * Load user accessibility preferences
     */
    loadUserPreferences() {
        try {
            const highContrast = localStorage.getItem(this.options.highContrastStorageKey);
            if (highContrast !== null) {
                this.state.highContrast = highContrast === 'true';
            }
            
            const reducedMotion = localStorage.getItem(this.options.reducedMotionStorageKey);
            if (reducedMotion !== null) {
                this.state.reducedMotion = reducedMotion === 'true';
            }
            
            const fontSize = localStorage.getItem(this.options.fontSizeStorageKey);
            if (fontSize) {
                this.state.fontSize = fontSize;
            }
            
            const keyboardNav = localStorage.getItem(this.options.keyboardNavStorageKey);
            if (keyboardNav !== null) {
                this.state.keyboardNavigation = keyboardNav === 'true';
            }
        } catch (error) {
            console.warn('Failed to load accessibility preferences:', error);
        }
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Keyboard navigation detection
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                this.enableKeyboardNavigation();
            }
        });
        
        // Mouse usage detection
        document.addEventListener('mousedown', () => {
            this.disableKeyboardNavigation();
        });
        
        // Focus management
        document.addEventListener('focusin', (e) => {
            this.handleFocusIn(e);
        });
        
        document.addEventListener('focusout', (e) => {
            this.handleFocusOut(e);
        });
    }
    
    /**
     * Create accessibility control panel
     */
    createAccessibilityControls() {
        const controlPanel = document.createElement('div');
        controlPanel.id = 'accessibility-controls';
        controlPanel.className = 'accessibility-controls';
        controlPanel.setAttribute('role', 'region');
        controlPanel.setAttribute('aria-label', 'Accessibility controls');
        
        controlPanel.innerHTML = `
            <button class="accessibility-toggle" aria-label="Open accessibility options" title="Accessibility Options">
                <i class="fas fa-universal-access" aria-hidden="true"></i>
            </button>
            <div class="accessibility-panel" role="dialog" aria-labelledby="accessibility-title" aria-hidden="true">
                <div class="accessibility-header">
                    <h3 id="accessibility-title">Accessibility Options</h3>
                    <button class="accessibility-close" aria-label="Close accessibility options">
                        <i class="fas fa-times" aria-hidden="true"></i>
                    </button>
                </div>
                <div class="accessibility-content">
                    <div class="accessibility-group">
                        <h4>Visual</h4>
                        <label class="accessibility-option">
                            <input type="checkbox" id="high-contrast-toggle" ${this.state.highContrast ? 'checked' : ''}>
                            <span>High Contrast Mode</span>
                        </label>
                        <div class="accessibility-option">
                            <label for="font-size-select">Font Size:</label>
                            <select id="font-size-select">
                                <option value="small" ${this.state.fontSize === 'small' ? 'selected' : ''}>Small</option>
                                <option value="medium" ${this.state.fontSize === 'medium' ? 'selected' : ''}>Medium</option>
                                <option value="large" ${this.state.fontSize === 'large' ? 'selected' : ''}>Large</option>
                                <option value="xlarge" ${this.state.fontSize === 'xlarge' ? 'selected' : ''}>Extra Large</option>
                            </select>
                        </div>
                    </div>
                    <div class="accessibility-group">
                        <h4>Motion</h4>
                        <label class="accessibility-option">
                            <input type="checkbox" id="reduced-motion-toggle" ${this.state.reducedMotion ? 'checked' : ''}>
                            <span>Reduce Motion</span>
                        </label>
                    </div>
                    <div class="accessibility-group">
                        <h4>Navigation</h4>
                        <button id="skip-to-main" class="accessibility-button">Skip to Main Content</button>
                        <button id="focus-outline-toggle" class="accessibility-button">Toggle Focus Outlines</button>
                    </div>
                </div>
            </div>
        `;
        
        // Add styles
        const styles = document.createElement('style');
        styles.textContent = this.getAccessibilityStyles();
        document.head.appendChild(styles);
        
        document.body.appendChild(controlPanel);
        this.bindAccessibilityControls();
    }
    
    /**
     * Get accessibility control styles
     */
    getAccessibilityStyles() {
        return `
            .accessibility-controls {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                font-family: var(--font-family-primary);
            }
            
            .accessibility-toggle {
                width: 50px;
                height: 50px;
                border-radius: 50%;
                background: var(--brand-blue-primary);
                color: white;
                border: none;
                cursor: pointer;
                box-shadow: var(--shadow-lg);
                transition: all var(--transition-normal);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.2rem;
            }
            
            .accessibility-toggle:hover {
                background: var(--brand-blue-600);
                transform: scale(1.1);
            }
            
            .accessibility-toggle:focus {
                outline: 3px solid var(--brand-green-secondary);
                outline-offset: 2px;
            }
            
            .accessibility-panel {
                position: absolute;
                top: 60px;
                right: 0;
                width: 300px;
                background: var(--surface-primary);
                border: 2px solid var(--border-primary);
                border-radius: var(--radius-lg);
                box-shadow: var(--shadow-2xl);
                transform: translateY(-10px);
                opacity: 0;
                visibility: hidden;
                transition: all var(--transition-normal);
            }
            
            .accessibility-panel[aria-hidden="false"] {
                transform: translateY(0);
                opacity: 1;
                visibility: visible;
            }
            
            .accessibility-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: var(--space-4);
                border-bottom: 1px solid var(--border-primary);
            }
            
            .accessibility-header h3 {
                margin: 0;
                color: var(--text-primary);
                font-size: 1.1rem;
            }
            
            .accessibility-close {
                background: none;
                border: none;
                color: var(--text-secondary);
                cursor: pointer;
                padding: var(--space-2);
                border-radius: var(--radius-md);
            }
            
            .accessibility-close:hover {
                background: var(--surface-hover);
                color: var(--text-primary);
            }
            
            .accessibility-content {
                padding: var(--space-4);
            }
            
            .accessibility-group {
                margin-bottom: var(--space-4);
            }
            
            .accessibility-group h4 {
                margin: 0 0 var(--space-3) 0;
                color: var(--text-primary);
                font-size: 1rem;
                font-weight: var(--font-weight-semibold);
            }
            
            .accessibility-option {
                display: flex;
                align-items: center;
                gap: var(--space-2);
                margin-bottom: var(--space-3);
                color: var(--text-secondary);
            }
            
            .accessibility-option input[type="checkbox"] {
                width: 18px;
                height: 18px;
                accent-color: var(--brand-green-secondary);
            }
            
            .accessibility-option select {
                padding: var(--space-2);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-md);
                background: var(--surface-primary);
                color: var(--text-primary);
            }
            
            .accessibility-button {
                display: block;
                width: 100%;
                padding: var(--space-2) var(--space-3);
                margin-bottom: var(--space-2);
                background: var(--surface-secondary);
                border: 1px solid var(--border-primary);
                border-radius: var(--radius-md);
                color: var(--text-primary);
                cursor: pointer;
                transition: all var(--transition-fast);
            }
            
            .accessibility-button:hover {
                background: var(--surface-hover);
                border-color: var(--brand-green-secondary);
            }
            
            /* High contrast mode styles */
            .high-contrast {
                filter: contrast(150%) brightness(120%);
            }
            
            .high-contrast * {
                border-color: currentColor !important;
                outline-color: currentColor !important;
            }
            
            .high-contrast .card-base,
            .high-contrast .btn-base {
                border: 2px solid currentColor !important;
            }
            
            /* Reduced motion styles */
            .reduced-motion *,
            .reduced-motion *::before,
            .reduced-motion *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
                scroll-behavior: auto !important;
            }
            
            /* Font size adjustments */
            .font-size-small { font-size: 0.875rem; }
            .font-size-medium { font-size: 1rem; }
            .font-size-large { font-size: 1.125rem; }
            .font-size-xlarge { font-size: 1.25rem; }
            
            /* Keyboard navigation styles */
            .keyboard-navigation *:focus {
                outline: 3px solid var(--brand-green-secondary) !important;
                outline-offset: 2px !important;
                box-shadow: 0 0 0 5px rgba(148, 216, 42, 0.3) !important;
            }
            
            /* Screen reader styles */
            .screen-reader-active .sr-only {
                position: static !important;
                width: auto !important;
                height: auto !important;
                padding: var(--space-2) !important;
                margin: var(--space-1) !important;
                overflow: visible !important;
                clip: auto !important;
                white-space: normal !important;
                border: 1px solid var(--border-primary) !important;
                background: var(--surface-secondary) !important;
                color: var(--text-primary) !important;
            }
            
            @media (prefers-reduced-motion: reduce) {
                .accessibility-panel {
                    transition: none;
                }
                
                .accessibility-toggle {
                    transition: none;
                }
            }
        `;
    }
    
    /**
     * Bind accessibility control events
     */
    bindAccessibilityControls() {
        const toggle = document.querySelector('.accessibility-toggle');
        const panel = document.querySelector('.accessibility-panel');
        const closeBtn = document.querySelector('.accessibility-close');
        
        // Toggle panel
        toggle.addEventListener('click', () => {
            const isHidden = panel.getAttribute('aria-hidden') === 'true';
            panel.setAttribute('aria-hidden', !isHidden);
            
            if (!isHidden) {
                // Focus first interactive element when opening
                const firstInput = panel.querySelector('input, select, button');
                if (firstInput) firstInput.focus();
            }
        });
        
        // Close panel
        closeBtn.addEventListener('click', () => {
            panel.setAttribute('aria-hidden', 'true');
            toggle.focus();
        });
        
        // High contrast toggle
        document.getElementById('high-contrast-toggle').addEventListener('change', (e) => {
            this.setHighContrast(e.target.checked);
        });
        
        // Reduced motion toggle
        document.getElementById('reduced-motion-toggle').addEventListener('change', (e) => {
            this.setReducedMotion(e.target.checked);
        });
        
        // Font size selector
        document.getElementById('font-size-select').addEventListener('change', (e) => {
            this.setFontSize(e.target.value);
        });
        
        // Skip to main content
        document.getElementById('skip-to-main').addEventListener('click', () => {
            this.skipToMainContent();
        });
        
        // Focus outline toggle
        document.getElementById('focus-outline-toggle').addEventListener('click', () => {
            this.toggleFocusOutlines();
        });
        
        // Close panel on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && panel.getAttribute('aria-hidden') === 'false') {
                panel.setAttribute('aria-hidden', 'true');
                toggle.focus();
            }
        });
    }
    
    /**
     * Set high contrast mode
     * @param {boolean} enabled - Enable high contrast
     * @param {boolean} persist - Save preference
     */
    setHighContrast(enabled, persist = true) {
        this.state.highContrast = enabled;
        
        if (enabled) {
            document.body.classList.add('high-contrast');
        } else {
            document.body.classList.remove('high-contrast');
        }
        
        if (persist) {
            try {
                localStorage.setItem(this.options.highContrastStorageKey, enabled.toString());
            } catch (error) {
                console.warn('Failed to save high contrast preference:', error);
            }
        }
        
        this.announce(`High contrast mode ${enabled ? 'enabled' : 'disabled'}`);
        this.notifyObservers('highContrastChanged', { enabled });
    }
    
    /**
     * Set reduced motion mode
     * @param {boolean} enabled - Enable reduced motion
     * @param {boolean} persist - Save preference
     */
    setReducedMotion(enabled, persist = true) {
        this.state.reducedMotion = enabled;
        
        if (enabled) {
            document.body.classList.add('reduced-motion');
        } else {
            document.body.classList.remove('reduced-motion');
        }
        
        if (persist) {
            try {
                localStorage.setItem(this.options.reducedMotionStorageKey, enabled.toString());
            } catch (error) {
                console.warn('Failed to save reduced motion preference:', error);
            }
        }
        
        this.announce(`Reduced motion ${enabled ? 'enabled' : 'disabled'}`);
        this.notifyObservers('reducedMotionChanged', { enabled });
    }
    
    /**
     * Set font size
     * @param {string} size - Font size (small, medium, large, xlarge)
     */
    setFontSize(size) {
        const validSizes = ['small', 'medium', 'large', 'xlarge'];
        if (!validSizes.includes(size)) {
            console.warn(`Invalid font size: ${size}`);
            return;
        }
        
        this.state.fontSize = size;
        
        // Remove existing font size classes
        validSizes.forEach(s => {
            document.body.classList.remove(`font-size-${s}`);
        });
        
        // Add new font size class
        document.body.classList.add(`font-size-${size}`);
        
        try {
            localStorage.setItem(this.options.fontSizeStorageKey, size);
        } catch (error) {
            console.warn('Failed to save font size preference:', error);
        }
        
        this.announce(`Font size changed to ${size}`);
        this.notifyObservers('fontSizeChanged', { size });
    }
    
    /**
     * Enable keyboard navigation mode
     */
    enableKeyboardNavigation() {
        if (this.state.keyboardNavigation) return;
        
        this.state.keyboardNavigation = true;
        document.body.classList.add('keyboard-navigation');
        
        try {
            localStorage.setItem(this.options.keyboardNavStorageKey, 'true');
        } catch (error) {
            console.warn('Failed to save keyboard navigation preference:', error);
        }
        
        this.notifyObservers('keyboardNavigationEnabled', {});
    }
    
    /**
     * Disable keyboard navigation mode
     */
    disableKeyboardNavigation() {
        if (!this.state.keyboardNavigation) return;
        
        this.state.keyboardNavigation = false;
        document.body.classList.remove('keyboard-navigation');
        
        try {
            localStorage.setItem(this.options.keyboardNavStorageKey, 'false');
        } catch (error) {
            console.warn('Failed to save keyboard navigation preference:', error);
        }
        
        this.notifyObservers('keyboardNavigationDisabled', {});
    }
    
    /**
     * Skip to main content
     */
    skipToMainContent() {
        const main = document.querySelector('main, [role="main"], #main-content');
        if (main) {
            main.focus();
            main.scrollIntoView({ behavior: 'smooth', block: 'start' });
            this.announce('Skipped to main content');
        }
    }
    
    /**
     * Toggle focus outlines visibility
     */
    toggleFocusOutlines() {
        const hasOutlines = document.body.classList.contains('show-focus-outlines');
        
        if (hasOutlines) {
            document.body.classList.remove('show-focus-outlines');
            this.announce('Focus outlines hidden');
        } else {
            document.body.classList.add('show-focus-outlines');
            this.announce('Focus outlines visible');
        }
    }
    
    /**
     * Setup keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        if (!this.options.enableKeyboardShortcuts) return;
        
        document.addEventListener('keydown', (e) => {
            // Alt + H: Toggle high contrast
            if (e.altKey && e.key === 'h') {
                e.preventDefault();
                this.setHighContrast(!this.state.highContrast);
            }
            
            // Alt + M: Toggle reduced motion
            if (e.altKey && e.key === 'm') {
                e.preventDefault();
                this.setReducedMotion(!this.state.reducedMotion);
            }
            
            // Alt + A: Open accessibility panel
            if (e.altKey && e.key === 'a') {
                e.preventDefault();
                const toggle = document.querySelector('.accessibility-toggle');
                if (toggle) toggle.click();
            }
            
            // Alt + S: Skip to main content
            if (e.altKey && e.key === 's') {
                e.preventDefault();
                this.skipToMainContent();
            }
        });
    }
    
    /**
     * Enhance existing elements with accessibility features
     */
    enhanceExistingElements() {
        // Add skip links
        this.addSkipLinks();
        
        // Enhance form labels
        this.enhanceFormLabels();
        
        // Add ARIA landmarks
        this.addAriaLandmarks();
        
        // Enhance interactive elements
        this.enhanceInteractiveElements();
    }
    
    /**
     * Add skip navigation links
     */
    addSkipLinks() {
        const skipLinks = document.createElement('div');
        skipLinks.className = 'skip-links';
        skipLinks.innerHTML = `
            <a href="#main-content" class="skip-link">Skip to main content</a>
            <a href="#navigation" class="skip-link">Skip to navigation</a>
        `;
        
        const skipStyles = `
            .skip-links {
                position: absolute;
                top: -40px;
                left: 0;
                z-index: 10001;
            }
            
            .skip-link {
                position: absolute;
                top: -40px;
                left: 6px;
                background: var(--brand-blue-primary);
                color: white;
                padding: 8px 16px;
                text-decoration: none;
                border-radius: var(--radius-md);
                font-weight: var(--font-weight-semibold);
                transition: top var(--transition-fast);
            }
            
            .skip-link:focus {
                top: 6px;
            }
        `;
        
        const style = document.createElement('style');
        style.textContent = skipStyles;
        document.head.appendChild(style);
        
        document.body.insertBefore(skipLinks, document.body.firstChild);
    }
    
    /**
     * Enhance form labels and associations
     */
    enhanceFormLabels() {
        // Find inputs without labels
        const inputs = document.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (!input.id) {
                input.id = `input-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
            }
            
            // Check if input has associated label
            const label = document.querySelector(`label[for="${input.id}"]`);
            if (!label && !input.getAttribute('aria-label') && !input.getAttribute('aria-labelledby')) {
                // Add aria-label based on placeholder or nearby text
                const placeholder = input.getAttribute('placeholder');
                if (placeholder) {
                    input.setAttribute('aria-label', placeholder);
                }
            }
        });
    }
    
    /**
     * Add ARIA landmarks to page structure
     */
    addAriaLandmarks() {
        // Add main landmark
        const main = document.querySelector('main');
        if (main && !main.getAttribute('role')) {
            main.setAttribute('role', 'main');
            main.id = main.id || 'main-content';
        }
        
        // Add navigation landmark
        const nav = document.querySelector('nav');
        if (nav && !nav.getAttribute('role')) {
            nav.setAttribute('role', 'navigation');
            nav.id = nav.id || 'navigation';
        }
        
        // Add banner landmark
        const header = document.querySelector('header');
        if (header && !header.getAttribute('role')) {
            header.setAttribute('role', 'banner');
        }
        
        // Add contentinfo landmark
        const footer = document.querySelector('footer');
        if (footer && !footer.getAttribute('role')) {
            footer.setAttribute('role', 'contentinfo');
        }
    }
    
    /**
     * Enhance interactive elements
     */
    enhanceInteractiveElements() {
        // Add role and aria attributes to buttons
        const buttons = document.querySelectorAll('button:not([role])');
        buttons.forEach(button => {
            if (!button.getAttribute('role')) {
                button.setAttribute('role', 'button');
            }
        });
        
        // Enhance cards that are clickable
        const clickableCards = document.querySelectorAll('.card[onclick], .card-base[onclick]');
        clickableCards.forEach(card => {
            card.setAttribute('role', 'button');
            card.setAttribute('tabindex', '0');
            
            // Add keyboard support
            card.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    card.click();
                }
            });
        });
    }
    
    /**
     * Handle focus in events
     */
    handleFocusIn(event) {
        this.focusHistory.push({
            element: event.target,
            timestamp: Date.now()
        });
        
        // Keep only last 10 focus events
        if (this.focusHistory.length > 10) {
            this.focusHistory.shift();
        }
    }
    
    /**
     * Handle focus out events
     */
    handleFocusOut(event) {
        // Could be used for focus management if needed
    }
    
    /**
     * Announce message to screen readers
     * @param {string} message - Message to announce
     */
    announce(message) {
        if (!this.options.announceChanges) return;
        
        let announcer = document.getElementById('accessibility-announcer');
        if (!announcer) {
            announcer = document.createElement('div');
            announcer.id = 'accessibility-announcer';
            announcer.setAttribute('aria-live', 'polite');
            announcer.setAttribute('aria-atomic', 'true');
            announcer.className = 'sr-only';
            document.body.appendChild(announcer);
        }
        
        announcer.textContent = message;
        
        // Clear after announcement
        setTimeout(() => {
            announcer.textContent = '';
        }, 1000);
    }
    
    /**
     * Add observer for accessibility events
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
     * Notify observers of accessibility events
     * @param {string} event - Event type
     * @param {Object} data - Event data
     */
    notifyObservers(event, data) {
        this.observers.forEach(callback => {
            try {
                callback(event, data);
            } catch (error) {
                console.error('Accessibility observer error:', error);
            }
        });
    }
    
    /**
     * Get current accessibility state
     * @returns {Object} Current state
     */
    getState() {
        return { ...this.state };
    }
    
    /**
     * Get debug information
     * @returns {Object} Debug info
     */
    getDebugInfo() {
        return {
            state: this.state,
            focusHistory: this.focusHistory.slice(-5),
            observers: this.observers.length,
            keyboardTrapStack: this.keyboardTrapStack.length
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AccessibilityEnhancer;
}

// Global access
window.AccessibilityEnhancer = AccessibilityEnhancer;