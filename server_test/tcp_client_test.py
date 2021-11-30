import time
import json
import os
import socket
import threading
import cv2
import base64
import numpy as np
import unicodedata

# 클라이언트는 지금 만든 GUI가 된다.
# 그러므로 클라이언트에서 사용할 서버와의 연동에 필요한 것들만 함수화 진행


class TCPClient:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self.client_socket.settimeout(10)

        # 서버와의 연결이 지속적으로 되어 있는가 확인
        self.is_connect = False

        # 파일 데이터 기록용
        self.data_path = ""
        self.data_type = 0

        self.plugin = ''

        # 결과를 기록해두는 리스트
        self.result_list = list()

        # 데이터를 보내는 중인지 확인중
        # 지속적으로 소켓통신 대기를 해야되므로 쓰레드로 돌려야됨
        # 그렇게 되면 만약에 서버가 실수로라도 데이터 보내라고 신호를 보냈을 때 두번 작업 될 수 있으므로
        # 변수를 하나 둔다.
        self.is_sending = False

        # 결과 값이 클때는 한번에 들어오지 못하므로 합쳐서 해야됨
        self.chunk_data = ""

        # 결과 값을 전부다 받아서 처리했다면 그것을 확인하기 위한 변수
        self.is_complete = False

        self.complete_send = False

    def _msg_log(self, message):
        now = time.localtime()
        if not os.path.exists("logs"):
            os.mkdir("logs")
        with open(os.path.join("logs", "%04d_%02d_%02d_client_error.log" % (now.tm_year, now.tm_mon, now.tm_mday)),
                  'a') as f:
            s = "[%04d-%02d-%02d %02d:%02d:%02d][INFO]" % (
                now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
            f.write(s + message + "\n")

    def _error_log(self, message):
        self.is_connect = False
        self.is_complete = False
        self.result_list = list()

        now = time.localtime()
        if not os.path.exists("logs"):
            os.mkdir("logs")
        with open(os.path.join("logs", "%04d_%02d_%02d_client_error.log" % (now.tm_year, now.tm_mon, now.tm_mday)),
                  'a') as f:
            s = "[%04d-%02d-%02d %02d:%02d:%02d][ERROR]" % (
                now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
            f.write(s + message + "\n")

    def connect_socket(self):
        """
        서버에 연결한다. 지속적인 확인이 필요하기 때문에 소켓으로 확인
        """
        try:
            self.client_socket.connect((self.server_ip, self.server_port))
            self.is_connect = True
            self._msg_log('서버 연결 완료')
        except (ConnectionRefusedError, TimeoutError, OSError) as e:
            self._error_log("서버 연결 실패. 네트워크 확인 해주세요.")
            self._error_log(f'ERROR : {e}')

    def send_data(self, buffer_size=4096):
        """
        판독할 비디오 파일을 서버로 보낸다.
        Args:
            buffer_size: 한번에 보낼 데이터 크기 (4096 고정)

        Returns: 성공시 True, 실패시 False

        """
        if self.client_socket is None:
            self._error_log("서버 전송 실패. 서버 연결이 되어있지 않습니다.")
            return

        if not os.path.isfile(self.data_path) or self.data_path == "":
            self._error_log(f"서버 전송 실패.\n파일이 존재하지 않습니다. 파일명: {self.data_path}")
            return

        # 만약 이미 보내고 있는 중이라면 리턴하고 스레드를 종료한다.
        if self.is_sending:
            return

        print("데이터 보내려고 준비중")
        self.is_sending = True
        vf = open(self.data_path, "rb")
        filename = os.path.basename(self.data_path)
        filename = unicodedata.normalize('NFC', filename)

        # test를 위해 앞에 test 붙힘
        vid_info = json.dumps({"filename": filename,'plugin': str(self.plugin)})

        try:
            # 1은 info 정보 2는 데이터를 보낸다는 신호로
            self.client_socket.send(b"1")
            time.sleep(0.1)
            self.client_socket.sendall(vid_info.encode("utf-8"))
            time.sleep(0.1)
            self.client_socket.send(b"2")
            time.sleep(0.1)

            # 파일 데이터 보내는중
            try:
                while True:
                    bytes_read = vf.read(buffer_size)

                    if not bytes_read:
                        # file transmitting is done
                        break

                    self.client_socket.sendall(bytes_read)
                    # time.sleep(0.0001)
            except Exception as e:
                # 실패했을 때 어떻게 할 것인가 정의
                print(e)

            # 0 끝을 의미
            vf.close()
            time.sleep(1)
            self.client_socket.send(b"0")
            self.is_sending = False
            self.complete_send = True
            print("데이터 전송 완료")
        except ConnectionRefusedError:
            # 서버와의 커넥션이 끊겼을 때 여기서 작업
            self._error_log("서버 연결 끊김. 서버 연결이 되어있지 않습니다.")

        return

    def recv_data(self):
        try:
        # 첫 연결의 시작으로 -1을 보냄
            self.client_socket.send(b"-1")
            # 보냄
            time.sleep(0.1)
            while True:
                data = self.client_socket.recv(4096)
                data = data.decode("utf-8")

                # data
                # 0번은 현재 서버가 다른 곳에서의 요청 때문에 작업중이니 대기하라는 뜻
                # 1번은 데이터를 보내란 뜻
                # 2번은 결과 데이터를 받으란 뜻
                # 3번은 결과 데이터 전송완료란 뜻
                # 4번은 결과 데이터 전송 중 뜻

                # data_type
                # 0번은 현재 영상 데이터를 서버에 전송중인 상태
                # 1번은 결과 이미지 및 결과 정보를 받아서 사용 하면 된다는 신호
                if data == "1":
                    self._msg_log("데이터 보내는 중")
                    # 연결이 끊기지 않고 지속적인 연결이 되어야 하므로 쓰레드로 진행
                    threading.Thread(target=self.send_data).start()
                    self.data_type = 0

                    # 다시 영상을 보내야 될 때 기존의 데이터를 계속 가져오려고 하므로 False 해야됨
                    self.is_complete = False
                    self.result_list = list()
                    continue
                elif data == "2":
                    self._msg_log("데이터 결과")
                    self.data_type = 1
                    continue
                elif data == "3":
                    try:
                        self._msg_log("전체 데이터 받기 완료")
                        # 결과 평가에 대한 json 해독
                        data = json.loads(self.chunk_data)
                        # worst_1 = data['worst_1']
                        # worst_2 = data['worst_2']
                        # mean = data['mean']

                        for k, v in data['result_list'].items():
                            # print(v['result_info'])
                            result_image = v['img']
                            result_info = v["result_info"]

                            # 이미지에 대한 처리를 한다.
                            result_image = base64.b64decode(result_image, ' /')
                            result_image = np.frombuffer(result_image, dtype=np.uint8)
                            result_image = cv2.imdecode(result_image, 1)
                            if k == 'worst_1':
                                self.worst_1 = {
                                    'img' : result_image,
                                    'result_info' : result_info
                                }
                            if k == 'worst_2':
                                self.worst_2 = {
                                    'img': result_image,
                                    'result_info': result_info
                                }
                            if k == 'mean':
                                self.mean = {
                                    'img': result_image,
                                    'result_info': result_info
                                }
                            # 결과 전송 다 받고 난뒤에 result list에 넣고 get result list로 꺼내서 진행
                            # self.result_list.append([result_image, result_info])

                        self.data_type = 0
                        self.is_complete = True
                    except Exception as e:
                        print(e)
                        self._msg_log("이미지 데이터 오류")
                        # 이미지 및 데이터가 잘못됬을 때 처리하는 곳
                        self.is_complete = False
                        self.result_list = list()

                    continue
                elif data == "0":
                    # 0번은 현재 서버가 다른 곳에서의 요청 때문에 작업중이니 대기하라는 뜻
                    # 끝났는지 확인하기 위해 지속적으로 -1번을 보내봄
                    self.client_socket.send(b"-1")
                    time.sleep(1)
                    continue

                # 결과 값이 클 때는 data가 분할되어 오기 때문에 합쳐야됨
                # try:
                if self.data_type == 1:
                    self.chunk_data += data
                # except Exception as e:
                #     print(e)

        except Exception as e:
            print(e)
            # 서버와의 커넥션이 끊겼을 때 여기서 작업
            self._error_log("서버 연결 끊김. 서버 연결이 되어있지 않습니다.")

    def set_data_path(self, data_path):
        self.data_path = data_path

    def set_plugin(self, plugin):
        self.plugin = plugin

    def get_is_connect(self):
        return self.is_connect

    def get_result_data(self):
        return self.worst_1, self.worst_2, self.mean

    def get_is_complete(self):
        return self.is_complete

    def close(self):
        # 만약 서버를 완전히 끊고 없애야 될 때 해당 함수를 부른다
        self.client_socket.close()
        # 혹시나 모를 초기화
        self.is_connect = False
        self.data_path = ""
        self.data_type = 0
        self.result_list = list()
        self.is_sending = False
        self.chunk_data = ""
        self.is_complete = False


if __name__ == "__main__":
    tcp_client = TCPClient(server_ip='121.151.92.251', server_port=1800)

    # 클라이언트(GUI)에서 업로드 할 동영상 파일을 선택 했을 때 서버 연결을 시도한다.
    # tcp_client.get_is_connect()로 연결이 되었는지 확인하고 소켓 통신 진행
    # 연결이 안된다면 팝업 이나 문구를 띄워서 현재 서버랑 연결이 되지 않는다고 해야됨
    tcp_client.connect_socket()
    """
    if tcp_client.get_is_connect():
        print("서버 연결이 안됨")
    """

    # 이후 연결이 되었다면 아래와 같이 셋팅
    file_path = "길이_각도별_평가.zip"
    tcp_client.set_data_path(file_path)
    # 파일 없거나 잘못됬을때 전송 안될수 있으니
    # 반드시 send_data 함수 제대로 확인할 것
    threading.Thread(target=tcp_client.recv_data).start()

    # 만약 서버와 전송이 끊기면 다시 아래와 같이 스레드 실행 해줘야됨
    # 예시)
    while True:
        time.sleep(0.01)
        if tcp_client.get_is_connect():
            # 데이터가 제대로 왔는지 지속적으로 확인해야됨
            if tcp_client.get_is_complete():
                result_list = tcp_client.get_result_data()

                for result_data in result_list:
                    image, info = result_data
                    cv2.imwrite("test.png", image)

                tcp_client.close()
                break
        else:
            print("연결 실패했음 인터넷 확인")
            break
