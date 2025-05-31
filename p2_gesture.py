from djitellopy import Tello
import time
import cv2
import numpy as np
import mediapipe as mp


mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)

wrist       =  0   # Muñeca

thumb_cmc   =  1   # Articulación base del pulgar (carpometacarpiana)
thumb_mcp   =  2   # Articulación metacarpofalángica del pulgar
thumb_ip    =  3   # Articulación interfalángica del pulgar
thumb_tip   =  4   # Punta del pulgar

index_mcp   =  5   # Nudillo del dedo índice
index_pip   =  6   # Primera articulación del dedo índice
index_dip   =  7   # Segunda articulación del dedo índice
index_tip   =  8   # Punta del dedo índice

middle_mcp  =  9   # Nudillo del dedo medio
middle_pip  = 10   # Primera articulación del dedo medio
middle_dip  = 11   # Segunda articulación del dedo medio
middle_tip  = 12   # Punta del dedo medio

ring_mcp    = 13   # Nudillo del dedo anular
ring_pip    = 14   # Primera articulación del dedo anular
ring_dip    = 15   # Segunda articulación del dedo anular
ring_tip    = 16   # Punta del dedo anular

pinky_mcp   = 17   # Nudillo del dedo meñique
pinky_pip   = 18   # Primera articulación del dedo meñique
pinky_dip   = 19   # Segunda articulación del dedo meñique
pinky_tip   = 20 

# --- CONFIG ---
WIDTH, HEIGHT = 650, 500
AREA_MIN     = 0.005 * (WIDTH * HEIGHT)  # minimum area to consider “in frame”
DESIRED_AREA = AREA_MIN                 # target area

THRESHOLD_X  = int(0.15 * WIDTH)        # dead-zone half-width
THRESHOLD_Y  = int(0.15 * HEIGHT)       # dead-zone half-height

# Proportional gains for yaw (deg/s), vertical (cm/s), forward/back (cm/s)
Kp_yaw = 0.4
Kp_v   = 0.4
Kp_fb  = 0.0002

MAX_YAW = 100
MAX_V   = 100
MAX_FB  = 100

# HSV trackbar initial values for green
H_MIN, H_MAX = 40, 110
S_MIN, S_MAX = 55, 192
V_MIN, V_MAX = 30, 214

def nothing(x):
    pass

# --- SETUP ---
drone = Tello()
drone.connect()
print(f"Battery: {drone.get_battery()}%")
drone.streamon()
time.sleep(2)

# Trackbars for HSV tuning
cv2.namedWindow('Trackbars')
cv2.resizeWindow('Trackbars', 600, 400)
cv2.createTrackbar('H Min','Trackbars',H_MIN,179,nothing)
cv2.createTrackbar('H Max','Trackbars',H_MAX,179,nothing)
cv2.createTrackbar('S Min','Trackbars',S_MIN,255,nothing)
cv2.createTrackbar('S Max','Trackbars',S_MAX,255,nothing)
cv2.createTrackbar('V Min','Trackbars',V_MIN,255,nothing)
cv2.createTrackbar('V Max','Trackbars',V_MAX,255,nothing)

drone.takeoff()
flying = True
mode = False  # manual control mode, true is manual mode.

try:
    while True:
        frame = drone.get_frame_read().frame
        if frame is None:
            continue

        # resize and do the original two-step conversion (BGR→RGB, then BGR→HSV)
        frame = cv2.resize(frame, (WIDTH, HEIGHT))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        hsv   = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        blurred = cv2.GaussianBlur(hsv, (15,15), 0)

        # read trackbar positions
        h_min = cv2.getTrackbarPos('H Min','Trackbars')
        h_max = cv2.getTrackbarPos('H Max','Trackbars')
        s_min = cv2.getTrackbarPos('S Min','Trackbars')
        s_max = cv2.getTrackbarPos('S Max','Trackbars')
        v_min = cv2.getTrackbarPos('V Min','Trackbars')
        v_max = cv2.getTrackbarPos('V Max','Trackbars')
        lower = np.array([h_min, s_min, v_min])
        upper = np.array([h_max, s_max, v_max])

        # mask and morphological clean-up
        mask = cv2.inRange(blurred, lower, upper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        # find largest contour
        contours, _ = cv2.findContours(mask,
                                       cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            c    = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(c)
        else:
            area = 0

        # default velocities
        lr_vel  = 0   # left/right unused
        fb_vel  = 0   # forward/back
        ud_vel  = 0   # up/down
        yaw_vel = 0   # rotation

        if area > AREA_MIN:
            x, y, w, h = cv2.boundingRect(c)
            cx, cy = x + w//2, y + h//2

            # draw bounding box + center dot
            cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)
            cv2.circle(frame, (cx,cy), 5, (0,0,255), -1)

            # compute errors
            err_x    = cx - WIDTH//2
            err_y    = HEIGHT//2 - cy
            err_area = DESIRED_AREA - (w*h)

            # YAW: flipped sign so +err_x → rotate right
            if abs(err_x) > THRESHOLD_X:
                yaw_vel = int(np.clip( Kp_yaw * err_x, -MAX_YAW, MAX_YAW))
            # VERTICAL
            if abs(err_y) > THRESHOLD_Y:
                ud_vel = int(np.clip( Kp_v  * err_y, -MAX_V,   MAX_V  ))
            # FORWARD/BACK
            fb_vel = int(np.clip( Kp_fb * err_area, -MAX_FB, MAX_FB))

            # annotate on frame
            if yaw_vel < 0:
                cv2.putText(frame, 'Rotate →', (10,30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2)
            elif yaw_vel > 0:
                cv2.putText(frame, 'Rotate ←', (10,30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2)

            if ud_vel > 0:
                cv2.putText(frame, 'Up', (10,60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2)
            elif ud_vel < 0:
                cv2.putText(frame, 'Down', (10,60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2)

            if fb_vel > 0:
                cv2.putText(frame, 'Forward', (10,90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2)
            elif fb_vel < 0:
                cv2.putText(frame, 'Backward', (10,90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2)

        # draw dead-zone rectangle
        cv2.rectangle(frame,
                      (WIDTH//2-THRESHOLD_X, HEIGHT//2-THRESHOLD_Y),
                      (WIDTH//2+THRESHOLD_X, HEIGHT//2+THRESHOLD_Y),
                      (0,0,255), 2)

        # guide lines
        cv2.line(frame,
                 (WIDTH//2-THRESHOLD_X, 0),
                 (WIDTH//2-THRESHOLD_X, HEIGHT),
                 (255,0,0), 2)
        cv2.line(frame,
                 (WIDTH//2+THRESHOLD_X, 0),
                 (WIDTH//2+THRESHOLD_X, HEIGHT),
                 (255,0,0), 2)
        cv2.line(frame,
                 (0, HEIGHT//2-THRESHOLD_Y),
                 (WIDTH, HEIGHT//2-THRESHOLD_Y),
                 (255,0,0), 2)
        cv2.line(frame,
                 (0, HEIGHT//2+THRESHOLD_Y),
                 (WIDTH, HEIGHT//2+THRESHOLD_Y),
                 (255,0,0), 2)

        # battery status
        bat = drone.get_battery()
        cv2.putText(frame, f"Battery: {bat}%", (10, HEIGHT-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)


        # display windows
        cv2.imshow('Tello', frame)
        cv2.imshow('Mask', mask)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('l') and flying:
            drone.land()
            flying = False
        elif key == ord('t') and not flying and bat > 15:
            drone.takeoff()
            flying = True
        elif key == ord('m'):
            mode = not mode
            if mode:
                cv2.putText(frame, "Manual Control", (10, 150), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            else:
                cv2.putText(frame, "Auto Control", (10, 150), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # manual control
        if flying and mode:
            if key == ord('w'):
                fb_vel = 100
            elif key == ord('s'):
                fb_vel = -100
            elif key == ord('a'):
                lr_vel = -100
            elif key == ord('d'):
                lr_vel = 100
            elif key == ord('r'):
                if drone.get_height() > 300:
                    cv2.putText(frame, "Height Exceeded", (10, 120), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    ud_vel = 0
                else:
                    ud_vel = 60
            elif key == ord('f'):
                ud_vel = -60
            elif key == ord('q'):
                yaw_vel = 100
            elif key == ord('e'):
                yaw_vel = -100
            else:
                fb_vel = 0
                lr_vel = 0
                ud_vel = 0
                yaw_vel = 0
            
        drone.send_rc_control(lr_vel, fb_vel, ud_vel, yaw_vel)

finally:
    if flying:
        drone.land()
    drone.streamoff()
    cv2.destroyAllWindows()