# 노래를 틀면서 보드에 시작 신호를 보냄
# 사용법: ~/lyrics_cube/tools/.venv/bin/python ~/lyrics_cube/play.py [늦추기초] [--wifi]
#   늦추기초: 가사가 노래보다 빠르면 +값(예: 0.2), 느리면 -값(예: -0.2). 기본 0
#   --wifi : USB가 꽂혀 있어도 와이파이로 보냄
#   USB가 안 꽂혀 있으면 자동으로 와이파이로 보냄
# 멈추기: Ctrl+C
import glob, os, socket, subprocess, sys, time, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
offset = float(args[0]) if args else 0.0
force_wifi = "--wifi" in sys.argv
song = os.path.join(ROOT, "song", "song.mp3")

ports = glob.glob("/dev/cu.usbserial-*")
use_usb = bool(ports) and not force_wifi

if use_usb:
    import serial
    port = serial.Serial()
    port.port = ports[0]
    port.baudrate = 115200
    port.dtr = False
    port.rts = False
    port.open()
    print("USB로 연결:", ports[0], "/ 준비 중...")
    time.sleep(2.5)  # 포트를 열 때 보드가 재시작될 수 있어서 기다림
    port.reset_input_buffer()
    send = lambda c: port.write(c.encode())
else:
    print("와이파이로 보드 찾는 중...")
    try:
        ip = socket.gethostbyname("lyrics-cube.local")
        state = urllib.request.urlopen(f"http://{ip}/ping", timeout=3).read().decode()
    except Exception as e:
        sys.exit(f"보드를 못 찾음 ({e}). 보드 전원과 와이파이(화면 오른쪽 위 점)를 확인하세요")
    print("와이파이로 연결:", ip, "/", state)
    path = {"S": "/start", "X": "/stop"}
    send = lambda c: urllib.request.urlopen(f"http://{ip}{path[c]}", timeout=3).read()

player = None
try:
    if offset < 0:
        send("S")
        time.sleep(-offset)
        player = subprocess.Popen(["afplay", song])
    else:
        player = subprocess.Popen(["afplay", song])
        time.sleep(offset)
        send("S")
    print("재생 시작! (멈추려면 Ctrl+C)")
    player.wait()
    print("노래 끝")
except KeyboardInterrupt:
    try:
        send("X")
    except Exception:
        pass
    if player:
        player.terminate()
    print("멈춤")
finally:
    if use_usb:
        time.sleep(0.2)
        port.close()
