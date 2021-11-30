import json
import socket
import base64
import cv2
import numpy as np

from settings import logger


class VideoServer:
    """
    UDP 서버는 동영상을 받을 때만 사용한다.
    현재 미완성이며 사용 안함!!
    """
    run = True
    # 현재는 아무 데이터도 넣지 않는다. 임시로 카운터만 넣음 카운터 및 클라이언트 정보 넣을수도 있음
    conn_info = list()
    conn_cnt = 1

    def __init__(self, host='localhost', port=1801, buffer_size=65535):
        self.host = host
        self.port = port

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF, buffer_size)
        self.server_socket.bind((self.host, self.port))

        # 실시간 처리할 모델 정의
        self.model = None

        # session list에 ip: session data
        self.session_list = {}

        # data_type 0은 비디오 정보, 1은 이미지 정보
        self.data_type = 0
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.frame_width = 0
        self.frame_height = 0
        self.out_video = None

        # 쪼갠 데이터 합쳐야됨
        self.chunk_data = ""
        # 쪼개진 데이터냐 아니냐 확인
        # -1은 전체 이미지, 3은 쪼갠 이미지, 4는 쪼갠이미지 완료
        self.chunk_type = -1

    def start_server(self):
        self.run = True
        logger.info('+++++++++++++++++++++++++++++++++++++++++++++++++++')
        logger.info("++ UDP Server Start, waiting clients...")
        logger.info('++ Server address: ' + self.host + '  Port: ' + str(self.port))
        logger.info('+++++++++++++++++++++++++++++++++++++++++++++++++++')

        while True:
            try:
                if self.run:
                    data, client_addr = self.server_socket.recvfrom(65536)
                    data = data.decode("utf-8")

                    if data == "1":
                        self.data_type = 0
                        continue
                    elif data == "2":
                        self.data_type = 1
                        continue
                    elif data == "0":
                        self.out_video.release()
                        self.out_video = None
                        logger.info("Complete upload Video.")
                        continue
                    elif data == "-1":
                        self.chunk_type = -1
                        continue
                    elif data == "3":
                        self.chunk_type = 3
                        continue
                    elif data == "4":
                        data = base64.b64decode(self.chunk_data, ' /')
                        npdata = np.fromstring(data, dtype=np.uint8)
                        data = cv2.imdecode(npdata, 1)
                        self.out_video.write(data)
                        self.chunk_data = ""
                        continue

                    if self.data_type == 0:
                        # {"fps": fps, "width": w, "height": h}
                        data = json.loads(data)
                        if self.out_video is None:
                            filename = data["filename"]
                            self.frame_width = int(data["width"])
                            self.frame_height = int(data["height"])
                            # print(self.frame_width, self.frame_height)
                            self.out_video = cv2.VideoWriter(filename, self.fourcc, int(data["fps"]),
                                                             (self.frame_width, self.frame_height))
                            logger.info("Ready video upload!")
                        continue

                    elif self.data_type == 1:
                        if self.chunk_type == -1:
                            data = base64.b64decode(data, ' /')
                            npdata = np.fromstring(data, dtype=np.uint8)
                            data = cv2.imdecode(npdata, 1)
                            self.out_video.write(data)
                        else:
                            self.chunk_data += data

                    # self.conn_info.append(self.conn_cnt)
                    self.conn_cnt += 1
            except Exception as e:
                logger.error(e)
                logger.info('---Client connect error!----')

    def stop_server(self):
        try:
            self.run = False
            self.server_socket.close()
            logger.info('-----Stop server-----')
            exit(0)
        except Exception:
            logger.error('---Fail Stop Server!!----')
