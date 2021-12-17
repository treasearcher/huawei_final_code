import cv2
import json
from socket import *
from tool.utils import load_class_names, plot_boxes_cv2
import queue, _thread, threading, time
import numpy as np

# ip_add = '192.168.1.110'
qsize = 3
lock = threading.Lock()
namesfile = 'data/coco.names'
class_names = load_class_names(namesfile)


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


class Image(threading.Thread):
    def __init__(self):
        super().__init__()

    def manual_init(self):
        self.img_recv = queue.Queue(qsize)
        self.last_recv = ''
        self.img_recv_cor = queue.Queue(qsize)
        self.last_recv_cor = ''

        self.server = socket(AF_INET, SOCK_STREAM)
        self.server.bind(('', 24999))
        self.server.listen(1)
        self.client, _ = self.server.accept()
        print(3)

    def recv_from_phone(self):
        acc_data = b''
        result = b''
        while 1:
            # print('recv_from_phone')
            acc_data = self.client.recv(1024)
            result += acc_data
            if len(acc_data) == 0 or \
                    (len(acc_data) == 1 and acc_data[0] == 217) or \
                    (len(acc_data) > 1 and acc_data[-1] == 217 and acc_data[-2] == 255):
                break
        if result == b'':
            #print(111)
            time.sleep(0.3)
            return b''
        img_buffer_numpy = np.frombuffer(result, dtype=np.uint8)  # 将 图片字节码bytes  转换成一维的numpy数组 到缓存中
        img_numpy = cv2.imdecode(img_buffer_numpy, 1)  # 从指定的内存缓存中读取一维numpy数据，并把数据转换(解码)成图像矩阵格式
        img_numpy = cv2.resize(img_numpy, (640, 480))
        # print('img')
        # print(img_numpy.shape)
        return img_numpy

    def recv_from_phone_thread(self):
        while 1:
            img = self.recv_from_phone()
            # print('recv')
            if len(img) == 0:
                continue
            if self.img_recv.full():
                lock.acquire()
                self.last_recv = img
                lock.release()
            else:
                lock.acquire()
                self.last_recv = ''
                self.img_recv.put(img)
                lock.release()
            if self.img_recv_cor.full():
                lock.acquire()
                self.last_recv_cor = img
                lock.release()
            else:
                lock.acquire()
                self.last_recv_cor = ''
                self.img_recv_cor.put(img)
                lock.release()
        self.server.close()
        self.client.close()

    def get_recv_img(self):
        while self.img_recv.empty() and self.last_recv == '':
            time.sleep(0.1)
        # print('get_recv')
        if not self.img_recv.empty():
            return self.img_recv.get()
        else:
            img = self.last_recv
            self.last_recv = ''
            return img

    def get_recv_img_cor(self):
        while self.img_recv_cor.empty() and self.last_recv_cor == '':
            time.sleep(0.1)
        # print('get_recv_cor')
        if not self.img_recv_cor.empty():
            return self.img_recv_cor.get()
        else:
            img = self.last_recv_cor
            self.last_recv_cor = ''
            return img

    def run(self) -> None:
        _thread.start_new_thread(self.recv_from_phone_thread, ())


image = Image()


class SingleCam(threading.Thread):
    def __init__(self):
        super().__init__()
        # self.ip_add='192.168.1.100'
        self.server = socket(AF_INET, SOCK_STREAM)
        self.server.bind(('', 26000))
        self.server.listen(1)
        self.client, _ = self.server.accept()
        print(1)
        self.fps = 0
        self.fps_dis = 0
        self.img_dis=queue.Queue(10)

    def fps_count(self):
        while 1:
            time.sleep(10)
            self.fps_dis = self.fps / 10
            # print(fps)
            self.fps = 0

    def deal(self):
        while (1):
            img = image.get_recv_img()
            # print(111)

            send_from(img, self.client)
            # print(222)
            lth = np.zeros(1, dtype=np.int64)
            recv_into(lth, self.client)
            if not lth[0] == 0:
                boxes = np.zeros((1, lth[0], 7), dtype=np.float32)
                recv_into(boxes, self.client)
                boxes = boxes.tolist()
                for i in range(lth[0]):
                    boxes[0][i][-1] = np.int64(boxes[0][i][-1])
                img = plot_boxes_cv2(img, boxes[0], 'predictions.jpg', class_names)
            self.fps += 1
            ###################slp
            #lock.acquire()
            img = cv2.putText(img, 'FPS: {}'.format(self.fps_dis), (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0),
                              2)
            if not self.img_dis.full():
                self.img_dis.put(img)
            #cv2.imshow('ONE:', img)
            #lock.release()
            #if cv2.waitKey(1) & 0xFF == ord('q'):
            #    break
        # self.server.close()
        # self.client.close()
    def send_to_com(self):
        while 1:
            if self.img_dis.empty():
                time.sleep(0.1)
                continue
            lock.acquire()
            img=self.img_dis.get()
            lock.release()
            send_from(img, self.c_com)

    def run(self) -> None:

        self.s_com = socket(AF_INET, SOCK_STREAM)
        self.s_com.bind(('', 27000))
        self.s_com.listen(1)
        self.c_com, _ = self.s_com.accept()
        print(4)
        _thread.start_new_thread(self.fps_count, ())
        _thread.start_new_thread(self.deal, ())
        _thread.start_new_thread(self.send_to_com, ())


class CorCam(threading.Thread):
    def __init__(self):
        super().__init__()
        print(555)
        self.ip_add = '192.168.1.110'
        self.server = socket(AF_INET, SOCK_STREAM)
        self.server.bind(('', 25000))
        self.server.listen(1)
        self.c_1, _ = self.server.accept()
        self.c_2 = socket(AF_INET, SOCK_STREAM)
        self.c_2.connect((self.ip_add, 25002))
        print(2)
        qsize = 3
        self.boxQue = queue.Queue(qsize)
        self.img_sent = queue.Queue(qsize)
        self.img_recv = queue.Queue(qsize)
        self.img_dis = queue.Queue(qsize)
        self.last_recv = ''
        self.fps_cor = 0
        self.fps_dis_cor = 0

    def recv_box(self):
        lth = np.zeros(shape=(1,), dtype=np.int64)
        while 1:
            if self.boxQue.full():
                time.sleep(0.1)
            else:
                recv_into(lth, self.c_2)
                if lth[0] == 0:
                    lock.acquire()
                    self.boxQue.put([0])
                    lock.release()
                    continue
                arr = np.zeros(shape=(1, lth[0], 7), dtype=np.float32)
                recv_into(arr, self.c_2)
                box = arr.tolist()
                for i in range(lth[0]):
                    box[0][i][-1] = np.int64(box[0][i][-1])
                lock.acquire()
                self.boxQue.put(box)
                lock.release()
                # print('recv')

    def cam_send(self):
        cnt_arr = np.zeros(shape=(1,), dtype=np.int32)
        #while 1:
        #    img = image.get_recv_img_cor()
        #    send_from(img, self.c_1)
        #    #print('cam_send_img')
        #    sumation=np.sum(img)
        #    #print(sumation.dtype)
        #    send_from(np.array([sumation], dtype=np.int32), self.c_1)
        #    recv_into(cnt_arr, self.c_1)
        #    if cnt_arr[0] >= 5:
        #        break
        while 1:
            while self.img_sent.full():
                # print('sent is full')
                # if self.img_sent.full():
                #     print('full')
                # else:
                #     print('empty')
                time.sleep(0.1)
            img = image.get_recv_img_cor()
            # print(img.shape)
            send_from(img, self.c_1)
            lock.acquire()
            self.img_sent.put(img)
            lock.release()

    def fps_update(self):
        while 1:
            time.sleep(10)
            # print(self.fps)
            self.fps_dis_cor = self.fps_cor / 10
            self.fps_cor = 0

    def deal(self):
        while (1):
            # get a frame
            #print('11111')
            while self.img_sent.empty() or self.boxQue.empty():
                # print(2)
                time.sleep(0.1)
            lock.acquire()
            img_cor = self.img_sent.get()
            boxes = self.boxQue.get()
            lock.release()
            if boxes[0] == 0:
                pass
            else:
                img_cor = plot_boxes_cv2(img_cor, boxes[0], 'predictions.jpg', class_names)
            #lock.acquire()
            img_cor = cv2.putText(img_cor, 'FPS: {}'.format(self.fps_dis_cor), (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2,
                              (0, 0, 0), 2)
            if not self.img_dis.full():
                self.img_dis.put(img_cor)
            #cv2.imshow('TWO:', img_cor)
            #lock.release()
            self.fps_cor += 1
            #if cv2.waitKey(1) & 0xFF == ord('q'):
            #    break
        cv2.destroyAllWindows()
        self.c_1.close()
        self.server.close()
        self.c_2.close()

    def send_to_cam(self):
        while 1:
            if self.img_dis.empty():
                time.sleep(0.1)
                continue
            lock.acquire()
            img = self.img_dis.get()
            lock.release()
            send_from(img, self.c_com)

    def run(self) -> None:

        self.s_com = socket(AF_INET, SOCK_STREAM)
        self.s_com.bind(('', 27001))
        self.s_com.listen(1)

        self.c_com, _ = self.s_com.accept()
        print(5)
        _thread.start_new_thread(self.recv_box, ())
        _thread.start_new_thread(self.cam_send, ())
        _thread.start_new_thread(self.fps_update, ())
        _thread.start_new_thread(self.deal, ())
        _thread.start_new_thread(self.send_to_cam, ())


single = SingleCam()
cor = CorCam()
image.manual_init()
image.run()
single.run()
cor.run()

while 1:
    time.sleep(10)
