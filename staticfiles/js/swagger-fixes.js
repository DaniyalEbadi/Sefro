// Wait for Swagger UI to be fully loaded
window.addEventListener('load', function() {
    // Add a timestamp to indicate when documentation was last viewed
    setTimeout(function() {
        const infoContainer = document.querySelector('.swagger-ui .info');
        if (infoContainer) {
            const timestamp = document.createElement('div');
            timestamp.className = 'last-viewed';
            timestamp.style.fontSize = '12px';
            timestamp.style.color = '#999';
            timestamp.style.marginTop = '10px';
            
            const now = new Date();
            timestamp.textContent = 'Documentation viewed: ' + now.toLocaleString();
            
            infoContainer.appendChild(timestamp);
        }
    }, 1000);
    
    // Add a more visible execute button for testing endpoints
    setTimeout(function() {
        const executeButtons = document.querySelectorAll('.swagger-ui button.execute');
        executeButtons.forEach(function(button) {
            button.style.fontWeight = 'bold';
            button.style.padding = '10px 15px';
            
            const originalText = button.textContent;
            button.textContent = '▶ ' + originalText;
        });
    }, 1000);
    
    // Highlight the currently selected operation
    setTimeout(function() {
        const operations = document.querySelectorAll('.swagger-ui .opblock');
        operations.forEach(function(op) {
            op.addEventListener('click', function() {
                operations.forEach(function(o) {
                    o.style.boxShadow = 'none';
                });
                op.style.boxShadow = '0 0 10px rgba(0, 0, 0, 0.1)';
            });
        });
    }, 1000);
});

window.onload = function() {
  // Fix operation IDs with line breaks
  setTimeout(function() {
    const opIds = document.querySelectorAll('.opblock-summary-operation-id');
    opIds.forEach(function(element) {
      const text = element.textContent;
      element.textContent = text.replace(/\s+/g, '');
      
      // Apply CSS fixes
      element.style.whiteSpace = 'nowrap';
      element.style.overflow = 'hidden';
      element.style.textOverflow = 'ellipsis';
      element.style.maxWidth = '100%';
      element.style.display = 'inline-block';
    });
  }, 1000);
}; 