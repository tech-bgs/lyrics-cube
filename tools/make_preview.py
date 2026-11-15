# preview.c 가 뽑은 프레임으로 GIF 미리보기를 만듦 (위 16줄 노랑, 나머지 하늘색)
import sys
from PIL import Image, ImageDraw

raw, out, step = sys.argv[1], sys.argv[2], int(sys.argv[3])
data = open(raw, "rb").read()
S = 4
YEL, CYAN, OFF = (255, 214, 40), (90, 220, 255), (8, 10, 18)
frames = []
for k in range(len(data) // 1024):
    b = data[k * 1024:(k + 1) * 1024]
    im = Image.new("RGB", (128 * S, 64 * S), OFF)
    d = ImageDraw.Draw(im)
    for y in range(64):
        col = YEL if y < 16 else CYAN
        for x in range(128):
            if (b[(y // 8) * 128 + x] >> (y % 8)) & 1:
                d.rectangle([x * S, y * S, x * S + S - 2, y * S + S - 2], fill=col)
    frames.append(im)
frames[0].save(out, save_all=True, append_images=frames[1:], duration=step, loop=0)
# 정지 화면 몇 장도 같이
picks = [int(len(frames) * p) for p in (0.05, 0.17, 0.3, 0.45, 0.6, 0.83)]
sheet = Image.new("RGB", (128 * S * 3 + 40, 64 * S * 2 + 30), (30, 30, 36))
for i, p in enumerate(picks):
    sheet.paste(frames[p], (10 + (i % 3) * (128 * S + 10), 10 + (i // 3) * (64 * S + 10)))
sheet.save(out.replace(".gif", "_stills.png"))
print(len(frames), "frames")
