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
        
        file_path = "actions/contents/logo_ext.png"  # Inserisci il percorso del tuo file
        
        with open(file_path, "rb") as file:     
            if tracker.get_latest_input_channel() == "telegram":
                 message = ""
                 dispatcher.utter_message(text=message, document={"file": file})
            else:
                encoded_pdf = base64.b64encode(file.read()).decode("utf-8")
                message = ""
                dispatcher.utter_message(text=message, attachment={"file": encoded_pdf, "contentType" : "image/jpeg"})
        
        return []

class ActionSetTopicAssociazione(Action):
    def name(self):
        return "action_set_topic_associazione"
    
    def run(self, dispatcher, tracker, domain):
        return [SlotSet("topic", "associazione")]

class ActionSetTopicLegal(Action):
    def name(self):
        return "action_set_topic_legal"
    
    def run(self, dispatcher, tracker, domain):
        return [SlotSet("topic", "legal")]
    
class ActionSetTopicEppi(Action):
    def name(self):
        return "action_set_topic_eppi"
    
    def run(self, dispatcher, tracker, domain):
        return [SlotSet("topic", "eppi")]
    

class ActionAskLLM(Action):
    def name(self) -> str:
        return "action_ask_llm"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict) -> list:
        user_question = tracker.get_slot("user_question")
        service_area = tracker.get_slot("topic")

        message_to_llm = ""

        #response = self.llm_query(message_to_llm)
        #llm_solution = self.estrai_text_response(response)

        llm_solution = "Risopsta di LLM"

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
        base_url       = os.getenv("LLM_BACKEND")
        workspace_slug = os.getenv("LLM_ENIVIRONMENT")
        api_key        = os.getenv("LLM_API_KEY")
        if not all((base_url, workspace_slug, api_key)):
            raise EnvironmentError(
                "Imposta le variabili LLM_BACKEND, LLM_ENIVIRONMENT e LLM_API_KEY."
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
    

class ActionBookMeeting(Action):
    def name(self) -> str:
        return "action_book_meeting"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict) -> list:
        user_name = tracker.get_slot("user_name")
        user_email = tracker.get_slot("user_email")

        utter_out = f"Appuntamento chiesto per {user_name} - Recapito {user_email}"

        dispatcher.utter_message(text=utter_out)

        return[]