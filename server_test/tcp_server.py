import datetime
import json
import socket
import threading
import time
import base64
import cv2
import os

import numpy as np
from server_test.preciseEvaluation import RULA, OWAS, REBA

from libs.utils.transforms import get_affine_transform
from libs.myutil import box_to_center_scale
import torchvision.transforms as transforms
from libs.core.inference import get_final_preds


from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2 import model_zoo

from gui_util import gui_util

from server_test.settings import logger

from libs.config import cfg as cfgs
import torch.backends.cudnn as cudnn
import torch
from libs.config import update_config
from libs.models.pose_hrnet import PoseHighResolutionNet
from deep_sort_pytorch.utils.parser import get_config
from deep_sort_pytorch.deep_sort import DeepSort


REQ_GET_OBJECT_COORDINATE = 0
REQ_GET_PALLET_COORDINATE = 1
REQ_GET_PALLET_IMAGE = 2

REQ_SET_RS_INIT = 99

ALREADY_CONNECT = False


class SessionData:
    client_name = 'unknown'
    ip = '127.0.0.1'
    dt = datetime.datetime.now
    data = ''

    def parse_inp_str(self, inp_str):
        if inp_str.find('pc_name', 0, len(inp_str)) != -1:
            self.client_name = inp_str[inp_str.find('pc_name:', 0) + 8: inp_str.find('ip:', 0)]
            self.ip = inp_str[inp_str.find('ip:', 0) + 3: inp_str.find('dt:', 0)]
            self.dt = inp_str[inp_str.find('dt:', 0) + 3:]

    def set_data_str(self, data):
        self.data = data


class ClientThread(threading.Thread):
    # 현재는 사용하지 않음
    # sess = SessionData()
    clients = []

    def __init__(self, channel, details, detec_model, posemodel, conn_info):
        self.channel = channel
        self.details = details
        self.killed = False
        self.thread = threading.current_thread()
        threading.Thread.__init__(self)
        logger.info(f'클라이언트 연결 완료. {details}')

        self.model = posemodel
        self.predictor = detec_model

        # self.deepsort = deepsort
        self.cfg2 = get_config()
        self.cfg2.merge_from_file("deep_sort_pytorch/configs/deep_sort.yaml")
        self.deepsort = DeepSort(self.cfg2.DEEPSORT.REID_CKPT,
                                 max_dist=self.cfg2.DEEPSORT.MAX_DIST, min_confidence=self.cfg2.DEEPSORT.MIN_CONFIDENCE,
                                 nms_max_overlap=self.cfg2.DEEPSORT.NMS_MAX_OVERLAP,
                                 max_iou_distance=self.cfg2.DEEPSORT.MAX_IOU_DISTANCE,
                                 max_age=self.cfg2.DEEPSORT.MAX_AGE, n_init=self.cfg2.DEEPSORT.N_INIT,
                                 nn_budget=self.cfg2.DEEPSORT.NN_BUDGET,
                                 use_cuda=True)

        self.conn_info = conn_info


        # data 저장용 file 변수
        self.vf = None
        # 바로 모델에서 사용하기 위하여 filename 알아야됨
        self.filename = None
        # data_type 1은 파일 정보, 2는 파일, 0은 종료임
        self.data_type = 0
        self.error = False

    def kill(self):
        self.killed = True

    def run(self):
        try:
            while True:
                data = self.input_data()
                if len(self.conn_info) == 1:
                    # data -1은 연결이 됬음을 알리는 시작 정보임
                    # data 1은 파일 정보, 2는 파일, 0은 파일 전송 종료임
                    if data == "-1":
                        # 클라이언트한테 이제 동영상 파일을 보내라고 신호를 줌
                        self.channel.send(b"1")
                        continue
                    elif data == "1":
                        logger.info('파일 정보 전송')
                        self.data_type = 1
                        continue
                    elif data == "2":
                        logger.info('동영상 전송')
                        self.data_type = 2
                        continue
                    elif data == b"0":
                        # 파일 전송이 끝나고 나서 0을 제공하는데
                        # 끝나는 시점 체크를 따로 하기 힘들어서 decode 안하고 byte 로 체크
                        logger.info('파일 전송 완료')
                        self.data_type = 0
                        self.vf.close()

                        # 0으로 종료되면 인공지능 모델 진행 후
                        # 결과를 보내줘야됨
                        # 단, 해당 데이터 전송한다고 소켓의 while 이 중단되면 안되므로 쓰레드 처리
                        threading.Thread(target=self.send_result_data).start()

                    if self.data_type == 1:
                        data = json.loads(data)
                        self.filename = os.path.join('data',data["filename"])
                        self.plugin = eval(data['plugin'])
                        self.vf = open(self.filename, "wb")

                    elif self.data_type == 2:
                        if self.vf is None:
                            continue

                        self.vf.write(data)
                else:
                    # 이미 다른 컴퓨터가 사용중이므로 대기 해야됨
                    # 일단 임시로 0을 보내서 대기중임을 강조
                    self.channel.send(b"0")
                    time.sleep(1)

        except ConnectionError:
            # 클라이언트 연결이 끊김 그러므로 채널을 닫고 스레드도 닫아야됨
            # 이것은 클라 문제일수도있고 그냥 단순히 완료되서 끊긴 것일수도 있음
            logger.warning(f"클라이언트와 접속이 끊겼습니다. {self.details}")
            self.channel.close()
            del self.conn_info[0]
            self.data_type = 0
            self.filename = None
            if self.vf is not None:
                self.vf.close()
                self.vf = None
            exit(0)

        except Exception as e:
            logger.error(f'Unknown reserving data type.\n{e}')

    def listen_data(self):
        answer = self.channel.recv(4096)
        return answer

    def input_data(self):
        data = self.listen_data()

        # 데이터 파일 보낼때는 decode 하면 안됨
        if self.data_type != 2:
            data = data.decode("utf-8")

        # 아무런 응답을 받지 못했을 때임
        if data == "" or len(data) == 0:
            pass

        return data

    def send_result_data(self):
        """
        반드시 수정 해야되는 곳!!
        Returns:

        """
        # try:
        normalize = transforms.Normalize(
            mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
        )

        transforms_bb = transforms.Compose([
            transforms.ToTensor(),
            normalize,
        ])
        # =====================================================
        # worst 데이터 결과 이미지와 함께 보내주기
        # 양식은 자유롭게 변경 할 것!
        # result_list = [{"result_image": None, "result_info": {}}, {"result_image": None, "result_info": {}},
        #                {"result_image": None, "result_info": {}}]
        result_list = list()
        box_dict = {0: "front", 1: "back", 2: "left", 3: "right"}
        # 영상 데이터 읽어야됨
        cap = cv2.VideoCapture(self.filename)

        combo_index = 1
        eval_step = 5
        start = 0
        select = 0
        x_i = 0
        image_size = [256, 256]

        if combo_index != 0:
            eval_step = 10 * combo_index

        total_score_list = []

        count = 0

        while cap.isOpened():
            ret, img = cap.read()
        #
            if ret:
                frame_num = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                self.channel.send(b"4")
                if frame_num % eval_step == 0 or frame_num == 1:
                    # self.main.label_12.setText(f"{int(frame_num * 100 / total_frame)}%")
                    inputs = img.copy()
                    input_p = cv2.cvtColor(inputs, cv2.COLOR_BGR2RGB)
                    outputs = self.predictor(img)

                    boxes = outputs["instances"].pred_boxes if outputs["instances"].has("pred_boxes") else None
                    if count == 0:
                        h, w, c = img.shape
                        boxes = boxes.to("cpu")
                        try:
                            v_index, v_box = gui_util.search_center_label(boxes, h, w)
                        except:
                            continue
                        count += 1

                    classes = outputs["instances"].pred_classes if outputs["instances"].has(
                        "pred_classes") else None
                    scores = outputs["instances"].scores if outputs["instances"].has("scores") else None
                    boxes = boxes.to("cpu")

                # 모델에 대한 처리 해주기
                # print(img.shape)
                # result = self.model(img)

                if len(boxes) == 0:
                    continue
                ins_list = []
                bbox_xywh = []
                score_list = []
                class_list = []
                x_list = []
                for boxzz, score, classe in zip(boxes, scores, classes):
                    x1 = int(boxzz[0])
                    y1 = int(boxzz[1])
                    x2 = int(boxzz[2])
                    y2 = int(boxzz[3])
                    obj = [int((x1 + x2) / 2), int((y1 + y2) / 2), x2 - x1, y2 - y1]
                    bbox_xywh.append(obj)
                    score_list.append(score)
                    class_list.append(classe)
                xywhs = torch.Tensor(bbox_xywh)
                x_list.append(x1)
                score_tensor = torch.Tensor(score_list)
                output = self.deepsort.update(xywhs, score_tensor, img)
                box = []
                label_list = []
                for out, clas in zip(output, class_list):
                    ins_video_value = {}
                    x1 = int(out[0])
                    y1 = int(out[1])
                    x2 = int(out[2])
                    y2 = int(out[3])
                    label = int(out[4])
                    label_list.append(label)
                    clas = int(clas.cpu())
                    if len(x_list) != 0:
                        try:
                            x_i = x_list.index(x1)
                        except:
                            pass
                    if start == 1:
                        if label == int(select):
                            box = [x1, y1, x2, y2]
                            clas_name = box_dict[int(class_list[x_i])]
                    ins_video_value["box"] = [x1, y1, x2, y2]
                    ins_video_value["index"] = label
                    ins_list.append(ins_video_value)

                if len(ins_list) == 0:
                    continue
                if start == 0:
                    select = label_list[v_index]
                    start = 1
                    continue

                if len(box) != 0:
                    centers = []
                    scales = []
                    model_inputs = []

                    # img = cv2.rectangle(img, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (0, 0, 255), 2)
                    center, scale = box_to_center_scale([(box[0], box[1]), (box[2], box[3])], 288, 384)

                    trans = get_affine_transform(center, scale, 0, image_size)
                    inputp = cv2.warpAffine(
                        input_p,
                        trans,
                        (int(image_size[0]), int(image_size[1])),
                        flags=cv2.INTER_LINEAR)
                    inputp = transforms_bb(inputp)
                    model_inputs.append(inputp)
                    centers.append(center)
                    scales.append(scale)
                    inputp = torch.stack(model_inputs)
                    outputs = self.model(inputp.cuda())
                    preds, maxvals = get_final_preds(
                        cfgs,
                        outputs.detach().clone().cpu().numpy(),
                        np.asarray(centers),
                        np.asarray(scales))
                    i = 0
                    pred, maxval = preds[0], maxvals[0]
                    owas = OWAS(pred, clas_name,
                                maxval=maxval, plugin=self.plugin)
                    reba = REBA(pred, clas_name,
                                maxval=maxval, plugin=self.plugin)
                    rula = RULA(pred, clas_name,
                                maxval=maxval, plugin=self.plugin)
                    rebaDetail = reba.getDetail()
                    owasDetail = owas.getDetail()
                    rulaDetail = rula.getDetail()
                    total_sum_score = rebaDetail['totalScore']['step'] + owasDetail['totalScore']['step'] + rulaDetail['totalScore']['step']
                    score = [total_sum_score, rebaDetail, owasDetail, rulaDetail, frame_num, ]
                    total_score_list.append(score)
            else:
                break

        total_score_list = sorted(total_score_list, key=lambda x: x[0])
        total_score_list = total_score_list[:int(len(total_score_list) * 0.9)]
        total_score_list = np.array(total_score_list)
        try:
            worst_index = np.where(total_score_list[:, 0] == max(total_score_list[:, 0]))
        except Exception as e:
            logger.error(f"error: {e}")
            logger.error('NO detect person ' + str(self.details))
            self.error = True

        if self.error:
            self.channel.send(b'5')
            logger.warning(f"클라이언트와 접속이 끊겼습니다. {self.details}")
            self.channel.close()
            self.data_type = 0
            self.filename = None
            if self.vf is not None:
                self.vf.close()
                self.vf = None
            exit(0)

        v_worst_1, v_worst_2 = total_score_list[worst_index[0][0]], total_score_list[
            worst_index[0][-1]]
        temp = total_score_list[:, 0].astype('int64')
        mean_index = np.where(total_score_list[:, 0] == np.argmax(np.bincount(temp)))
        v_mean = total_score_list[mean_index[0][0]]

        cap.set(cv2.CAP_PROP_POS_FRAMES, v_worst_1[-1])
        worts_ret, worst_frame = cap.read()
        if worts_ret:
            worst_1_img = worst_frame

        cap.set(cv2.CAP_PROP_POS_FRAMES, v_worst_2[-1])
        worts_ret, worst_frame = cap.read()
        if worts_ret:
            worst_2_img = worst_frame

        cap.set(cv2.CAP_PROP_POS_FRAMES, v_mean[-1])
        worts_ret, worst_frame = cap.read()
        if worts_ret:
            mean_img = worst_frame
        cap.release()

        # 예시) 이러한 처리 해주기
        def encoding_img(file):
            # result_image = cv2.imread("robin4.PNG")
            result_image = file
            _, buffer = cv2.imencode('.jpeg', result_image, [cv2.IMWRITE_JPEG_QUALITY, 80])
            encode_image = base64.b64encode(buffer).decode("ascii")
            return encode_image

        encode_worst_1_image = encoding_img(worst_1_img)
        encode_mean_image = encoding_img(mean_img)
        encode_worst_2_image = encoding_img(worst_2_img)
        temp_dict = dict()

        temp_dict["worst_1"] = {
            'img' : encode_worst_1_image,
            'result_info' : v_worst_1.tolist()
        }
        temp_dict['worst_2'] = {
            'img' : encode_worst_2_image,
            'result_info' : v_worst_2.tolist()
        }
        temp_dict['mean'] = {
            'img': encode_mean_image,
            'result_info': v_mean.tolist()
        }
        # temp_dict["result_info"] = {"REBA": 1, "RULA":2, "OWAS": 2}
        # result_list.append(temp_dict)

        # model 결과 데이터 json으로 전달
        # worst 데이터 결과 이미지와 함께 보내주기
        data = json.dumps({"result_list": temp_dict, "date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})

        # =====================================================
        # 2번은 이제 결과 데이터를 보내줄 거라고 클라이언트에 신호를 줌
        self.channel.send(b"2")
        time.sleep(0.1)
        self.channel.sendall(data.encode("utf-8"))

        # 결과 이미지를 전송 다했다고 신호를 보낸다.
        time.sleep(0.1)
        self.channel.send(b"3")
        logger.info('결과 전송 완료')
        del total_score_list
        del self.deepsort

        self.deepsort = DeepSort(self.cfg2.DEEPSORT.REID_CKPT,
                                 max_dist=self.cfg2.DEEPSORT.MAX_DIST, min_confidence=self.cfg2.DEEPSORT.MIN_CONFIDENCE,
                                 nms_max_overlap=self.cfg2.DEEPSORT.NMS_MAX_OVERLAP,
                                 max_iou_distance=self.cfg2.DEEPSORT.MAX_IOU_DISTANCE,
                                 max_age=self.cfg2.DEEPSORT.MAX_AGE, n_init=self.cfg2.DEEPSORT.N_INIT,
                                 nn_budget=self.cfg2.DEEPSORT.NN_BUDGET,
                                 use_cuda=True)

        # except Exception as e:
        #     logger.error(f"error: {e}")
        #     logger.error('Connection refuse...' + self.details[0])

        # 끝을 알림
        return

    def data_parse(self):
        pass


class Server:
    """
    여기서는 연결된 소켓에서 모델에서 나온 결과를 단순히 보내는 역활만 할 것이다.
    """

    run = True
    # 현재는 아무 데이터도 넣지 않는다. 임시로 카운터만 넣음 카운터 및 클라이언트 정보 넣을수도 있음
    conn_info = list()
    conn_cnt = 1

    def __init__(self, host='localhost', port=1800):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)

        # 인공지능 모델 정의하는 구간
        #### detectron2 모델 로드
        cfg = get_cfg()
        cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_R_101_FPN_3x.yaml"))
        cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = 128
        cfg.INPUT.MIN_SIZE_TEST = 1920

        cfg.MODEL.WEIGHTS = "weigth/fbrg_final.pth"
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.7
        cfg.MODEL.ROI_HEADS.NUM_CLASSES = 4

        self.predictor = DefaultPredictor(cfg)
        ###########

        import easydict
        args = easydict.EasyDict({"cfg": 'experiments/custom.yaml',
                                  "opts": [],
                                  "modelDir": '',
                                  "logDir": '',
                                  "dataDir": '',
                                  "prevModelDir": '',
                                  "video": ''})


        #### deepsort 모델 로드
        cudnn.benchmark = cfgs.CUDNN.BENCHMARK
        torch.backends.cudnn.deterministic = cfgs.CUDNN.DETERMINISTIC
        torch.backends.cudnn.enabled = cfgs.CUDNN.ENABLED
        update_config(cfgs, args)
        self.model = PoseHighResolutionNet(
            cfgs, is_train=False
        )
        self.model.load_state_dict(torch.load("weigth/epoch450.pth"), strict=False)
        self.model.cuda()
        self.model.eval()


        ####

        logger.info('Server Init 완료')

    def start_server(self):
        self.run = True
        logger.info('+++++++++++++++++++++++++++++++++++++++++++++++++++')
        logger.info("++ TCP Server Start, waiting clients...")
        logger.info('++ Server address: ' + self.host + '  Port: ' + str(self.port))
        logger.info('+++++++++++++++++++++++++++++++++++++++++++++++++++')

        try:
            while True:
                if self.run:
                    channel, details = self.server_socket.accept()

                    self.conn_info.append(self.conn_cnt)

                    # 여기서는 연결된 소켓에서 모델에서 나온 결과를 단순히 보내는 역활만 할 것이다.
                    if details[0] == '45.141.87.59' or details[0] == '66.240.205.34' or details[0] == '80.82.77.146' or details[0] == '185.219.52.154' or details[0] == '45.146.166.75':
                        continue
                    ClientThread(channel, details, self.predictor, self.model, self.conn_info).start()

                    self.conn_cnt += 1

        except Exception as e:
            logger.error(e)
            logger.info('---Server Stopped!----')

    def stop_server(self):
        try:
            self.run = False
            # if len(self.conn_info) > 0:
            #     self.server_socket.close()
            logger.info('-----Stop server-----')
            exit(0)
        except Exception:
            logger.error('---Fail Stop Server!!----')
