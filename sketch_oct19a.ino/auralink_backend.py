"""
AuraLink Backend - Email Summarization with LLM
Version: 1.0
Author: Your Name
Description: Backend service for AuraLink IoT device with email integration
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
import imaplib
import email
from email.header import decode_header
import os
import sys
from openai import OpenAI
import re

# ========================================
# CONFIGURATION SECTION - EDIT THIS PART
# ========================================

# MQTT Configuration
MQTT_BROKER = "broker.hivemq.com"  # Free public broker
MQTT_PORT = 1883
MQTT_TOPIC_SENSOR = "auralink/sensor/data"
MQTT_TOPIC_BACKEND = "auralink/backend/message"
MQTT_CLIENT_ID = "auralink_backend_001"

# Email Configuration
EMAIL_ADDRESS = "your.email@gmail.com"          # Your Gmail address
EMAIL_PASSWORD = "xxxx xxxx xxxx xxxx"          # Gmail App Password (16 chars)
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

# OpenAI Configuration
OPENAI_API_KEY = "sk-proj-xxxxxxxxxxxxx"        # Your OpenAI API key
OPENAI_MODEL = "gpt-3.5-turbo"                  # Model to use

# System Settings
EMAIL_CHECK_INTERVAL = 300      # Check emails every 5 minutes (300 seconds)
MAX_EMAILS_TO_FETCH = 5         # Number of recent emails to check
LOG_FILE = "sensor_log.txt"     # Sensor data log file
EMAIL_LOG_FILE = "email_log.txt" # Email activity log file
DEBUG_MODE = True               # Set to False for production

# ========================================
# END OF CONFIGURATION
# ========================================

class EmailManager:
    """Handles email fetching and processing"""
    
    def __init__(self, email_address, password, imap_server, imap_port):
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.last_check_time = 0
        
    def connect(self):
        """Connect to email server"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_address, self.password)
            return mail
        except imaplib.IMAP4.error as e:
            print(f"❌ Email login failed: {e}")
            print("💡 Make sure you're using Gmail App Password, not regular password!")
            return None
        except Exception as e:
            print(f"❌ Email connection error: {e}")
            return None
    
    def fetch_recent_emails(self, max_emails=5):
        """Fetch recent unread emails"""
        try:
            mail = self.connect()
            if not mail:
                return []
            
            mail.select('inbox')
            
            # Search for unread emails
            status, messages = mail.search(None, 'UNSEEN')
            
            if status != 'OK':
                print("No unread emails found")
                mail.close()
                mail.logout()
                return []
            
            email_ids = messages[0].split()
            
            if not email_ids:
                print("📭 No new emails")
                mail.close()
                mail.logout()
                return []
            
            print(f"📬 Found {len(email_ids)} unread email(s)")
            
            emails_data = []
            
            # Get last N emails
            for email_id in email_ids[-max_emails:]:
                try:
                    status, msg_data = mail.fetch(email_id, '(RFC822)')
                    
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            
                            # Decode subject
                            subject = self._decode_header(msg["Subject"])
                            
                            # Get sender
                            from_ = msg.get("From")
                            sender_name = self._extract_sender_name(from_)
                            
                            # Get date
                            date_ = msg.get("Date")
                            
                            # Get body
                            body = self._get_email_body(msg)
                            
                            emails_data.append({
                                'from': from_,
                                'sender_name': sender_name,
                                'subject': subject,
                                'date': date_,
                                'body': body[:1000]  # First 1000 chars
                            })
                            
                            if DEBUG_MODE:
                                print(f"  📧 From: {sender_name}")
                                print(f"     Subject: {subject[:50]}...")
                
                except Exception as e:
                    print(f"Error processing email {email_id}: {e}")
                    continue
            
            mail.close()
            mail.logout()
            
            # Log email activity
            self._log_email_activity(len(emails_data))
            
            return emails_data
        
        except Exception as e:
            print(f"❌ Error fetching emails: {e}")
            return []
    
    def _decode_header(self, header):
        """Decode email header"""
        if header is None:
            return "No Subject"
        
        decoded = decode_header(header)
        subject = ""
        for content, encoding in decoded:
            if isinstance(content, bytes):
                try:
                    subject += content.decode(encoding if encoding else "utf-8")
                except:
                    subject += content.decode("utf-8", errors="ignore")
            else:
                subject += str(content)
        return subject
    
    def _extract_sender_name(self, from_header):
        """Extract sender name from email header"""
        if not from_header:
            return "Unknown"
        
        # Try to extract name from "Name <email@domain.com>" format
        match = re.match(r'^"?([^"<]+)"?\s*<.*>$', from_header)
        if match:
            return match.group(1).strip()
        
        # If no name, return email address
        match = re.search(r'<(.+?)>', from_header)
        if match:
            return match.group(1)
        
        return from_header
    
    def _get_email_body(self, msg):
        """Extract email body text"""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='ignore')
                        break
                    except:
                        continue
        else:
            try:
                payload = msg.get_payload(decode=True)
                charset = msg.get_content_charset() or 'utf-8'
                body = payload.decode(charset, errors='ignore')
            except:
                body = str(msg.get_payload())
        
        # Clean up body
        body = re.sub(r'\s+', ' ', body).strip()
        return body
    
    def _log_email_activity(self, count):
        """Log email check activity"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(EMAIL_LOG_FILE, 'a') as f:
            f.write(f"{timestamp} | Checked emails: {count} unread\n")


class LLMProcessor:
    """Handles LLM operations for quote generation and summarization"""
    
    def __init__(self, api_key, model="gpt-3.5-turbo"):
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def generate_literature_quote(self, temperature, humidity):
        """Generate poetic quote based on sensor data"""
        try:
            # Determine conditions
            temp_desc = "warm" if temperature > 25 else "cool" if temperature < 20 else "comfortable"
            humid_desc = "humid" if humidity > 60 else "dry" if humidity < 40 else "balanced"
            
            prompt = f"""Create a SHORT poetic quote (maximum 80 characters) inspired by these indoor conditions:
- Temperature: {temperature}°C ({temp_desc})
- Humidity: {humidity}% ({humid_desc})

The quote should be:
- Literary and aesthetic
- Inspirational or calming
- Related to the atmosphere
- Very brief and elegant

Examples:
- "Warmth embraces, comfort awaits"
- "In stillness, serenity blooms"
- "Cool air whispers peace"

Return ONLY the quote, nothing else."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a poetic writer creating brief, elegant quotes."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=30,
                temperature=0.8
            )
            
            quote = response.choices[0].message.content.strip()
            quote = quote.strip('"').strip("'")  # Remove quotes if present
            
            # Truncate if too long
            if len(quote) > 80:
                quote = quote[:77] + "..."
            
            if DEBUG_MODE:
                print(f"✨ Generated Quote: {quote}")
            
            return quote
        
        except Exception as e:
            print(f"❌ Error generating quote: {e}")
            return "Every moment holds new possibilities"
    
    def summarize_emails(self, emails_data):
        """Summarize emails and determine urgency"""
        if not emails_data:
            return "No new emails", 0
        
        try:
            # Prepare email information
            email_count = len(emails_data)
            emails_text = f"I have {email_count} unread email(s):\n\n"
            
            for i, email_item in enumerate(emails_data, 1):
                emails_text += f"Email {i}:\n"
                emails_text += f"From: {email_item['sender_name']}\n"
                emails_text += f"Subject: {email_item['subject']}\n"
                emails_text += f"Preview: {email_item['body'][:300]}\n\n"
            
            prompt = f"""{emails_text}

Create a VERY brief summary (max 150 characters) for display on a small screen.

Format:
"{email_count} emails: [brief description of most important]"

Also determine urgency:
- HIGH: Urgent keywords (urgent, asap, deadline, important, critical)
- MEDIUM: Work-related, meetings, tasks
- LOW: Newsletters, notifications, casual

Return format:
SUMMARY: [your summary]
URGENCY: [HIGH/MEDIUM/LOW]"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an efficient email assistant creating ultra-brief summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=80,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            
            # Parse response
            summary_match = re.search(r'SUMMARY:\s*(.+)', result, re.IGNORECASE)
            urgency_match = re.search(r'URGENCY:\s*(HIGH|MEDIUM|LOW)', result, re.IGNORECASE)
            
            summary = summary_match.group(1).strip() if summary_match else f"{email_count} new emails"
            urgency_text = urgency_match.group(1).upper() if urgency_match else "LOW"
            
            # Convert to numeric urgency
            urgency_map = {"HIGH": 2, "MEDIUM": 1, "LOW": 0}
            urgency = urgency_map.get(urgency_text, 0)
            
            # Truncate summary if needed
            if len(summary) > 150:
                summary = summary[:147] + "..."
            
            if DEBUG_MODE:
                print(f"📝 Email Summary: {summary}")
                print(f"⚠️  Urgency: {urgency_text} ({urgency})")
            
            return summary, urgency
        
        except Exception as e:
            print(f"❌ Error summarizing emails: {e}")
            return f"{len(emails_data)} new emails", 1


class AuraLinkBackend:
    """Main backend service"""
    
    def __init__(self):
        self.mqtt_client = None
        self.email_manager = EmailManager(EMAIL_ADDRESS, EMAIL_PASSWORD, IMAP_SERVER, IMAP_PORT)
        self.llm_processor = LLMProcessor(OPENAI_API_KEY, OPENAI_MODEL)
        self.sensor_data = {}
        self.last_email_check = 0
        
    def on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            print("✅ Connected to MQTT broker successfully")
            client.subscribe(MQTT_TOPIC_SENSOR)
            print(f"📡 Subscribed to: {MQTT_TOPIC_SENSOR}")
        else:
            print(f"❌ Connection failed with code {rc}")
    
    def on_message(self, client, userdata, msg):
        """MQTT message received callback"""
        try:
            payload = json.loads(msg.payload.decode())
            self.sensor_data = payload
            
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"\n{'='*60}")
            print(f"[{timestamp}] 📊 SENSOR DATA RECEIVED")
            print(f"{'='*60}")
            print(f"🌡️  Temperature: {payload.get('temperature', 'N/A')}°C")
            print(f"💧 Humidity: {payload.get('humidity', 'N/A')}%")
            print(f"📱 Device: {payload.get('device', 'Unknown')}")
            
            # Log sensor data
            self.log_sensor_data(payload)
            
            # Process and respond
            self.process_and_respond(client, payload)
            
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON received: {e}")
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    def log_sensor_data(self, data):
        """Log sensor data to file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"{timestamp} | Temp: {data.get('temperature', 'N/A')}°C | Humidity: {data.get('humidity', 'N/A')}%\n"
        
        with open(LOG_FILE, 'a') as f:
            f.write(log_entry)
    
    def process_and_respond(self, mqtt_client, sensor_data):
        """Process sensor data and send response"""
        print(f"\n{'='*60}")
        print("🤖 PROCESSING WITH LLM")
        print(f"{'='*60}")
        
        temperature = sensor_data.get('temperature', 25)
        humidity = sensor_data.get('humidity', 50)
        
        # Generate literature quote
        print("✨ Generating quote...")
        quote = self.llm_processor.generate_literature_quote(temperature, humidity)
        
        # Check emails periodically
        email_summary = "No new emails"
        urgency = 0
        
        current_time = time.time()
        time_since_check = current_time - self.last_email_check
        
        if time_since_check >= EMAIL_CHECK_INTERVAL:
            print(f"\n📧 Checking emails (last check: {int(time_since_check)}s ago)...")
            emails = self.email_manager.fetch_recent_emails(max_emails=MAX_EMAILS_TO_FETCH)
            
            if emails:
                email_summary, urgency = self.llm_processor.summarize_emails(emails)
            else:
                email_summary = "No new emails"
                urgency = 0
                print("✅ Inbox clear")
            
            self.last_email_check = current_time
        else:
            next_check = int(EMAIL_CHECK_INTERVAL - time_since_check)
            print(f"⏳ Email check skipped (next check in {next_check}s)")
            email_summary = "Checked recently"
            urgency = 0
        
        # Prepare response message
        response = {
            'quote': quote,
            'email_summary': email_summary,
            'urgency': urgency,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Send via MQTT
        try:
            mqtt_client.publish(MQTT_TOPIC_BACKEND, json.dumps(response))
            print(f"\n{'='*60}")
            print("📤 RESPONSE SENT TO DEVICE")
            print(f"{'='*60}")
            print(f"💬 Quote: {quote}")
            print(f"📧 Email: {email_summary}")
            print(f"🚦 Urgency: {['🟢 Low', '🔵 Medium', '🔴 High'][urgency]}")
            print(f"{'='*60}\n")
        except Exception as e:
            print(f"❌ Failed to publish response: {e}")
    
    def start(self):
        """Start the backend service"""
        print("\n" + "="*60)
        print("🚀 AURALINK BACKEND SERVICE")
        print("="*60)
        print(f"Version: 1.0")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")
        
        # Verify configuration
        print("🔍 Verifying configuration...")
        
        if EMAIL_ADDRESS == "your.email@gmail.com":
            print("⚠️  WARNING: Email address not configured!")
        
        if EMAIL_PASSWORD == "xxxx xxxx xxxx xxxx":
            print("⚠️  WARNING: Email password not configured!")
        
        if OPENAI_API_KEY == "sk-proj-xxxxxxxxxxxxx":
            print("⚠️  WARNING: OpenAI API key not configured!")
        
        print(f"📧 Email: {EMAIL_ADDRESS}")
        print(f"🤖 LLM Model: {OPENAI_MODEL}")
        print(f"📡 MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        print(f"⏱️  Email Check Interval: {EMAIL_CHECK_INTERVAL}s\n")
        
        # Create MQTT client
        self.mqtt_client = mqtt.Client(MQTT_CLIENT_ID)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        
        # Connect to broker
        print(f"🔌 Connecting to MQTT broker...")
        try:
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return
        
        print("\n✅ Backend is running!")
        print("👀 Waiting for sensor data from ESP32...")
        print("Press Ctrl+C to stop\n")
        
        # Start MQTT loop
        try:
            self.mqtt_client.loop_forever()
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down backend...")
            self.mqtt_client.disconnect()
            print("✅ Backend stopped successfully")


if __name__ == "__main__":
    try:
        backend = AuraLinkBackend()
        backend.start()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)