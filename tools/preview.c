// 맥북 미리보기: scene.h 를 그대로 돌려서 프레임을 뽑음 (큐브로 볼 때 모습)
#include <stdio.h>
#include "u8g2.h"
#include "../scene.h"

int main(int argc, char** argv) {
  int step = argc > 1 ? atoi(argv[1]) : 33;  // 한 프레임 간격(ms)
  u8g2_t u;
  u8g2_Setup_ssd1306_128x64_noname_f(&u, U8G2_R0, u8x8_byte_empty, u8x8_dummy_cb);
  Scene sc;
  scene_init(&sc);
  for (uint32_t now = 0; now < SONG_LEN; now += step) {
    scene_draw(&u, &sc, now, now);
    fwrite(u8g2_GetBufferPtr(&u), 1, 1024, stdout);
  }
  return 0;
}
