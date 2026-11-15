// 화면 그리기 (보드와 맥북 미리보기가 같이 씀)
// 위 노란 칸: 노래 진행 줄 + 거꾸로 매달린 막대
// 가운데 파란 칸: 네 귀퉁이 꺾쇠 + 큰 단어 + 단어 바뀔 때 퍼지는 원
// 아래: 막대
#pragma once
#include <math.h>
#include <stdint.h>
#include <stdlib.h>
#include "font_data.h"
#include "lyrics_data.h"

#define SC_W 128
#define SC_H 64
#define ZONE_TOP 17   // 파란 칸 시작 (0~15줄은 노란색)
#define ZONE_BOT 47   // 파란 칸 끝
#define MID_Y 32      // 단어 가운데 높이
#define BAR_TOP 49
#define NB 21

typedef struct {
  int idx;
  uint32_t changeMs;
  float energy;
  float barH[NB];
  uint32_t seed;
} Scene;

static int sc_rand(Scene* s, int n) {
  s->seed = s->seed * 1103515245u + 12345u;
  return (int)((s->seed >> 16) % (uint32_t)n);
}

static float ease_out(float t) {
  if (t >= 1) return 1;
  float u = 1 - t;
  return 1 - u * u * u;
}

// ---------- 글자 ----------
static int utf8_next(const char** p) {
  const unsigned char* s = (const unsigned char*)*p;
  int c;
  if (s[0] < 0x80) { c = s[0]; *p += 1; }
  else if ((s[0] & 0xE0) == 0xC0) { c = ((s[0] & 0x1F) << 6) | (s[1] & 0x3F); *p += 2; }
  else if ((s[0] & 0xF0) == 0xE0) { c = ((s[0] & 0x0F) << 12) | ((s[1] & 0x3F) << 6) | (s[2] & 0x3F); *p += 3; }
  else { c = '?'; *p += 4; }
  return c;
}

typedef struct {
  const uint8_t* bits;
  const uint32_t (*glyphs)[3];
  int count, h, gap, space;
} Font;

static Font font_get(int big) {
  Font f;
  if (big) { f.bits = FONT_L_BITS; f.glyphs = FONT_L_GLYPHS; f.count = FONT_L_COUNT; f.h = FONT_L_H; f.gap = 2; f.space = 8; }
  else { f.bits = FONT_S_BITS; f.glyphs = FONT_S_GLYPHS; f.count = FONT_S_COUNT; f.h = FONT_S_H; f.gap = 1; f.space = 5; }
  return f;
}

static int font_find(const Font* f, int cp) {
  for (int i = 0; i < f->count; i++)
    if ((int)f->glyphs[i][0] == cp) return i;
  return -1;
}

static int text_width(const Font* f, const char* s) {
  int w = 0, n = 0;
  while (*s) {
    int cp = utf8_next(&s);
    int g = font_find(f, cp);
    w += (g < 0 ? f->space : (int)f->glyphs[g][1]);
    n++;
  }
  return n ? w + (n - 1) * f->gap : 0;
}

static int clipPix(int x, int y) { return x >= 0 && x < SC_W && y >= ZONE_TOP - 1 && y <= ZONE_BOT + 1; }

// visible: 보이는 글자 수, jitter: 줄마다 좌우로 흔들림(글리치)
static void draw_text(u8g2_t* u, Scene* sc, const Font* f, const char* s, int x, int y, int visible, int jitter) {
  int n = 0;
  while (*s && n < visible) {
    int cp = utf8_next(&s);
    int g = font_find(f, cp);
    if (g < 0) { x += f->space + f->gap; n++; continue; }
    int w = f->glyphs[g][1];
    const uint8_t* b = f->bits + f->glyphs[g][2];
    int bpr = (w + 7) / 8;
    for (int row = 0; row < f->h; row++) {
      int jx = jitter ? sc_rand(sc, jitter * 2 + 1) - jitter : 0;
      for (int col = 0; col < w; col++)
        if (b[row * bpr + col / 8] & (0x80 >> (col % 8))) {
          int X = x + col + jx, Y = y + row;
          if (clipPix(X, Y)) u8g2_DrawPixel(u, X, Y);
        }
    }
    x += w + f->gap;
    n++;
  }
}

static int char_count(const char* s) {
  int n = 0;
  while (*s) { utf8_next(&s); n++; }
  return n;
}

// ---------- 장식 ----------
static void ring(u8g2_t* u, float r, int dotted) {
  for (float a = 0; a < 6.2832f; a += 0.7f / r) {
    int x = SC_W / 2 + (int)(cosf(a) * r * 1.4f);  // 가로로 조금 긴 원
    int y = MID_Y + (int)(sinf(a) * r);
    if (dotted && ((x + y) & 1)) continue;
    if (clipPix(x, y) && y >= ZONE_TOP && y <= ZONE_BOT) u8g2_DrawPixel(u, x, y);
  }
}

static void brackets(u8g2_t* u, int in) {
  int L = 6, x0 = 2 + in, x1 = 125 - in, y0 = ZONE_TOP + in / 2, y1 = ZONE_BOT - in / 2;
  u8g2_DrawHLine(u, x0, y0, L); u8g2_DrawVLine(u, x0, y0, L);
  u8g2_DrawHLine(u, x1 - L + 1, y0, L); u8g2_DrawVLine(u, x1, y0, L);
  u8g2_DrawHLine(u, x0, y1, L); u8g2_DrawVLine(u, x0, y1 - L + 1, L);
  u8g2_DrawHLine(u, x1 - L + 1, y1, L); u8g2_DrawVLine(u, x1, y1 - L + 1, L);
}

// ---------- 매 프레임 ----------
static void scene_init(Scene* sc) {
  sc->idx = -1;
  sc->changeMs = 0;
  sc->energy = 0;
  sc->seed = 12345;
  for (int i = 0; i < NB; i++) sc->barH[i] = 2;
}

// el: 노래 시작 후 지난 시간(ms), now: 지금 시각(ms)
static void scene_draw(u8g2_t* u, Scene* sc, uint32_t el, uint32_t now) {
  // 지금 단어 찾기
  int idx = 0;
  for (int i = WORD_COUNT - 1; i >= 0; i--)
    if (el >= WORDS[i].ms) { idx = i; break; }
  if (idx != sc->idx) {
    sc->idx = idx;
    sc->changeMs = now;
    sc->energy = 1.0f;
  }
  const Word* w = &WORDS[idx];
  uint32_t dt = now - sc->changeMs;
  float en = sc->energy;

  u8g2_ClearBuffer(u);
  u8g2_SetDrawColor(u, 1);

  // 막대 높이 계산 (단어 바뀌면 크게 튐)
  float tt = now / 300.0f;
  for (int i = 0; i < NB; i++) {
    float shape = 0.55f + 0.45f * sinf(i * 0.55f + tt);
    float target = 2 + sc_rand(sc, 100) / 100.0f * (4 + 10 * en) * shape;
    sc->barH[i] += (target - sc->barH[i]) * 0.45f;
  }

  // ===== 위 노란 칸 =====
  // 진행 줄
  int prog = (int)(120.0f * el / SONG_LEN);
  for (int x = 4; x < 124; x += 2) u8g2_DrawPixel(u, x, 1);
  u8g2_DrawHLine(u, 4, 1, prog);
  u8g2_DrawBox(u, 3 + prog, 0, 3, 3);
  // 거꾸로 매달린 막대 (아래 막대를 뒤집어서)
  for (int i = 0; i < NB; i++) {
    int h = (int)(sc->barH[NB - 1 - i] * 0.7f);
    if (h < 1) h = 1;
    if (h > 10) h = 10;
    u8g2_DrawBox(u, 1 + i * 6, 5, 5, h);
  }

  // ===== 가운데 파란 칸 =====
  // 꺾쇠: 박자에 맞춰 안쪽으로 숨 쉼
  brackets(u, (int)(en * 4));

  // 퍼지는 원 (단어 바뀔 때)
  if (dt < 420) {
    float t = dt / 420.0f;
    ring(u, 6 + t * 40, t > 0.5f);
    if (w->fx && dt > 80) ring(u, 6 + (dt - 80) / 420.0f * 40, 1);
  }

  // 단어
  Font fl = font_get(1);
  Font fs = font_get(0);
  Font* f = text_width(&fl, w->text) <= 116 ? &fl : &fs;
  int tw = text_width(f, w->text);
  int tx = SC_W / 2 - tw / 2;
  int ty = MID_Y - f->h / 2;
  int visible = 99, jitter = 0;
  int mode = w->fx ? 4 : idx % 4;  // 단어마다 등장 방식이 바뀜
  float t = ease_out(dt / 200.0f);
  if (mode == 0) tx += (int)((1 - t) * 50);            // 오른쪽에서 밀려 들어옴
  else if (mode == 1) ty -= (int)((1 - t) * 14);       // 위에서 떨어짐
  else if (mode == 2) visible = 1 + dt / 90;           // 한 글자씩 타자
  else if (mode == 3 && dt < 180) jitter = 3;          // 지지직 글리치
  else if (mode == 4 && dt < 120) jitter = 2;          // 강조: 흔들림 + 번쩍

  // 글자 뒤 검은 바탕 (원·선이 글자를 가리지 않게)
  u8g2_SetDrawColor(u, 0);
  u8g2_DrawBox(u, tx - 4, ty - 1, tw + 8, f->h + 2);
  u8g2_SetDrawColor(u, 1);

  // 좌우 가로선: 단어가 나오면 바깥으로 쭉 뻗음
  int lineLen = (int)(ease_out(dt / 300.0f) * 40);
  int lx = SC_W / 2 - tw / 2 - 6;
  int rx = SC_W / 2 + tw / 2 + 6;
  if (lx - 8 > 0) {
    int a = lx - lineLen; if (a < 10) a = 10;
    if (lx > a) u8g2_DrawHLine(u, a, MID_Y, lx - a);
    int b = rx + lineLen; if (b > 118) b = 118;
    if (b > rx) u8g2_DrawHLine(u, rx, MID_Y, b - rx);
  }

  draw_text(u, sc, f, w->text, tx, ty, visible, jitter);

  // ===== 아래 막대 =====
  u8g2_SetDrawColor(u, 0);
  u8g2_DrawBox(u, 0, BAR_TOP, SC_W, SC_H - BAR_TOP);
  u8g2_SetDrawColor(u, 1);
  for (int i = 0; i < NB; i++) {
    int h = (int)sc->barH[i];
    if (h < 1) h = 1;
    if (h > 14) h = 14;
    u8g2_DrawBox(u, 1 + i * 6, SC_H - h, 5, h);
  }

  // 강조 단어: 처음 0.2초 화면 반전
  if (w->fx && dt < 200) {
    u8g2_SetDrawColor(u, 2);
    u8g2_DrawBox(u, 0, 0, SC_W, SC_H);
    u8g2_SetDrawColor(u, 1);
  }

  sc->energy *= 0.92f;
}
