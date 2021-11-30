import time
from pprint import pprint
import json
import os
from tqdm import tqdm


def change_filename():
    path = '../ai_json/추가 정밀평가3'
    li = sorted(os.listdir(path),key=lambda x : int(x.split('.')[0]))
    for json_file in li:
        json_path = os.path.join(path, json_file)
        new_name = str(int(json_file.split('/')[-1].split('.')[0])+60)+'.json'
        print(json_file,'-->',new_name)
        new_path = os.path.join(path,new_name)
        os.rename(json_path,new_path)


def compare_gt_ai(ai_path,gt_path,is_only_step):
    ai_json_dirs = sorted([os.path.join(ai_path,i) for i in os.listdir(ai_path) if os.path.isdir(os.path.join(ai_path,i))],key=lambda x: int(x[-1]))
    # gt_json_dirs = [os.path.join(gt_path, i) for i in os.listdir(gt_path) if os.path.isdir(os.path.join(gt_path,i))]
    gt_json_dirs = sorted([os.path.join(gt_path, i) for i in os.listdir(gt_path) if os.path.isdir(os.path.join(gt_path,i))],key=lambda x : int(x[-1]))
    zip_ai_gt = zip(ai_json_dirs,gt_json_dirs)
    rula_acc_list = []
    reba_acc_list = []
    owas_acc_list = []

    for _ in tqdm(range(100)):
        score_list = []
        for ai, gt in list(zip(ai_json_dirs,gt_json_dirs)):
            # for _ in range(100):
            #     time.sleep(0.1)
            assert os.path.split(ai)[-1] == os.path.split(gt)[-1], f'directory name is not same {os.path.split(ai)[-1]} != {os.path.split(gt)[-1]}'
            # assert ai.split('/')[-1] == gt.split('/')[-1], 'directory name is not same'

            ai_jsons = sorted([os.path.join(ai,j) for j in os.listdir(ai)],key=lambda x : int(os.path.split(x)[-1].split('.')[0]))
            gt_jsons = sorted([os.path.join(gt,j) for j in os.listdir(gt)],key=lambda x : int(os.path.split(x)[-1].split('.')[0]))
            for ai_json, gt_json in zip(ai_jsons,gt_jsons):
                assert os.path.split(ai_json)[-1] == os.path.split(gt_json)[-1], f'File is not same {os.path.split(ai_json)[-1]} != {os.path.split(gt_json)[-1]}'
                with open(ai_json,'r') as f:
                    ai = json.load(f)

                with open(gt_json,'r') as f:
                    gt = json.load(f)
                if is_only_step == 1:
                    # print(ai)
                    temp = 0
                    for key, pre in ai.items():
                        if int(gt[key]) == int(pre['totalScore']['step']):
                            temp += 1


                    if 98 >= temp >= 1:
                        score_list.append(1)
                    elif temp == 99:
                        continue
                    elif temp == 0:
                        score_list.append(0)


                # if temp != 0:
                #     score_list.append(1)
            # else:
            #     for key,pre in ai.items():
            #         answer_list = []
            #         if key.lower() == 'rula':
            #             for k,v in pre.items():
            #                 if k == 'wristTwist':
            #                     answer_list.append(0)
            #
            #                 elif k == 'shoulder':
            #                     if abs(ai[key][k]['poseScore'] - gt[key]['shou']) <= 1:
            #                         answer_list.append(0)
            #                     else:
            #                         answer_list.append(1)
            #
            #                 elif k == 'back':
            #                     if abs(ai[key][k]['poseScore'] - gt[key][k]) <= 1:
            #                         answer_list.append(0)
            #                     else:
            #                         answer_list.append(1)
            #
            #                 elif k == 'neck':
            #                     answer_list.append(0)
            #
            #
            #                 elif k == 'leg':
            #                     if ai[key][k]['poseScore'] == gt[key][k]:
            #                         answer_list.append(0)
            #                     else:
            #                         answer_list.append(1)
            #
            #                 elif k == 'elbow':
            #                     if ai[key][k]['poseScore'] == gt[key][k]:
            #                         answer_list.append(0)
            #                     else:
            #                         answer_list.append(1)
            #
            #                 elif k == 'wrist':
            #                     if ai[key][k]['poseScore'] == gt[key][k]:
            #                         answer_list.append(0)
            #                     else:
            #                         answer_list.append(1)
            #
            #                 if 'add' in ai[key][k].keys():
            #                     if k == 'shoulder':
            #                         answer_list.append(0)
            #                     else:
            #                         answer_list.append(0)
            #
            #             rula_acc_list.append(answer_list)
            #
            #
            #         elif key.lower() == 'reba':
            #             if type(gt[key]['weight']) == int:
            #                 answer_list.append(0)
            #             if type(gt[key]['handler']) == int:
            #                 answer_list.append(0)
            #             if type(gt[key]['action']) == int:
            #                 answer_list.append(0)
            #             for ak,av in ai[key]['group A'].items():
            #                 if ak == 'back':
            #                     if gt[key][ak] == 1:
            #                         answer_list.append(0)
            #                     elif gt[key][ak] == av['poseScore']:
            #                         answer_list.append(0)
            #                     else:
            #                         answer_list.append(1)
            #                     pass
            #                 elif ak == 'neck':
            #                     if gt[key][ak] == av['poseScore']:
            #                         answer_list.append(0)
            #                     else:
            #                         answer_list.append(1)
            #                     pass
            #                 elif ak == 'leg':
            #                     if gt[key][ak] == av['poseScore']:
            #                         answer_list.append(0)
            #                     else:
            #                         answer_list.append(1)
            #
            #
            #                 if type(av) == dict:
            #                     if 'add' in av.keys():
            #                         answer_list.append(0)
            #
            #
            #             for bk,bv in ai[key]['group B'].items():
            #                 if bk == 'shoulder':
            #                     bk = 'shou'
            #                     if gt[key][bk] == 1:
            #                         answer_list.append(0)
            #                     elif gt[key][bk] == bv['poseScore']:
            #                         answer_list.append(0)
            #                     else:
            #                         answer_list.append(1)
            #                     pass
            #                 elif bk == 'elbow':
            #                     if gt[key][bk] == bv['poseScore']:
            #                         answer_list.append(0)
            #                     else:
            #                         answer_list.append(1)
            #                     pass
            #                 elif bk == 'wrist':
            #                     answer_list.append(0)
            #
            #
            #                 if type(bv) == dict:
            #                     if 'add' in bv.keys():
            #                         answer_list.append(0)
            #
            #             reba_acc_list.append(answer_list)
            #             pass
            #         elif key.lower() == 'owas':
            #             for k,v in ai[key].items():
            #                 if k == 'arm':
            #                     k = 'shou'
            #
            #                 if k == 'back':
            #                     if gt[key][k] == 1 or gt[key][k] == 2:
            #                         answer_list.append(0)
            #                     elif gt[key][k] == ai[key][k]['poseCode']:
            #                         answer_list.append(0)
            #                     else:
            #                         answer_list.append(1)
            #
            #                 elif k == 'shou':
            #                     if gt[key][k] == ai[key]['arm']['poseCode']:
            #                         answer_list.append(0)
            #                     else:
            #                         answer_list.append(1)
            #
            #                 elif k == 'leg':
            #                     if gt[key][k] == 1:
            #                         answer_list.append(0)
            #                     elif gt[key][k] == ai[key][k]['poseCode']:
            #                         answer_list.append(0)
            #                     else:
            #                         answer_list.append(1)
            #
            #                 elif k == 'weight':
            #                     answer_list.append(0)
            #
            #             owas_acc_list.append(answer_list)

    if is_only_step == 1:
        return score_list

    else:
        return rula_acc_list, reba_acc_list, owas_acc_list
print()
print('평가 시작')
score = compare_gt_ai('/home/bong08/mskim/infinyx/bit_ms/ai_json','/home/bong08/mskim/infinyx/bit_ms/only_step',1)
print('정확도 : ',round(len([i for i in score if i == 1])/94*100,1),'%')
print()
# change_filename()
# # print(len(rula[0]),len(reba[0]),len(owas[0]))
# rula_ = [sum(i)/len(i) for i in rula]
# reba_ = [sum(i)/len(i) for i in reba]
# owas_ = [sum(i)/len(i) for i in owas]
# print('RULA : ',sum(rula_)/len(rula_))
# print('REBA : ',sum(reba_)/len(reba_))
# print('OWAS : ',sum(owas_)/len(owas_))

