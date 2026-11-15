// 가사 큐브
// 가사 바꾸는 법: lyrics.txt 고치고 → python3 tools/make_data.py → 다시 업로드
// 그림은 scene.h 에 있음 (맥북 미리보기와 같은 코드)
// 시작: 맥북에서 tools/.venv/bin/python play.py (노래 재생 + 시작 신호)
//   USB로 연결돼 있으면 USB로, 아니면 와이파이로 신호가 옴 (http://lyrics-cube.local/start)
// BOOT 버튼: 누를 때마다 큐브용(좌우 뒤집힘) ↔ 정면용 바뀜. 마지막 선택은 꺼져도 기억함.
// 기다리는 동안 화면 오른쪽 위 작은 점 = 와이파이 연결됨

#include <Arduino.h>
#include <ESPmDNS.h>
#include <Preferences.h>
#include <U8g2lib.h>
#include <WebServer.h>
#include <WiFi.h>
#include <Wire.h>
#include "scene.h"
#include "secrets.h"

#define BTN_PIN 0  // BOOT 버튼

U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(U8G2_MIRROR, U8X8_PIN_NONE);
Preferences prefs;
WebServer server(80);
Scene scene;
uint32_t songStart = 0;
bool playing = false;  // 시작 신호를 받으면 true
bool mirror = true;    // true = 큐브용
bool lastBtn = HIGH;
uint32_t lastBtnMs = 0;
bool netReady = false;

void applyMirror() {
  u8g2.setDisplayRotation(mirror ? U8G2_MIRROR : U8G2_R0);
  Serial.println(mirror ? "mode: cube (mirrored)" : "mode: front");
}

void startSong() {
  songStart = millis();
  playing = true;
  scene.idx = -1;
  Serial.println("play");
}

void stopSong() {
  playing = false;
  scene.idx = -1;
  Serial.println("stop");
}

void setup() {
  Serial.begin(115200);
  pinMode(BTN_PIN, INPUT_PULLUP);
  prefs.begin("lyrics", false);
  mirror = prefs.getBool("mirror", true);
  u8g2.setBusClock(400000);
  u8g2.begin();
  applyMirror();
  scene_init(&scene);

  // 와이파이는 기다리지 않고 뒤에서 연결 (화면은 바로 시작)
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);  // 신호가 늦게 도착하지 않게
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  server.on("/start", []() {
    startSong();
    server.send(200, "text/plain", "OK");
  });
  server.on("/stop", []() {
    stopSong();
    server.send(200, "text/plain", "OK");
  });
  server.on("/ping", []() { server.send(200, "text/plain", playing ? "playing" : "ready"); });
  Serial.println("lyrics_cube start");
}

void loop() {
  uint32_t now = millis();

  // 와이파이 연결되면 서버 시작 (한 번만)
  if (!netReady && WiFi.status() == WL_CONNECTED) {
    netReady = true;
    MDNS.begin("lyrics-cube");
    server.begin();
    Serial.print("WiFi ok: ");
    Serial.println(WiFi.localIP());
  }
  if (netReady) server.handleClient();

  // 버튼 눌림 (떨림 무시)
  bool btn = digitalRead(BTN_PIN);
  if (btn == LOW && lastBtn == HIGH && now - lastBtnMs > 250) {
    lastBtnMs = now;
    mirror = !mirror;
    prefs.putBool("mirror", mirror);
    applyMirror();
  }
  lastBtn = btn;

  // USB로 오는 신호: S = 시작, X = 멈춤
  while (Serial.available()) {
    int c = Serial.read();
    if (c == 'S') startSong();
    else if (c == 'X') stopSong();
  }

  // 기다리는 동안은 첫 화면(♪)에 머묾
  uint32_t el = playing ? millis() - songStart : 0;
  if (playing && el >= SONG_LEN) {
    playing = false;
    el = 0;
    Serial.println("song end");
  }
  int before = scene.idx;
  scene_draw(u8g2.getU8g2(), &scene, el, now);
  if (scene.idx != before) Serial.printf("%lu ms: %s\n", (unsigned long)el, WORDS[scene.idx].text);

  // 기다리는 중 + 와이파이 연결됨 → 오른쪽 위 작은 점
  if (!playing && WiFi.status() == WL_CONNECTED) u8g2.drawBox(123, 0, 3, 3);

  u8g2.sendBuffer();
}
