// Set hero text immediately (before DOMContentLoaded) for low-end devices
(function() {
  if (typeof window === 'undefined') return;
  const isToolPage = window.location.pathname.includes('/tools/');
  if (!isToolPage) {
    const typingNodes = document.querySelectorAll('.typing-text');
    typingNodes.forEach(node => {
      if (!node.textContent.trim()) {
        node.textContent = "Tools that just work.";
      }
    });
  }
})();

document.addEventListener('DOMContentLoaded', () => {
  // Skip expensive animations on tool pages for better performance
  const isToolPage = window.location.pathname.includes('/tools/');
  const prefersReducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const enableParallax = false;

  if (isToolPage) {
    const nav = document.querySelector('.nav');
    if (nav) {
      nav.style.display = 'none';
    }
  // Utility: truncate text nicely with ellipsis
  function truncateText(text, max) {
    if (!text) return '';
    if (text.length <= max) return text;
    const head = Math.max(0, max - 1); // reserve 1 for ellipsis
    return text.slice(0, head) + '…';
  }

  // Globally enhance file inputs across tools: show truncated filename next to input
  const fileInputs = Array.from(document.querySelectorAll('.tool-body input[type="file"]'));
  fileInputs.forEach((inp) => {
    const max = Number(inp.getAttribute('data-max-chars') || 20);
    let label = inp.nextElementSibling && inp.nextElementSibling.classList && inp.nextElementSibling.classList.contains('filename')
      ? inp.nextElementSibling
      : null;
    if (!label) {
      label = document.createElement('span');
      label.className = 'filename truncate';
      label.style.marginLeft = '8px';
      inp.insertAdjacentElement('afterend', label);
    }
    function applyName() {
      const file = inp.files && inp.files[0];
      const name = file ? file.name : '';
      label.title = name;
      label.textContent = truncateText(name, max);
    }
    inp.addEventListener('change', applyName);
    applyName();
  });
  }

  // Typewriter effect for hero title - deferred to not block initial render
  const typeWriter = () => {
    const text = "Tools that just work.";
    const typingNodes = Array.from(document.querySelectorAll('.typing-text'));
    if (!typingNodes.length) return;
    
    // Check if text is already set (e.g., when returning from tool page)
    const alreadyHasText = typingNodes.some(node => node.textContent.trim().length > 0);
    if (alreadyHasText) return; // Don't re-animate if text is already there
    
    typingNodes.forEach(node => node.textContent = '');
    let i = 0;
    
    // Start typing after a short delay
    setTimeout(() => {
      const typeInterval = setInterval(() => {
        if (i < text.length) {
          typingNodes.forEach(node => node.innerHTML += text.charAt(i));
          i++;
        } else {
          clearInterval(typeInterval);
          // After finished, keep subtitles visible in case animation was skipped
          const subtitles = document.querySelectorAll('.hero-subtitle');
          subtitles.forEach(el => el.style.opacity = '1');
        }
      }, 80); // Adjust speed here (lower = faster)
    }, 500);
  };
  
  // Initialize text immediately if not already set (for performance and when returning)
  const typingNodes = Array.from(document.querySelectorAll('.typing-text'));
  if (typingNodes.length && !isToolPage) {
    typingNodes.forEach(node => {
      if (!node.textContent.trim()) {
        // Set text immediately, then optionally animate
        node.textContent = "Tools that just work.";
      }
    });
  }
  
  // Defer typewriter effect until page is interactive or idle
  const startTypewriter = () => {
    if (document.readyState === 'complete') {
      // Use requestIdleCallback if available, otherwise setTimeout
      if ('requestIdleCallback' in window) {
        requestIdleCallback(typeWriter, { timeout: 2000 });
      } else {
        setTimeout(typeWriter, 1000);
      }
    } else {
      window.addEventListener('load', () => {
        if ('requestIdleCallback' in window) {
          requestIdleCallback(typeWriter, { timeout: 2000 });
        } else {
          setTimeout(typeWriter, 1000);
        }
      });
    }
  };
  
  // Start typewriter effect (deferred) - skip on tool pages
  if (!isToolPage) {
    startTypewriter();
  }
  
  // Parallax mesh effect (disabled by default to reduce GPU load) - skip on tool pages
  const meshLayer = document.querySelector('.bg-mesh');
  if (meshLayer && !prefersReducedMotion && enableParallax) {
    let pending = false;
    let targetX = 0;
    let targetY = 0;
    function applyParallax() {
      const xOffset = (targetX - 0.5) * 30;
      const yOffset = (targetY - 0.5) * 30;
      meshLayer.style.transform = `translate(${xOffset}px, ${yOffset}px) scale(1.05)`;
      pending = false;
    }
    function queueUpdate(x, y) {
      targetX = x;
      targetY = y;
      if (!pending) {
        pending = true;
        requestAnimationFrame(applyParallax);
      }
    }
    document.addEventListener('mousemove', (e) => {
      queueUpdate(e.clientX / window.innerWidth, e.clientY / window.innerHeight);
    });
    
    // Reset position when mouse leaves window
    document.addEventListener('mouseleave', () => {
      meshLayer.style.transform = 'translate(0px, 0px) scale(1)';
    });
    
    // Touch support for mobile devices
    document.addEventListener('touchmove', (e) => {
      const touch = e.touches[0];
      queueUpdate(touch.clientX / window.innerWidth, touch.clientY / window.innerHeight);
    });
    
    // Reset on touch end
    document.addEventListener('touchend', () => {
      meshLayer.style.transform = 'translate(0px, 0px) scale(1)';
    });
  }

  // Optimized reveal animations - single observer with higher threshold
  // Skip expensive animations on tool pages
  if (!isToolPage && 'IntersectionObserver' in window) {
    // Combined observer for better performance - higher threshold, larger rootMargin
    const revealObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          // Unobserve after animation to reduce overhead (for one-time animations)
          if (!entry.target.classList.contains('glass-card')) {
            revealObserver.unobserve(entry.target);
          }
        } else {
          // Only remove visible class for cards that need to re-animate
          if (entry.target.classList.contains('glass-card') && entry.target.style.display !== 'none') {
            entry.target.classList.remove('visible');
          }
        }
      });
    }, {
      threshold: 0.15, // Increased from 0.05/0.1 to reduce callbacks
      rootMargin: '50px 0px 50px 0px' // Larger margin for earlier but less frequent triggers
    });

    // Card reveal animations
    const cards = document.querySelectorAll('.glass-card');
    cards.forEach((card) => {
      card.style.transitionDelay = '0ms';
      // Ensure cards are visible immediately if they're already in viewport
      if (card.getBoundingClientRect().top < window.innerHeight) {
        card.classList.add('visible');
        card.style.opacity = '1';
        card.style.transform = 'translateY(0)';
      }
      revealObserver.observe(card);
    });

    // General reveal animations for other elements
    const animatedSelectors = '.reveal, .cards-grid, .tool-list, .tool-item, .tool-card, .toolbar, .advanced-controls, .preview, .result, .results, .panel, .editor-container';
    const revealEls = document.querySelectorAll(animatedSelectors);
    revealEls.forEach((el) => {
      el.classList.add('reveal');
      // Ensure elements are visible immediately if they're already in viewport
      if (el.getBoundingClientRect().top < window.innerHeight) {
        el.classList.add('visible');
        if (el.classList.contains('cards-grid')) {
          el.style.opacity = '1';
          el.style.transform = 'translateY(0)';
        }
      }
      revealObserver.observe(el);
    });
  } else {
    // Fallback for browsers without IntersectionObserver
    const cards = document.querySelectorAll('.glass-card');
    cards.forEach((card) => card.classList.add('visible'));
    const animatedSelectors = '.reveal, .cards-grid, .tool-card, .toolbar, .advanced-controls, .preview, .result, .results, .panel, .editor-container';
    const revealEls = document.querySelectorAll(animatedSelectors);
    revealEls.forEach((el) => {
      el.classList.add('reveal');
      el.classList.add('visible');
    });
  }

  // Nav background and hide-on-scroll behavior - skip on tool pages for performance
  const nav = document.querySelector('.nav');
  if (nav && !isToolPage) {
    let lastY = window.scrollY;
    let ticking = false;
    function onScroll() {
      const y = window.scrollY;
      // Background adjustment
      nav.style.background = y > 8 ? 'rgba(29, 29, 31, 0.72)' : 'rgba(29, 29, 31, 0.6)';
      
      // Check if search is focused to prevent hiding while typing
      const searchInput = document.querySelector('.nav-search input');
      const isSearchFocused = searchInput && document.activeElement === searchInput;

      // Hide when scrolling down, show when scrolling up
      if (y > lastY && y > 120 && !isSearchFocused) {
        nav.classList.add('nav--hidden');
      } else {
        nav.classList.remove('nav--hidden');
      }
      lastY = y;
      ticking = false;
    }
    window.addEventListener('scroll', () => {
      if (!ticking) {
        window.requestAnimationFrame(onScroll);
        ticking = true;
      }
    });
  }

  // Hide scroll indicator when scrolling down - skip on tool pages
  const scrollIndicator = document.querySelector('.scroll-indicator');
  if (scrollIndicator && !isToolPage) {
    window.addEventListener('scroll', () => {
      const currentScrollY = window.scrollY;
      const fadeThreshold = 100;
      
      if (currentScrollY > fadeThreshold) {
        const opacity = Math.max(0, 1 - ((currentScrollY - fadeThreshold) / 200));
        scrollIndicator.style.opacity = opacity;
      } else {
        scrollIndicator.style.opacity = 1;
      }
    });
  }

  // Pause particle animations during scroll to reduce GPU spikes - skip on tool pages
  const floatingParticles = Array.from(document.querySelectorAll('.floating-particle'));
  if (floatingParticles.length && !isToolPage) {
    let resumeTimeout;
    function pauseParticles() {
      floatingParticles.forEach(p => p.style.animationPlayState = 'paused');
      clearTimeout(resumeTimeout);
      resumeTimeout = setTimeout(() => {
        floatingParticles.forEach(p => p.style.animationPlayState = 'running');
      }, 200);
    }
    window.addEventListener('scroll', pauseParticles, { passive: true });
  }
});

// Service Worker Update Notification
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').then(reg => {
      if (reg.waiting) showUpdateToast(reg.waiting);
      
      reg.addEventListener('updatefound', () => {
        const newWorker = reg.installing;
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            showUpdateToast(newWorker);
          }
        });
      });
    });
  });

  let refreshing = false;
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (!refreshing) {
      refreshing = true;
      window.location.reload();
    }
  });
}

function showUpdateToast(worker) {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  if (document.querySelector('.toast-update')) return;

  const toast = document.createElement('div');
  toast.className = 'toast toast-info toast-update';
  toast.innerHTML = `
    <div class="toast-icon">🔄</div>
    <div class="toast-message">New update available</div>
    <button class="update-btn" style="background:rgba(255,255,255,0.1); color:inherit; border:1px solid rgba(255,255,255,0.3); padding:4px 12px; border-radius:6px; font-size:12px; font-weight:600; cursor:pointer; margin-left:auto; transition:background 0.2s;">Update</button>
  `;
  
  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('visible'));
  
  const btn = toast.querySelector('.update-btn');
  btn.addEventListener('click', () => {
    btn.textContent = 'Updating...';
    worker.postMessage({ type: 'SKIP_WAITING' });
  });
}
