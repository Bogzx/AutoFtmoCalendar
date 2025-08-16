# main.py
import requests
from bs4 import BeautifulSoup
import datetime
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
# Get the API key from the .env file
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']
FTMO_URL = 'https://ftmo.com/en/trading-updates/'
KEYWORDS = ['maintenance', 'crypto market is closed', 'ctrader']

class FTMOScraper:
    """
    Scrapes the FTMO trading updates page for relevant information using BeautifulSoup.
    """
    def __init__(self, url):
        """
        Initializes the scraper with the URL to scrape.
        Args:
            url (str): The URL of the FTMO trading updates page.
        """
        self.url = url

    def get_latest_update(self):
        """
        Fetches the latest trading update from the FTMO website.
        Returns:
            str: The text content of the latest trading update, or None if an error occurs.
        """
        try:
            # Using headers to mimic a real browser visit
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(self.url, headers=headers)
            response.raise_for_status()  # Raise an exception for bad status codes
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # This selector is confirmed to be correct based on the site's HTML structure.
            latest_update_container = soup.find('div', class_='trup-primary')
            
            if latest_update_container:
                # Use separator=' ' and strip=True to get clean, space-separated text
                return latest_update_container.get_text(separator=' ', strip=True)
            else:
                print("Error: Could not find the trading update container (div with class 'trup-primary'). The website structure may have changed.")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching the URL: {e}")
            return None

class GeminiEventParser:
    """
    Uses the Gemini AI to parse event details from text.
    """
    def __init__(self, api_key):
        """
        Initializes the parser and configures the Gemini API.
        Args:
            api_key (str): Your Google Gemini API key.
        """
        genai.configure(api_key=api_key)
        # CORRECTED: Updated to a current and stable model name.
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def parse_event_details(self, text):
        """
        Sends the text to the Gemini API to extract start and end times.
        Args:
            text (str): The text of the trading update.
        Returns:
            tuple: A tuple containing the start_time and end_time (as datetime objects), or (None, None).
        """
        prompt = f"""
        Analyze the following text from a trading update. Your task is to identify any scheduled maintenance or market closure related to cTrader or cryptocurrencies.

        If you find such an event, extract the exact start date and time, and the end date and time.
        The text explicitly states times are in "GMT+3". Please ensure your output reflects this.
        
        Provide the output ONLY as a single, minified JSON object with keys "start_time" and "end_time".
        The values should be in the ISO 8601 format (YYYY-MM-DDTHH:MM:SS).

        If no specific event date and time is found in the text, return a JSON object with null values for both keys.

        Text to analyze:
        ---
        {text}
        ---
        """
        try:
            response = self.model.generate_content(prompt)
            # The model is instructed to return only JSON, making it easier to parse.
            details = json.loads(response.text)
            
            start_time_str = details.get("start_time")
            end_time_str = details.get("end_time")

            if start_time_str and end_time_str:
                start_time = datetime.datetime.fromisoformat(start_time_str)
                end_time = datetime.datetime.fromisoformat(end_time_str)
                print(f"AI identified event start: {start_time}, end: {end_time}")
                return start_time, end_time
            else:
                print("AI did not find a specific event time in the text.")
                return None, None
        except (json.JSONDecodeError, ValueError, TypeError, Exception) as e:
            print(f"An error occurred while parsing the AI response: {e}")
            print(f"Raw AI response was: {response.text if 'response' in locals() else 'No response from AI.'}")
            return None, None


class GoogleCalendarManager:
    """
    Manages events on a Google Calendar.
    """
    def __init__(self, credentials_file='credentials.json', token_file='token.json'):
        """
        Initializes the GoogleCalendarManager and handles authentication.
        Args:
            credentials_file (str): The path to the credentials.json file.
            token_file (str): The path to the token.json file.
        """
        self.creds = None
        if os.path.exists(token_file):
            self.creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file, SCOPES)
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_file, 'w') as token:
                token.write(self.creds.to_json())

    def create_event(self, summary, description, start_time, end_time):
        """
        Creates an event on the user's primary calendar.
        Args:
            summary (str): The title of the event.
            description (str): The description of the event.
            start_time (datetime.datetime): The start time of the event.
            end_time (datetime.datetime): The end time of the event.
        """
        try:
            service = build('calendar', 'v3', credentials=self.creds)
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'Etc/GMT-3', # Explicitly using GMT+3 as mentioned on the site
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'Etc/GMT-3', # Explicitly using GMT+3
                },
            }
            event = service.events().insert(calendarId='primary', body=event).execute()
            print(f"Event created successfully: {event.get('htmlLink')}")
        except HttpError as error:
            print(f'An error occurred while creating the calendar event: {error}')

class TradingUpdateScheduler:
    """
    Orchestrates the process of scraping for updates and scheduling them on Google Calendar.
    """
    def __init__(self, scraper, calendar_manager, parser):
        """
        Initializes the scheduler.
        Args:
            scraper (FTMOScraper): An instance of the FTMOScraper.
            calendar_manager (GoogleCalendarManager): An instance of the GoogleCalendarManager.
            parser (GeminiEventParser): An instance of the GeminiEventParser.
        """
        self.scraper = scraper
        self.calendar_manager = calendar_manager
        self.parser = parser

    def run(self):
        """
        Executes the full process of scraping, parsing, and scheduling.
        """
        print(f"--- Running FTMO Update Check: {datetime.datetime.now()} ---")
        latest_update_text = self.scraper.get_latest_update()
        
        if not latest_update_text:
            print("Process finished: Could not retrieve update text.")
            return

        if any(keyword in latest_update_text.lower() for keyword in KEYWORDS):
            print("Relevant update found. Parsing details with AI...")
            start_time, end_time = self.parser.parse_event_details(latest_update_text)

            if start_time and end_time:
                self.calendar_manager.create_event(
                    summary='cTrader Maintenance/Crypto Market Closure',
                    description=latest_update_text,
                    start_time=start_time,
                    end_time=end_time
                )
            else:
                print("Could not create event as AI did not return specific times.")
        else:
            print("No relevant updates found containing the specified keywords.")
        
        print("--- Check Finished ---")


if __name__ == '__main__':
    if not GEMINI_API_KEY:
        print("FATAL ERROR: GEMINI_API_KEY not found. Please create a .env file and add your key.")
    else:
        try:
            # Initialize components
            ftmo_scraper = FTMOScraper(FTMO_URL)
            gcal_manager = GoogleCalendarManager()
            gemini_parser = GeminiEventParser(api_key=GEMINI_API_KEY)
            
            # Initialize and run the main scheduler
            scheduler = TradingUpdateScheduler(ftmo_scraper, gcal_manager, gemini_parser)
            scheduler.run()

        except Exception as e:
            print(f"An unexpected error occurred during execution: {e}")
