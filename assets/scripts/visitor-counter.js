// Privacy-friendly visitor counter for ombra tools
(function() {
  'use strict';

  // Initialize visitor counter
  function initVisitorCounter() {
    // Inject the CounterAPI script
    const script = document.createElement('script');
    script.src = 'https://counterapi.com/c.js';
    script.async = true;
    document.head.appendChild(script);

    // Check if we are on the homepage and have a hero section
    const hero = document.querySelector('.hero');
    
    if (hero) {
      // Prevent duplicate counters
      if (hero.querySelector('.visitor-counter-hero')) return;

      // Hero counter container matching old design
      const container = document.createElement('div');
      container.className = 'visitor-counter-hero';
      
      // Inner HTML structure with icon, counterapi div, and label
      container.innerHTML = `
        <span class="icon">👁️</span>
        <div class="counterapi count" style="display:inline-block; min-height:0; min-width:1em;"></div>
        <span class="label">page views</span>
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
          <div class="counterapi" style="display:inline-block; min-height:0; min-width:1em;"></div>
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
