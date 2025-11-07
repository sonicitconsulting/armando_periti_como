from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, UserUtteranceReverted
from rasa_sdk.types import DomainDict
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.events import SlotSet
from datetime import datetime, timedelta
import base64
import os
import requests
from typing import Any, Dict, Optional
from msal import ConfidentialClientApplication


class ActionDefaultFallback(Action):

    def name(self) -> Text:
        return "action_default_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Messaggio di fallback predefinito
        fallback_message = "Mi scuso, non ho capito. Potresti ripetere, per favore?"

        # Invia il messaggio di fallback all'utente
        dispatcher.utter_message(text=fallback_message)

        return [UserUtteranceReverted()]
    
class ActionDownloadLogo(Action):
    def name(self) -> Text:
        return "action_download_logo"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        file_path = "actions/contents/logo-vanoncinisas.png"  # Inserisci il percorso del tuo file
        
        with open(file_path, "rb") as file:     
            if tracker.get_latest_input_channel() == "telegram":
                 message = ""
                 dispatcher.utter_message(text=message, document={"file": file})
            else:
                encoded_pdf = base64.b64encode(file.read()).decode("utf-8")
                message = ""
                dispatcher.utter_message(text=message, attachment={"file": encoded_pdf, "contentType" : "image/jpeg"})
        
        return []

class ActionValidateLogin(Action):
    def name(self):
        return "action_validate_login"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):

        username = tracker.get_slot("username")

        # login con utente di sistema
        bearer_token = self.atium_login(username)
        if not bearer_token:
            dispatcher.utter_message(text="Errore di autenticazione con il sistema Atium.")
            return [SlotSet("user_logged", False)]
        else:
            SlotSet("user_logged", False)

        # Verifica se l'utente è valido
        is_valid_user, user_id = self.atium_check_user(username, bearer_token)
        if not is_valid_user:
            dispatcher.utter_message(text=f"Errore: {user_id}")
            return [SlotSet("user_logged", False)]
        else:
            dispatcher.utter_message(text="Utente risconosciuto.")
            return [SlotSet("user_logged", False), SlotSet("atium_user_id", user_id), 
                    SlotSet("auth_bearer", bearer_token)]

    @staticmethod
    def atium_login(user_id, timeout: int | float = 30) -> None:
        """
        Login su sistema Atium.
        Parameters"""
        
        atium_endpoint = os.getenv("ATIUM_ENDPOINT")
        atium_user = os.getenv("ATIUM_USER")
        atium_password = os.getenv("ATIUM_PASSWORD")
        if not all((atium_endpoint, atium_user, atium_password)):
            raise EnvironmentError(
                "Imposta le variabili ATIUM_ENDPOINT, ATIUM_USER e ATIUM_PASSWORD."
            )
        url = f"{atium_endpoint}/auth/login"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {"username": atium_user, "password": atium_password, "grant_type": "password"}

        response = requests.post(url, headers=headers, json=payload, timeout=timeout)

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()  # solleva se status >= 400
        except requests.RequestException as err:
            # Log dettagliato per debug
            print("=== ERRORE HTTP ===", err)
            if isinstance(err, requests.HTTPError):
                print("=== STATUS ===", response.status_code)
                print("=== HEADERS ===", response.headers)
                print("=== BODY ===\n", response.text)
            return False

        # A questo punto lo status è 2xx: parse del JSON
        try:
            data = response.json()
        except ValueError:  # JSON decode error
            print("Risposta non in formato JSON valido:", response.text)
            return False

        auth_token = data.get("auth_token")
        if auth_token:
            # Puoi memorizzare expires_in o id se ti serve:
            # expires_in = data.get("expires_in")
            # user_claim  = data.get("id")
            return auth_token

        # Nessun token presente: considera la risposta non valida
        print("JSON di risposta privo di 'auth_token':", data)
        return False

    @staticmethod
    def atium_check_user(user_vat: str, auth_bearer: str, timeout: int | float = 30) -> str:
        """Verifica se l'utente è registrato su Atium."""

        atium_endpoint = os.getenv("ATIUM_ENDPOINT")
        if not atium_endpoint:
            raise EnvironmentError("Imposta la variabile ATIUM_ENDPOINT.")

        url = f"{atium_endpoint}/modules/crm/checkCustomerExistance"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {auth_bearer}",
        }

        payload = {"searchString": user_vat}

        response = requests.post(url, headers=headers, json=payload, timeout=timeout)

        match response.status_code:
            case 200:
                data = response.json()
                user_id = data.get("CustSupp")
                return True, user_id
            case 204:
                return False, "Utente non registrato"
            case _:
                return False, f"Errore {response.status_code}: {response.text}"
                  
class ActionSetServiceAreaMago(Action):
    def name(self):
        return "action_set_service_area_mago"

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("service_area", "mago")]
    
class ActionSetServiceAreaFotocopiatori(Action):
    def name(self):
        return "action_set_service_area_fotocopiatori"

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("service_area", "fotocopiatori")]
    
class ActionSetServiceAreaRegistratori(Action):
    def name(self):
        return "action_set_service_area_registratori_di_cassa"

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("service_area", "registratori_di_cassa")]

class ActionSetInfoType_1(Action):
    def name(self):
        return "action_set_info_type_1"

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("info_type", "hwsw")]
    
class ActionSetInfoType_2(Action):
    def name(self):
        return "action_set_info_type_2"

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("info_type", "regcas")]

class ValidateGenericAssistanceForm(FormValidationAction):
    def name(self) -> str:
        return "validate_generic_assistance_form"

    async def validate_device_model(
        self, slot_value: str, dispatcher, tracker, domain
    ) -> dict:
        """Accetta sempre il valore dato dall’utente."""
        return {"device_model": slot_value}

    async def validate_problem_description(
        self, slot_value: str, dispatcher, tracker, domain
    ) -> dict:
        if slot_value.strip().lower() == (tracker.get_slot("device_model") or "").strip().lower():
            # 👉 niente dispatcher.utter_message qui
            return {"problem_description": None}
        return {"problem_description": slot_value}
    
class ActionAskLLM(Action):
    def name(self) -> str:
        return "action_ask_llm"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict) -> list:
        device_model = tracker.get_slot("device_model")
        description = tracker.get_slot("problem_description")
        service_area = tracker.get_slot("service_area")

        message_to_llm = (
            f"Con riferimento al prodotto '{device_model}' "
            f"il cliente ha questo problema: '{description}'. Trova la risposta nella knowledge base."
        )

        response = self.llm_query(message_to_llm)
        llm_solution = self.estrai_text_response(response)

        if llm_solution == "__NO__KB__":
            dispatcher.utter_message(response="utter_no_knowledge_base")
            dispatcher.utter_message(response="utter_ask_for_opening_ticket")
        else:
            dispatcher.utter_message(text=llm_solution)

        return [SlotSet("llm_solution", llm_solution)]
    
    @staticmethod
    def llm_query(message: str, *, timeout: int | float = 30) -> Dict[str, Any]:
        """
        Invia `message` al thread di default del workspace configurato via
        variabili d’ambiente e restituisce il JSON di risposta.

        Richiede le variabili:
            - ANYTHINGLLM_URL            es. "http://5.249.150.59:3001"
            - ANYTHINGLLM_WORKSPACE      es. "geronimo"
            - ANYTHINGLLM_API_KEY        es. "5MH9BWF-…"

        Parameters
        ----------
        message : str
            La domanda da inviare al chatbot.
        timeout : int | float, default 30
            Timeout HTTP in secondi.

        Returns
        -------
        dict
            JSON decodificato proveniente dal backend.

        Raises
        ------
        EnvironmentError
            Se una delle variabili d’ambiente non è impostata.
        requests.HTTPError
            Se il server risponde con status code ≥ 400.
        """

        # Recupero variabili d'ambiente — fallisco subito se mancano
        base_url       = os.getenv("ANYTHINGLLM_URL")
        workspace_slug = os.getenv("ANYTHINGLLM_WORKSPACE")
        api_key        = os.getenv("ANYTHINGLLM_API_KEY")
        if not all((base_url, workspace_slug, api_key)):
            raise EnvironmentError(
                "Imposta le variabili ANYTHINGLLM_URL, ANYTHINGLLM_WORKSPACE e ANYTHINGLLM_API_KEY."
            )

        url = f"{base_url.rstrip('/')}/api/v1/workspace/{workspace_slug}/chat"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {"message": message, "mode": "query"}   # mode fissato a "query"

        response = requests.post(url, headers=headers, json=payload, timeout=timeout)

        try:
            response.raise_for_status()
        except requests.HTTPError as err:
            # Logga corpo e headers per capire l'errore interno
            print("=== STATUS ===", response.status_code)
            print("=== HEADERS ===", response.headers)
            print("=== BODY ===")
            print(response.text)
            raise                  # rilancia l'eccezione per Rasa, se vuoi
        
        return response.json()
    
    @staticmethod
    def estrai_text_response(api_response: Dict[str, Any]) -> Optional[str]:
        """
        Estrae e restituisce il campo 'textResponse' dal JSON già decodificato
        ricevuto da `llm_query(...)`.

        Parameters
        ----------
        api_response : dict
            Dizionario prodotto da `llm_query()`.

        Returns
        -------
        str | None
            Il contenuto di 'textResponse', oppure None se il campo non è presente.
        """
        return api_response.get("textResponse")

class TicketClosed(Action):
    def name(self):
        return "action_open_a_closed_ticket"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):

        username = tracker.get_slot("username")
        device_model = tracker.get_slot("device_model")
        description = tracker.get_slot("problem_description")
        service_area = tracker.get_slot("service_area")
        llm_solution = tracker.get_slot("llm_solution")
        atium_user_id = tracker.get_slot("atium_user_id")
        auth_bearer = tracker.get_slot("auth_bearer")

        if self.closed_ticket(atium_user_id, auth_bearer, service_area):
            message = ((
                f"Ticket chiuso per l'utente '{username}' "
                f"con il dispositivo '{device_model}'. "
                f"Problema descritto: '{description}'. "
                f"Area di servizio: '{service_area}'. "
                f"Soluzione LLM: '{llm_solution}'."
                f"Stato del ticket: Chiuso. "
                f"Data e ora di chiusura: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ))
        else:
            message = "Errore nella registrazione dell'intervento sul sistema ATIUM"

        dispatcher.utter_message(text=message)

        return []
    
    @staticmethod
    def closed_ticket(atium_user_id: str, auth_bearer: str, service_area: str, description: str,timeout: int | float = 30) -> bool:

        atium_endpoint = os.getenv("ATIUM_ENDPOINT")
        if not atium_endpoint:
            raise EnvironmentError("Imposta la variabile ATIUM_ENDPOINT.")

        url = f"{atium_endpoint}/modules/rapportino/createTicketFromExternal"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {auth_bearer}",
        }

        if service_area == 'Mago':
            template_id = 59
        else:
            template_id = 62

        payload = {"activityDate": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                   "activityTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                   "activityState":"CL",
                   "customer":atium_user_id,
                   "IsTicket": True,
                   "templateId":template_id,
                   "OpenedBy": 37,
                   "description": description
                   }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()  # solleva se status >= 400
        except requests.RequestException as err:
            # Log dettagliato per debug
            print("=== ERRORE HTTP ===", err)
            if isinstance(err, requests.HTTPError):
                print("=== STATUS ===", response.status_code)
                print("=== HEADERS ===", response.headers)
                print("=== BODY ===\n", response.text)
            return False
        
        if response.status_code == 200:
            return True
           
class TicketOpen(Action):

    def name(self):
        return "action_open_a_open_ticket"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):

        username = tracker.get_slot("username")
        device_model = tracker.get_slot("device_model")
        description = tracker.get_slot("problem_description")
        service_area = tracker.get_slot("service_area")
        llm_solution = tracker.get_slot("llm_solution")
        atium_user_id = tracker.get_slot("atium_user_id")
        auth_bearer = tracker.get_slot("auth_bearer")

        if self.open_ticket(atium_user_id, auth_bearer, service_area): 
            message = ((
                f"Ticket aperto per l'utente '{username}' "
                f"con il dispositivo '{device_model}'. "
                f"Problema descritto: '{description}'. "
                f"Area di servizio: '{service_area}'. "
                f"Soluzione LLM: '{llm_solution}'."
                f"Stato del ticket: Aperto. "
                f"Data e ora di apertura: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            ))
        else:
            message = "Errore nell'apertura dell'intervento sul sistema ATIUM"

        dispatcher.utter_message(text=message)

        return []
    
    @staticmethod
    def open_ticket(atium_user_id: str, auth_bearer: str, service_area: str, description: str, timeout: int | float = 30) -> bool:

        atium_endpoint = os.getenv("ATIUM_ENDPOINT")
        if not atium_endpoint:
            raise EnvironmentError("Imposta la variabile ATIUM_ENDPOINT.")

        url = f"{atium_endpoint}/modules/rapportino/createTicketFromExternal"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {auth_bearer}",
        }

        if service_area == 'Mago':
            template_id = 59
        else:
            template_id = 62

        payload = {"activityDate": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                   "activityTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                   "activityState":"AP",
                   "customer":atium_user_id,
                   "IsTicket": True,
                   "templateId":template_id,
                   "OpenedBy": 37,
                   "description": description
                   }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()  # solleva se status >= 400
        except requests.RequestException as err:
            # Log dettagliato per debug
            print("=== ERRORE HTTP ===", err)
            if isinstance(err, requests.HTTPError):
                print("=== STATUS ===", response.status_code)
                print("=== HEADERS ===", response.headers)
                print("=== BODY ===\n", response.text)
            return False
        
        if response.status_code == 200:
            return True
        

class SendInfoMail(Action):
    def name(self):
        return "action_send_mail_for_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):

        info_type = tracker.get_slot("info_type")
        info_request = tracker.get_slot("info_request")
        info_address = tracker.get_slot("info_address")
        if info_type == 'hwsw':
            destinatario = os.getenv("MAILTO_HWSW")
        else:
            destinatario = os.getenv("MAILTO_REGCASSA")

        oggetto = f"Richiesta informazioni"

        email = f"Ricontattare {info_address} per la seguente richiesta di informazioni: {info_request}"

        dispatcher.utter_message(text=email)
        
        status_code = self.invia_email_office365_oauth(destinatario, oggetto, email)

        if status_code == 202:
            message = "Richiesta di informazioni inviata con successo, sarà nostra cura ricontattarla nel più breve tempo possibile"
        else:
            message = "Errore nell'invio: " + status_code

        dispatcher.utter_message(text=message)


    @staticmethod
    def invia_email_office365_oauth(destinatario, oggetto, testo):
        
        mittente = os.getenv("MAIL_BOX")
        tenant_id = os.getenv("MAIL_TENANT_ID")
        client_id = os.getenv("MAIL_CLIENT_ID")
        client_secret = os.getenv("MAIL_CLIENT_SECRET")

        
        # 1. Autenticazione via MSAL
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        scope = ["https://graph.microsoft.com/.default"]

        app = ConfidentialClientApplication(
            client_id,
            authority=authority,
            client_credential=client_secret
        )

        token_response = app.acquire_token_for_client(scopes=scope)

        if "access_token" not in token_response:
            print("Errore durante l'autenticazione:", token_response.get("error_description"))
            return

        access_token = token_response['access_token']

        # 2. Composizione della mail
        email = {
            "message": {
                "subject": oggetto,
                "body": {
                    "contentType": "Text",
                    "content": testo
                },
                "toRecipients": [
                    {"emailAddress": {"address": destinatario}}
                ]
            },
            "saveToSentItems": "true"
        }

        # 3. Invio tramite Microsoft Graph
        url = f"https://graph.microsoft.com/v1.0/users/{mittente}/sendMail"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, json=email)
        
        return response.status_code