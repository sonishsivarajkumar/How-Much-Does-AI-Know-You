
// AI Audit Privacy Monitor - Content Script
(function() {
    'use strict';
    
    const API_BASE = 'http://localhost:8000';
    let isAnalyzing = false;
    let highlightedElements = [];
    
    // Initialize the privacy monitor
    function initPrivacyMonitor() {
        console.log('AI Audit Privacy Monitor initialized');
        
        // Add style for highlighted elements
        addHighlightStyles();
        
        // Analyze page on load
        setTimeout(analyzePage, 2000);
        
        // Listen for DOM changes
        const observer = new MutationObserver(debounce(analyzePage, 1000));
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    function addHighlightStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .ai-audit-highlight {
                position: relative;
                outline: 2px solid transparent;
                transition: outline-color 0.3s ease;
            }
            .ai-audit-highlight-high { outline-color: #ff4444; }
            .ai-audit-highlight-medium { outline-color: #ffaa00; }
            .ai-audit-highlight-low { outline-color: #ffff00; }
            .ai-audit-highlight-minimal { outline-color: #88ff88; }
            
            .ai-audit-tooltip {
                position: absolute;
                top: -30px;
                left: 0;
                background: #333;
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
                z-index: 10000;
                display: none;
                white-space: nowrap;
            }
            
            .ai-audit-highlight:hover .ai-audit-tooltip {
                display: block;
            }
        `;
        document.head.appendChild(style);
    }
    
    async function analyzePage() {
        if (isAnalyzing) return;
        isAnalyzing = true;
        
        try {
            const elements = extractPageElements();
            if (elements.length === 0) {
                isAnalyzing = false;
                return;
            }
            
            const analysis = await analyzeElements(elements);
            if (analysis && analysis.risky_elements) {
                highlightRiskyElements(analysis.risky_elements);
                updateBadge(analysis.risk_level);
            }
        } catch (error) {
            console.error('Privacy analysis error:', error);
        }
        
        isAnalyzing = false;
    }
    
    function extractPageElements() {
        const elements = [];
        const url = window.location.href;
        
        // Extract profile fields based on platform
        if (url.includes('github.com')) {
            extractGitHubElements(elements);
        } else if (url.includes('twitter.com') || url.includes('x.com')) {
            extractTwitterElements(elements);
        } else if (url.includes('linkedin.com')) {
            extractLinkedInElements(elements);
        }
        
        return elements;
    }
    
    function extractGitHubElements(elements) {
        // GitHub profile elements
        const bio = document.querySelector('.user-profile-bio');
        if (bio) {
            elements.push({
                element_id: 'github-bio',
                type: 'bio_text',
                field_name: 'bio',
                content: bio.textContent.trim(),
                element: bio
            });
        }
        
        const location = document.querySelector('[itemprop="homeLocation"]');
        if (location) {
            elements.push({
                element_id: 'github-location',
                type: 'location_data',
                field_name: 'location',
                content: location.textContent.trim(),
                element: location
            });
        }
        
        const email = document.querySelector('[itemprop="email"]');
        if (email) {
            elements.push({
                element_id: 'github-email',
                type: 'contact_info',
                field_name: 'email',
                content: email.textContent.trim(),
                element: email
            });
        }
    }
    
    function extractTwitterElements(elements) {
        // Twitter profile elements
        const bio = document.querySelector('[data-testid="UserDescription"]');
        if (bio) {
            elements.push({
                element_id: 'twitter-bio',
                type: 'bio_text',
                field_name: 'bio',
                content: bio.textContent.trim(),
                element: bio
            });
        }
        
        const location = document.querySelector('[data-testid="UserLocation"]');
        if (location) {
            elements.push({
                element_id: 'twitter-location',
                type: 'location_data',
                field_name: 'location',
                content: location.textContent.trim(),
                element: location
            });
        }
    }
    
    function extractLinkedInElements(elements) {
        // LinkedIn profile elements
        const headline = document.querySelector('.text-heading-xlarge');
        if (headline) {
            elements.push({
                element_id: 'linkedin-headline',
                type: 'profile_field',
                field_name: 'headline',
                content: headline.textContent.trim(),
                element: headline
            });
        }
        
        const location = document.querySelector('.text-body-small.inline');
        if (location) {
            elements.push({
                element_id: 'linkedin-location',
                type: 'location_data',
                field_name: 'location',
                content: location.textContent.trim(),
                element: location
            });
        }
    }
    
    async function analyzeElements(elements) {
        try {
            const response = await fetch(`${API_BASE}/api/browser-extension/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: window.location.href,
                    elements: elements.map(e => ({
                        element_id: e.element_id,
                        type: e.type,
                        field_name: e.field_name,
                        content: e.content
                    }))
                })
            });
            
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Analysis request failed:', error);
        }
        
        return null;
    }
    
    function highlightRiskyElements(riskyElements) {
        // Clear previous highlights
        clearHighlights();
        
        riskyElements.forEach(element => {
            const domElement = document.querySelector(`[data-element-id="${element.element_id}"]`) ||
                             findElementByContent(element.content_preview);
            
            if (domElement) {
                highlightElement(domElement, element);
            }
        });
    }
    
    function highlightElement(element, riskData) {
        element.classList.add('ai-audit-highlight');
        element.classList.add(`ai-audit-highlight-${riskData.risk_level || 'medium'}`);
        
        // Add tooltip
        const tooltip = document.createElement('div');
        tooltip.className = 'ai-audit-tooltip';
        tooltip.textContent = `Privacy Risk: ${riskData.risk_score}/10 - ${riskData.risk_reasons[0] || 'Review recommended'}`;
        element.appendChild(tooltip);
        
        highlightedElements.push(element);
    }
    
    function clearHighlights() {
        highlightedElements.forEach(element => {
            element.classList.remove('ai-audit-highlight', 'ai-audit-highlight-high', 
                                   'ai-audit-highlight-medium', 'ai-audit-highlight-low', 
                                   'ai-audit-highlight-minimal');
            const tooltip = element.querySelector('.ai-audit-tooltip');
            if (tooltip) {
                tooltip.remove();
            }
        });
        highlightedElements = [];
    }
    
    function findElementByContent(content) {
        const elements = document.querySelectorAll('*');
        for (let element of elements) {
            if (element.textContent.includes(content.substring(0, 50))) {
                return element;
            }
        }
        return null;
    }
    
    function updateBadge(riskLevel) {
        chrome.runtime.sendMessage({
            action: 'updateBadge',
            riskLevel: riskLevel
        });
    }
    
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
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPrivacyMonitor);
    } else {
        initPrivacyMonitor();
    }
})();
