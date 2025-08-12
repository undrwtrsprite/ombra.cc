// Back button functionality for tool pages
(function() {
  'use strict';
  
  // Create back button element
  function createBackButton() {
    const backButton = document.createElement('button');
    backButton.className = 'back-button';
    backButton.innerHTML = '← Back to Tools';
    backButton.setAttribute('aria-label', 'Go back to tools');
    
    // Add click handler
    backButton.addEventListener('click', function() {
      // Try to go back in history first, fallback to tools page
      if (window.history.length > 1) {
        window.history.back();
      } else {
        window.location.href = '/index.html#tools';
      }
    });
    
    return backButton;
  }
  
  // Add back button to the page
  function addBackButton() {
    // Check if we're on a tool page (has tool-container)
    const toolContainer = document.querySelector('.tool-container');
    if (!toolContainer) return;
    
    // Check if back button already exists
    if (document.querySelector('.back-button')) return;
    
    // Create back button
    const backButton = createBackButton();
    
    // Insert at the beginning of tool-container
    toolContainer.insertBefore(backButton, toolContainer.firstChild);
  }
  
  // Add styles for back button
  function addBackButtonStyles() {
    if (document.querySelector('#back-button-styles')) return;
    
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
        transition: all 0.2s ease;
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
  
  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      addBackButtonStyles();
      addBackButton();
    });
  } else {
    addBackButtonStyles();
    addBackButton();
  }
})();
