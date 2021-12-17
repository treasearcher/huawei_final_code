import cv2
import json
from socket import *
from tool.utils import load_class_names, plot_boxes_cv2
import queue, _thread, threading, time
import numpy as np
#
# qsize = 3
# lock = threading.Lock()
#
# class Image(threading.Thread):
#     def __init__(self):
#         super().__init__()
#
#     def manual_init(self):
#         self.img_recv = queue.Queue(qsize)
#         self.last_recv = ''
#         self.img_recv_cor = queue.Queue(qsize)
#         self.last_recv_cor = ''
#
#         self.server = socket(AF_INET, SOCK_STREAM)
#         self.server.bind(('', 24999))
#         self.server.listen(1)
#         self.client, _ = self.server.accept()
#         print(3)
#
#     def recv_from_phone(self):
#         acc_data = b''
#         result = b''
#         while 1:
#             # print('recv_from_phone')
#             acc_data = self.client.recv(1024)
#             result += acc_data
#             # print("acc_data")
#             if len(acc_data) == 0 or \
#                     (len(acc_data) == 1 and acc_data[0] == 217) or \
#                     (len(acc_data) > 1 and acc_data[-1] == 217 and acc_data[-2] == 255):
#                 break
#         if result == b'':
#             print(111)
#             time.sleep(0.3)
#             return b''
#         img_buffer_numpy = np.frombuffer(result, dtype=np.uint8)  # 将 图片字节码bytes  转换成一维的numpy数组 到缓存中
#         img_numpy = cv2.imdecode(img_buffer_numpy, 1)  # 从指定的内存缓存中读取一维numpy数据，并把数据转换(解码)成图像矩阵格式
#         img_numpy = cv2.resize(img_numpy, (640, 480))
#         # print('img')
#         # print(img_numpy.shape)
#         return img_numpy
#
#     def recv_from_phone_thread(self):
#         while 1:
#             print('?')
#             img = self.recv_from_phone()
#             # img_cor=img.copy()
#             # print('recv')
#             if len(img) == 0:
#                 # print("??")
#                 continue
#             if self.img_recv.full():
#                 lock.acquire()
#                 self.last_recv = img
#                 lock.release()
#                 print('1 full')
#             else:
#                 lock.acquire()
#                 self.last_recv = ''
#                 self.img_recv.put(img)
#                 lock.release()
#             if self.img_recv_cor.full():
#                 lock.acquire()
#                 self.last_recv_cor = img
#                 lock.release()
#             else:
#                 lock.acquire()
#                 self.last_recv_cor = ''
#                 self.img_recv_cor.put(img)
#         # self.server.close()
#         # self.client.close()
#
#     def get_recv_img(self):
#         while self.img_recv.empty() and self.last_recv == '':
#             time.sleep(0.1)
#         print('get_recv')
#         if not self.img_recv.empty():
#             return self.img_recv.get()
#         else:
#             img = self.last_recv
#             self.last_recv = ''
#             return img
#
#     def get_recv_img_cor(self):
#         while self.img_recv_cor.empty() and self.last_recv_cor == '':
#             time.sleep(0.1)
#         print('get_recv_cor')
#         if not self.img_recv_cor.empty():
#             return self.img_recv_cor.get()
#         else:
#             img = self.last_recv_cor
#             self.last_recv_cor = ''
#             return img
#
#     def run(self) -> None:
#         _thread.start_new_thread(self.recv_from_phone_thread, ())
#
#
# image = Image()
# image.manual_init()
#
# # def get_img():
# #     global image
# #     while 1:
# #         img=image.get_recv_img()
# #         print(1, img.shape)
# #         # cv2.imshow('1', img)
# #
# # def get_img_cor():
# #     global image
# #     while 1:
# #         img=image.get_recv_img_cor()
# #         print(2, img.shape)
# #         # cv2.imshow('2', img)
#
# image.start()
# # _thread.start_new_thread(get_img, ())
# # _thread.start_new_thread(get_img_cor, ())
#
# while 1:
#     img = image.get_recv_img()
#     print(1, img.shape)












qsize = 3
img_recv = queue.Queue(qsize)
last_recv = ''
img_recv_cor = queue.Queue(qsize)
last_recv_cor = ''
lock = threading.Lock()
# time.sleep(10)

s_phone = socket(AF_INET, SOCK_STREAM)
s_phone.bind(('', 24999))
s_phone.listen(1)
c_p, a_p=s_phone.accept()
print(3)

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
    # print('img')
    # print(img_numpy.shape)
    return img_numpy


def recv_from_phone_thread():
    global img_recv, last_recv
    while 1:
        img = recv_from_phone()
        img_cor=img.copy()
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
        if img_recv_cor.full():
            lock.acquire()
            last_recv_cor=img
            lock.release()
        else:
            lock.acquire()
            last_recv_cor=''
            img_recv_cor.put(img)
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
def get_recv_img_cor():
    global img_recv_cor, last_recv_cor
    while img_recv_cor.empty() and last_recv_cor == '':
        time.sleep(0.1)
    #print('get_recv_cor')
    if not img_recv_cor.empty():
        return img_recv_cor.get()
    else:
        img = last_recv_cor
        last_recv_cor = ''
        return img

        

_thread.start_new_thread(recv_from_phone_thread, ())
while 1:
    img = get_recv_img()
    cv2.imshow('11',img)
    cv2.waitKey(1)
    img2=get_recv_img_cor()
    cv2.imshow('22',img2)
    cv2.waitKey(1)

