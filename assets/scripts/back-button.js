// Back button functionality for tool pages
(function() {
  'use strict';
  
  // Create back button element
  function createBackButton() {
    const backButton = document.createElement('button');
    backButton.className = 'back-button';
    backButton.innerHTML = '← Back';
    backButton.addEventListener('click', handleBackClick);
    return backButton;
  }

  function handleBackClick() {
    // Add exit animations to all elements
    const toolContainer = document.querySelector('.tool-container');
    const toolCard = document.querySelector('.tool-card');
    const toolHeader = document.querySelector('.tool-header');
    const toolBody = document.querySelector('.tool-body');
    
    if (toolContainer && toolCard && toolHeader && toolBody) {
      toolContainer.classList.add('exiting');
      toolCard.classList.add('exiting');
      toolHeader.classList.add('exiting');
      toolBody.classList.add('exiting');
      
      // Add a flag to trigger homepage return animation
      sessionStorage.setItem('returningFromTool', 'true');
      
      // Wait for animation to complete before going back
      setTimeout(() => {
        window.history.back();
      }, 400); // Match the CSS animation duration (0.25s + 0.15s delay)
    } else {
      // Fallback if animations aren't available
      window.history.back();
    }
  }
  
  // Add back button to the page
  function addBackButton() {
    const toolContainer = document.querySelector('.tool-container');
    if (toolContainer && !document.querySelector('.back-button')) {
      const backButton = createBackButton();
      toolContainer.insertBefore(backButton, toolContainer.firstChild);
    }
  }
  
  // Add styles for back button
  function addBackButtonStyles() {
    if (!document.getElementById('back-button-styles')) {
      const style = document.createElement('style');
      style.id = 'back-button-styles';
      style.textContent = `
        .back-button {
          position: relative;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 12px 20px;
          margin-bottom: 24px;
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 12px;
          color: #ffffff;
          font-size: 14px;
          font-weight: 500;
          text-decoration: none;
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          backdrop-filter: blur(10px);
          font-family: inherit;
        }
        
        .back-button:hover {
          background: rgba(255, 255, 255, 0.15);
          border-color: rgba(255, 255, 255, 0.3);
          transform: translateY(-1px);
        }
        
        .back-button:active {
          transform: translateY(0);
        }
        
        .back-button:focus {
          outline: 2px solid rgba(147, 51, 234, 0.5);
          outline-offset: 2px;
        }
        
        @media (max-width: 768px) {
          .back-button {
            padding: 10px 16px;
            font-size: 13px;
            margin-bottom: 20px;
          }
        }
      `;
      document.head.appendChild(style);
    }
  }
  
  // Initialize when DOM is loaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      addBackButtonStyles();
      addBackButton();
    });
  } else {
    addBackButtonStyles();
    addBackButton();
  }
})();
