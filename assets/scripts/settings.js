// Settings management for ombra tools
(function() {
  'use strict';

  function initSettings() {
    const motionToggle = document.getElementById('motionToggle');
    const clearDataBtn = document.getElementById('clearDataBtn');

    // --- Motion Handling ---
    const savedMotion = localStorage.getItem('ombra-motion');
    const systemPrefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    // Check if body already has the class (e.g. from low-power mode script in index.html)
    const bodyHasReducedClass = document.body.classList.contains('reduce-effects');
    
    let reduceMotion = false;
    
    if (savedMotion === 'reduce') {
      reduceMotion = true;
    } else if (savedMotion === 'no-preference') {
      reduceMotion = false;
    } else {
      // No user preference saved: use system preference or existing class (low power mode)
      reduceMotion = systemPrefersReduced || bodyHasReducedClass;
    }

    // Apply final state
    if (reduceMotion) {
      document.body.classList.add('reduce-effects');
    } else {
      document.body.classList.remove('reduce-effects');
    }

    if (motionToggle) {
      motionToggle.checked = reduceMotion;
      
      motionToggle.addEventListener('change', (e) => {
        if (e.target.checked) {
          document.body.classList.add('reduce-effects');
          localStorage.setItem('ombra-motion', 'reduce');
        } else {
          document.body.classList.remove('reduce-effects');
          localStorage.setItem('ombra-motion', 'no-preference');
        }
      });
    }

    // --- Clear Data ---
    if (clearDataBtn) {
      clearDataBtn.addEventListener('click', () => {
        if (confirm('Are you sure you want to clear all local data? This will reset your settings and tool history.')) {
          localStorage.clear();
          sessionStorage.clear();
          window.location.reload();
        }
      });
    }
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSettings);
  } else {
    initSettings();
  }

  // Listen for system preference changes (only if no manual override)
  window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
    if (!localStorage.getItem('ombra-motion')) {
      const motionToggle = document.getElementById('motionToggle');
      if (e.matches) {
        document.body.classList.add('reduce-effects');
        if (motionToggle) motionToggle.checked = true;
      } else {
        document.body.classList.remove('reduce-effects');
        if (motionToggle) motionToggle.checked = false;
      }
    }
  });

})();