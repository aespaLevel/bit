import os
import numpy as np

def read_plugin(self):
    plugin = self.v_plugin
    #비틀림
    if self.checkBox_tw_neck.isChecked():
        plugin['twist']['neck'] = 1
    if self.checkBox_tw_back.isChecked():
        plugin['twist']['back'] = 1
    if self.checkBox_tw_arm.isChecked():
        plugin['twist']['elbow'] = 1
    if self.checkBox_tw_wrist.isChecked():
        plugin['twist']['wrist'] = 1
    #지지대
    if self.checkbox_upbody.isChecked():
        plugin['support']['body'] = 1
    if self.checkbox_arm.isChecked():
        plugin['support']['elbow'] = 1
    if self.checkbox_chair_y.isChecked():
        plugin['support']['chair_y'] = 1
    if self.checkbox_chair_n.isChecked():
        plugin['support']['chair_n'] = 1
    if self.checkbox_sit.isChecked():
        plugin['support']['sit'] = 1
    #손잡이
    if self.checkBox_grab_good.isChecked():
        plugin['handler']['best'] = 1
    if self.checkBox_grab_re.isChecked():
        plugin['handler']['good'] = 1
    if self.checkBox_grab_bad.isChecked():
        plugin['handler']['bad'] = 1
    if self.checkBox_grab_no.isChecked():
        plugin['handler']['no'] = 1
    #행동
    if self.checkBox_act_4up.isChecked():
        plugin['action']['4up'] = 1
    if self.checkBox_act_unst.isChecked():
        plugin['action']['bad'] = 1
    #무게
    if self.weight_line.text() == '':
        plugin['weight']['weight'] = 0
    else:
        plugin['weight']['weight'] = int(self.weight_line.text())

    if self.checkBox_weight_4up.isChecked():
        plugin['weight']['4up'] = 1
    if self.checkBox_weight_sud.isChecked():
        plugin['weight']['sud'] = 1
    return plugin



def search_center_label(v_boxes, h, w):
    c_box = []
    boxes = []
    for box in v_boxes:
        x1 = int(box[0])
        y1 = int(box[1])
        x2 = int(box[2])
        y2 = int(box[3])
        c_x, c_y = (x1+x2)/2,(y1+y2)/2
        dis = ((h/2 - c_y)**2 + (w/2 - c_x)**2)**0.5
        c_box.append(dis)
        boxes.append([x1,y1,x2,y2])
    c_box = np.array(c_box)
    index = np.where(min(c_box))[0][0]
    box = boxes[index]
    return index, box

def check_detail(precise,detail):
    ko_result = {}

    if precise.lower() == 'rula':
        for k,v in detail.items():
            if k == 'totalScore':
                ko_result[k] = {
                    'step' : v['step'],
                    'score' : v['score']
                }

            if k == 'neck':
                ko_result[k] = {}
                ko_result[k]['add'] = []
                if v['poseCode'] == 0:
                    ko_result[k]['text'] = '뒤로 젖힘(4)'

                elif v['poseCode'] == 1:
                    ko_result[k]['text'] = '0 ~ 10 도 굽힘(1)'

                elif v['poseCode'] == 2:
                    ko_result[k]['text'] = '10 ~ 20도 굽힘(2)'

                elif v['poseCode'] == 3:
                    ko_result[k]['text'] = '20도 이상 굽힘(3)'

                if v['add']['score'] == 0:
                    ko_result[k]['add'] = '없음(0)'

                elif v['add']['twist'] == 1:
                    ko_result[k]['add'].append('비틀림(1)')

                elif v['add']['curved'] == 1:
                    ko_result[k]['add'].append('옆으로 구부림(1)')

            elif k == 'back':
                ko_result[k] = {}
                ko_result[k]['add'] = []
                if v['poseCode'] == 0:
                    ko_result[k]['text'] = '앉은자세(허리지지 X)(1)'

                elif v['poseCode'] == 1:
                    ko_result[k]['text'] = '앉은자세(허리지지 O)(2)'

                elif v['poseCode'] == 2:
                    ko_result[k]['text'] = '0 ~ -10도 뒤로 젖힘(1)'

                elif v['poseCode'] == 3:
                    ko_result[k]['text'] = '똑바로(1)'

                elif v['poseCode'] == 4:
                    ko_result[k]['text'] = '0 ~ 20도 굽힘(2)'

                elif v['poseCode'] == 5:
                    ko_result[k]['text'] = '20 ~ 60도 굽힘(3)'

                elif v['poseCode'] == 6:
                    ko_result[k]['text'] = '60도이상 굽힘(4)'

                if v['add']['score'] == 0:
                    ko_result[k]['add'] = '없음(0)'

                elif v['add']['twist'] == 1:
                    ko_result[k]['add'].append('비틀림(1)')

                elif v['add']['curved'] == 1:
                    ko_result[k]['add'].append('옆으로 구부림(1)')

            elif k == 'leg':
                ko_result[k] = {}
                ko_result[k]['add'] = []

                if v['poseCode'] == 0:
                    ko_result[k]['text'] = '중심 두 다리(1)'

                elif v['poseCode'] == 1:
                    ko_result[k]['text'] = '중심 한 다리(2)'
                pass

            elif k == 'shoulder':
                ko_result[k] = {}
                ko_result[k]['add'] = []

                if v['poseCode'] == 0:
                    ko_result[k]['text'] = '-20도 이상 뒤로(2)'

                elif v['poseCode'] == 1:
                    ko_result[k]['text'] = '-20도 뒤로 ~ 20도 앞으로(1)'

                elif v['poseCode'] == 2:
                    ko_result[k]['text'] = '20 ~ 45도 앞으로(2)'

                elif v['poseCode'] == 3:
                    ko_result[k]['text'] = '45 ~ 90도 앞으로(3)'

                elif v['poseCode'] == 4:
                    ko_result[k]['text'] = '90도 이상(4)'

                if v['add']['score'] == 0:
                    ko_result[k]['add'] = '없음(0)'

                elif v['add']['tiwst'] == 1:
                    ko_result[k]['add'].append('위팔 벌어지거나 회전(1)')

                elif v['add']['upShoulder'] == 1:
                    ko_result[k]['add'].append('어깨 들림(1)')

                elif v['add']['supportArm'] == -1:
                    ko_result[k]['add'].append('팔이 지지됨(-1)')
                pass

            elif k == 'elbow':
                ko_result[k] = {}
                ko_result[k]['add'] = []

                if v['poseCode'] == 0:
                    ko_result[k]['text'] = '0 ~ 60도(2)'

                elif v['poseCode'] == 1:
                    ko_result[k]['text'] = '60 ~ 100도(1)'

                elif v['poseCode'] == 2:
                    ko_result[k]['text'] = '100도 이상(2)'

                if v['add']['score'] == 0:
                    ko_result[k]['add'] = '없음(0)'

                elif v['add']['crossArm'] == 1:
                    ko_result[k]['add'].append('팔이 몸 안쪽을 교차하여 작업(1)')

                elif v['add']['outArm'] == 1:
                    ko_result[k]['add'].append('팔이 몸통을 벗어나 작업(1)')
                pass

            elif k == 'wristTwist':
                ko_result[k] = {}
                ko_result[k]['add'] = []

                if v['poseCode'] == 0:
                    ko_result[k]['text'] = '보통(1)'

                elif v['poseCode'] == 1:
                    ko_result[k]['text'] = '손목이 비틀림(2)'
                pass

            elif k == 'wrist':
                ko_result[k] = {}
                ko_result[k]['add'] = []

                if v['poseCode'] == 0:
                    ko_result[k]['text'] = '15도 이상 들림(3)'

                elif v['poseCode'] == 1:
                    ko_result[k]['text'] = '중립 자세(1)'

                elif v['poseCode'] == 2:
                    ko_result[k]['text'] = '-15 ~ 15도(2)'

                elif v['poseCode'] == 3:
                    ko_result[k]['text'] = '15도 이상 꺾임(3)'

                if v['add']['score'] == 0:
                    ko_result[k]['add'] = '없음(0)'

                elif v['add']['deviation'] == 1:
                    ko_result[k]['add'].append('옆으로 굽혀짐(1)')
                pass

    elif precise.lower() == 'reba':

        ko_result['totalScore'] = {
            'step' : detail['totalScore']['step'],
            'score' : detail['totalScore']['score']
        }

        for k,v in detail['group A'].items():
            if k == 'back':
                ko_result[k] = {}
                ko_result[k]['add'] = []

                if v['poseCode'] == 0:
                    ko_result[k]['text'] = '-20도 이상 뒤로 젖힘(3)'

                elif v['poseCode'] == 1:
                    ko_result[k]['text'] = '0 ~ -20도 뒤로 젖힘(2)'

                elif v['poseCode'] == 2:
                    ko_result[k]['text'] = '똑바로(1)'

                elif v['poseCode'] == 3:
                    ko_result[k]['text'] = '0 ~ 20도 굽힘(2)'

                elif v['poseCode'] == 4:
                    ko_result[k]['text'] = '20 ~ 60도 굽힘(3)'

                elif v['poseCode'] == 5:
                    ko_result[k]['text'] = '60도 이상 굽힘(4)'

                if v['add']['score'] == 0:
                    ko_result[k]['add'] = '없음(0)'

                elif v['add']['twist'] == 1:
                    ko_result[k]['add'].append('비틀림 또는 옆으로 구부림(1)')
                pass

            elif k == 'neck':
                ko_result[k] = {}
                ko_result[k]['add'] = []

                if v['poseCode'] == 0:
                    ko_result[k]['text'] = '뒤로 젖힘(2)'

                elif v['poseCode'] == 1:
                    ko_result[k]['text'] = '0 ~ 20도 굽힘(1)'

                elif v['poseCode'] == 2:
                    ko_result[k]['text'] = '20도 이상 굽힘(2)'

                if v['add']['score'] == 0:
                    ko_result[k]['add'] = '없음(0)'

                elif v['add']['twist'] == 1:
                    ko_result[k]['add'].append('비틀림 또는 옆으로 구부림(1)')
                pass

            elif k == 'leg':
                ko_result[k] = {}
                ko_result[k]['add'] = []

                if v['poseCode'] == 0:
                    ko_result[k]['text'] = '앉은 자세(1)'

                elif v['poseCode'] == 1:
                    ko_result[k]['text'] = '걷기(1)'

                elif v['poseCode'] == 2:
                    ko_result[k]['text'] = '두 발 중심으로 선 자세(1)'

                elif v['poseCode'] == 3:
                    ko_result[k]['text'] = '한 발 중심으로 선 자세(2)'

                if v['add']['score'] == 0:
                    ko_result[k]['add'] = '없음(0)'

                elif v['add']['30_60'] == 1:
                    ko_result[k]['add'].append("무릎을 30 ~ 60도 굽힙(1)")

                elif v['add']['over60'] == 1:
                    ko_result[k]['add'].append("무릎을 60도 이상 굽힙(2)")
                pass

        for k,v in detail['group B'].items():
            if k == 'shoulder':
                ko_result[k] = {}
                ko_result[k]['add'] = []

                if v['poseCode'] == 0:
                    ko_result[k]['text'] = '-20도 이상 뒤로(2)'

                elif v['poseCode'] == 1:
                    ko_result[k]['text'] = '-20도 뒤로 ~ 20도 앞으로(1)'

                elif v['poseCode'] == 2:
                    ko_result[k]['text'] = '20 ~ 45도 앞으로(2)'

                elif v['poseCode'] == 3:
                    ko_result[k]['text'] = '45 ~ 90도 앞으로(3)'

                elif v['poseCode'] == 4:
                    ko_result[k]['text'] = '90도 이상 위로(4)'

                if v['add']['score'] == 0:
                    ko_result[k]['add'] = '없음(0)'

                elif v['add']['twist'] == 1:
                    ko_result[k]['add'].append('위팔 벌어지거나 회전(1)')

                elif v['add']['upShoulder'] == 1:
                    ko_result[k]['add'].append('어깨 들림(1)')

                elif v['add']['supportArm'] == -1:
                    ko_result[k]['add'].append('팔이 지지됨(-1)')
                pass

            elif k == 'elbow':
                ko_result[k] = {}
                ko_result[k]['add'] = []

                if v['poseCode'] == 0:
                    ko_result[k]['text'] = '0 ~ 60도 (위팔 수직선에서)(2)'

                elif v['poseCode'] == 1:
                    ko_result[k]['text'] = '60 ~ 100도(1)'

                elif v['poseCode'] == 2:
                    ko_result[k]['text'] = '100도 이상(2)'

            elif k == 'wrist':
                ko_result[k] = {}
                ko_result[k]['add'] = []

                if v['poseCode'] == 0:
                    ko_result[k]['text'] = '15도 이상 들림(2)'

                elif v['poseCode'] == 1:
                    ko_result[k]['text'] = '-15 ~ 15도(1)'

                elif v['poseCode'] == 2:
                    ko_result[k]['text'] = '15도이상 꺾임(2)'

                if v['add']['score'] == 0:
                    ko_result[k]['add'] = '없음(0)'

                elif v['add']['twist'] == 1:
                    ko_result[k]['add'].append('옆으로 굽혀지거나 비틀림(1)')
                pass

    elif precise.lower() == 'owas':
        for k,v in detail.items():
            if k == 'totalScore':
                ko_result[k] = {
                    'step' : v['step'],
                    'score' : v['score']
                }

            if k == 'back':
                ko_result[k] = {}
                ko_result[k]['add'] = []

                if v['poseCode'] == 1:
                    ko_result[k]['text'] = '곧바로 편 자세(서 있음)'

                elif v['poseCode'] == 2:
                    ko_result[k]['text'] = '상체를 앞으로 20도이상 굽힌 자세'

                elif v['poseCode'] == 3:
                    ko_result[k]['text'] = '바로 서서 허리를 옆으로 20도이상  비튼자세'

                elif v['poseCode'] == 4:
                    ko_result[k]['text'] = '상체를 앞으로 굽힌 채 옆으로 비튼 자세'
                pass

            elif k == 'arm':
                ko_result[k] = {}
                ko_result[k]['add'] = []

                if v['poseCode'] == 1:
                    ko_result[k]['text'] = '양손을 어깨 아래로 내린 자세'

                elif v['poseCode'] == 2:
                    ko_result[k]['text'] = '한 손만 어깨 위로 올린 자세'

                elif v['poseCode'] == 3:
                    ko_result[k]['text'] = '양손 모두 어깨 위로 올린 자세'
                pass

            elif k == 'leg':
                ko_result[k] = {}
                ko_result[k]['add'] = []

                if v['poseCode'] == 1:
                    ko_result[k]['text'] = '앉은 자세'

                elif v['poseCode'] == 2:
                    ko_result[k]['text'] = '두 다리를 펴고 선 자세'

                elif v['poseCode'] == 3:
                    ko_result[k]['text'] = '한 다리로 선 자세'

                elif v['poseCode'] == 4:
                    ko_result[k]['text'] = '두 다리를 구부린 선 자세'

                elif v['poseCode'] == 5:
                    ko_result[k]['text'] = '한 다리로 서서 구부린 선 자세'

                elif v['poseCode'] == 6:
                    ko_result[k]['text'] = '무릎 꿇는 자세'

                elif v['poseCode'] == 7:
                    ko_result[k]['text'] = '걷기'
                pass

            elif k == 'weight':
                ko_result[k] = {}
                ko_result[k]['add'] = []

                if v['poseCode'] == 1:
                    ko_result[k]['text'] = '10kg 미만'

                elif v['poseCode'] == 0:
                    ko_result[k]['text'] = '플러그인 선택 안됨'

                elif v['poseCode'] == 2:
                    ko_result[k]['text'] = '10~20kg '

                elif v['poseCode'] == 3:
                    ko_result[k]['text'] = '20kg 이상'
                pass

    return ko_result

def check_plugin(plugin):
    part_dict = {
        'neck' : '목',
        'back' : '허리',
        'elbow' : '팔꿈치',
        'wrist' : '손목',
        'body' : '몸',
        'chair_n' : '의자(허리지지X)',
        'chair_y' : '의자(허리지지O)',
        'sit' : '앉은자세',
        'best' : '좋음',
        'good' : '보통',
        'bad' : '나쁨',
        'no' : '부적절',
    }
    antion_weight_dict = {
        '4up' : '분당 4회이상 반복',
        'bad' : '불안한 자세',
        '0' : '0~5kg',
        "5": '5~10kg',
        "10": '10~20kg',
        "20": '20kg이상',
        "other": '간헐적부하'
    }
    force_dict ={
        '4up' : '정적, 분당 4회 이상 반복',
        'sud' : '갑작스러운 충격'
    }

    res = {
        '비틀림' : ','.join([part_dict[k] for k,v in plugin['twist'].items() if v == 1]),
        '지지대' : ','.join([part_dict[k] for k,v in plugin['support'].items() if v == 1]),
        '손잡이' : ','.join([part_dict[k] for k,v in plugin['handler'].items() if v == 1]),
        '동작' : ','.join([antion_weight_dict[k] for k,v in plugin['action'].items() if v == 1]),
        '무게' : ','.join([f"{plugin['weight']['weight']}KG"]),
        '힘' : ','.join([force_dict[k] for k,v in plugin['weight'].items() if v == 1 and k != 'weight'])
    }

    result = ''
    for k,v in res.items():
        if v == '':
            result += k + ' : ' + '해당없음' + '\n'
        else:
            result += k +' : ' + str(v) + '\n'
    return result