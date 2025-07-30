import cv2

# IDs manuell anpassen basierend auf vorherigem Test
external_cam_ids = [2, 3, 4]
caps = []

for cam_id in external_cam_ids:
    cap = cv2.VideoCapture(cam_id)
    if cap.isOpened():
        print(f"Kamera {cam_id} geöffnet")
        caps.append((cam_id, cap))
    else:
        print(f"Kamera {cam_id} konnte NICHT geöffnet werden")

if not caps:
    print("Keine Kamera verfügbar.")
    exit()

while True:
    for cam_id, cap in caps:
        ret, frame = cap.read()
        if not ret:
            print(f"Fehler bei Kamera {cam_id}")
            continue
        cv2.imshow(f"Kamera {cam_id}", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

for _, cap in caps:
    cap.release()
cv2.destroyAllWindows()