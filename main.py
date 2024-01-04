
import cv2 
import mediapipe as mp 
import numpy as np 
import tensorflow as tf
from tensorflow.keras.models import load_model

# Mediapipe 

mpHands = mp.solutions.hands
hands = mpHands.Hands(max_num_hands=3, min_detection_confidence=0.7)
mpDraw = mp.solutions.drawing_utils

# Load model 

model = load_model ('mp_hand_gesture')

# Load Class Names 

f = open('gesture.names' , 'r')
labels = f.read().split('\n')
f.close()
print(labels)

# Initilize Opencv 

cap = cv2.VideoCapture(0)

while True:
    # Read each frame from the webcam
    _, frame = cap.read()

    x, y, c = frame.shape

    # Flip the frame vertically
    frame = cv2.flip(frame, 1)
    framergb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Get hand landmark prediction
    result = hands.process(framergb)

    # print(result)
    
    className = ''

    # post process the result
    if result.multi_hand_landmarks:
        landmarks = []
        for handslms in result.multi_hand_landmarks:
            for lm in handslms.landmark:
                # print(id, lm)
                lmx = int(lm.x * x)
                lmy = int(lm.y * y)

                landmarks.append([lmx, lmy])

            # Drawing landmarks on frames
            mpDraw.draw_landmarks(frame, handslms, mpHands.HAND_CONNECTIONS)

    # Show the final output
    cv2.imshow("Spotify Gestures", frame) 

    if cv2.waitKey(1) == ord('q'):
        break


    # Release 
    # cap.release()
    cv2.destroyAllWindows()