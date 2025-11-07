document.addEventListener('DOMContentLoaded', function() {
    var form = document.getElementById('contactForm');
    form.addEventListener('submit', function(event) {
      event.preventDefault();

    var nameInput = document.getElementById('name');
    var nameError = document.getElementById('nameError');

    var mailInput = document.getElementById('email');
    var mailError = document.getElementById('emailError');    
    
    var phoneInput = document.getElementById('phone');
    var phoneError = document.getElementById('phoneError');
    
    var messageInput = document.getElementById('message');
    var messageError = document.getElementById('messageError');

    if (nameInput.value.trim() === '') {
      // Il campo email è vuoto o il formato non è corretto
      nameError.style.display = 'block';  // Rendi visibile il messaggio di errore
      event.preventDefault();  // Impedisci l'invio del modulo
      return
    }

    if (mailInput.value.trim() === '' || !isValidEmail(mailInput.value)) {
      // Il campo email è vuoto o il formato non è corretto
      mailError.style.display = 'block';  // Rendi visibile il messaggio di errore
      event.preventDefault();  // Impedisci l'invio del modulo
      return
    }

    if (phoneInput.value.trim() === '') {
      // Il campo email è vuoto o il formato non è corretto
      phoneError.style.display = 'block';  // Rendi visibile il messaggio di errore
      event.preventDefault();  // Impedisci l'invio del modulo
      return
    }
    
    if (messageInput.value.trim() === '') {
      // Il campo email è vuoto o il formato non è corretto
      messageError.style.display = 'block';  // Rendi visibile il messaggio di errore
      event.preventDefault();  // Impedisci l'invio del modulo
      return
    }
      sendEmail();
    });
  });
  
  function isValidEmail(email) {
    // Utilizza una semplice espressione regolare per la verifica di base
    var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  function sendEmail() {
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value
    const phone = document.getElementById('phone').value
    const message = document.getElementById('message').value

    var templateParams = {
        from_name: name,
        email_address: email,
        phone_number: phone,
        message_text: message
    };
  
    emailjs.send('service_qqf6ue8', 'template_7uaevp8', templateParams, 'FyPzH-nywzRayqi4L')
      .then(function(response) {
        console.log('Email sent successfully!', response.status, response.text);
        // Reset the form fields after successful submission if needed
        document.getElementById('contactForm').reset();
        document.getElementById('submitSuccessMessage').display = 'block';
        
      }, function(error) {
        console.error('Error sending email:', error);
        document.getElementById('submitErrorMessage').display = 'block';
      });
  }