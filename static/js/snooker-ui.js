/**
 * Snooker Detection Pro - Enhanced UI Interactions
 * Following UI Guidelines: Energetic, playful, and motivating
 * Ensuring accessibility and smooth user experience
 */

class SnookerUI {
    constructor() {
        this.init();
    }

    init() {
        this.setupAnimations();
        this.setupAccessibility();
        this.setupInteractiveElements();
        this.setupProgressTracking();
        this.setupMotivationalMessages();
    }

    // Energetic animations and interactions
    setupAnimations() {
        // Add entrance animations to cards
        const cards = document.querySelectorAll('.card');
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.animation = 'slideInUp 0.6s ease-out';
                }
            });
        }, { threshold: 0.1 });

        cards.forEach(card => observer.observe(card));

        // Add hover effects to buttons
        document.querySelectorAll('.btn').forEach(btn => {
            btn.addEventListener('mouseenter', this.addButtonHoverEffect);
            btn.addEventListener('mouseleave', this.removeButtonHoverEffect);
        });

        // Add click ripple effect
        document.querySelectorAll('.btn, .card').forEach(element => {
            element.addEventListener('click', this.createRippleEffect);
        });
    }

    // Accessibility enhancements
    setupAccessibility() {
        // Add keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-navigation');
            }
        });

        document.addEventListener('mousedown', () => {
            document.body.classList.remove('keyboard-navigation');
        });

        // Add screen reader announcements
        this.setupScreenReaderAnnouncements();

        // Add high contrast mode toggle
        this.setupHighContrastMode();
    }

    // Interactive elements for engagement
    setupInteractiveElements() {
        // Add motivational tooltips
        this.addMotivationalTooltips();

        // Add progress celebrations
        this.setupProgressCelebrations();

        // Add dynamic status updates
        this.setupDynamicStatusUpdates();
    }

    // Progress tracking with motivational feedback
    setupProgressTracking() {
        const progressBars = document.querySelectorAll('.progress-bar');
        
        progressBars.forEach(bar => {
            const observer = new MutationObserver((mutations) => {
                mutations.forEach(mutation => {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                        const progress = parseInt(bar.style.width);
                        this.updateProgressMotivation(progress, bar);
                    }
                });
            });
            
            observer.observe(bar, { attributes: true });
        });
    }

    // Motivational messages system
    setupMotivationalMessages() {
        this.motivationalMessages = {
            start: [
                "🚀 Let's analyze your game!",
                "🎯 Time to unlock your potential!",
                "⚡ Get ready for some insights!",
                "🏆 Your journey to mastery begins now!"
            ],
            progress: {
                25: ["🔥 Great start! Keep it going!", "💪 You're on fire!"],
                50: ["🎊 Halfway there! Amazing progress!", "⭐ You're crushing it!"],
                75: ["🚀 Almost done! The finish line is near!", "🎯 Excellence is within reach!"],
                100: ["🏆 Fantastic! Analysis complete!", "🎉 You did it! Check out those results!"]
            },
            encouragement: [
                "Every shot tells a story 📖",
                "Precision meets passion 🎱",
                "Your game, elevated by AI 🤖",
                "Champions analyze, legends improve 👑"
            ]
        };

        // Show random motivational message on page load
        this.showMotivationalMessage();
    }

    // Button hover effects
    addButtonHoverEffect(e) {
        const btn = e.target;
        btn.style.transform = 'translateY(-2px) scale(1.05)';
        btn.style.boxShadow = '0 8px 25px rgba(255, 107, 53, 0.4)';
    }

    removeButtonHoverEffect(e) {
        const btn = e.target;
        btn.style.transform = '';
        btn.style.boxShadow = '';
    }

    // Ripple effect for clicks
    createRippleEffect(e) {
        const element = e.currentTarget;
        const rect = element.getBoundingClientRect();
        const ripple = document.createElement('span');
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;

        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: rgba(255, 215, 0, 0.3);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s ease-out;
            pointer-events: none;
            z-index: 1000;
        `;

        element.style.position = 'relative';
        element.style.overflow = 'hidden';
        element.appendChild(ripple);

        setTimeout(() => ripple.remove(), 600);
    }

    // Screen reader announcements
    setupScreenReaderAnnouncements() {
        const announcer = document.createElement('div');
        announcer.setAttribute('aria-live', 'polite');
        announcer.setAttribute('aria-atomic', 'true');
        announcer.className = 'sr-only';
        announcer.id = 'screen-reader-announcer';
        document.body.appendChild(announcer);
    }

    announce(message) {
        const announcer = document.getElementById('screen-reader-announcer');
        if (announcer) {
            announcer.textContent = message;
        }
    }

    // High contrast mode
    setupHighContrastMode() {
        const toggleButton = document.createElement('button');
        toggleButton.innerHTML = '<i class="fas fa-adjust"></i>';
        toggleButton.className = 'btn btn-outline-light position-fixed';
        toggleButton.style.cssText = `
            bottom: 20px;
            right: 20px;
            z-index: 1050;
            border-radius: 50%;
            width: 50px;
            height: 50px;
        `;
        toggleButton.setAttribute('aria-label', 'Toggle high contrast mode');
        toggleButton.addEventListener('click', this.toggleHighContrast);
        
        document.body.appendChild(toggleButton);
    }

    toggleHighContrast() {
        document.body.classList.toggle('high-contrast');
        const isHighContrast = document.body.classList.contains('high-contrast');
        localStorage.setItem('highContrast', isHighContrast);
        
        // Announce change
        const ui = new SnookerUI();
        ui.announce(isHighContrast ? 'High contrast mode enabled' : 'High contrast mode disabled');
    }

    // Motivational tooltips
    addMotivationalTooltips() {
        const tooltips = {
            '.btn-primary': 'Ready to see the magic happen? 🎩✨',
            '.feature-icon': 'This feature will blow your mind! 🤯',
            '.card': 'Click to explore this amazing feature! 🚀',
            '.progress-bar': 'Watch your progress soar! 📈'
        };

        Object.entries(tooltips).forEach(([selector, message]) => {
            document.querySelectorAll(selector).forEach(element => {
                element.setAttribute('title', message);
                element.setAttribute('data-bs-toggle', 'tooltip');
            });
        });

        // Initialize Bootstrap tooltips if available
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
        }
    }

    // Progress celebrations
    setupProgressCelebrations() {
        this.celebrationEmojis = ['🎉', '🎊', '🏆', '⭐', '🚀', '💫', '🔥', '💪'];
    }

    updateProgressMotivation(progress, progressBar) {
        const container = progressBar.closest('.progress').parentElement;
        
        // Add motivational messages at key milestones
        if (this.motivationalMessages.progress[progress]) {
            const messages = this.motivationalMessages.progress[progress];
            const message = messages[Math.floor(Math.random() * messages.length)];
            this.showTemporaryMessage(message, container);
        }

        // Add celebration effects at 100%
        if (progress >= 100) {
            this.triggerCelebration(container);
        }
    }

    showTemporaryMessage(message, container) {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
        const isLightMode = currentTheme === 'light';
        
        const messageEl = document.createElement('div');
        messageEl.className = 'alert alert-success mt-2 animate-bounce theme-aware-notification';
        messageEl.innerHTML = `<i class="fas fa-star me-2"></i>${message}`;
        messageEl.style.cssText = `
            animation: slideInUp 0.5s ease-out;
            ${isLightMode ? 
                'background-color: #d1fae5 !important; color: #065f46 !important; border-color: #10b981 !important;' : 
                'background-color: #064e3b !important; color: #d1fae5 !important; border-color: #10b981 !important;'
            }
        `;
        
        container.appendChild(messageEl);
        
        setTimeout(() => {
            messageEl.style.animation = 'slideOutUp 0.5s ease-in';
            setTimeout(() => messageEl.remove(), 500);
        }, 3000);
    }

    triggerCelebration(container) {
        // Create celebration animation
        for (let i = 0; i < 10; i++) {
            setTimeout(() => {
                const emoji = this.celebrationEmojis[Math.floor(Math.random() * this.celebrationEmojis.length)];
                this.createFloatingEmoji(emoji, container);
            }, i * 100);
        }

        // Play success sound (if audio is enabled)
        this.playSuccessSound();
    }

    createFloatingEmoji(emoji, container) {
        const emojiEl = document.createElement('div');
        emojiEl.textContent = emoji;
        emojiEl.style.cssText = `
            position: absolute;
            font-size: 2rem;
            pointer-events: none;
            z-index: 1000;
            animation: floatUp 2s ease-out forwards;
            left: ${Math.random() * 100}%;
            top: 100%;
        `;
        
        container.style.position = 'relative';
        container.appendChild(emojiEl);
        
        setTimeout(() => emojiEl.remove(), 2000);
    }

    playSuccessSound() {
        // Create a simple success sound using Web Audio API
        if (typeof AudioContext !== 'undefined' || typeof webkitAudioContext !== 'undefined') {
            const audioContext = new (AudioContext || webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
            oscillator.frequency.setValueAtTime(1000, audioContext.currentTime + 0.1);
            oscillator.frequency.setValueAtTime(1200, audioContext.currentTime + 0.2);
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
        }
    }

    // Dynamic status updates
    setupDynamicStatusUpdates() {
        // Update system status with motivational messages
        const statusElements = document.querySelectorAll('#systemStatus, .system-status');
        
        statusElements.forEach(element => {
            const observer = new MutationObserver(() => {
                this.updateStatusMotivation(element);
            });
            
            observer.observe(element, { childList: true, characterData: true, subtree: true });
        });
    }

    updateStatusMotivation(element) {
        const status = element.textContent.toLowerCase();
        let motivationalClass = '';
        let icon = '';
        
        if (status.includes('ready')) {
            motivationalClass = 'text-success animate-glow';
            icon = '🚀';
        } else if (status.includes('processing')) {
            motivationalClass = 'text-warning animate-pulse';
            icon = '⚡';
        } else if (status.includes('complete')) {
            motivationalClass = 'text-success animate-bounce';
            icon = '🏆';
        }
        
        element.className = `${element.className.split(' ')[0]} ${motivationalClass}`;
        if (icon && !element.textContent.includes(icon)) {
            element.textContent = `${icon} ${element.textContent}`;
        }
    }

    // Show motivational message on page load
    showMotivationalMessage() {
        const messages = this.motivationalMessages.encouragement;
        const message = messages[Math.floor(Math.random() * messages.length)];
        
        // Get current theme to determine appropriate styling
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
        const isLightMode = currentTheme === 'light';
        
        // Create floating message with theme-appropriate styling
        const messageEl = document.createElement('div');
        messageEl.className = `position-fixed p-3 rounded shadow notification-popup theme-aware-notification`;
        
        // Apply theme-appropriate styles
        if (isLightMode) {
            messageEl.style.cssText = `
                top: 100px;
                right: 20px;
                z-index: 1050;
                animation: slideInRight 0.5s ease-out;
                max-width: 300px;
                background: #ffffff !important;
                color: #1a202c !important;
                border: 1px solid #e2e8f0 !important;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;
            `;
        } else {
            messageEl.style.cssText = `
                top: 100px;
                right: 20px;
                z-index: 1050;
                animation: slideInRight 0.5s ease-out;
                max-width: 300px;
                background: #374151 !important;
                color: #ffffff !important;
                border: 1px solid #6b7280 !important;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
            `;
        }
        
        messageEl.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-lightbulb me-2" style="color: ${isLightMode ? '#d97706' : '#fbbf24'} !important;"></i>
                <span style="color: ${isLightMode ? '#1a202c' : '#ffffff'} !important; font-weight: 500;">${message}</span>
                <button class="btn-close ${isLightMode ? '' : 'btn-close-white'} ms-auto" 
                        onclick="this.parentElement.parentElement.remove()"
                        style="filter: ${isLightMode ? 'invert(1)' : 'none'}; opacity: 0.8;"
                        onmouseover="this.style.opacity='1'"
                        onmouseout="this.style.opacity='0.8'"></button>
            </div>
        `;
        
        document.body.appendChild(messageEl);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageEl.parentElement) {
                messageEl.style.animation = 'slideOutRight 0.5s ease-in';
                setTimeout(() => messageEl.remove(), 500);
            }
        }, 5000);
    }

    // Utility methods
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// CSS animations for the JavaScript effects
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInUp {
        from { transform: translateY(100%); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    
    @keyframes slideOutUp {
        from { transform: translateY(0); opacity: 1; }
        to { transform: translateY(-100%); opacity: 0; }
    }
    
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    @keyframes floatUp {
        from { transform: translateY(0) rotate(0deg); opacity: 1; }
        to { transform: translateY(-200px) rotate(360deg); opacity: 0; }
    }
    
    @keyframes ripple {
        to { transform: scale(4); opacity: 0; }
    }
    
    .keyboard-navigation *:focus {
        outline: 3px solid #ffd700 !important;
        outline-offset: 2px !important;
    }
    
    .high-contrast {
        filter: contrast(150%) brightness(120%);
    }
    
    .high-contrast .card {
        border: 2px solid #ffffff !important;
    }
    
    .high-contrast .text-muted {
        color: #cccccc !important;
    }
    
    /* Theme-aware notification popup styling */
    [data-theme="light"] .notification-popup,
    [data-theme="light"] .theme-aware-notification {
        background: #ffffff !important;
        color: #1a202c !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;
    }
    
    [data-theme="light"] .notification-popup *,
    [data-theme="light"] .theme-aware-notification * {
        color: #1a202c !important;
    }
    
    [data-theme="light"] .notification-popup .btn-close,
    [data-theme="light"] .theme-aware-notification .btn-close {
        filter: invert(1) !important;
    }
    
    [data-theme="dark"] .notification-popup,
    [data-theme="dark"] .theme-aware-notification {
        background: #2d3748 !important;
        color: #ffffff !important;
        border: 1px solid #4a5568 !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
    }
    
    [data-theme="dark"] .notification-popup *,
    [data-theme="dark"] .theme-aware-notification * {
        color: #ffffff !important;
    }
    
    [data-theme="dark"] .notification-popup .btn-close,
    [data-theme="dark"] .theme-aware-notification .btn-close {
        filter: none !important;
    }
`;
document.head.appendChild(style);

// Initialize the UI system when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.snookerUI = new SnookerUI();
    
    // Load saved preferences
    if (localStorage.getItem('highContrast') === 'true') {
        document.body.classList.add('high-contrast');
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SnookerUI;
}