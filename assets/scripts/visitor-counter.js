// Privacy-friendly visitor counter for ombra tools
(function() {
  'use strict';

  // Initialize visitor counter
  function initVisitorCounter() {
    // Check if we are on the homepage and have a hero section
    const hero = document.querySelector('.hero');
    
    if (hero) {
      // Prevent duplicate counters
      if (hero.querySelector('.visitor-counter-hero')) return;

      // Hero counter container matching old design
      const container = document.createElement('div');
      container.className = 'visitor-counter-hero';
      
      // Inner HTML structure using image badge to avoid CORS issues
      container.innerHTML = `
        <img src="https://counterapi.com/api/ombra.cc/view/index?icon=eye&color=ffffff&bg=00000000&size=15" alt="page views" style="vertical-align: middle; height: 24px;" />
        <span class="label" style="margin-left: 8px;">page views</span>
      `;

      // Insert after subtitle
      const subtitle = hero.querySelector('.hero-subtitle');
      if (subtitle) {
        subtitle.parentNode.insertBefore(container, subtitle.nextSibling);
      } else {
        hero.appendChild(container);
      }
    } else {
      // Footer fallback for other pages
      const footer = document.querySelector('.footer');
      if (footer && !document.querySelector('.visitor-counter')) {
        const container = document.createElement('div');
        container.className = 'visitor-counter';
        container.innerHTML = `
          <span class="visitor-counter-label">Total views:</span>
          <img src="https://counterapi.com/api/ombra.cc/view/index?icon=eye&color=ffffff&bg=00000000&size=12" alt="views" style="vertical-align: middle; margin-left: 6px; height: 16px;" />
        `;
        
        const footerText = footer.querySelector('p');
        if (footerText) {
          footer.insertBefore(container, footerText);
        } else {
          footer.appendChild(container);
        }
      }
    }
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initVisitorCounter);
  } else {
    initVisitorCounter();
  }
})();
