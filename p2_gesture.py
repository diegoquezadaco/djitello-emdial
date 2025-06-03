from djitellopy import Tello  # Librería para controlar el dron Tello
import cv2  # OpenCV para procesamiento de video
import time  # Para manejar tiempos de espera
import mediapipe as mp  # Para detección de manos

# Inicialización de MediaPipe Hands para detectar una sola mano con alta confianza
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)

global hand_landmarks  # Variable global para guardar los landmarks de la mano

cv2.namedWindow('Configuración de Vuelo')  # Ventana para configurar parámetros de vuelo

# Callback para actualizar la altura máxima desde el trackbar
def set_max_height(value):
    global max_height
    max_height = value

# Crear trackbars para ajustar las velocidades del dron en tiempo real
cv2.createTrackbar('Velocidad X', 'Configuración de Vuelo', 0, 100, lambda x: None)
cv2.createTrackbar('Velocidad Y', 'Configuración de Vuelo', 0, 100, lambda x: None)
cv2.createTrackbar('Velocidad Z', 'Configuración de Vuelo', 0, 100, lambda x: None)
cv2.createTrackbar('Velocidad Yaw', 'Configuración de Vuelo', 0, 100, lambda x: None)

# Trackbar para limitar la altura máxima del dron
cv2.createTrackbar('Altura Máxima', 'Configuración de Vuelo', 0, 500, set_max_height)

# Función para obtener los valores actuales de todos los trackbars
def get_trackbar_values():
    vx = cv2.getTrackbarPos('Velocidad X', 'Configuración de Vuelo')
    vy = cv2.getTrackbarPos('Velocidad Y', 'Configuración de Vuelo')
    vz = cv2.getTrackbarPos('Velocidad Z', 'Configuración de Vuelo')
    yaw = cv2.getTrackbarPos('Velocidad Yaw', 'Configuración de Vuelo')
    height = cv2.getTrackbarPos('Altura Máxima', 'Configuración de Vuelo')
    return vx, vy, vz, yaw, height

# Coordenadas
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
pinky_tip   = 20   # Punta del dedo meñique

# Conectar al dron
drone = Tello()
drone.connect()

#iniciar stream de video
drone.streamon()
time.sleep(3) # Espera para que el video se estabilice

global flying  # Indica si el dron está volando
global mode  # Indica el modo de control (manual o por gestos)

# Función para cerrar el programa de manera segura
def clean_exit():
    print("\nCerrando el programa...")
    if flying:
        drone.send_rc_control(0, 0, 0, 0)  # Detiene el movimiento
        time.sleep(1)
        drone.land()  # Aterriza el dron si está volando
    cv2.destroyAllWindows()  # Cierra todas las ventanas
    drone.streamoff()  # Apaga el stream
    drone.end()  # Finaliza la conexión
    print("Programa cerrado correctamente.")


# Función principal para controlar el dron
def control():
    flying = False
    mode = True  # Comienza en modo de gestos

    # Inicialización de velocidades
    fb_vel = 0
    lr_vel = 0
    ud_vel = 0
    yaw_vel = 0

    while True:
        frame = drone.get_frame_read().frame  # Obtiene el frame actual de la cámara
        if frame is None:
            print('No se recibio el cuadro')
            continue

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.flip(frame, 1)  # Efecto espejo
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Conversión para MediaPipe

        vx, vy, vz, yaw, max_height = get_trackbar_values()  # Lee valores de control
        result = hands.process(rgb)  # Procesa el frame para detectar manos
        label = "No se detecta mano"

        # Muestra estado del dron en pantalla
        cv2.putText(frame, "Battery: {}%".format(drone.get_battery()), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "Height: {}cm".format(drone.get_height()), (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        if flying:
            cv2.putText(frame, "Flying", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "Landed", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Advertencias por batería baja
        if drone.get_battery() <= 15 and not flying:
            cv2.putText(frame, "Bateria baja. No se puede despegar.", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        if drone.get_battery() <= 10 and flying:
            cv2.putText(frame, "Bateria crítica. Aterrizando automaticamente.", (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            drone.land()
            flying = False

        key = cv2.waitKey(50) & 0xFF  # Lee teclas presionadas

        # Salida segura
        if key == ord('p'):
            clean_exit()
            break

        # Tecla 't': despegue
        if key == ord('t'):
            if not flying and drone.get_battery() > 15:
                drone.takeoff()
                flying = True

        # Tecla 'l': aterrizaje
        if key == ord('l') and flying:
            drone.land()
            flying = False

        # Tecla 'm': cambiar de modo manual a gestos
        if key == ord('m'):
            mode = not mode

        # Modo manual (teclado)
        if flying and not mode:
            if key == ord('w'):
                fb_vel = vx
            elif key == ord('s'):
                fb_vel = -vx
            elif key == ord('a'):
                lr_vel = -vy
            elif key == ord('d'):
                lr_vel = vy
            elif key == ord('r'):
                if drone.get_height() > max_height:
                    cv2.putText(frame, "Height Exceeded", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    ud_vel = 0
                else:
                    ud_vel = vz
            elif key == ord('f'):
                ud_vel = -vz
            elif key == ord('q'):
                yaw_vel = yaw
            elif key == ord('e'):
                yaw_vel = -yaw
            else:
                fb_vel = lr_vel = ud_vel = yaw_vel = 0

            cv2.putText(frame, "Modo Manual", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Modo de control por gestos
        elif flying and mode:
            if result.multi_hand_landmarks and result.multi_handedness:
                hand_landmarks = result.multi_hand_landmarks[0]
                handedness = result.multi_handedness[0]
                landmarks = hand_landmarks.landmark

                # Cada gesto detectado se compara con la posición de los dedos
                # TAKEOFF
                if landmarks[middle_tip].y < landmarks[middle_mcp].y and \
                   landmarks[ring_tip].y < landmarks[ring_mcp].y and \
                   landmarks[pinky_tip].y < landmarks[pinky_mcp].y and \
                   landmarks[thumb_tip].y < landmarks[thumb_mcp].y and \
                   landmarks[index_tip].y < landmarks[index_mcp].y:
                    label = "Takeoff"
                    if not flying and drone.get_battery() > 15:
                        drone.takeoff()
                        flying = True

                # LAND
                elif landmarks[middle_tip].y < landmarks[middle_dip].y and \
                     landmarks[middle_dip].y < landmarks[middle_pip].y and \
                     landmarks[middle_pip].y < landmarks[middle_mcp].y and \
                     landmarks[index_tip].y < landmarks[index_dip].y and \
                     landmarks[index_dip].y < landmarks[index_pip].y and \
                     landmarks[index_pip].y < landmarks[index_mcp].y and \
                     landmarks[ring_tip].y > landmarks[ring_mcp].y and \
                     landmarks[pinky_tip].y > landmarks[pinky_mcp].y and \
                     landmarks[ring_tip].y > landmarks[ring_mcp].y and \
                     landmarks[ring_tip].y < landmarks[wrist].y:
                    label = "Land"
                    if flying:
                        drone.land()
                        flying = False

                # Comandos UP / DOWN / LEFT / RIGHT / FRONT / BACK / GIRO (Yaw)
                # Todos los dedos y la mando volteando hacia arriba
                elif landmarks[pinky_tip].y < landmarks[pinky_mcp].y and landmarks[thumb_tip].x > landmarks[thumb_mcp].x and landmarks[index_tip].y > landmarks[index_mcp].y and landmarks[middle_tip].y > landmarks[middle_mcp].y and landmarks[ring_tip].y > landmarks[ring_mcp].y:
                    label = "Up"
                    ud_vel = vz
                # Posicion de amor y paz
                elif landmarks[pinky_tip].y > landmarks[pinky_dip].y and \
                     landmarks[pinky_dip].y > landmarks[pinky_pip].y and \
                     landmarks[pinky_pip].y > landmarks[pinky_mcp].y and \
                     landmarks[thumb_tip].y > landmarks[thumb_mcp].y and \
                     landmarks[index_tip].y > landmarks[index_mcp].y and \
                     landmarks[index_pip].y > landmarks[index_tip].y and \
                     landmarks[middle_tip].y > landmarks[wrist].y and \
                     landmarks[ring_tip].y > landmarks[wrist].y:
                    label = "Down"
                    ud_vel = -vz
                # Letra L con la mano, de manera invertida, es decir con la mano derecha
                elif landmarks[thumb_tip].y < landmarks[thumb_mcp].y and landmarks[index_tip].y < landmarks[index_mcp].y and landmarks[thumb_tip].x < landmarks[pinky_mcp].x and landmarks[middle_tip].y > landmarks[middle_mcp].y and landmarks[ring_tip].y > landmarks[ring_mcp].y and landmarks[pinky_tip].y > landmarks[pinky_mcp].y:
                    label = "Right"
                    lr_vel = -vy
                # Letra L con la mano, de manera normal, es decir con la mano izquierda
                elif landmarks[thumb_tip].y < landmarks[thumb_mcp].y and landmarks[index_tip].y < landmarks[index_mcp].y and landmarks[thumb_tip].x > landmarks[pinky_mcp].x and landmarks[middle_tip].y > landmarks[middle_mcp].y and landmarks[ring_tip].y > landmarks[ring_mcp].y and landmarks[pinky_tip].y > landmarks[pinky_mcp].y:
                    label = "Left"
                    lr_vel = vy
                # Mano derecha en posicion de rock, con el pulgar, indice y menique hacia arriba
                elif landmarks[thumb_tip].y < landmarks[thumb_mcp].y and landmarks[index_tip].y < landmarks[index_mcp].y and landmarks[thumb_tip].x < landmarks[pinky_mcp].x and landmarks[middle_tip].y > landmarks[middle_mcp].y and landmarks[ring_tip].y > landmarks[ring_mcp].y and landmarks[pinky_tip].y < landmarks[pinky_mcp].y:
                    label = "Front"
                    fb_vel = vx
                # Mano izquierda en posicion de rock, con el pulgar, indice y menique hacia arriba
                elif landmarks[thumb_tip].y < landmarks[thumb_mcp].y and landmarks[index_tip].y < landmarks[index_mcp].y and landmarks[thumb_tip].x > landmarks[pinky_mcp].x and landmarks[middle_tip].y > landmarks[middle_mcp].y and landmarks[ring_tip].y > landmarks[ring_mcp].y and landmarks[pinky_tip].y < landmarks[pinky_mcp].y:
                    label = "Back"
                    fb_vel = -vx
                # Mano derecha en forma de telefono, con el pulgar y el meñique hacia arriba
                elif landmarks[thumb_tip].y < landmarks[thumb_ip].y and landmarks[thumb_ip].y < landmarks[thumb_mcp].y and landmarks[index_tip].x > landmarks[index_pip].x and landmarks[middle_tip].x > landmarks[middle_pip].x and landmarks[ring_tip].x > landmarks[ring_pip].x and landmarks[pinky_tip].x < landmarks[pinky_dip].x and landmarks[pinky_dip].x < landmarks[pinky_pip].x and landmarks[pinky_pip].x < landmarks[pinky_mcp].x:
                    label = "Chill"
                    yaw_vel = yaw
                # Mano izquierda en forma de telefono, con el pulgar y el meñique hacia arriba
                elif landmarks[thumb_tip].y < landmarks[thumb_ip].y and landmarks[thumb_ip].y < landmarks[thumb_mcp].y and landmarks[index_tip].x < landmarks[index_pip].x and landmarks[middle_tip].x < landmarks[middle_pip].x and landmarks[ring_tip].x < landmarks[ring_pip].x and landmarks[pinky_tip].x > landmarks[pinky_dip].x and landmarks[pinky_dip].x > landmarks[pinky_pip].x and landmarks[pinky_pip].x > landmarks[pinky_mcp].x:
                    label = "Chill Pal otro lado"
                    yaw_vel = -yaw
                else:
                    label = "Otro gesto"
                    fb_vel = lr_vel = ud_vel = yaw_vel = 0

                print(f"Detected command: {label}")
                cv2.putText(frame, "Modo Gestos", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.putText(frame, label, (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Evita que suba más allá de la altura máxima
            if drone.get_height() > max_height and ud_vel > 0:
                print("Altura máxima alcanzada. No se puede subir más.")
                ud_vel = 0
                drone.send_rc_control(0, 0, 0, 0)
                drone.land()

        # Envía los comandos de velocidad al dron
        drone.send_rc_control(lr_vel, fb_vel, ud_vel, yaw_vel)

        # Muestra el frame en pantalla
        cv2.imshow('Video Stream', frame)

# Función principal que ejecuta el control y captura interrupciones
def main():
    try:
        control()
    except KeyboardInterrupt:
        clean_exit()

# Punto de entrada
if __name__ == '__main__':
    main()