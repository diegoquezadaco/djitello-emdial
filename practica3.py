import cv2
import mediapipe as mp

# Inicializar MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)

# Coordenadas
thumb_
thumb_tip = 4
index_base = 5
middle_tip = 12
middle_mcp = 19
ring_tip = 16
ring_mcp = 13
pinky_tip = 20
pinky_mcp = 17

# Iniciar cámara
cap = cv2.VideoCapture(0)

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
        if landmarks[thumb_tip].y < landmarks[index_base].y:
            label = "Pulgar arriba detectado"
        else:
            label = "Otro gesto"

        # Dibujar puntos de la mano
        mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    # Mostrar resultado
    cv2.putText(frame, label, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
    cv2.imshow("Detector de gestos", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
