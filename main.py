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
        self.increase_volume_triggered = False
        self.decrease_volume_triggered = False
        self.pause_triggered = False
        self.play_triggered = False
        self.gesture_delay = 1

    def setup_spotify(self):
        client_id = '6ab1dd4df626495199c0a6eae899b084'
        client_secret = 'c5d5b858acd54bccbfff015782c28009'
        redirect_uri = 'https://github.com'  # Redirect URI
        scope = "user-modify-playback-state", "user-read-playback-state"

        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                                       client_secret=client_secret,
                                                       redirect_uri=redirect_uri,
                                                       scope=scope))
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

        cap = cv2.VideoCapture(0)

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
        gestures = self.current_gestures.copy()  # gestures listesini kopyalayalım
        self.lock.release()
        open_hand_detected = False
        closed_fist_detected = False
        two_finger_up_detected = False
        two_finger_down_detected = False

        # El hareketleri taraması
        for hand_gesture_name in gestures:
            cv2.putText(frame, hand_gesture_name, (10, 50), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0, 0, 255), 2, cv2.LINE_AA)

            if hand_gesture_name == 'open hand':
                open_hand_detected = True
            elif hand_gesture_name == 'closed fist':
                closed_fist_detected = True
            elif hand_gesture_name == '2 finger up':
                two_finger_up_detected = True
            elif hand_gesture_name == '2 finger down':
                two_finger_down_detected = True

        # if len(gestures) == 0:
        #     return

        # El izleme sonuçlarını işleyin
        # landmarks = self.mediapipe_hands.process(frame).multi_hand_landmarks
        # if landmarks and len(landmarks) > 0:
        #     hand_landmarks = landmarks[0]

            # İlgili parmak pozisyonlarını kontrol edin
            # index_finger = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.INDEX_FINGER_TIP]
            # middle_finger = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.MIDDLE_FINGER_TIP]
            ###########################################################################################
            # İlgili el işareti algılandıysa
            # if '2 finger up' in gestures:
            #     two_finger_up_detected = True

            #     if two_finger_up_detected:
            #         if index_finger.y > self.last_finger_positions[0] and middle_finger.y > self.last_finger_positions[1]:
            #             self.last_finger_positions = [
            #                 index_finger.y, middle_finger.y]
            #             if not self.increase_volume_triggered:
            #                 self.increase_volume_triggered = True
            #                 threading.Timer(self.gesture_delay,
            #                                 self.reset_volume_trigger).start()
            #                 threading.Thread(
            #                     target=self.increase_volume).start()
            #         else:
            #             self.last_finger_positions = [
            #                 index_finger.y, middle_finger.y]
            ###########################################################################################

        if open_hand_detected and not self.play_triggered:
            self.play_triggered = True
            threading.Timer(self.gesture_delay,
                            self.reset_play_trigger).start()
            threading.Thread(target=self.start_spotify_playback).start()
        elif closed_fist_detected and not self.pause_triggered:
            self.pause_triggered = True
            threading.Timer(self.gesture_delay,
                            self.reset_pause_trigger).start()
            threading.Thread(target=self.pause_spotify_playback).start()
        elif two_finger_up_detected and not self.increase_volume_triggered:
            self.increase_volume_triggered = True
            threading.Timer(self.gesture_delay,
                            self.reset_volume_trigger).start()
            threading.Thread(target=self.increase_volume).start()
        elif two_finger_down_detected and not self.decrease_volume_triggered:
            self.decrease_volume_triggered = True
            threading.Timer(self.gesture_delay,
                            self.reset_decrease_volume_trigger).start()
            threading.Thread(target=self.decrease_volume).start()

    def reset_play_trigger(self):
        self.play_triggered = False

    def reset_pause_trigger(self):
        self.pause_triggered = False

    def reset_volume_trigger(self):
        self.increase_volume_triggered = False

    def reset_decrease_volume_trigger(self):
        self.decrease_volume_triggered = False

    def decrease_volume(self):
        try:
            current_volume = self.sp.current_playback().get(
                'device', {}).get('volume_percent', 50)
            new_volume = max(0, current_volume - 10)
            self.sp.volume(new_volume)
            print(
                f"Müziğin sesi azaltıldı: Yeni ses seviyesi {new_volume}")
        except spotipy.SpotifyException as e:
            if "Restriction violated" in str(e):
                print("Şarkı zaten çalıyor veya durdurulmuş durumda.")
            else:
                print(f"SpotifyException: {e}")

    def increase_volume(self):
        try:
            current_volume = self.sp.current_playback().get(
                'device', {}).get('volume_percent', 50)
            new_volume = min(100, current_volume + 10)
            self.sp.volume(new_volume)
            print(
                f"Müziğin sesi artırıldı: Yeni ses seviyesi {new_volume}")
        except spotipy.SpotifyException as e:
            if "Restriction violated" in str(e):
                print("Şarkı zaten çalıyor veya durdurulmuş durumda.")
            else:
                print(f"SpotifyException: {e}")

    def start_spotify_playback(self):
        try:
            if not self.playing:
                self.sp.start_playback()
                self.playing = True
                print('Şarkı başladı.')
        except spotipy.SpotifyException as e:
            if "Restriction violated" in str(e):
                print("Şarkı zaten çalıyor veya durdurulmuş durumda.")
            else:
                print(f"SpotifyException: {e}")

    def pause_spotify_playback(self):
        try:
            if self.playing:
                self.sp.pause_playback()
                self.playing = False
                print('Şarkı durduruldu.')
        except spotipy.SpotifyException as e:
            if "Restriction violated" in str(e):
                print("Şarkı zaten çalıyor veya durdurulmuş durumda.")
            else:
                print(f"SpotifyException: {e}")

    def __result_callback(self, result, output_image, timestamp_ms):
        self.lock.acquire()
        self.current_gestures = []
        if result is not None and any(result.gestures):
            for single_hand_gesture_data in result.gestures:
                gesture_name = single_hand_gesture_data[0].category_name
                self.current_gestures.append(gesture_name)
        self.lock.release()


if __name__ == "__main__":
    rec = GestureRecognizer()
    rec.main()
