# 노래에서 목소리만 분리해서 song/vocals.wav 로 저장
# 사용법: tools/.venv/bin/python tools/vocals.py
import os, subprocess, wave
import numpy as np
import torch
from demucs.pretrained import get_model
from demucs.apply import apply_model

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 44100
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{ROOT}/song/song.mp3", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                     capture_output=True, check=True).stdout
x = torch.from_numpy(np.frombuffer(raw, np.float32).reshape(-1, 2).T.copy())
model = get_model("htdemucs")
model.eval()
ref = x.mean(0)
xin = (x - ref.mean()) / ref.std()
dev = "mps" if torch.backends.mps.is_available() else "cpu"
with torch.no_grad():
    out = apply_model(model, xin[None], device=dev, progress=False)[0]
vi = model.sources.index("vocals")
voc = (out[vi] * ref.std() + ref.mean()).mean(0).cpu().numpy()
pcm = (np.clip(voc, -1, 1) * 32767).astype(np.int16)
with wave.open(f"{ROOT}/song/vocals.wav", "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("saved", len(pcm) / SR, "sec, device", dev)
