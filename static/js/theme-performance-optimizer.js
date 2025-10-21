/**
 * Theme Performance Optimizer - Snooker Detection Pro
 * Optimizes theme switching performance and memory usage
 * Provides preloading, caching, and efficient CSS variable updates
 */

class ThemePerformanceOptimizer {
    constructor(options = {}) {
        this.options = {
            enablePreloading: true,
            enableCaching: true,
            enableGPUAcceleration: true,
            enableVirtualization: false,
            maxCacheSize: 50, // Maximum cached theme states
            preloadDelay: 100, // Delay before preloading (ms)
            transitionOptimization: true,
            memoryThreshold: 50 * 1024 * 1024, // 50MB memory threshold
            ...options
        };
        
        this.cache = new Map();
        this.preloadedThemes = new Set();
        this.performanceMetrics = {
            switchTimes: [],
            memoryUsage: [],
            cacheHits: 0,
            cacheMisses: 0
        };
        
        this.observers = [];
        this.isOptimizing = false;
        
        this.init();
    }
    
    /**
     * Initialize performance optimizer
     */
    init() {
        this.setupPerformanceMonitoring();
        this.optimizeInitialLoad();
        this.setupMemoryManagement();
        this.enableGPUAcceleration();
        
        if (this.options.enablePreloading) {
            this.schedulePreloading();
        }
        
        console.log('⚡ Theme Performance Optimizer initialized');
    }
    
    /**
     * Setup performance monitoring
     */
    setupPerformanceMonitoring() {
        // Monitor theme switch performance
        if (typeof PerformanceObserver !== 'undefined') {
            const observer = new PerformanceObserver((list) => {
                list.getEntries().forEach(entry => {
                    if (entry.name.includes('theme-switch')) {
                        this.recordSwitchTime(entry.duration);
                    }
                });
            });
            
            try {
                observer.observe({ entryTypes: ['measure'] });
            } catch (error) {
                console.warn('Performance monitoring not available:', error);
            }
        }
        
        // Monitor memory usage
        this.setupMemoryMonitoring();
    }
    
    /**
     * Setup memory monitoring
     */
    setupMemoryMonitoring() {
        if (typeof performance !== 'undefined' && performance.memory) {
            setInterval(() => {
                const memoryInfo = {
                    used: performance.memory.usedJSHeapSize,
                    total: performance.memory.totalJSHeapSize,
                    limit: performance.memory.jsHeapSizeLimit,
                    timestamp: Date.now()
                };
                
                this.performanceMetrics.memoryUsage.push(memoryInfo);
                
                // Keep only last 100 measurements
                if (this.performanceMetrics.memoryUsage.length > 100) {
                    this.performanceMetrics.memoryUsage.shift();
                }
                
                // Check memory threshold
                if (memoryInfo.used > this.options.memoryThreshold) {
                    this.optimizeMemoryUsage();
                }
            }, 5000); // Check every 5 seconds
        }
    }
    
    /**
     * Optimize initial page load
     */
    optimizeInitialLoad() {
        // Preload critical CSS
        this.preloadCriticalCSS();
        
        // Optimize font loading
        this.optimizeFontLoading();
        
        // Setup efficient CSS variable system
        this.setupEfficientCSSVariables();
    }
    
    /**
     * Preload critical CSS
     */
    preloadCriticalCSS() {
        const criticalCSS = [
            '/static/css/themes/brand-colors.css',
            '/static/css/themes/light-theme.css',
            '/static/css/themes/dark-theme.css'
        ];
        
        criticalCSS.forEach(href => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.as = 'style';
            link.href = href;
            link.onload = () => {
                link.rel = 'stylesheet';
            };
            document.head.appendChild(link);
        });
    }
    
    /**
     * Optimize font loading
     */
    optimizeFontLoading() {
        // Preload Inter font
        const fontLink = document.createElement('link');
        fontLink.rel = 'preload';
        fontLink.as = 'font';
        fontLink.type = 'font/woff2';
        fontLink.href = 'https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hiA.woff2';
        fontLink.crossOrigin = 'anonymous';
        document.head.appendChild(fontLink);
    }
    
    /**
     * Setup efficient CSS variable system
     */
    setupEfficientCSSVariables() {
        // Create a style element for dynamic CSS variables
        this.dynamicStyleElement = document.createElement('style');
        this.dynamicStyleElement.id = 'theme-dynamic-variables';
        document.head.appendChild(this.dynamicStyleElement);
        
        // Batch CSS variable updates
        this.pendingVariableUpdates = new Map();
        this.variableUpdateScheduled = false;
    }
    
    /**
     * Enable GPU acceleration for theme elements
     */
    enableGPUAcceleration() {
        if (!this.options.enableGPUAcceleration) return;
        
        const accelerationCSS = `
            .theme-gpu-accelerated,
            .card-base,
            .btn-base,
            .navbar-themed,
            .theme-switcher-nav {
                transform: translateZ(0);
                -webkit-transform: translateZ(0);
                will-change: transform, opacity;
                backface-visibility: hidden;
                -webkit-backface-visibility: hidden;
            }
            
            .theme-transitioning * {
                will-change: background-color, color, border-color, box-shadow;
            }
        `;
        
        const style = document.createElement('style');
        style.textContent = accelerationCSS;
        document.head.appendChild(style);
    }
    
    /**
     * Schedule theme preloading
     */
    schedulePreloading() {
        setTimeout(() => {
            this.preloadThemes(['light', 'dark']);
        }, this.options.preloadDelay);
    }
    
    /**
     * Preload themes for faster switching
     * @param {Array} themes - Themes to preload
     */
    async preloadThemes(themes) {
        const preloadPromises = themes.map(theme => this.preloadTheme(theme));
        
        try {
            await Promise.all(preloadPromises);
            console.log('⚡ Themes preloaded successfully');
        } catch (error) {
            console.warn('Theme preloading failed:', error);
        }
    }
    
    /**
     * Preload single theme
     * @param {string} theme - Theme to preload
     */
    async preloadTheme(theme) {
        if (this.preloadedThemes.has(theme)) return;
        
        const themeData = await this.generateThemeData(theme);
        
        if (this.options.enableCaching) {
            this.cache.set(theme, themeData);
        }
        
        this.preloadedThemes.add(theme);
        
        // Preload theme-specific assets
        await this.preloadThemeAssets(theme);
    }
    
    /**
     * Generate theme data
     * @param {string} theme - Theme name
     * @returns {Object} Theme data
     */
    async generateThemeData(theme) {
        const themeData = {
            name: theme,
            variables: this.extractThemeVariables(theme),
            assets: this.getThemeAssets(theme),
            timestamp: Date.now()
        };
        
        return themeData;
    }
    
    /**
     * Extract theme CSS variables
     * @param {string} theme - Theme name
     * @returns {Object} CSS variables
     */
    extractThemeVariables(theme) {
        const testElement = document.createElement('div');
        testElement.setAttribute('data-theme', theme);
        testElement.style.position = 'absolute';
        testElement.style.visibility = 'hidden';
        document.body.appendChild(testElement);
        
        const computedStyle = getComputedStyle(testElement);
        const variables = {};
        
        // Extract CSS custom properties
        for (let i = 0; i < computedStyle.length; i++) {
            const property = computedStyle[i];
            if (property.startsWith('--')) {
                variables[property] = computedStyle.getPropertyValue(property);
            }
        }
        
        document.body.removeChild(testElement);
        return variables;
    }
    
    /**
     * Get theme-specific assets
     * @param {string} theme - Theme name
     * @returns {Array} Asset URLs
     */
    getThemeAssets(theme) {
        return [
            `/static/assets/logos/logo-${theme}.svg`,
            `/static/assets/logos/icon-${theme}.svg`
        ];
    }
    
    /**
     * Preload theme assets
     * @param {string} theme - Theme name
     */
    async preloadThemeAssets(theme) {
        const assets = this.getThemeAssets(theme);
        
        const preloadPromises = assets.map(asset => {
            return new Promise((resolve, reject) => {
                const img = new Image();
                img.onload = resolve;
                img.onerror = resolve; // Don't fail on missing assets
                img.src = asset;
            });
        });
        
        await Promise.all(preloadPromises);
    }
    
    /**
     * Optimize theme switch performance
     * @param {string} fromTheme - Current theme
     * @param {string} toTheme - Target theme
     */
    async optimizeThemeSwitch(fromTheme, toTheme) {
        if (this.isOptimizing) return;
        
        this.isOptimizing = true;
        const startTime = performance.now();
        
        try {
            // Mark performance measurement start
            performance.mark('theme-switch-start');
            
            // Use cached theme data if available
            let themeData = this.cache.get(toTheme);
            if (themeData) {
                this.performanceMetrics.cacheHits++;
            } else {
                this.performanceMetrics.cacheMisses++;
                themeData = await this.generateThemeData(toTheme);
                
                if (this.options.enableCaching) {
                    this.cacheThemeData(toTheme, themeData);
                }
            }
            
            // Apply optimized theme switch
            await this.applyOptimizedThemeSwitch(themeData);
            
            // Mark performance measurement end
            performance.mark('theme-switch-end');
            performance.measure('theme-switch', 'theme-switch-start', 'theme-switch-end');
            
            const endTime = performance.now();
            this.recordSwitchTime(endTime - startTime);
            
        } catch (error) {
            console.error('Theme switch optimization failed:', error);
        } finally {
            this.isOptimizing = false;
        }
    }
    
    /**
     * Apply optimized theme switch
     * @param {Object} themeData - Theme data
     */
    async applyOptimizedThemeSwitch(themeData) {
        // Batch CSS variable updates
        this.batchCSSVariableUpdates(themeData.variables);
        
        // Update theme attribute efficiently
        this.updateThemeAttribute(themeData.name);
        
        // Preload next likely theme
        this.preloadNextLikelyTheme(themeData.name);
    }
    
    /**
     * Batch CSS variable updates for better performance
     * @param {Object} variables - CSS variables to update
     */
    batchCSSVariableUpdates(variables) {
        Object.entries(variables).forEach(([property, value]) => {
            this.pendingVariableUpdates.set(property, value);
        });
        
        if (!this.variableUpdateScheduled) {
            this.variableUpdateScheduled = true;
            
            requestAnimationFrame(() => {
                this.flushVariableUpdates();
                this.variableUpdateScheduled = false;
            });
        }
    }
    
    /**
     * Flush pending CSS variable updates
     */
    flushVariableUpdates() {
        if (this.pendingVariableUpdates.size === 0) return;
        
        let cssText = ':root {\n';
        this.pendingVariableUpdates.forEach((value, property) => {
            cssText += `  ${property}: ${value};\n`;
        });
        cssText += '}';
        
        this.dynamicStyleElement.textContent = cssText;
        this.pendingVariableUpdates.clear();
    }
    
    /**
     * Update theme attribute efficiently
     * @param {string} theme - Theme name
     */
    updateThemeAttribute(theme) {
        // Use DocumentFragment for efficient DOM updates
        const elements = [document.documentElement, document.body];
        
        elements.forEach(element => {
            element.setAttribute('data-theme', theme);
        });
    }
    
    /**
     * Preload next likely theme
     * @param {string} currentTheme - Current theme
     */
    preloadNextLikelyTheme(currentTheme) {
        const nextTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        if (!this.preloadedThemes.has(nextTheme)) {
            setTimeout(() => {
                this.preloadTheme(nextTheme);
            }, 100);
        }
    }
    
    /**
     * Cache theme data with size management
     * @param {string} theme - Theme name
     * @param {Object} themeData - Theme data
     */
    cacheThemeData(theme, themeData) {
        // Remove oldest entries if cache is full
        if (this.cache.size >= this.options.maxCacheSize) {
            const oldestKey = this.cache.keys().next().value;
            this.cache.delete(oldestKey);
        }
        
        this.cache.set(theme, themeData);
    }
    
    /**
     * Optimize memory usage
     */
    optimizeMemoryUsage() {
        console.log('🧹 Optimizing memory usage...');
        
        // Clear old cache entries
        const now = Date.now();
        const maxAge = 5 * 60 * 1000; // 5 minutes
        
        for (const [key, data] of this.cache.entries()) {
            if (now - data.timestamp > maxAge) {
                this.cache.delete(key);
            }
        }
        
        // Clear old performance metrics
        if (this.performanceMetrics.switchTimes.length > 50) {
            this.performanceMetrics.switchTimes = this.performanceMetrics.switchTimes.slice(-25);
        }
        
        if (this.performanceMetrics.memoryUsage.length > 50) {
            this.performanceMetrics.memoryUsage = this.performanceMetrics.memoryUsage.slice(-25);
        }
        
        // Force garbage collection if available
        if (typeof window.gc === 'function') {
            window.gc();
        }
    }
    
    /**
     * Record theme switch time
     * @param {number} duration - Switch duration in ms
     */
    recordSwitchTime(duration) {
        this.performanceMetrics.switchTimes.push({
            duration,
            timestamp: Date.now()
        });
        
        // Keep only last 50 measurements
        if (this.performanceMetrics.switchTimes.length > 50) {
            this.performanceMetrics.switchTimes.shift();
        }
        
        // Notify observers
        this.notifyObservers('switchTimeRecorded', { duration });
    }
    
    /**
     * Get performance statistics
     * @returns {Object} Performance stats
     */
    getPerformanceStats() {
        const switchTimes = this.performanceMetrics.switchTimes.map(s => s.duration);
        const recentMemory = this.performanceMetrics.memoryUsage.slice(-10);
        
        return {
            averageSwitchTime: switchTimes.length > 0 
                ? switchTimes.reduce((a, b) => a + b, 0) / switchTimes.length 
                : 0,
            fastestSwitchTime: switchTimes.length > 0 ? Math.min(...switchTimes) : 0,
            slowestSwitchTime: switchTimes.length > 0 ? Math.max(...switchTimes) : 0,
            totalSwitches: switchTimes.length,
            cacheHitRate: this.performanceMetrics.cacheHits / 
                (this.performanceMetrics.cacheHits + this.performanceMetrics.cacheMisses) * 100,
            cacheSize: this.cache.size,
            preloadedThemes: Array.from(this.preloadedThemes),
            currentMemoryUsage: recentMemory.length > 0 
                ? recentMemory[recentMemory.length - 1].used 
                : 0,
            memoryTrend: this.calculateMemoryTrend(recentMemory)
        };
    }
    
    /**
     * Calculate memory usage trend
     * @param {Array} memoryData - Recent memory usage data
     * @returns {string} Trend direction
     */
    calculateMemoryTrend(memoryData) {
        if (memoryData.length < 2) return 'stable';
        
        const recent = memoryData.slice(-5);
        const older = memoryData.slice(-10, -5);
        
        if (recent.length === 0 || older.length === 0) return 'stable';
        
        const recentAvg = recent.reduce((sum, item) => sum + item.used, 0) / recent.length;
        const olderAvg = older.reduce((sum, item) => sum + item.used, 0) / older.length;
        
        const difference = (recentAvg - olderAvg) / olderAvg * 100;
        
        if (difference > 5) return 'increasing';
        if (difference < -5) return 'decreasing';
        return 'stable';
    }
    
    /**
     * Clear all caches and reset performance metrics
     */
    clearCaches() {
        this.cache.clear();
        this.preloadedThemes.clear();
        this.performanceMetrics = {
            switchTimes: [],
            memoryUsage: [],
            cacheHits: 0,
            cacheMisses: 0
        };
        
        console.log('🧹 Caches cleared and metrics reset');
    }
    
    /**
     * Add performance observer
     * @param {Function} callback - Observer callback
     */
    addObserver(callback) {
        if (typeof callback === 'function') {
            this.observers.push(callback);
        }
    }
    
    /**
     * Notify observers
     * @param {string} event - Event type
     * @param {Object} data - Event data
     */
    notifyObservers(event, data) {
        this.observers.forEach(callback => {
            try {
                callback(event, data);
            } catch (error) {
                console.error('Performance observer error:', error);
            }
        });
    }
    
    /**
     * Get debug information
     * @returns {Object} Debug info
     */
    getDebugInfo() {
        return {
            options: this.options,
            cacheSize: this.cache.size,
            preloadedThemes: Array.from(this.preloadedThemes),
            isOptimizing: this.isOptimizing,
            performanceStats: this.getPerformanceStats(),
            memoryInfo: typeof performance !== 'undefined' && performance.memory 
                ? {
                    used: performance.memory.usedJSHeapSize,
                    total: performance.memory.totalJSHeapSize,
                    limit: performance.memory.jsHeapSizeLimit
                } 
                : null
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemePerformanceOptimizer;
}

// Global access
window.ThemePerformanceOptimizer = ThemePerformanceOptimizer;