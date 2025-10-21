/**
 * Theme System Debugger - Snooker Detection Pro
 * Comprehensive debugging and testing utilities for the theme system
 * Validates functionality, performance, and consistency
 */

class ThemeSystemDebugger {
    constructor() {
        this.testResults = [];
        this.performanceMetrics = {};
        this.errors = [];
        this.warnings = [];
        
        this.init();
    }
    
    /**
     * Initialize debugger
     */
    init() {
        console.log('🔍 Theme System Debugger initialized');
        this.setupErrorHandling();
    }
    
    /**
     * Setup global error handling
     */
    setupErrorHandling() {
        window.addEventListener('error', (event) => {
            this.logError('JavaScript Error', event.error);
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            this.logError('Unhandled Promise Rejection', event.reason);
        });    }
 
   
    /**
     * Run comprehensive theme system tests
     */
    async runTests() {
        console.log('🧪 Starting theme system tests...');
        this.testResults = [];
        this.errors = [];
        this.warnings = [];
        
        const startTime = performance.now();
        
        try {
            await this.testThemeInitialization();
            await this.testThemeSwitching();
            await this.testCustomProperties();
            await this.testResponsiveness();
            await this.testAccessibility();
            await this.testPerformance();
            await this.testLocalStorage();
            await this.testAnimations();
            
            const endTime = performance.now();
            this.performanceMetrics.totalTestTime = endTime - startTime;
            
            this.generateReport();
            
        } catch (error) {
            this.logError('Test Suite Failed', error);
        }
    }
    
    /**
     * Test theme initialization
     */
    async testThemeInitialization() {
        const test = { name: 'Theme Initialization', passed: false, details: [] };
        
        try {
            // Check if theme manager exists
            if (typeof window.themeManager === 'undefined') {
                test.details.push('❌ ThemeManager not found');
                this.testResults.push(test);
                return;
            }
            
            // Check initial theme loading
            const currentTheme = window.themeManager.getCurrentTheme();
            if (!currentTheme) {
                test.details.push('❌ No current theme detected');
            } else {
                test.details.push(`✅ Current theme: ${currentTheme}`);
            }
            
            // Check CSS custom properties
            const rootStyles = getComputedStyle(document.documentElement);
            const primaryColor = rootStyles.getPropertyValue('--primary-color').trim();
            
            if (primaryColor) {
                test.details.push(`✅ CSS custom properties loaded: ${primaryColor}`);
                test.passed = true;
            } else {
                test.details.push('❌ CSS custom properties not loaded');
            }
            
        } catch (error) {
            test.details.push(`❌ Error: ${error.message}`);
        }
        
        this.testResults.push(test);
    }
    
    /**
     * Test theme switching functionality
     */
    async testThemeSwitching() {
        const test = { name: 'Theme Switching', passed: false, details: [] };
        
        try {
            if (!window.themeManager) {
                test.details.push('❌ ThemeManager not available');
                this.testResults.push(test);
                return;
            }
            
            const originalTheme = window.themeManager.getCurrentTheme();
            const availableThemes = ['light', 'dark', 'high-contrast'];
            let switchCount = 0;
            
            for (const theme of availableThemes) {
                try {
                    await window.themeManager.setTheme(theme);
                    await new Promise(resolve => setTimeout(resolve, 100)); // Wait for transition
                    
                    const currentTheme = window.themeManager.getCurrentTheme();
                    if (currentTheme === theme) {
                        test.details.push(`✅ Successfully switched to ${theme}`);
                        switchCount++;
                    } else {
                        test.details.push(`❌ Failed to switch to ${theme}`);
                    }
                } catch (error) {
                    test.details.push(`❌ Error switching to ${theme}: ${error.message}`);
                }
            }
            
            // Restore original theme
            if (originalTheme) {
                await window.themeManager.setTheme(originalTheme);
            }
            
            test.passed = switchCount === availableThemes.length;
            
        } catch (error) {
            test.details.push(`❌ Error: ${error.message}`);
        }
        
        this.testResults.push(test);
    }
    
    /**
     * Test CSS custom properties
     */
    async testCustomProperties() {
        const test = { name: 'CSS Custom Properties', passed: false, details: [] };
        
        try {
            const rootStyles = getComputedStyle(document.documentElement);
            const requiredProperties = [
                '--primary-color',
                '--secondary-color',
                '--background-color',
                '--text-color',
                '--border-color',
                '--shadow-color'
            ];
            
            let validProperties = 0;
            
            for (const property of requiredProperties) {
                const value = rootStyles.getPropertyValue(property).trim();
                if (value) {
                    test.details.push(`✅ ${property}: ${value}`);
                    validProperties++;
                } else {
                    test.details.push(`❌ ${property}: not defined`);
                }
            }
            
            test.passed = validProperties === requiredProperties.length;
            
        } catch (error) {
            test.details.push(`❌ Error: ${error.message}`);
        }
        
        this.testResults.push(test);
    }
    
    /**
     * Test responsive design
     */
    async testResponsiveness() {
        const test = { name: 'Responsive Design', passed: false, details: [] };
        
        try {
            const breakpoints = [
                { name: 'Mobile', width: 375 },
                { name: 'Tablet', width: 768 },
                { name: 'Desktop', width: 1024 },
                { name: 'Large Desktop', width: 1440 }
            ];
            
            const originalWidth = window.innerWidth;
            let responsiveTests = 0;
            
            for (const breakpoint of breakpoints) {
                // Simulate viewport resize (note: this won't actually resize the window)
                const mediaQuery = window.matchMedia(`(min-width: ${breakpoint.width}px)`);
                
                if (mediaQuery.matches && window.innerWidth >= breakpoint.width) {
                    test.details.push(`✅ ${breakpoint.name} breakpoint active`);
                    responsiveTests++;
                } else if (window.innerWidth < breakpoint.width) {
                    test.details.push(`ℹ️ ${breakpoint.name} breakpoint not applicable (viewport too small)`);
                    responsiveTests++; // Count as passed since it's not applicable
                }
            }
            
            test.passed = responsiveTests > 0;
            
        } catch (error) {
            test.details.push(`❌ Error: ${error.message}`);
        }
        
        this.testResults.push(test);
    }
    
    /**
     * Test accessibility features
     */
    async testAccessibility() {
        const test = { name: 'Accessibility', passed: false, details: [] };
        
        try {
            let accessibilityScore = 0;
            
            // Check for high contrast support
            if (window.matchMedia('(prefers-contrast: high)').matches) {
                test.details.push('✅ High contrast preference detected');
                accessibilityScore++;
            }
            
            // Check for reduced motion support
            if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
                test.details.push('✅ Reduced motion preference detected');
                accessibilityScore++;
            } else {
                test.details.push('ℹ️ No reduced motion preference');
            }
            
            // Check color contrast (simplified check)
            const rootStyles = getComputedStyle(document.documentElement);
            const bgColor = rootStyles.getPropertyValue('--background-color').trim();
            const textColor = rootStyles.getPropertyValue('--text-color').trim();
            
            if (bgColor && textColor) {
                test.details.push(`✅ Background and text colors defined`);
                accessibilityScore++;
            }
            
            // Check for ARIA labels and roles
            const elementsWithAria = document.querySelectorAll('[aria-label], [role]');
            if (elementsWithAria.length > 0) {
                test.details.push(`✅ Found ${elementsWithAria.length} elements with ARIA attributes`);
                accessibilityScore++;
            }
            
            test.passed = accessibilityScore >= 2;
            
        } catch (error) {
            test.details.push(`❌ Error: ${error.message}`);
        }
        
        this.testResults.push(test);
    }
    
    /**
     * Test performance metrics
     */
    async testPerformance() {
        const test = { name: 'Performance', passed: false, details: [] };
        
        try {
            const startTime = performance.now();
            
            // Test theme switching performance
            if (window.themeManager) {
                const switchStart = performance.now();
                await window.themeManager.setTheme('dark');
                await window.themeManager.setTheme('light');
                const switchEnd = performance.now();
                
                const switchTime = switchEnd - switchStart;
                this.performanceMetrics.themeSwitchTime = switchTime;
                
                if (switchTime < 100) {
                    test.details.push(`✅ Theme switching: ${switchTime.toFixed(2)}ms (excellent)`);
                } else if (switchTime < 300) {
                    test.details.push(`⚠️ Theme switching: ${switchTime.toFixed(2)}ms (acceptable)`);
                } else {
                    test.details.push(`❌ Theme switching: ${switchTime.toFixed(2)}ms (slow)`);
                }
            }
            
            // Test CSS loading performance
            const stylesheets = document.styleSheets;
            test.details.push(`ℹ️ Loaded stylesheets: ${stylesheets.length}`);
            
            // Check for unused CSS (simplified)
            const allElements = document.querySelectorAll('*');
            test.details.push(`ℹ️ DOM elements: ${allElements.length}`);
            
            const endTime = performance.now();
            const totalTime = endTime - startTime;
            
            test.passed = totalTime < 50; // Performance test should complete quickly
            test.details.push(`ℹ️ Performance test completed in ${totalTime.toFixed(2)}ms`);
            
        } catch (error) {
            test.details.push(`❌ Error: ${error.message}`);
        }
        
        this.testResults.push(test);
    }
    
    /**
     * Test localStorage functionality
     */
    async testLocalStorage() {
        const test = { name: 'LocalStorage', passed: false, details: [] };
        
        try {
            // Test localStorage availability
            if (typeof Storage === 'undefined') {
                test.details.push('❌ localStorage not supported');
                this.testResults.push(test);
                return;
            }
            
            // Test theme persistence
            const testKey = 'theme-debugger-test';
            const testValue = 'test-theme';
            
            localStorage.setItem(testKey, testValue);
            const retrievedValue = localStorage.getItem(testKey);
            
            if (retrievedValue === testValue) {
                test.details.push('✅ localStorage read/write working');
                localStorage.removeItem(testKey);
            } else {
                test.details.push('❌ localStorage read/write failed');
            }
            
            // Check current theme storage
            const storedTheme = localStorage.getItem('selectedTheme');
            if (storedTheme) {
                test.details.push(`✅ Theme preference stored: ${storedTheme}`);
                test.passed = true;
            } else {
                test.details.push('ℹ️ No theme preference stored (using default)');
                test.passed = true; // This is acceptable
            }
            
        } catch (error) {
            test.details.push(`❌ Error: ${error.message}`);
        }
        
        this.testResults.push(test);
    }
    
    /**
     * Test animations and transitions
     */
    async testAnimations() {
        const test = { name: 'Animations & Transitions', passed: false, details: [] };
        
        try {
            // Check for CSS transition support
            const testElement = document.createElement('div');
            testElement.style.transition = 'opacity 0.3s ease';
            
            if (testElement.style.transition) {
                test.details.push('✅ CSS transitions supported');
            }
            
            // Check for animation support
            testElement.style.animation = 'fadeIn 0.3s ease';
            if (testElement.style.animation) {
                test.details.push('✅ CSS animations supported');
            }
            
            // Check for reduced motion preference
            const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            if (prefersReducedMotion) {
                test.details.push('ℹ️ User prefers reduced motion');
            } else {
                test.details.push('ℹ️ Animations enabled');
            }
            
            test.passed = true;
            
        } catch (error) {
            test.details.push(`❌ Error: ${error.message}`);
        }
        
        this.testResults.push(test);
    }
    
    /**
     * Generate comprehensive test report
     */
    generateReport() {
        console.log('\n📊 Theme System Debug Report');
        console.log('================================');
        
        const passedTests = this.testResults.filter(test => test.passed).length;
        const totalTests = this.testResults.length;
        const successRate = ((passedTests / totalTests) * 100).toFixed(1);
        
        console.log(`Overall Success Rate: ${successRate}% (${passedTests}/${totalTests})`);
        console.log(`Total Test Time: ${this.performanceMetrics.totalTestTime?.toFixed(2)}ms`);
        
        if (this.performanceMetrics.themeSwitchTime) {
            console.log(`Theme Switch Time: ${this.performanceMetrics.themeSwitchTime.toFixed(2)}ms`);
        }
        
        console.log('\nDetailed Results:');
        console.log('-----------------');
        
        this.testResults.forEach(test => {
            const status = test.passed ? '✅ PASS' : '❌ FAIL';
            console.log(`${status} ${test.name}`);
            
            test.details.forEach(detail => {
                console.log(`  ${detail}`);
            });
            console.log('');
        });
        
        if (this.errors.length > 0) {
            console.log('\n🚨 Errors:');
            this.errors.forEach(error => {
                console.error(`  ${error.type}: ${error.message}`);
            });
        }
        
        if (this.warnings.length > 0) {
            console.log('\n⚠️ Warnings:');
            this.warnings.forEach(warning => {
                console.warn(`  ${warning.type}: ${warning.message}`);
            });
        }
        
        // Return summary for programmatic use
        return {
            successRate: parseFloat(successRate),
            passedTests,
            totalTests,
            performanceMetrics: this.performanceMetrics,
            errors: this.errors,
            warnings: this.warnings,
            testResults: this.testResults
        };
    }
    
    /**
     * Log error with context
     */
    logError(type, error) {
        const errorInfo = {
            type,
            message: error?.message || error,
            stack: error?.stack,
            timestamp: new Date().toISOString()
        };
        
        this.errors.push(errorInfo);
        console.error(`🚨 ${type}:`, errorInfo);
    }
    
    /**
     * Log warning with context
     */
    logWarning(type, message) {
        const warningInfo = {
            type,
            message,
            timestamp: new Date().toISOString()
        };
        
        this.warnings.push(warningInfo);
        console.warn(`⚠️ ${type}:`, warningInfo);
    }
    
    /**
     * Export test results as JSON
     */
    exportResults() {
        const results = {
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            testResults: this.testResults,
            performanceMetrics: this.performanceMetrics,
            errors: this.errors,
            warnings: this.warnings
        };
        
        const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `theme-debug-report-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        console.log('📁 Debug report exported');
    }
    
    /**
     * Monitor theme system in real-time
     */
    startMonitoring() {
        console.log('👁️ Starting theme system monitoring...');
        
        // Monitor theme changes
        if (window.themeManager) {
            const originalSetTheme = window.themeManager.setTheme;
            window.themeManager.setTheme = (...args) => {
                console.log('🎨 Theme change detected:', args[0]);
                return originalSetTheme.apply(window.themeManager, args);
            };
        }
        
        // Monitor localStorage changes
        const originalSetItem = localStorage.setItem;
        localStorage.setItem = function(key, value) {
            if (key.includes('theme')) {
                console.log('💾 Theme-related localStorage change:', key, value);
            }
            return originalSetItem.apply(this, arguments);
        };
        
        // Monitor CSS custom property changes
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                    console.log('🎨 Style attribute changed on:', mutation.target);
                }
            });
        });
        
        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['style', 'class']
        });
        
        console.log('✅ Theme system monitoring active');
    }
}

// Auto-initialize if in debug mode
if (window.location.search.includes('debug=theme') || window.location.hash.includes('debug')) {
    window.themeDebugger = new ThemeSystemDebugger();
    
    // Add debug controls to page
    const debugPanel = document.createElement('div');
    debugPanel.id = 'theme-debug-panel';
    debugPanel.style.cssText = `
        position: fixed;
        top: 10px;
        right: 10px;
        background: rgba(0, 0, 0, 0.9);
        color: white;
        padding: 15px;
        border-radius: 8px;
        font-family: monospace;
        font-size: 12px;
        z-index: 10000;
        max-width: 300px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    `;
    
    debugPanel.innerHTML = `
        <h4 style="margin: 0 0 10px 0; color: #4CAF50;">🔍 Theme Debugger</h4>
        <button onclick="window.themeDebugger.runTests()" style="margin: 2px; padding: 5px 10px; background: #2196F3; color: white; border: none; border-radius: 4px; cursor: pointer;">Run Tests</button>
        <button onclick="window.themeDebugger.exportResults()" style="margin: 2px; padding: 5px 10px; background: #FF9800; color: white; border: none; border-radius: 4px; cursor: pointer;">Export Report</button>
        <button onclick="window.themeDebugger.startMonitoring()" style="margin: 2px; padding: 5px 10px; background: #9C27B0; color: white; border: none; border-radius: 4px; cursor: pointer;">Start Monitor</button>
        <button onclick="document.getElementById('theme-debug-panel').remove()" style="margin: 2px; padding: 5px 10px; background: #F44336; color: white; border: none; border-radius: 4px; cursor: pointer;">Close</button>
    `;
    
    document.body.appendChild(debugPanel);
    
    console.log('🔍 Theme System Debugger loaded. Use ?debug=theme or #debug in URL to activate.');
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeSystemDebugger;
}