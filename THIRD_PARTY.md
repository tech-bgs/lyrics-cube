# 사용한 남의 것들

이 저장소의 코드는 MIT 라이선스예요(LICENSE). 아래는 함께 쓰는 다른 사람의 라이브러리·도구·글꼴이에요. 저장소에 그 파일들이 들어 있지는 않고, 각자 설치해서 써요.

| 이름 | 쓰는 곳 | 라이선스 |
|---|---|---|
| [U8g2](https://github.com/olikraus/u8g2) | OLED 화면 그리기 (보드, 맥북 미리보기) | BSD 2-Clause |
| [Arduino-ESP32](https://github.com/espressif/arduino-esp32) | 보드 기본 기능 (와이파이, 웹서버 등) | LGPL-2.1 |
| [mlx-whisper](https://github.com/ml-explore/mlx-examples) / [Whisper](https://github.com/openai/whisper) | 노래 듣고 단어 시간 뽑기 | MIT |
| [Demucs](https://github.com/facebookresearch/demucs) | 노래에서 목소리만 분리 | MIT |
| [Pillow](https://python-pillow.org) | 글꼴을 픽셀 그림으로 바꾸기 | MIT-CMU (HPND) |
| [pyserial](https://github.com/pyserial/pyserial) | USB로 시작 신호 보내기 | BSD 3-Clause |
| 배달의민족 도현체 | 화면 글꼴 (기본값) | 우아한형제들 배포 글꼴. 사용 조건은 배포처에서 직접 확인하세요 |

## 글꼴

글꼴 파일과, 글꼴에서 뽑은 글자 그림(`font_data.h`)은 저장소에 넣지 않았어요. `tools/make_data.py`가 각자 컴퓨터의 글꼴로 만들어요. 다른 한글 글꼴을 쓰려면 `LYRICS_FONT=/경로/글꼴.ttf`를 지정하세요.

## 노래·가사

노래 파일과 가사는 저작권이 있어서 넣지 않았어요. 저장소에는 직접 만든 시험용 단어(`lyrics.demo.txt`)만 있어요.
