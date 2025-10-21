/**
 * Theme Persistence Manager - Snooker Detection Pro
 * Handles theme preference storage, loading, and error recovery
 * Provides fallback mechanisms and data validation
 */

class ThemePersistence {
    constructor(options = {}) {
        this.options = {
            storageKey: 'snooker-theme-preference',
            fallbackTheme: 'dark',
            maxRetries: 3,
            retryDelay: 1000,
            enableCompression: false,
            enableEncryption: false,
            ...options
        };
        
        this.retryCount = 0;
        this.isStorageAvailable = this.checkStorageAvailability();
        this.fallbackStorage = new Map(); // In-memory fallback
        
        this.init();
    }
    
    /**
     * Initialize persistence manager
     */
    init() {
        this.validateStoredData();
        this.setupStorageEventListener();
        
        console.log('💾 ThemePersistence initialized:', {
            storageAvailable: this.isStorageAvailable,
            currentPreference: this.load()
        });
    }
    
    /**
     * Save theme preference with error handling and retries
     * @param {string} theme - Theme preference to save
     * @param {Object} metadata - Additional metadata to store
     * @returns {Promise<boolean>} Success status
     */
    async save(theme, metadata = {}) {
        if (!this.isValidTheme(theme)) {
            console.warn(`Invalid theme preference: ${theme}`);
            return false;
        }
        
        const data = {
            theme,
            timestamp: Date.now(),
            version: '1.0',
            metadata: {
                userAgent: navigator.userAgent,
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight
                },
                systemPreference: this.detectSystemPreference(),
                ...metadata
            }
        };
        
        return this.saveWithRetry(data);
    }
    
    /**
     * Load theme preference with validation and fallback
     * @returns {string|null} Loaded theme preference or null
     */
    load() {
        try {
            const data = this.loadRaw();
            
            if (!data) {
                return null;
            }
            
            // Validate loaded data
            if (!this.validateData(data)) {
                console.warn('Invalid theme data found, clearing storage');
                this.clear();
                return null;
            }
            
            // Check if data is expired (optional)
            if (this.isDataExpired(data)) {
                console.info('Theme preference expired, clearing storage');
                this.clear();
                return null;
            }
            
            return data.theme;
            
        } catch (error) {
            console.error('Failed to load theme preference:', error);
            return this.loadFromFallback();
        }
    }
    
    /**
     * Get full theme data including metadata
     * @returns {Object|null} Complete theme data or null
     */
    loadFull() {
        try {
            const data = this.loadRaw();
            return this.validateData(data) ? data : null;
        } catch (error) {
            console.error('Failed to load full theme data:', error);
            return null;
        }
    }
    
    /**
     * Clear stored theme preference
     * @returns {boolean} Success status
     */
    clear() {
        try {
            if (this.isStorageAvailable) {
                localStorage.removeItem(this.options.storageKey);
            }
            
            this.fallbackStorage.delete(this.options.storageKey);
            
            console.log('🗑️ Theme preference cleared');
            return true;
            
        } catch (error) {
            console.error('Failed to clear theme preference:', error);
            return false;
        }
    }
    
    /**
     * Get storage statistics and health info
     * @returns {Object} Storage information
     */
    getStorageInfo() {
        const info = {
            isAvailable: this.isStorageAvailable,
            hasData: !!this.load(),
            storageType: this.isStorageAvailable ? 'localStorage' : 'memory',
            dataSize: 0,
            lastModified: null,
            isValid: false
        };
        
        try {
            const data = this.loadFull();
            if (data) {
                info.dataSize = JSON.stringify(data).length;
                info.lastModified = new Date(data.timestamp);
                info.isValid = this.validateData(data);
            }
        } catch (error) {
            console.error('Error getting storage info:', error);
        }
        
        return info;
    }
    
    /**
     * Migrate data from old storage format
     * @param {string} oldKey - Old storage key to migrate from
     * @returns {boolean} Migration success status
     */
    migrate(oldKey) {
        try {
            if (!this.isStorageAvailable) {
                return false;
            }
            
            const oldData = localStorage.getItem(oldKey);
            if (!oldData) {
                return false;
            }
            
            // Try to parse old data
            let theme;
            try {
                const parsed = JSON.parse(oldData);
                theme = parsed.theme || parsed;
            } catch {
                // Assume it's a plain string
                theme = oldData;
            }
            
            if (this.isValidTheme(theme)) {
                this.save(theme, { migrated: true, oldKey });
                localStorage.removeItem(oldKey);
                
                console.log(`🔄 Migrated theme preference from ${oldKey}`);
                return true;
            }
            
        } catch (error) {
            console.error('Migration failed:', error);
        }
        
        return false;
    }
    
    /**
     * Export theme preferences for backup
     * @returns {string} Serialized theme data
     */
    export() {
        const data = this.loadFull();
        if (!data) {
            return null;
        }
        
        const exportData = {
            ...data,
            exportedAt: Date.now(),
            version: '1.0'
        };
        
        return JSON.stringify(exportData, null, 2);
    }
    
    /**
     * Import theme preferences from backup
     * @param {string} serializedData - Serialized theme data
     * @returns {boolean} Import success status
     */
    import(serializedData) {
        try {
            const data = JSON.parse(serializedData);
            
            if (!this.validateData(data)) {
                console.error('Invalid import data');
                return false;
            }
            
            return this.save(data.theme, {
                ...data.metadata,
                imported: true,
                importedAt: Date.now()
            });
            
        } catch (error) {
            console.error('Import failed:', error);
            return false;
        }
    }
    
    // Private methods
    
    /**
     * Save data with retry mechanism
     * @param {Object} data - Data to save
     * @returns {Promise<boolean>} Success status
     */
    async saveWithRetry(data) {
        for (let attempt = 0; attempt < this.options.maxRetries; attempt++) {
            try {
                const success = await this.saveData(data);
                if (success) {
                    this.retryCount = 0;
                    return true;
                }
            } catch (error) {
                console.warn(`Save attempt ${attempt + 1} failed:`, error);
            }
            
            if (attempt < this.options.maxRetries - 1) {
                await this.delay(this.options.retryDelay * (attempt + 1));
            }
        }
        
        console.error('All save attempts failed, using fallback storage');
        return this.saveToFallback(data);
    }
    
    /**
     * Save data to storage
     * @param {Object} data - Data to save
     * @returns {boolean} Success status
     */
    saveData(data) {
        const serialized = JSON.stringify(data);
        
        if (this.isStorageAvailable) {
            try {
                localStorage.setItem(this.options.storageKey, serialized);
                
                // Verify the save was successful
                const verification = localStorage.getItem(this.options.storageKey);
                if (verification !== serialized) {
                    throw new Error('Storage verification failed');
                }
                
                return true;
            } catch (error) {
                if (error.name === 'QuotaExceededError') {
                    console.warn('Storage quota exceeded, attempting cleanup');
                    this.cleanupStorage();
                    
                    // Retry once after cleanup
                    try {
                        localStorage.setItem(this.options.storageKey, serialized);
                        return true;
                    } catch (retryError) {
                        console.error('Save failed even after cleanup:', retryError);
                    }
                }
                throw error;
            }
        }
        
        return this.saveToFallback(data);
    }
    
    /**
     * Load raw data from storage
     * @returns {Object|null} Raw data or null
     */
    loadRaw() {
        if (this.isStorageAvailable) {
            const stored = localStorage.getItem(this.options.storageKey);
            if (stored) {
                return JSON.parse(stored);
            }
        }
        
        return this.loadFromFallback();
    }
    
    /**
     * Save to fallback memory storage
     * @param {Object} data - Data to save
     * @returns {boolean} Success status
     */
    saveToFallback(data) {
        try {
            this.fallbackStorage.set(this.options.storageKey, data);
            console.warn('Using fallback memory storage for theme preference');
            return true;
        } catch (error) {
            console.error('Fallback storage failed:', error);
            return false;
        }
    }
    
    /**
     * Load from fallback memory storage
     * @returns {Object|null} Data or null
     */
    loadFromFallback() {
        return this.fallbackStorage.get(this.options.storageKey) || null;
    }
    
    /**
     * Check if localStorage is available
     * @returns {boolean} Storage availability
     */
    checkStorageAvailability() {
        try {
            const testKey = '__theme_storage_test__';
            localStorage.setItem(testKey, 'test');
            localStorage.removeItem(testKey);
            return true;
        } catch {
            return false;
        }
    }
    
    /**
     * Validate theme data structure
     * @param {Object} data - Data to validate
     * @returns {boolean} Validation result
     */
    validateData(data) {
        if (!data || typeof data !== 'object') {
            return false;
        }
        
        // Required fields
        if (!data.theme || !data.timestamp || !data.version) {
            return false;
        }
        
        // Validate theme value
        if (!this.isValidTheme(data.theme)) {
            return false;
        }
        
        // Validate timestamp
        if (typeof data.timestamp !== 'number' || data.timestamp <= 0) {
            return false;
        }
        
        return true;
    }
    
    /**
     * Check if theme value is valid
     * @param {string} theme - Theme to validate
     * @returns {boolean} Validation result
     */
    isValidTheme(theme) {
        const validThemes = ['light', 'dark', 'auto'];
        return typeof theme === 'string' && validThemes.includes(theme);
    }
    
    /**
     * Check if data has expired
     * @param {Object} data - Data to check
     * @returns {boolean} Expiration status
     */
    isDataExpired(data) {
        // For now, theme preferences don't expire
        // This could be implemented for security or cleanup purposes
        return false;
    }
    
    /**
     * Detect system color scheme preference
     * @returns {string} System preference
     */
    detectSystemPreference() {
        if (typeof window === 'undefined' || !window.matchMedia) {
            return 'dark';
        }
        
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    
    /**
     * Validate stored data and clean up if necessary
     */
    validateStoredData() {
        const data = this.loadRaw();
        if (data && !this.validateData(data)) {
            console.warn('Found invalid stored theme data, cleaning up');
            this.clear();
        }
    }
    
    /**
     * Setup storage event listener for cross-tab synchronization
     */
    setupStorageEventListener() {
        if (typeof window === 'undefined') {
            return;
        }
        
        window.addEventListener('storage', (e) => {
            if (e.key === this.options.storageKey) {
                console.log('🔄 Theme preference changed in another tab');
                
                // Notify about external change
                const event = new CustomEvent('themePreferenceChanged', {
                    detail: {
                        oldValue: e.oldValue,
                        newValue: e.newValue,
                        external: true
                    }
                });
                
                window.dispatchEvent(event);
            }
        });
    }
    
    /**
     * Clean up storage to free space
     */
    cleanupStorage() {
        if (!this.isStorageAvailable) {
            return;
        }
        
        try {
            // Remove old or invalid theme-related keys
            const keysToCheck = [];
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                if (key && key.includes('theme') && key !== this.options.storageKey) {
                    keysToCheck.push(key);
                }
            }
            
            keysToCheck.forEach(key => {
                try {
                    const data = JSON.parse(localStorage.getItem(key));
                    if (!this.validateData(data)) {
                        localStorage.removeItem(key);
                        console.log(`Cleaned up invalid theme data: ${key}`);
                    }
                } catch {
                    // If it's not valid JSON, it might be old format
                    localStorage.removeItem(key);
                    console.log(`Cleaned up old theme data: ${key}`);
                }
            });
            
        } catch (error) {
            console.error('Storage cleanup failed:', error);
        }
    }
    
    /**
     * Delay utility for retries
     * @param {number} ms - Milliseconds to delay
     * @returns {Promise} Delay promise
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemePersistence;
}

// Global access
window.ThemePersistence = ThemePersistence;