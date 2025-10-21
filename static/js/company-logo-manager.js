/**
 * Company Logo Manager - Snooker Detection Pro
 * Handles dynamic loading, animations, and interactions for company logos
 * Provides abstract and professional logo integration
 */

class CompanyLogoManager {
    constructor(options = {}) {
        this.options = {
            logoPath: '/common_logo/',
            animationDelay: 2000,
            enableAnimations: true,
            enableTooltips: true,
            loadingPlaceholder: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMTgiIHN0cm9rZT0iIzk0YTNiOCIgc3Ryb2tlLXdpZHRoPSI0IiBzdHJva2UtZGFzaGFycmF5PSI4IDQiLz4KPC9zdmc+',
            ...options
        };
        
        this.logos = new Map();
        this.loadingStates = new Map();
        this.animationTimers = new Map();
        
        this.init();
    }
    
    /**
     * Initialize the logo manager
     */
    init() {
        this.setupLogoElements();
        this.preloadLogos();
        this.setupEventListeners();
        this.startAnimations();
        
        console.log('🏢 Company Logo Manager initialized');
    }
    
    /**
     * Setup logo elements and add loading states
     */
    setupLogoElements() {
        const logoElements = document.querySelectorAll('.company-logo, .navbar-company-logo, .footer-company-logo, .powered-by-logo');
        
        logoElements.forEach(logo => {
            // Add loading class
            logo.classList.add('loading');
            
            // Store original src
            const originalSrc = logo.src;
            this.logos.set(logo, originalSrc);
            
            // Set loading placeholder
            logo.src = this.options.loadingPlaceholder;
            
            // Add error handling
            logo.addEventListener('error', () => this.handleLogoError(logo));
            logo.addEventListener('load', () => this.handleLogoLoad(logo));
        });
    }
    
    /**
     * Preload all company logos
     */
    async preloadLogos() {
        const logoFiles = [
            'primary-logo.png',
            'color-logo1.png',
            'color-logo2.png',
            'color-logo3.png'
        ];
        
        const preloadPromises = logoFiles.map(filename => {
            return new Promise((resolve, reject) => {
                const img = new Image();
                img.onload = () => resolve({ filename, success: true });
                img.onerror = () => resolve({ filename, success: false });
                img.src = this.options.logoPath + filename;
            });
        });
        
        try {
            const results = await Promise.all(preloadPromises);
            const successCount = results.filter(r => r.success).length;
            
            console.log(`📸 Preloaded ${successCount}/${logoFiles.length} company logos`);
            
            // Load actual logos after preloading
            setTimeout(() => this.loadActualLogos(), 500);
            
        } catch (error) {
            console.warn('Logo preloading failed:', error);
            this.loadActualLogos(); // Load anyway
        }
    }
    
    /**
     * Load actual logos replacing placeholders
     */
    loadActualLogos() {
        this.logos.forEach((originalSrc, logoElement) => {
            // Fade out placeholder
            logoElement.style.opacity = '0.3';
            
            setTimeout(() => {
                logoElement.src = originalSrc;
            }, 200);
        });
    }
    
    /**
     * Handle successful logo loading
     */
    handleLogoLoad(logoElement) {
        logoElement.classList.remove('loading');
        
        // Fade in effect
        logoElement.style.opacity = '0';
        logoElement.style.transition = 'opacity 0.5s ease-in-out';
        
        setTimeout(() => {
            logoElement.style.opacity = '';
        }, 100);
        
        // Add loaded class for styling
        logoElement.classList.add('loaded');
        
        // Start individual animations
        if (this.options.enableAnimations) {
            this.startLogoAnimation(logoElement);
        }
    }
    
    /**
     * Handle logo loading errors
     */
    handleLogoError(logoElement) {
        logoElement.classList.remove('loading');
        logoElement.classList.add('error');
        
        // Set fallback image or hide
        logoElement.style.opacity = '0.2';
        logoElement.alt = 'Partner Logo';
        
        console.warn('Failed to load company logo:', logoElement.src);
    }
    
    /**
     * Setup event listeners for logo interactions
     */
    setupEventListeners() {
        // Hover effects
        document.addEventListener('mouseover', (e) => {
            if (e.target.matches('.company-logo, .navbar-company-logo, .footer-company-logo, .powered-by-logo')) {
                this.handleLogoHover(e.target, true);
            }
        });
        
        document.addEventListener('mouseout', (e) => {
            if (e.target.matches('.company-logo, .navbar-company-logo, .footer-company-logo, .powered-by-logo')) {
                this.handleLogoHover(e.target, false);
            }
        });
        
        // Click analytics (optional)
        document.addEventListener('click', (e) => {
            if (e.target.matches('.company-logo, .navbar-company-logo, .footer-company-logo, .powered-by-logo')) {
                this.trackLogoClick(e.target);
            }
        });
        
        // Intersection observer for scroll animations
        this.setupScrollAnimations();
    }
    
    /**
     * Handle logo hover effects
     */
    handleLogoHover(logoElement, isHovering) {
        if (isHovering) {
            logoElement.style.transform = 'scale(1.1) rotate(2deg)';
            logoElement.style.filter = 'grayscale(0%) brightness(1.2)';
            
            // Add subtle glow effect
            if (logoElement.classList.contains('powered-by-logo')) {
                logoElement.style.boxShadow = '0 0 20px rgba(148, 216, 42, 0.3)';
            }
        } else {
            logoElement.style.transform = '';
            logoElement.style.filter = '';
            logoElement.style.boxShadow = '';
        }
    }
    
    /**
     * Track logo clicks for analytics
     */
    trackLogoClick(logoElement) {
        const logoType = this.getLogoType(logoElement);
        const logoSrc = logoElement.src;
        
        console.log('🔗 Logo clicked:', { type: logoType, src: logoSrc });
        
        // You can integrate with analytics services here
        if (typeof gtag !== 'undefined') {
            gtag('event', 'logo_click', {
                'logo_type': logoType,
                'logo_src': logoSrc
            });
        }
    }
    
    /**
     * Get logo type from element
     */
    getLogoType(logoElement) {
        if (logoElement.classList.contains('navbar-company-logo')) return 'navbar';
        if (logoElement.classList.contains('footer-company-logo')) return 'footer';
        if (logoElement.classList.contains('powered-by-logo')) return 'powered-by';
        return 'general';
    }
    
    /**
     * Start logo animations
     */
    startAnimations() {
        if (!this.options.enableAnimations) return;
        
        const animatedLogos = document.querySelectorAll('.animate-float, .animate-glow');
        
        animatedLogos.forEach((logo, index) => {
            // Stagger animation start times
            setTimeout(() => {
                logo.style.animationDelay = `${index * 0.5}s`;
            }, index * 200);
        });
    }
    
    /**
     * Start individual logo animation
     */
    startLogoAnimation(logoElement) {
        // Random subtle animation
        const animations = ['animate-float', 'animate-glow'];
        const randomAnimation = animations[Math.floor(Math.random() * animations.length)];
        
        // Add animation with delay
        setTimeout(() => {
            logoElement.classList.add(randomAnimation);
        }, Math.random() * 3000);
    }
    
    /**
     * Setup scroll-based animations
     */
    setupScrollAnimations() {
        if (typeof IntersectionObserver === 'undefined') return;
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const logo = entry.target;
                    logo.classList.add('in-view');
                    
                    // Trigger entrance animation
                    setTimeout(() => {
                        logo.style.transform = 'translateY(0) scale(1)';
                        logo.style.opacity = '1';
                    }, 100);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '50px'
        });
        
        // Observe powered-by logos
        document.querySelectorAll('.powered-by-logo').forEach(logo => {
            // Set initial state
            logo.style.transform = 'translateY(20px) scale(0.9)';
            logo.style.opacity = '0.5';
            logo.style.transition = 'all 0.6s ease-out';
            
            observer.observe(logo);
        });
    }
    
    /**
     * Update logo theme based on current theme
     */
    updateLogoTheme(theme) {
        const logos = document.querySelectorAll('.company-logo, .navbar-company-logo, .footer-company-logo, .powered-by-logo');
        
        logos.forEach(logo => {
            if (theme === 'dark') {
                logo.style.filter = 'grayscale(30%) brightness(1.2) contrast(0.9)';
            } else {
                logo.style.filter = 'grayscale(20%) brightness(0.9) contrast(1.1)';
            }
        });
        
        console.log(`🎨 Updated logo theme to: ${theme}`);
    }
    
    /**
     * Add new logo dynamically
     */
    addLogo(container, logoSrc, options = {}) {
        const logo = document.createElement('img');
        logo.src = logoSrc;
        logo.alt = options.alt || 'Partner Logo';
        logo.className = `company-logo ${options.className || ''}`;
        
        if (options.tooltip) {
            logo.classList.add('company-logo-tooltip');
            logo.setAttribute('data-company', options.tooltip);
        }
        
        // Add loading state
        logo.classList.add('loading');
        logo.addEventListener('load', () => this.handleLogoLoad(logo));
        logo.addEventListener('error', () => this.handleLogoError(logo));
        
        container.appendChild(logo);
        
        return logo;
    }
    
    /**
     * Remove logo
     */
    removeLogo(logoElement) {
        // Fade out animation
        logoElement.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
        logoElement.style.opacity = '0';
        logoElement.style.transform = 'scale(0.8)';
        
        setTimeout(() => {
            if (logoElement.parentNode) {
                logoElement.parentNode.removeChild(logoElement);
            }
        }, 300);
    }
    
    /**
     * Get logo statistics
     */
    getStats() {
        const totalLogos = document.querySelectorAll('.company-logo, .navbar-company-logo, .footer-company-logo, .powered-by-logo').length;
        const loadedLogos = document.querySelectorAll('.company-logo.loaded, .navbar-company-logo.loaded, .footer-company-logo.loaded, .powered-by-logo.loaded').length;
        const errorLogos = document.querySelectorAll('.company-logo.error, .navbar-company-logo.error, .footer-company-logo.error, .powered-by-logo.error').length;
        
        return {
            total: totalLogos,
            loaded: loadedLogos,
            errors: errorLogos,
            loadRate: totalLogos > 0 ? (loadedLogos / totalLogos * 100).toFixed(1) : 0
        };
    }
    
    /**
     * Cleanup and destroy
     */
    destroy() {
        // Clear timers
        this.animationTimers.forEach(timer => clearTimeout(timer));
        this.animationTimers.clear();
        
        // Remove event listeners
        // (In a real implementation, you'd store references to remove them)
        
        console.log('🏢 Company Logo Manager destroyed');
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.companyLogoManager = new CompanyLogoManager();
    
    // Connect to theme manager if available
    if (window.themeManager) {
        window.themeManager.addObserver((event, data) => {
            if (event === 'themeChanged') {
                window.companyLogoManager.updateLogoTheme(data.to);
            }
        });
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CompanyLogoManager;
}

// Global access
window.CompanyLogoManager = CompanyLogoManager;