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
      
      // Inner HTML structure using hitwebcounter
      container.innerHTML = `
        <span class="icon">👁️</span>
        <a href="https://www.hitwebcounter.com/" target="_blank" style="display: flex; align-items: center;">
          <img src="https://hitwebcounter.com/counter/counter.php?page=21475421&style=0008&nbdigits=9&type=page&initCount=0" title="Free Tools" Alt="Free Tools" border="0" />
        </a>
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
          <a href="https://www.hitwebcounter.com/" target="_blank" style="display: inline-flex; align-items: center; margin-left: 6px;">
            <img src="https://hitwebcounter.com/counter/counter.php?page=21475421&style=0008&nbdigits=9&type=page&initCount=0" title="Free Tools" Alt="Free Tools" border="0" />
          </a>
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
