from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, UserUtteranceReverted
from rasa_sdk.types import DomainDict
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.events import SlotSet
from datetime import datetime, timedelta, date, timezone, time
import base64
import os
import requests
from typing import Any, Dict, Optional
import logging
import sys
import time
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pytz
import locale
import json
from itertools import islice

logger = logging.getLogger(__name__)




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

class ActionResetCustomSlots(Action):
    def name(self) -> Text:
        return "action_reset_custom_slots"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        slots_to_reset = [
            "user_question",
            "user_name",
            "user_email",
            "user_phone",
            "llm_solution"
        ]

        return [SlotSet(slot, None) for slot in slots_to_reset]
    
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

        response = self.llm_query(user_question)
        llm_solution = response.get("answer")

        if not llm_solution:
            dispatcher.utter_message(response="utter_no_knowledge_base")
            dispatcher.utter_message(response="utter_ask_for_opening_ticket")
        else:
            dispatcher.utter_message(text=llm_solution)

        return [SlotSet("llm_solution", llm_solution)]

    @staticmethod
    def llm_query(message: str, *, timeout: int | float = 180) -> Dict[str, Any]:
        if not message.strip():
            raise ValueError("Il parametro 'message' non può essere vuoto.")

        base_url = os.getenv("LLM_BACKEND")
        collection = os.getenv("RAG_COLLECTION")
        if not all((base_url, collection)):
            raise EnvironmentError("Imposta le variabili LLM_BACKEND e RAG_COLLECTION.")

        url = f"{base_url.rstrip('/')}/query"
        headers = {"Content-Type": "application/json"}
        payload: Dict[str, Any] = {"query": message, "collection": collection}

        logger.info("[OUTGOING] POST %s payload=%s", url, payload)
        t0 = time.perf_counter()
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        elapsed = time.perf_counter() - t0

        logger.info("[RESPONSE] status=%s elapsed=%.3fs body=%s", response.status_code, elapsed, response.text)

        try:
            response.raise_for_status()
        except requests.HTTPError:
            logger.error("[RESPONSE ERROR] status=%s headers=%s body=%s", response.status_code, response.headers, response.text)
            raise

        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            logger.error("[RESPONSE ERROR] body non-JSON: %s", response.text)
            raise
    
class ActionFindMeetingSlot(Action):
    
    def name(self) -> str:
        return "action_find_slots"
    

    @staticmethod
    def get_service():

        service_account_file = os.getenv("SERVICE_ACCOUNT_FILE")
        scopes = os.getenv("SCOPES")

        scopes = [scopes]

        credentials = service_account.Credentials.from_service_account_file(service_account_file, scopes=scopes)
        service = build('calendar', 'v3', credentials=credentials)

        return service
    
    @staticmethod
    def to_rfc3339(dt):
        # Converts datetime to RFC3339 ("Z" timezone for UTC)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')

    @staticmethod
    def next_monday(start_date=None):
        if start_date is None:
            start_date = datetime.now()
        # Prendi solo la parte della data (senza ora)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        # weekday(): lunedì == 0
        days_until_monday = (0 - start_date.weekday()) % 7
        first_monday = start_date + timedelta(days=days_until_monday)
        return first_monday

    @staticmethod
    def days_complement_busy(busy_list, tz=timezone.utc):
        # Trova il range di date totale coperto
        if not busy_list:
            return {}
        min_start = min(b[0] for b in busy_list).date()
        max_end = max(b[1] for b in busy_list).date()

        # Costruisce tabella free per ogni giorno
        results = {}
        for n in range((max_end - min_start).days + 1):
            day = min_start + timedelta(days=n)
            start_of_day = datetime.combine(day, time.min, tz)
            end_of_day = start_of_day + timedelta(days=1)

            # Filtra i busy che intersecano il giorno
            busy_intervals = []
            for b_start, b_end in busy_list:
                if b_end > start_of_day and b_start < end_of_day:
                    busy_intervals.append( (max(b_start, start_of_day), min(b_end, end_of_day)) )
            busy_intervals.sort()

            # Calcola i complementi (slot liberi)
            free_slots = []
            current = start_of_day
            for b_start, b_end in busy_intervals:
                if current < b_start:
                    free_slots.append( (current, b_start) )
                current = max(current, b_end)
            if current < end_of_day:
                free_slots.append( (current, end_of_day) )

            results[day] = free_slots

            results = {k: v for k, v in results.items() if v != []}

        return results
    
    @staticmethod
    def split_slot_in_hourly_blocks(slot, duration=timedelta(hours=1)):
        blocks = []
        slot_start, slot_end = slot
        current = slot_start
        while current + duration <= slot_end:
            block_end = current + duration
            blocks.append((current, block_end))
            current = block_end
        return blocks

    def split_all_slots_by_day(self, day_slots_dict, duration=timedelta(hours=1)):
        """
        day_slots_dict: dict { datetime.date : [ (datetime, datetime), ... ] }
        duration: blocco in output (default: 1 ora)
        return: dict { datetime.date : [ (datetime, datetime), ... ] }
        """
        result = {}
        for day, slots in day_slots_dict.items():
            hour_blocks = []
            for slot in slots:
                hour_blocks.extend(self.split_slot_in_hourly_blocks(slot, duration))
            if hour_blocks:
                result[day] = hour_blocks
        return result


    def find_free_hourly_slots(self, service, start, end, calendar_id="", slot_duration=timedelta(hours=1)):

        calendar_id = os.getenv("CALENDAR_ID")

        body = {
            "timeMin": self.to_rfc3339(start),
            "timeMax": self.to_rfc3339(end),
            "items": [{"id": calendar_id}]
        }
        logger.info("[OUTGOING] Calendar freebusy.query calendar_id=%s timeMin=%s timeMax=%s", calendar_id, body["timeMin"], body["timeMax"])
        t0 = time.perf_counter()
        events_result = service.freebusy().query(body=body).execute()
        elapsed = time.perf_counter() - t0
        busy_periods = events_result['calendars'][calendar_id]['busy']
        logger.info("[RESPONSE] freebusy.query elapsed=%.3fs busy_count=%d", elapsed, len(busy_periods))

        busy_times = []
        for period in busy_periods:
            busy_times.append((
                datetime.fromisoformat(period['start'].replace('Z', '+00:00')),
                datetime.fromisoformat(period['end'].replace('Z', '+00:00'))
            ))

        slots = self.days_complement_busy(busy_times)

        slots = self.split_all_slots_by_day(slots)

        return slots

    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict) -> list:

        locale.setlocale(locale.LC_TIME, 'it_IT.UTF-8')
        rome = pytz.timezone('Europe/Rome')


        service = self.get_service()

        start_date = self.next_monday()
        end_date = start_date + timedelta(weeks=4)
        slot_duration = timedelta(hours=1)
    
        free_slots = self.find_free_hourly_slots(service, start=start_date, end=end_date, slot_duration=slot_duration)

        buttons = []

        for d, slots in free_slots.items():
            for i, (start_utc, end_utc) in enumerate(slots):
                if i == 10:
                    break
                # Converti in locale Roma
                start_local = start_utc.astimezone(rome)
                end_local = end_utc.astimezone(rome)
                # Formatta testo pulsante: "Lunedì 17 novembre 2025, 14:00-15:00"
                day_str = start_local.strftime('%A %d %B %Y')
                time_str = f"{start_local.strftime('%H:%M')}-{end_local.strftime('%H:%M')}"
                button_text = f"{day_str}, {time_str}"
                # Rendi testo con maiuscola iniziale
                button_text = button_text[0].upper() + button_text[1:]
                # Prepara payload (ad esempio 'action_prenota' come nome azione)
                payload = f"/book_meeting{{\"start\": \"{start_local.isoformat()}\", \"end\": \"{end_local.isoformat()}\"}}"
                buttons.append({'title': button_text, 'payload': payload})

        dispatcher.utter_message(text="Scegli una fascia oraria:", buttons=buttons)

        return []

class ActionBookMeeting(Action):
    def name(self) -> str:
        return "action_book_meeting"
    
    @staticmethod
    def get_service():

        service_account_file = os.getenv("SERVICE_ACCOUNT_FILE")
        scopes = os.getenv("SCOPES")

        scopes = [scopes]

        credentials = service_account.Credentials.from_service_account_file(service_account_file, scopes=scopes)
        service = build('calendar', 'v3', credentials=credentials)

        return service

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict) -> list:
        
        user_question = tracker.get_slot("user_question")
        service_area = tracker.get_slot("topic")
        user_name = tracker.get_slot("user_name")
        user_email = tracker.get_slot("user_email")
        user_phone = tracker.get_slot("user_phone")

        try:
            intent_text = tracker.latest_message.get("text", "")
            json_part = intent_text[intent_text.find("{"):]  # trova la parentesi graffa
            params = json.loads(json_part)
            start = params.get("start")
            end = params.get("end")
        except Exception:
            start = None
            end = None

        service = self.get_service()
        
        titolo = f"Incontro con {user_name}"
        argomento = f"Incontro con {user_name} - Email: {user_email} - Telefono {user_phone} \n \n Quesito sottoposto: {user_question}"

        logging.info(f"start date type: {type(start)}")
        if self.add_google_calendar_event(service=service, titolo=titolo, argomento=argomento, inizio=start, fine=end):
            date_str = self.format_date(start.replace(" ", "T"))
            utter_out = f"Appuntamento fissato per {date_str}. Grazie per aver usato il nostro assistente virtuale!"
        else:
            utter_out = "Ci spiace, ma non è stato possibile fissare il suo appuntamento. La preghiamo di contattare la segreteria allo 031 267431"

        dispatcher.utter_message(text=utter_out)

        return[]
 
    def add_google_calendar_event(self, service, titolo, argomento, inizio, fine):
        """
        Crea un evento su Google Calendar.
        :param titolo: Titolo dell'evento
        :param argomento: Descrizione/argomento dell'evento
        :param inizio: datetime.datetime di inizio
        :param fine: datetime.datetime di fine
        """
        calendar_id = os.getenv("CALENDAR_ID")

        inizio = datetime.fromisoformat(inizio)
        fine = datetime.fromisoformat(fine)

        evento = {
            'summary': titolo,
            'description': argomento,
            'start': {
                'dateTime': self.safe_isoformat(inizio),
                'timeZone': 'Europe/Rome',
            },
            'end': {
                'dateTime': self.safe_isoformat(fine),
                'timeZone': 'Europe/Rome',
            }
        }
        logger.info(
            "[OUTGOING] Calendar events.insert calendar_id=%s summary=%r start=%s end=%s",
            calendar_id, titolo, evento['start']['dateTime'], evento['end']['dateTime'],
        )
        try:
            t0 = time.perf_counter()
            evento_creato = service.events().insert(calendarId=calendar_id, body=evento).execute()
            elapsed = time.perf_counter() - t0
            event_id = evento_creato.get('id')
            logger.info("[RESPONSE] events.insert elapsed=%.3fs event_id=%s", elapsed, event_id)
            return True
        except Exception as e:
            logger.error("[RESPONSE ERROR] events.insert error=%s", e)
            return False
        
    @staticmethod
    def safe_isoformat(dt):
        # accetta sia datetime sia stringa già formattata
        if isinstance(dt, str):
            return dt
        return dt.isoformat()
    
    @staticmethod
    def format_date(data_str):
        settimane = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

        # Converti la stringa a oggetto datetime
        dt = datetime.fromisoformat(data_str)
        # Estrai i componenti
        weekday = settimane[dt.weekday()]
        month = mesi[dt.month - 1]
        return f"{weekday} {dt.day} {month} {dt.year} ore {dt.hour}"