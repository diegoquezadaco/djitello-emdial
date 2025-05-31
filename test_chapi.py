import cv2
import mediapipe as mp
from djitellopy import Tello
import time

# ──────────────────────────────────────────────────────────────────────────────
# 1) SET UP MEDIAPIPE HANDS (no change here except that we will feed it
#    a square image to avoid the “NORM_RECT without IMAGE_DIMENSIONS” warning).
# ──────────────────────────────────────────────────────────────────────────────
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# We will pass only a square frame into .process(), so Mediapipe will not complain.
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# ──────────────────────────────────────────────────────────────────────────────
# 2) INDEXES FOR LANDMARKS (same as before)
# ──────────────────────────────────────────────────────────────────────────────
wrist       =  0

thumb_cmc   =  1
thumb_mcp   =  2
thumb_ip    =  3
thumb_tip   =  4

index_mcp   =  5
index_pip   =  6
index_dip   =  7
index_tip   =  8

middle_mcp  =  9
middle_pip  = 10
middle_dip  = 11
middle_tip  = 12

ring_mcp    = 13
ring_pip    = 14
ring_dip    = 15
ring_tip    = 16

pinky_mcp   = 17
pinky_pip   = 18
pinky_dip   = 19
pinky_tip   = 20

# ──────────────────────────────────────────────────────────────────────────────
# 3) CONNECT TO TELLO
# ──────────────────────────────────────────────────────────────────────────────
drone = Tello()
drone.connect()

# Turn on video streaming
drone.streamon()
time.sleep(2)

# ──────────────────────────────────────────────────────────────────────────────
# 4) GLOBAL FLAGS (we will mark them global inside control())
# ──────────────────────────────────────────────────────────────────────────────
flying = False   # Is the drone currently in flight?
mode = False     # False = auto (gesture) mode; True = manual mode
# (we will re‐use these inside control())

# ──────────────────────────────────────────────────────────────────────────────
# 5) CLEAN EXIT (unchanged)
# ──────────────────────────────────────────────────────────────────────────────
def clean_exit():
    global flying
    print("\n[+] Closing program...")
    if flying:
        drone.send_rc_control(0, 0, 0, 0)
        time.sleep(1)
        drone.land()
    cv2.destroyAllWindows()
    drone.streamoff()
    drone.end()
    print("[+] Program exited cleanly.")

# ──────────────────────────────────────────────────────────────────────────────
# 6) MAIN CONTROL LOOP
# ──────────────────────────────────────────────────────────────────────────────
def control():
    global flying, mode

    # All velocities start at zero
    fb_vel = 0
    lr_vel = 0
    ud_vel = 0
    yaw_vel = 0

    while True:
        # ──────────────────────────────────────────────────────────────────────────
        # 6a) READ FRAME FROM DRONE & MAKE IT SQUARE
        # ──────────────────────────────────────────────────────────────────────────
        frame_bgr = drone.get_frame_read().frame
        if frame_bgr is None:
            print("[!] No frame received. Retrying...")
            continue

        # Mirror image for “selfie” view
        frame_bgr = cv2.flip(frame_bgr, 1)

        # Get original dimensions
        orig_h, orig_w = frame_bgr.shape[:2]

        # We will resize (or pad) to a square. Let's pick the larger side:
        square_size = max(orig_w, orig_h)

        # Create a black square canvas
        square_canvas = cv2.copyMakeBorder(
            frame_bgr,
            top=0,
            bottom=square_size - orig_h,
            left=0,
            right=square_size - orig_w,
            borderType=cv2.BORDER_CONSTANT,
            value=[0, 0, 0]
        )

        # Now resize the square canvas to a fixed square resolution (e.g. 640×640).
        # You can choose any square resolution; 640×640 is common, but you could also do 480×480 etc.
        S = 640
        square_frame_bgr = cv2.resize(square_canvas, (S, S), interpolation=cv2.INTER_AREA)

        # Convert that square BGR frame to RGB for Mediapipe
        square_frame_rgb = cv2.cvtColor(square_frame_bgr, cv2.COLOR_BGR2RGB)

        # ──────────────────────────────────────────────────────────────────────────
        # 6b) RUN HANDS.PPROCESS
        # ──────────────────────────────────────────────────────────────────────────
        result = hands.process(square_frame_rgb)

        # ──────────────────────────────────────────────────────────────────────────
        # 6c) DISPLAY DRONE STATUS (battery, height, flying/landed)
        # ──────────────────────────────────────────────────────────────────────────
        # We will draw these on the *original* (mirrored) BGR frame, not on the square padded one,
        # because the user expects to see the actual camera output size.
        cv2.putText(
            frame_bgr,
            f"Battery: {drone.get_battery()}%",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )
        cv2.putText(
            frame_bgr,
            f"Height: {drone.get_height()}cm",
            (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )
        if flying:
            cv2.putText(frame_bgr, "Flying", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            cv2.putText(frame_bgr, "Landed", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # If battery is low (<15%) and not flying, show warning
        if drone.get_battery() <= 15 and not flying:
            cv2.putText(
                frame_bgr,
                "LOW BATTERY: cannot take off",
                (10, 150),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )

        # If battery is very low while flying, force auto‐land
        if drone.get_battery() <= 10 and flying:
            cv2.putText(
                frame_bgr,
                "CRITICAL BATTERY: landing...",
                (10, 190),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )
            drone.land()
            flying = False

        # ──────────────────────────────────────────────────────────────────────────
        # 6d) IF A HAND IS DETECTED, EXTRACT LANDMARKS AND INTERPRET GESTURES
        # ──────────────────────────────────────────────────────────────────────────
        label = "No hand"
        if result.multi_hand_landmarks:
            print('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
            hand_landmarks = result.multi_hand_landmarks[0]
            landmarks = hand_landmarks.landmark

            # Check “all fingers up = TAKEOFF” gesture:
            if (
                landmarks[middle_tip].y < landmarks[middle_mcp].y and
                landmarks[ring_tip].y   < landmarks[ring_mcp].y   and
                landmarks[pinky_tip].y  < landmarks[pinky_mcp].y  and
                landmarks[thumb_tip].y  < landmarks[thumb_mcp].y  and
                landmarks[index_tip].y  < landmarks[index_mcp].y
            ):
                label = "TAKEOFF"

                if not flying and drone.get_battery() > 15:
                    drone.takeoff()
                    flying = True

            # Check “all fingers down = LAND” gesture:
            elif (
                landmarks[middle_tip].y > landmarks[middle_mcp].y and
                landmarks[ring_tip].y   > landmarks[ring_mcp].y   and
                landmarks[pinky_tip].y  > landmarks[pinky_mcp].y  and
                landmarks[index_tip].y  > landmarks[index_mcp].y
            ):
                label = "LAND"
                if flying:
                    drone.land()
                    flying = False

            # Check “pinky up, thumb right, rest down = UP” gesture:
            elif (
                landmarks[pinky_tip].y  < landmarks[pinky_mcp].y  and
                landmarks[thumb_tip].x  > landmarks[thumb_mcp].x  and
                landmarks[index_tip].y  > landmarks[index_mcp].y  and
                landmarks[middle_tip].y > landmarks[middle_mcp].y and
                landmarks[ring_tip].y   > landmarks[ring_mcp].y
            ):
                label = "UP"
                if flying:
                    ud_vel = 30

            # Check “pinky down, thumb down, rest above wrist = DOWN” gesture:
            elif (
                landmarks[pinky_tip].y  > landmarks[pinky_mcp].y and
                landmarks[thumb_tip].y  > landmarks[thumb_mcp].y and
                landmarks[index_tip].y  > landmarks[wrist].y   and
                landmarks[middle_tip].y > landmarks[wrist].y   and
                landmarks[ring_tip].y   > landmarks[wrist].y
            ):
                label = "DOWN"
                if flying:
                    ud_vel = -30

            # Check “thumb right, index+middle up, ring+pinky down = RIGHT” gesture:
            elif (
                landmarks[thumb_tip].y    < landmarks[thumb_mcp].y and
                landmarks[index_tip].y    < landmarks[index_mcp].y and
                landmarks[thumb_tip].x    < landmarks[pinky_mcp].x and
                landmarks[middle_tip].y   > landmarks[middle_mcp].y and
                landmarks[ring_tip].y     > landmarks[ring_mcp].y and
                landmarks[pinky_tip].y    > landmarks[pinky_mcp].y
            ):
                label = "RIGHT"
                if flying:
                    lr_vel = 50

            # Check “thumb left, index+middle up, ring+pinky down = LEFT” gesture:
            elif (
                landmarks[thumb_tip].y    < landmarks[thumb_mcp].y and
                landmarks[index_tip].y    < landmarks[index_mcp].y and
                landmarks[thumb_tip].x    > landmarks[pinky_mcp].x and
                landmarks[middle_tip].y   > landmarks[middle_mcp].y and
                landmarks[ring_tip].y     > landmarks[ring_mcp].y and
                landmarks[pinky_tip].y    > landmarks[pinky_mcp].y
            ):
                label = "LEFT"
                if flying:
                    lr_vel = -50

            # Check “front = thumb right & pinky up & rest down”
            elif (
                landmarks[thumb_tip].y    < landmarks[thumb_mcp].y    and
                landmarks[index_tip].y    < landmarks[index_mcp].y    and
                landmarks[thumb_tip].x    < landmarks[pinky_mcp].x and
                landmarks[middle_tip].y   > landmarks[middle_mcp].y and
                landmarks[ring_tip].y     > landmarks[ring_mcp].y and
                landmarks[pinky_tip].y    < landmarks[pinky_mcp].y
            ):
                label = "FRONT"
                if flying:
                    fb_vel = 50

            # Check “back = thumb right & pinky down & rest down”
            elif (
                landmarks[thumb_tip].y    < landmarks[thumb_mcp].y and
                landmarks[index_tip].y    < landmarks[index_mcp].y and
                landmarks[thumb_tip].x    > landmarks[pinky_mcp].x and
                landmarks[middle_tip].y   > landmarks[middle_mcp].y and
                landmarks[ring_tip].y     > landmarks[ring_mcp].y and
                landmarks[pinky_tip].y    < landmarks[pinky_mcp].y
            ):
                label = "BACK"
                if flying:
                    fb_vel = -50

            # Check “rotate clockwise (‘Chill’) = thumb up & index+middle+ring right & pinky left”
            elif (
                landmarks[thumb_tip].y    < landmarks[thumb_ip].y    and
                landmarks[thumb_ip].y     < landmarks[thumb_mcp].y   and
                landmarks[index_tip].x    > landmarks[index_pip].x   and
                landmarks[middle_tip].x   > landmarks[middle_pip].x  and
                landmarks[ring_tip].x     > landmarks[ring_pip].x    and
                landmarks[pinky_tip].x    < landmarks[pinky_dip].x   and
                landmarks[pinky_dip].x    < landmarks[pinky_pip].x   and
                landmarks[pinky_pip].x    < landmarks[pinky_mcp].x
            ):
                label = "ROTATE CW"
                if flying:
                    yaw_vel = 60

            # Check “rotate counterclockwise = mirror of above”
            elif (
                landmarks[thumb_tip].y    < landmarks[thumb_ip].y    and
                landmarks[thumb_ip].y     < landmarks[thumb_mcp].y   and
                landmarks[index_tip].x    < landmarks[index_pip].x   and
                landmarks[middle_tip].x   < landmarks[middle_pip].x  and
                landmarks[ring_tip].x     < landmarks[ring_pip].x    and
                landmarks[pinky_tip].x    > landmarks[pinky_dip].x   and
                landmarks[pinky_dip].x    > landmarks[pinky_pip].x   and
                landmarks[pinky_pip].x    > landmarks[pinky_mcp].x
            ):
                label = "ROTATE CCW"
                if flying:
                    yaw_vel = -60

            else:
                # No known gesture → hover in place
                label = "OTHER"
                fb_vel = 0
                lr_vel = 0
                ud_vel = 0
                yaw_vel = 0

        print(f"[Gesture detected] {label}")

        # ──────────────────────────────────────────────────────────────────────────
        # 6e) IF WE’VE REACHED MAX HEIGHT, FORBID UPWARD VELOCITY
        # ──────────────────────────────────────────────────────────────────────────
        if drone.get_height() > 300 and ud_vel > 0:
            print("[!] Max height reached. No further UP.")
            ud_vel = 0

        # ──────────────────────────────────────────────────────────────────────────
        # 6f) SHOW THE LIVE CAMERA FEED (BGR). We overlay label on the original frame.
        # ──────────────────────────────────────────────────────────────────────────
        cv2.putText(
            frame_bgr,
            f"Gesture: {label}",
            (10, orig_h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )
        cv2.imshow("Tello Video Stream", frame_bgr)

        # ──────────────────────────────────────────────────────────────────────────
        # 6g) KEYBOARD CONTROLS
        # ──────────────────────────────────────────────────────────────────────────
        key = cv2.waitKey(1) & 0xFF

        if key == ord('v'):
            # Quit immediately
            break

        elif key == ord('l') and flying:
            # Manual LAND
            drone.land()
            flying = False

        elif key == ord('t') and not flying and drone.get_battery() > 15:
            # Manual TAKEOFF
            drone.takeoff()
            flying = True

        elif key == ord('m'):
            # Toggle manual vs. auto (gesture) mode
            mode = not mode
            if mode:
                print("[Mode] MANUAL control (keys).")
                cv2.putText(
                    frame_bgr,
                    "Mode: MANUAL",
                    (10, orig_h - 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 255),
                    2
                )
            else:
                print("[Mode] AUTO (gesture) control.")
                cv2.putText(
                    frame_bgr,
                    "Mode: AUTO (Gestures)",
                    (10, orig_h - 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 255),
                    2
                )

        # ──────────────────────────────────────────────────────────────────────────
        # 6h) IF IN MANUAL MODE, OVERWRITE VELOCITIES BASED ON W/A/S/D/Q/E/R/F
        # ──────────────────────────────────────────────────────────────────────────
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
                # UP, but check max‐height
                if drone.get_height() > 300:
                    print("[!] Height exceeded. Cannot go up.")
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
                # No key pressed → hover
                fb_vel = 0
                lr_vel = 0
                ud_vel = 0
                yaw_vel = 0

        # ──────────────────────────────────────────────────────────────────────────
        # 6i) FINALLY, SEND RC CONTROL TO TELL0
        # ──────────────────────────────────────────────────────────────────────────
        drone.send_rc_control(lr_vel, fb_vel, ud_vel, yaw_vel)

    # End of while True
    clean_exit()

# ──────────────────────────────────────────────────────────────────────────────
# 7) RUN
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        control()
    except KeyboardInterrupt:
        clean_exit()