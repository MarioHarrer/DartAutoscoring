import cv2

# Kamera-ID 0 (integrierte oder erste USB-Kamera)
cap = cv2.VideoCapture(1)

if not cap.isOpened():
    print("Kamera konnte nicht geöffnet werden.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Fehler beim Lesen des Kamerabildes.")
        break

    cv2.imshow("Live-Kamera", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()