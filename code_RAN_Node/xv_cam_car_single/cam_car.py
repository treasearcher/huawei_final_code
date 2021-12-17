import time

import cv2
import json
from socket import *
# import socket
import numpy as np
from tool.utils import load_class_names, plot_boxes_cv2
import _thread
# import requests


def send_from(arr, dest):
    view = memoryview(arr).cast('B')
    while len(view):
        nsent = dest.send(view)
        view = view[nsent:]

def recv_into(arr, source):
    view = memoryview(arr).cast('B')
    while len(view):
        nrecv = source.recv_into(view)
        view = view[nrecv:]

fps = 0
fps_dis = 0
def fps_count():
    global fps, fps_dis
    while 1:
        time.sleep(10)
        fps_dis=fps/10
        print(fps)
        # requests.post(url='', data={'fps': str(fps)},
        #               headers={'Content-Type': 'application/x-www-form-urlencoded'})
        fps=0

_thread.start_new_thread(fps_count, ())

s = socket(AF_INET, SOCK_STREAM)
s.bind(('', 25000))
s.listen(1)
c,a = s.accept()
# c_3,a_3=s.accept()
cap = cv2.VideoCapture(0)
flag = cap.isOpened()
print(flag)
namesfile = 'data/coco.names'
class_names = load_class_names(namesfile)
while (1):
    # get a frame
    _, img = cap.read()
    # print(111)

    send_from(img, c)
    # print(222)
    lth = np.zeros(1, dtype=np.int64)
    recv_into(lth, c)
    if not lth[0]==0:
        boxes = np.zeros((1, lth[0], 7), dtype=np.float32)
        recv_into(boxes, c)
        boxes=boxes.tolist()
        for i in range(lth[0]):
            boxes[0][i][-1]=np.int64(boxes[0][i][-1])
        img = plot_boxes_cv2(img, boxes[0], 'predictions.jpg', class_names)
    fps += 1
    img = cv2.putText(img, 'FPS: {}'.format(fps_dis), (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 2)
    cv2.imshow('', img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
c.close()
s.close()