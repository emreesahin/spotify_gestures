import cv2
import mediapipe as mp
from mediapipe.tasks import python
import threading
import spotipy
from spotipy.oauth2 import SpotifyOAuth


class GestureRecognizer:
    def __init__(self):
        self.sp = self.setup_spotify()
        self.playing = False

    def setup_spotify(self):
        client_id = '6ab1dd4df626495199c0a6eae899b084'
        client_secret = 'c5d5b858acd54bccbfff015782c28009'
        redirect_uri = 'https://github.com'  # Redirect URI
        scope = "user-modify-playback-state", "user-read-playback-state"

        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                                       client_secret=client_secret,
                                                       redirect_uri=redirect_uri,
                                                       scope=scope))

        current_track = sp.current_playback()
        if current_track is not None:
            print("Currently Playing Track:")
            print(current_track)
        else:
            print("Spotify is not connected.")
        return sp

    def main(self):
        num_hands = 2
        model_path = "../../gesture_recognizer.task"
        GestureRecognizer = mp.tasks.vision.GestureRecognizer
        GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
        VisionRunningMode = mp.tasks.vision.RunningMode

        self.mediapipe_hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils

        self.lock = threading.Lock()
        self.current_gestures = []
        options = GestureRecognizerOptions(
            base_options=python.BaseOptions(model_asset_path=model_path),
            running_mode=VisionRunningMode.LIVE_STREAM,
            num_hands=num_hands,
            result_callback=self.__result_callback)
        recognizer = GestureRecognizer.create_from_options(options)

        timestamp = 0
        mp_drawing = mp.solutions.drawing_utils
        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=num_hands,
            min_detection_confidence=0.65,
            min_tracking_confidence=0.65)

        cap = cv2.VideoCapture(1)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(frame)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            np_array = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    mp_image = mp.Image(
                        image_format=mp.ImageFormat.SRGB, data=np_array)
                    recognizer.recognize_async(mp_image, timestamp)
                    timestamp = timestamp + 1

                self.put_gestures(frame)

            cv2.imshow('MediaPipe Hands', frame)
            key = cv2.waitKey(1)
            if key == ord('q') or key == 27:
                break

        cap.release()

    def put_gestures(self, frame):
        self.lock.acquire()
        gestures = self.current_gestures
        self.lock.release()
        open_hand_detected = False
        closed_fist_detected = False

        # El hareketleri taraması
        for hand_gesture_name in gestures:
            cv2.putText(frame, hand_gesture_name, (10, 50), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0, 0, 255), 2, cv2.LINE_AA)

            if hand_gesture_name == 'open hand':
                open_hand_detected = True
            elif hand_gesture_name == 'closed fist':
                closed_fist_detected = True

        # Durumu kontrol etme ve Spotify işlemlerini gerçekleştirme
        if open_hand_detected and not self.playing:
            self.sp.start_playback()
            self.playing = True
        elif closed_fist_detected and self.playing:
            self.sp.pause_playback()
            self.playing = False

    def __result_callback(self, result, output_image, timestamp_ms):
        self.lock.acquire()
        self.current_gestures = []
        if result is not None and any(result.gestures):
            print("Recognized gestures:")
            for single_hand_gesture_data in result.gestures:
                gesture_name = single_hand_gesture_data[0].category_name
                print(gesture_name)
                self.current_gestures.append(gesture_name)
        self.lock.release()


if __name__ == "__main__":
    rec = GestureRecognizer()
    rec.main()
