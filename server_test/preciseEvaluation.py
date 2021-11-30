import numpy as np
import math


def angle_between(p1, p2):
    ang1 = np.arctan2(*p1[::-1])
    ang2 = np.arctan2(*p2[::-1])
    res = np.rad2deg((ang1 - ang2) % (2 * np.pi))
    return res

def getAngle3P(p1,centerP,p2):

    # if None in [p1,centerP,p2]:
    #     return False
    pt1 = (p1[0] - centerP[0], p1[1] - centerP[1])
    pt2 = (p2[0] - centerP[0], p2[1] - centerP[1])
    res = angle_between(pt1, pt2)
    res = (res + 360) % 360
    if res > 180:
        res = 360 - res
    return res

def getDist2P(p1,p2):
    x = (p1[0] - p2[0]) ** 2
    y = (p1[1] - p2[1]) ** 2
    dist = math.sqrt(x + y)
    return dist

class OWAS:
    def __init__(self,keypoints,label = None, **kwargs):
        self.class_list = ["head", "neck-up", "neck-down", "spine-1",
                      "spine-2", "r-shou", "l-shou",
                      "r-elbow", "l-elbow", "r-wrist", "l-wrist",
                      "r-hand", "l-hand", "r-hip", "l-hip",
                      "r-knee", "l-knee", "r-ankle", "l-ankle"]
        self.label = label
        self.KEY_DICT = {k: v for k, v in zip(self.class_list, keypoints)}

        self.maxval = kwargs['maxval'] if 'maxval' in kwargs.keys() else None
        self.plugin = kwargs['plugin'] if 'plugin' in kwargs.keys() else None

        self.update()

    def update(self):
        self.addArm()
        self.addLeg()
        self.addBack()
        self.addWeight()
        self.calScore()

    def addWeight(self):
        weight_int = int(self.plugin['weight']['weight'])

        if weight_int < 10:
            self.weight = {
                'poseCode' : 1,
                'detail' : 'under 10kg'
            }
        elif 10 <= weight_int < 20:
            self.weight = {
                'poseCode': 2,
                'detail': 'between 10kg and 20kg'
            }
        elif 20 <= weight_int:
            self.weight = {
                'poseCode' : 3,
                'detail' : 'up 20kg'
            }
        else:
            self.weight = {
                'poseCode': 0,
                'detail': 'sometime attack'
            }

    def _oneD(self,p1, p2, benchmark):
        try:
            x1, y1, x2, y2, a1, a2 = p1[0], p1[1], p2[0], p2[1], benchmark[0], benchmark[1]
            a = (x2 - x1) / (y2 - y1)
            r = a * x1
            b = y1 - r
            t = a * a1 + b
        except:
            return 'right'
        if a < 0:
            if t - a2 > 0:
                return 'right'
            else:
                return 'left'
        else:
            if t - a2 > 0:
                return 'right'
            else:
                return 'left'

    def addBack(self):

        self.back = {
            'poseCode' : 1,
            'detail' : ''
        }
        backAngle = getAngle3P(self.KEY_DICT['neck-down'], self.KEY_DICT['spine-2'],
                               [self.KEY_DICT['spine-2'][0], self.KEY_DICT['spine-2'][1] - 20])
        if self.label == 'right':
            if self.KEY_DICT['neck-down'][0] < self.KEY_DICT['spine-2'][0]:
                backAngle *= -1
            else:
                pass
            if backAngle > 45:
                rElbow = self._oneD(self.KEY_DICT['neck-down'],self.KEY_DICT['spine-2'],self.KEY_DICT['r-elbow'])
                lElbow = self._oneD(self.KEY_DICT['neck-down'],self.KEY_DICT['spine-2'],self.KEY_DICT['l-elbow'])
                rHand = self._oneD(self.KEY_DICT['neck-down'], self.KEY_DICT['spine-2'], self.KEY_DICT['r-hand'])
                lHand = self._oneD(self.KEY_DICT['neck-down'], self.KEY_DICT['spine-2'], self.KEY_DICT['l-hand'])

                if rElbow == 'right' and rHand =='right' and lElbow == 'left' and lHand == 'left':
                    self.back['poseCode'] = 4
                    self.back['detail'] = 'stand curved and twist'
                elif rElbow == 'left' and rHand =='left' and lElbow == 'right' and lHand == 'right':
                    self.back['poseCode'] = 4
                    self.back['detail'] = 'stand curved and twist'
                else:
                    self.back['poseCode'] = 2
                    self.back['detail'] = 'just stand curved'

            else:
                rElbow = self._oneD(self.KEY_DICT['neck-down'], self.KEY_DICT['spine-2'], self.KEY_DICT['r-elbow'])
                lElbow = self._oneD(self.KEY_DICT['neck-down'], self.KEY_DICT['spine-2'], self.KEY_DICT['l-elbow'])
                rHand = self._oneD(self.KEY_DICT['neck-down'], self.KEY_DICT['spine-2'], self.KEY_DICT['r-hand'])
                lHand = self._oneD(self.KEY_DICT['neck-down'], self.KEY_DICT['spine-2'], self.KEY_DICT['l-hand'])

                if rElbow == 'right' and rHand == 'right' and lElbow == 'left' and lHand == 'left':
                    self.back['poseCode'] = 3
                    self.back['detail'] = 'stand straight and twist'

                elif rElbow == 'left' and rHand == 'left' and lElbow == 'right' and lHand == 'right':
                    self.back['poseCode'] = 3
                    self.back['detail'] = 'stand straight and twist'

                else:
                    self.back['poseCode'] = 1
                    self.back['detail'] = 'just stand straight'

        elif self.label == 'left':
            if self.KEY_DICT['neck-down'][0] > self.KEY_DICT['spine-2'][0]:
                backAngle *= -1
            else:
                pass

            if backAngle > 45:
                pass

            else:
                self.back['poseCode'] = 1
                self.back['detail'] = 'just stand straight'
                pass
        else:
            if backAngle > 45:
                self.back['poseCode'] = 2
                self.back['detail'] = 'just stand curved'
            else:
                self.back['poseCode'] = 2
                self.back['detail'] = 'just stand straight'
        pass

    def addArm(self):
        self.arm = {
            'poseCode': 0,
            'detail': ''
        }
        rHand = self.KEY_DICT['r-hand']
        lHand = self.KEY_DICT['l-hand']
        rShou = self.KEY_DICT['r-shou']
        lShou = self.KEY_DICT['l-shou']
        mShou = [(r+l)/2 for r,l in zip(rShou,lShou)]

        if mShou[1] > rHand[1] and mShou[1] > lHand[1]:
            '''
            양손 모두 어깨 위로 올린 자세
            '''
            self.arm['poseCode'] = 3
            self.arm['detail'] = 'put up both arm'

        elif mShou[1] <= rHand[1] and mShou[1] > lHand[1]:
            '''
            한 손만 어깨 위로 올린 자세
            '''
            self.arm['poseCode'] = 2
            self.arm['detail'] = 'put up one arm'

        elif mShou[1] > rHand[1] and mShou[1] <= lHand[1]:
            '''
            한 손만 어깨 위로 올린 자세
            '''
            self.arm['poseCode'] = 2
            self.arm['detail'] = 'put up one arm'

        elif mShou[1] <= rHand[1] and mShou[1] <= lHand[1]:
            '''
            양손을 어깨 아래로 내린 자세
            '''
            self.arm['poseCode'] = 1
            self.arm['detail'] = 'put down both arm'

    def addLeg(self):
        self.leg = {
            'poseCode': 1,
            'detail': ''
        }

        rLegAngle = getAngle3P(self.KEY_DICT['r-hip'],self.KEY_DICT['r-knee'],self.KEY_DICT['r-ankle'])
        lLegAngle = getAngle3P(self.KEY_DICT['l-hip'],self.KEY_DICT['l-knee'],self.KEY_DICT['l-ankle'])

        rHipAngle = getAngle3P(self.KEY_DICT['r-shou'],self.KEY_DICT['r-hip'],self.KEY_DICT['r-knee'])
        lHipAngle = getAngle3P(self.KEY_DICT['l-shou'], self.KEY_DICT['l-hip'], self.KEY_DICT['l-knee'])

        rKnee = self.KEY_DICT['r-knee']
        lKnee = self.KEY_DICT['l-knee']
        rAnkle = self.KEY_DICT['r-ankle']
        lAnkle = self.KEY_DICT['l-ankle']

        thr = max(getDist2P(self.KEY_DICT['neck-up'],self.KEY_DICT['r-ankle']),getDist2P(self.KEY_DICT['neck-up'],self.KEY_DICT['l-ankle']))

        if self.label == 'right' or self.label == 'left' or self.label == 'front' or self.label == 'back':
            rLegState = 0
            lLegState = 0
            if rLegAngle < 140:
                rLegState = 1
            if lLegAngle < 140:
                lLegState = 1

            if self.plugin['support']['sit'] == 1 or self.plugin['support']['chair_n'] == 1 or self.plugin['support']['chair_y'] == 1:
                self.leg['poseCode'] = 1
                self.leg['detail'] = 'sit'

            elif rLegState == 0 and lLegState == 0:
                self.leg['poseCode'] = 2
                self.leg['detail'] = 'normal'

            elif rLegState != lLegState:
                self.leg['poseCode'] = 3
                self.leg['detail'] = 'stand one leg'

            elif rLegState == 1 and lLegState == 1:
                if abs(rKnee[1] - rAnkle[1]) <=  thr * 0.1 or abs(lKnee[1] - lAnkle[1]) <= thr * 0.1:
                    self.leg['poseCode'] = 6
                    self.leg['detail'] = 'kneel'

                elif abs(rKnee[1] - lKnee[1]) <= thr * 0.1:
                    self.leg['poseCode'] = 5
                    self.leg['detail'] = 'stand curved one leg'

                else:
                    self.leg['poseCode'] = 4
                    self.leg['detail'] = 'stand curved two leg'

    def calScore(self):
        # scoreTable[back][arm][leg][weight]
        scoreTable = \
            [
                [
                    [
                        [1, 1, 1],
                        [1, 1, 1],
                        [1, 1, 1],
                        [2, 2, 2],
                        [2, 2, 2],
                        [1, 1, 1],
                        [1, 1, 1]
                    ],
                    [
                        [1, 1, 1],
                        [1, 1, 1],
                        [1, 1, 1],
                        [2, 2, 2],
                        [2, 2, 2],
                        [1, 1, 1],
                        [1, 1, 1]
                    ],
                    [
                        [1, 1, 1],
                        [1, 1, 1],
                        [1, 1, 1],
                        [2, 2, 3],
                        [2, 2, 3],
                        [1, 1, 1],
                        [1, 1, 2]
                    ],
                ],
                [
                    [
                        [2, 2, 3],
                        [2, 2, 3],
                        [2, 2, 3],
                        [3, 3, 3],
                        [3, 3, 3],
                        [2, 2, 2],
                        [2, 3, 3]
                    ],
                    [
                        [2, 2, 3],
                        [2, 2, 3],
                        [2, 3, 3],
                        [3, 4, 4],
                        [3, 4, 4],
                        [3, 3, 4],
                        [2, 3, 4]
                    ],
                    [
                        [3, 3, 4],
                        [2, 2, 3],
                        [3, 3, 3],
                        [3, 4, 4],
                        [4, 4, 4],
                        [4, 4, 4],
                        [2, 3, 4]
                    ]
                ],
                [
                    [
                        [1, 1, 1],
                        [1, 1, 1],
                        [1, 1, 2],
                        [3, 3, 3],
                        [4, 4, 4],
                        [1, 1, 1],
                        [1, 1, 1]
                    ],
                    [
                        [2, 2, 3],
                        [1, 1, 1],
                        [1, 1, 2],
                        [4, 4, 4],
                        [4, 4, 4],
                        [3, 3, 3],
                        [1, 1, 1]
                    ],
                    [
                        [2, 2, 3],
                        [1, 1, 1],
                        [2, 3, 3],
                        [4, 4, 4],
                        [4, 4, 4],
                        [4, 4, 4],
                        [1, 1, 1]
                    ]
                ],
                [
                    [
                        [2, 3, 3],
                        [2, 2, 3],
                        [2, 2, 3],
                        [4, 4, 4],
                        [4, 4, 4],
                        [4, 4, 4],
                        [2, 3, 4]
                    ],
                    [
                        [3, 3, 4],
                        [2, 3, 4],
                        [3, 3, 4],
                        [4, 4, 4],
                        [4, 4, 4],
                        [4, 4, 4],
                        [2, 3, 4]
                    ],
                    [
                        [4, 4, 4],
                        [2, 3, 4],
                        [3, 3, 4],
                        [4, 4, 4],
                        [4, 4, 4],
                        [4, 4, 4],
                        [2, 3, 4]
                    ]
                ]
            ]
        if self.back['poseCode'] == 0 or self.leg['poseCode'] == 0 or self.arm['poseCode'] == 0:
            self.score = 0
        else:
            self.score = scoreTable[self.back['poseCode']-1][self.arm['poseCode']-1][self.leg['poseCode']-1][self.weight['poseCode']-1]

        if self.score == 1:
            self.scoreTotal = {
                'step': 1,
                'score': self.score,
                'danger': '양호',
                'action': '양호'
            }
        elif self.score == 2:
            self.scoreTotal = {
                'step': 2,
                'score': self.score,
                'danger': '지속적 관찰',
                'action': '지속적 관찰'
            }
        elif self.score == 3:
            self.scoreTotal = {
                'step': 3,
                'score': self.score,
                'danger': '개선',
                'action': '개선'
            }
        elif self.score == 4:
            self.scoreTotal = {
                'step': 4,
                'score': self.score,
                'danger': '즉시 개선',
                'action': '즉시 개선'
            }

    def getDetail(self):
        totalDetail = {
            'totalScore' : self.scoreTotal,
            'back' : self.back,
            'arm' : self.arm,
            'leg' : self.leg,
            'weight' :  self.weight,
        }
        return totalDetail

class REBA:
    def __init__(self,keypoints,label = None, **kwargs):
        self.gA = {
            'score' : 0,
            'back' : None,
            'neck' : None,
            'leg' : None
        }
        self.gB = {
            'score' : 0,
            'shoulder' : None,
            'elbow' : None,
            'wrist' : None
        }

        self.class_list = ["head", "neck-up", "neck-down", "spine-1",
                      "spine-2", "r-shou", "l-shou",
                      "r-elbow", "l-elbow", "r-wrist", "l-wrist",
                      "r-hand", "l-hand", "r-hip", "l-hip",
                      "r-knee", "l-knee", "r-ankle", "l-ankle"]
        self.label = label
        self.KEY_DICT = {k: v for k, v in zip(self.class_list, keypoints)}

        self.maxval = kwargs['maxval'] if 'maxval' in kwargs.keys() else None
        self.plugin = kwargs['plugin'] if 'plugin' in kwargs.keys() else None

        self.calScore()

    def update(self):
        self.addBack()
        self.addNeck()
        self.addLeg()
        self.addElbow()
        self.addWrist()
        self.addShoulder()

        self.gA['back'] = self.back
        self.gA['neck'] = self.neck
        self.gA['leg'] = self.leg
        self.gB['shoulder'] = self.shoulder
        self.gB['elbow'] = self.elbow
        self.gB['wrist'] = self.wrist

    def calScore(self):

        '''
        scoreATable[neck][body][leg]
        scoreBTable[elbow][shoulder][wrist]
        scoreTotal[scoreA][scoreB]
        '''

        scoreC = [
            [1, 1, 1, 2, 3, 3, 4, 5, 6, 7, 7, 7],
            [1, 2, 2, 3, 4, 4, 5, 6, 6, 7, 7, 8],
            [2, 3, 3, 3, 4, 5, 6, 7, 7, 8, 8, 8],
            [3, 4, 4, 4, 5, 6, 7, 8, 8, 9, 9, 9],
            [4, 4, 4, 5, 6, 7, 8, 8, 9, 9, 9, 9],
            [6, 6, 6, 7, 8, 8, 9, 10, 10, 10, 10, 10],
            [7, 7, 7, 8, 9, 9, 10, 10, 11, 11, 11, 11],
            [8, 8, 8, 9, 10, 10, 10, 10, 11, 11, 11, 11],
            [9, 9, 9, 10, 10, 10, 11, 11, 11, 12, 12, 12],
            [10, 10, 10, 11, 11, 11, 11, 12, 12, 12, 12, 12],
            [11, 11, 11, 11, 12, 12, 12, 12, 12, 12, 12, 12],
            [12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12]
        ]
        scoreATable = [
            [
                [1, 2, 3, 4],
                [2, 3, 4, 5],
                [2, 4, 5, 6],
                [3, 5, 6, 7],
                [4, 6, 7, 8]
            ],
            [
                [1, 2, 3, 4],
                [3, 4, 5, 6],
                [4, 5, 6, 7],
                [5, 6, 7, 8],
                [6, 7, 8, 9]
            ],
            [
                [3, 3, 5, 6],
                [4, 5, 6, 7],
                [5, 6, 7, 8],
                [6, 7, 8, 9],
                [7, 8, 9, 9]
            ]
        ]
        scoreBTable = [
            [
                [1, 2, 2],
                [1, 2, 3],
                [3, 4, 5],
                [4, 5, 6],
                [7, 8, 9],
                [7, 8, 8],
            ],
            [
                [1, 2, 3],
                [2, 3, 4],
                [4, 5, 6],
                [5, 6, 7],
                [7, 8, 8],
                [8, 9, 9]
            ]
        ]

        self.update()

        grab = 0
        try:
            kind = [k for k,v in self.plugin['handler'].items() if v == 1][0]
        except:
            kind = 'nothing'

        if kind == 'best':
            grab = 0
        elif kind == 'good':
            grab = 1
        elif kind == 'bad':
            grab = 2
        elif kind == 'no':
            grab = 3

        weight = 0
        we_int = int(self.plugin['weight']['weight'])
        if we_int < 5:
            weight = 0

        elif we_int < 10:
            weight = 1

        else:
            weight = 2

        if int(self.plugin['weight']['sud']) == 1:
            weight += 1

        neckScore = self.gA['neck']['poseScore'] + self.gA['neck']['add']['score'] - 1
        backScore = self.gA['back']['poseScore'] + self.gA['back']['add']['score'] - 1
        legScore = self.gA['leg']['poseScore'] - 1

        shoulderScore = self.gB['shoulder']['poseScore'] + self.gB['shoulder']['add']['score'] - 1
        wristScore = self.gB['wrist']['poseScore'] + self.gB['wrist']['add']['score'] - 1
        elbowScore = self.gB['elbow']['poseScore'] - 1

        self.gA['score'] = scoreATable[neckScore][backScore][legScore] + weight
        self.gB['score'] = scoreBTable[elbowScore][shoulderScore][wristScore] + grab

        '''
        need to add action score
        '''
        actionScore = 0

        if self.plugin['action']['4up'] == 1:
            actionScore += 1

        if self.plugin['action']['bad'] == 1:
            actionScore += 1


        self.scoreC = scoreC[self.gA['score']-1][self.gB['score']-1]
        self.REBAscore = self.scoreC + actionScore

        if self.REBAscore == 1:
            self.scoreTotal = {
                'step' : 0,
                'score' : self.REBAscore,
                'danger' : '무시해도 좋음',
                'action' : '필요없음'
            }

        elif 1 < self.REBAscore <= 3:
            self.scoreTotal = {
                'step': 1,
                'score': self.REBAscore,
                'danger': '낮음',
                'action': '필요할지도 모름'
            }

        elif 3 < self.REBAscore <= 7:
            self.scoreTotal = {
                'step': 2,
                'score': self.REBAscore,
                'danger': '보통',
                'action': '필요함'
            }

        elif 7 < self.REBAscore <= 10:
            self.scoreTotal = {
                'step': 3,
                'score': self.REBAscore,
                'danger': '높음',
                'action': '지금 즉시 필요함'
            }

        elif 10 < self.REBAscore:
            self.scoreTotal = {
                'step': 4,
                'score': self.REBAscore,
                'danger': '매우 높음',
                'action': '곧 필요함'
            }

        return self.gA, self.gB,self.scoreC, self.scoreTotal

    def addBack(self):
        self.back = {
            'poseCode' : int,
            'poseScore' : int,
            'detail' : str,
            'add' : {
                'score' : 0,
                'twist' : 0
            }
        }
        if self.plugin['twist']['back'] == 1:
            self.back['add']['twist'] = 1
            self.back['add']['score'] += 1


        backAngle = getAngle3P(self.KEY_DICT['neck-down'], self.KEY_DICT['spine-2'],
                               [self.KEY_DICT['spine-2'][0], self.KEY_DICT['spine-2'][1] - 20])
        if self.label == 'right':
            if self.KEY_DICT['neck-down'][0] < self.KEY_DICT['spine-2'][0]:
                backAngle *= -1
            else:
                pass

        elif self.label == 'left':
            if self.KEY_DICT['neck-down'][0] > self.KEY_DICT['spine-2'][0]:
                backAngle *= -1
            else:
                pass

        if backAngle < -20:
            self.back['poseCode'] = 0
            self.back['poseScore'] = 3
            self.back['detail'] = 'back over -20'

        elif -20 <= backAngle < -5:
            self.back['poseCode'] = 1
            self.back['poseScore'] = 2
            self.back['detail'] = 'back between -20 and 0'

        elif -5 <= backAngle < 10:
            self.back['poseCode'] = 2
            self.back['poseScore'] = 1
            self.back['detail'] = 'straight'

        elif 10 <= backAngle < 30:
            self.back['poseCode'] = 3
            self.back['poseScore'] = 2
            self.back['detail'] = 'forward between 0 and 20'

        elif 30 <= backAngle < 70:
            self.back['poseCode'] = 4
            self.back['poseScore'] = 3
            self.back['detail'] = 'forward between 20 and 60'

        elif 70 <= backAngle:
            self.back['poseCode'] = 5
            self.back['poseScore'] = 4
            self.back['detail'] = 'forward over 60'

    def addNeck(self):
        self.neck = {
            'poseCode': int,
            'poseScore': int,
            'detail': str,
            'add' : {
                'score' : 0,
                'twist' : 0
            }
        }

        if self.plugin['twist']['neck'] == 1:
            self.neck['add']['twist'] = 1
            self.neck['add']['score'] += 1


        neckAngle = 180 - getAngle3P(self.KEY_DICT['neck-up'], self.KEY_DICT['neck-down'],
                               self.KEY_DICT['spine-1'])

        if self.label == 'right':
            if self.KEY_DICT['neck-down'][0] < self.KEY_DICT['spine-1'][0]:
                neckAngle *= -1
            else:
                pass

        elif self.label == 'left':
            if self.KEY_DICT['neck-down'][0] > self.KEY_DICT['spine-1'][0]:
                neckAngle *= -1
            else:
                pass

        if neckAngle < 0:
            self.neck['poseCode'] = 0
            self.neck['poseScore'] = 2
            self.neck['detail'] = 'back'

        elif 0 <= neckAngle < 62:
            self.neck['poseCode'] = 1
            self.neck['poseScore'] = 1
            self.neck['detail'] = 'straight'

        elif 62 <= neckAngle:
            self.neck['poseCode'] = 2
            self.neck['poseScore'] = 2
            self.neck['detail'] = 'forward over 20'

    def addLeg(self):
        self.leg = {
            'poseCode': int,
            'poseScore': int,
            'detail': str,
            'add' : {
                'score' : 0,
                '30_60' : 0,
                'over60' : 0
            }
        }
        rLegAngle = getAngle3P(self.KEY_DICT['r-hip'],self.KEY_DICT['r-knee'],self.KEY_DICT['r-ankle'])
        lLegAngle = getAngle3P(self.KEY_DICT['l-hip'], self.KEY_DICT['l-knee'], self.KEY_DICT['l-ankle'])
        thr = max(getDist2P(self.KEY_DICT['neck-up'],self.KEY_DICT['r-ankle']),getDist2P(self.KEY_DICT['neck-up'],self.KEY_DICT['l-ankle']))*0.1
        if self.maxval[self.class_list.index('r-knee')] >= self.maxval[self.class_list.index('l-knee')]:
            if 30 <= rLegAngle <= 70:
                self.leg['add']['score'] = 1
                self.leg['add']['30_60'] = 1

            elif 70 <= rLegAngle:
                self.leg['add']['score'] = 2
                self.leg['add']['over60'] = 1

        else:
            if 30 <= lLegAngle <= 70:
                self.leg['add']['score'] = 1
                self.leg['add']['30_60'] = 1

            elif 70 <= lLegAngle:
                self.leg['add']['score'] = 2
                self.leg['add']['over60'] = 1

        if self.plugin['support']['sit'] == 1 or self.plugin['support']['chair_n'] == 1 or self.plugin['support']['chair_y'] == 1:
            self.leg['poseCode'] = 0
            self.leg['poseScore'] = 1
            self.leg['detail'] = 'sit'

        elif abs(self.KEY_DICT['r-ankle'][1] - self.KEY_DICT['l-ankle'][1]) > thr:
            self.leg['poseCode'] = 3
            self.leg['poseScore'] = 2
            self.leg['detail'] = 'stand one leg'

        else:
            self.leg['poseCode'] = 2
            self.leg['poseScore'] = 1
            self.leg['detail'] = 'stand two leg'

    def addShoulder(self):
        self.shoulder = {
            'poseCode': int,
            'poseScore': int,
            'detail': str,
            'add' : {
                'score' : 0,
                'twist' : 0,
                'upShoulder' : 0,
                'supportArm' : 0,
            }
        }

        if self.plugin['twist']['elbow'] == 1:
            self.shoulder['add']['score'] += 1
            self.shoulder['add']['twist'] = 1

        if self.plugin['support']['elbow'] == 1:
            self.shoulder['add']['supportArm'] = -1
            self.shoulder['add']['score'] -= 1

        rShoulderAngle = getAngle3P(self.KEY_DICT['r-hip'],self.KEY_DICT['r-shou'],self.KEY_DICT['r-elbow'])
        lShoulderAngle = getAngle3P(self.KEY_DICT['l-hip'], self.KEY_DICT['l-shou'], self.KEY_DICT['l-elbow'])


        '''
        단순 x 값으로만 비교하다 보니 7.볼팅작업에 대해서 음수가 나옴
        '''
        if self.label == 'right':
            if self.KEY_DICT['r-elbow'][0] < self.KEY_DICT['r-shou'][0]:
                rShoulderAngle *= -1

            else:
                pass

            if self.KEY_DICT['l-elbow'][0] < self.KEY_DICT['l-shou'][0]:
                lShoulderAngle *= -1

            else:
                pass

        elif self.label == 'left':
            if self.KEY_DICT['r-elbow'][0] > self.KEY_DICT['r-shou'][0]:
                rShoulderAngle *= -1
            else:
                pass
            if self.KEY_DICT['l-elbow'][0] > self.KEY_DICT['l-shou'][0]:
                lShoulderAngle *= -1
            else:
                pass

        if self.maxval[self.class_list.index('r-elbow')] >= self.maxval[self.class_list.index('l-elbow')]:
            if rShoulderAngle < -20:
                self.shoulder['poseCode'] = 0
                self.shoulder['poseScore'] = 2
                self.shoulder['detail'] = 'back over -20'

            elif -30 <= rShoulderAngle < 30:
                self.shoulder['poseCode'] = 1
                self.shoulder['poseScore'] = 1
                self.shoulder['detail'] = 'straight'

            elif 20 <= rShoulderAngle < 63:
                self.shoulder['poseCode'] = 2
                self.shoulder['poseScore'] = 2
                self.shoulder['detail'] = 'forward between 20 and 45'

            elif 63 <= rShoulderAngle < 110:
                self.shoulder['poseCode'] = 3
                self.shoulder['poseScore'] = 3
                self.shoulder['detail'] = 'forward between 45 and 90'

            elif 110 <= rShoulderAngle:
                self.shoulder['poseCode'] = 4
                self.shoulder['poseScore'] = 4
                self.shoulder['detail'] = 'forward over 90'

        else:
            if lShoulderAngle < -20:
                self.shoulder['poseCode'] = 0
                self.shoulder['poseScore'] = 2
                self.shoulder['detail'] = 'back over -20'

            elif -30 <= lShoulderAngle < 30:
                self.shoulder['poseCode'] = 1
                self.shoulder['poseScore'] = 1
                self.shoulder['detail'] = 'straight'

            elif 30 <= lShoulderAngle < 63:
                self.shoulder['poseCode'] = 2
                self.shoulder['poseScore'] = 2
                self.shoulder['detail'] = 'forward between 20 and 45'

            elif 63 <= lShoulderAngle < 110:
                self.shoulder['poseCode'] = 3
                self.shoulder['poseScore'] = 3
                self.shoulder['detail'] = 'forward between 45 and 90'

            elif 110 <= lShoulderAngle:
                self.shoulder['poseCode'] = 4
                self.shoulder['poseScore'] = 4
                self.shoulder['detail'] = 'forward over 90'

    def addElbow(self):
        self.elbow = {
            'poseCode' : int,
            'poseScore' : int,
            'detail' : str,
        }
        rElbowAngle = 180 - getAngle3P(self.KEY_DICT['r-shou'], self.KEY_DICT['r-elbow'], self.KEY_DICT['r-wrist'])
        lElbowAngle = 180 - getAngle3P(self.KEY_DICT['l-shou'], self.KEY_DICT['l-elbow'], self.KEY_DICT['l-wrist'])


        if self.maxval[self.class_list.index('r-shou')] >= self.maxval[self.class_list.index('l-shou')]:
            if 0 <= rElbowAngle < 50:
                self.elbow['poseCode'] = 0
                self.elbow['poseScore'] = 2
                self.elbow['detail'] = 'forward between 0 and 60'

            elif 50 <= rElbowAngle < 100:
                self.elbow['poseCode'] = 1
                self.elbow['poseScore'] = 1
                self.elbow['detail'] = 'forward between 60 and 100'

            elif 100 <= rElbowAngle:
                self.elbow['poseCode'] = 2
                self.elbow['poseScore'] = 2
                self.elbow['detail'] = 'forward over 100'

        else:
            if 0 <= lElbowAngle < 50:
                self.elbow['poseCode'] = 0
                self.elbow['poseScore'] = 2
                self.elbow['detail'] = 'forward between 0 and 60'

            elif 50 <= lElbowAngle < 100:
                self.elbow['poseCode'] = 1
                self.elbow['poseScore'] = 1
                self.elbow['detail'] = 'forward between 60 and 100'

            elif 100 <= lElbowAngle:
                self.elbow['poseCode'] = 2
                self.elbow['poseScore'] = 2
                self.elbow['detail'] = 'forward over 100'

    def addWrist(self):
        self.wrist = {
            'poseCode' : int,
            'poseScore' : int,
            'detail' : str,
            'add' : {
                'score' : 0,
                'twist' : 0,
            }
        }
        if self.plugin['twist']['wrist'] == 1:
            self.wrist['add']['score'] += 1
            self.wrist['add']['twist'] = 1

        rWristAngle = 180 - getAngle3P(self.KEY_DICT['r-elbow'], self.KEY_DICT['r-wrist'], self.KEY_DICT['r-hand'])
        lWristAngle = 180 - getAngle3P(self.KEY_DICT['l-elbow'], self.KEY_DICT['l-wrist'], self.KEY_DICT['l-hand'])

        if self.KEY_DICT['r-wrist'][1] > self.KEY_DICT['r-hand'][1]:
            rWristAngle *= -1
        if self.KEY_DICT['l-wrist'][1] > self.KEY_DICT['l-hand'][1]:
            lWristAngle *= -1

        if self.maxval[self.class_list.index('r-wrist')] >= self.maxval[self.class_list.index('l-wrist')]:
            if 30 <= rWristAngle:
                self.wrist['poseCode'] = 0
                self.wrist['poseScore'] = 2
                self.wrist['detail'] = 'forward over 15'

            elif -30 <= rWristAngle < 30:
                self.wrist['poseCode'] = 1
                self.wrist['poseScore'] = 1
                self.wrist['detail'] = 'straight'

            elif rWristAngle < -30:
                self.wrist['poseCode'] = 2
                self.wrist['poseScore'] = 2
                self.wrist['detail'] = 'back over -15'


        else:
            if 30 <= lWristAngle:
                self.wrist['poseCode'] = 0
                self.wrist['poseScore'] = 2
                self.wrist['detail'] = 'forward over 15'

            elif -30 <= lWristAngle < 30:
                self.wrist['poseCode'] = 1
                self.wrist['poseScore'] = 1
                self.wrist['detail'] = 'straight'

            elif lWristAngle < -30:
                self.wrist['poseCode'] = 2
                self.wrist['poseScore'] = 2
                self.wrist['detail'] = 'back over -15'

    def getDetail(self):
        totalDetail = {
            'group A' : self.gA,
            'group B' : self.gB,
            'score C' : self.scoreC,
            'totalScore' : self.scoreTotal
        }
        return totalDetail

class RULA:
    def __init__(self,keypoints,label=None,**kwargs):
        self.class_list = ["head", "neck-up", "neck-down", "spine-1",
                           "spine-2", "r-shou", "l-shou",
                           "r-elbow", "l-elbow", "r-wrist", "l-wrist",
                           "r-hand", "l-hand", "r-hip", "l-hip",
                           "r-knee", "l-knee", "r-ankle", "l-ankle"]
        self.label = label
        self.keypoints = keypoints
        self.KEY_DICT = {k: v for k, v in zip(self.class_list, keypoints)}

        self.maxval = kwargs['maxval'] if 'maxval' in kwargs.keys() else None
        self.plugin = kwargs['plugin'] if 'plugin' in kwargs.keys() else None
        self.img = kwargs['img'] if 'img' in kwargs.keys() else None

        self.update()

    def update(self):
        self.addBack()
        self.addNeck()
        self.addLeg()
        self.addElbow()
        self.addWrist()
        self.addShoulder()
        self.addWristTwist()
        self.calScore()

    def calScore(self):
        sA = \
            [
                [
                    [
                        [1, 2],
                        [2, 2],
                        [2, 3],
                        [3, 3]
                    ],
                    [
                        [2, 2],
                        [2, 2],
                        [3, 3],
                        [3, 3]
                    ],
                    [
                        [2, 3],
                        [3, 3],
                        [3, 3],
                        [4, 4]
                    ]
                ],
                [
                    [
                        [2, 3],
                        [3, 3],
                        [3, 4],
                        [4, 4]
                    ],
                    [
                        [3, 3],
                        [3, 3],
                        [3, 4],
                        [4, 4]
                    ],
                    [
                        [3, 4],
                        [4, 4],
                        [4, 4],
                        [5, 5]
                    ]
                ],
                [
                    [
                        [3, 3],
                        [4, 4],
                        [4, 4],
                        [5, 5]
                    ],
                    [
                        [3, 4],
                        [4, 4],
                        [4, 4],
                        [5, 5]
                    ],
                    [
                        [4, 4],
                        [4, 4],
                        [4, 5],
                        [5, 5]
                    ]
                ],
                [
                    [
                        [4, 4],
                        [4, 4],
                        [4, 5],
                        [5, 5]
                    ],
                    [
                        [4, 4],
                        [4, 4],
                        [4, 5],
                        [5, 5]
                    ],
                    [
                        [4, 4],
                        [4, 5],
                        [5, 5],
                        [6, 6]
                    ]
                ],
                [
                    [
                        [5, 5],
                        [5, 5],
                        [5, 6],
                        [6, 7]
                    ],
                    [
                        [5, 6],
                        [6, 6],
                        [6, 7],
                        [7, 7]
                    ],
                    [
                        [6, 6],
                        [6, 7],
                        [7, 7],
                        [7, 8]
                    ]
                ],
                [
                    [
                        [7, 7],
                        [7, 7],
                        [7, 8],
                        [8, 9]
                    ],
                    [
                        [8, 8],
                        [8, 8],
                        [7, 9],
                        [9, 9]
                    ],
                    [
                        [9, 9],
                        [9, 9],
                        [9, 9],
                        [9, 9]
                    ]
                ]
            ]

        sB = \
            [
                [
                    [1, 3],
                    [2, 3],
                    [3, 4],
                    [5, 5],
                    [6, 6],
                    [7, 7]
                ],
                [
                    [2, 3],
                    [2, 3],
                    [4, 5],
                    [5, 5],
                    [6, 7],
                    [7, 7]
                ],
                [
                    [3, 3],
                    [3, 4],
                    [4, 5],
                    [5, 6],
                    [6, 7],
                    [7, 7]
                ],
                [
                    [5, 5],
                    [5, 6],
                    [6, 7],
                    [7, 7],
                    [7, 7],
                    [8, 8]
                ],
                [
                    [7, 7],
                    [7, 7],
                    [7, 8],
                    [8, 8],
                    [8, 8],
                    [8, 8]
                ],
                [
                    [8, 8],
                    [8, 8],
                    [8, 8],
                    [8, 9],
                    [9, 9],
                    [9, 9]
                ]
            ]

        gS = \
            [
                [1, 2, 3, 3, 4, 5, 5, 5, 5, 5, 5, 5, 5],
                [2, 2, 3, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5],
                [3, 3, 3, 4, 4, 4, 6, 6, 6, 6, 6, 6, 6],
                [3, 3, 3, 4, 5, 6, 6, 6, 6, 6, 6, 6, 6],
                [4, 4, 4, 5, 6, 7, 7, 7, 7, 7, 7, 7, 7],
                [4, 4, 5, 5, 6, 6, 7, 7, 7, 7, 7, 7, 7],
                [5, 5, 6, 6, 7, 7, 7, 7, 7, 7, 7, 7, 7],
                [5, 5, 6, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
                [5, 5, 6, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
                [5, 5, 6, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
                [5, 5, 6, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
                [5, 5, 6, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
                [5, 5, 6, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7],
            ]
        # sA[상완][전완][손목][비틀림]
        # sB[목][상체][다리]
        # gS[scoreC][scoreD]

        mus = 0
        if 'action' in self.plugin.keys():
            if int(self.plugin['action']['4up']) == 1:
                mus += 1

        fs = 0
        w_int = int(self.plugin['weight']['weight'])
        if w_int < 2:
            fs = 0
        elif w_int < 10:
            fs = 1
        else:
            fs = 2

        if w_int > 2 and int(self.plugin['weight']['4up']) == 1:
            fs += 1

        if int(self.plugin['weight']['sud']) == 1:
            fs = 3

        # if 'weight' in self.plugin.keys():
        #     ws = [k for k,v in self.plugin['weight'].items() if v == 1]
        #     for w in ws:
        #         if w == '5':
        #             fs += 1
        #         elif w == '10' or w == '20':
        #             fs += 3

        shoulderScore = self.shoulder['poseScore'] + self.shoulder['add']['score'] -1
        elbowScore = self.elbow['poseScore'] + self.elbow['add']['score'] - 1
        wristScore = self.wrist['poseScore'] + self.wrist['add']['score'] - 1

        neckScore = self.neck['poseScore'] + self.neck['add']['score'] - 1
        backScore = self.back['poseScore'] + self.back['add']['score'] - 1

        scoreA = sA[shoulderScore][wristScore][elbowScore][self.wristTwist['poseScore']-1]
        scoreB = sB[neckScore][backScore][self.leg['poseScore']-1]

        # print(f'scoreA \n shoulder : {shoulderScore} \n wristScore : {wristScore} \n elbowScore : {elbowScore} \n wristTwist : {self.wristTwist["poseScore"]-1}')
        #
        # print(f'\nscoreB \n neckScore : {neckScore} \n backSCore : {backScore} \n leg : {self.leg["poseScore"]-1}\n')
        # print(f'mus : {mus}, fs : {fs}')
        sC = scoreA + mus + fs - 1
        sD = scoreB + mus + fs - 1
        if sC >= 13:
            sC = 12
        if sD >= 13:
            sD = 12
        grandScore = gS[sC][sD]

        if 1 <= grandScore <= 2:
            self.scoreTotal = {
                'step': 1,
                'score': grandScore,
                'danger': '양호',
                'action': '작업이 오랫동안 지속적으로 그리고, 반복적으로만 행해지지 않는다면 작업 자세가 별 문제가 없음을 나타낸다.'
            }
        elif 3 <= grandScore <= 4:
            self.scoreTotal = {
                'step': 2,
                'score': grandScore,
                'danger': '관찰',
                'action': '작업 자세에 대한 추가적인 연구가 필요하고 작업 자세를 바꾸는 게 낫다는 것을 나타낸다.'
            }
        elif 5 <= grandScore <= 6:
            self.scoreTotal = {
                'step': 3,
                'score': grandScore,
                'danger': '개선',
                'action': '작업자세를 되도록 빨리 바꾸는 게 낫다는 것을 나타낸다. '
            }
        elif 7 <= grandScore:
            self.scoreTotal = {
                'step': 4,
                'score': grandScore,
                'danger': '즉시 개선',
                'action': '작업자세를 즉각 바꾸어야 한다는 것을 나타낸다.'
            }

        return grandScore, self.scoreTotal

    def getDetail(self):
        detail = {
            'totalScore' : self.scoreTotal,
            'back' : self.back,
            'neck' : self.neck,
            'leg' : self.leg,
            'shoulder' : self.shoulder,
            'elbow' : self.elbow,
            'wristTwist' : self.wristTwist,
            'wrist' : self.wrist
        }

        return detail

    def addBack(self):
        self.back = {
            'poseCode' : int,
            'poseScore' : int,
            'detail' : str,
            'add' : {
                'score' : 0,
                'twist' : 0,
                'curved' : 0,
            }
        }

        if self.plugin['twist']['back'] == 1:
            self.back['add']['score'] += 1
            self.back['add']['twist'] = 1

        backAngle = getAngle3P(self.KEY_DICT['neck-down'], self.KEY_DICT['spine-2'],
                               [self.KEY_DICT['spine-2'][0], self.KEY_DICT['spine-2'][1] - 20])
        if self.label == 'right':
            if self.KEY_DICT['neck-down'][0] < self.KEY_DICT['spine-2'][0]:
                backAngle *= -1
            else:
                pass

        elif self.label == 'left':
            if self.KEY_DICT['neck-down'][0] > self.KEY_DICT['spine-2'][0]:
                backAngle *= -1
            else:
                pass

        if self.plugin['support']['chair_n'] == 1:
            self.back['poseCode'] = 1
            self.back['poseScore'] = 2
            self.back['detail'] = 'sit without back support'

        elif self.plugin['support']['chair_y'] == 1:
            self.back['poseCode'] = 0
            self.back['poseScore'] = 1
            self.back['detail'] = 'sit with back support'

        elif backAngle < -5:
            self.back['poseCode'] = 2
            self.back['poseScore'] = 1
            self.back['detail'] = 'back over 0'

        elif -5 <= backAngle < 10:
            self.back['poseCode'] = 3
            self.back['poseScore'] = 1
            self.back['detail'] = 'straight'

        elif 10 <= backAngle < 30:
            self.back['poseCode'] = 4
            self.back['poseScore'] = 2
            self.back['detail'] = 'forward between 0 and 20'

        elif 30 <= backAngle < 70:
            self.back['poseCode'] = 5
            self.back['poseScore'] = 3
            self.back['detail'] = 'forward between 20 and 60'

        elif 70 <= backAngle:
            self.back['poseCode'] = 6
            self.back['poseScore'] = 4
            self.back['detail'] = 'forward over 60'

    def addNeck(self):
        self.neck = {
            'poseCode': int,
            'poseScore': int,
            'detail': str,
            'angle' : int,
            'add' : {
                'score' : 0,
                'twist' : 0,
                'curved' : 0
            }
        }

        if self.plugin['twist']['neck'] == 1:
            self.neck['add']['score'] += 1
            self.neck['add']['twist'] = 1


        neckAngle = 180 - getAngle3P(self.KEY_DICT['neck-up'], self.KEY_DICT['neck-down'],
                               self.KEY_DICT['spine-2'])

        if self.label == 'right':
            if self.KEY_DICT['neck-down'][0] < self.KEY_DICT['spine-1'][0]:
                neckAngle *= -1
            else:
                pass

        elif self.label == 'left':
            if self.KEY_DICT['neck-down'][0] > self.KEY_DICT['spine-1'][0]:
                neckAngle *= -1
            else:
                pass

        self.neck['angle'] = neckAngle

        if neckAngle < -50:
            self.neck['poseCode'] = 0
            self.neck['poseScore'] = 4
            self.neck['detail'] = 'back'

        elif -50 <= neckAngle < 40:
            self.neck['poseCode'] = 1
            self.neck['poseScore'] = 1
            self.neck['detail'] = 'straight'

        elif 40 <= neckAngle < 60:
            self.neck['poseCode'] = 2
            self.neck['poseScore'] = 2
            self.neck['detail'] = 'forward between 10 and 20'

        elif 60 <= neckAngle:
            self.neck['poseCode'] = 3
            self.neck['poseScore'] = 3
            self.neck['detail'] = 'forward over 20'

    def addLeg(self):
        self.leg = {
            'poseCode': int,
            'poseScore': int,
            'detail': str
        }
        rLegAngle = getAngle3P(self.KEY_DICT['r-hip'],self.KEY_DICT['r-knee'],self.KEY_DICT['r-ankle'])
        lLegAngle = getAngle3P(self.KEY_DICT['l-hip'], self.KEY_DICT['l-knee'], self.KEY_DICT['l-ankle'])
        thr = max(getDist2P(self.KEY_DICT['neck-up'],self.KEY_DICT['r-ankle']),getDist2P(self.KEY_DICT['neck-up'],self.KEY_DICT['l-ankle']))*0.1

        if int(self.plugin['action']['bad']) == 1:
            self.leg['poseCode'] = 1
            self.leg['poseScore'] = 2
            self.leg['detail'] = 'unbalancee leg'
        else:
            self.leg['poseCode'] = 0
            self.leg['poseScore'] = 1
            self.leg['detail'] = 'balanced leg'

        # if abs(self.KEY_DICT['r-ankle'][1] - self.KEY_DICT['l-ankle'][1]) > thr:
        #     self.leg['poseCode'] = 1
        #     self.leg['poseScore'] = 2
        #     self.leg['detail'] = 'stand one leg'
        #
        # else:
        #     self.leg['poseCode'] = 0
        #     self.leg['poseScore'] = 1
        #     self.leg['detail'] = 'stand two leg'

        # if abs(rLegAngle-lLegAngle) < 30:
        #     self.leg['poseCode'] = 0
        #     self.leg['poseScore'] = 1
        #     self.leg['detail'] = 'stand two leg'
        #
        # else:
        #     self.leg['poseCode'] = 1
        #     self.leg['poseScore'] = 2
        #     self.leg['detail'] = 'stand one leg'

    def addShoulder(self):
        self.shoulder = {
            'poseCode': int,
            'poseScore': int,
            'detail': str,
            'add' : {
                'score' : 0,
                'twist' : 0,
                'upShoulder' : 0,
                'supportArm' : 0,
            }
        }

        if self.plugin['twist']['elbow'] == 1:
            self.shoulder['add']['score'] += 1
            self.shoulder['add']['twist'] = 1

        if self.plugin['support']['elbow'] == 1:
            self.shoulder['add']['score'] -= 1
            self.shoulder['add']['supportArm'] = -1

        rShoulderAngle = getAngle3P(self.KEY_DICT['r-hip'],self.KEY_DICT['r-shou'],self.KEY_DICT['r-elbow'])
        lShoulderAngle = getAngle3P(self.KEY_DICT['l-hip'], self.KEY_DICT['l-shou'], self.KEY_DICT['l-elbow'])

        if self.label == 'right':
            if self.KEY_DICT['r-elbow'][0] < self.KEY_DICT['r-shou'][0]:
                rShoulderAngle *= -1

            else:
                pass

            if self.KEY_DICT['l-elbow'][0] < self.KEY_DICT['l-shou'][0]:
                lShoulderAngle *= -1

            else:
                pass

        elif self.label == 'left':
            if self.KEY_DICT['r-elbow'][0] > self.KEY_DICT['r-shou'][0]:
                rShoulderAngle *= -1
            else:
                pass
            if self.KEY_DICT['l-elbow'][0] > self.KEY_DICT['l-shou'][0]:
                lShoulderAngle *= -1
            else:
                pass

        if self.maxval[self.class_list.index('r-shou')] >= self.maxval[self.class_list.index('l-shou')]:
            if rShoulderAngle < -20:
                self.shoulder['poseCode'] = 0
                self.shoulder['poseScore'] = 2
                self.shoulder['detail'] = 'back over -20'

            elif -20 <= rShoulderAngle < 30:
                self.shoulder['poseCode'] = 1
                self.shoulder['poseScore'] = 1
                self.shoulder['detail'] = 'straight'

            elif 30 <= rShoulderAngle < 60:
                self.shoulder['poseCode'] = 2
                self.shoulder['poseScore'] = 2
                self.shoulder['detail'] = 'forward between 20 and 45'

            elif 60 <= rShoulderAngle < 110:
                self.shoulder['poseCode'] = 3
                self.shoulder['poseScore'] = 3
                self.shoulder['detail'] = 'forward between 45 and 90'

            elif 110 <= rShoulderAngle:
                self.shoulder['poseCode'] = 4
                self.shoulder['poseScore'] = 4
                self.shoulder['detail'] = 'forward over 90'

        else:
            if lShoulderAngle < -20:
                self.shoulder['poseCode'] = 0
                self.shoulder['poseScore'] = 2
                self.shoulder['detail'] = 'back over -20'

            elif -20 <= lShoulderAngle < 30:
                self.shoulder['poseCode'] = 1
                self.shoulder['poseScore'] = 1
                self.shoulder['detail'] = 'straight'

            elif 30 <= lShoulderAngle < 60:
                self.shoulder['poseCode'] = 2
                self.shoulder['poseScore'] = 2
                self.shoulder['detail'] = 'forward between 20 and 45'

            elif 60 <= lShoulderAngle < 110:
                self.shoulder['poseCode'] = 3
                self.shoulder['poseScore'] = 3
                self.shoulder['detail'] = 'forward between 45 and 90'

            elif 110 <= lShoulderAngle:
                self.shoulder['poseCode'] = 4
                self.shoulder['poseScore'] = 4
                self.shoulder['detail'] = 'forward over 90'

    def addElbow(self):
        self.elbow = {
            'poseCode' : int,
            'poseScore' : int,
            'detail' : str,
            'add' : {
                'score' : 0,
                'crossArm' : 0,
                'outArm' : 0
            }
        }
        rElbowAngle = 180 - getAngle3P(self.KEY_DICT['r-shou'], self.KEY_DICT['r-elbow'], self.KEY_DICT['r-wrist'])
        lElbowAngle = 180 - getAngle3P(self.KEY_DICT['l-shou'], self.KEY_DICT['l-elbow'], self.KEY_DICT['l-wrist'])


        if self.maxval[self.class_list.index('r-shou')] >= self.maxval[self.class_list.index('l-shou')]:
            if 0 <= rElbowAngle < 60:
                self.elbow['poseCode'] = 0
                self.elbow['poseScore'] = 2
                self.elbow['detail'] = 'forward between 0 and 60'

            elif 60 <= rElbowAngle < 100:
                self.elbow['poseCode'] = 1
                self.elbow['poseScore'] = 1
                self.elbow['detail'] = 'forward between 60 and 100'

            elif 100 <= rElbowAngle:
                self.elbow['poseCode'] = 2
                self.elbow['poseScore'] = 2
                self.elbow['detail'] = 'forward over 100'

        else:
            if 0 <= lElbowAngle < 60:
                self.elbow['poseCode'] = 0
                self.elbow['poseScore'] = 2
                self.elbow['detail'] = 'forward between 0 and 60'

            elif 60 <= lElbowAngle < 100:
                self.elbow['poseCode'] = 1
                self.elbow['poseScore'] = 1
                self.elbow['detail'] = 'forward between 60 and 100'

            elif 100 <= lElbowAngle:
                self.elbow['poseCode'] = 2
                self.elbow['poseScore'] = 2
                self.elbow['detail'] = 'forward over 100'

    def addWrist(self):
        self.wrist = {
            'poseCode' : int,
            'poseScore' : int,
            'detail' : str,
            'add' : {
                'score' : 0,
                'deviation' : 0
            }
        }
        rWristAngle = 180 - getAngle3P(self.KEY_DICT['r-elbow'], self.KEY_DICT['r-wrist'], self.KEY_DICT['r-hand'])
        lWristAngle = 180 - getAngle3P(self.KEY_DICT['l-elbow'], self.KEY_DICT['l-wrist'], self.KEY_DICT['l-hand'])

        if self.KEY_DICT['r-wrist'][1] > self.KEY_DICT['r-hand'][1]:
            rWristAngle *= -1
        if self.KEY_DICT['l-wrist'][1] > self.KEY_DICT['l-hand'][1]:
            lWristAngle *= -1

        if self.maxval[self.class_list.index('r-wrist')] >= self.maxval[self.class_list.index('l-wrist')]:
            if 50 <= rWristAngle:
                self.wrist['poseCode'] = 0
                self.wrist['poseScore'] = 3
                self.wrist['detail'] = 'forward over 15'

            elif -40 <= rWristAngle < 40:
                self.wrist['poseCode'] = 1
                self.wrist['poseScore'] = 1
                self.wrist['detail'] = 'straight'

            elif -50 <= rWristAngle < -40:
                self.wrist['poseCode'] = 2
                self.wrist['poseScore'] = 2
                self.wrist['detail'] = 'between -15 and 15'

            elif 40 <= rWristAngle < 50:
                self.wrist['poseCode'] = 2
                self.wrist['poseScore'] = 2
                self.wrist['detail'] = 'between -15 and 15'

            elif rWristAngle < -50:
                self.wrist['poseCode'] = 3
                self.wrist['poseScore'] = 3
                self.wrist['detail'] = 'back over -15'

        else:
            if 50 <= lWristAngle:
                self.wrist['poseCode'] = 0
                self.wrist['poseScore'] = 2
                self.wrist['detail'] = 'forward over 15'

            elif -40 <= lWristAngle < 40:
                self.wrist['poseCode'] = 1
                self.wrist['poseScore'] = 1
                self.wrist['detail'] = 'straight'

            elif -50 <= lWristAngle < -40:
                self.wrist['poseCode'] = 2
                self.wrist['poseScore'] = 2
                self.wrist['detail'] = 'between -15 and 15'

            elif 40 <= lWristAngle < 50:
                self.wrist['poseCode'] = 2
                self.wrist['poseScore'] = 2
                self.wrist['detail'] = 'between -15 and 15'

            elif lWristAngle < -50:
                self.wrist['poseCode'] = 3
                self.wrist['poseScore'] = 3
                self.wrist['detail'] = 'back over -15'

    def addWristTwist(self):
        self.wristTwist = {
            'poseCode' : int,
            'poseScore' : int,
            'detail' : str
        }
        """
        pred -> 키포인트 (1,19)
        maxval -> 정확도 (19)
        img -> 원본이미지
        state -> 정면 측면 후면 상태 ex front, left ....
        """
        if self.plugin['twist']['wrist'] == 1:
            self.wristTwist['poseCode'] = 1
            self.wristTwist['poseScore'] = 2
            self.wristTwist['detail'] = 'twist wrist'

        else:
            self.wristTwist['poseCode'] = 0
            self.wristTwist['poseScore'] = 1
            self.wristTwist['detail'] = 'normal wrist'
        # maxvals = self.maxval
        # preds = self.keypoints
        # img = self.img
        # state = self.label
        #
        # final_score = 1
        # r_hand = []
        # l_hand = []
        # input_p = img
        #
        # mpHands = mp.solutions.hands
        # hands = mpHands.Hands()
        #
        # for i, (pred, maxval) in enumerate(zip(preds, maxvals)):
        #     if i == 0:
        #         img = cv2.putText(img, f"{i}", (int(pred[0]), int(pred[1])), 1, 1, (0, 0, 255), 2)
        #     if i == 9 or i == 11:
        #         if maxval > 0.85:
        #             r_hand.append([int(pred[0]), int(pred[1])])
        #     if i == 10 or i == 12:
        #         if maxval > 0.85:
        #             l_hand.append([int(pred[0]), int(pred[1])])
        #
        # if state == "right":
        #     if len(r_hand) == 2:
        #         p3 = [int(preds[7][0]), int(preds[7][1])]
        #         p1 = [int(preds[9][0]), int(preds[9][1])]
        #         p2 = [int(preds[7][0]) - 1, int(preds[7][1])]
        #         if p1[1] >= p3[1]:
        #             pos_a = int(getAngle3P(p1, p2, p3))
        #         else:
        #             pos_a = -(int(getAngle3P(p1, p2, p3)))
        #
        #         r_x_d = abs(r_hand[0][0] - r_hand[1][0]) * 3
        #         if r_x_d > 15:
        #             c_x, c_y = int((r_hand[1][0] + r_hand[0][0]) / 2), int((r_hand[1][1] + r_hand[0][1]) / 2)
        #             r_crop_hand = input_p[c_y - r_x_d:c_y + r_x_d, c_x - r_x_d:c_x + r_x_d]
        #             r_crop_hand = cv2.resize(r_crop_hand, (200, 200))
        #             M = cv2.getRotationMatrix2D((200 / 2, 200 / 2), pos_a, 1)
        #             r_crop_hand = cv2.warpAffine(r_crop_hand, M, (250, 250))
        #             r_results = hands.process(r_crop_hand)
        #             r_crop_hand = cv2.cvtColor(r_crop_hand, cv2.COLOR_BGR2RGB)
        #             thumb = 0
        #             wrist = 0
        #             if r_results.multi_hand_landmarks:
        #                 for r in r_results.multi_hand_landmarks:
        #                     for r_id, r_lm in enumerate(r.landmark):
        #                         r_crop_hand = cv2.circle(r_crop_hand, (int(r_lm.x * 250), int(r_lm.y * 250)), 1,
        #                                                  (0, 0, 255), -1)
        #                         if r_id == 0:
        #                             wrist = r_lm.y
        #                         if r_id == 2:
        #                             thumb = r_lm.y
        #
        #             if thumb <= wrist:
        #                 final_score = 1
        #             else:
        #                 final_score = 2
        #     else:
        #         pass
        #
        # if state == "left":
        #     if len(l_hand) == 2:
        #         p3 = [int(preds[8][0]), int(preds[8][1])]
        #         p1 = [int(preds[10][0]), int(preds[10][1])]
        #         p2 = [int(preds[8][0]) + 1, int(preds[8][1])]
        #         if p1[1] >= p3[1]:
        #             pos_a = -int(getAngle3P(p1, p2, p3))
        #         else:
        #             pos_a = (int(getAngle3P(p1, p2, p3)))
        #
        #         l_x_d = abs(l_hand[0][0] - l_hand[1][0]) * 3
        #         if l_x_d > 15:
        #             c_x, c_y = int((l_hand[1][0] + l_hand[0][0]) / 2), int((l_hand[1][1] + l_hand[0][1]) / 2)
        #             l_crop_hand = input_p[c_y - l_x_d:c_y + l_x_d, c_x - l_x_d:c_x + l_x_d]
        #             l_crop_hand = cv2.resize(l_crop_hand, (200, 200))
        #             M = cv2.getRotationMatrix2D((200 / 2, 200 / 2), pos_a, 1)
        #             l_crop_hand = cv2.warpAffine(l_crop_hand, M, (250, 250))
        #             l_results = hands.process(l_crop_hand)
        #             thumb = 0
        #             wrist = 0
        #             if l_results.multi_hand_landmarks:
        #                 for l in l_results.multi_hand_landmarks:
        #                     for l_id, l_lm in enumerate(l.landmark):
        #                         if l_id == 0:
        #                             wrist = l_lm.y
        #                         if l_id == 2:
        #                             thumb = l_lm.y
        #             if thumb >= wrist:
        #                 final_score = 1
        #             else:
        #                 final_score = 2
        #     else:
        #         pass
        #
        # self.wristTwist = {
        #     'poseCode': 1 if final_score == 1 else 2,
        #     'poseScore': 1 if final_score == 1 else 2,
        #     'detail': 'Normal' if final_score == 1 else 'Twist'
        # }

def box_to_center_scale(box, model_image_width, model_image_height):

    center = np.zeros((2), dtype=np.float32)

    bottom_left_corner = box[0]
    top_right_corner = box[1]
    box_width = top_right_corner[0]-bottom_left_corner[0]
    box_height = top_right_corner[1]-bottom_left_corner[1]
    bottom_left_x = bottom_left_corner[0]
    bottom_left_y = bottom_left_corner[1]
    center[0] = bottom_left_x + box_width * 0.5
    center[1] = bottom_left_y + box_height * 0.5

    aspect_ratio = model_image_width * 1.0 / model_image_height
    pixel_std = 200

    if box_width > aspect_ratio * box_height:
        box_height = box_width * 1.0 / aspect_ratio
    elif box_width < aspect_ratio * box_height:
        box_width = box_height * aspect_ratio
    scale = np.array(
        [box_width * 1.0 / pixel_std, box_height * 1.0 / pixel_std],
        dtype=np.float32)
    if center[0] != -1:
        scale = scale * 1.25

    return center, scale

# for i in range(0,30):
#     with open(f'test_dir/test_result{i}.txt','r') as f:
#         a = f.read()
#
#     with open(f'test_dir/maxval{i}.txt','r') as f:
#         maxval = f.read()
#
#     from pprint import pprint
#     maxval = eval(maxval.replace('array','').replace(', dtype=float32)','').replace('(','').replace("'",''))
#     keypoints = eval(a.replace('array','').replace(', dtype=float32)','').replace('(','').replace("'",''))
#     class_list = ["head", "neck-up", "neck-down", "spine-1",
#                           "spine-2", "r-shou", "l-shou",
#                           "r-elbow", "l-elbow", "r-wrist", "l-wrist",
#                           "r-hand", "l-hand", "r-hip", "l-hip",
#                           "r-knee", "l-knee", "r-ankle", "l-ankle"]
#     KEY_DICT = {k: v for k, v in zip(class_list, keypoints)}
#     print(i)
#     label = None
#     # owas = OWAS(keypoints,label,maxval=maxval)
#     # print(owas.getDetail())
#     # print(owas.calScore())
#     reba = REBA(keypoints,maxval=maxval)
#     rula = RULA(keypoints,maxval=maxval)
#     # gA, gB,scoreC, scoreTotal = reba.calScore()
#     # print(gA)
#     # print(gB)
#     # print(scoreC)
#     # print(scoreTotal)
#
#     # print(f'file name is : {i}')
#     # print(getAngle3P(KEY_DICT['spine-2'],KEY_DICT['spine-1'],KEY_DICT['neck-up']))
#     # print(getDist2P(KEY_DICT['r-shou'],KEY_DICT['l-shou']) / getDist2P(KEY_DICT['r-hip'],KEY_DICT['l-hip']))
#     # print(getDist2P(KEY_DICT['r-shou'], KEY_DICT['l-shou']) / getDist2P(KEY_DICT['r-hip'], KEY_DICT['l-hip']))
#     # print()
#     # print()