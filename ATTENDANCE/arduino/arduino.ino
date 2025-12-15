#include <esp32cam.h>

#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include <hd44780.h>
#include <hd44780ioClass/hd44780_I2Cexp.h>

#define RST_PIN    2
#define SS_PIN     10
#define LED_G      5
#define LED_R      4
#define BUZZER     3
#define LED_BLINK  6  // LED for card detection

hd44780_I2Cexp lcd;
MFRC522 mfrc522(SS_PIN, RST_PIN);

const int LCD_COLS = 16;
const int LCD_ROWS = 2;

void setup() {
  Serial.begin();
  SPI.begin();
  mfrc522.PCD_Init();

  lcd.begin(LCD_COLS, LCD_ROWS);
  lcd.clear();
  showPrompt();

  pinMode(LED_G, OUTPUT);
  pinMode(LED_R, OUTPUT);
  pinMode(LED_BLINK, OUTPUT);
  pinMode(BUZZER, OUTPUT);

  digitalWrite(LED_G, LOW);
  digitalWrite(LED_R, LOW);
  digitalWrite(LED_BLINK, LOW);
  noTone(BUZZER);
}

void loop() {
  if (Serial.available()) handleSerialInput();

  if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
    String uidString = getUIDString();

    // Send clean UID to Python:
    Serial.print("UID:");
    Serial.println(uidString);
    Serial.flush();

    blinkOnCardDetected();
    showUIDOnLCD(uidString);

    mfrc522.PICC_HaltA();
    mfrc522.PCD_StopCrypto1();
  }
}

void handleSerialInput() {
  String input = Serial.readStringUntil('\n');
  input.trim();

  int delimiterIndex = input.indexOf('$');
  if (delimiterIndex != -1) {
    String firstLine = input.substring(1, delimiterIndex);
    String secondLine = input.substring(delimiterIndex + 1);

    lcd.clear();
    lcd.setCursor(0, 0); lcd.print(firstLine);
    lcd.setCursor(0, 1); lcd.print(secondLine);
    delay(2000);
    showPrompt();
  }

  if (input.startsWith("PRESENT")) {
    tone(BUZZER, 1000);
    digitalWrite(LED_G, HIGH);
    delay(1000);
    noTone(BUZZER);
    digitalWrite(LED_G, LOW);
  } else if (input.startsWith("NOT_RECOGNIZED")) {
    tone(BUZZER, 1000);
    digitalWrite(LED_R, HIGH);
    delay(1000);
    noTone(BUZZER);
    digitalWrite(LED_R, LOW);
  }
}

String getUIDString() {
  String content = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) content += "0";
    content += String(mfrc522.uid.uidByte[i], HEX);
  }
  content.toUpperCase();
  return content;
}

void blinkOnCardDetected() {
  tone(BUZZER, 1200);
  digitalWrite(LED_BLINK, HIGH);
  delay(500);
  noTone(BUZZER);
  digitalWrite(LED_BLINK, LOW);
}

void showUIDOnLCD(String uid) {
  lcd.clear();
  lcd.setCursor(0, 0); lcd.print("UID Detected:");
  lcd.setCursor(0, 1); lcd.print(uid);
  delay(2000);
  showPrompt();
}

void showPrompt() {
  lcd.clear();
  lcd.setCursor(3, 0); lcd.print("SHOW YOUR");
  lcd.setCursor(4, 1); lcd.print("ID CARD");
}
