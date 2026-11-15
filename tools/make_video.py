# preview.c 프레임 + 노래 소리 → mp4 미리보기 (가사 시간 확인용)
# 사용법: tools/.venv/bin/python tools/make_video.py frames.raw step_ms out.mp4
import subprocess, sys, os
import numpy as np

raw, step, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = np.fromfile(raw, dtype=np.uint8).reshape(-1, 8, 128)
S = 4
YEL, CYAN, OFF = np.array([255, 214, 40]), np.array([90, 220, 255]), np.array([8, 10, 18])
colors = np.zeros((64, 1, 3), np.uint8)
colors[:16] = YEL
colors[16:] = CYAN
cell = np.ones((S, S), bool)
cell[-1, :] = cell[:, -1] = False  # 점 사이 틈
rowcol = np.repeat(colors, S, axis=0)  # (256,1,3)

p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{128*S}x{64*S}",
                      "-r", f"{1000/step}", "-i", "-", "-i", f"{ROOT}/song/song.mp3", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                      "-c:a", "aac", "-shortest", out], stdin=subprocess.PIPE)
for fr in data:
    bits = np.unpackbits(fr[:, None, :], axis=1, bitorder="little").reshape(64, 128).astype(bool)
    big = np.kron(bits, cell)
    img = np.where(big[..., None], rowcol, OFF).astype(np.uint8)
    p.stdin.write(img.tobytes())
p.stdin.close()
p.wait()
print(len(data), "frames")
