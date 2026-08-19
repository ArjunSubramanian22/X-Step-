# X-Step insole firmware
# Board: ESP32 (BLE). 4x FSR402 on ADC pins via 10k ohm dividers.
# Sites: GPIO34 MET1, GPIO35 MET2, GPIO32 MET5, GPIO33 HEEL
#
# Nordic UART-style BLE service. Packets match xstep_ml/protocol.py (28 bytes).

#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

#define SERVICE_UUID        "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
#define CHARACTERISTIC_RX   "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
#define CHARACTERISTIC_TX   "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

#ifndef INSOLE_SIDE_LEFT
#define INSOLE_SIDE_LEFT 1
#endif

static const int PIN_MET1 = 34;
static const int PIN_MET2 = 35;
static const int PIN_MET5 = 32;
static const int PIN_HEEL = 33;
static const int SAMPLE_HZ = 25;

BLECharacteristic *txChar;
bool deviceConnected = false;
uint16_t seq = 0;

class ServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer *pServer) { deviceConnected = true; }
  void onDisconnect(BLEServer *pServer) {
    deviceConnected = false;
    pServer->startAdvertising();
  }
};

void packPacket(uint8_t *out, uint16_t a0, uint16_t a1, uint16_t a2, uint16_t a3, uint8_t battery) {
  out[0] = 'X';
  out[1] = 'S';
  out[2] = 1;  // version
  uint8_t flags = INSOLE_SIDE_LEFT ? 0x01 : 0x02;
  out[3] = flags;
  out[4] = seq & 0xFF;
  out[5] = (seq >> 8) & 0xFF;
  uint32_t t = millis();
  memcpy(out + 6, &t, 4);
  uint16_t adc[4] = {a0, a1, a2, a3};
  memcpy(out + 10, adc, 8);
  out[18] = battery;
  out[19] = 0;
  memset(out + 20, 0, 8);  // temperatures reserved
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  BLEDevice::init(INSOLE_SIDE_LEFT ? "XSTEP-L" : "XSTEP-R");
  BLEServer *server = BLEDevice::createServer();
  server->setCallbacks(new ServerCallbacks());
  BLEService *service = server->createService(SERVICE_UUID);
  txChar = service->createCharacteristic(
      CHARACTERISTIC_TX, BLECharacteristic::PROPERTY_NOTIFY | BLECharacteristic::PROPERTY_READ);
  txChar->addDescriptor(new BLE2902());
  BLECharacteristic *rx = service->createCharacteristic(
      CHARACTERISTIC_RX, BLECharacteristic::PROPERTY_WRITE);
  service->start();
  BLEAdvertising *adv = BLEDevice::getAdvertising();
  adv->addServiceUUID(SERVICE_UUID);
  adv->setScanResponse(true);
  BLEDevice::startAdvertising();
}

void loop() {
  uint16_t a0 = analogRead(PIN_MET1);
  uint16_t a1 = analogRead(PIN_MET2);
  uint16_t a2 = analogRead(PIN_MET5);
  uint16_t a3 = analogRead(PIN_HEEL);
  uint8_t packet[28];
  packPacket(packet, a0, a1, a2, a3, 90);
  if (deviceConnected) {
    txChar->setValue(packet, 28);
    txChar->notify();
  }
  seq++;
  delay(1000 / SAMPLE_HZ);
}
