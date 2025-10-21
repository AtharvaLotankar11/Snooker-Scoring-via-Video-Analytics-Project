/**
 * Brand Compliance Validator - Snooker Detection Pro
 * Validates brand guideline adherence and color usage
 * Provides automated checking and correction suggestions
 */

class BrandComplianceValidator {
    constructor(options = {}) {
        this.options = {
            approvedColors: {
                primary: '#0B405B',
                secondary: '#94D82A'
            },
            toleranceThreshold: 5, // Color difference tolerance
            enableAutoCorrection: false,
            enableDeveloperWarnings: true,
            reportingEndpoint: null,
            ...options
        };
        
        this.violations = [];
        this.corrections = [];
        this.observers = [];
        this.validationRules = new Map();
        
        this.init();
    }
    
    /**
     * Initialize brand compliance validator
     */
    init() {
        this.setupValidationRules();
        this.setupMutationObserver();
        this.validateInitialState();
        
        console.log('🛡️ Brand Compliance Validator initialized');
    }
    
    /**
     * Setup validation rules
     */
    setupValidationRules() {
        // Color usage rules
        this.validationRules.set('colorUsage', {
            name: 'Brand Color Usage',
            description: 'Only approved brand colors should be used',
            validate: (element) => this.validateColorUsage(element),
            severity: 'error'
        });
        
        // Logo usage rules
        this.validationRules.set('logoUsage', {
            name: 'Logo Usage Guidelines',
            description: 'Logos must follow brand guidelines',
            validate: (element) => this.validateLogoUsage(element),
            severity: 'warning'
        });
        
        // Typography rules
        this.validationRules.set('typography', {
            name: 'Typography Guidelines',
            description: 'Typography must follow brand standards',
            validate: (element) => this.validateTypography(element),
            severity: 'info'
        });
        
        // Spacing rules
        this.validationRules.set('spacing', {
            name: 'Spacing Guidelines',
            description: 'Spacing must follow design system',
            validate: (element) => this.validateSpacing(element),
            severity: 'info'
        });
        
        // Contrast rules
        this.validationRules.set('contrast', {
            name: 'Color Contrast',
            description: 'Text must meet WCAG AA contrast requirements',
            validate: (element) => this.validateContrast(element),
            severity: 'error'
        });
    }
    
    /**
     * Setup mutation observer to watch for DOM changes
     */
    setupMutationObserver() {
        if (typeof MutationObserver === 'undefined') return;
        
        const observer = new MutationObserver((mutations) => {
            mutations.forEach(mutation => {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            this.validateElement(node);
                        }
                    });
                }
                
                if (mutation.type === 'attributes') {
                    this.validateElement(mutation.target);
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['style', 'class']
        });
    }
    
    /**
     * Validate initial page state
     */
    validateInitialState() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.validatePage();
            });
        } else {
            this.validatePage();
        }
    }
    
    /**
     * Validate entire page
     */
    validatePage() {
        this.violations = [];
        this.corrections = [];
        
        // Validate all elements
        const elements = document.querySelectorAll('*');
        elements.forEach(element => {
            this.validateElement(element);
        });
        
        // Generate report
        this.generateReport();
        
        return {
            violations: this.violations,
            corrections: this.corrections,
            isCompliant: this.violations.length === 0
        };
    }
    
    /**
     * Validate single element
     * @param {HTMLElement} element - Element to validate
     */
    validateElement(element) {
        if (!element || element.nodeType !== Node.ELEMENT_NODE) return;
        
        // Run all validation rules
        this.validationRules.forEach((rule, ruleId) => {
            try {
                const result = rule.validate(element);
                if (result && !result.isValid) {
                    this.addViolation(element, ruleId, result);
                }
            } catch (error) {
                console.warn(`Validation rule ${ruleId} failed:`, error);
            }
        });
    }
    
    /**
     * Validate color usage
     * @param {HTMLElement} element - Element to validate
     */
    validateColorUsage(element) {
        const computedStyle = window.getComputedStyle(element);
        const violations = [];
        
        // Check background color
        const bgColor = this.parseColor(computedStyle.backgroundColor);
        if (bgColor && !this.isApprovedColor(bgColor)) {
            violations.push({
                property: 'background-color',
                value: computedStyle.backgroundColor,
                suggestion: this.suggestApprovedColor(bgColor)
            });
        }
        
        // Check text color
        const textColor = this.parseColor(computedStyle.color);
        if (textColor && !this.isApprovedColor(textColor)) {
            violations.push({
                property: 'color',
                value: computedStyle.color,
                suggestion: this.suggestApprovedColor(textColor)
            });
        }
        
        // Check border color
        const borderColor = this.parseColor(computedStyle.borderColor);
        if (borderColor && !this.isApprovedColor(borderColor)) {
            violations.push({
                property: 'border-color',
                value: computedStyle.borderColor,
                suggestion: this.suggestApprovedColor(borderColor)
            });
        }
        
        return violations.length > 0 ? {
            isValid: false,
            violations,
            message: `Element uses non-approved colors: ${violations.map(v => v.property).join(', ')}`
        } : { isValid: true };
    }
    
    /**
     * Validate logo usage
     * @param {HTMLElement} element - Element to validate
     */
    validateLogoUsage(element) {
        if (!element.matches('img[src*="logo"], [data-logo], .logo')) {
            return { isValid: true };
        }
        
        const violations = [];
        const computedStyle = window.getComputedStyle(element);
        
        // Check logo size
        const width = parseInt(computedStyle.width);
        const height = parseInt(computedStyle.height);
        
        if (width < 120 || height < 40) {
            violations.push({
                property: 'size',
                value: `${width}x${height}`,
                message: 'Logo is too small (minimum 120x40px)'
            });
        }
        
        if (width > 400 || height > 200) {
            violations.push({
                property: 'size',
                value: `${width}x${height}`,
                message: 'Logo is too large (maximum 400x200px)'
            });
        }
        
        // Check logo aspect ratio
        const aspectRatio = width / height;
        if (aspectRatio < 2.5 || aspectRatio > 4) {
            violations.push({
                property: 'aspect-ratio',
                value: aspectRatio.toFixed(2),
                message: 'Logo aspect ratio should be between 2.5:1 and 4:1'
            });
        }
        
        return violations.length > 0 ? {
            isValid: false,
            violations,
            message: `Logo usage violations: ${violations.map(v => v.property).join(', ')}`
        } : { isValid: true };
    }
    
    /**
     * Validate typography
     * @param {HTMLElement} element - Element to validate
     */
    validateTypography(element) {
        const computedStyle = window.getComputedStyle(element);
        const violations = [];
        
        // Check font family
        const fontFamily = computedStyle.fontFamily.toLowerCase();
        const approvedFonts = ['inter', 'segoe ui', 'system-ui', 'sans-serif'];
        
        if (!approvedFonts.some(font => fontFamily.includes(font))) {
            violations.push({
                property: 'font-family',
                value: computedStyle.fontFamily,
                message: 'Font family should be Inter or system fonts'
            });
        }
        
        // Check font sizes follow scale
        const fontSize = parseInt(computedStyle.fontSize);
        const approvedSizes = [12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 64];
        
        if (!approvedSizes.includes(fontSize)) {
            const closestSize = approvedSizes.reduce((prev, curr) => 
                Math.abs(curr - fontSize) < Math.abs(prev - fontSize) ? curr : prev
            );
            
            violations.push({
                property: 'font-size',
                value: `${fontSize}px`,
                suggestion: `${closestSize}px`,
                message: 'Font size should follow the design system scale'
            });
        }
        
        return violations.length > 0 ? {
            isValid: false,
            violations,
            message: `Typography violations: ${violations.map(v => v.property).join(', ')}`
        } : { isValid: true };
    }
    
    /**
     * Validate spacing
     * @param {HTMLElement} element - Element to validate
     */
    validateSpacing(element) {
        const computedStyle = window.getComputedStyle(element);
        const violations = [];
        
        // Check if spacing follows 4px grid
        const spacingProperties = ['marginTop', 'marginRight', 'marginBottom', 'marginLeft', 
                                 'paddingTop', 'paddingRight', 'paddingBottom', 'paddingLeft'];
        
        spacingProperties.forEach(prop => {
            const value = parseInt(computedStyle[prop]);
            if (value > 0 && value % 4 !== 0) {
                violations.push({
                    property: prop,
                    value: `${value}px`,
                    suggestion: `${Math.round(value / 4) * 4}px`,
                    message: 'Spacing should follow 4px grid system'
                });
            }
        });
        
        return violations.length > 0 ? {
            isValid: false,
            violations,
            message: `Spacing violations: ${violations.map(v => v.property).join(', ')}`
        } : { isValid: true };
    }
    
    /**
     * Validate color contrast
     * @param {HTMLElement} element - Element to validate
     */
    validateContrast(element) {
        const computedStyle = window.getComputedStyle(element);
        const textColor = this.parseColor(computedStyle.color);
        const bgColor = this.parseColor(computedStyle.backgroundColor);
        
        if (!textColor || !bgColor) {
            return { isValid: true };
        }
        
        const contrastRatio = this.calculateContrastRatio(textColor, bgColor);
        const minContrast = 4.5; // WCAG AA standard
        
        if (contrastRatio < minContrast) {
            return {
                isValid: false,
                violations: [{
                    property: 'contrast',
                    value: contrastRatio.toFixed(2),
                    message: `Contrast ratio ${contrastRatio.toFixed(2)}:1 is below WCAG AA standard (${minContrast}:1)`
                }]
            };
        }
        
        return { isValid: true };
    }
    
    /**
     * Check if color is approved
     * @param {Object} color - RGB color object
     * @returns {boolean} Whether color is approved
     */
    isApprovedColor(color) {
        const approvedColors = [
            this.hexToRgb(this.options.approvedColors.primary),
            this.hexToRgb(this.options.approvedColors.secondary),
            { r: 255, g: 255, b: 255 }, // White
            { r: 0, g: 0, b: 0 }, // Black
            // Neutral grays
            { r: 248, g: 250, b: 252 }, // neutral-50
            { r: 241, g: 245, b: 249 }, // neutral-100
            { r: 226, g: 232, b: 240 }, // neutral-200
            { r: 203, g: 213, b: 225 }, // neutral-300
            { r: 148, g: 163, b: 184 }, // neutral-400
            { r: 100, g: 116, b: 139 }, // neutral-500
            { r: 71, g: 85, b: 105 },   // neutral-600
            { r: 51, g: 65, b: 85 },    // neutral-700
            { r: 30, g: 41, b: 59 },    // neutral-800
            { r: 15, g: 23, b: 42 }     // neutral-900
        ];
        
        return approvedColors.some(approved => 
            this.colorDistance(color, approved) <= this.options.toleranceThreshold
        );
    }
    
    /**
     * Suggest approved color alternative
     * @param {Object} color - RGB color object
     * @returns {string} Suggested color hex
     */
    suggestApprovedColor(color) {
        const approvedColors = [
            { color: this.hexToRgb(this.options.approvedColors.primary), hex: this.options.approvedColors.primary },
            { color: this.hexToRgb(this.options.approvedColors.secondary), hex: this.options.approvedColors.secondary },
            { color: { r: 255, g: 255, b: 255 }, hex: '#ffffff' },
            { color: { r: 0, g: 0, b: 0 }, hex: '#000000' }
        ];
        
        let closestColor = approvedColors[0];
        let minDistance = this.colorDistance(color, closestColor.color);
        
        approvedColors.forEach(approved => {
            const distance = this.colorDistance(color, approved.color);
            if (distance < minDistance) {
                minDistance = distance;
                closestColor = approved;
            }
        });
        
        return closestColor.hex;
    }
    
    /**
     * Calculate color distance
     * @param {Object} color1 - First RGB color
     * @param {Object} color2 - Second RGB color
     * @returns {number} Color distance
     */
    colorDistance(color1, color2) {
        const rDiff = color1.r - color2.r;
        const gDiff = color1.g - color2.g;
        const bDiff = color1.b - color2.b;
        
        return Math.sqrt(rDiff * rDiff + gDiff * gDiff + bDiff * bDiff);
    }
    
    /**
     * Parse color string to RGB object
     * @param {string} colorStr - Color string
     * @returns {Object|null} RGB color object
     */
    parseColor(colorStr) {
        if (!colorStr || colorStr === 'transparent' || colorStr === 'rgba(0, 0, 0, 0)') {
            return null;
        }
        
        // Handle rgb/rgba
        const rgbMatch = colorStr.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
        if (rgbMatch) {
            return {
                r: parseInt(rgbMatch[1]),
                g: parseInt(rgbMatch[2]),
                b: parseInt(rgbMatch[3])
            };
        }
        
        // Handle hex
        const hexMatch = colorStr.match(/^#([a-f\d]{6})$/i);
        if (hexMatch) {
            return this.hexToRgb(colorStr);
        }
        
        return null;
    }
    
    /**
     * Convert hex to RGB
     * @param {string} hex - Hex color string
     * @returns {Object} RGB color object
     */
    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }
    
    /**
     * Calculate contrast ratio between two colors
     * @param {Object} color1 - First RGB color
     * @param {Object} color2 - Second RGB color
     * @returns {number} Contrast ratio
     */
    calculateContrastRatio(color1, color2) {
        const l1 = this.getLuminance(color1);
        const l2 = this.getLuminance(color2);
        
        const lighter = Math.max(l1, l2);
        const darker = Math.min(l1, l2);
        
        return (lighter + 0.05) / (darker + 0.05);
    }
    
    /**
     * Get relative luminance of color
     * @param {Object} color - RGB color object
     * @returns {number} Relative luminance
     */
    getLuminance(color) {
        const { r, g, b } = color;
        
        const [rs, gs, bs] = [r, g, b].map(c => {
            c = c / 255;
            return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
        });
        
        return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
    }
    
    /**
     * Add violation to list
     * @param {HTMLElement} element - Element with violation
     * @param {string} ruleId - Rule ID
     * @param {Object} result - Validation result
     */
    addViolation(element, ruleId, result) {
        const rule = this.validationRules.get(ruleId);
        
        const violation = {
            element,
            ruleId,
            ruleName: rule.name,
            severity: rule.severity,
            message: result.message,
            violations: result.violations || [],
            timestamp: Date.now(),
            selector: this.getElementSelector(element)
        };
        
        this.violations.push(violation);
        
        // Auto-correct if enabled
        if (this.options.enableAutoCorrection) {
            this.attemptAutoCorrection(violation);
        }
        
        // Developer warnings
        if (this.options.enableDeveloperWarnings && rule.severity === 'error') {
            console.warn(`🛡️ Brand Compliance Violation: ${rule.name}`, {
                element,
                message: result.message,
                violations: result.violations
            });
        }
    }
    
    /**
     * Attempt automatic correction
     * @param {Object} violation - Violation object
     */
    attemptAutoCorrection(violation) {
        if (violation.ruleId === 'colorUsage') {
            violation.violations.forEach(v => {
                if (v.suggestion) {
                    violation.element.style[v.property] = v.suggestion;
                    
                    this.corrections.push({
                        element: violation.element,
                        property: v.property,
                        oldValue: v.value,
                        newValue: v.suggestion,
                        timestamp: Date.now()
                    });
                }
            });
        }
    }
    
    /**
     * Get CSS selector for element
     * @param {HTMLElement} element - Element
     * @returns {string} CSS selector
     */
    getElementSelector(element) {
        if (element.id) {
            return `#${element.id}`;
        }
        
        if (element.className) {
            return `.${element.className.split(' ').join('.')}`;
        }
        
        return element.tagName.toLowerCase();
    }
    
    /**
     * Generate compliance report
     */
    generateReport() {
        const report = {
            timestamp: new Date().toISOString(),
            isCompliant: this.violations.length === 0,
            violationCount: this.violations.length,
            correctionCount: this.corrections.length,
            violations: this.violations.map(v => ({
                rule: v.ruleName,
                severity: v.severity,
                message: v.message,
                selector: v.selector,
                violations: v.violations
            })),
            corrections: this.corrections,
            summary: this.generateSummary()
        };
        
        // Send to reporting endpoint if configured
        if (this.options.reportingEndpoint) {
            this.sendReport(report);
        }
        
        // Notify observers
        this.notifyObservers('reportGenerated', report);
        
        return report;
    }
    
    /**
     * Generate summary statistics
     */
    generateSummary() {
        const severityCounts = this.violations.reduce((acc, v) => {
            acc[v.severity] = (acc[v.severity] || 0) + 1;
            return acc;
        }, {});
        
        const ruleCounts = this.violations.reduce((acc, v) => {
            acc[v.ruleId] = (acc[v.ruleId] || 0) + 1;
            return acc;
        }, {});
        
        return {
            severityCounts,
            ruleCounts,
            complianceScore: Math.max(0, 100 - (this.violations.length * 5))
        };
    }
    
    /**
     * Send report to endpoint
     * @param {Object} report - Compliance report
     */
    async sendReport(report) {
        try {
            await fetch(this.options.reportingEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(report)
            });
        } catch (error) {
            console.error('Failed to send compliance report:', error);
        }
    }
    
    /**
     * Add observer for compliance events
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
                console.error('Compliance observer error:', error);
            }
        });
    }
    
    /**
     * Get current violations
     * @returns {Array} Current violations
     */
    getViolations() {
        return [...this.violations];
    }
    
    /**
     * Get current corrections
     * @returns {Array} Current corrections
     */
    getCorrections() {
        return [...this.corrections];
    }
    
    /**
     * Clear all violations and corrections
     */
    clear() {
        this.violations = [];
        this.corrections = [];
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BrandComplianceValidator;
}

// Global access
window.BrandComplianceValidator = BrandComplianceValidator;