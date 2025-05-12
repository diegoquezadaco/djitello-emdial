from djitellopy import Tello
import time
import cv2
import numpy as np

# --- CONFIG ---
WIDTH, HEIGHT    = 650, 500
# once past this, we consider the object “at the right distance”
AREA_MIN         = 0.05 * (WIDTH * HEIGHT)
# once past this much smaller size, we can still center on it
MIN_DETECT_AREA  = 0.005 * (WIDTH * HEIGHT)
# target area for approaching/retreating
DESIRED_AREA     = AREA_MIN

THRESHOLD_X = int(0.15 * WIDTH)
THRESHOLD_Y = int(0.15 * HEIGHT)

# Proportional gains
Kp_yaw = 0.4     # deg/sec per px error
Kp_v   = 0.4     # cm/sec per px error
Kp_fb  = 0.004  # cm/sec per area error

MAX_YAW  = 100
MAX_V   = 100
MAX_FB  = 30

# HSV trackbar start values for green
H_MIN, H_MAX = 40, 82
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

# HSV tuning window
cv2.namedWindow('Trackbars')
cv2.resizeWindow('Trackbars', 600, 400)
for name, val, mx in [
    ('H Min', H_MIN, 179), ('H Max', H_MAX, 179),
    ('S Min', S_MIN, 255), ('S Max', S_MAX, 255),
    ('V Min', V_MIN, 255), ('V Max', V_MAX, 255),
]:
    cv2.createTrackbar(name, 'Trackbars', val, mx, nothing)

drone.takeoff()
flying = True

try:
    while True:
        frame = drone.get_frame_read().frame
        if frame is None:
            continue

        # resize & do original two-step conversion
        frame = cv2.resize(frame, (WIDTH, HEIGHT))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        hsv   = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        blurred = cv2.GaussianBlur(hsv, (15,15), 0)

        # read HSV limits
        h_min = cv2.getTrackbarPos('H Min','Trackbars')
        h_max = cv2.getTrackbarPos('H Max','Trackbars')
        s_min = cv2.getTrackbarPos('S Min','Trackbars')
        s_max = cv2.getTrackbarPos('S Max','Trackbars')
        v_min = cv2.getTrackbarPos('V Min','Trackbars')
        v_max = cv2.getTrackbarPos('V Max','Trackbars')
        lower = np.array([h_min, s_min, v_min])
        upper = np.array([h_max, s_max, v_max])

        # mask & clean
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
        lr_vel  = 0
        fb_vel  = 0
        ud_vel  = 0
        yaw_vel = 0

        # if we see something above the tiny threshold, do all axes
        if area > MIN_DETECT_AREA:
            x, y, w, h = cv2.boundingRect(c)
            cx, cy = x + w//2, y + h//2

            # draw box + center dot
            cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)
            cv2.circle(frame, (cx,cy), 5, (0,0,255), -1)

            # compute errors
            err_x    = cx - WIDTH//2
            err_y    = HEIGHT//2 - cy
            err_area = DESIRED_AREA - (w*h)

            # ---- YAW & VERTICAL (always) ---- #
            if abs(err_x) > THRESHOLD_X:
                yaw_vel = int(np.clip(Kp_yaw * err_x, -MAX_YAW, MAX_YAW))
            if abs(err_y) > THRESHOLD_Y:
                ud_vel = int(np.clip(Kp_v * err_y, -MAX_V, MAX_V))

            # ---- FORWARD/BACK (now unconditional for any detected blob) ---- #
            fb_vel = int(np.clip(Kp_fb * err_area, -MAX_FB, MAX_FB))

            # annotate
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

        # draw dead-zone & guides
        cv2.rectangle(frame,
                      (WIDTH//2-THRESHOLD_X, HEIGHT//2-THRESHOLD_Y),
                      (WIDTH//2+THRESHOLD_X, HEIGHT//2+THRESHOLD_Y),
                      (0,0,255), 2)
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

        # send commands
        drone.send_rc_control(lr_vel, fb_vel, ud_vel, yaw_vel)

        # display
        cv2.imshow('Tello', frame)
        cv2.imshow('Mask', mask)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('l') and flying:
            drone.land(); flying = False
        elif key == ord('t') and not flying and bat > 15:
            drone.takeoff(); flying = True

finally:
    if flying:
        drone.land()
    drone.streamoff()
    cv2.destroyAllWindows()