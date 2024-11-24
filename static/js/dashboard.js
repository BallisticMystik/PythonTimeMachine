document.addEventListener('DOMContentLoaded', function() {
    const resetButton = document.getElementById('reset-button');
    resetButton.addEventListener('click', function() {
      if (confirm('Are you sure you want to reset your application state?')) {
        fetch('/reset', { method: 'POST' })
          .then(response => response.json())
          .then(data => {
            if (data.status === 'success') {
              alert('Application state reset successfully!');
              location.reload();
            } else {
              alert('Failed to reset application state.');
            }
          })
          .catch(error => console.error('Error:', error));
      }
    });
  });