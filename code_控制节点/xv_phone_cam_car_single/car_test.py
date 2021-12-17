import time

import cv2
import json
from socket import *
# import socket
import numpy as np
from tool.utils import load_class_names, plot_boxes_cv2
import _thread
import requests
cap = cv2.VideoCapture(0)
print(cap.isOpened())
while 1:
    _, img = cap.read()
    # print(img.shape)
    cv2.imshow('', img)
    cv2.waitKey(1)
cap.release()
cv2.destroyAllWindows()

