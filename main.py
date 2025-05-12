from djitellopy import Tello
import cv2
import time

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
            drone.land()
            flying = False
            
        
        cv2.imshow('Video Stream', frame)
        key = cv2.waitKey(50) & 0xFF
        

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