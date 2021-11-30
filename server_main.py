import threading

import time

from server_test.tcp_server import Server
# from udp_server import VideoServer
from server_test.settings import logger
import argparse


def server_down(server, ck_stop):
    if not ck_stop:
        server.stop_server()

def parse_args():
    parser = argparse.ArgumentParser(description='Train keypoints network')
    # general
    parser.add_argument('--host',
                        help='Host ip',
                        required=True,
                        type=str)

    parser.add_argument('--port',
                        help="Port",
                        required=True,
                        type=int)

    args = parser.parse_args()

    return args

if __name__ == "__main__":
    args = parse_args()

    run_state = False

    # load 된 모델 넣기
    model = None

    # 모델 결과 를 TCP를 통해 보내야됨
    infinyx_server = Server(args.host, args.port)
    server_thread = threading.Thread(target=infinyx_server.start_server)
    server_thread.daemon = True
    server_thread.start()

    # tcp 서버 다 열릴때 까지 잠시 기다리기
    time.sleep(1)

    # 동영상 받을 UDP를 열어야됨
    # 생각해보니 스트리밍으로 받아서 실시간으로 처리하는것은 위험함
    # 영상이 씹힐 수 있으므로 잠시 봉인
    # 그래도 만든 것이 있으니 이건 git에 올리기
    # udp_server = VideoServer('127.0.0.1', 1801)
    # udp_thread = threading.Thread(target=udp_server.start_server)
    # udp_thread.daemon = True
    # udp_thread.start()

    checked_stop = False
    while True:
        data = input()

        if not isinstance(data, str):
            logger.info("q 입력만 가능합니다.")
            continue

        data = data.lower()
        if data == 'q':
            checked_stop = True
            infinyx_server.stop_server()
            # udp_server.stop_server()
        else:
            logger.info("Invalid argument. (Only 'q' or 'Q')")

    # 강제 종료가 만약 있다면.....
    # atexit.register(server_down, server=infinyx_server, ck_stop=checked_stop)
    # atexit.register(server_down, server=udp_server, ck_stop=checked_stop)


