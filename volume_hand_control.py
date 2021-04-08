import cv2
import time
import numpy as np
import hand_tracking_module as htm
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

cam_width, cam_height = 640, 480

cap = cv2.VideoCapture('http://192.168.0.3:8080/videofeed')
cap.set(3, cam_width)
cap.set(4, cam_height)
past_time = 0

detector = htm.HandDetector(detection_confidence=0.86)

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
# volume.GetMute()
# volume.GetMasterVolumeLevel()
volRange = volume.GetVolumeRange()
# print(volRange)

minVol = volRange[0]
maxVol = volRange[1]
volBar = 400
vol = volume.GetMasterVolumeLevel()
vol_percents = 0
last_detect_time = 0
ui_color = (120, 120, 255)
while True:
    success, img = cap.read()
    img = detector.find_hands(img)
    lmList = detector.find_position(img, draw=False)
    if len(lmList) != 0:

        x1, y1 = lmList[4][1], lmList[4][2]
        x2, y2 = lmList[8][1], lmList[8][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
        cv2.circle(img, (x2, y2), 15, (255, 0, 255), cv2.FILLED)
        cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
        cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)

        length = math.hypot(x2 - x1, y2 - y1)
        # print(length)
        # hand range 50 - 300
        # Volume Range -64 - 0

        vol_percents = (length - 50) / 2.5
        if vol_percents > 100:
            vol_percents = 100
            vol = 0.0
        elif vol_percents < 0:
            vol_percents = 0.4
            vol = -64.0
        # vol = np.interp(length, [50, 300], [minVol, maxVol])
        else:
            vol = -64.2537 + 13.8217 * math.log(vol_percents)
            if vol > 0:
                vol = 0
            elif vol < -64:
                vol = -64

        volBar = np.interp(vol_percents, [0, 100], [400, 150])
        # print(volPer, vol, volBar)
        # volPer = np.interp(length, [50, 300], [0, 100])
        # print(int(length), vol)
        volume.SetMasterVolumeLevel(vol, None)

        if length < 50:
            cv2.circle(img, (cx, cy), 15, (0, 255, 0), cv2.FILLED)

        cv2.rectangle(img, (50, 150), (85, 400), ui_color, 3)
        cv2.rectangle(img, (50, int(volBar)), (85, 400), ui_color, cv2.FILLED)
        cv2.putText(img, f'{int(vol_percents)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX, 1, ui_color, 3)

        last_detect_time = time.time()

    else:
        if time.time() - last_detect_time < 2:
            cv2.rectangle(img, (50, 150), (85, 400), ui_color, 3)
            cv2.rectangle(img, (50, int(volBar)), (85, 400), ui_color, cv2.FILLED)
            cv2.putText(img, f'{int(vol_percents)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX, 1, ui_color, 3)

    current_time = time.time()
    fps = 1 / (current_time - past_time)
    past_time = current_time

    cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)

    cv2.imshow("Img", img)
    cv2.waitKey(1)
