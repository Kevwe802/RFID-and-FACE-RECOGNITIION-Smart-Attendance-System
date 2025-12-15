#include <esp32cam.h>

#include <WebServer.h>
#include <WiFi.h>
#include <esp32cam.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

#define LED_BUILTIN 4

const char* WIFI_SSID = "AborICT-LIB";
const char* WIFI_PASS = "3Bqs4!N#7@1";

WebServer server(80);

static auto loRes = esp32cam::Resolution::find(320, 240);
static auto midRes = esp32cam::Resolution::find(350, 530);
static auto hiRes = esp32cam::Resolution::find(800, 600);

bool isWebcamActive = false;
unsigned long lastClientCheck = 0;
const unsigned long clientTimeout = 10000; // 10 seconds

void serveJpg() {
  if (!isWebcamActive) {
    digitalWrite(LED_BUILTIN, HIGH);
    isWebcamActive = true;
  }

  // Use std::unique_ptr to manage the frame
  auto frame = esp32cam::capture();
  if (!frame) {
    Serial.println("CAPTURE FAIL");
    server.send(503, "", "");
    digitalWrite(LED_BUILTIN, LOW);
    return;
  }

  Serial.printf("CAPTURE OK %dx%d %db\n", frame->getWidth(), frame->getHeight(),
                static_cast<int>(frame->size()));

  server.setContentLength(frame->size());
  server.send(200, "image/jpeg");
  WiFiClient client = server.client();
  frame->writeTo(client); // writeTo() releases the unique_ptr automatically
}

void handleJpgLo() {
  if (!esp32cam::Camera.changeResolution(loRes)) {
    Serial.println("SET-LO-RES FAIL");
  }
  serveJpg();
}

void handleJpgHi() {
  if (!esp32cam::Camera.changeResolution(hiRes)) {
    Serial.println("SET-HI-RES FAIL");
  }
  serveJpg();
}

void handleJpgMid() {
  if (!esp32cam::Camera.changeResolution(midRes)) {
    Serial.println("SET-MID-RES FAIL");
  }
  serveJpg();
}

void stopWebcam() {
  if (isWebcamActive) {
    digitalWrite(LED_BUILTIN, LOW);
    isWebcamActive = false;
    Serial.println("No clients, webcam stopped");
  }
}

void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0); // Disable brownout
  Serial.begin(115200);
  Serial.println();

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  {
    using namespace esp32cam;
    Config cfg;
    cfg.setPins(pins::AiThinker);
    cfg.setResolution(loRes); // Default to low resolution
    cfg.setBufferCount(2);
    cfg.setJpeg(60); // Lower JPEG quality

    bool ok = Camera.begin(cfg);
    Serial.println(ok ? "CAMERA OK" : "CAMERA FAIL");
  }

  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  IPAddress local_IP(192, 168, 5, 116);
  IPAddress gateway(192, 168, 5, 1);
  IPAddress subnet(255, 255, 255, 0);
  WiFi.config(local_IP, gateway, subnet);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.print("http://");
  Serial.println(WiFi.localIP());
  Serial.println("  /cam-lo.jpg");
  Serial.println("  /cam-hi.jpg");
  Serial.println("  /cam-mid.jpg");

  server.on("/cam-lo.jpg", handleJpgLo);
  server.on("/cam-hi.jpg", handleJpgHi);
  server.on("/cam-mid.jpg", handleJpgMid);

  server.begin();
}

void loop() {
  server.handleClient();
  if (millis() - lastClientCheck > clientTimeout) {
    lastClientCheck = millis();
    // Check if there are no active clients by inspecting server state
    if (server.args() == 0 && server.client().connected() == false) {
      stopWebcam();
    }
  }
}