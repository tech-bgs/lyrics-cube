# 노래를 듣고 단어별 시간을 뽑아 song/words.json 에 저장
# 사용법: tools/.venv/bin/python tools/transcribe.py
import json, os
import mlx_whisper

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lyrics = open(os.path.join(ROOT, "원본가사.txt"), encoding="utf-8").read()
res = mlx_whisper.transcribe(
    os.path.join(ROOT, "song", "song.mp3"),
    path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
    language="ko",
    word_timestamps=True,
    initial_prompt=lyrics.replace("\n", " ")[:200],
    condition_on_previous_text=False,
)
words = []
for seg in res["segments"]:
    for w in seg.get("words", []):
        words.append({"w": w["word"].strip(), "s": round(w["start"], 2), "e": round(w["end"], 2)})
json.dump(words, open(os.path.join(ROOT, "song", "words.json"), "w"), ensure_ascii=False, indent=0)
print(len(words), "words")
print(" ".join(f'{x["s"]}:{x["w"]}' for x in words))
