function cookieConsent() {
  const cookieBanner = document.getElementById('cookie-banner');
  const acceptBtn = document.getElementById('accept-btn');
  const declineBtn = document.getElementById('decline-btn');

  // Check if the user has already made a choice
  const consentCookie = getCookie('cookie_consent');
  if (consentCookie === 'true') {
    cookieBanner.style.display = 'none';
    return;
  }

  // Show the cookie consent banner
  cookieBanner.style.display = 'block';

  // Set cookies based on user's response
  acceptBtn.addEventListener('click', () => {
    setCookie('cookie_consent', 'true', 365);
    cookieBanner.style.display = 'none';
  });

  declineBtn.addEventListener('click', () => {
    setCookie('cookie_consent', 'false', 365);
    cookieBanner.style.display = 'none';
  });
}

// Helper functions for setting and getting cookies
function setCookie(name, value, days) {
  const expirationTime = days * 24 * 60 * 60 * 1000; // Convert days to milliseconds
  const expirationDate = new Date(Date.now() + expirationTime).toUTCString();
  const cookieValue = encodeURIComponent(value);
  const cookieString = `${name}=${cookieValue};expires=${expirationDate};path=/`;

  try {
    localStorage.setItem(name, cookieString);
    if (getCookie(name) === value) {
      console.log(`Cookie ${name} was successfully set with value ${value}`);
    } else {
      console.log(`Cookie ${name} was not set or did not have the expected value`);
    }
  } catch (error) {
    console.error(`Error setting cookie ${name}: ${error}`);
  }
}

function getCookie(name) {
  const cookieString = localStorage.getItem(name);
  if (cookieString) {
    var cookieValue = decodeURIComponent(cookieString.split('=')[1]);
    cookieValue = cookieValue.split(';')[0];
    return cookieValue;
  }
  return null;
}

// Check for cookie consent on page load
window.onload = function() {
  cookieConsent();
};
