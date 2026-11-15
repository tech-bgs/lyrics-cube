# 원본가사.txt 와 song/words.json(Whisper가 들은 단어+시간)을 맞춰서 lyrics.txt 를 만듦
# 사용법: python3 tools/align.py
import difflib, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMPH = {"해줘요", "비밀을", "펼쳐보아요", "안녕을", "영원히", "거야"}  # 화면이 번쩍일 단어
GAP_IDLE = 3.0  # 다음 단어까지 이만큼(초) 비면 중간에 빈 화면(♪)

words = json.load(open(os.path.join(ROOT, "song", "words.json"), encoding="utf-8"))
dur = float(os.popen(f'ffprobe -v error -show_entries format=duration -of csv=p=0 "{ROOT}/song/song.mp3"').read())

clean = lambda s: re.sub(r"[^가-힣A-Za-z0-9]", "", s)

# 가사 어절 목록
toks = []
for line in open(os.path.join(ROOT, "원본가사.txt"), encoding="utf-8"):
    for t in line.split():
        t2 = t.strip("(),.")
        if clean(t2):
            toks.append(t2)

L, Lidx = "", []
for i, t in enumerate(toks):
    for ch in clean(t):
        L += ch
        Lidx.append(i)
W, Widx = "", []
for j, w in enumerate(words):
    c = clean(w["w"])
    for k, ch in enumerate(c):
        W += ch
        Widx.append((j, k, len(c)))

# 글자 단위로 맞추기
m = {}
for a, b, n in difflib.SequenceMatcher(None, L, W, autojunk=False).get_matching_blocks():
    for k in range(n):
        m[a + k] = b + k

start = [None] * len(toks)
end = [None] * len(toks)
pos = 0
for i, t in enumerate(toks):
    n = len(clean(t))
    hits = [m[p] for p in range(pos, pos + n) if p in m]
    if hits:
        j, k, cl = Widx[hits[0]]
        w = words[j]
        # 한 단어 안에 여러 어절이 붙어 있으면 글자 위치로 나눔
        start[i] = w["s"] + (w["e"] - w["s"]) * k / cl
        j2, k2, cl2 = Widx[hits[-1]]
        end[i] = words[j2]["s"] + (words[j2]["e"] - words[j2]["s"]) * (k2 + 1) / cl2
    pos += n

# 목소리가 쉬다가 다시 나오는 순간으로 시작 시간을 늦춤 (Whisper는 쉬는 구간을 다음 단어에 붙여서 일찍 나옴)
vpath = os.path.join(ROOT, "song", "vocals.wav")
if os.path.exists(vpath):
    import wave
    import numpy as np
    wv = wave.open(vpath)
    sr = wv.getframerate()
    a = np.frombuffer(wv.readframes(wv.getnframes()), np.int16) / 32768
    hop = int(sr * 0.02)
    nf = len(a) // hop
    db = 20 * np.log10(np.sqrt((a[: nf * hop].reshape(nf, hop) ** 2).mean(1)) + 1e-9)
    db -= np.percentile(db, 99)
    moved = 0
    for i in range(len(toks)):
        if start[i] is None or end[i] is None:
            continue
        f0 = int(start[i] / 0.02)
        f1 = min(int((end[i] - 0.1) / 0.02), f0 + 200)
        quiet = 0
        for f in range(f0, max(f0, f1)):
            if db[f] < -40:
                quiet += 1
            elif db[f] > -20 and quiet >= 8:  # 0.16초 이상 조용하다가 목소리 시작
                new = f * 0.02 - 0.05
                if new > start[i] + 0.1:
                    start[i] = new
                    moved += 1
                break
            elif db[f] > -20:
                quiet = 0
    print(f"목소리 기준으로 늦춘 어절 {moved}개")

# 못 찾은 어절은 앞뒤 사이를 고르게 나눔
guessed = [s is None for s in start]
i = 0
while i < len(toks):
    if start[i] is None:
        a = i
        while i < len(toks) and start[i] is None:
            i += 1
        t0 = end[a - 1] if a > 0 else 0
        t1 = start[i] if i < len(toks) else min(dur, t0 + 2 * (i - a))
        for k in range(a, i):
            start[k] = t0 + (t1 - t0) * (k - a + 0.3) / (i - a)
            end[k] = start[k] + 0.6
    else:
        i += 1

out = ["# 자동 생성 (tools/align.py). 시간이 어긋나면 숫자를 직접 고쳐도 됨",
       "# 한 줄에 단어 하나:  시작초  단어  (끝에 * 붙이면 화면이 번쩍)",
       "# (추정) 표시는 Whisper가 못 들어서 앞뒤 시간으로 짐작한 것",
       f"LENGTH {dur:.1f}",
       "0.0  ♪"]
for i, t in enumerate(toks):
    line = f"{start[i]:.2f}  {t}" + (" *" if t in EMPH else "")
    if guessed[i]:
        line += "      # (추정)"
    out.append(line)
    nxt = start[i + 1] if i + 1 < len(toks) else dur
    if nxt - end[i] > GAP_IDLE:
        out.append(f"{end[i] + 0.8:.2f}  ♪")
open(os.path.join(ROOT, "lyrics.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print(f"어절 {len(toks)}개, 추정 {sum(guessed)}개")
for i, t in enumerate(toks):
    if guessed[i]:
        print("  추정:", f"{start[i]:.1f}", t)
