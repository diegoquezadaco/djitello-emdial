from djitellopy import Tello
import time
import cv2
import numpy as np

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

        if result.multi_hand_landmarks and result.multi_handedness:
            hand_landmarks = result.multi_hand_landmarks[0]
            handedness = result.multi_handedness[0]

            landmarks = hand_landmarks.landmark
            if landmarks[middle_tip].y < landmarks[middle_mcp].y and landmarks[ring_tip].y < landmarks[ring_mcp].y and landmarks[pinky_tip].y < landmarks[pinky_mcp].y and landmarks[thumb_tip].y < landmarks[thumb_mcp].y and landmarks[index_tip].y < landmarks[index_mcp].y:
                label = "Takeoff"
        
                if flying:
                    pass
                else:
                    if drone.get_battery() <= 15 and not flying:
                        pass
                    else:
                        drone.takeoff()
                        flying = True
            elif landmarks[middle_tip].y > landmarks[middle_mcp].y and landmarks[ring_tip].y > landmarks[ring_mcp].y and landmarks[pinky_tip].y > landmarks[pinky_mcp].y and landmarks[index_tip].y > landmarks[index_mcp].y:
                label = "Land"
                if flying:
                    drone.land()
                    flying = False
                else:
                    pass
            elif landmarks[pinky_tip].y < landmarks[pinky_mcp].y and landmarks[thumb_tip].x > landmarks[thumb_mcp].x and landmarks[index_tip].y > landmarks[index_mcp].y and landmarks[middle_tip].y > landmarks[middle_mcp].y and landmarks[ring_tip].y > landmarks[ring_mcp].y:
                label = "Up"
                if flying:
                    ud_vel = 30
                
            elif landmarks[pinky_tip].y > landmarks[pinky_mcp].y and landmarks[thumb_tip].y > landmarks[thumb_mcp].y and landmarks[index_tip].y > landmarks[wrist].y and landmarks[middle_tip].y > landmarks[wrist].y and landmarks[ring_tip].y > landmarks[wrist].y:
                label = "Down"
                if flying:
                    ud_vel = -30
                
            elif landmarks[thumb_tip].y < landmarks[thumb_mcp].y and landmarks[index_tip].y < landmarks[index_mcp].y and landmarks[thumb_tip].x < landmarks[pinky_mcp].x and landmarks[middle_tip].y > landmarks[middle_mcp].y and landmarks[ring_tip].y > landmarks[ring_mcp].y and landmarks[pinky_tip].y > landmarks[pinky_mcp].y:
                label = "Right"
                if flying:
                    lr_vel = 50
                
            elif landmarks[thumb_tip].y < landmarks[thumb_mcp].y and landmarks[index_tip].y < landmarks[index_mcp].y and landmarks[thumb_tip].x > landmarks[pinky_mcp].x and landmarks[middle_tip].y > landmarks[middle_mcp].y and landmarks[ring_tip].y > landmarks[ring_mcp].y and landmarks[pinky_tip].y > landmarks[pinky_mcp].y:
                label = "Left"
                if flying:
                    lr_vel = -50
                
            elif landmarks[thumb_tip].y < landmarks[thumb_mcp].y and landmarks[index_tip].y < landmarks[index_mcp].y and landmarks[thumb_tip].x < landmarks[pinky_mcp].x and landmarks[middle_tip].y > landmarks[middle_mcp].y and landmarks[ring_tip].y > landmarks[ring_mcp].y and landmarks[pinky_tip].y < landmarks[pinky_mcp].y:
                label = "Front"
                if flying:
                    fb_vel = 50
                
            elif landmarks[thumb_tip].y < landmarks[thumb_mcp].y and landmarks[index_tip].y < landmarks[index_mcp].y and landmarks[thumb_tip].x > landmarks[pinky_mcp].x and landmarks[middle_tip].y > landmarks[middle_mcp].y and landmarks[ring_tip].y > landmarks[ring_mcp].y and landmarks[pinky_tip].y < landmarks[pinky_mcp].y:
                label = "Back"
                if flying:
                    fb_vel = -50
                
            elif landmarks[thumb_tip].y < landmarks[thumb_ip].y and \
                    landmarks[thumb_ip].y < landmarks[thumb_mcp].y and \
                    landmarks[index_tip].x > landmarks[index_pip].x and \
                    landmarks[middle_tip].x > landmarks[middle_pip].x and \
                    landmarks[ring_tip].x > landmarks[ring_pip].x and \
                    landmarks[pinky_tip].x < landmarks[pinky_dip].x and \
                    landmarks[pinky_dip].x < landmarks[pinky_pip].x and \
                    landmarks[pinky_pip].x < landmarks[pinky_mcp].x:
                label = "Chill"
                if flying:
                    yaw_vel = 60
        
            elif landmarks[thumb_tip].y < landmarks[thumb_ip].y and \
                    landmarks[thumb_ip].y < landmarks[thumb_mcp].y and \
                    landmarks[index_tip].x < landmarks[index_pip].x and \
                    landmarks[middle_tip].x < landmarks[middle_pip].x and \
                    landmarks[ring_tip].x < landmarks[ring_pip].x and \
                    landmarks[pinky_tip].x > landmarks[pinky_dip].x and \
                    landmarks[pinky_dip].x > landmarks[pinky_pip].x and \
                    landmarks[pinky_pip].x > landmarks[pinky_mcp].x:
                label = "Chill Pal otro lado"
                if flying:
                    yaw_vel = -60
                
                #label = (f'Distance: {distance:.4} - Index pointing up')

                
            else:
                label = "Otro gesto"
                fb_vel = 0
                lr_vel = 0
                ud_vel = 0
                yaw_vel = 0
            
            print(f"Detected command: {label}")

        


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