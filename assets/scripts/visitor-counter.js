// Privacy-friendly visitor counter for ombra tools
(function() {
  'use strict';

  // Initialize visitor counter
  function initVisitorCounter() {
    // Simple client-side counter (stored in localStorage)
    let count = parseInt(localStorage.getItem('ombra-visitor-count') || '0');
    
    // Increment if this is a new session
    const sessionKey = 'ombra-session-' + new Date().toDateString();
    if (!sessionStorage.getItem(sessionKey)) {
      count++;
      localStorage.setItem('ombra-visitor-count', count.toString());
      sessionStorage.setItem(sessionKey, 'true');
    }

    // Format number with commas
    const formattedCount = count.toLocaleString();

    // Animation helper
    function animateValue(obj, start, end, duration, callback) {
      let startTimestamp = null;
      const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const ease = 1 - Math.pow(1 - progress, 4); // Ease out quart
        const current = Math.floor(progress * (end - start) + start);
        obj.textContent = current.toLocaleString();
        if (progress < 1) {
          window.requestAnimationFrame(step);
        } else {
          obj.textContent = end.toLocaleString();
          if (callback) callback();
        }
      };
      window.requestAnimationFrame(step);
    }

    // Check if we are on the homepage and have a hero section
    const hero = document.querySelector('.hero');
    
    if (hero) {
      // Prevent duplicate counters
      if (hero.querySelector('.visitor-counter-hero')) return;

      // Hero counter
      const counterElement = document.createElement('div');
      counterElement.className = 'visitor-counter-hero';
      counterElement.innerHTML = `
        <span class="icon">👥</span>
        <span class="count">0</span>
        <span class="label" style="opacity: 0; transition: opacity 0.5s ease;">users served</span>
      `;
      
      // Insert after subtitle
      const subtitle = hero.querySelector('.hero-subtitle');
      if (subtitle) {
        subtitle.parentNode.insertBefore(counterElement, subtitle.nextSibling);
      } else {
        hero.appendChild(counterElement);
      }

      // Animate count (delayed to match CSS fade-in)
      setTimeout(() => {
        const countEl = counterElement.querySelector('.count');
        const labelEl = counterElement.querySelector('.label');
        if (countEl) {
          animateValue(countEl, 0, count, 800, () => {
            if (labelEl) labelEl.style.opacity = '1';
          });
        }
      }, 1000);
    } else {
      // Footer fallback for other pages
      const footer = document.querySelector('.footer');
      if (footer && !document.getElementById('visitor-counter')) {
        const counterElement = document.createElement('div');
        counterElement.id = 'visitor-counter';
        counterElement.className = 'visitor-counter';
        counterElement.innerHTML = `<span class="visitor-counter-label">Visited by</span> <span class="visitor-counter-number">0</span> <span class="visitor-counter-label">users</span>`;
        
        const footerText = footer.querySelector('p');
        if (footerText) {
          footer.insertBefore(counterElement, footerText);
        } else {
          footer.appendChild(counterElement);
        }

        const countEl = counterElement.querySelector('.visitor-counter-number');
        if (countEl) animateValue(countEl, 0, count, 800);
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
