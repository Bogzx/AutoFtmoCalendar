
# FTMO Trading Calendar Updater

Automate your trading schedule by automatically scraping FTMO for cTrader maintenance updates and adding them to a dedicated Google Calendar.

## Features

* **Automated Scraping** : Uses BeautifulSoup to fetch the latest trading updates from FTMO.
* **Intelligent Parsing** : Leverages the Gemini AI to accurately extract multiple event dates and times from unstructured text.
* **Dedicated Google Calendar** : Automatically finds or creates a sub-calendar named "Trading" to keep your events organized.
* **Duplicate Prevention** : Checks the calendar to ensure the same event is never added twice.
* **Secure** : Keeps your API keys safe using a `.env` file.
* **Customizable** : Easily change the keywords to track different platforms or events.

## Configuration

By default, the script is configured to detect maintenance for **cTrader** and  **crypto** . You can customize this by editing the `KEYWORDS` list at the top of the `main.py` file:

```
# main.py

# ...
KEYWORDS = ['maintenance', 'crypto market is closed', 'ctrader']
# ...

```

## Setup Instructions

### 1. Prerequisites

* Python 3.7+
* A Google Account

### 2. Clone the Repository

```
git clone https://github.com/Bogzx/AutoFtmoCalendar
cd AutoFtmoCalendar
```

### 3. Install Dependencies

This project uses a `requirements.txt` file to manage its dependencies. Install them using pip:

```
pip install -r requirements.txt

```

### 4. Configure API Keys and Environment

You will need an API key from Google's Gemini AI.

1. **Create a `.env` file** : Copy the example file:

```
   cp .env.example .env

```

1. **Add your API Key** : Open the new `.env` file and paste in your API key.

```
   GEMINI_API_KEY="YOUR_API_KEY_HERE"

```

### 5. Configure Google Calendar API

You only need to do this once.

1. **Enable the API & Download Credentials** : Follow the official Google guide to [enable the Google Calendar API and download your `credentials.json` file](https://developers.google.com/workspace/calendar/api/quickstart/python "null").
2. **Move the file** : Place the downloaded `credentials.json` file in the root of the project directory.

### 6. First Run & Authorization

The first time you run the script, it will open a browser window to ask for permission to access your Google Calendar.

```
python main.py

```

After you grant permission, a `token.json` file will be created. This will keep you logged in for future runs.

## Usage

To run the script manually, simply execute the `main.py` file.

```
python main.py

```

For automated daily checks, you can set up a cron job on a Linux server.

 *This is a personal project and is not affiliated with FTMO.* O
