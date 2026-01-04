import re
from datetime import datetime, timedelta, time
from typing import Optional, Dict, Any, Tuple

from langdetect import detect, LangDetectException

from models import SessionData, Reservation
from responses import RESPONSES
from config import (
    OPENING_HOURS, MAX_CAPACITY, 
    LAST_RESERVATION_TIME_LUNCH, LAST_RESERVATION_TIME_DINNER
)
from pratos_do_dia import PRATOS_DO_DIA

# In-memory storage
reservations: Dict[str, Reservation] = {}

# --- Parsing Helper Functions ---

def parse_datetime_from_text(text: str) -> Optional[datetime]:
    """Parses a datetime from natural language text, including spelled-out numbers."""
    today = datetime.now()
    text = text.lower()  # Normalize text

    # --- Date Parsing ---
    if "amanha" in text or "amanhã" in text:
        day = today + timedelta(days=1)
    elif "hoje" in text:
        day = today
    else:
        weekdays = {"segunda": 0, "terca": 1, "terça": 1, "quarta": 2, "quinta": 3, "sexta": 4, "sabado": 5, "sábado": 5, "domingo": 6}
        day_found = False
        for wd, wd_idx in weekdays.items():
            if wd in text:
                days_ahead = wd_idx - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                day = today + timedelta(days=days_ahead)
                day_found = True
                break
        if not day_found:
            match = re.search(r"dia (\d+)", text)
            if match:
                day_num = int(match.group(1))
                try:
                    day = today.replace(day=day_num)
                    if day < today:  # Already passed this month
                        day = (today.replace(day=1) + timedelta(days=31)).replace(day=day_num)
                except ValueError:
                    return None  # Invalid day for month
            else:
                day = today  # Default to today

    # --- Time Parsing ---
    hour, minute = 20, 0  # Default dinner time

    if "almoco" in text or "almoço" in text:
        hour, minute = 13, 0
    elif "jantar" in text:
        hour, minute = 20, 0
    else:
        num_words = {
            "uma": 1, "duas": 2, "tres": 3, "três": 3, "quatro": 4, "cinco": 5, "seis": 6,
            "sete": 7, "oito": 8, "nove": 9, "dez": 10, "onze": 11, "doze": 12,
            "treze": 13, "catorze": 14, "quinze": 15, "dezasseis": 16, "dezassete": 17,
            "dezoito": 18, "dezanove": 19, "vinte": 20
        }
        
        time_match = re.search(
            r"(?:às|as|pelas|pela)\s+(\w+)(?:\s+e\s+(\w+))?", text
        )
        
        if time_match:
            hour_word = time_match.group(1)
            minute_word = time_match.group(2)

            hour = num_words.get(hour_word, hour)

            if minute_word:
                if "meia" in minute_word:
                    minute = 30
                elif "quarto" in minute_word:
                    minute = 15
                else:
                    minute = num_words.get(minute_word, 0)
        else:
            match = re.search(r"(\d{1,2})h(\d{2})?", text)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2) or 0)

    return day.replace(hour=hour, minute=minute, second=0, microsecond=0)

def extract_name(text: str) -> Optional[str]:
    """Extracts a name (simple: 2 capitalized words) from text."""
    # Adjusted regex to be more flexible, looking for capitalised words after "para"
    match = re.search(r"(?:para|a|o)?\s+([A-Z][a-z]+(?: [A-Z][a-z]+){0,2})", text)
    if match:
        name_candidate = match.group(1).strip()
        # Further refine if it's not a standalone word like "para"
        if len(name_candidate.split()) > 1: # Basic check for at least two words
            return name_candidate
    
    # Fallback to previous logic
    match = re.search(r"([A-Z][a-z]+(?: [A-Z][a-z]+)+)", text)
    return match.group(1) if match else None

def extract_phone(text: str) -> Optional[str]:
    """Extracts a phone number from text."""
    match = re.search(r"(\d{9}|\d{3}[ -]\d{3}[ -]\d{3})", text)
    return match.group(1).replace(" ", "").replace("-", "") if match else None

def extract_party_size(text: str) -> int:
    """Extracts the number of people for the reservation."""
    match = re.search(r"para (\d+|um|uma|dois|duas|tres|três|quatro|cinco|seis|sete|oito|nove|dez)", text)
    if not match: return 2 # Default party size
    
    size_str = match.group(1)
    word_to_num = {
        "um":1, "uma":1, "dois": 2, "duas": 2, "tres": 3, "três": 3, "quatro": 4, 
        "cinco": 5, "seis": 6, "sete": 7, "oito": 8, "nove": 9, "dez": 10
    }
    return word_to_num.get(size_str, int(size_str))


def parse_reservation_request(text: str) -> Dict[str, Any]:
    """Parses a full reservation request from text."""
    return {
        "datetime": parse_datetime_from_text(text),
        "name": extract_name(text),
        "phone": extract_phone(text),
        "party_size": extract_party_size(text),
    }

# --- Core Logic Functions ---

def is_open(dt: datetime) -> bool:
    """Checks if the restaurant is open at a given datetime."""
    # Tuesday is closed
    if dt.weekday() == 1:
        return False

    # Saturday or Sunday
    if dt.weekday() in [5, 6]:
        day_hours = OPENING_HOURS.get("weekend")
    else: # Weekday
        day_hours = OPENING_HOURS.get("weekday")

    if not day_hours:
        return False

    t = dt.time()
    return (time(day_hours["lunch"]["start"]) <= t <= time(day_hours["lunch"]["end"])) or \
           (time(day_hours["dinner"]["start"]) <= t <= time(day_hours["dinner"]["end"])))

def get_total_people_at(dt: datetime) -> int:
    return sum(res.party_size for res in reservations.values() if abs(res.reservation_time - dt).total_seconds() < 7200)


def format_date_for_user(dt: datetime, lang: str, include_year: bool = False) -> str:
    """Formats a date for user-facing messages."""
    months_pt = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    
    if include_year or dt.year != datetime.now().year:
        return f"dia {dt.day} de {months_pt[dt.month-1]} de {dt.year}"
    return f"dia {dt.day} de {months_pt[dt.month-1]}"
def stage_reservation(session: SessionData, details: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """Stages a reservation for staff confirmation."""
    lang = session.language

    if not all(details.values()):
        return RESPONSES[lang]["fallback"], None # Missing information

    # Validate open hours
    if not is_open(details["datetime"]):
        return RESPONSES[lang]["hours_info"], None

    # Check last reservation time
    req_time = details["datetime"].time()
    is_dinner = req_time.hour >= 19
    
    if is_dinner:
        last_res_time = time(LAST_RESERVATION_TIME_DINNER["hour"], LAST_RESERVATION_TIME_DINNER["minute"])
        if req_time > last_res_time:
            return RESPONSES[lang]["last_reservation_time_exceeded"], None
    else: # Lunch
        last_res_time = time(LAST_RESERVATION_TIME_LUNCH["hour"], LAST_RESERVATION_TIME_LUNCH["minute"])
        if req_time > last_res_time:
            return RESPONSES[lang]["hours_info"], None # Using hours_info as a generic "too late" for lunch

    # Check capacity (simplified - actual capacity check would be more complex)
    if get_total_people_at(details["datetime"]) + details["party_size"] > MAX_CAPACITY:
        available_time = (details["datetime"] + timedelta(hours=1)).strftime("%H:%M")
        return RESPONSES[lang]["reservation_full"].format(available_time=available_time), None

    # Store pending reservation in session
    pending_res = Reservation(
        name=details["name"],
        phone=details["phone"],
        reservation_time=details["datetime"],
        party_size=details["party_size"],
    )
    session.pending_confirmation_reservation = pending_res
    
    # Prepare staff message
    date_short = format_date_for_user(details["datetime"], lang)
    time_str = details["datetime"].strftime("%H:%M")
    staff_msg = RESPONSES[lang]["staff_whatsapp_template"].format(
        date_short=date_short,
        time=time_str,
        name=details["name"],
        phone=details["phone"],
        party_size=details["party_size"],
    )

    return RESPONSES[lang]["reservation_staging"], staff_msg


def confirm_reservation(session: SessionData, table_number: str) -> str:
    """Confirms a staged reservation with a table number."""
    lang = session.language
    pending_res = session.pending_confirmation_reservation

    if not pending_res:
        return RESPONSES[lang]["fallback"] # No pending reservation

    reservations[session.session_id] = pending_res # Move to confirmed reservations
    session.reservation = pending_res # Attach to session for history
    session.pending_confirmation_reservation = None # Clear pending

    # Format response
    date_short = format_date_for_user(pending_res.reservation_time, lang)
    time_str = pending_res.reservation_time.strftime("%H:%M")
    
    # Get menu by weekday name
    weekdays_en = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    day_name = weekdays_en[pending_res.reservation_time.weekday()]
    menu_list = PRATOS_DO_DIA.get(day_name, [])
    menu_str = ", ".join(menu_list) if menu_list else ""

    return RESPONSES[lang]["reservation_confirmed_staff"].format(
        table_number=table_number,
        date_short=date_short,
        time=time_str,
        menu=menu_str,
    )


def process_message(session: SessionData, user_input: str) -> str:
    """Processes the user input and returns a response."""
    if not session.language:
        try:
            session.language = detect(user_input)
            if session.language not in RESPONSES: session.language = "en"
        except LangDetectException:
            session.language = "en"
    
    lang = session.language
    lower_input = user_input.lower()

    if (datetime.utcnow() - session.created_at).total_seconds() < 5:
        return RESPONSES[lang]["greeting"]

    # --- Staff Confirmation Check ---
    if session.pending_confirmation_reservation:
        staff_confirm_match = re.search(r"(?:ok|okey|sim) mesa (\w+)", lower_input, re.IGNORECASE)
        if staff_confirm_match:
            table_number = staff_confirm_match.group(1)
            return confirm_reservation(session, table_number)
        
        # If user says something else, assume no confirmation from staff
        # For a real system, this would be timed out
        if any(keyword in lower_input for keyword in ["desculpa", "nao", "não"]): # Simple "no" from staff
            session.pending_confirmation_reservation = None
            return RESPONSES[lang]["staff_confirmation_timeout"]


    # --- Intent: Make Reservation ---
    if any(keyword in lower_input for keyword in ["reserva", "booking", "réservation"]):
        details = parse_reservation_request(user_input)
        client_response, staff_message = stage_reservation(session, details)
        
        # For simulation purposes, return client response and log staff message
        if staff_message:
            return f"{client_response}\n\n[SIMULAÇÃO STAFF WHATSAPP]: {staff_message}"
        else:
            return client_response

    # --- Other Intents ---
    if any(keyword in lower_input for keyword in ["cancelar", "cancel", "annuler"]):
        return RESPONSES[lang]["cancel_prompt"]

    if any(keyword in lower_input for keyword in ["horário", "hours", "heures"]):
        return RESPONSES[lang]["hours_info"]

    # --- Intent: Full Menu/Wine List ---
    if any(keyword in lower_input for keyword in ["menu", "carta", "vinhos", "wine list", "full menu", "cardápio"]):
        return RESPONSES[lang]["full_menu_info"]

    return RESPONSES[lang]["fallback"]