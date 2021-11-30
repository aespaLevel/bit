import json
import os
import sys
sys.path.append("../")


def compare_gt_ai(gt_json, ai_json):
    with open(gt_json) as json_file:
        gt_data = json.load(json_file)

    with open(ai_json) as json_file:
        ai_data = json.load(json_file)

    gt_rula = gt_data["RULA"]
    ai_rula = ai_data["RULA"]

    gt_reba = gt_data["REBA"]
    ai_reba = ai_data["REBA"]

    gt_owas = gt_data["OWAS"]
    ai_owas = ai_data["OWAS"]

    # rula
    ru_back = abs(gt_rula['back'] - (ai_rula['back']['poseScore']))
    ru_neck = abs(gt_rula['neck'] - (ai_rula['neck']['poseScore']))
    ru_leg = abs(gt_rula['leg'] - (ai_rula['leg']['poseScore']))
    ru_shou = abs(gt_rula['shou'] - (ai_rula['shoulder']['poseScore']))
    ru_elbow = abs(gt_rula['elbow'] - (ai_rula['elbow']['poseScore']))
    ru_wrist = abs(gt_rula['wrist'] - (ai_rula['wrist']['poseScore']))

    rula_score = ((ru_back + ru_neck + ru_leg + ru_shou + ru_elbow + ru_wrist)/9) ** 2
    print('\n',os.path.split(gt_json)[-1],os.path.split(gt_json)[-1])
    print("-rula-")
    ru_class_list = ['back', 'neck', 'leg', 'shou', 'elbow', 'wrist']
    ru_score_list = [ru_back, ru_neck, ru_leg, ru_shou, ru_elbow, ru_wrist]
    for ru_c, ru_s in zip(ru_class_list, ru_score_list):
        print(f'{ru_c} miss = {ru_s}')

    # reba

    re_back = abs(gt_reba['back'] - (ai_reba['group A']['back']['poseScore']))
    re_neck = abs(gt_reba['neck'] - (ai_reba['group A']['neck']['poseScore']))
    re_leg = abs(gt_reba['leg'] - (ai_reba['group A']['leg']['poseScore']))
    re_shou = abs(gt_reba['shou'] - (ai_reba['group B']['shoulder']['poseScore']))
    re_elbow = abs(gt_reba['elbow'] - (ai_reba['group B']['elbow']['poseScore']))
    re_wrist = abs(gt_reba['wrist'] - (ai_reba['group B']['wrist']['poseScore']))

    reba_score = ((re_back + re_neck + re_leg + re_shou + re_elbow + re_wrist)/9) ** 2

    print("\n-reba-")
    re_class_list = ['back', 'neck', 'leg', 'shou', 'elbow', 'wrist']
    re_score_list = [re_back, re_neck, re_leg, re_shou, re_elbow, re_wrist]
    for re_c, re_s in zip(re_class_list, re_score_list):
        print(f'{re_c} miss = {re_s}')

    # owas

    ow_back = abs(gt_owas['back'] - (ai_owas['back']['poseCode']))
    ow_shou = abs(gt_owas['shou'] - (ai_owas['arm']['poseCode']))
    ow_leg = abs(gt_owas['leg'] - (ai_owas['leg']['poseCode']))

    owas_score = ((ow_back + ow_shou + ow_leg)/5) ** 2

    print('\n-owas-')
    ow_class_list = ['back', 'shou', 'leg']
    ow_score_list = [ow_back, ow_shou, ow_leg]
    for ow_c, ow_s in zip(ow_class_list, ow_score_list):
        print(f'{ow_c} miss = {ow_s}')

    return rula_score, reba_score, owas_score

def cal_score(gtpath,aipath):
    json_names = os.listdir(aipath)
    rula_total_score = 0
    reba_total_score = 0
    owas_total_score = 0
    file_num = 0
    for json_name in json_names:
        ai_dir = os.path.join(aipath, json_name)
        gt_dir = os.path.join(gtpath, json_name)
        if os.path.isdir(ai_dir) or os.path.isdir(gt_dir):
            continue
        ru, re, ow = compare_gt_ai(gt_dir, ai_dir)
        rula_total_score += ru
        reba_total_score += re
        owas_total_score += ow
        file_num += 1
        #
        # except:
        #     print(f"error---> {json_name} none gt file or calc miss")

    if file_num != 0:
        rula_total_score = rula_total_score/file_num
        reba_total_score = reba_total_score/file_num
        owas_total_score = owas_total_score/file_num

        total_score = (rula_total_score + reba_total_score + owas_total_score)/3
    else:
        return None, None, None, None

    return rula_total_score, reba_total_score, owas_total_score, total_score

