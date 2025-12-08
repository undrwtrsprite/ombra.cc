document.addEventListener('DOMContentLoaded', () => {
  const prefersReducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const enableParallax = false; // set true to re-enable mesh parallax
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
  // Typewriter effect for hero title
  const typeWriter = () => {
    const text = "Tools that just work.";
    const typingNodes = Array.from(document.querySelectorAll('.typing-text'));
    if (!typingNodes.length) return;
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
        }
      }, 80); // Adjust speed here (lower = faster)
    }, 500);
  };
  
  // Start typewriter effect
  typeWriter();
  
  // Parallax mesh effect (disabled by default to reduce GPU load)
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

  // Card reveal animations (faster)
  const cards = document.querySelectorAll('.glass-card');
  if ('IntersectionObserver' in window) {
    const cardObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
        } else {
          // If scrolled away and it's displayable, keep it ready to re-animate when needed
          if (entry.target.style.display !== 'none') {
            entry.target.classList.remove('visible');
          }
        }
      });
    }, {
      threshold: 0.05,
      rootMargin: '0px 0px -20px 0px'
    });

    cards.forEach((card) => {
      // remove any previous stagger to reveal immediately
      card.style.transitionDelay = '0ms';
      cardObserver.observe(card);
    });
  } else {
    cards.forEach((card) => card.classList.add('visible'));
  }

  // General reveal animations for other elements
  const animatedSelectors = '.reveal, .cards-grid, .tool-card, .toolbar, .advanced-controls, .preview, .result, .results, .panel, .editor-container';
  const revealEls = document.querySelectorAll(animatedSelectors);
  revealEls.forEach((el) => el.classList.add('reveal'));
  
  if ('IntersectionObserver' in window) {
    const generalObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
    revealEls.forEach((el) => generalObserver.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add('visible'));
  }

  // Smooth scroll for hash links
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener('click', (e) => {
      const target = document.querySelector(anchor.getAttribute('href'));
      if (!target) return;
      e.preventDefault();
      const targetPosition = target.getBoundingClientRect().top + window.pageYOffset;
      const startPosition = window.pageYOffset;
      const distance = targetPosition - startPosition;
      const duration = 900; let start = null;
      function step(currentTime) {
        if (start === null) start = currentTime;
        const timeElapsed = currentTime - start;
        const t = Math.min(timeElapsed / duration, 1);
        const ease = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
        window.scrollTo(0, startPosition + (distance * ease));
        if (timeElapsed < duration) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    });
  });

  // Nav background and hide-on-scroll behavior
  const nav = document.querySelector('.nav');
  if (nav) {
    let lastY = window.scrollY;
    let ticking = false;
    function onScroll() {
      const y = window.scrollY;
      // Background adjustment
      nav.style.background = y > 8 ? 'rgba(29, 29, 31, 0.72)' : 'rgba(29, 29, 31, 0.6)';
      // Hide when scrolling down, show when scrolling up
      if (y > lastY && y > 120) {
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

  // Hide scroll indicator when scrolling down
  const scrollIndicator = document.querySelector('.scroll-indicator');
  if (scrollIndicator) {
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

  // Pause particle animations during scroll to reduce GPU spikes
  const floatingParticles = Array.from(document.querySelectorAll('.floating-particle'));
  if (floatingParticles.length) {
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


