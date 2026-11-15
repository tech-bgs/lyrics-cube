# lyrics.txt 를 읽어서 보드용 파일 2개를 만듦 (lyrics.txt 가 없으면 lyrics.demo.txt)
#   lyrics_data.h : 단어와 시간
#   font_data.h   : 가사에 나오는 글자만 픽셀 그림으로 (기본: 배민 도현체)
# 사용법: python3 tools/make_data.py   (lyrics_cube 폴더에서)
#   다른 글꼴: LYRICS_FONT=/경로/글꼴.ttf python3 tools/make_data.py
import glob, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SIZES = {"L": 24, "S": 16}


def find_font():
    if os.environ.get("LYRICS_FONT"):
        return os.environ["LYRICS_FONT"]
    pats = ["/System/Library/AssetsV2/*/*/AssetData/BMDoHyeon-Regular.otf",
            os.path.expanduser("~/Library/Fonts/BMDoHyeon*"), "/Library/Fonts/BMDoHyeon*"]
    for p in pats:
        hits = glob.glob(p)
        if hits:
            return hits[0]
    sys.exit("글꼴을 못 찾음. LYRICS_FONT=/경로/글꼴.ttf 로 지정하세요 (한글이 있는 글꼴)")


FONT = find_font()
lyr = os.path.join(ROOT, "lyrics.txt")
if not os.path.exists(lyr):
    lyr = os.path.join(ROOT, "lyrics.demo.txt")
print("가사 파일:", os.path.basename(lyr), "/ 글꼴:", os.path.basename(FONT))

words, length = [], None
for line in open(lyr, encoding="utf-8"):
    line = line.split("#")[0].strip()  # # 뒤는 메모
    if not line:
        continue
    parts = line.split()
    if parts[0] == "LENGTH":
        length = float(parts[1])
        continue
    fx = 1 if parts[-1] == "*" else 0
    if fx:
        parts = parts[:-1]
    words.append((int(round(float(parts[0]) * 1000)), " ".join(parts[1:]), fx))
words.sort()
if length is None:
    length = words[-1][0] / 1000 + 2

chars = sorted(set("".join(w for _, w, _ in words)) - {" "})


def c_str(s):
    return '"' + "".join(c if c.isascii() and c not in '"\\' else "".join("\\%03o" % b for b in c.encode()) for c in s) + '"'


out = ["// 자동 생성 파일 (tools/make_data.py). 직접 고치지 말 것", "#pragma once", "#include <stdint.h>", ""]
for key, sz in SIZES.items():
    f = ImageFont.truetype(FONT, sz)
    imgs = []
    top, bot = 999, -999
    for ch in chars:
        im = Image.new("1", (sz * 2, sz * 2), 0)
        d = ImageDraw.Draw(im)
        d.fontmode = "1"
        d.text((4, 4), ch, font=f, fill=1)
        bb = im.getbbox()
        imgs.append((ch, im, bb))
        if bb:
            top, bot = min(top, bb[1]), max(bot, bb[3])
    h = bot - top
    glyphs, bits = [], []
    for ch, im, bb in imgs:
        x0, x1 = (bb[0], bb[2]) if bb else (0, sz // 3)
        w = x1 - x0
        off = len(bits)
        px = im.load()
        for y in range(top, bot):
            for bx in range(0, w, 8):
                v = 0
                for k in range(8):
                    if bx + k < w and px[x0 + bx + k, y]:
                        v |= 0x80 >> k
                bits.append(v)
        glyphs.append((ord(ch), w, off))
    out.append(f"#define FONT_{key}_H {h}")
    out.append(f"static const uint8_t FONT_{key}_BITS[] = {{" + ",".join(str(b) for b in bits) + "};")
    out.append(f"static const uint32_t FONT_{key}_GLYPHS[][3] = {{" + ",".join(f"{{{c},{w},{o}}}" for c, w, o in glyphs) + "};")
    out.append(f"#define FONT_{key}_COUNT {len(glyphs)}")
    out.append("")
open(os.path.join(ROOT, "font_data.h"), "w").write("\n".join(out))

ly = ["// 자동 생성 파일 (tools/make_data.py). 직접 고치지 말 것", "#pragma once", "#include <stdint.h>", "",
      "typedef struct { uint32_t ms; const char* text; uint8_t fx; } Word;",
      "static const Word WORDS[] = {"]
for ms, w, fx in words:
    ly.append(f"  {{{ms}, {c_str(w)}, {fx}}},  // {w}")
ly.append("};")
ly.append(f"#define WORD_COUNT {len(words)}")
ly.append(f"#define SONG_LEN {int(length * 1000)}")
open(os.path.join(ROOT, "lyrics_data.h"), "w").write("\n".join(ly) + "\n")
print(f"단어 {len(words)}개, 글자 {len(chars)}종, 길이 {length}초")
