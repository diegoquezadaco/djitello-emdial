from djitellopy import Tello  # DJI Tello SDK
import time                   # Time utilities
import cv2                    # OpenCV for vision processing
import numpy as np            # Numerical operations

# --- CONFIGURATION PARAMETERS ---
WIDTH, HEIGHT    = 650, 500                      # Frame dimensions (px)
# Minimum contour area to consider object "at distance"
AREA_MIN         = 0.05 * (WIDTH * HEIGHT)
# Absolute minimum area to detect and track
MIN_DETECT_AREA  = 0.005 * (WIDTH * HEIGHT)
# Desired target area for forward/backward control
DESIRED_AREA     = AREA_MIN

# Dead-zone thresholds (px) around center to ignore small errors
THRESHOLD_X = int(0.15 * WIDTH)
THRESHOLD_Y = int(0.15 * HEIGHT)

# Proportional control gains
Kp_yaw = 0.4     # Yaw gain: deg/sec per pixel error in X\Kp
Kp_v   = 0.4     # Vertical gain: cm/sec per pixel error in Y
Kp_fb  = 0.004   # Forward/back gain: cm/sec per area error

# Maximum velocities (absolute)
MAX_YAW  = 100   # Max yaw speed (deg/sec)
MAX_V    = 100   # Max vertical speed (cm/sec)
MAX_FB   = 30    # Max forward/back speed (cm/sec)

# Initial HSV trackbar values for green object
H_MIN, H_MAX = 40, 82
S_MIN, S_MAX = 55, 192
V_MIN, V_MAX = 30, 214


def nothing(x):
    """Dummy callback for trackbars."""
    pass

# --- DRONE SETUP ---
drone = Tello()
drone.connect()  # Establish connection
print(f"Battery: {drone.get_battery()}%")  # Report initial battery

drone.streamon()  # Turn on video stream
time.sleep(2)     # Allow camera to warm up

# Create HSV tuning UI
cv2.namedWindow('Trackbars')
cv2.resizeWindow('Trackbars', 600, 400)
for name, val, mx in [
    ('H Min', H_MIN, 179), ('H Max', H_MAX, 179),
    ('S Min', S_MIN, 255), ('S Max', S_MAX, 255),
    ('V Min', V_MIN, 255), ('V Max', V_MAX, 255),
]:
    cv2.createTrackbar(name, 'Trackbars', val, mx, nothing)

# Take off to begin flight
drone.takeoff()
flying = True                # Flag to track flight state
mode = False                 # False = automatic, True = manual control

try:
    while True:
        # Retrieve latest frame
        frame = drone.get_frame_read().frame
        if frame is None:
            continue

        # Preprocess frame: resize, color conversion, blur
        frame = cv2.resize(frame, (WIDTH, HEIGHT))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        hsv   = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        blurred = cv2.GaussianBlur(hsv, (15,15), 0)

        # Read current HSV thresholds from trackbars
        h_min = cv2.getTrackbarPos('H Min','Trackbars')
        h_max = cv2.getTrackbarPos('H Max','Trackbars')
        s_min = cv2.getTrackbarPos('S Min','Trackbars')
        s_max = cv2.getTrackbarPos('S Max','Trackbars')
        v_min = cv2.getTrackbarPos('V Min','Trackbars')
        v_max = cv2.getTrackbarPos('V Max','Trackbars')
        lower = np.array([h_min, s_min, v_min])
        upper = np.array([h_max, s_max, v_max])

        # Create mask for target color and clean up noise
        mask = cv2.inRange(blurred, lower, upper)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        # Find contours on mask and pick the largest
        contours, _ = cv2.findContours(mask,
                                       cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            c    = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(c)
        else:
            area = 0

        # Initialize velocity commands
        lr_vel  = 0  # left/right
        fb_vel  = 0  # forward/backward
        ud_vel  = 0  # up/down
        yaw_vel = 0  # rotation

        # If the detected area is big enough, compute control
        if area > MIN_DETECT_AREA:
            # Get bounding box and center
            x, y, w, h = cv2.boundingRect(c)
            cx, cy = x + w//2, y + h//2

            # Draw rectangle and center dot
            cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)
            cv2.circle(frame, (cx,cy), 5, (0,0,255), -1)

            # Compute errors relative to frame center and desired area
            err_x    = cx - WIDTH//2            # positive => object to the right
            err_y    = HEIGHT//2 - cy           # positive => object below center
            err_area = DESIRED_AREA - (w*h)     # positive => too small => move forward

            # YAW control: rotate to center X error
            if abs(err_x) > THRESHOLD_X:
                yaw_vel = int(np.clip(Kp_yaw * err_x, -MAX_YAW, MAX_YAW))
            # VERTICAL control: move up/down to center Y error
            if abs(err_y) > THRESHOLD_Y:
                ud_vel = int(np.clip(Kp_v * err_y, -MAX_V, MAX_V))

            # FORWARD/BACK control: adjust distance based on area error
            fb_vel = int(np.clip(Kp_fb * err_area, -MAX_FB, MAX_FB))

            # Display annotations for direction
            if yaw_vel < 0:
                cv2.putText(frame, 'Rotate →', (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2)
            elif yaw_vel > 0:
                cv2.putText(frame, 'Rotate ←', (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2)

            if ud_vel > 0:
                cv2.putText(frame, 'Up', (10,60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2)
            elif ud_vel < 0:
                cv2.putText(frame, 'Down', (10,60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2)

            if fb_vel > 0:
                cv2.putText(frame, 'Forward', (10,90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2)
            elif fb_vel < 0:
                cv2.putText(frame, 'Backward', (10,90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2)

        # Draw central dead-zone and guide lines
        cv2.rectangle(frame,
                      (WIDTH//2-THRESHOLD_X, HEIGHT//2-THRESHOLD_Y),
                      (WIDTH//2+THRESHOLD_X, HEIGHT//2+THRESHOLD_Y),
                      (0,0,255), 2)
        # Vertical guides
        cv2.line(frame,
                 (WIDTH//2-THRESHOLD_X, 0),
                 (WIDTH//2-THRESHOLD_X, HEIGHT), (255,0,0), 2)
        cv2.line(frame,
                 (WIDTH//2+THRESHOLD_X, 0),
                 (WIDTH//2+THRESHOLD_X, HEIGHT), (255,0,0), 2)
        # Horizontal guides
        cv2.line(frame,
                 (0, HEIGHT//2-THRESHOLD_Y),
                 (WIDTH, HEIGHT//2-THRESHOLD_Y), (255,0,0), 2)
        cv2.line(frame,
                 (0, HEIGHT//2+THRESHOLD_Y),
                 (WIDTH, HEIGHT//2+THRESHOLD_Y), (255,0,0), 2)

        # Display battery status on screen
        bat = drone.get_battery()
        cv2.putText(frame, f"Battery: {bat}%", (10, HEIGHT-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

        # Show the camera feed and mask windows
        cv2.imshow('Tello', frame)
        cv2.imshow('Mask', mask)

        # Handle key inputs
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            # Quit program
            break
        elif key == ord('l') and flying:
            # Land on 'l'
            drone.land(); flying = False
        elif key == ord('t') and not flying and bat > 15:
            # Take off on 't' if battery sufficient
            drone.takeoff(); flying = True
        elif key == ord('m'):
            # Toggle manual/auto mode
            mode = not mode
            status = "Manual" if mode else "Auto"
            cv2.putText(frame, f"{status} Control", (10,150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

        # MANUAL CONTROL overrides when enabled
        if flying and mode:
            if key == ord('w'):     fb_vel = 100  # forward
            elif key == ord('s'):   fb_vel = -100 # backward
            elif key == ord('a'):   lr_vel = -100 # left
            elif key == ord('d'):   lr_vel = 100  # right
            elif key == ord('r'):   # ascend, with height limit
                if drone.get_height() > 300:
                    cv2.putText(frame, "Height Exceeded", (10,120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
                else:
                    ud_vel = 60
            elif key == ord('f'):   ud_vel = -60  # descend
            elif key == ord('q'):   yaw_vel = 100 # rotate right
            elif key == ord('e'):   yaw_vel = -100# rotate left
            else:
                # no key -> hover
                fb_vel = lr_vel = ud_vel = yaw_vel = 0

        # Send computed control signals to drone
        drone.send_rc_control(lr_vel, fb_vel, ud_vel, yaw_vel)

finally:
    # Ensure safe landing and cleanup
    if flying:
        drone.land()
    drone.streamoff()
    cv2.destroyAllWindows()