from djitellopy import Tello
import time
import cv2
# pip install opencv-python
import numpy as np
# pip install numpy
width = 650
height = 500    
area_min = 0.05 * (width * height)  # Área mínima para detectar objetos
threshold_x = int(0.15 *width)
threshold_y = int(0.15 *height)

#Conectar al dron
drone = Tello()
drone.connect()

#iniciar stream de video
drone.streamon()
time.sleep(3)

def callback(x):
    pass

# Inicia la captura de la webcam
cap = cv2.VideoCapture(0)

# Crea una ventana para las trackbars
cv2.namedWindow('Trackbars')
# Define un tamaño personalizado para la ventana de trackbars
cv2.resizeWindow('Trackbars', 600, 400)  # Ancho = 600 píxeles, Alto = 400 píxeles

# Crea trackbars para ajustar los valores H, S, V
cv2.createTrackbar('H Min', 'Trackbars', 40, 179, callback)
cv2.createTrackbar('H Max', 'Trackbars', 110, 179, callback)
cv2.createTrackbar('S Min', 'Trackbars', 55, 255, callback)
cv2.createTrackbar('S Max', 'Trackbars', 192, 255, callback)
cv2.createTrackbar('V Min', 'Trackbars', 30, 255, callback)
cv2.createTrackbar('V Max', 'Trackbars', 214, 255, callback)

drone.takeoff()
flyings = True

while True:
    # Lee la imagen de la webcam
    # ret, frame = cap.read()

    # if not ret:
    #     break

    frame = drone.get_frame_read().frame
    if frame is None:
        print('No se recibio el cuadro')
        continue

    frame = cv2.resize(frame, (width, height))  # Redimensiona la imagen
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Convierte la imagen de BGR a HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Obtiene los valores de las trackbars
    h_min = cv2.getTrackbarPos('H Min', 'Trackbars')
    s_min = cv2.getTrackbarPos('S Min', 'Trackbars')
    v_min = cv2.getTrackbarPos('V Min', 'Trackbars')
    h_max = cv2.getTrackbarPos('H Max', 'Trackbars')
    s_max = cv2.getTrackbarPos('S Max', 'Trackbars')
    v_max = cv2.getTrackbarPos('V Max', 'Trackbars')

    # Define los límites del filtro HSV
    lower_hsv = np.array([h_min, s_min, v_min])
    upper_hsv = np.array([h_max, s_max, v_max])

    # Aplica desenfoque gaussiano para reducir el ruido
    blurred = cv2.GaussianBlur(hsv, (15, 15), 0)

    # Aplica el filtro de color en la imagen desenfocada
    mask = cv2.inRange(blurred, lower_hsv, upper_hsv)

    # Erosión y dilatación para eliminar ruido en la máscara
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    # Aplica la máscara a la imagen original
    result = cv2.bitwise_and(frame, frame, mask=mask)

    # Encuentra objetos segun el filtro de color
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    # Area min 5% del ancho y alto de la imagen



    key = cv2.waitKey(50) & 0xFF

    cv2.putText(frame, "Battery: {}%".format(drone.get_battery()), 
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)



    for contour in contours:
        area = cv2.contourArea(contour)
        if area > area_min:
            cv2.drawContours(frame, contour, -1, (255, 0, 255), 7)
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
            x, y, w, h = cv2.boundingRect(approx)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 5)
            center = (x + w // 2, y + h // 2)
            cv2.circle(frame, center, 5, (0, 0, 255), cv2.FILLED)

            
            
            
            # revisamos si el objrto esta en la parte izquierda
            if x + w // 2 < width // 2 - threshold_x:
                cv2.putText(frame, "Izquierda", (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                error = width // 2 - threshold_x - (x + w // 2)
                # Si el objeto está a la izquierda, envía un comando al dron para girar a la izquierda implementando un control PID
                if error > 0:
                    drone.send_rc_control(0, 0, 0, -int(error*0.5))
                else:
                    drone.send_rc_control(0, 0, 0, 0)


            # revisamos si el objeto esta en la parte derecha
            elif x + w // 2 > width // 2 + threshold_x:
                cv2.putText(frame, "Derecha", (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                error = (x + w // 2) - (width // 2 + threshold_x)
                # Si el objeto está a la derecha, envía un comando al dron para girar a la derecha implementando un control PID
                if error > 0:
                    drone.send_rc_control(0, 0, 0, int(error*0.5))
                else:
                    drone.send_rc_control(0, 0, 0, 0)
            else:
                cv2.putText(frame, "Centro", (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                drone.send_rc_control(0, 0, 0, 0)
            # revisamos si el objeto esta en la parte superior
            
            if y + h/2 < height // 2 - threshold_x:
                cv2.putText(frame, "Arriba", (10,10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                error = height // 2 - threshold_x - (y + h // 2)
                # Si el objeto está arriba, envía un comando al dron para subir implementando un control PID
                if error > 0:
                    drone.send_rc_control(0, 0, int(error*0.5), 0)
                else:
                    drone.send_rc_control(0, 0, 0, 0)
            
            # revisamos si el objeto esta en la parte inferior
            elif y+ h/2  > height // 2 + threshold_x:
                cv2.putText(frame, "Abajo", (10,10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                error = (y + h // 2) - (height // 2 + threshold_x)
                # Si el objeto está abajo, envía un comando al dron para bajar implementando un control PID
                if error > 0:
                    drone.send_rc_control(0, 0, -int(error*0.5), 0)
            else:
                cv2.putText(frame, "Centro", (10,10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                drone.send_rc_control(0, 0, 0, 0)

            # Revisamos el tamaño del objeto para determinar si el dron debe avanzar o retroceder
            if w * h > area_min:
                cv2.putText(frame, "Grande", (10,40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                # Si el objeto es grande, envía un comando al dron para avanzar implementando un control PID
                error = w * h - area_min
                if error > 0:
                    # limitar la velocidad de avance
                    if error > 200:
                        error = 200
                    drone.send_rc_control(0, int(error*0.5), 0, 0)
                else:
                    drone.send_rc_control(0, 0, 0, 0)
            else:
                cv2.putText(frame, "Pequeño", (10,40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                # Si el objeto es pequeño, envía un comando al dron para retroceder implementando un control PID
                error = area_min - (w * h)
                if error > 0:
                    #limitar la velocidad de retroceso
                    if error > 200:
                        error = 200
                    drone.send_rc_control(0, -int(error*0.5), 0, 0)
                else:
                    drone.send_rc_control(0, 0, 0, 0)

            if key == ord('l'):
                if flying:
                    drone.land()
                    flying = False
                else:
                    pass

            if key == ord('t'):
                if flying:
                    pass
                else:
                    if drone.get_battery() <= 15 and not flying:
                        pass
                    else:
                        drone.takeoff()
                        flying = True

            
            
            
    # Dibuja una linea vertical al centro de la imagen
    cv2.line(frame, (width // 2 - threshold_x, 0), (width // 2 - threshold_x, height), (255, 0, 0), 2)
    cv2.line(frame, (width // 2 + threshold_x, 0), (width // 2 + threshold_x, height), (255, 0, 0), 2)

    # Dibuja una linea horizontal al centro de la imagen
    cv2.line(frame, (0, height // 2 - threshold_y), (width, height // 2 - threshold_y), (255, 0, 0), 2)
    cv2.line(frame, (0, height // 2 + threshold_y), (width, height // 2 + threshold_y), (255, 0, 0), 2)

    # Dibuja un rectángulo en el centro de la imagen del area de detección
    cv2.rectangle(frame, (width // 2 - threshold_x, height // 2 - threshold_y), (width // 2 + threshold_x, height // 2 + threshold_y), (0, 0, 255), 2)
    
    # Muestra la imagen original, la imagen filtrada y la imagen filtrada sobrepuesta en la original
    cv2.imshow('Original', frame)
    cv2.imshow('Mask', mask)
    cv2.imshow('Filtrado', result)

    # Salir cuando se presiona 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Libera la captura y cierra las ventanas
cap.release()
cv2.destroyAllWindows()