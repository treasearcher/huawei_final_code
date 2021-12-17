import cv2
import json
from socket import *
from tool.utils import load_class_names, plot_boxes_cv2
import queue, _thread, threading, time
import numpy as np


ip_add = '192.168.1.110'
# ip_add = '127.0.0.1'
# ip_add = ''

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


s = socket(AF_INET, SOCK_STREAM)
s.bind(('', 25000))
s.listen(1)
c,a = s.accept()
print(1)
c_2 = socket(AF_INET, SOCK_STREAM)
c_2.connect((ip_add, 25002))
print(2)
qsize = 3
boxQue = queue.Queue(qsize)
img_sent = queue.Queue(qsize)
img_recv = queue.Queue(qsize)
last_recv = ''
lock = threading.Lock()
# time.sleep(10)

s_phone = socket(AF_INET, SOCK_STREAM)
s_phone.bind(('', 24999))
s_phone.listen(1)
c_p, a_p=s_phone.accept()
print(3)

fps = 0
fps_dis = 0

def recv_box():
    lth = np.zeros(shape=(1, ),dtype=np.int64)
    while 1:
        if boxQue.full():
            # print('box is full')
            time.sleep(0.1)
        else:
            recv_into(lth, c_2)
            if lth[0] == 0:
                lock.acquire()
                boxQue.put([0])
                lock.release()
                continue
            arr = np.zeros(shape=(1, lth[0], 7), dtype=np.float32)
            recv_into(arr, c_2)
            box = arr.tolist()
            for i in range(lth[0]):
                box[0][i][-1]=np.int64(box[0][i][-1])
            lock.acquire()
            boxQue.put(box)
            lock.release()
            print('recv')

# sum_flag = np.zeros(shape=(1,), dtype=np.int32)
# def recv_flag():
#     global sum_flag
#     recv_into(sum_flag, c)
#     print('done')

def recv_from_phone():
    acc_data = b''
    result = b''
    while 1:
        acc_data = c_p.recv(1024)
        result += acc_data
        if len(acc_data) == 0 or \
                (len(acc_data) == 1 and acc_data[0] == 217) or \
                (len(acc_data) > 1 and acc_data[-1] == 217 and acc_data[-2] == 255):
            break
    if result == b'':
        print(111)
        time.sleep(0.3)
        return b''
    img_buffer_numpy = np.frombuffer(result, dtype=np.uint8)  # 将 图片字节码bytes  转换成一维的numpy数组 到缓存中
    img_numpy = cv2.imdecode(img_buffer_numpy, 1)  # 从指定的内存缓存中读取一维numpy数据，并把数据转换(解码)成图像矩阵格式
    img_numpy = cv2.resize(img_numpy, (640, 480))
    print('img')
    print(img_numpy.shape)
    return img_numpy

def recv_from_phone_thread():
    global img_recv, last_recv
    while 1:
        img = recv_from_phone()
        if len(img)==0:
            continue
        if img_recv.full():
            lock.acquire()
            last_recv=img
            lock.release()
        else:
            lock.acquire()
            last_recv=''
            img_recv.put(img)
            lock.release()

def get_recv_img():
    global img_recv, last_recv
    while img_recv.empty() and last_recv=='':
        time.sleep(0.1)
    if not img_recv.empty():
        return img_recv.get()
    else:
        img = last_recv
        last_recv=''
        return img

def cam_send():
    cnt_arr = np.zeros(shape=(1,), dtype=np.int32)
    while 1:
        img = get_recv_img()
        # print(img.shape)
        send_from(img, c)
        send_from(np.array([np.sum(img)]), c)
        recv_into(cnt_arr, c)
        if cnt_arr[0]>=5:
            break
    while 1:
        while img_sent.full() or img_recv.empty():
            # print('sent is full')
            time.sleep(0.1)
        img = get_recv_img()
        print(img.shape)
        send_from(img, c)
        lock.acquire()
        img_sent.put(img)
        lock.release()
        # print(img)
        # print(np.sum(img))
        print('send')

def fps_update():
    global fps, fps_dis
    while 1:
        time.sleep(10)
        print(fps)
        fps_dis = fps / 10
        fps = 0

_thread.start_new_thread(recv_box, ())
_thread.start_new_thread(cam_send, ())
_thread.start_new_thread(fps_update, ())
_thread.start_new_thread(recv_from_phone_thread, ())

# def get_box():
#     while boxQue.empty():
#         time.sleep(0.1)
#     lock.acquire()
#     box = boxQue.get()
#     lock.release()
#     return box

namesfile = 'data/coco.names'
class_names = load_class_names(namesfile)
while (1):
    # get a frame
    while img_sent.empty() or boxQue.empty():
        # print('sent or box are empty')
        time.sleep(0.1)
    lock.acquire()
    img = img_sent.get()
    boxes = boxQue.get()
    lock.release()
    # print(np.sum(img))
    # start = time.time()
    if boxes[0] == 0:
        pass
    else:
        img = plot_boxes_cv2(img, boxes[0], 'predictions.jpg', class_names)
    img = cv2.putText(img, 'FPS: {}'.format(fps_dis), (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 2)
    # end = time.time()
    # print('time: ', end - start)
    cv2.imshow('fps:', img)
    fps += 1
    # send_from(frame, c_3)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
c.close()
s.close()

