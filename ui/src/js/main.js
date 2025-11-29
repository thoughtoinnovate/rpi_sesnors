// Main entry point for the Air Quality UI
// This file imports and initializes all modules

// Import modules (they're loaded via script tags in HTML)
// This file serves as the main entry point for bundling

console.log('Air Quality UI - Lightweight Version');
console.log('Optimized for Raspberry Pi 3');

// Global initialization
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing application...');
    
    // Check if all required dependencies are loaded
    if (typeof Alpine === 'undefined') {
        console.error('Alpine.js not loaded');
        return;
    }
    
    if (typeof Chart === 'undefined') {
        console.error('Chart.js not loaded');
        return;
    }
    
    if (typeof apiClient === 'undefined') {
        console.error('API client not loaded');
        return;
    }
    
    console.log('All dependencies loaded successfully');
});

// Export for module bundling
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {};
}