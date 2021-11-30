import numpy as np
import cv2

class_list = ["head", "neck-up", "neck-down", "spine-1",
              "spine-2", "r-shou", "l-shou",
              "r-elbow", "l-elbow", "r-wrist", "l-wrist",
              "r-hand", "l-hand", "r-hip", "l-hip",
              "r-knee", "l-knee", "r-ankle", "l-ankle"]



def angle_between(p1, p2):
    ang1 = np.arctan2(*p1[::-1])
    ang2 = np.arctan2(*p2[::-1])
    res = np.rad2deg((ang1 - ang2) % (2 * np.pi))
    return res

def getAngle3P(p1, p2, p3):
    pt1 = (p1[0] - p2[0], p1[1] - p2[1])
    pt2 = (p3[0] - p2[0], p3[1] - p2[1])
    res = angle_between(pt1, pt2)
    res = (res + 360) % 360
    if res > 180:
        res = 360 - res
    return res


def box_to_center_scale(box, model_image_width, model_image_height):

    pixel_std = 200
    aspect_ratio = model_image_width / model_image_height
    center = np.zeros((2), dtype=np.float32)


    x = box[0][0]
    y = box[0][1]
    w = box[1][0] - box[0][0]
    h = box[1][1] - box[0][1]


    center[0] = x + w * 0.5
    center[1] = y + h * 0.5

    if w > aspect_ratio * h:
        h = w * 1.0 / aspect_ratio
    elif w < aspect_ratio * h:
        w = h * aspect_ratio

    scale = np.array(
        [w * 1.0 / pixel_std, h * 1.0 / pixel_std],
        dtype=np.float32)
    if center[0] != -1:
        scale = scale * 1.25

    return center, scale

######여기서 키는
# key = [[x,y], [x,y], ......] 형식으로 사용하면됩니다
# ex
# reba_r = REBA(key)
# hand_state, hand_angle = reba_r.reba_hand()
############################

def twist_hand(preds, maxvals, img, state):
    """
    pred -> 키포인트 (1,19)
    maxval -> 정확도 (19)
    img -> 원본이미지에서 cv2.COLOR_BGR2RGB
    state -> 정면 측면 후면 상태 ex front, left ....
    """

    final_score = 1
    r_hand = []
    l_hand = []
    input_p = img

    for i, (pred, maxval) in enumerate(zip(preds, maxvals)):
        if i == 0:
            img = cv2.putText(img, f"{i}", (int(pred[0]), int(pred[1])), 1, 1, (0, 0, 255), 2)
        if i == 9 or i == 11:
            if maxval > 0.85:
                r_hand.append([int(pred[0]), int(pred[1])])
        if i == 10 or i == 12:
            if maxval > 0.85:
                l_hand.append([int(pred[0]), int(pred[1])])

    if state == "right":
        if len(r_hand) == 2:
            p3 = [int(preds[7][0]), int(preds[7][1])]
            p1 = [int(preds[9][0]), int(preds[9][1])]
            p2 = [int(preds[7][0]) - 1, int(preds[7][1])]
            if p1[1] >= p3[1]:
                pos_a = int(getAngle3P(p1, p2, p3))
            else:
                pos_a = -(int(getAngle3P(p1, p2, p3)))

            r_x_d = abs(r_hand[0][0] - r_hand[1][0]) * 3
            if r_x_d > 15:
                c_x, c_y = int((r_hand[1][0] + r_hand[0][0]) / 2), int((r_hand[1][1] + r_hand[0][1]) / 2)
                r_crop_hand = input_p[c_y - r_x_d:c_y + r_x_d, c_x - r_x_d:c_x + r_x_d]
                r_crop_hand = cv2.resize(r_crop_hand, (200, 200))
                M = cv2.getRotationMatrix2D((200 / 2, 200 / 2), pos_a, 1)
                r_crop_hand = cv2.warpAffine(r_crop_hand, M, (250, 250))
                r_results = hands.process(r_crop_hand)
                r_crop_hand = cv2.cvtColor(r_crop_hand, cv2.COLOR_BGR2RGB)
                thumb = 0
                wrist = 0
                if r_results.multi_hand_landmarks:
                    for r in r_results.multi_hand_landmarks:
                        for r_id, r_lm in enumerate(r.landmark):
                            r_crop_hand = cv2.circle(r_crop_hand, (int(r_lm.x*250), int(r_lm.y*250)), 1, (0,0,255), -1)
                            if r_id == 0:
                                wrist = r_lm.y
                            if r_id == 2:
                                thumb = r_lm.y

                if thumb <= wrist:
                    final_score = 1
                else:
                    final_score = 2
        else:
            pass

    if state == "left":
        if len(l_hand) == 2:
            p3 = [int(preds[8][0]), int(preds[8][1])]
            p1 = [int(preds[10][0]), int(preds[10][1])]
            p2 = [int(preds[8][0]) + 1, int(preds[8][1])]
            if p1[1] >= p3[1]:
                pos_a = -int(getAngle3P(p1, p2, p3))
            else:
                pos_a = (int(getAngle3P(p1, p2, p3)))

            l_x_d = abs(l_hand[0][0] - l_hand[1][0]) * 3
            if l_x_d > 15:
                c_x, c_y = int((l_hand[1][0] + l_hand[0][0]) / 2), int((l_hand[1][1] + l_hand[0][1]) / 2)
                l_crop_hand = input_p[c_y - l_x_d:c_y + l_x_d, c_x - l_x_d:c_x + l_x_d]
                l_crop_hand = cv2.resize(l_crop_hand, (200, 200))
                M = cv2.getRotationMatrix2D((200 / 2, 200 / 2), pos_a, 1)
                l_crop_hand = cv2.warpAffine(l_crop_hand, M, (250, 250))
                l_results = hands.process(l_crop_hand)
                thumb = 0
                wrist = 0
                if l_results.multi_hand_landmarks:
                    for l in l_results.multi_hand_landmarks:
                        for l_id, l_lm in enumerate(l.landmark):
                            if l_id == 0:
                                wrist = l_lm.y
                            if l_id == 2:
                                thumb = l_lm.y
                if thumb >= wrist:
                    final_score = 1
                else:
                    final_score = 2
        else:
            pass

    return final_score

class REBA:
    def __init__(self, key):
        class_dict = {}
        for class_name, k in zip(class_list, key):
            class_dict[class_name] = k
        self.class_dicts = class_dict

    def reba_hand(self):
        c_dict = self.class_dicts
        l_angle = abs(180 - getAngle3P(c_dict["l-elbow"], c_dict["l-wrist"], c_dict["l-hand"]))
        r_angle = abs(180 - getAngle3P(c_dict["r-elbow"], c_dict["r-wrist"], c_dict["r-hand"]))
        if l_angle > 90:
            l_angle = -1
        if r_angle > 90:
            r_angle = -1

        if l_angle > r_angle:
            b_angle = l_angle
        else:
            b_angle = r_angle

        if b_angle < 15:
            state = 1
        else:
            state = 2

        return state, int(b_angle)

    def reba_elbow(self):
        c_dict = self.class_dicts
        l_angle = abs(180 - getAngle3P(c_dict["l-shou"], c_dict["l-elbow"], c_dict["l-wrist"]))
        r_angle = abs(180 -getAngle3P(c_dict["r-shou"], c_dict["r-elbow"], c_dict["r-wrist"]))

        if l_angle > r_angle:
            b_angle = l_angle
        else:
            b_angle = r_angle

        if b_angle < 60:
            state = 2
        elif 60 <= b_angle < 100:
            state = 1
        elif 100 <= b_angle:
            state = 2

        return state, int(b_angle)

    def reba_shou(self):
        c_dict = self.class_dicts
        l_angle = abs(getAngle3P(c_dict["spine-1"], c_dict["l-shou"], c_dict["l-elbow"]))
        r_angle = abs(getAngle3P(c_dict["spine-1"], c_dict["r-shou"], c_dict["r-elbow"]))

        if l_angle > r_angle:
            b_angle = l_angle
        else:
            b_angle = r_angle

        if b_angle < 20:
            state = 1
        elif 20 <= b_angle < 45:
            state = 2
        elif 45 <= b_angle < 90:
            state = 3
        elif 90 <= b_angle:
            state = 4

        return state, int(b_angle)

    def reba_back(self):
        c_dict = self.class_dicts
        spine2_up = [c_dict["spine-2"][0], c_dict["spine-2"][1] + 5]
        b_angle = abs(180 - getAngle3P(spine2_up, c_dict["spine-2"], c_dict["spine-1"]))

        if b_angle < 5:
            state = 1
        elif 5 <= b_angle < 20:
            state = 2
        elif 20 <= b_angle < 60:
            state = 3
        elif 60 <= b_angle:
            state = 4

        return state, int(b_angle)

    def reba_neck(self):
        c_dict = self.class_dicts
        # neck_down_up = [c_dict["neck-down"][0], c_dict["neck-down"][1] + 5]
        b_angle = abs(180 - getAngle3P(c_dict["spine-1"], c_dict["neck-down"], c_dict["neck-up"]))

        if b_angle < 20:
            state = 1
        elif 20 <= b_angle:
            state = 2

        return state, int(b_angle)

    def reba_leg(self):
        c_dict = self.class_dicts
        l_angle = abs(180 - getAngle3P(c_dict["l-hip"], c_dict["l-knee"], c_dict["l-ankle"]))
        r_angle = abs(180 - getAngle3P(c_dict["r-hip"], c_dict["r-knee"], c_dict["r-ankle"]))

        if l_angle > r_angle:
            b_angle = l_angle
        else:
            b_angle = r_angle

        if b_angle < 60:
            state = 1
        elif 60 <= b_angle:
            state = 2

        return state, int(b_angle)

class OWAS:
    def __init__(self, key):
        class_dict = {}
        for class_name, k in zip(class_list, key):
            class_dict[class_name] = k
        self.class_dicts = class_dict

    def owas_back(self):
        c_dict = self.class_dicts
        spine2_up = [c_dict["spine-2"][0], c_dict["spine-2"][1] + 5]
        b_angle = abs(180 - getAngle3P(spine2_up, c_dict["spine-2"], c_dict["spine-1"]))

        if b_angle < 30:
            state = 1
        else:
            state = 2

        return state, int(b_angle)

    def owas_shou(self):
        c_dict = self.class_dicts
        l_shou_y = c_dict["l-shou"][1]
        r_shou_y = c_dict["r-shou"][1]
        l_hand_y = c_dict["l-hand"][1]
        r_hand_y = c_dict["r-hand"][1]
        state = 1
        if l_hand_y < l_shou_y:
            state += 1

        if r_hand_y < r_shou_y:
            state += 1


        return state, 0

    def owas_neck(self):
        c_dict = self.class_dicts
        # neck_down_up = [c_dict["neck-down"][0], c_dict["neck-down"][1] + 5]
        b_angle = abs(180 - getAngle3P(c_dict["spine-1"], c_dict["neck-down"], c_dict["neck-up"]))
        if b_angle > 90:
            b_angle = 180 - b_angle

        if b_angle < 20:
            state = 1
        elif 20 <= b_angle:
            state = 2

        return state, int(b_angle)









