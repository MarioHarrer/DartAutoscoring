import cv2
import numpy as np
import os
import torch
import requests
import threading
from flask import Flask, jsonify, Response, render_template
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor

# ------ 1. KONFIGURATION ------
# Homographie
SIZE = 800  # Größe der entzerrten Dartscheibe
CENTER = (400, 400)  # Mittelpunkt
CAM_IDS = [0, 1, 2]  # Die 3 Kameras

# --SAM 2 Pfade--
# os sodass es betriebsunabhängig ist ich damit kommunizieren kann
# Liest von innen nach außen holt sich filenamen und danach automatisch den absoluten pfad und danach schneide ich die datei vom ordner ab
# das mache ich, das ich danahc zum beispiel das sam2 modell anfügen
# das file holen also kamera_test.py damit ich einen Ankerpunkt habe sodas ich dazu den pfad finden kann und python keine bessere lösung hat
# Beispiel: "C:\Users\Mario\OneDrive - HTL Saalfelden\Schule\DartAu...\camera\kamera_test.py"
# Nach der Zeile: "C:\Users\Mario\OneDrive - HTL Saalfelden\Schule\DartAu...\camera"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Diese Zeile fügt deinen ermittelten Hauptordner, den Unterordner sam_checkpoints und den Dateinamen sam2.1_hiera_large.pt automatisch zu einem vollständigen Dateipfad zusammen
# damit das Programm exakt weiß, wo es die KI-Datei auf deiner Festplatte findet.
# "C:\Users\Mario\OneDrive - HTL Saalfelden\Schule\DartAu...\camera\sam_checkpoints\sam2.1_hiera_large.pt"
CHECKPOINT = os.path.join(BASE_DIR, "sam_checkpoints", "sam2.1_hiera_large.pt")

# Das hier ist die config datei sodass es ein bauplan gibt um das model zu laden
# wird später genutzt welche modelgrße später geladen werden soll
# Large datei damit wir gut die pfeilspitzen erkenn können.
# config datein ist in der datei die heruntergeladen wurde
MODEL_CFG = "configs/sam2.1/sam2.1_hiera_l.yaml"
# durch den 3 zeilen habe ich den pfad sodass ich dann später das sam2 Model laden kann

# Ziel-Koordinaten für die Homographie (Double-Ring)
# ZIEL-SCHABLONE FÜR DIE ENTZERRUNG:
# Diese 4 perfekten Koordinaten geben der Mathematik das Ziel vor.
# Sie zwingen die 4 schiefen Kamera-Klicks auf ein perfektes Kreuz
# (genau 320 Pixel Radius), damit die Scheibe wieder kreisrund wird.
DST_PTS = np.array([
    [400, 80],  # Double 20
    [720, 400],  # Double 6
    [400, 720],  # Double 3
    [80, 400]  # Double 11
], dtype="float32")

# Reihenfolge der Dart-Felder im Uhrzeigersinn
# Wird genutzt, um die berechnung des Pfeils in Punkte umzuwandeln.
SEGMENTS = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5]

# Leere Liste für meine 4 Mausklicks zum zuordnen
pts_tmp = []

# --- NEU: FLASK WEBSERVER & STATE FÜR BACKEND-KOMMUNIKATION ---
app = Flask(__name__)
system_active = False  # Steuert den Ruhezustand der Kameras

# Speichert die jeweils aktuellsten Frames für das Web-Dashboard
dashboard_frames = {
    "live": None,
    "result": None,
    "debug": None,
    "homography": None
}

# Globale Referenz für das Linien-State, damit das Web-Dashboard Kameras direkt per Klick umschalten kann
global_app_state = {'lines_data': [], 'board_img': np.zeros((SIZE, SIZE, 3), dtype=np.uint8)}


@app.route('/api/camera/start', methods=['POST'])
def start_cameras():
    global system_active
    system_active = True
    print("\n🟢 START-BEFEHL EMPFANGEN: Kameras werden initialisiert.")
    return jsonify({"status": "Kameras werden gestartet"})


@app.route('/api/camera/stop', methods=['POST'])
def stop_cameras():
    global system_active
    system_active = False
    print("\n🔴 STOP-BEFEHL EMPFANGEN: Kameras gehen in den Ruhezustand.")
    return jsonify({"status": "Kameras werden gestoppt"})


@app.route('/api/camera/toggle/<int:cid>', methods=['POST'])
def toggle_camera_web(cid):
    """ Ermöglicht das Umschalten einer Kamera direkt über das Web-Dashboard """
    found = False
    for line in global_app_state['lines_data']:
        if line['cid'] == cid:
            line['active'] = not line['active']
            status = "DEAKTIVIERT" if not line['active'] else "AKTIVIERT"
            print(f"Kamera {cid} per Web-Klick {status}")
            found = True
            break

    update_result_board_global(is_correction=True)
    return jsonify({"status": "success", "cid": cid, "found": found})


trigger_background = False
trigger_throw = False


@app.route('/api/action/background')
def web_background():
    global trigger_background
    trigger_background = True
    return jsonify({"status": "Background angefordert"})


@app.route('/api/action/throw')
def web_throw():
    global trigger_throw
    trigger_throw = True
    return jsonify({"status": "Wurfauswertung gestartet"})


# NEU: Diese Route wird aufgerufen, wenn im Browser manuell korrigiert wird
@app.route('/api/action/clear_lines', methods=['POST'])
def clear_lines():
    global_app_state['lines_data'] = []
    update_result_board_global(is_correction=False)
    print("🔒 Manueller Eingriff im Web: Kameras gesperrt bis zum nächsten Wurf.")
    return jsonify({"status": "gesperrt"})


def update_result_board_global(is_correction=False):
    """ Zeichnet das Board global neu, wenn Kameras über das Web-Dashboard umgeschaltet werden """
    board = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    cv2.circle(board, CENTER, 345, (50, 50, 50), -1)
    cv2.circle(board, CENTER, 14, (0, 0, 255), -1)

    active_lines = []
    for line in global_app_state['lines_data']:
        p1, p2 = line['p1'], line['p2']
        if line['active']:
            active_lines.append((p1, p2))
            cv2.line(board, p1, p2, line['color'], 2)
        else:
            cv2.line(board, p1, p2, (80, 80, 80), 1)

    if len(active_lines) >= 2:
        intersection = get_intersection(active_lines)
        if intersection:
            label, mult, total, backend_score, is_dbl, is_tpl = get_score(intersection[0], intersection[1])
            print(f"🎯 NEUER SCORE BERECHNET: {label} | Punkte: {total} | Korrektur: {is_correction}")

            send_score_to_backend(backend_score, is_dbl, is_tpl, is_correction)

            cv2.circle(board, intersection, 6, (0, 255, 255), -1)
            cv2.putText(board, f"{label} ({total})", (intersection[0] + 15, intersection[1]),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    else:
        # Kein Print bei 0 Linien (um Spam zu vermeiden, wenn gesperrt ist)
        if len(global_app_state['lines_data']) > 0:
            print("INFO: Zu wenige Kameras aktiv (<2) um einen Schnittpunkt zu berechnen.")

    global_app_state['board_img'] = board
    dashboard_frames["result"] = board


def generate_web_stream(frame_key):
    while True:
        frame = dashboard_frames.get(frame_key)
        if frame is None:
            # Sende ein schwarzes Platzhalter-Bild, falls noch kein Frame da ist
            frame = np.zeros((300, 400, 3), dtype=np.uint8)

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret: continue

        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@app.route('/stream/<frame_key>')
def video_feed(frame_key):
    return Response(generate_web_stream(frame_key), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    # NEU: Übergibt dem HTML, ob gerade ein Kamerawurf aktiv ist und welche Kamera an/aus ist
    has_throw = len(global_app_state['lines_data']) > 0
    cam_states = {}
    for line in global_app_state['lines_data']:
        cam_states[line['cid']] = line['active']

    return render_template('index.html', has_throw=has_throw, cam_states=cam_states)


def start_flask_server():
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)  # Verhindert Spam in der Konsole
    app.run(port=5000, debug=False, use_reloader=False)


def send_score_to_backend(base_score, is_double, is_triple, is_correction=False):
    """ Sendet den Wurf asynchron per HTTP POST an das Quarkus-Backend """
    url = "http://localhost:8080/api/dart/score"

    payload = {
        "score": base_score,
        "isDouble": is_double,
        "isTriple": is_triple,
        "isCorrection": is_correction
    }

    def post_request():
        try:
            response = requests.post(url, json=payload, timeout=2)
            print(f"🌐 Score an Backend gesendet! Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Verbindung zum Backend fehlgeschlagen: {e}")

    threading.Thread(target=post_request).start()


# ---------------- 2. KI MODELL LADEN ----------------
print("Lade SAM 2 Modell...")
# Schaut ob eine Grafikkarte cuba verfügbar is ansonsten wird gpu Prozessor verwendet
device = "cuda" if torch.cuda.is_available() else "cpu"
# Das Ki modell wird in die Hardware auf cuda oder gpu geladen
sam2_model = build_sam2(MODEL_CFG, CHECKPOINT, device=device)
# Verpackt das nackte KI-Modell in ein Werkzeug (Predictor).
# Er übersetzt unsere Kamerabilder für die KI, speichert Berechnungen
# und erlaubt mit simplen X/Y-Pixeln nach Darts zu suchen.
predictor = SAM2ImagePredictor(sam2_model)
print(f"SAM 2 geladen auf {device.upper()}")


# ---------------- 3. MATHEMATIK & GEOMETRIE ----------------
def get_score(x, y):  # Pixel Koordinaten
    dx = x - CENTER[
        0]  # Berechnet die Distanz auf der X-Achse: Wie viele Pixel liegt der Treffer links oder rechts vom absoluten Zentrum
    dy = y - CENTER[
        1]  # Berechnet die Distanz auf der Y-Achse: Wie viele Pixel liegt der Treffer über oder unter dem Zentrum
    r = np.sqrt(
        dx ** 2 + dy ** 2)  # Das ist der klassische Satz des Pythagoras. Es berechnet die direkte Luftlinie in Pixeln vom Bullseye bis zum Dartpfeil.

    R_BULL, R_SINGLE_BULL = 14, 35  # Das innere, rote Bullseye ist 14 Pixel groß. Das äußere, grüne Single Bull geht bis 35 Pixel.
    R_TRIPLE_START, R_TRIPLE_END = 195, 220
    R_DOUBLE_START, R_DOUBLE_END = 315, 360

    # bis hier auf der homographie

    if r <= R_BULL:
        return "BULLSEYE", 50, 50, 50, True, False
    elif r <= R_SINGLE_BULL:
        return "SINGLE BULL", 25, 25, 25, False, False
    elif r > R_DOUBLE_END:
        return "AUSSERHALB", 0, 0, 0, False, False

    #
    # Beispiel-Ablauf für einen Treffer auf der Double 20 (X=400, Y=80):
    # 1. dx = 400 - 400 = 0   | dy = 80 - 400 = -320
    # 2. np.arctan2(-320, 0)  -> -1.5708 Radian
    # 3. np.degrees(-1.5708)  -> angle = -90.0° (exakt oben auf 12 Uhr)
    # WINKEL-BERECHNUNG (-180° bis +180°):
    # WICHTIG: Auf Computerbildschirmen liegt der Nullpunkt (0,0) OBEN links!
    # - Ein Pfeil OBEN (z. B. Feld 20) hat einen KLEINEREN Y-Wert als die Mitte. Die Distanz 'dy' wird negativ.
    # - Ein Pfeil UNTEN (z. B. Feld 3) hat einen GRÖSSEREN Y-Wert als die Mitte. Die Distanz 'dy' wird positiv.
    # Da die Mathe-Funktion arctan2 diesen Bildschirm-Dreher nicht kennt,
    # gibt sie für 12 Uhr (Feld 20) fälschlicherweise -90° (unten) und für 6 Uhr (Feld 3) +90° (oben) aus.
    angle = np.degrees(np.arctan2(dy, dx))

    # Beispiel-Ablauf für Feld 5 (links neben der 20, angle = -100.0°):
    # 1. -100.0 + 90 -> -10.0 (Liegt 10° links von der 12-Uhr-Linie)
    # 2.   -10.0 +  9 ->  -1.0 (Verschiebung um 9° zur Zentrierung)
    # 3.    -1.0 % 360 -> 359.0 (Modulo dreht -1° zum Kreisende bei 359°)
    #
    # -> Ergebnis: adjusted_angle = 359.0
    # -> Test für später: 359 // 18 = 19 -> Index 19 in SEGMENTS -> 5 Punkte

    # WARUM DAS "+ 9" EXTREM WICHTIG IST (Feld-Zentrierung):
    # Das 20er-Feld ist 18° breit und liegt mittig auf 12 Uhr (-9° bis +9°).
    # Ohne "+ 9" würde die linke Hälfte der 20 (-9° bis 0°) fälschlicherweise als 5 gewertet!
    #
    # OHNE "+ 9":
    # - Pfeil A (in der 20 bei -5°):  -5° % 360 = 355° -> 355 // 18 = Index 19 (5 Punkte -> FALSCH!)
    # - Pfeil B (in der  5 bei -10°): -10° % 360 = 350° -> 350 // 18 = Index 19 (5 Punkte -> Richtig)
    #
    # MIT "+ 9" (Verschiebt das 20er-Feld auf saubere 0° bis 18°):
    # - Pfeil A (in der 20 bei -5°):   -5° + 9 = +4° ->   4 // 18 = Index 0  (20 Punkte -> KORREKT!)
    # - Pfeil B (in der  5 bei -10°): -10° + 9 = -1° -> -1° % 360 = 359° -> 359 // 18 = Index 19 (5 Punkte -> KORREKT!)
    adjusted_angle = (angle + 90 + 9) % 360

    if adjusted_angle < 0: adjusted_angle += 360  # falls neigativer winkel entsteht

    # Hier werden von den 360 Grad jewils die ganzen Punkte den Grad zugeordnet (Index) jedes Feld hat 18 Grad
    # es wird die gradzahl dividiert durch 18, sodass wir die index stelle haben und dannach
    # wird mit dem max kontrolliert, sodass der index nicht unter 0 fällt
    # und bei min das der inex nicht über 19 geht
    segment_index = min(max(0, int(adjusted_angle // 18)), 19)
    # hier übergebe ich meiner Liste den Index und hole mir die echte Punktezahl
    base_points = SEGMENTS[segment_index]

    if R_TRIPLE_START <= r <= R_TRIPLE_END:
        return f"TRIPLE {base_points}", 3, base_points * 3, base_points, False, True
    elif R_DOUBLE_START <= r <= R_DOUBLE_END:
        return f"DOUBLE {base_points}", 2, base_points * 2, base_points, True, False
    else:
        return f"SINGLE {base_points}", 1, base_points, base_points, False, False


# PROJEKTION / ENTZEHRUNG:
# Wandelt einen Punkt aus dem schrägen 2D-Kamerabild mithilfe der Kalibrierungsmatrix H
# in die flache Draufsicht auf dem normierten 800x800 Dartboard um.
#
# Wofür benötigt?
# 1. Entzerrung schräger Kamerawinkel (Perspektivkorrektur).
# 2. Vereinheitlichung aller Kamerakoordinaten für Schnittpunkt-Berechnungen (get_intersection).
# 3. Hohe Performance: Rechnet nur 1 Punkt um, statt das ganze Videobild zu verzerren.
def transform_point(pt, H):
    # Erweitert (x,y) um eine 1 zu homogenen Koordinaten [x, y, 1],
    # damit Matrizen-Multiplikation mit der 3x3 Homographie-Matrix H möglich ist.
    p = np.array([pt[0], pt[1], 1.0])
    p_trans = H.dot(p)
    if p_trans[2] == 0: return (0, 0)
    # ERGÄNZUNG: Perspektiven-Division (Re-Normalisierung).
    # Teilt X und Y durch die homogene Skalierung Z (p_trans[2]),
    # um wieder echte 2D-Pixelkoordinaten zu erhalten.
    return (int(p_trans[0] / p_trans[2]), int(p_trans[1] / p_trans[2]))


# MULTI-KAMERA SCHNITTPUNKT-BERECHNUNG (Least Squares):
# Wandelt die Sichtlinien mehrerer Kameras in das Format Ax + By = C um und berechnet
# den optimalen Schnittpunkt (x, y) auf dem Board.

# WARUM 'lstsq' (Least Squares)?
# In der Realität schneiden sich 3 (oder mehr) Kameralinien wegen winziger Messfehler
# oder Kamerarauschen fast nie exakt in einem einzigen Pixel (sie bilden eher ein kleines Dreieck).
# 'lstsq' berechnet den fairsten Kompromiss: Es findet den einen Punkt auf dem Board,
# dessen Gesamtabstand zu ALLEN 3 Linien gleichzeitig so gering wie möglich ist.

# Wofür benötigt?
# 1. Messfehler-Toleranz: Findet bei 3+ Kameras den besten mathematischen Mittelpunkt.
# 2. Kombiniert alle Kamerasignale zu einer einzigen, präzisen Pfeilspitzen-Koordinate.

# Beispiel mit 2 Linien: (0,50)->(100,50) und (50,0)->(50,100) -> Schnittpunkt: (50, 50)
def get_intersection(
        lines):  # es wird für ein Schnittpunkt immer midenstens zwei linien benötigt. lines sind die Linien(Achsen) der Kameras
    if len(lines) < 2: return None  # len steht für length
    A, b = [], []
    # wir gehen hier alle linien durch und jede linie hat einen sart und enpunkt und dazu holen wir uns jeweils den x und y wert zum rechnen
    for p1, p2 in lines:
        x1, y1 = p1
        x2, y2 = p2
        # da es mit der normalen linien formel ein problem gibt also y = k * x + d (durch die homographie
        # Linien-Gleichung: Ax + By = C
        A_coef = y2 - y1
        B_coef = x1 - x2
        C_coef = A_coef * x1 + B_coef * y1
        A.append([A_coef, B_coef])
        b.append(C_coef)

    try:
        ans, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
        return (int(ans[0]), int(ans[1]))
    except:
        return None


# RECHTWINKLIGER ABSTAND PUNKT-ZU-LINIE (Lotabstand in Pixeln):
# Berechnet den kürzesten Abstand eines Punktes P(px, py) zu einer Geraden durch P1(x1, y1) und P2(x2, y2).
#
# DREI HAUPT-ANWENDUNGEN IM DART-SYSTEM:
# 1. GUI-Interaktion: Ermittelt bei einem Maus-Klick, welche Kamera-Linie der Nutzer anklicken wollte.
# 2. Kamera-Filterung: Identifiziert Ausreißer-Kameras, deren Sichtlinie zu weit vom Schnittpunkt abweicht.
# 3. Draht-Kollision: Prüft, ob eine Pfeilspitze direkt auf dem Metalldraht (Spider) sitzt.
#
# Beispiel: Punkt P(10, 10) und waagerechte Linie von (0,0) bis (10,0) -> Ergebnis: 10.0 Pixel
def point_line_distance(px, py, x1, y1, x2, y2):
    den = np.hypot(y2 - y1, x2 - x1)
    if den == 0: return float('inf')
    return abs((y2 - y1) * px - (x2 - x1) * py + x2 * y1 - y2 * x1) / den


# ---------------- 4. BILDVERARBEITUNG & SAM2 ----------------
def process_camera_dart(img_ref, img_new, H, predictor, cid=0):
    """ Führt Differenz, SAM2 und Achsenberechnung aus und erzeugt ein Visualisierungsbild """
    debug_img = img_new.copy()

    img_ref_blur = cv2.GaussianBlur(img_ref, (5, 5), 0)
    img_new_blur = cv2.GaussianBlur(img_new, (5, 5), 0)
    diff = cv2.absdiff(img_ref_blur, img_new_blur)

    gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray_diff, 35, 255, cv2.THRESH_BINARY)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(thresh, 8)
    if num_labels < 2:
        cv2.putText(debug_img, f"Kam {cid}: Keine Differenz", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        return None, debug_img

    largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    coords_diff = np.argwhere(labels == largest_label)

    mean_yx = coords_diff.mean(axis=0)
    centered = coords_diff - mean_yx
    cov = np.cov(centered.T)
    _, eigvecs = np.linalg.eigh(cov)
    principal_axis = eigvecs[:, -1]
    projections = centered @ principal_axis

    positive_points = []
    for p in (20, 50, 80):
        target = np.percentile(projections, p)
        idx = np.argmin(np.abs(projections - target))
        y, x = coords_diff[idx]
        positive_points.append([int(x), int(y)])

    h, w = img_new.shape[:2]
    negative_points = [
        [w // 8, h // 8],
        [7 * w // 8, h // 8],
        [w // 8, 7 * h // 8],
        [7 * w // 8, 7 * h // 8]
    ]
    input_point = np.array(positive_points + negative_points)
    input_label = np.array([1, 1, 1, 0, 0, 0, 0])

    predictor.set_image(cv2.cvtColor(img_new, cv2.COLOR_BGR2RGB))
    masks, scores, _ = predictor.predict(point_coords=input_point, point_labels=input_label, multimask_output=True)

    best_idx, best_val = -1, -1.0
    for i, (m, s) in enumerate(zip(masks, scores)):
        mm = m if m.ndim == 2 else m[0]
        c = np.argwhere(mm.astype(bool))
        if len(c) < 50: continue
        ev = np.linalg.eigvalsh(np.cov((c - c.mean(0)).T))
        elong = ev[-1] / max(ev[0], 1e-3)
        val = float(s) + 0.05 * np.log1p(elong)

        if val > best_val:
            best_val, best_idx = val, i

    if best_idx == -1:
        cv2.putText(debug_img, f"Kam {cid}: SAM2 Maske ungueltig", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255),
                    2)
        return None, debug_img

    mask = masks[best_idx].astype(bool)
    if mask.ndim == 3: mask = mask[0]

    coords_mask = np.argwhere(mask)
    if len(coords_mask) == 0:
        return None, debug_img

    # --- SAM2 MASKE VISUALISIEREN ---
    overlay = debug_img.copy()
    overlay[mask] = (0, 255, 0)  # Grünes transparentes Overlay
    debug_img = cv2.addWeighted(overlay, 0.4, debug_img, 0.6, 0)

    # Grüne Außenkontur
    mask_uint8 = (mask * 255).astype(np.uint8)
    contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(debug_img, contours, -1, (0, 255, 0), 2)

    # --- PROMPT-PUNKTE VISUALISIEREN ---
    # Positiv-Punkte (Grüne Kreise)
    for p in positive_points:
        cv2.circle(debug_img, (p[0], p[1]), 6, (0, 255, 0), -1)
        cv2.circle(debug_img, (p[0], p[1]), 8, (255, 255, 255), 1)

    # Negativ-Punkte (Rotes X)
    for p in negative_points:
        cv2.circle(debug_img, (p[0], p[1]), 5, (0, 0, 255), -1)
        cv2.drawMarker(debug_img, (p[0], p[1]), (255, 255, 255), cv2.MARKER_CROSS, 8, 1)

    # --- ACHSE & ENDPUNKTE VISUALISIEREN ---
    mean_yx = coords_mask.mean(axis=0)
    centered = coords_mask - mean_yx
    cov = np.cov(centered.T)
    _, eigvecs = np.linalg.eigh(cov)
    axis = eigvecs[:, -1]

    projs = centered @ axis
    idx_min, idx_max = np.argmin(projs), np.argmax(projs)
    y1, x1 = coords_mask[idx_min]
    y2, x2 = coords_mask[idx_max]

    cv2.line(debug_img, (x1, y1), (x2, y2), (0, 255, 255), 2)
    cv2.circle(debug_img, (x1, y1), 5, (255, 0, 255), -1)
    cv2.circle(debug_img, (x2, y2), 5, (255, 0, 255), -1)

    cv2.putText(debug_img, f"Kam {cid}: Pfeil erkannt", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    pt1_warp = transform_point((x1, y1), H)
    pt2_warp = transform_point((x2, y2), H)

    return (pt1_warp, pt2_warp), debug_img


# ---------------- 5. KALIBRIERUNG ----------------
def click_event_calibration(event, x, y, flags, param):
    global pts_tmp
    if event == cv2.EVENT_LBUTTONDOWN and len(pts_tmp) < 4:
        pts_tmp.append([float(x), float(y)])


def calibrate_camera(cap, cam_id):
    global pts_tmp
    pts_tmp = []
    window_name = f"Kalibrierung Kam {cam_id}"
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, click_event_calibration)

    print(f"\n=== KAMERA {cam_id} KALIBRIEREN ===")
    print("Klicke: 1. Double-20 | 2. Double-6 | 3. Double-3 | 4. Double-11")

    H = None
    while True:
        ret, frame = cap.read()
        if not ret: break
        display_frame = frame.copy()

        for i, pt in enumerate(pts_tmp):
            cv2.circle(display_frame, (int(pt[0]), int(pt[1])), 5, (0, 0, 255), -1)
            cv2.putText(display_frame, str(i + 1), (int(pt[0]) + 10, int(pt[1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (0, 0, 255), 2)

        if len(pts_tmp) >= 4:
            cv2.putText(display_frame, "ENTER: Bestaetigen | R: Reset", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (0, 255, 255), 2)
            src_pts = np.array(pts_tmp, dtype="float32")
            H, _ = cv2.findHomography(src_pts, DST_PTS)

        cv2.imshow(window_name, display_frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 13 and len(pts_tmp) == 4:
            break
        elif key == ord('r'):
            pts_tmp = []

    cv2.destroyWindow(window_name)
    return H


# ---------------- 6. MAIN LOOP ----------------
def main():
    global system_active, trigger_background, trigger_throw

    # 1. Starte den Flask-Server im Hintergrund
    threading.Thread(target=start_flask_server, daemon=True).start()
    print("=========================================")
    print("PYTHON BEREIT. Warte auf Start-Signal aus dem Browser...")
    print("Port 5000 ist offen.")
    print("=========================================")

    # --- DIE GROSSE ENDLOSSCHLEIFE ---
    while True:
        # Im Ruhezustand (Kameras aus) wartet Python hier ressourcenschonend
        if not system_active:
            cv2.waitKey(200)
            continue

        print("\n=== SYSTEM WIRD GESTARTET ===")
        caps = []
        for cid in CAM_IDS:
            cap = cv2.VideoCapture(cid)
            if cap.isOpened():
                caps.append((cid, cap))
            else:
                print(f"Warnung: Kamera {cid} konnte nicht geöffnet werden.")
                cap.release()

        if not caps:
            print("Keine Kameras gefunden! Gehe zurück in Ruhezustand.")
            system_active = False
            continue

        matrices = {}
        for cid, cap in caps:
            H = calibrate_camera(cap, cid)
            if H is not None: matrices[cid] = H

        print("\n=== SYSTEM BEREIT ===")
        print("'b' druecken = Leeres Board speichern (Background)")
        print("'t' druecken = Auswertung starten (Throw) nach einem Wurf")
        print("Kameras im Web-Dashboard ein-/ausschalten")
        print("'q' druecken = Beenden und in Ruhezustand wechseln")

        global_app_state['lines_data'] = []
        global_app_state['board_img'] = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)

        backgrounds = {}
        base_colors = [(255, 0, 0), (0, 255, 0), (255, 255, 0)]
        update_result_board_global()

        # Aktive Kamera-Schleife, läuft solange system_active = True ist
        debug_frames = []  # Einmalig vor der Schleife leeren

        while system_active:
            frames = {}
            display_frames = []
            warped_frames = []

            for cid, cap in caps:
                ret, frame = cap.read()
                if ret:
                    frames[cid] = frame
                    display_frames.append(cv2.resize(frame, (400, 300)))

                    if cid in matrices:
                        warped = cv2.warpPerspective(frame, matrices[cid], (SIZE, SIZE))
                        # Optional: Text ins Bild malen
                        cv2.putText(warped, f"Kam {cid} Homografie", (20, 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                        warped_frames.append(cv2.resize(warped, (400, 400)))

            # --- BILDER AN DAS WEB-DASHBOARD SENDEN ---
            if display_frames:
                dashboard_frames["live"] = np.hstack(display_frames)
                dashboard_frames["result"] = global_app_state['board_img']

            if warped_frames:
                dashboard_frames["homography"] = np.hstack(warped_frames)

            if debug_frames:
                dashboard_frames["debug"] = np.hstack(debug_frames)

            # --- TASTATUR & WEB-BUTTON ABFRAGE ---
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                system_active = False
                break

            elif key == ord('b') or trigger_background:
                backgrounds = frames.copy()
                print("Backgrounds gespeichert! Bereit fuer Wuerfe.")
                trigger_background = False  # Sofort zurücksetzen

            elif key == ord('t') or trigger_throw:
                trigger_throw = False  # Sofort zurücksetzen

                if not backgrounds:
                    print("FEHLER: Zuerst ein leeres Board speichern!")
                    continue

                print("\nAnalysiere Wurf...")
                global_app_state['lines_data'] = []
                debug_frames = []
                c_idx = 0

                for cid in frames:
                    if cid in matrices and cid in backgrounds:
                        line_pts, debug_img = process_camera_dart(
                            backgrounds[cid], frames[cid], matrices[cid], predictor, cid=cid
                        )
                        if line_pts:
                            print(f"Kamera {cid}: Achse gefunden.")
                            global_app_state['lines_data'].append({
                                'cid': cid,
                                'p1': line_pts[0],
                                'p2': line_pts[1],
                                'active': True,
                                'color': base_colors[c_idx % len(base_colors)]
                            })
                        else:
                            print(f"Kamera {cid}: Kein Pfeil erkannt.")

                        debug_frames.append(cv2.resize(debug_img, (400, 300)))
                    c_idx += 1

                # NEU: Das ist ein echter Wurf -> Kein Korrektur-Flag
                update_result_board_global(is_correction=False)

            elif key in [ord('1'), ord('2'), ord('3')]:
                cam_idx = key - ord('1')
                if cam_idx < len(caps):
                    target_cid = caps[cam_idx][0]
                    for line in global_app_state['lines_data']:
                        if line['cid'] == target_cid:
                            line['active'] = not line['active']
                            status = "DEAKTIVIERT" if not line['active'] else "AKTIVIERT"
                            print(f"Kamera {target_cid} per Tastatur {status}")

                            update_result_board_global(is_correction=True)
                            break

        # Cleanup Kameras (wird ausgeführt, wenn 'q' gedrückt oder das Stop-Signal empfangen wurde)
        for _, cap in caps: cap.release()
        cv2.destroyAllWindows()
        print("\n=== Kameras gestoppt. Python wartet wieder auf Start-Signal ===")


if __name__ == "__main__":
    main()