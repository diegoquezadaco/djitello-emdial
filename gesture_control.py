import cv2
import mediapipe as mp
from djitellopy import Tello
import time

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)

# Coordenadas de los puntos de referencia de la mano
wrist = 0
thumb_mcp = 2
thumb_tip = 4
index_base = 5
index_tip = 8
middle_tip = 12
middle_mcp = 19
ring_tip = 16
ring_mcp = 13
pinky_tip = 20
pinky_mcp = 17

# Conectar al dron
drone = Tello()
drone.connect()

#iniciar stream de video
drone.streamon()
time.sleep(3)

global flying

def clean_exit():
    
    print("\nCerrando el programa...")
    if flying:
        drone.send_rc_control(0, 0, 0, 0)
        time.sleep(1)
        drone.land()
    cv2.destroyAllWindows()
    drone.streamoff()
    drone.end()
    print("Programa cerrado correctamente.")

def control():
    
    flying = False

    fb_vel = 0
    lr_vel = 0
    ud_vel = 0
    yaw_vel = 0


    while True:
        
        frame = drone.get_frame_read().frame
        if frame is None:
            print('No se recibio el cuadro')
            continue

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Flip para espejo
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        result = hands.process(rgb)
        label = "No se detecta mano"
        cv2.putText(frame, "Battery: {}%".format(drone.get_battery()), 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "Height: {}cm".format(drone.get_height()), 
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        if flying:
            cv2.putText(frame, "Flying", (10, 90), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "Landed", (10, 90), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
        if drone.get_battery() <= 15 and not flying:
            cv2.putText(frame, "Bateria baja. No se puede despegar.", (10, 150), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            
        if drone.get_battery() <= 10 and flying:
            cv2.putText(frame, "Bateria crítica. Aterrizando automaticamente.", (10, 180), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            #drone.land()
            #flying = False
            
        
        cv2.imshow('Video Stream', frame)
        if result.multi_hand_landmarks and result.multi_handedness:
            hand_landmarks = result.multi_hand_landmarks[0]
            handedness = result.multi_handedness[0]

            landmarks = hand_landmarks.landmark
            if landmarks[middle_tip].y < landmarks[middle_mcp].y and landmarks[ring_tip].y < landmarks[ring_mcp].y and landmarks[pinky_tip].y < landmarks[pinky_mcp].y and landmarks[thumb_tip].y < landmarks[thumb_mcp].y and landmarks[index_tip].y < landmarks[index_base].y:
                label = "Takeoff"
        
                if flying:
                    pass
                else:
                    if drone.get_battery() <= 15 and not flying:
                        pass
                    else:
                        drone.takeoff()
                        flying = True
            elif landmarks[middle_tip].y > landmarks[middle_mcp].y and landmarks[ring_tip].y > landmarks[ring_mcp].y and landmarks[pinky_tip].y > landmarks[pinky_mcp].y and landmarks[index_tip].y > landmarks[index_base].y:
                label = "Land"
                cmd = 1
                if flying:
                    drone.land()
                    flying = False
                else:
                    pass
            elif landmarks[pinky_tip].y < landmarks[pinky_mcp].y and landmarks[thumb_tip].x > landmarks[thumb_mcp].x and landmarks[index_tip].y > landmarks[index_base].y and landmarks[middle_tip].y > landmarks[middle_mcp].y and landmarks[ring_tip].y > landmarks[ring_mcp].y:
                label = "Up"
                cmd = 2
            elif landmarks[pinky_tip].y > landmarks[pinky_mcp].y and landmarks[thumb_tip].y > landmarks[thumb_mcp].y and landmarks[index_tip].y > landmarks[wrist].y and landmarks[middle_tip].y > landmarks[wrist].y and landmarks[ring_tip].y > landmarks[wrist].y:
                label = "Down"
                cmd = 3
            elif landmarks[thumb_tip].y < landmarks[thumb_mcp].y and landmarks[index_tip].y < landmarks[index_base].y and landmarks[thumb_tip].x < landmarks[pinky_mcp].x and landmarks[middle_tip].y > landmarks[middle_mcp].y and landmarks[ring_tip].y > landmarks[ring_mcp].y and landmarks[pinky_tip].y > landmarks[pinky_mcp].y:
                label = "Right"
                cmd = 4
            elif landmarks[thumb_tip].y < landmarks[thumb_mcp].y and landmarks[index_tip].y < landmarks[index_base].y and landmarks[thumb_tip].x > landmarks[pinky_mcp].x and landmarks[middle_tip].y > landmarks[middle_mcp].y and landmarks[ring_tip].y > landmarks[ring_mcp].y and landmarks[pinky_tip].y > landmarks[pinky_mcp].y:
                label = "Left"
                cmd = 5
            elif landmarks[thumb_tip].y < landmarks[thumb_mcp].y and landmarks[index_tip].y < landmarks[index_base].y and landmarks[thumb_tip].x < landmarks[pinky_mcp].x and landmarks[middle_tip].y > landmarks[middle_mcp].y and landmarks[ring_tip].y > landmarks[ring_mcp].y and landmarks[pinky_tip].y < landmarks[pinky_mcp].y:
                label = "Front"
                cmd = 6
            elif landmarks[thumb_tip].y < landmarks[thumb_mcp].y and landmarks[index_tip].y < landmarks[index_base].y and landmarks[thumb_tip].x > landmarks[pinky_mcp].x and landmarks[middle_tip].y > landmarks[middle_mcp].y and landmarks[ring_tip].y > landmarks[ring_mcp].y and landmarks[pinky_tip].y < landmarks[pinky_mcp].y:
                label = "Back"
                cmd = 7
            print(f"Detected command: {label}")

        

        '''if drone.get_height() > 300 and ud_vel > 0:
            print("Altura máxima alcanzada. No se puede subir más.")
            ud_vel = 0
            drone.send_rc_control(0, 0, 0, 0)
            drone.land()'''

        if key == ord('p'):
            clean_exit()
            break


        


        if key == ord('t'):
            if flying:
                pass
            else:
                if drone.get_battery() <= 15 and not flying:
                    pass
                else:
                    drone.takeoff()
                    flying = True
        
        if key == ord('l'):
            if flying:
                drone.land()
                flying = False
            else:
                pass
        
        if flying:
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




def main():
    try:
        control()
    except KeyboardInterrupt:
        clean_exit()

if __name__ == '__main__':
    main()