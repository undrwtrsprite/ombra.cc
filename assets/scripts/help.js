// Help and tooltip system for ombra tools
(function() {
  'use strict';

  // Tooltip system
  function initTooltips() {
    // Add tooltips to tool cards
    const toolCards = document.querySelectorAll('.glass-card');
    toolCards.forEach(card => {
      const description = card.querySelector('.card-description');
      if (description) {
        const title = card.querySelector('.card-title')?.textContent || '';
        const desc = description.textContent || '';
        
        // Add title attribute for native tooltip
        card.setAttribute('title', `${title}: ${desc}`);
        
        // Create custom tooltip on hover
        let tooltip = null;
        
        card.addEventListener('mouseenter', function(e) {
          if (tooltip) return;
          
          tooltip = document.createElement('div');
          tooltip.className = 'custom-tooltip';
          tooltip.textContent = desc;
          document.body.appendChild(tooltip);
          
          const rect = card.getBoundingClientRect();
          tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
          tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
          
          // Adjust if tooltip goes off screen
          setTimeout(() => {
            const tooltipRect = tooltip.getBoundingClientRect();
            if (tooltipRect.left < 10) {
              tooltip.style.left = '10px';
            }
            if (tooltipRect.right > window.innerWidth - 10) {
              tooltip.style.left = (window.innerWidth - tooltipRect.width - 10) + 'px';
            }
            if (tooltipRect.top < 10) {
              tooltip.style.top = rect.bottom + 8 + 'px';
            }
            tooltip.classList.add('visible');
          }, 10);
        });
        
        card.addEventListener('mouseleave', function() {
          if (tooltip) {
            tooltip.classList.remove('visible');
            setTimeout(() => {
              if (tooltip && tooltip.parentNode) {
                tooltip.parentNode.removeChild(tooltip);
              }
              tooltip = null;
            }, 200);
          }
        });
      }
    });
  }

  // Help overlay for first-time visitors
  function initHelpOverlay() {
    // Check if user has seen help before
    const hasSeenHelp = localStorage.getItem('ombra-help-seen');
    if (hasSeenHelp) return;

    // Only show on homepage
    if (window.location.pathname !== '/' && !window.location.pathname.endsWith('index.html')) {
      return;
    }

    // Create help overlay
    const overlay = document.createElement('div');
    overlay.className = 'help-overlay';
    overlay.id = 'helpOverlay';
    overlay.innerHTML = `
      <div class="help-overlay-content">
        <button class="help-overlay-close" aria-label="Close help">×</button>
        <h2>Welcome to ombra tools!</h2>
        <p>Here's a quick guide to get you started:</p>
        <ul>
          <li><strong>Search:</strong> Use the search bar or press <kbd>Ctrl+K</kbd> to find tools quickly</li>
          <li><strong>Navigate:</strong> Use arrow keys to browse tools, press <kbd>Enter</kbd> to open</li>
          <li><strong>Privacy:</strong> All tools run locally in your browser - your data never leaves your device</li>
          <li><strong>Offline:</strong> Install as a PWA to use tools without internet</li>
        </ul>
        <div class="help-overlay-actions">
          <button class="btn-primary" id="helpGotIt">Got it!</button>
          <label class="help-dont-show">
            <input type="checkbox" id="helpDontShow"> Don't show this again
          </label>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);

    // Show overlay after a short delay
    setTimeout(() => {
      overlay.classList.add('visible');
    }, 1000);

    // Close handlers
    const closeBtn = overlay.querySelector('.help-overlay-close');
    const gotItBtn = overlay.querySelector('#helpGotIt');
    const dontShowCheck = overlay.querySelector('#helpDontShow');

    function closeHelp() {
      overlay.classList.remove('visible');
      setTimeout(() => {
        if (overlay.parentNode) {
          overlay.parentNode.removeChild(overlay);
        }
      }, 300);

      if (dontShowCheck.checked) {
        localStorage.setItem('ombra-help-seen', 'true');
      }
    }

    closeBtn.addEventListener('click', closeHelp);
    gotItBtn.addEventListener('click', closeHelp);
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) closeHelp();
    });
  }

  // Contextual help on tool pages
  function initToolPageHelp() {
    // Only on tool pages
    if (!window.location.pathname.includes('/tools/')) return;

    // Add help icon to tool header if it exists
    const toolHeader = document.querySelector('.tool-header');
    if (toolHeader && !document.querySelector('.help-icon')) {
      const helpIcon = document.createElement('button');
      helpIcon.className = 'help-icon';
      helpIcon.setAttribute('aria-label', 'Show help');
      helpIcon.innerHTML = '?';
      helpIcon.title = 'Show help';

      // Insert after tool icon
      const toolIcon = toolHeader.querySelector('.tool-icon, .card-icon');
      if (toolIcon) {
        toolIcon.parentNode.insertBefore(helpIcon, toolIcon.nextSibling);
      } else {
        toolHeader.insertBefore(helpIcon, toolHeader.firstChild);
      }

      helpIcon.addEventListener('click', () => {
        // Show contextual help modal
        const helpModal = document.createElement('div');
        helpModal.className = 'help-modal';
        helpModal.innerHTML = `
          <div class="help-modal-content">
            <button class="help-modal-close" aria-label="Close">×</button>
            <h3>Tool Help</h3>
            <div class="help-modal-body">
              <p>This tool processes everything locally in your browser. Your data never leaves your device.</p>
              <p>For keyboard shortcuts, press <kbd>?</kbd> to see available commands.</p>
            </div>
          </div>
        `;
        document.body.appendChild(helpModal);

        setTimeout(() => helpModal.classList.add('visible'), 10);

        const closeBtn = helpModal.querySelector('.help-modal-close');
        closeBtn.addEventListener('click', () => {
          helpModal.classList.remove('visible');
          setTimeout(() => {
            if (helpModal.parentNode) {
              helpModal.parentNode.removeChild(helpModal);
            }
          }, 300);
        });

        helpModal.addEventListener('click', (e) => {
          if (e.target === helpModal) {
            closeBtn.click();
          }
        });
      });
    }
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      initTooltips();
      initHelpOverlay();
      initToolPageHelp();
    });
  } else {
    initTooltips();
    initHelpOverlay();
    initToolPageHelp();
  }
})();

