// Keyboard shortcuts system for ombra tools
(function() {
  'use strict';

  let selectedCardIndex = -1;
  let cards = [];
  let shortcutsHelpVisible = false;

  // Initialize keyboard shortcuts
  function initKeyboardShortcuts() {
    // Global shortcuts
    document.addEventListener('keydown', handleGlobalShortcuts);

    // Tool card navigation (only on homepage)
    if (window.location.pathname === '/' || window.location.pathname.endsWith('index.html')) {
      initToolCardNavigation();
    }

    // Show keyboard shortcuts help
    initShortcutsHelp();
  }

  // Handle global keyboard shortcuts
  function handleGlobalShortcuts(e) {
    // Ctrl/Cmd + K: Focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      const searchInput = document.querySelector('#navSearch input[type="search"], input[type="search"]');
      if (searchInput) {
        const navSearch = document.getElementById('navSearch');
        if (navSearch) {
          navSearch.classList.remove('collapsed');
          navSearch.classList.add('expanded');
        }
        searchInput.focus();
        searchInput.select();
      }
      return;
    }

    // Escape: Close modals, drawers, help overlays
    if (e.key === 'Escape') {
      // Close help overlay
      const helpOverlay = document.getElementById('helpOverlay');
      if (helpOverlay && helpOverlay.classList.contains('visible')) {
        helpOverlay.querySelector('.help-overlay-close')?.click();
        return;
      }

      // Close help modal
      const helpModal = document.querySelector('.help-modal.visible');
      if (helpModal) {
        helpModal.querySelector('.help-modal-close')?.click();
        return;
      }

      // Close drawer/modal
      const drawer = document.querySelector('.drawer.visible, .modal-overlay[style*="flex"]');
      if (drawer) {
        const closeBtn = drawer.querySelector('.drawer-close, .modal-close');
        if (closeBtn) {
          closeBtn.click();
        } else if (window.Modal && window.Modal.close) {
          window.Modal.close();
        }
        return;
      }

      // Close shortcuts help
      if (shortcutsHelpVisible) {
        hideShortcutsHelp();
        return;
      }
    }

    // ?: Show keyboard shortcuts help
    if (e.key === '?' && !e.ctrlKey && !e.metaKey && !e.altKey) {
      const activeElement = document.activeElement;
      const isInput = activeElement && (
        activeElement.tagName === 'INPUT' ||
        activeElement.tagName === 'TEXTAREA' ||
        activeElement.isContentEditable
      );
      
      if (!isInput) {
        e.preventDefault();
        toggleShortcutsHelp();
      }
    }
  }

  // Initialize tool card navigation
  function initToolCardNavigation() {
    cards = Array.from(document.querySelectorAll('.glass-card'));
    
    if (cards.length === 0) return;

    // Remove existing selection
    function clearSelection() {
      cards.forEach(card => card.classList.remove('keyboard-selected'));
      selectedCardIndex = -1;
    }

    // Select card
    function selectCard(index) {
      if (index < 0 || index >= cards.length) return;
      
      clearSelection();
      selectedCardIndex = index;
      cards[index].classList.add('keyboard-selected');
      
      // Scroll into view
      cards[index].scrollIntoView({
        behavior: 'smooth',
        block: 'nearest'
      });
    }

    // Handle arrow key navigation
    document.addEventListener('keydown', (e) => {
      // Only handle if not in input/textarea
      const activeElement = document.activeElement;
      const isInput = activeElement && (
        activeElement.tagName === 'INPUT' ||
        activeElement.tagName === 'TEXTAREA' ||
        activeElement.isContentEditable
      );

      if (isInput) return;

      if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
        e.preventDefault();
        if (selectedCardIndex < 0) {
          selectCard(0);
        } else {
          selectCard((selectedCardIndex + 1) % cards.length);
        }
      } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
        e.preventDefault();
        if (selectedCardIndex < 0) {
          selectCard(cards.length - 1);
        } else {
          selectCard((selectedCardIndex - 1 + cards.length) % cards.length);
        }
      } else if (e.key === 'Enter' && selectedCardIndex >= 0) {
        e.preventDefault();
        cards[selectedCardIndex].click();
      } else if (e.key === 'Escape') {
        clearSelection();
      }
    });

    // Clear selection on click
    cards.forEach(card => {
      card.addEventListener('click', clearSelection);
    });
  }

  // Initialize shortcuts help
  function initShortcutsHelp() {
    // Create shortcuts help modal
    const shortcutsHelp = document.createElement('div');
    shortcutsHelp.id = 'shortcutsHelp';
    shortcutsHelp.className = 'shortcuts-help';
    shortcutsHelp.innerHTML = `
      <div class="shortcuts-help-content">
        <button class="shortcuts-help-close" aria-label="Close">×</button>
        <h2>Keyboard Shortcuts</h2>
        <div class="shortcuts-list">
          <div class="shortcut-item">
            <kbd>Ctrl</kbd> + <kbd>K</kbd>
            <span>Focus search</span>
          </div>
          <div class="shortcut-item">
            <kbd>↑</kbd> <kbd>↓</kbd> <kbd>←</kbd> <kbd>→</kbd>
            <span>Navigate tool cards</span>
          </div>
          <div class="shortcut-item">
            <kbd>Enter</kbd>
            <span>Open selected tool</span>
          </div>
          <div class="shortcut-item">
            <kbd>Esc</kbd>
            <span>Close modals/overlays</span>
          </div>
          <div class="shortcut-item">
            <kbd>?</kbd>
            <span>Show this help</span>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(shortcutsHelp);

    const closeBtn = shortcutsHelp.querySelector('.shortcuts-help-close');
    closeBtn.addEventListener('click', hideShortcutsHelp);

    shortcutsHelp.addEventListener('click', (e) => {
      if (e.target === shortcutsHelp) {
        hideShortcutsHelp();
      }
    });
  }

  // Show shortcuts help
  function showShortcutsHelp() {
    const help = document.getElementById('shortcutsHelp');
    if (help) {
      help.classList.add('visible');
      shortcutsHelpVisible = true;
    }
  }

  // Hide shortcuts help
  function hideShortcutsHelp() {
    const help = document.getElementById('shortcutsHelp');
    if (help) {
      help.classList.remove('visible');
      shortcutsHelpVisible = false;
    }
  }

  // Toggle shortcuts help
  function toggleShortcutsHelp() {
    if (shortcutsHelpVisible) {
      hideShortcutsHelp();
    } else {
      showShortcutsHelp();
    }
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initKeyboardShortcuts);
  } else {
    initKeyboardShortcuts();
  }
})();

