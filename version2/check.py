from __future__ import print_function
import json
import math
import operator
from functools import reduce
import numpy as np
from PIL import Image
from config import TODAY_PATH, YESTERDAY_PATH

def check():
    from config import URL, PROJECT_NAME, TO, PRESENTATION_ID, PROJECT_PATH, TODAY_PATH, YESTERDAY_PATH, IMAGE_SIZE
    yesterday_record = open(YESTERDAY_PATH  + 'slide_id.json', 'r')
    today_record = open(TODAY_PATH + '/slide_id.json', 'r')

    yesterday_detail = json.load(yesterday_record)
    today_detail = json.load(today_record)

    yesterday_id = list(np.array(yesterday_detail)[:, 0])
    today_id = list(np.array(today_detail)[:, 0])
    yesterday_id_split = [item.split('~*~')[0] for item in yesterday_id]
    today_id_split = [item.split('~*~')[0] for item in today_id]

    # deteted slides
    deteted_slides = []
    yesterday_remove_id = []
    for i in range(len(yesterday_id_split)):
        if yesterday_id_split[i] not in today_id_split:
            deteted_slides.append((yesterday_detail[i][0], 'deleted'))
            yesterday_remove_id.append(i)
    for id in yesterday_id_split:
        if id in yesterday_remove_id:
            yesterday_id.remove(id)

    # added slides
    added_slides = []
    today_remove_id = []
    for i in range(len(today_id)):
        if today_id_split[i] not in yesterday_id_split:
            added_slides.append((today_detail[i][0], 'added'))
            today_remove_id.append(i)
    for id in today_id_split:
        if id in today_remove_id:
            today_id_split.remove(id)

    # changed slides
    changed_slides = []
    for i in range(len(today_id)):
        if today_id[i] in yesterday_id:
            for j in range(len(yesterday_id)):  # find index of yesterday_id == today_id
                if yesterday_id[j] == today_id[i]:
                    break
            if today_detail[i][2] != yesterday_detail[j][2]:  # check diffrence
                changed_slides.append((today_detail[i][0], 'changed'))

    yesterday_record.close()
    today_record.close()
    return deteted_slides, added_slides, changed_slides


def checkout_changed(changed):
    from config import URL, PROJECT_NAME, TO, PRESENTATION_ID, PROJECT_PATH, TODAY_PATH, YESTERDAY_PATH, IMAGE_SIZE
    changed_remove = []
    for item in changed:
        today_im = Image.open(TODAY_PATH + item[0].split('~*~')[0] + '.jpg')
        yesterday_im = Image.open(YESTERDAY_PATH + item[0].split('~*~')[0] + '.jpg')
        histogram1 = today_im.histogram()
        histogram2 = yesterday_im.histogram()
        differ = math.sqrt(
            reduce(operator.add, list(map(lambda a, b: (a - b) ** 2, histogram1, histogram2))) / len(histogram1))
        print(str(item[0]) + ' : ' + str(differ))
        if differ == 0:
            changed_remove.append(item)

    for item in changed_remove:
        changed.remove(item)
    return changed

def get_diff_list():
    print("=== * CHECK DIFF * ===")
    result_list = []
    deleted, added, changed = check()
    changed = checkout_changed(changed)
    results = deleted + added + changed
    for result in results:
        item = [item.split('~*~') for item in result]
        item[0].append(result[1])
        result_list.append(item[0])
    result_list = sorted(result_list, key=lambda x : x[1])
    return result_list
