import cv2
import json
from socket import *
import queue, _thread, threading, time
import numpy as np
from tool.utils import load_class_names, plot_boxes_cv2
from PIL import Image
import matplotlib.pyplot as plt


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


s_1 = socket(AF_INET, SOCK_STREAM)
s_1.bind(('', 26000))
s_1.listen(1)
c_1, _ = s_1.accept()
print('send 1')
s_2 = socket(AF_INET, SOCK_STREAM)
s_2.bind(('', 25000))
s_2.listen(1)
c_2, _ = s_2.accept()
print('send 2')
c_2_2 = socket(AF_INET, SOCK_STREAM)
c_2_2.connect(('192.168.1.110', 25002))
print('send 2 2')

s_3 = socket(AF_INET, SOCK_STREAM)
s_3.bind(('', 28000))
s_3.listen(1)
c_3, _ = s_3.accept()
print('recv')
qsize=10
recv_que_one = queue.Queue(qsize)
recv_que_two = queue.Queue(qsize)
send_que_one = queue.Queue(qsize)
send_que_two = queue.Queue(qsize)
lock_one = threading.Lock()
lock_two = threading.Lock()

namesfile = 'data/coco.names'
class_names = load_class_names(namesfile)


def recv():
    global recv_que_one, recv_que_two
    arr = np.zeros(shape=(480, 640, 3), dtype=np.uint8)
    while 1:
        recv_into(arr, c_3)
        cnt = 0
        if not recv_que_one.full():
            lock_one.acquire()
            recv_que_one.put(arr)
            lock_one.release()
        else:
            cnt+=1
        if not recv_que_two.full():
            lock_two.acquire()
            recv_que_two.put(arr)
            lock_two.release()
        else:
            cnt+=1
        if cnt==2:
            time.sleep(0.1)


fps_one = 0
fps_dis_one = 0
def fps_one_update():
    global fps_one, fps_dis_one
    while 1:
        time.sleep(10)
        fps_dis_one=fps_one/10
        fps_one=0
def send_one():
    global recv_que_one, fps_one, fps_dis_one
    while 1:
        if recv_que_one.empty():
            time.sleep(0.1)
            continue
        lock_one.acquire()
        img = recv_que_one.get()
        # send_que_one.put(img)
        lock_one.release()
        send_from(img, c_1)
        lth = np.zeros(1, dtype=np.int64)
        recv_into(lth, c_1)
        if not lth[0] == 0:
            boxes = np.zeros((1, lth[0], 7), dtype=np.float32)
            recv_into(boxes, c_1)
            boxes = boxes.tolist()
            for i in range(lth[0]):
                boxes[0][i][-1] = np.int64(boxes[0][i][-1])
            img = plot_boxes_cv2(img, boxes[0], 'predictions.jpg', class_names)
        fps_one += 1
        img = cv2.putText(img, 'FPS: {}'.format(fps_dis_one), (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 2)
        # image = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        # image.show()
        # plt.imshow(image)
        # plt.show()
        cv2.imshow('ONE:', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


def send_two():
    global send_que_two
    while 1:
        if recv_que_two.empty() or send_que_two.full():
            time.sleep(0.1)
            continue
        lock_two.acquire()
        img = recv_que_two.get()
        send_que_two.put(img)
        lock_two.release()
        send_from(img, c_2)


fps_two = 0
fps_dis_two = 0
def fps_update_two():
    global fps_two, fps_dis_two
    while 1:
        time.sleep(10)
        fps_dis_two=fps_two/10
        fps_two=0
def recv_two():
    global fps_two, fps_dis_two, send_que_two
    while 1:
        if send_que_two.empty():
            time.sleep(0.1)
            continue
        lock_two.acquire()
        img = send_que_two.get()
        lock_two.release()
        lth = np.zeros(1, dtype=np.int64)
        recv_into(lth, c_2_2)
        if not lth[0] == 0:
            boxes = np.zeros((1, lth[0], 7), dtype=np.float32)
            recv_into(boxes, c_2_2)
            boxes = boxes.tolist()
            for i in range(lth[0]):
                boxes[0][i][-1] = np.int64(boxes[0][i][-1])
            img = plot_boxes_cv2(img, boxes[0], 'predictions.jpg', class_names)
        fps_two += 1
        img = cv2.putText(img, 'FPS: {}'.format(fps_dis_two), (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 2)
        cv2.imshow('TWO:', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


_thread.start_new_thread(recv, ())
_thread.start_new_thread(send_one, ())
_thread.start_new_thread(send_two, ())
_thread.start_new_thread(fps_one_update, ())
_thread.start_new_thread(fps_update_two, ())
_thread.start_new_thread(recv_two, ())

while 1:
    time.sleep(10)
