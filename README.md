# AuraLink
Smart Agentic IoT Device with LLM Backend

Hardware Requirements
ESP32 Components:

ESP32 Development Board (ESP32-WROOM-32 or similar)
DHT22 Sensor (Temperature & Humidity)
OLED Display (128x64, SSD1306, I2C)
RGB LED (Common Cathode) or 3 separate LEDs
Resistors: 3x 220Ω (for LEDs)
Breadboard and Jumper Wires
USB Cable (for programming)

Software Requirements
Arduino IDE Setup:

Install Arduino IDE (version 1.8.19 or later)

Download from: https://www.arduino.cc/en/software


Tools → Board → Boards Manager → Search "ESP32" → Install


Install Required Libraries:
Open Sketch → Include Library → Manage Libraries, then install:

DHT sensor library by Adafruit
Adafruit Unified Sensor
Adafruit SSD1306
Adafruit GFX Library
PubSubClient by Nick O'Leary
ArduinoJson by Benoit Blanchon

Python Backend Setup:

Install Python 3.8+

Download from: https://www.python.org/downloads/

Install Required Packages:
   pip install paho-mqtt
   pip install openai
   pip install python-dotenv
   
Create a virtual environment (recommended):

   python -m venv auralink_env
   source auralink_env/bin/activate  # On Windows: auralink_env\Scripts\activate
   pip install paho-mqtt openai python-dotenv


 API Keys & Credentials Setup
1. OpenAI API Key:

Sign up at: https://platform.openai.com/
Go to API Keys section
Create new secret key
Copy and save it securely

2. Gmail App Password (for email access):

Go to Google Account settings: https://myaccount.google.com/
Security → 2-Step Verification (must be enabled)
App Passwords → Select "Mail" and "Other"
Generate password
Copy the 16-character password







