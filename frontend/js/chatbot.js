setConfiguration()

let chatbotWindowVisible = false;

// Open chatbot window
document.getElementById('chatbotBtn').addEventListener('click', function(e) {
    e.stopPropagation(); // Evita la propagazione dell'evento
    document.getElementById('chatbotWindow').style.display = 'block';
    document.getElementById('chatbotBtn').style.display = 'none';
    chatbotWindowVisible = true;
    runAction('/start_conversation')
  });
  
  // Close chatbot window
document.getElementById('closeChatbot').addEventListener('click', function(e) {
    e.stopPropagation(); // Evita la propagazione dell'evento
    document.getElementById('chatbotWindow').style.display = 'none';
    document.getElementById('chatbotBtn').style.display = 'block';
    chatbotWindowVisible = false;
  });

  // Aggiungi un listener per nascondere il bottone quando si clicca al di fuori della finestra del chatbot
document.addEventListener('click', function(event) {
  const chatbotWindow = document.getElementById('chatbotWindow');
  const chatbotBtn = document.getElementById('chatbotBtn');

  if (chatbotWindowVisible && event.target !== chatbotBtn && !chatbotWindow.contains(event.target)) {
    chatbotWindow.style.display = 'none';
    chatbotBtn.style.display = 'block';
    chatbotWindowVisible = false;
  }
});

// Send message
document.getElementById('chatInput').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
      handleUserInput();
    }
  });
  
document.getElementById('sendBtn').addEventListener('click', function () {
    handleUserInput();
  });
  
  async function handleUserInput() {
    const message = document.getElementById('chatInput').value;

    appendMessage('You', message);
    
    const jsonPayload = JSON.stringify({
      sender: sessionStorage.getItem("ArmandoUser"),
      message: message,
    });
    
    try {
      const response = await fetch(getUttersBackendUrl(), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonPayload,
      });

      if (!response.ok) {
        throw new Error(`Errore HTTP! Stato: ${response.status}`);
      }

      const data = await response.json();

      // Processa gli elementi di data uno alla volta
      for (const element of data) {
        if (element.text) {
          await appendMessage(getChatbotName(), convertNewlineToBreak(element.text)); // Attendi che il messaggio venga completamente visualizzato
        }

        if (element.buttons && Array.isArray(element.buttons)) {
          element.buttons.forEach(button => {
            appendActionButton(button.title, button.payload);
          });
        }

        if (element.image) {
          appendImage(element.image);
        }

        if (element.attachment) {
          appendDocument(element.attachment);
        }

        // Aggiungi un breve ritardo tra la gestione di ogni elemento, se necessario
        await new Promise(resolve => setTimeout(resolve, 100)); // facoltativo
      }
    } catch (error) {
      console.error('Errore nella richiesta:', error.message);
    }
    
    document.getElementById('chatInput').value = '';
}


async function runAction(action) {
  const jsonPayload = JSON.stringify({
    sender: sessionStorage.getItem("ArmandoUser"),
    message: action,
  });

  try {
    const response = await fetch(getUttersBackendUrl(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonPayload,
    });

    if (!response.ok) {
      throw new Error(`Errore HTTP! Stato: ${response.status}`);
    }

    const data = await response.json();
    console.log(data);

    // Processa gli elementi di data uno alla volta
    for (const element of data) {
      if (element.text) {
        await appendMessage(getChatbotName(), convertNewlineToBreak(element.text)); // Attendi che il messaggio venga completamente visualizzato
      }

      if (element.buttons && Array.isArray(element.buttons)) {
        element.buttons.forEach(button => {
          appendActionButton(button.title, button.payload);
        });
      }

      if (element.image) {
        appendImage(element.image);
      }

      if (element.attachment) {
        appendDocument(element.attachment);
      }

      // Aggiungi un breve ritardo tra la gestione di ogni elemento, se necessario
      await new Promise(resolve => setTimeout(resolve, 100)); // facoltativo
    }
  } catch (error) {
    console.error('Errore nella richiesta:', error.message);
  }
}


async function appendMessage(sender, message) {
  const chatBody = document.querySelector('.chatbot-body');
  const newMessage = document.createElement('div');
  newMessage.classList.add('mb-2');
  newMessage.classList.add('chatbot-text');

  // Creare un elemento span per visualizzare il sender
  const senderElement = document.createElement('span');
  senderElement.classList.add('sender');
  senderElement.textContent = `${sender}: `;
  newMessage.appendChild(senderElement);

  // Aggiungere un elemento span per visualizzare il testo
  const textContainer = document.createElement('span');
  newMessage.appendChild(textContainer);

  chatBody.appendChild(newMessage);

  // Funzione per visualizzare il testo con entità HTML un carattere alla volta
  function displayTextCharacterByCharacter(htmlString) {
    return new Promise((resolve) => {
      let index = 0;
      const length = htmlString.length;

      function displayCharacter() {
        if (index < length) {
          const char = htmlString[index];

          textContainer.innerHTML += char;

          // Scrollerà quando un nuovo carattere è aggiunto
          chatBody.scrollTop = chatBody.scrollHeight;

          index++;
          setTimeout(displayCharacter, 20); // Tempo di attesa tra un carattere e l'altro (in millisecondi)
        } else {
          // Quando il messaggio è completato, gestiamo eventuali tag HTML mancanti
          textContainer.innerHTML = htmlString;
          resolve(); // Risolvi la Promise quando l'intero messaggio è stato visualizzato
        }
      }

      displayCharacter();
    });
  }

  // Avvia la visualizzazione del testo e aspetta che finisca
  await displayTextCharacterByCharacter(message);
}

  
  
  function appendActionButton(title, payload) {
  const chatBody = document.querySelector('.chatbot-body')
  const newButton = document.createElement('button');
  newButton.classList.add('btn', 'btn-primary', 'rounded');
  newButton.innerText = title;
  newButton.style.margin = '1px';
  newButton.setAttribute('onclick', `runAction('${payload}')`);
  chatBody.appendChild(newButton)
  chatBody.scrollTop = chatBody.scrollHeight;
}

function appendImage(url) {
  const chatBody = document.querySelector('.chatbot-body');
  const newImage = document.createElement('img');
  newImage.src = url;
  newImage.classList.add('rounded'); // Aggiungi classi CSS necessarie
  newImage.style.margin = '1px';
  chatBody.appendChild(newImage);
  chatBody.scrollTop = chatBody.scrollHeight;
}

function appendDocument(attachment) {
  const chatBody = document.querySelector('.chatbot-body');

  // Verifica se il tipo di contenuto è supportato
  const supportedTypes = ['application/pdf', 'image/jpeg', 'image/png'];
  if (!supportedTypes.includes(attachment.contentType)) {
    console.error('Tipo di documento non supportato:', attachment.contentType);
    return;
  }

  if (attachment.contentType === 'application/pdf') {
    // Crea un Blob dal file PDF
    const byteCharacters = atob(attachment.file);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: 'application/pdf' });
    const blobUrl = URL.createObjectURL(blob);

    // Crea un link per aprire il PDF nel lettore integrato di Chrome
    const pdfLink = document.createElement('a');
    pdfLink.href = blobUrl; // Usa l'URL Blob
    pdfLink.target = '_blank'; // Apre in una nuova scheda
    pdfLink.textContent = 'Visualizza PDF';
    chatBody.appendChild(pdfLink);

    // Messaggio informativo
    const message = document.createElement('div');
    message.textContent = 'Clicca sul link per visualizzare il PDF.';
    chatBody.appendChild(message);
  } else if (['image/jpeg', 'image/png'].includes(attachment.contentType)) {
    // Gestione delle immagini
    const img = document.createElement('img');
    img.src = 'data:' + attachment.contentType + ';base64,' + attachment.file;
    img.style.maxWidth = '100%'; // Imposta la larghezza massima
    img.style.height = 'auto'; // Mantiene le proporzioni
    chatBody.appendChild(img);
  }

  // Scorri verso il basso per mostrare il nuovo contenuto
  chatBody.scrollTop = chatBody.scrollHeight;
}

function convertNewlineToBreak(inputString) {
  return inputString.replace(/\n/g, '<br>');
}

function generateRandomString(length) {
  const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let randomString = '';

  for (let i = 0; i < length; i++) {
    const randomIndex = Math.floor(Math.random() * characters.length);
    randomString += characters.charAt(randomIndex);
  }

  return randomString;
}

function setConfiguration() {
  sessionStorage.setItem("ArmandoUser", generateRandomString(10));
  return new Promise(function(resolve, reject) {
      $.getJSON("js/config.json", function(data) {
          var backendUrl = data.backendUrl;
          if (backendUrl) {
              // Salva il valore in sessionStorage
              sessionStorage.setItem("ArmandoBackendUrl", backendUrl);
              resolve(backendUrl);
          } else {
              reject("Il campo backendUrl non è definito nel file config.json.");
          }
          var botName = data.botName;
          if (botName){
            sessionStorage.setItem('botName', botName);
            resolve(botName);
          }
      })
      .fail(function(jqxhr, textStatus, error) {
          reject("Errore nel caricamento del file config.json: " + textStatus + ", " + error);
      });
  });
}

function getUttersBackendUrl(){
  let backendUrl = sessionStorage.getItem("ArmandoBackendUrl")
  let uttersBackendUrl = backendUrl + '/webhooks/rest/webhook'
  return uttersBackendUrl
}

function getChatbotName(){
  let botName = sessionStorage.getItem("botName")
  return botName
}
