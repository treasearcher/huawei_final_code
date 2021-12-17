import cv2
import json
from socket import *
import queue, _thread, threading, time
import numpy as np


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


def display_one():
    ip_add = '192.168.1.120'
    client = socket(AF_INET, SOCK_STREAM)
    client.connect((ip_add, 27000))
    img = np.zeros(shape=(480, 640, 3), dtype=np.uint8)
    while 1:
        recv_into(img, client)
        cv2.imshow("ONE:", img)
        cv2.waitKey(1)


def display_two():
    ip_add = '192.168.1.120'
    client = socket(AF_INET, SOCK_STREAM)
    client.connect((ip_add, 27001))
    img = np.zeros(shape=(480, 640, 3), dtype=np.uint8)
    while 1:
        recv_into(img, client)
        cv2.imshow("TWO:", img)
        cv2.waitKey(1)


_thread.start_new_thread(display_one, ())
_thread.start_new_thread(display_two, ())
while 1:
    time.sleep(10)
