#include <WiFi.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_SSD1306.h>

// ====== OLED Display Setup ======
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// ====== LED Pins ======
#define RED_LED 25
#define GREEN_LED 26
#define BLUE_LED 27

// ====== Wi-Fi & MQTT Credentials ======
const char* ssid = "Your_WiFi_Name";
const char* password = "Your_WiFi_Password";
const char* mqtt_server = "broker.hivemq.com"; // Or your local MQTT broker

WiFiClient espClient;
PubSubClient client(espClient);

// ====== Topics ======
const char* subTopic = "auralink/email_summary"; // From backend
const char* pubTopic = "auralink/status";        // ESP32 publishes status

// ====== Function Declarations ======
void setup_wifi();
void callback(char* topic, byte* payload, unsigned int length);
void reconnect();
void showMessage(String message);
void setUrgencyLED(String level);

void setup() {
  Serial.begin(115200);
  pinMode(RED_LED, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(BLUE_LED, OUTPUT);

  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED not found!");
    for(;;);
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 10);
  display.println("AuraLink starting...");
  display.display();

  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();
}

// ====== WiFi Connection ======
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
}

// ====== MQTT Reconnect ======
void reconnect() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...");
    if (client.connect("AuraLink_ESP32")) {
      Serial.println("connected");
      client.subscribe(subTopic);
      client.publish(pubTopic, "ESP32 connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 5 seconds");
      delay(5000);
    }
  }
}

// ====== Callback when message arrives ======
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");

  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println(message);

  // Parse message: format -> "URGENT: Meeting today 3PM"
  showMessage(message);

  if (message.startsWith("URGENT")) setUrgencyLED("red");
  else if (message.startsWith("NORMAL")) setUrgencyLED("green");
  else setUrgencyLED("blue");
}

// ====== Display Message ======
void showMessage(String message) {
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("📧 Email Summary:");
  display.println("------------------");
  display.println(message.substring(0, 100)); // show first part
  display.display();
}

// ====== LED Color ======
void setUrgencyLED(String level) {
  if (level == "red") {
    digitalWrite(RED_LED, HIGH);
    digitalWrite(GREEN_LED, LOW);
    digitalWrite(BLUE_LED, LOW);
  } else if (level == "green") {
    digitalWrite(RED_LED, LOW);
    digitalWrite(GREEN_LED, HIGH);
    digitalWrite(BLUE_LED, LOW);
  } else {
    digitalWrite(RED_LED, LOW);
    digitalWrite(GREEN_LED, LOW);
    digitalWrite(BLUE_LED, HIGH);
  }
}
