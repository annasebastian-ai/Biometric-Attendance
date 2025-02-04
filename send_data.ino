#include <SoftwareSerial.h>
#include <Adafruit_Fingerprint.h>
#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <time.h>
#include "secrets.h"

#define TIME_ZONE -5
#define AWS_IOT_PUBLISH_TOPIC   "esp8266/pub"
#define AWS_IOT_SUBSCRIBE_TOPIC "esp8266/sub"

WiFiClientSecure net;
BearSSL::X509List cert(cacert);
BearSSL::X509List client_crt(client_cert);
BearSSL::PrivateKey key(privkey);
PubSubClient client(net);

SoftwareSerial mySerial(D2, D1); // RX, TX
Adafruit_Fingerprint finger = Adafruit_Fingerprint(&mySerial);

unsigned long lastMillis = 0; // Initialize lastMillis
char jsonBuffer[256]; // Buffer to hold the JSON string

time_t now;
time_t nowish = 1510592825;

void NTPConnect(void) {
    Serial.print("Setting time using SNTP");
    configTime(TIME_ZONE * 3600, 0 * 3600, "pool.ntp.org", "time.nist.gov");
    now = time(nullptr);
    while (now < nowish) {
        delay(500);
        Serial.print(".");
        now = time(nullptr);
    }
    Serial.println("done!");
    struct tm timeinfo;
    gmtime_r(&now, &timeinfo);
    Serial.print("Current time: ");
    Serial.print(asctime(&timeinfo));
}

void messageReceived(char *topic, byte *payload, unsigned int length) {
    Serial.print("Received [");
    Serial.print(topic);
    Serial.print("]: ");
    for (int i = 0; i < length; i++) {
        Serial.print((char)payload[i]);
    }
    Serial.println();
}

void connectAWS() {
    delay(3000);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    Serial.println(String("Attempting to connect to SSID: ") + String(WIFI_SSID));

    while (WiFi.status() != WL_CONNECTED) {
        Serial.print(".");
        delay(1000);
    }

    NTPConnect();

    net.setTrustAnchors(&cert);
    net.setClientRSACert(&client_crt, &key);

    client.setServer(MQTT_HOST, 8883);
    client.setCallback(messageReceived);

    Serial.println("Connecting to AWS IOT");

    while (!client.connect(THINGNAME)) {
        Serial.print(".");
        delay(1000);
    }

    if (!client.connected()) {
        Serial.println("AWS IoT Timeout!");
        return;
    }

    // Subscribe to a topic
    client.subscribe(AWS_IOT_SUBSCRIBE_TOPIC);
    Serial.println("AWS IoT Connected!");
}

void publishMessage() {
    // Create a JSON object
    StaticJsonDocument<1024> doc;  // Adjust the size as needed

    // Read fingerprint
    int id = getFingerprintID(); // Get fingerprint ID
    int tempdata = convFingerprint();  // Get template
    doc["fingerprint_id"] = id; // Include fingerprint ID in JSON
    doc["template"] = tempdata; //Include template in JSON
    // Serialize JSON to buffer
    serializeJson(doc, jsonBuffer);

    // Publish the JSON buffer
    client.publish(AWS_IOT_PUBLISH_TOPIC, jsonBuffer);

    // For demonstration, we'll just print the template data
    Serial.println("Fingerprint template: ");
    Serial.println(tempdata);
}


void setup() {
  Serial.begin(115200);
  mySerial.begin(57600);
  connectAWS();
  // Initialize the fingerprint sensor
  finger.begin(57600);
  
  // Check if the sensor is available
  if (finger.verifyPassword()) {
    Serial.println("Fingerprint sensor found!");
  } else {
    Serial.println("No fingerprint sensor found.");
    while (1); // Stop if not found
  }
}

void loop() {
  getFingerprintID();
  now = time(nullptr);
  delay(3000); // Wait before checking again
  publishMessage();

}

int getFingerprintID() {
  int id = finger.getImage();
  if (id == FINGERPRINT_OK) {
    Serial.println("Image taken");
    // Process fingerprint data here
  } else {
    Serial.println("Failed to get image: ");
    Serial.println(id);
  }
  return finger.fingerID;  //Return the fingerprint ID
}

int convFingerprint(){
  int id = finger.image2Tz();
  if (id == FINGERPRINT_OK) {
    Serial.println("Image converted to template");
  } else {
    Serial.println("Failed to convert the image");
  }
  return finger.image2Tz(); // Return the template
}
