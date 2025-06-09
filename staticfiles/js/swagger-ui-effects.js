// Advanced interactive effects for Swagger UI

document.addEventListener('DOMContentLoaded', function() {
  // Wait for Swagger UI to fully load
  const checkSwaggerUI = setInterval(() => {
    if (document.querySelector('.swagger-ui')) {
      clearInterval(checkSwaggerUI);
      initCustomEffects();
    }
  }, 100);
});

function initCustomEffects() {
  // Add tooltip animation
  addTooltipEffects();
  
  // Add endpoint highlight effects
  addEndpointHighlights();
  
  // Add method badge effects
  addMethodBadgeEffects();
  
  // Add expanding effects for descriptions
  addDescriptionExpanders();
  
  // Add interaction observer for operations
  observeOperationExpansion();
  
  // Enhance try it out buttons
  enhanceTryItOutButtons();
  
  // Fix parameter visibility
  enhanceParameterSections();
}

function addTooltipEffects() {
  // Create a tooltip element
  const tooltip = document.createElement('div');
  tooltip.className = 'custom-tooltip';
  tooltip.style.cssText = `
    position: absolute;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 5px 10px;
    border-radius: 4px;
    font-size: 12px;
    z-index: 1000;
    opacity: 0;
    transition: opacity 0.3s, transform 0.3s;
    pointer-events: none;
    transform: translateY(10px);
    max-width: 200px;
  `;
  document.body.appendChild(tooltip);
  
  // Add tooltips to HTTP method badges
  document.querySelectorAll('.opblock-summary-method').forEach(method => {
    const methodType = method.textContent.trim();
    let description = '';
    
    switch (methodType) {
      case 'GET':
        description = 'Retrieve resource(s) - Safe, Idempotent';
        break;
      case 'POST':
        description = 'Create a new resource - Not Idempotent';
        break;
      case 'PUT':
        description = 'Update/Replace a resource - Idempotent';
        break;
      case 'DELETE':
        description = 'Remove a resource - Idempotent';
        break;
      case 'PATCH':
        description = 'Partially update a resource - Not Idempotent';
        break;
      default:
        description = methodType;
    }
    
    method.addEventListener('mouseenter', e => {
      tooltip.textContent = description;
      tooltip.style.opacity = '1';
      tooltip.style.transform = 'translateY(0)';
      
      const rect = e.target.getBoundingClientRect();
      tooltip.style.left = `${rect.left}px`;
      tooltip.style.top = `${rect.bottom + 5}px`;
    });
    
    method.addEventListener('mouseleave', () => {
      tooltip.style.opacity = '0';
      tooltip.style.transform = 'translateY(10px)';
    });
  });
}

function addEndpointHighlights() {
  // Add hover effect to entire endpoint row
  document.querySelectorAll('.opblock-summary').forEach(endpoint => {
    endpoint.addEventListener('mouseenter', () => {
      endpoint.style.backgroundColor = 'rgba(0, 0, 0, 0.03)';
    });
    
    endpoint.addEventListener('mouseleave', () => {
      endpoint.style.backgroundColor = '';
    });
  });
}

function addMethodBadgeEffects() {
  // Add pulse effect when clicking method badges
  document.querySelectorAll('.opblock-summary-method').forEach(method => {
    method.addEventListener('click', (e) => {
      // Prevent the default expansion behavior
      e.stopPropagation();
      
      // Add animation class
      method.classList.add('pulse-animation');
      
      // Trigger the parent click to expand
      setTimeout(() => {
        method.parentElement.click();
      }, 200);
      
      // Remove animation class
      setTimeout(() => {
        method.classList.remove('pulse-animation');
      }, 1000);
    });
  });
  
  // Add the pulse animation CSS
  const style = document.createElement('style');
  style.textContent = `
    @keyframes pulse-animation {
      0% { transform: scale(1); }
      50% { transform: scale(1.15); }
      100% { transform: scale(1); }
    }
    
    .pulse-animation {
      animation: pulse-animation 0.5s ease-out;
    }
  `;
  document.head.appendChild(style);
}

function addDescriptionExpanders() {
  // Make parameter descriptions expand smoothly
  const style = document.createElement('style');
  style.textContent = `
    .swagger-ui .markdown p {
      transition: max-height 0.5s ease-in-out, opacity 0.5s ease-in-out;
      max-height: 100px;
      overflow: hidden;
    }
    
    .swagger-ui .markdown p:hover {
      max-height: 500px;
    }
  `;
  document.head.appendChild(style);
}

function observeOperationExpansion() {
  // Add slide-down effect when expanding operations
  const observer = new MutationObserver(mutations => {
    mutations.forEach(mutation => {
      if (mutation.type === 'childList' && mutation.addedNodes.length) {
        // Find newly expanded operation content
        const opblockWrappers = document.querySelectorAll('.opblock-body');
        opblockWrappers.forEach(wrapper => {
          if (!wrapper.classList.contains('animated-in')) {
            wrapper.classList.add('animated-in');
            wrapper.style.animation = 'slideDown 0.4s ease-in-out';
          }
        });
        
        // If new operations are expanded, enhance try it out and parameters sections
        enhanceTryItOutButtons();
        enhanceParameterSections();
      }
    });
  });
  
  // Add the slide-down animation CSS
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideDown {
      from { opacity: 0; transform: translateY(-20px); }
      to { opacity: 1; transform: translateY(0); }
    }
  `;
  document.head.appendChild(style);
  
  // Start observing
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
}

function enhanceTryItOutButtons() {
  // Find all Try it out buttons and enhance them
  setTimeout(() => {
    document.querySelectorAll('.try-out__btn').forEach(btn => {
      if (!btn.classList.contains('enhanced')) {
        btn.classList.add('enhanced');
        
        // Add pulsing animation to make it more visible
        const pulseAnimation = document.createElement('span');
        pulseAnimation.className = 'btn-pulse';
        pulseAnimation.style.cssText = `
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          border-radius: 4px;
          background-color: transparent;
          border: 2px solid #2196f3;
          opacity: 0;
          pointer-events: none;
        `;
        btn.style.position = 'relative';
        btn.appendChild(pulseAnimation);
        
        // Add animation keyframes
        const btnStyle = document.createElement('style');
        btnStyle.textContent = `
          @keyframes btnPulse {
            0% { opacity: 0.8; transform: scale(1); }
            100% { opacity: 0; transform: scale(1.2); }
          }
          
          .swagger-ui .try-out__btn:hover .btn-pulse {
            animation: btnPulse 1.5s ease-out infinite;
          }
        `;
        document.head.appendChild(btnStyle);
        
        // Add tooltip to explain what Try it out does
        btn.setAttribute('title', 'Enable interactive testing of this endpoint');
      }
    });
    
    // Also enhance Execute buttons
    document.querySelectorAll('.execute').forEach(btn => {
      if (!btn.classList.contains('enhanced')) {
        btn.classList.add('enhanced');
        btn.setAttribute('title', 'Send the request with the parameters you specified');
      }
    });
  }, 500);
}

function enhanceParameterSections() {
  // Enhance parameter sections to make them more visible
  setTimeout(() => {
    document.querySelectorAll('.parameters-container').forEach(container => {
      if (!container.classList.contains('enhanced')) {
        container.classList.add('enhanced');
        
        // Add a header if none exists
        if (!container.querySelector('.parameters-container-header')) {
          const header = document.createElement('div');
          header.className = 'parameters-container-header';
          header.innerHTML = `
            <h4 style="color: #2196f3; margin-bottom: 15px; font-weight: bold;">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 4V20M4 12H20"/>
              </svg>
              Parameters
            </h4>
          `;
          container.insertBefore(header, container.firstChild);
        }
        
        // Highlight parameter rows on hover
        container.querySelectorAll('tr').forEach(row => {
          row.style.transition = 'background-color 0.3s ease';
          row.addEventListener('mouseenter', () => {
            row.style.backgroundColor = 'rgba(33, 150, 243, 0.1)';
          });
          row.addEventListener('mouseleave', () => {
            row.style.backgroundColor = '';
          });
        });
      }
    });
    
    // Fix parameter tables by adding highlighting
    document.querySelectorAll('.parameter__name').forEach(name => {
      if (!name.classList.contains('enhanced')) {
        name.classList.add('enhanced');
        name.style.fontWeight = 'bold';
        name.style.color = '#e0e0e0';
      }
    });
  }, 500);
} 