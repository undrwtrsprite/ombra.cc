// Drawer-style modal system for ombra tools
(function() {
  'use strict';

  let activeDrawer = null;
  let focusableElements = [];
  let previousActiveElement = null;

  // Calculate scrollbar width to prevent layout shift
  function getScrollbarWidth() {
    return window.innerWidth - document.documentElement.clientWidth;
  }

  // Get focusable elements within drawer
  function getFocusableElements(drawer) {
    const selector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
    return Array.from(drawer.querySelectorAll(selector)).filter(el => {
      return !el.disabled && el.offsetParent !== null;
    });
  }

  // Trap focus within drawer
  function trapFocus(e) {
    if (!activeDrawer || !activeDrawer.classList.contains('visible')) return;

    const focusable = focusableElements;
    if (focusable.length === 0) return;

    const firstElement = focusable[0];
    const lastElement = focusable[focusable.length - 1];

    if (e.key === 'Tab') {
      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    }
  }

  // Open drawer
  function openDrawer(drawer, options = {}) {
    if (activeDrawer) {
      closeDrawer();
    }

    activeDrawer = drawer;
    previousActiveElement = document.activeElement;

    // Determine position
    let position = options.position || drawer.dataset.position || 'bottom';

    // Remove any existing position classes to prevent conflicts
    const existingClasses = Array.from(drawer.classList).filter(c => c.startsWith('drawer-') && c !== 'drawer');
    existingClasses.forEach(c => drawer.classList.remove(c));

    drawer.classList.add(`drawer-${position}`);
    
    // Force reflow to ensure start position is applied before transition
    void drawer.offsetWidth;
    
    drawer.classList.add('visible');

    // Prevent body scroll and handle layout shift
    const scrollbarWidth = getScrollbarWidth();
    if (scrollbarWidth > 0) {
      document.body.style.paddingRight = `${scrollbarWidth}px`;
      const nav = document.querySelector('.nav');
      if (nav) {
        nav.style.marginLeft = `-${scrollbarWidth / 2}px`;
      }
    }
    document.body.style.overflow = 'hidden';

    // Get focusable elements
    focusableElements = getFocusableElements(drawer);

    // Focus first element or close button
    const closeBtn = drawer.querySelector('.drawer-close');
    const firstFocusable = focusableElements[0] || closeBtn;
    if (firstFocusable) {
      setTimeout(() => firstFocusable.focus(), 100);
    }

    // Add event listeners
    document.addEventListener('keydown', trapFocus);
    document.addEventListener('keydown', handleDrawerEscape);

    // Trigger open event
    drawer.dispatchEvent(new CustomEvent('drawer:open'));
  }

  // Close drawer
  function closeDrawer() {
    if (!activeDrawer) return;

    const drawerToClose = activeDrawer;

    // Clean up inline styles from drag interactions immediately
    // so CSS transitions can take over for the closing animation
    const drawerContent = activeDrawer.querySelector('.drawer-content, .modal-card');
    if (drawerContent) {
      drawerContent.style.transform = '';
      drawerContent.style.transition = '';
    }
    activeDrawer.style.opacity = '';

    activeDrawer.classList.remove('visible');

    // Restore body scroll
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
    const nav = document.querySelector('.nav');
    if (nav) {
      nav.style.marginLeft = '';
    }

    // Remove event listeners
    document.removeEventListener('keydown', trapFocus);
    document.removeEventListener('keydown', handleDrawerEscape);

    // Restore focus
    if (previousActiveElement) {
      previousActiveElement.focus();
    }

    // Trigger close event
    activeDrawer.dispatchEvent(new CustomEvent('drawer:close'));

    // Clean up after animation
    setTimeout(() => {
      if (drawerToClose) {
        const classes = Array.from(drawerToClose.classList);
        const drawerClass = classes.find(c => c.startsWith('drawer-') && c !== 'drawer');
        if (drawerClass) drawerToClose.classList.remove(drawerClass);
      }
      
      if (activeDrawer === drawerToClose) {
        activeDrawer = null;
        focusableElements = [];
        previousActiveElement = null;
      }
    }, 300);
  }

  // Handle Escape key
  function handleDrawerEscape(e) {
    if (e.key === 'Escape' && activeDrawer && activeDrawer.classList.contains('visible')) {
      closeDrawer();
    }
  }

  // Initialize drawer system
  function initDrawerSystem() {
    // Convert existing modals to drawers
    const existingModals = document.querySelectorAll('.modal-overlay');
    existingModals.forEach(modal => {
      modal.classList.add('drawer');
      
      // Add close button if missing
      if (!modal.querySelector('.drawer-close, .modal-close')) {
        const closeBtn = document.createElement('button');
        closeBtn.className = 'drawer-close';
        closeBtn.setAttribute('aria-label', 'Close');
        closeBtn.innerHTML = '×';
        const modalCard = modal.querySelector('.modal-card, .drawer-content');
        if (modalCard) {
          modalCard.insertBefore(closeBtn, modalCard.firstChild);
        }
      }

      // Update close button handlers
      const closeBtn = modal.querySelector('.drawer-close, .modal-close');
      if (closeBtn) {
        closeBtn.addEventListener('click', () => closeDrawer());
      }

      // Backdrop click to close
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          closeDrawer();
        }
      });
    });

    // Drag-to-dismiss on mobile
    initDragToDismiss();
  }

  // Drag-to-dismiss for mobile
  function initDragToDismiss() {
    let startY = 0;
    let currentY = 0;
    let isDragging = false;

    document.addEventListener('touchstart', (e) => {
      if (!activeDrawer || !activeDrawer.classList.contains('visible')) return;
      
      const touch = e.touches[0];
      const drawerContent = activeDrawer.querySelector('.drawer-content, .modal-card');
      
      // Only allow drag if we are at the top of the content to avoid conflict with internal scrolling
      if (drawerContent && drawerContent.scrollTop > 0) {
        return;
      }

      if (drawerContent && drawerContent.contains(e.target)) {
        startY = touch.clientY;
        isDragging = true;
      }
    }, { passive: true });

    document.addEventListener('touchmove', (e) => {
      if (!isDragging || !activeDrawer) return;
      
      const touch = e.touches[0];
      currentY = touch.clientY;
      const deltaY = currentY - startY;
      
      // Only allow downward drag
      if (deltaY > 0) {
        const drawerContent = activeDrawer.querySelector('.drawer-content, .modal-card');
        if (drawerContent) {
          drawerContent.style.transform = `translateY(${deltaY}px)`;
          drawerContent.style.transition = 'none';
          
          // Add opacity fade
          const opacity = Math.max(0, 1 - (deltaY / 300));
          activeDrawer.style.opacity = opacity;
        }
      }
    }, { passive: true });

    document.addEventListener('touchend', () => {
      if (!isDragging || !activeDrawer) return;
      
      isDragging = false;
      const drawerContent = activeDrawer.querySelector('.drawer-content, .modal-card');
      
      if (drawerContent) {
        const deltaY = currentY - startY;
        
        // If dragged more than 100px, close drawer
        if (deltaY > 100) {
          closeDrawer();
        } else {
          // Snap back
          drawerContent.style.transform = '';
          drawerContent.style.transition = '';
          activeDrawer.style.opacity = '';
        }
      }
      
      startY = 0;
      currentY = 0;
    });
  }

  // Public API
  window.Modal = {
    open: openDrawer,
    close: closeDrawer,
    init: initDrawerSystem
  };

  // Auto-initialize
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDrawerSystem);
  } else {
    initDrawerSystem();
  }
})();
