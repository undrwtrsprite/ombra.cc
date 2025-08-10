document.addEventListener('DOMContentLoaded', () => {
  // Parallax mesh effect
  const meshLayer = document.querySelector('.bg-mesh');
  if (meshLayer) {
    document.addEventListener('mousemove', (e) => {
      const x = e.clientX / window.innerWidth;
      const y = e.clientY / window.innerHeight;
      const xOffset = (x - 0.5) * 30;
      const yOffset = (y - 0.5) * 30;
      meshLayer.style.transform = `translate(${xOffset}px, ${yOffset}px) scale(1.05)`;
    });
    
    // Reset position when mouse leaves window
    document.addEventListener('mouseleave', () => {
      meshLayer.style.transform = 'translate(0px, 0px) scale(1)';
    });
    
    // Touch support for mobile devices
    document.addEventListener('touchmove', (e) => {
      const touch = e.touches[0];
      const x = touch.clientX / window.innerWidth;
      const y = touch.clientY / window.innerHeight;
      const xOffset = (x - 0.5) * 20;
      const yOffset = (y - 0.5) * 20;
      meshLayer.style.transform = `translate(${xOffset}px, ${yOffset}px) scale(1.02)`;
    });
    
    // Reset on touch end
    document.addEventListener('touchend', () => {
      meshLayer.style.transform = 'translate(0px, 0px) scale(1)';
    });
  }

  // Reveal on scroll
  const revealEls = document.querySelectorAll('.reveal, .cards-grid, .glass-card');
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
    revealEls.forEach((el) => observer.observe(el));
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

  // Nav background on scroll
  const nav = document.querySelector('.nav');
  if (nav) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 50) {
        nav.style.background = 'rgba(29, 29, 31, 0.8)';
        nav.style.borderColor = 'rgba(255, 255, 255, 0.15)';
      } else {
        nav.style.background = 'rgba(29, 29, 31, 0.72)';
        nav.style.borderColor = 'rgba(255, 255, 255, 0.1)';
      }
    });
  }
});


