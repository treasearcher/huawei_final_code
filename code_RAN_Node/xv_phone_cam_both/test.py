import numpy as np
import queue
a=queue.Queue(3)
b=queue.Queue(3)
c=np.zeros(1)
print(c)
# print(a.get())
a.put(c)
b.put(c)
print(a.get())
# print(a.get())
print(b.get())
# print(a.get())

import cv2
cv2.imshow('1', np.zeros((480,640)))
cv2.waitKey(0)
cv2.imshow('1', np.ones((480,640)))
cv2.waitKey(0)
