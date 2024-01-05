import cv2
import os
import time

# OpenCV'nin başlatılması
cap = cv2.VideoCapture(0)  # VideoCapture(0) webcam üzerinden görüntü alır

# Dikdörtgen koordinatları ve boyutları
rectangle_top_left = (200, 200)
rectangle_bottom_right = (900, 900)

# Klasör oluşturma
gesture_folder = "el_hareketleri_klasoru"
if not os.path.exists(gesture_folder):
    os.makedirs(gesture_folder)

# Kayıt durumu
recording = False

# Zamanı izlemek için bir sayaç başlat
time_counter = time.time()

while True:
    # Webcam'den her bir çerçeveyi oku
    ret, frame = cap.read()

    if not ret:
        print("Webcam'den görüntü alınamıyor!")
        break

    x, y, c = frame.shape

    # Kareyi dikey olarak çevir
    frame = cv2.flip(frame, 1)

    # Dikdörtgeni çiz
    cv2.rectangle(frame, rectangle_top_left,
                  rectangle_bottom_right, (255, 0, 0), 2)

    # R tuşuna basarak kayıtı başlat veya durdur
    key = cv2.waitKey(1) & 0xFF
    if key == ord('r'):
        if recording:
            recording = False
            print("Kayıt Durduruldu!")
        else:
            recording = True
            print("Kayıt Başladı!")
        time_counter = time.time()  # Zamanı sıfırla

    # Her 2 saniyede bir fotoğrafı kaydet
    if recording and time.time() - time_counter >= 2:
        time_counter = time.time()  # Zamanı sıfırla

        # Dikdörtgen içindeki görüntüyü al
        x1, y1 = rectangle_top_left
        x2, y2 = rectangle_bottom_right
        crop_img = frame[y1:y2, x1:x2]

        # Görüntüyü dosyaya kaydet
        if crop_img.size != 0:
            file_name = f"gesture_{len(os.listdir(gesture_folder))}.jpg"
            cv2.imwrite(os.path.join(gesture_folder, file_name), crop_img)
            print("Görüntü Kaydedildi!")
        else:
            print("Kesilen görüntü boş!")

    # Kayıt durumu gösterimi
    if recording:
        cv2.putText(frame, "Recording...", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    else:
        cv2.putText(frame, "Press 'R' to start recording...", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # Son çıktıyı göster
    cv2.imshow("Spotify Gestures", frame)

    if cv2.waitKey(1) == ord('q'):
        break

# Kaynakları serbest bırak
cap.release()
cv2.destroyAllWindows()
