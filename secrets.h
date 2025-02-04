#include <pgmspace.h>
 
#define SECRET
 
const char WIFI_SSID[] = "";               
const char WIFI_PASSWORD[] = "";           
 
#define THINGNAME "ThingName"
 
int8_t TIME_ZONE = -5; //NYC(USA): -5 UTC
 
const char MQTT_HOST[] = "";
 
 
static const char cacert[] PROGMEM = R"EOF(
)EOF";
 
 
// Copy contents from XXXXXXXX-certificate.pem.crt here ▼
static const char client_cert[] PROGMEM = R"KEY(
)KEY";
 
 
// Copy contents from  XXXXXXXX-private.pem.key here ▼
static const char privkey[] PROGMEM = R"KEY( 
)KEY";
