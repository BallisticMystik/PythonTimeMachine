document.addEventListener('DOMContentLoaded', (event) => {
    const passwordInput = document.querySelector('input[name="password"]');
    const strengthMeter = document.getElementById('password-strength-meter');
    const strengthText = document.getElementById('password-strength-text');
    
    passwordInput.addEventListener('input', () => {
      const strengths = {
        0: "Very Weak",
        1: "Weak",
       2: "Fair",
       3: "Good",
       4: "Strong"
     };
     const val = passwordInput.value;
     let score = 0;
     if (val.length > 8) score++;
     if (/[A-Z]/.test(val)) score++;
     if (/[a-z]/.test(val)) score++;
     if (/[0-9]/.test(val)) score++;
     if (/[@$!%*?&]/.test(val)) score++;
     
     strengthMeter.value = score;
     strengthText.innerText = strengths[score];
   });
  });