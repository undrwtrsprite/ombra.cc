// Settings management for ombra tools
(function() {
  'use strict';

  function applyReduceMotion(reduce) {
    if (reduce) {
      document.documentElement.classList.add('reduce-effects');
      document.body.classList.add('reduce-effects');
    } else {
      document.documentElement.classList.remove('reduce-effects');
      document.body.classList.remove('reduce-effects');
    }
  }

  function initSettings() {
    const motionToggle = document.getElementById('motionToggle');
    const clearDataBtn = document.getElementById('clearDataBtn');

    // --- Motion Handling ---
    const savedMotion = localStorage.getItem('ombra-motion');
    const systemPrefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const bodyHasReducedClass = document.body.classList.contains('reduce-effects');

    let reduceMotion = false;
    if (savedMotion === 'reduce') {
      reduceMotion = true;
    } else if (savedMotion === 'no-preference') {
      reduceMotion = false;
    } else {
      reduceMotion = systemPrefersReduced || bodyHasReducedClass;
    }

    applyReduceMotion(reduceMotion);

    if (motionToggle) {
      motionToggle.checked = reduceMotion;
      motionToggle.addEventListener('change', (e) => {
        const reduce = !!e.target.checked;
        applyReduceMotion(reduce);
        localStorage.setItem('ombra-motion', reduce ? 'reduce' : 'no-preference');
      });
    }

    // --- Clear Data ---
    if (clearDataBtn) {
      clearDataBtn.addEventListener('click', () => {
        if (!confirm('Are you sure you want to clear all local data? This will reset your settings, preferences, and tool history.')) return;
        localStorage.clear();
        sessionStorage.clear();
        if ('caches' in window && typeof caches.keys === 'function') {
          caches.keys().then(function(names) {
            return Promise.all(names.map(function(name) { return caches.delete(name); }));
          }).then(function() {
            window.location.reload();
          }).catch(function() {
            window.location.reload();
          });
        } else {
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
    if (localStorage.getItem('ombra-motion')) return;
    const motionToggle = document.getElementById('motionToggle');
    const reduce = !!e.matches;
    applyReduceMotion(reduce);
    if (motionToggle) motionToggle.checked = reduce;
  });

})();