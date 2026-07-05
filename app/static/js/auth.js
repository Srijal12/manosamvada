/**
 * Manosamvada — Auth Interaction Enhancements
 * Client-side password strength hinting and OTP input auto-formatting.
 * Server-side validation remains the source of truth for security.
 */

(function () {
  "use strict";

  const passwordInput = document.getElementById("password");
  const strengthHint = document.getElementById("password-strength-hint");

  function scorePassword(pw) {
    let score = 0;
    if (pw.length >= 8) score++;
    if (/[A-Z]/.test(pw)) score++;
    if (/[a-z]/.test(pw)) score++;
    if (/\d/.test(pw)) score++;
    if (/[!@#$%^&*(),.?":{}|<>]/.test(pw)) score++;
    return score;
  }

  if (passwordInput && strengthHint) {
    passwordInput.addEventListener("input", () => {
      const score = scorePassword(passwordInput.value);
      const labels = ["Very weak", "Weak", "Fair", "Good", "Strong", "Excellent"];
      strengthHint.textContent = passwordInput.value
        ? `Password strength: ${labels[score]}`
        : "";
    });
  }

  const otpInput = document.getElementById("otp");
  if (otpInput) {
    otpInput.addEventListener("input", () => {
      otpInput.value = otpInput.value.replace(/\D/g, "").slice(0, 6);
    });
    otpInput.focus();
  }
})();
