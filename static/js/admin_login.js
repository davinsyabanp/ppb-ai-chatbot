/**
 * Admin Login Page JavaScript
 * Handles password visibility toggle functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    /**
     * Toggle password visibility
     * Changes input type between 'password' and 'text'
     * and updates the icon accordingly
     */
    const passwordInput = document.getElementById('password');
    const passwordToggle = document.getElementById('password-toggle');
    const passwordIcon = document.getElementById('password-icon');
    
    passwordToggle.addEventListener('click', function() {
        if (passwordInput.type === 'password') {
            // Show password
            passwordInput.type = 'text';
            passwordIcon.className = 'bi bi-eye-slash';
            passwordToggle.title = 'Hide Password';
        } else {
            // Hide password
            passwordInput.type = 'password';
            passwordIcon.className = 'bi bi-eye';
            passwordToggle.title = 'Show Password';
        }
    });
});
