/*
 * Arduino Uno firmware for Raspberry Pi Radar's Arduino variant.
 * Hardware: HC-SR04 + SG90 servo.
 * Serial protocol (115200 baud):
 *   Arduino -> PC: angle,distance_cm\n
 *   PC -> Arduino: START\n | STOP\n | STEP:<1..10>\n
 * Pins (Arduino Uno R3): servo signal D9, HC-SR04 TRIG D10, ECHO D11.
 * No proximity LED is implemented in this minimal variant.
 */
#include <Servo.h>

const uint8_t SERVO_PIN = 9;
const uint8_t TRIG_PIN = 10;
const uint8_t ECHO_PIN = 11;
const unsigned long SERIAL_BAUD = 115200;
const unsigned long ECHO_TIMEOUT_US = 25000UL;
const int MAX_DISTANCE_CM = 200;

Servo radarServo;
int angleDeg = 0;
int direction = 1;
int stepDeg = 2;
bool scanning = true;
String commandBuffer;
unsigned long lastSampleMs = 0;
const unsigned long SAMPLE_INTERVAL_MS = 80;

int measureDistanceCm() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(3);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  unsigned long duration = pulseIn(ECHO_PIN, HIGH, ECHO_TIMEOUT_US);
  if (duration == 0) return MAX_DISTANCE_CM;
  int distance = (int)(duration * 0.0343f / 2.0f + 0.5f);
  if (distance < 2) return MAX_DISTANCE_CM; // avoid treating invalid near-field echoes as a target
  if (distance > MAX_DISTANCE_CM) return MAX_DISTANCE_CM;
  return distance;
}

void handleCommand(String command) {
  command.trim();
  command.toUpperCase();
  if (command == "START") {
    scanning = true;
  } else if (command == "STOP") {
    scanning = false;
  } else if (command.startsWith("STEP:")) {
    int requested = command.substring(5).toInt();
    if (requested >= 1 && requested <= 10) stepDeg = requested;
  }
}

void readSerialCommands() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n') {
      handleCommand(commandBuffer);
      commandBuffer = "";
    } else if (c != '\r' && commandBuffer.length() < 32) {
      commandBuffer += c;
    }
  }
}

void setup() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  digitalWrite(TRIG_PIN, LOW);
  radarServo.attach(SERVO_PIN, 500, 2400);
  radarServo.write(angleDeg);
  Serial.begin(SERIAL_BAUD);
  commandBuffer.reserve(32);
  delay(500);
}

void loop() {
  readSerialCommands();
  if (!scanning) {
    delay(5);
    return;
  }

  unsigned long now = millis();
  if (now - lastSampleMs < SAMPLE_INTERVAL_MS) return;
  lastSampleMs = now;

  radarServo.write(angleDeg);
  delay(25); // let the servo settle before taking the ping
  int distanceCm = measureDistanceCm();
  Serial.print(angleDeg);
  Serial.print(',');
  Serial.println(distanceCm);

  int nextAngle = angleDeg + direction * stepDeg;
  if (nextAngle >= 180) {
    nextAngle = 180;
    direction = -1;
  } else if (nextAngle <= 0) {
    nextAngle = 0;
    direction = 1;
  }
  angleDeg = nextAngle;
}
