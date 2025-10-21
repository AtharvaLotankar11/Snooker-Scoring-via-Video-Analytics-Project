/**
 * Industry Standard Enhancements - Snooker Detection Pro
 * Comprehensive JavaScript enhancements for professional user experience
 * Includes performance optimizations, accessibility improvements, and modern UX patterns
 */

(function() {
    'use strict';

    // ===== PERFORMANCE OPTIMIZATIONS =====
    
    // Debounce function for performance
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Throttle function for scroll events
    function throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // ===== ENHANCED NAVIGATION =====
    
    class NavigationEnhancer {
        constructor() {
            this.navbar = document.getElementById('mainNavbar');
            this.lastScrollTop = 0;
            this.scrollThreshold = 100;
            this.init();
        }

        init() {
            this.setupScrollBehavior();
            this.setupMobileMenu();
            this.setupActiveNavigation();
            this.setupSmoothScrolling();
        }

        setupScrollBehavior() {
            const handleScroll = throttle(() => {
                const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                
                // Add scrolled class for styling
                if (scrollTop > 50) {
                    this.navbar?.classList.add('scrolled');
                } else {
                    this.navbar?.classList.remove('scrolled');
                }

                // Hide/show navbar on scroll (optional)
                if (scrollTop > this.scrollThreshold) {
                    if (scrollTop > this.lastScrollTop) {
                        // Scrolling down
                        this.navbar?.classList.add('navbar-hidden');
                    } else {
                        // Scrolling up
                        this.navbar?.classList.remove('navbar-hidden');
                    }
                }
                
                this.lastScrollTop = scrollTop;
            }, 100);

            window.addEventListener('scroll', handleScroll, { passive: true });
        }

        setupMobileMenu() {
            const toggleButton = document.querySelector('.navbar-toggler');
            const navbarCollapse = document.querySelector('.navbar-collapse');

            if (toggleButton && navbarCollapse) {
                toggleButton.addEventListener('click', () => {
                    const isExpanded = toggleButton.getAttribute('aria-expanded') === 'true';
                    toggleButton.setAttribute('aria-expanded', !isExpanded);
                    navbarCollapse.classList.toggle('show');
                });

                // Close mobile menu when clicking outside
                document.addEventListener('click', (e) => {
                    if (!toggleButton.contains(e.target) && !navbarCollapse.contains(e.target)) {
                        toggleButton.setAttribute('aria-expanded', 'false');
                        navbarCollapse.classList.remove('show');
                    }
                });
            }
        }

        setupActiveNavigation() {
            const navLinks = document.querySelectorAll('.nav-link');
            const currentPath = window.location.pathname;

            navLinks.forEach(link => {
                if (link.getAttribute('href') === currentPath) {
                    link.classList.add('active');
                    link.setAttribute('aria-current', 'page');
                }
            });
        }

        setupSmoothScrolling() {
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function (e) {
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {
                        const offsetTop = target.offsetTop - (this.navbar?.offsetHeight || 76);
                        window.scrollTo({
                            top: offsetTop,
                            behavior: 'smooth'
                        });
                    }
                });
            });
        }
    }

    // ===== ENHANCED THEME SYSTEM =====
    
    class ThemeSystemEnhancer {
        constructor() {
            this.currentTheme = localStorage.getItem('snooker-theme-preference') || 'dark';
            this.init();
        }

        init() {
            this.applyTheme(this.currentTheme);
            this.setupThemeToggle();
            this.setupSystemPreferenceDetection();
            this.setupThemeTransitions();
        }

        applyTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            document.body.setAttribute('data-theme', theme);
            document.documentElement.style.colorScheme = theme;
            
            this.updateThemeToggleUI(theme);
            this.updateMetaThemeColor(theme);
            
            localStorage.setItem('snooker-theme-preference', theme);
            this.currentTheme = theme;

            // Dispatch custom event for other components
            window.dispatchEvent(new CustomEvent('themeChanged', { 
                detail: { theme } 
            }));
        }

        setupThemeToggle() {
            const toggleButtons = document.querySelectorAll('[id*="ThemeToggle"], .theme-toggle-btn');
            
            toggleButtons.forEach(button => {
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
                    this.applyTheme(newTheme);
                    
                    // Add visual feedback
                    button.style.transform = 'scale(0.95)';
                    setTimeout(() => {
                        button.style.transform = '';
                    }, 150);
                });
            });

            // Keyboard shortcut: Ctrl/Cmd + Shift + T
            document.addEventListener('keydown', (e) => {
                if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
                    e.preventDefault();
                    const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
                    this.applyTheme(newTheme);
                    this.announceThemeChange(newTheme);
                }
            });
        }

        updateThemeToggleUI(theme) {
            const icons = document.querySelectorAll('[id*="ThemeIcon"]');
            const texts = document.querySelectorAll('[id*="ThemeText"]');
            
            icons.forEach(icon => {
                icon.className = theme === 'light' ? 'fas fa-moon me-1' : 'fas fa-sun me-1';
            });
            
            texts.forEach(text => {
                text.textContent = theme === 'light' ? 'Dark' : 'Light';
            });
        }

        updateMetaThemeColor(theme) {
            let metaThemeColor = document.querySelector('meta[name="theme-color"]');
            if (!metaThemeColor) {
                metaThemeColor = document.createElement('meta');
                metaThemeColor.name = 'theme-color';
                document.head.appendChild(metaThemeColor);
            }
            
            metaThemeColor.content = theme === 'light' ? '#ffffff' : '#1a202c';
        }

        setupSystemPreferenceDetection() {
            if (window.matchMedia) {
                const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
                
                const handleChange = (e) => {
                    if (!localStorage.getItem('snooker-theme-preference')) {
                        this.applyTheme(e.matches ? 'dark' : 'light');
                    }
                };
                
                mediaQuery.addEventListener('change', handleChange);
                
                // Apply system preference if no saved preference
                if (!localStorage.getItem('snooker-theme-preference')) {
                    this.applyTheme(mediaQuery.matches ? 'dark' : 'light');
                }
            }
        }

        setupThemeTransitions() {
            document.body.classList.add('theme-transition');
        }

        announceThemeChange(theme) {
            const announcement = document.createElement('div');
            announcement.setAttribute('aria-live', 'polite');
            announcement.setAttribute('aria-atomic', 'true');
            announcement.className = 'sr-only';
            announcement.textContent = `Theme changed to ${theme} mode`;
            document.body.appendChild(announcement);
            
            setTimeout(() => {
                document.body.removeChild(announcement);
            }, 1000);
        }
    }

    // ===== ENHANCED FORM INTERACTIONS =====
    
    class FormEnhancer {
        constructor() {
            this.init();
        }

        init() {
            this.setupFileUploads();
            this.setupFormValidation();
            this.setupProgressIndicators();
        }

        setupFileUploads() {
            const fileInputs = document.querySelectorAll('input[type="file"]');
            
            fileInputs.forEach(input => {
                const dropZone = input.closest('.upload-area-motivating, .upload-area');
                
                if (dropZone) {
                    this.setupDragAndDrop(dropZone, input);
                }
                
                input.addEventListener('change', (e) => {
                    this.handleFileSelection(e.target);
                });
            });
        }

        setupDragAndDrop(dropZone, input) {
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, this.preventDefaults, false);
            });

            ['dragenter', 'dragover'].forEach(eventName => {
                dropZone.addEventListener(eventName, () => {
                    dropZone.classList.add('dragover');
                }, false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, () => {
                    dropZone.classList.remove('dragover');
                }, false);
            });

            dropZone.addEventListener('drop', (e) => {
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    input.files = files;
                    this.handleFileSelection(input);
                }
            }, false);
        }

        preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        handleFileSelection(input) {
            const file = input.files[0];
            if (!file) return;

            // Validate file
            if (!this.validateFile(file)) {
                this.showError('Please select a valid video file (MP4, AVI, MOV, MKV, WEBM)');
                return;
            }

            // Update UI
            this.updateFileInfo(file);
            this.enableSubmitButton();
        }

        validateFile(file) {
            const validTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo', 'video/webm'];
            const validExtensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm'];
            
            return validTypes.includes(file.type) || 
                   validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
        }

        updateFileInfo(file) {
            const fileName = document.getElementById('fileName');
            const fileSize = document.getElementById('fileSize');
            const fileInfo = document.getElementById('fileInfo');
            
            if (fileName) fileName.textContent = file.name;
            if (fileSize) fileSize.textContent = this.formatFileSize(file.size);
            if (fileInfo) fileInfo.classList.remove('d-none');
        }

        enableSubmitButton() {
            const submitBtn = document.getElementById('analyzeBtn');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.classList.add('btn-ready');
            }
        }

        formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }

        setupFormValidation() {
            const forms = document.querySelectorAll('form');
            
            forms.forEach(form => {
                form.addEventListener('submit', (e) => {
                    if (!this.validateForm(form)) {
                        e.preventDefault();
                        return false;
                    }
                });
            });
        }

        validateForm(form) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    this.showFieldError(field, 'This field is required');
                    isValid = false;
                } else {
                    this.clearFieldError(field);
                }
            });
            
            return isValid;
        }

        showFieldError(field, message) {
            field.classList.add('is-invalid');
            
            let errorDiv = field.parentNode.querySelector('.invalid-feedback');
            if (!errorDiv) {
                errorDiv = document.createElement('div');
                errorDiv.className = 'invalid-feedback';
                field.parentNode.appendChild(errorDiv);
            }
            errorDiv.textContent = message;
        }

        clearFieldError(field) {
            field.classList.remove('is-invalid');
            const errorDiv = field.parentNode.querySelector('.invalid-feedback');
            if (errorDiv) {
                errorDiv.remove();
            }
        }

        showError(message) {
            this.showNotification(message, 'error');
        }

        showNotification(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
            notification.style.cssText = 'top: 100px; right: 20px; z-index: 9999; min-width: 300px;';
            notification.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.remove();
            }, 5000);
        }

        setupProgressIndicators() {
            // This would be enhanced with WebSocket connections in a real implementation
            const progressBars = document.querySelectorAll('.progress-bar');
            
            progressBars.forEach(bar => {
                const targetWidth = bar.style.width || bar.getAttribute('data-width') || '0%';
                bar.style.width = '0%';
                
                setTimeout(() => {
                    bar.style.width = targetWidth;
                }, 100);
            });
        }
    }

    // ===== ENHANCED ANIMATIONS =====
    
    class AnimationEnhancer {
        constructor() {
            this.init();
        }

        init() {
            this.setupIntersectionObserver();
            this.setupParallaxEffects();
            this.setupCounterAnimations();
        }

        setupIntersectionObserver() {
            if (!window.IntersectionObserver) return;

            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('animate-in');
                        
                        // Trigger counter animations
                        if (entry.target.classList.contains('stat-value')) {
                            this.animateCounter(entry.target);
                        }
                    }
                });
            }, {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            });

            // Observe elements for animation
            document.querySelectorAll('.card, .stat-item, .feature-icon').forEach(el => {
                observer.observe(el);
            });
        }

        setupParallaxEffects() {
            const parallaxElements = document.querySelectorAll('.hero-logo-backdrop');
            
            if (parallaxElements.length === 0) return;

            const handleScroll = throttle(() => {
                const scrolled = window.pageYOffset;
                
                parallaxElements.forEach(element => {
                    const rate = scrolled * -0.5;
                    element.style.transform = `translateY(${rate}px)`;
                });
            }, 16);

            window.addEventListener('scroll', handleScroll, { passive: true });
        }

        animateCounter(element) {
            const target = parseInt(element.textContent) || 0;
            const duration = 2000;
            const start = performance.now();
            const startValue = 0;

            const animate = (currentTime) => {
                const elapsed = currentTime - start;
                const progress = Math.min(elapsed / duration, 1);
                
                const easeOutQuart = 1 - Math.pow(1 - progress, 4);
                const current = Math.floor(startValue + (target - startValue) * easeOutQuart);
                
                element.textContent = current;
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                }
            };

            requestAnimationFrame(animate);
        }

        setupCounterAnimations() {
            // Add CSS for animation states
            const style = document.createElement('style');
            style.textContent = `
                .animate-in {
                    animation: fadeInUp 0.6s ease-out forwards;
                }
                
                @keyframes fadeInUp {
                    from {
                        opacity: 0;
                        transform: translateY(30px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }

    // ===== ACCESSIBILITY ENHANCEMENTS =====
    
    class AccessibilityEnhancer {
        constructor() {
            this.init();
        }

        init() {
            this.setupKeyboardNavigation();
            this.setupFocusManagement();
            this.setupARIALabels();
            this.setupReducedMotion();
        }

        setupKeyboardNavigation() {
            // Escape key to close modals
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    const openModal = document.querySelector('.modal.show');
                    if (openModal) {
                        const closeBtn = openModal.querySelector('.btn-close');
                        if (closeBtn) closeBtn.click();
                    }
                }
            });

            // Tab navigation improvements
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Tab') {
                    document.body.classList.add('keyboard-navigation');
                }
            });

            document.addEventListener('mousedown', () => {
                document.body.classList.remove('keyboard-navigation');
            });
        }

        setupFocusManagement() {
            // Focus trap for modals
            const modals = document.querySelectorAll('.modal');
            
            modals.forEach(modal => {
                modal.addEventListener('shown.bs.modal', () => {
                    const focusableElements = modal.querySelectorAll(
                        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
                    );
                    
                    if (focusableElements.length > 0) {
                        focusableElements[0].focus();
                    }
                });
            });
        }

        setupARIALabels() {
            // Add missing ARIA labels
            const buttons = document.querySelectorAll('button:not([aria-label]):not([aria-labelledby])');
            buttons.forEach(button => {
                const text = button.textContent.trim();
                if (text) {
                    button.setAttribute('aria-label', text);
                }
            });

            // Add role attributes where needed
            const navs = document.querySelectorAll('nav:not([role])');
            navs.forEach(nav => nav.setAttribute('role', 'navigation'));
        }

        setupReducedMotion() {
            if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
                document.documentElement.style.setProperty('--transition-duration', '0.01ms');
                document.documentElement.style.setProperty('--animation-duration', '0.01ms');
            }
        }
    }

    // ===== PERFORMANCE MONITORING =====
    
    class PerformanceMonitor {
        constructor() {
            this.init();
        }

        init() {
            this.setupLazyLoading();
            this.setupImageOptimization();
            this.monitorWebVitals();
        }

        setupLazyLoading() {
            if ('IntersectionObserver' in window) {
                const imageObserver = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const img = entry.target;
                            img.src = img.dataset.src;
                            img.classList.remove('lazy');
                            imageObserver.unobserve(img);
                        }
                    });
                });

                document.querySelectorAll('img[data-src]').forEach(img => {
                    imageObserver.observe(img);
                });
            }
        }

        setupImageOptimization() {
            // Add loading="lazy" to images below the fold
            const images = document.querySelectorAll('img:not([loading])');
            images.forEach((img, index) => {
                if (index > 2) { // Skip first 3 images (likely above fold)
                    img.setAttribute('loading', 'lazy');
                }
            });
        }

        monitorWebVitals() {
            // Basic performance monitoring
            if ('performance' in window) {
                window.addEventListener('load', () => {
                    const perfData = performance.getEntriesByType('navigation')[0];
                    
                    console.log('Performance Metrics:', {
                        'DOM Content Loaded': perfData.domContentLoadedEventEnd - perfData.domContentLoadedEventStart,
                        'Load Complete': perfData.loadEventEnd - perfData.loadEventStart,
                        'Total Load Time': perfData.loadEventEnd - perfData.fetchStart
                    });
                });
            }
        }
    }

    // ===== INITIALIZATION =====
    
    function initializeEnhancements() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initializeEnhancements);
            return;
        }

        try {
            new NavigationEnhancer();
            new ThemeSystemEnhancer();
            new FormEnhancer();
            new AnimationEnhancer();
            new AccessibilityEnhancer();
            new PerformanceMonitor();
            
            console.log('🚀 Industry standard enhancements initialized successfully');
        } catch (error) {
            console.error('❌ Error initializing enhancements:', error);
        }
    }

    // Initialize when script loads
    initializeEnhancements();

    // Global utilities
    window.SnookerEnhancements = {
        debounce,
        throttle,
        formatFileSize: (bytes) => {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
    };

})();