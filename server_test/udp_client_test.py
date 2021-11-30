import datetime
import time
import json
import os
import socket
import threading
import cv2
import base64
import queue
from io import BytesIO

from concurrent.futures import ThreadPoolExecutor

# 클라이언트는 지금 만든 GUI가 된다.
# 그러므로 클라이언트에서 사용할 서버와의 연동에 필요한 것들만 함수화 진행

def connect_socket(server_ip="127.0.0.1", server_port=1800, buffer_size=65535):
    """
    서버에 연결한다. 지속적인 확인이 필요하기 때문에 소켓으로 확인
    Args:
        server_ip: 아이피
        server_port: 포트

    Returns: 연결완료시 socket 객체, 아니면 None
    """
    try:
        print("연결 확인")
        # SOCK_STREAM SOCK_DGRAM
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_size)
        client_socket.connect((server_ip, server_port))

        return client_socket
    except (ConnectionRefusedError, TimeoutError, OSError):
        now = time.localtime()
        if not os.path.exists("log"):
            os.mkdir("log")
        with open(os.path.join("log", "error_log_%04d_%02d_%02d.txt" % (now.tm_year, now.tm_mon, now.tm_mday)),
                  'a') as f:
            s = "[%04d-%02d-%02d %02d:%02d:%02d]" % (
                now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
            f.write(s + "서버 연결 실패.\n")

        client_socket.close()
        return None

def video_stream_gen(queue, vid):
    while vid.isOpened():
        try:
            _, frame = vid.read()
            queue.put(frame)
        except:
            os._exit(1)
    print('Player closed')
    vid.release()

def send_data(client_socket, file_path, chunk_size=65000):
    """
    판독할 비디오 파일을 서버로 보낸다.
    Args:
        client_socket: 연결된 클라이언트 소켓. 연결 부재시 None 체크
        file_path: 비디오 파일의 절대경로.
                 단, 여러 비디오 파일을 보내고 싶다면 따로 코딩하기

    Returns: 성공시 True, 실패시 False

    """
    if client_socket is None:
        now = time.localtime()
        if not os.path.exists("log"):
            os.mkdir("log")
        with open(os.path.join("log", "error_log_%04d_%02d_%02d.txt" % (now.tm_year, now.tm_mon, now.tm_mday)),
                  'a') as f:
            s = "[%04d-%02d-%02d %02d:%02d:%02d]" % (
                now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
            f.write(s + f"서버 전송 실패. 서버 연결이 되어있지 않습니다.\n")

        return False

    if not os.path.isfile(file_path):
        now = time.localtime()
        if not os.path.exists("log"):
            os.mkdir("log")
        with open(os.path.join("log", "error_log_%04d_%02d_%02d.txt" % (now.tm_year, now.tm_mon, now.tm_mday)),
                  'a') as f:
            s = "[%04d-%02d-%02d %02d:%02d:%02d]" % (
                now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
            f.write(s + f"서버 전송 실패.\n파일이 존재하지 않습니다. 파일명: {file_path}\n")

            return False

    # 어짜피 인공지능에 들어가는 이미지 크기는 정해져 있음
    # 네트워크 부하가 매우 크므로 여기서 resize 후 정보 보내주는것이 가장 현명함
    # 리사이즈 할 크기 지정후 width/height 설정
    vid = cv2.VideoCapture(file_path)
    fps = int(vid.get(cv2.CAP_PROP_FPS))
    w = round(vid.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = round(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # opencv는 avi만 취급하므로 확장자 변경
    filename = os.path.basename(file_path)
    img_name, ext = os.path.splitext(filename)
    filename = f"{img_name}.avi"
    vid_info = json.dumps({"filename": filename, "fps": fps, "width": w, "height": h})

    # 1은 info 정보 2는 데이터를 보낸다는 신호로
    client_socket.sendto(b'1', ('127.0.0.1', 1801))
    client_socket.sendall(vid_info.encode("utf-8"))
    time.sleep(1)

    client_socket.sendto(b"2", ('127.0.0.1', 1801))
    time.sleep(1)

    try:
        while vid.isOpened():
            ret, frame = vid.read()

            if ret:
                # 리사이즈를 정했으면 여기서 리사이즈 후 보내야됨
                # frame = cv2.resize(frame, (512, 288))
                encoded, buffer = cv2.imencode('.jpeg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                message = base64.b64encode(buffer)
                # 크기를 줄여야 된다.
                # 두번 나눠서 보내자
                m_size = len(message)
                if chunk_size < m_size:
                    portion = m_size // chunk_size
                    for index in range(portion+1):
                        chunk = message[chunk_size * index:chunk_size * (index + 1)]
                        # 쪼개진 데이터로 3을 넣는다.
                        client_socket.sendto(b"3", ('127.0.0.1', 1801))
                        client_socket.sendto(chunk, ('127.0.0.1', 1801))
                        time.sleep(0.0001)
                    # 청크가 완료됬음을 알린다.
                    client_socket.sendto(b"4", ('127.0.0.1', 1801))
                else:
                    # 임의의 약속으로 -1은 전체 사이즈 인것을 표현한다.
                    client_socket.sendto(b"-1", ('127.0.0.1', 1801))
                    client_socket.sendto(message, ('127.0.0.1', 1801))
                    time.sleep(0.0001)
            else:
                break
    except Exception as e:
        print(e)
        vid.release()
        client_socket.sendto(b"0", ('127.0.0.1', 1801))
        return False

    # 0 끝을 의미
    vid.release()
    client_socket.sendto(b"0", ('127.0.0.1', 1801))

    return True


if __name__ == "__main__":
    client_socket = connect_socket(server_ip="127.0.0.1", server_port=1801)

    file_path = "t1_video_00001_최신.mp4"
    is_send = send_data(client_socket, file_path)

    print(is_send)
