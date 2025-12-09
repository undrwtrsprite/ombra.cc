// Performance utilities for tool pages
(function() {
  'use strict';

  // Debounce function for input handlers
  window.debounce = function(func, wait = 150) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  };

  // Throttle function for frequent events
  window.throttle = function(func, limit = 100) {
    let inThrottle;
    return function(...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  };

  // RequestAnimationFrame wrapper for DOM updates
  window.rafUpdate = function(callback) {
    if (window.requestAnimationFrame) {
      requestAnimationFrame(callback);
    } else {
      setTimeout(callback, 16);
    }
  };

  // Button loading state management
  window.setButtonLoading = function(button, loading = true, originalText = null) {
    if (!button) return;
    
    if (loading) {
      if (!originalText) {
        button.dataset.originalText = button.textContent;
      }
      button.disabled = true;
      button.dataset.loading = 'true';
      button.textContent = button.dataset.loadingText || 'Processing...';
    } else {
      button.disabled = false;
      button.removeAttribute('data-loading');
      button.textContent = button.dataset.originalText || originalText || button.textContent;
    }
  };

  // Optimized DOM update helper
  window.batchDOMUpdates = function(updates) {
    rafUpdate(() => {
      updates.forEach(update => update());
    });
  };

  // Prevent multiple rapid clicks
  window.preventDoubleClick = function(button, handler) {
    let isProcessing = false;
    button.addEventListener('click', async (e) => {
      if (isProcessing) {
        e.preventDefault();
        return;
      }
      isProcessing = true;
      try {
        await handler(e);
      } finally {
        setTimeout(() => {
          isProcessing = false;
        }, 300);
      }
    });
  };

  // Optimize large text operations with chunking
  window.chunkedOperation = function(items, chunkSize, operation, onProgress) {
    return new Promise((resolve) => {
      let index = 0;
      const results = [];
      
      function processChunk() {
        const chunk = items.slice(index, index + chunkSize);
        chunk.forEach(item => results.push(operation(item)));
        index += chunkSize;
        
        if (onProgress) {
          onProgress(index, items.length);
        }
        
        if (index < items.length) {
          rafUpdate(processChunk);
        } else {
          resolve(results);
        }
      }
      
      processChunk();
    });
  };
})();

