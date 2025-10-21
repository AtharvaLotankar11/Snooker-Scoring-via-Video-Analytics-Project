/**
 * ThemeSwitcher Component - Snooker Detection Pro
 * Accessible theme toggle UI component with keyboard navigation
 * Integrates with ThemeManager for theme switching functionality
 */

class ThemeSwitcher {
    constructor(container, themeManager, options = {}) {
        this.container = typeof container === 'string' 
            ? document.querySelector(container) 
            : container;
        
        this.themeManager = themeManager;
        this.options = {
            showLabels: true,
            showAuto: true,
            size: 'medium', // 'small', 'medium', 'large'
            variant: 'toggle', // 'toggle', 'dropdown', 'radio'
            position: 'right', // 'left', 'right', 'center'
            ...options
        };
        
        this.currentSelection = null;
        this.isOpen = false;
        
        if (!this.container) {
            console.error('ThemeSwitcher: Container element not found');
            return;
        }
        
        if (!this.themeManager) {
            console.error('ThemeSwitcher: ThemeManager instance required');
            return;
        }
        
        this.init();
    }
    
    /**
     * Initialize the theme switcher component
     */
    init() {
        this.render();
        this.bindEvents();
        this.updateSelection();
        
        // Listen for theme changes from other sources
        this.themeManager.addObserver((event, data) => {
            if (event === 'themeChanged') {
                this.updateSelection();
            }
        });
        
        console.log('🎛️ ThemeSwitcher initialized');
    }
    
    /**
     * Render the theme switcher UI
     */
    render() {
        const { variant } = this.options;
        
        switch (variant) {
            case 'dropdown':
                this.renderDropdown();
                break;
            case 'radio':
                this.renderRadioGroup();
                break;
            case 'toggle':
            default:
                this.renderToggle();
                break;
        }
        
        this.container.classList.add('theme-switcher-initialized');
    }
    
    /**
     * Render toggle button variant
     */
    renderToggle() {
        const currentTheme = this.themeManager.getCurrentTheme();
        const persistedTheme = this.themeManager.loadPersistedTheme() || 'auto';
        
        this.container.innerHTML = `
            <button 
                class="theme-toggle-btn theme-toggle-${this.options.size}"
                type="button"
                aria-label="Toggle theme (current: ${currentTheme})"
                title="Switch between light and dark themes"
                data-theme-switcher="toggle"
            >
                <i class="theme-icon ${this.getThemeIcon(currentTheme)}" aria-hidden="true"></i>
                ${this.options.showLabels ? `<span class="theme-label">${this.getThemeLabel(currentTheme)}</span>` : ''}
            </button>
        `;
    }
    
    /**
     * Render dropdown variant
     */
    renderDropdown() {
        const currentTheme = this.themeManager.getCurrentTheme();
        const persistedTheme = this.themeManager.loadPersistedTheme() || 'auto';
        
        this.container.innerHTML = `
            <div class="theme-dropdown theme-dropdown-${this.options.size}">
                <button 
                    class="theme-dropdown-toggle"
                    type="button"
                    aria-expanded="false"
                    aria-haspopup="true"
                    aria-label="Theme selection menu"
                    data-theme-switcher="dropdown-toggle"
                >
                    <i class="theme-icon ${this.getThemeIcon(currentTheme)}" aria-hidden="true"></i>
                    ${this.options.showLabels ? `<span class="theme-label">${this.getThemeLabel(currentTheme)}</span>` : ''}
                    <i class="fas fa-chevron-down theme-dropdown-arrow" aria-hidden="true"></i>
                </button>
                <div class="theme-dropdown-menu" role="menu" aria-label="Theme options">
                    ${this.renderThemeOptions()}
                </div>
            </div>
        `;
    }
    
    /**
     * Render radio group variant
     */
    renderRadioGroup() {
        const persistedTheme = this.themeManager.loadPersistedTheme() || 'auto';
        
        this.container.innerHTML = `
            <fieldset class="theme-radio-group theme-radio-${this.options.size}">
                <legend class="sr-only">Theme selection</legend>
                ${this.renderRadioOptions(persistedTheme)}
            </fieldset>
        `;
    }
    
    /**
     * Render theme options for dropdown
     */
    renderThemeOptions() {
        const themes = [
            { value: 'light', icon: 'fas fa-sun', label: 'Light' },
            { value: 'dark', icon: 'fas fa-moon', label: 'Dark' }
        ];
        
        if (this.options.showAuto) {
            themes.push({ value: 'auto', icon: 'fas fa-adjust', label: 'Auto' });
        }
        
        const persistedTheme = this.themeManager.loadPersistedTheme() || 'auto';
        
        return themes.map(theme => `
            <button 
                class="theme-option ${persistedTheme === theme.value ? 'active' : ''}"
                type="button"
                role="menuitem"
                data-theme="${theme.value}"
                aria-label="Switch to ${theme.label.toLowerCase()} theme"
            >
                <i class="${theme.icon}" aria-hidden="true"></i>
                <span>${theme.label}</span>
                ${persistedTheme === theme.value ? '<i class="fas fa-check theme-check" aria-hidden="true"></i>' : ''}
            </button>
        `).join('');
    }
    
    /**
     * Render radio options for radio group
     */
    renderRadioOptions(selectedTheme) {
        const themes = [
            { value: 'light', icon: 'fas fa-sun', label: 'Light' },
            { value: 'dark', icon: 'fas fa-moon', label: 'Dark' }
        ];
        
        if (this.options.showAuto) {
            themes.push({ value: 'auto', icon: 'fas fa-adjust', label: 'Auto' });
        }
        
        return themes.map(theme => `
            <label class="theme-radio-option">
                <input 
                    type="radio" 
                    name="theme-selection" 
                    value="${theme.value}"
                    ${selectedTheme === theme.value ? 'checked' : ''}
                    class="theme-radio-input sr-only"
                >
                <span class="theme-radio-custom">
                    <i class="${theme.icon}" aria-hidden="true"></i>
                    ${this.options.showLabels ? `<span class="theme-radio-label">${theme.label}</span>` : ''}
                </span>
            </label>
        `).join('');
    }
    
    /**
     * Bind event listeners
     */
    bindEvents() {
        const { variant } = this.options;
        
        switch (variant) {
            case 'dropdown':
                this.bindDropdownEvents();
                break;
            case 'radio':
                this.bindRadioEvents();
                break;
            case 'toggle':
            default:
                this.bindToggleEvents();
                break;
        }
        
        // Global keyboard shortcuts
        this.bindKeyboardShortcuts();
    }
    
    /**
     * Bind toggle button events
     */
    bindToggleEvents() {
        const toggleBtn = this.container.querySelector('[data-theme-switcher="toggle"]');
        
        if (toggleBtn) {
            toggleBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleToggle();
            });
            
            toggleBtn.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.handleToggle();
                }
            });
        }
    }
    
    /**
     * Bind dropdown events
     */
    bindDropdownEvents() {
        const dropdownToggle = this.container.querySelector('[data-theme-switcher="dropdown-toggle"]');
        const dropdownMenu = this.container.querySelector('.theme-dropdown-menu');
        const options = this.container.querySelectorAll('.theme-option');
        
        if (dropdownToggle) {
            dropdownToggle.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleDropdown();
            });
            
            dropdownToggle.addEventListener('keydown', (e) => {
                this.handleDropdownKeydown(e);
            });
        }
        
        options.forEach(option => {
            option.addEventListener('click', (e) => {
                e.preventDefault();
                const theme = option.dataset.theme;
                this.selectTheme(theme);
                this.closeDropdown();
            });
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.closeDropdown();
            }
        });
    }
    
    /**
     * Bind radio group events
     */
    bindRadioEvents() {
        const radioInputs = this.container.querySelectorAll('.theme-radio-input');
        
        radioInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.selectTheme(e.target.value);
                }
            });
        });
    }
    
    /**
     * Bind global keyboard shortcuts
     */
    bindKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + Shift + T for theme toggle
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
                e.preventDefault();
                this.handleToggle();
                this.announceShortcut();
            }
        });
    }
    
    /**
     * Handle theme toggle
     */
    handleToggle() {
        this.themeManager.toggleTheme();
        this.updateSelection();
        
        // Provide haptic feedback on supported devices
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
    }
    
    /**
     * Handle theme selection
     */
    selectTheme(theme) {
        this.themeManager.setTheme(theme);
        this.updateSelection();
    }
    
    /**
     * Toggle dropdown open/closed
     */
    toggleDropdown() {
        if (this.isOpen) {
            this.closeDropdown();
        } else {
            this.openDropdown();
        }
    }
    
    /**
     * Open dropdown menu
     */
    openDropdown() {
        const dropdownToggle = this.container.querySelector('[data-theme-switcher="dropdown-toggle"]');
        const dropdownMenu = this.container.querySelector('.theme-dropdown-menu');
        
        if (dropdownToggle && dropdownMenu) {
            this.isOpen = true;
            dropdownToggle.setAttribute('aria-expanded', 'true');
            dropdownMenu.classList.add('show');
            
            // Focus first option
            const firstOption = dropdownMenu.querySelector('.theme-option');
            if (firstOption) {
                firstOption.focus();
            }
        }
    }
    
    /**
     * Close dropdown menu
     */
    closeDropdown() {
        const dropdownToggle = this.container.querySelector('[data-theme-switcher="dropdown-toggle"]');
        const dropdownMenu = this.container.querySelector('.theme-dropdown-menu');
        
        if (dropdownToggle && dropdownMenu) {
            this.isOpen = false;
            dropdownToggle.setAttribute('aria-expanded', 'false');
            dropdownMenu.classList.remove('show');
        }
    }
    
    /**
     * Handle dropdown keyboard navigation
     */
    handleDropdownKeydown(e) {
        const options = Array.from(this.container.querySelectorAll('.theme-option'));
        const currentIndex = options.findIndex(option => option === document.activeElement);
        
        switch (e.key) {
            case 'Enter':
            case ' ':
                e.preventDefault();
                if (this.isOpen) {
                    if (document.activeElement.classList.contains('theme-option')) {
                        document.activeElement.click();
                    }
                } else {
                    this.openDropdown();
                }
                break;
                
            case 'Escape':
                e.preventDefault();
                this.closeDropdown();
                this.container.querySelector('[data-theme-switcher="dropdown-toggle"]').focus();
                break;
                
            case 'ArrowDown':
                e.preventDefault();
                if (!this.isOpen) {
                    this.openDropdown();
                } else {
                    const nextIndex = (currentIndex + 1) % options.length;
                    options[nextIndex].focus();
                }
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                if (this.isOpen) {
                    const prevIndex = currentIndex <= 0 ? options.length - 1 : currentIndex - 1;
                    options[prevIndex].focus();
                }
                break;
        }
    }
    
    /**
     * Update UI to reflect current selection
     */
    updateSelection() {
        const currentTheme = this.themeManager.getCurrentTheme();
        const persistedTheme = this.themeManager.loadPersistedTheme() || 'auto';
        
        // Update toggle button
        const toggleBtn = this.container.querySelector('[data-theme-switcher="toggle"]');
        if (toggleBtn) {
            const icon = toggleBtn.querySelector('.theme-icon');
            const label = toggleBtn.querySelector('.theme-label');
            
            if (icon) {
                icon.className = `theme-icon ${this.getThemeIcon(currentTheme)}`;
            }
            
            if (label) {
                label.textContent = this.getThemeLabel(currentTheme);
            }
            
            toggleBtn.setAttribute('aria-label', `Toggle theme (current: ${currentTheme})`);
        }
        
        // Update dropdown
        const dropdownToggle = this.container.querySelector('[data-theme-switcher="dropdown-toggle"]');
        if (dropdownToggle) {
            const icon = dropdownToggle.querySelector('.theme-icon');
            const label = dropdownToggle.querySelector('.theme-label');
            
            if (icon) {
                icon.className = `theme-icon ${this.getThemeIcon(currentTheme)}`;
            }
            
            if (label) {
                label.textContent = this.getThemeLabel(currentTheme);
            }
        }
        
        // Update dropdown options
        const options = this.container.querySelectorAll('.theme-option');
        options.forEach(option => {
            const isActive = option.dataset.theme === persistedTheme;
            option.classList.toggle('active', isActive);
            
            const checkIcon = option.querySelector('.theme-check');
            if (checkIcon) {
                checkIcon.style.display = isActive ? 'inline' : 'none';
            }
        });
        
        // Update radio buttons
        const radioInputs = this.container.querySelectorAll('.theme-radio-input');
        radioInputs.forEach(input => {
            input.checked = input.value === persistedTheme;
        });
    }
    
    /**
     * Get theme icon class
     */
    getThemeIcon(theme) {
        const icons = {
            light: 'fas fa-sun',
            dark: 'fas fa-moon',
            auto: 'fas fa-adjust'
        };
        return icons[theme] || icons.dark;
    }
    
    /**
     * Get theme label
     */
    getThemeLabel(theme) {
        const labels = {
            light: 'Light',
            dark: 'Dark',
            auto: 'Auto'
        };
        return labels[theme] || labels.dark;
    }
    
    /**
     * Announce keyboard shortcut usage
     */
    announceShortcut() {
        const announcer = document.getElementById('theme-announcer') || this.createAnnouncer();
        announcer.textContent = 'Theme toggled using keyboard shortcut';
        
        setTimeout(() => {
            announcer.textContent = '';
        }, 1000);
    }
    
    /**
     * Create screen reader announcer
     */
    createAnnouncer() {
        const announcer = document.createElement('div');
        announcer.id = 'theme-switcher-announcer';
        announcer.setAttribute('aria-live', 'polite');
        announcer.setAttribute('aria-atomic', 'true');
        announcer.className = 'sr-only';
        document.body.appendChild(announcer);
        return announcer;
    }
    
    /**
     * Destroy the theme switcher
     */
    destroy() {
        if (this.container) {
            this.container.innerHTML = '';
            this.container.classList.remove('theme-switcher-initialized');
        }
    }
    
    /**
     * Update options
     */
    updateOptions(newOptions) {
        this.options = { ...this.options, ...newOptions };
        this.render();
        this.bindEvents();
        this.updateSelection();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeSwitcher;
}

// Global access
window.ThemeSwitcher = ThemeSwitcher;