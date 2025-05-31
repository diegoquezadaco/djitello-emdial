import cv2
import mediapipe as mp

# Inicializar MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)

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


# Iniciar cámara
cap = cv2.VideoCapture(0)

def compute_distance(landmark1, landmark2):
    """Calcula la distancia entre dos puntos de referencia."""
    return ((landmark1.x - landmark2.x) ** 2 + (landmark1.y - landmark2.y) ** 2) ** 0.5

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Flip para espejo
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    result = hands.process(rgb)
    label = "No se detecta mano"

    if result.multi_hand_landmarks and result.multi_handedness:
        hand_landmarks = result.multi_hand_landmarks[0]
        handedness = result.multi_handedness[0]

        landmarks = hand_landmarks.landmark
        if landmarks[middle_tip].y < landmarks[middle_mcp].y and landmarks[ring_tip].y < landmarks[ring_mcp].y and landmarks[pinky_tip].y < landmarks[pinky_mcp].y and landmarks[thumb_tip].y < landmarks[thumb_mcp].y and landmarks[index_tip].y < landmarks[index_mcp].y:
            label = "Takeoff"
    
        elif landmarks[middle_tip].y > landmarks[middle_mcp].y and landmarks[ring_tip].y > landmarks[ring_mcp].y and landmarks[pinky_tip].y > landmarks[pinky_mcp].y and landmarks[index_tip].y > landmarks[index_mcp].y:
            label = "Land"
        elif landmarks[pinky_tip].y < landmarks[pinky_mcp].y and landmarks[thumb_tip].x > landmarks[thumb_mcp].x and landmarks[index_tip].y > landmarks[index_mcp].y and landmarks[middle_tip].y > landmarks[middle_mcp].y and landmarks[ring_tip].y > landmarks[ring_mcp].y:
            label = "Up"
            cmd = 2
        elif landmarks[pinky_tip].y > landmarks[pinky_mcp].y and landmarks[thumb_tip].y > landmarks[thumb_mcp].y and landmarks[index_tip].y > landmarks[wrist].y and landmarks[middle_tip].y > landmarks[wrist].y and landmarks[ring_tip].y > landmarks[wrist].y:
            label = "Down"
            cmd = 3
        elif landmarks[thumb_tip].y < landmarks[thumb_mcp].y and landmarks[index_tip].y < landmarks[index_mcp].y and landmarks[thumb_tip].x < landmarks[pinky_mcp].x and landmarks[middle_tip].y > landmarks[middle_mcp].y and landmarks[ring_tip].y > landmarks[ring_mcp].y and landmarks[pinky_tip].y > landmarks[pinky_mcp].y:
            label = "Right"
            cmd = 4
        elif landmarks[thumb_tip].y < landmarks[thumb_mcp].y and landmarks[index_tip].y < landmarks[index_mcp].y and landmarks[thumb_tip].x > landmarks[pinky_mcp].x and landmarks[middle_tip].y > landmarks[middle_mcp].y and landmarks[ring_tip].y > landmarks[ring_mcp].y and landmarks[pinky_tip].y > landmarks[pinky_mcp].y:
            label = "Left"
            cmd = 5
        elif landmarks[thumb_tip].y < landmarks[thumb_mcp].y and landmarks[index_tip].y < landmarks[index_mcp].y and landmarks[thumb_tip].x < landmarks[pinky_mcp].x and landmarks[middle_tip].y > landmarks[middle_mcp].y and landmarks[ring_tip].y > landmarks[ring_mcp].y and landmarks[pinky_tip].y < landmarks[pinky_mcp].y:
            label = "Front"
            cmd = 6
        elif landmarks[thumb_tip].y < landmarks[thumb_mcp].y and landmarks[index_tip].y < landmarks[index_mcp].y and landmarks[thumb_tip].x > landmarks[pinky_mcp].x and landmarks[middle_tip].y > landmarks[middle_mcp].y and landmarks[ring_tip].y > landmarks[ring_mcp].y and landmarks[pinky_tip].y < landmarks[pinky_mcp].y:
            label = "Back"
            cmd = 7
        elif landmarks[thumb_tip].y < landmarks[thumb_ip].y and \
                landmarks[thumb_ip].y < landmarks[thumb_mcp].y and \
                landmarks[index_tip].x > landmarks[index_pip].x and \
                landmarks[middle_tip].x > landmarks[middle_pip].x and \
                landmarks[ring_tip].x > landmarks[ring_pip].x and \
                landmarks[pinky_tip].x < landmarks[pinky_dip].x and \
                landmarks[pinky_dip].x < landmarks[pinky_pip].x and \
                landmarks[pinky_pip].x < landmarks[pinky_mcp].x:
            label = "Chill"
    
        elif landmarks[thumb_tip].y < landmarks[thumb_ip].y and \
                landmarks[thumb_ip].y < landmarks[thumb_mcp].y and \
                landmarks[index_tip].x < landmarks[index_pip].x and \
                landmarks[middle_tip].x < landmarks[middle_pip].x and \
                landmarks[ring_tip].x < landmarks[ring_pip].x and \
                landmarks[pinky_tip].x > landmarks[pinky_dip].x and \
                landmarks[pinky_dip].x > landmarks[pinky_pip].x and \
                landmarks[pinky_pip].x > landmarks[pinky_mcp].x:
            label = "Chill Pal otro lado"

        elif landmarks[thumb_tip].x < landmarks[thumb_ip].x and \
                landmarks[thumb_ip].x < landmarks[thumb_mcp].x and \
                landmarks[index_tip].y > landmarks[pinky_mcp].y and \
                landmarks[index_tip].x < landmarks[index_dip].x and \
                landmarks[index_dip].x < landmarks[index_pip].x and \
                landmarks[index_pip].x < landmarks[index_mcp].x: #and \
            print("index tip", landmarks[index_tip].x, "index mcp", landmarks[index_mcp].x)
            distance = compute_distance(landmarks[index_tip], landmarks[thumb_tip])
            cv2.line(frame, (int(landmarks[index_tip].x * w), int(landmarks[index_tip].y * h)),
                    (int(landmarks[thumb_tip].x * w), int(landmarks[thumb_tip].y * h)), (0, 255, 0), 2)
            
            #label = (f'Distance: {distance:.4} - Index pointing up')

            cv2.putText(frame, f'Distance: {distance:.4}', (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            if distance <= 0.2:  # Ajusta el umbral según sea necesario
                label = "Backward"
            elif distance > 0.2:
                label = "Forward"
            
        else:
            label = "Otro gesto"
            print(f"Detected command: {label}")

        # Dibujar puntos de la mano
        mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    # Mostrar resultado
    cv2.putText(frame, label, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
    cv2.imshow("Detector de gestos", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
