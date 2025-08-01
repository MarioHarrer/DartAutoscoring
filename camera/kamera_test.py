import cv2
import time
import numpy as np
import sys
from functools import partial
import requests

def get_available_cameras(max_tested=6):
    available = []
    print("Suche verfügbare Kameras...")
    sys.stdout.flush()
    for cam_id in range(max_tested):
        cap = cv2.VideoCapture(cam_id)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"Kamera {cam_id} funktioniert")
                available.append(cam_id)
            cap.release()
        else:
            print(f"Kamera {cam_id} konnte nicht geöffnet werden")
        sys.stdout.flush()
    return available

def choose_cameras(camera_ids):
    selected = []
    for cam_id in camera_ids:
        cap = cv2.VideoCapture(cam_id)
        if not cap.isOpened():
            continue
        ret, frame = cap.read()
        if ret:
            cv2.imshow(f"Kamera {cam_id} Vorschau", frame)
            print(f"Kamera {cam_id}: Drücke 'y' zum Auswählen, 'n' zum Überspringen.")
            sys.stdout.flush()
            while True:
                key = cv2.waitKey(0)
                if key == ord('y'):
                    selected.append(cam_id)
                    print(f"Kamera {cam_id} ausgewählt.")
                    break
                elif key == ord('n'):
                    print(f"Kamera {cam_id} übersprungen.")
                    break
                sys.stdout.flush()
        cap.release()
        cv2.destroyAllWindows()
    return selected

def compare_images(img1, img2):
    diff = cv2.absdiff(img1, img2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours, thresh

def detect_motion(prev_frame, curr_frame):
    diff = cv2.absdiff(prev_frame, curr_frame)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
    motion_pixels = cv2.countNonZero(thresh)
    return motion_pixels > 1000

def get_user_mode():
    print("\nWähle Modus:")
    print("Drücke die Taste für den gewünschten Modus:")
    print("1 = Automatische Bewegungserkennung")
    print("2 = Manuelles Auslösen (Taste 'm')")
    print("3 = Bewegung mit Bestätigung (Taste 'n')")
    sys.stdout.flush()

    cv2.namedWindow('Moduswahl')
    while True:
        key = cv2.waitKey(0) & 0xFF

        if key == ord('1'):
            cv2.destroyWindow('Moduswahl')
            return "1"
        elif key == ord('2'):
            cv2.destroyWindow('Moduswahl')
            return "2"
        elif key == ord('3'):
            cv2.destroyWindow('Moduswahl')
            return "3"
        elif key == ord('q'):
            cv2.destroyWindow('Moduswahl')
            return None


def run_manual_mode(cap):
    print("Referenzbild aufnehmen (ohne Dart)...")
    sys.stdout.flush()
    time.sleep(1)
    ret, reference = cap.read()
    if not ret:
        print("Fehler beim Referenzbild.")
        sys.stdout.flush()
        return

    print("Drücke 'm' für manuelles Erfassen, 'q' zum Beenden.")
    sys.stdout.flush()
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('m'):
            print("Manuelles Bild aufgenommen, vergleiche...")
            sys.stdout.flush()
            contours, thresh = compare_images(reference, frame)
            display_frame = frame.copy()
            for cnt in contours:
                if cv2.contourArea(cnt) < 100:
                    continue
                x, y, w, h = cv2.boundingRect(cnt)
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.imshow("Manueller Vergleich", display_frame)
            cv2.imshow("Differenzbild", thresh)
            cv2.waitKey(2000)
            cv2.destroyWindow("Manueller Vergleich")
            cv2.destroyWindow("Differenzbild")

        cv2.imshow("Live", frame)

    cap.release()
    cv2.destroyAllWindows()

def run_motion_mode(cap):
    print("Referenzbild aufnehmen (ohne Dart)...")
    sys.stdout.flush()
    time.sleep(1)
    ret, reference = cap.read()
    if not ret:
        print("Fehler beim Referenzbild.")
        sys.stdout.flush()
        return

    prev = None
    ready_for_next = True

    print("Starte automatische Bewegungserkennung...")
    sys.stdout.flush()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if prev is not None:
            movement = detect_motion(prev, frame)

            if movement and ready_for_next:
                print("Bewegung erkannt! Warte 1 Sekunde...")
                sys.stdout.flush()
                ready_for_next = False
                time.sleep(1)

                ret, new_frame = cap.read()
                if not ret:
                    continue

                print("Bild aufgenommen, vergleiche mit Referenz...")
                sys.stdout.flush()
                contours, thresh = compare_images(reference, new_frame)

                for cnt in contours:
                    if cv2.contourArea(cnt) < 100:
                        continue
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(new_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                cv2.imshow("Unterschied erkannt", new_frame)
                cv2.imshow("Differenzbild", thresh)

            elif not movement:
                ready_for_next = True

        prev = frame
        cv2.imshow("Live", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

def run_manual_confirm_mode(cap):
    print("Referenzbild aufnehmen (ohne Dart)...")
    sys.stdout.flush()
    time.sleep(1)
    ret, reference = cap.read()
    if not ret:
        print("Fehler beim Referenzbild.")
        sys.stdout.flush()
        return

    prev = None
    ready_for_next = True

    print("Starte automatische Bewegungserkennung mit Bestätigung...")
    sys.stdout.flush()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if prev is not None:
            movement = detect_motion(prev, frame)

            if movement and ready_for_next:
                print("Bewegung erkannt! Warte 1 Sekunde...")
                sys.stdout.flush()
                ready_for_next = False
                time.sleep(1)

                ret, new_frame = cap.read()
                if not ret:
                    continue

                print("Bild aufgenommen, vergleiche mit Referenz...")
                sys.stdout.flush()
                contours, thresh = compare_images(reference, new_frame)

                for cnt in contours:
                    if cv2.contourArea(cnt) < 100:
                        continue
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(new_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                cv2.imshow("Unterschied erkannt", new_frame)
                cv2.imshow("Differenzbild", thresh)

                # Erstelle ein Fenster mit Buttons
                confirm_window = np.zeros((200, 400, 3), np.uint8)
                # Zeichne Buttons
                cv2.rectangle(confirm_window, (50, 50), (150, 100), (0, 255, 0), -1)  # Grüner "Ja" Button
                cv2.rectangle(confirm_window, (250, 50), (350, 100), (0, 0, 255), -1)  # Roter "Nein" Button
                # Füge Text hinzu
                cv2.putText(confirm_window, "20 Punkte akzeptieren?", (100, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(confirm_window, "Ja", (85, 85),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
                cv2.putText(confirm_window, "Nein", (285, 85),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                cv2.imshow("Wurf bestätigen", confirm_window)

                # Mausklick-Callback-Funktion
                def mouse_callback(event, x, y, flags, param):
                    if event == cv2.EVENT_LBUTTONDOWN:
                        if 50 <= x <= 150 and 50 <= y <= 100:  # Ja-Button geklickt
                            try:
                                response = requests.post('http://localhost:8080/dartboard/throw',
                                                         data={
                                                             "score": 20,
                                                             "isDouble": False,
                                                             "isTriple": False
                                                         },
                                                         headers={
                                                             "Content-Type": "application/x-www-form-urlencoded"
                                                         })

                                if response.status_code == 200:
                                    print("20 Punkte wurden erfolgreich registriert!")
                                else:
                                    print("Fehler beim Registrieren der Punkte!")
                            except Exception as e:
                                print(f"Fehler beim Senden der Punkte: {str(e)}")

                            cv2.setMouseCallback("Wurf bestätigen", lambda *args: None)
                            cv2.destroyWindow("Wurf bestätigen")
                            cv2.destroyWindow("Unterschied erkannt")
                            cv2.destroyWindow("Differenzbild")
                            param[0] = True  # Signal zum Fortfahren

                        elif 250 <= x <= 350 and 50 <= y <= 100:  # Nein-Button geklickt
                            cv2.setMouseCallback("Wurf bestätigen", lambda *args: None)
                            cv2.destroyWindow("Wurf bestätigen")
                            cv2.destroyWindow("Unterschied erkannt")
                            cv2.destroyWindow("Differenzbild")
                            param[0] = True  # Signal zum Fortfahren

                # Setze Mouse-Callback und warte auf Klick
                button_clicked = [False]
                cv2.setMouseCallback("Wurf bestätigen", mouse_callback, button_clicked)
                while not button_clicked[0]:
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        cap.release()
                        cv2.destroyAllWindows()
                        return

                ready_for_next = True

            elif not movement:
                ready_for_next = True

        prev = frame
        cv2.imshow("Live", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()






# Hilfsfunktion zum Registrieren der Punkte
def register_points(points):
    # Hier implementieren Sie die Logik, die normalerweise
    # durch den Mausklick auf die Dartscheibe ausgelöst wird
    print(f"{points} Punkte wurden zum Spielstand hinzugefügt!")
    sys.stdout.flush()


def main():
    all_cams = get_available_cameras()
    if not all_cams:
        print("Keine Kameras gefunden.")
        sys.stdout.flush()
        return

    selected_cams = choose_cameras(all_cams)
    if not selected_cams:
        print("Keine Kamera ausgewählt.")
        sys.stdout.flush()
        return

    # Separater Aufruf für die Modusauswahl
    mode = get_user_mode()
    if not mode:
        return

    cam_id = selected_cams[0]
    cap = cv2.VideoCapture(cam_id)
    if not cap.isOpened():
        print("Kamera konnte nicht geöffnet werden.")
        sys.stdout.flush()
        return

    if mode == "1":
        run_motion_mode(cap)
    elif mode == "2":
        run_manual_mode(cap)
    elif mode == "3":
        run_manual_confirm_mode(cap)

if __name__ == "__main__":
    main()
