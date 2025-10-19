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

3. Configuration:
In Python Backend (auralink_backend.py):

# Email Configuration
EMAIL_ADDRESS = "your.email@gmail.com"  # Your Gmail address
EMAIL_PASSWORD = "xxxx xxxx xxxx xxxx"  # 16-char App Password
IMAP_SERVER = "imap.gmail.com"

# OpenAI Configuration
OPENAI_API_KEY = "sk-proj-xxxxxxxxxxxxxxxxxx"  # Your OpenAI key

In ESP32 Code:

// WiFi Configuration
const char* ssid = "Your_WiFi_Name";
const char* password = "Your_WiFi_Password";

Running the System
Step 1: Upload ESP32 Code

Open AuraLink_ESP32.ino in Arduino IDE
Select Board: Tools → Board → ESP32 Arduino → ESP32 Dev Module
Select Port: Tools → Port → (your ESP32 port)
Click Upload button
Open Serial Monitor (115200 baud) to verify connection

Run Python Backend

python auralink_backend.py

should see:

==
AuraLink Backend - Email Summarization with LLM
==

Connecting to MQTT broker: broker.hivemq.com:1883
Connected to MQTT broker with result code 0
Subscribed to auralink/sensor/data

Backend is running. Waiting for sensor data...

Monitor the System

Serial Monitor: View ESP32 sensor readings and MQTT messages
OLED Display: See temperature, humidity, quotes, and email summaries
RGB LED:

Green = No urgent emails
Blue = Medium urgency
Red = High urgency emails

ESP32 Device              MQTT Broker              Python Backend
    |                          |                          |
    |---(sensor data)--------->|                          |
    |                          |----(sensor data)-------->|
    |                          |                          |
    |                          |                    [Process Data]
    |                          |                    [Generate Quote]
    |                          |                    [Check Emails]
    |                          |                    [Summarize]
    |                          |                          |
    |                          |<---(quote + summary)-----|
    |<--(quote + summary)------|                          |
    |                          |                          |
[Update Display]
[Set LED Color]


[ESP32 Device              MQTT Broker.docx](https://github.com/user-attachments/files/22987970/ESP32.Device.MQTT.Broker.docx)









