import cv2
import numpy as np
import os
import torch
import requests
import threading
import time
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

# --- NEU: GESCHWINDIGKEIT ---
# Größe des SAM2-Modells. Kleinere Modelle sind auf der CPU deutlich schneller:
# "large" (am genauesten, am langsamsten) | "base_plus" | "small" | "tiny" (am schnellsten)
# Die passende .pt-Datei muss im Ordner sam_checkpoints liegen, sonst wird automatisch "large" verwendet.
SAM2_MODEL_SIZE = "small"
SAM2_MODELS = {
    "large": ("sam2.1_hiera_large.pt", "configs/sam2.1/sam2.1_hiera_l.yaml"),
    "base_plus": ("sam2.1_hiera_base_plus.pt", "configs/sam2.1/sam2.1_hiera_b+.yaml"),
    "small": ("sam2.1_hiera_small.pt", "configs/sam2.1/sam2.1_hiera_s.yaml"),
    "tiny": ("sam2.1_hiera_tiny.pt", "configs/sam2.1/sam2.1_hiera_t.yaml"),
}
_ckpt_name, _ckpt_cfg = SAM2_MODELS.get(SAM2_MODEL_SIZE, SAM2_MODELS["large"])
_ckpt_path = os.path.join(BASE_DIR, "sam_checkpoints", _ckpt_name)
if os.path.exists(_ckpt_path):
    CHECKPOINT, MODEL_CFG = _ckpt_path, _ckpt_cfg
else:
    print(f"⚠️ {_ckpt_name} nicht gefunden – verwende sam2.1_hiera_large.pt")
    SAM2_MODEL_SIZE = "large"

# Schnellmodus: Ist der Differenz-Fleck eindeutig länglich (= Pfeil), wird die Achse direkt
# aus dem Differenzbild berechnet und SAM2 übersprungen (Millisekunden statt Sekunden).
# Nur bei unklaren Bildern (Hand, großer Schatten, mehrere Flecken) wird SAM2 als Rückfallebene genutzt.
USE_FAST_MODE = True
FAST_MIN_ELONGATION = 15.0  # Wie länglich der Fleck mindestens sein muss (Pfeil: sehr länglich, Hand/Schatten: rundlich)
FAST_MIN_AREA = 150  # Mindestgröße des Flecks in Pixeln (kleiner = nur Rauschen)
FAST_MIN_SHARE = 0.6  # Anteil des größten Flecks an allen Differenz-Pixeln (darunter = unklares Bild)

# --- NEU: AUTOMATIK-MODUS (Ruhe -> Bewegung -> Ruhe) ---
# Ablauf: Solange die Scheibe ruhig ist, wird laufend der Hintergrund übernommen.
# Wird eine Bewegung erkannt, wartet das System, bis wieder Ruhe ist, und vergleicht dann mit dem Hintergrund:
#   kleine Veränderung + kurze Bewegung = Pfeil -> automatisch auswerten
#   große Veränderung oder lange Bewegung = Hand / Pfeile ziehen -> kein Wurf, nur neuer Hintergrund
# Alle Werte beziehen sich auf ein verkleinertes Graubild (AUTO_ANALYSIS_SIZE) und werden als Anteil der Pixel angegeben.
AUTO_ANALYSIS_SIZE = (320, 240)  # Auf diese Größe wird für die Bewegungserkennung verkleinert (schneller)
AUTO_MOTION_PIXEL_THRESHOLD = 25  # Grauwert-Unterschied zwischen zwei Frames, ab dem ein Pixel als "bewegt" zählt
AUTO_MOTION_MIN_RATIO = 0.002  # Anteil bewegter Pixel (0.2 %), ab dem es als Bewegung gilt
AUTO_STABLE_TIME = 0.7  # Sekunden ohne Bewegung = Bild ist ruhig (Pfeil zittert nicht mehr)
AUTO_CHANGE_PIXEL_THRESHOLD = 35  # Grauwert-Unterschied zum Hintergrund, ab dem ein Pixel als "verändert" zählt
AUTO_CHANGE_MIN_RATIO = 0.0015  # Mindest-Veränderung zum Hintergrund für einen Pfeil (darunter = nichts passiert)
AUTO_CHANGE_MAX_RATIO = 0.08  # Mehr Veränderung als 8 % = Hand / Person / Pfeile entfernt -> kein Wurf
AUTO_MAX_THROW_MOTION = 1.5  # Bewegung länger als 1,5 s = jemand an der Scheibe (z.B. Pfeile ziehen) -> kein Wurf
AUTO_BG_REFRESH_TIME = 2.0  # Alle 2 s Ruhe wird geprüft und der Hintergrund aufgefrischt (z.B. Lichtänderung)
AUTO_SETTLE_TIME = 2.0  # Nach einer großen Veränderung (Pfeile ziehen) erst nach 2 s völliger Ruhe wieder Würfe werten

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
    # Gesperrt: Kein Kamerawurf vorhanden (z.B. nach manuellem Klick im Browser oder neuem Hintergrund)
    if len(global_app_state['lines_data']) == 0:
        print(f"Kamera {cid} kann nicht umgeschaltet werden: Kameras gesperrt bis zum nächsten Wurf.")
        return jsonify({"status": "locked", "cid": cid, "found": False})

    found = False
    for line in global_app_state['lines_data']:
        if line['cid'] == cid:
            line['active'] = not line['active']
            status = "DEAKTIVIERT" if not line['active'] else "AKTIVIERT"
            print(f"Kamera {cid} per Web-Klick {status}")
            found = True
            break

    # Nur neu berechnen, wenn sich wirklich etwas geändert hat (Kamera ohne erkannte Linie -> keine Korrektur)
    if found:
        update_result_board_global(is_correction=True)
    return jsonify({"status": "success", "cid": cid, "found": found})


@app.route('/api/camera/states')
def camera_states():
    """ Liefert dem Web-Dashboard den aktuellen Zustand der Kamera-Buttons """
    # has_throw = False -> Buttons gesperrt (kein Kamerawurf oder manueller Eingriff)
    # cams: {"0": True/False, ...} -> nur Kameras, die beim letzten Wurf eine Linie erkannt haben
    cams = {}
    for line in global_app_state['lines_data']:
        cams[str(line['cid'])] = line['active']
    return jsonify({
        "has_throw": len(global_app_state['lines_data']) > 0,
        "cams": cams
    })


trigger_background = False
trigger_throw = False

# NEU: Automatik-Modus (False = Manuell mit Buttons, True = Automatisch per Bewegungserkennung)
auto_mode = False
auto_status = "Manueller Modus"  # Text für die Statusanzeige im Dashboard


def set_auto_status(text):
    """ Setzt den Statustext, den das Dashboard im Automatik-Modus anzeigt """
    global auto_status
    auto_status = text


@app.route('/api/mode')
def get_mode():
    """ Liefert dem Dashboard den aktuellen Modus und Status """
    status = auto_status if system_active else "Kameras nicht gestartet"
    return jsonify({"mode": "auto" if auto_mode else "manual", "status": status})


@app.route('/api/mode/<mode>', methods=['POST'])
def set_mode(mode):
    """ Schaltet zwischen Manuell und Automatisch um """
    global auto_mode
    if mode not in ("auto", "manual"):
        return jsonify({"status": "unbekannter Modus"}), 400
    auto_mode = (mode == "auto")
    set_auto_status("Warte auf ruhiges Bild ..." if auto_mode else "Manueller Modus")
    print(f"\n⚙️ MODUS: {'AUTOMATISCH' if auto_mode else 'MANUELL'}")
    return jsonify({"mode": mode})


@app.route('/api/action/background')
def web_background():
    global trigger_background
    # NEU: Im Automatik-Modus wird der Hintergrund automatisch gesetzt
    if auto_mode:
        return jsonify({"status": "Automatik aktiv - Button ignoriert"})
    trigger_background = True
    return jsonify({"status": "Background angefordert"})


@app.route('/api/action/throw')
def web_throw():
    global trigger_throw
    # NEU: Im Automatik-Modus wird der Wurf automatisch ausgewertet
    if auto_mode:
        return jsonify({"status": "Automatik aktiv - Button ignoriert"})
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

    # --- NEU: SCHNELLMODUS (ohne SAM2) ---
    # Wenn der größte Differenz-Fleck klar länglich ist, ist das mit hoher Sicherheit der Pfeil.
    # Dann reicht die Hauptachse aus dem Differenzbild -> SAM2 (mehrere Sekunden) wird übersprungen.
    if USE_FAST_MODE:
        diff_area = len(coords_diff)
        total_diff = int(np.count_nonzero(thresh))
        ev_diff = np.linalg.eigvalsh(cov)
        elongation = ev_diff[-1] / max(ev_diff[0], 1e-3)
        share = diff_area / max(total_diff, 1)

        if diff_area >= FAST_MIN_AREA and elongation >= FAST_MIN_ELONGATION and share >= FAST_MIN_SHARE:
            idx_min, idx_max = np.argmin(projections), np.argmax(projections)
            y1, x1 = coords_diff[idx_min]
            y2, x2 = coords_diff[idx_max]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            # Differenz-Fleck türkis einfärben, Achse und Endpunkte einzeichnen
            overlay = debug_img.copy()
            overlay[labels == largest_label] = (255, 255, 0)
            debug_img = cv2.addWeighted(overlay, 0.4, debug_img, 0.6, 0)
            cv2.line(debug_img, (x1, y1), (x2, y2), (0, 255, 255), 2)
            cv2.circle(debug_img, (x1, y1), 5, (255, 0, 255), -1)
            cv2.circle(debug_img, (x2, y2), 5, (255, 0, 255), -1)
            cv2.putText(debug_img, f"Kam {cid}: Schnellmodus", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (255, 255, 0), 2)

            print(f"Kamera {cid}: Schnellmodus (Laenglichkeit {elongation:.0f}, Anteil {share:.0%})")
            pt1_warp = transform_point((x1, y1), H)
            pt2_warp = transform_point((x2, y2), H)
            return (pt1_warp, pt2_warp), debug_img

        print(f"Kamera {cid}: Differenz unklar (Laenglichkeit {elongation:.1f}, Anteil {share:.0%}) -> SAM2")

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


# ---------------- NEU: AUTOMATIK-MODUS HILFSFUNKTIONEN ----------------
def auto_small_gray(frame):
    """ Verkleinert ein Kamerabild und macht es grau + leicht unscharf (für schnelle Bewegungserkennung) """
    small = cv2.resize(frame, AUTO_ANALYSIS_SIZE)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    return cv2.GaussianBlur(gray, (5, 5), 0)


def auto_changed_ratio(gray_a, gray_b, pixel_threshold):
    """ Anteil der Pixel (0.0 - 1.0), die sich zwischen zwei Graubildern stärker als pixel_threshold unterscheiden """
    diff = cv2.absdiff(gray_a, gray_b)
    _, th = cv2.threshold(diff, pixel_threshold, 255, cv2.THRESH_BINARY)
    return cv2.countNonZero(th) / th.size


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

        # NEU: Zustand für den Automatik-Modus
        auto_bg = None  # Hintergrund vor dem nächsten Wurf (pro Kamera)
        auto_prev_gray = {}  # Letztes Graubild pro Kamera (für die Bewegungserkennung)
        auto_motion_active = False  # Läuft gerade eine Bewegung?
        auto_motion_start = 0.0  # Wann hat die Bewegung begonnen?
        auto_last_motion = time.time()  # Wann war zuletzt Bewegung?
        auto_last_check = time.time()  # Wann wurde zuletzt mit dem Hintergrund verglichen?
        auto_was_active = False  # War der Automatik-Modus im letzten Durchlauf schon aktiv?
        auto_settling = False  # Nach großer Veränderung: warten, bis die Scheibe wieder frei und ruhig ist
        if auto_mode:
            set_auto_status("Warte auf ruhiges Bild ...")

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

            # --- NEU: AUTOMATIK-MODUS (Ruhe -> Bewegung -> Ruhe) ---
            if auto_mode and frames:
                now = time.time()

                # Gerade auf Automatisch umgeschaltet -> Zustand neu beginnen
                if not auto_was_active:
                    auto_bg = None
                    auto_prev_gray = {}
                    auto_motion_active = False
                    auto_last_motion = now
                    auto_last_check = now
                    auto_settling = False
                    auto_was_active = True
                    set_auto_status("Warte auf ruhiges Bild ...")

                # 1. Bewegung erkennen: aktuelles Bild mit dem vorherigen Bild jeder Kamera vergleichen
                gray_now = {cid: auto_small_gray(f) for cid, f in frames.items()}
                motion_ratio = 0.0
                for cid, g in gray_now.items():
                    if cid in auto_prev_gray:
                        motion_ratio = max(motion_ratio,
                                           auto_changed_ratio(auto_prev_gray[cid], g, AUTO_MOTION_PIXEL_THRESHOLD))
                auto_prev_gray = gray_now

                if motion_ratio >= AUTO_MOTION_MIN_RATIO:
                    auto_last_motion = now
                    if not auto_motion_active:
                        auto_motion_active = True
                        auto_motion_start = now
                        set_auto_status("🟡 Bewegung erkannt ...")

                # 2. Ist das Bild wieder ruhig?
                stable = (now - auto_last_motion) >= AUTO_STABLE_TIME

                if stable and auto_bg is None:
                    # Erster ruhiger Moment -> Starthintergrund übernehmen
                    auto_bg = frames.copy()
                    auto_motion_active = False
                    auto_last_check = now
                    print("AUTO: Hintergrund gespeichert. Bereit fuer Wuerfe.")
                    set_auto_status("🟢 Bereit – warte auf Wurf")

                elif stable and auto_settling:
                    # Nach großer Veränderung: nur den Hintergrund nachführen (kein Wurf),
                    # bis die Scheibe lange genug völlig ruhig ist (Person ist wieder weg)
                    auto_bg = frames.copy()
                    auto_motion_active = False
                    if now - auto_last_motion >= AUTO_SETTLE_TIME:
                        auto_settling = False
                        auto_last_check = now
                        print("AUTO: Scheibe wieder ruhig. Bereit fuer Wuerfe.")
                        set_auto_status("🟢 Bereit – warte auf Wurf")

                elif stable and auto_bg is not None and (
                        auto_motion_active or now - auto_last_check >= AUTO_BG_REFRESH_TIME):
                    # 3. Ruhiges Bild mit dem Hintergrund vergleichen und entscheiden, was passiert ist
                    motion_duration = (auto_last_motion - auto_motion_start) if auto_motion_active else 0.0
                    change_ratio = 0.0
                    for cid, g in gray_now.items():
                        if cid in auto_bg:
                            change_ratio = max(change_ratio,
                                               auto_changed_ratio(auto_small_gray(auto_bg[cid]), g,
                                                                  AUTO_CHANGE_PIXEL_THRESHOLD))

                    if change_ratio < AUTO_CHANGE_MIN_RATIO:
                        # Nichts Relevantes verändert (z.B. Schatten, leichte Lichtänderung) -> Hintergrund auffrischen
                        if auto_motion_active:
                            print(f"AUTO: Bewegung ohne Veraenderung (Aenderung {change_ratio:.2%}) -> kein Wurf")
                        auto_bg = frames.copy()
                        set_auto_status("🟢 Bereit – warte auf Wurf")

                    elif change_ratio > AUTO_CHANGE_MAX_RATIO or motion_duration > AUTO_MAX_THROW_MOTION:
                        # Große Veränderung oder lange Bewegung -> Hand / Person / Pfeile entfernt -> kein Wurf
                        print(f"AUTO: Grosse Veraenderung (Aenderung {change_ratio:.2%}, "
                              f"Bewegung {motion_duration:.1f} s) -> kein Wurf, neuer Hintergrund")
                        auto_bg = frames.copy()
                        # Alte Kameralinien verwerfen (wie beim manuellen Hintergrund speichern)
                        global_app_state['lines_data'] = []
                        update_result_board_global(is_correction=False)
                        auto_settling = True  # Erst wieder werten, wenn die Scheibe frei und ruhig ist
                        set_auto_status("⚪ Große Veränderung (z.B. Pfeile entfernt) – warte bis Scheibe frei ist")

                    else:
                        # Kleine Veränderung nach kurzer Bewegung -> Pfeil -> automatisch auswerten
                        print(f"AUTO: Wurf erkannt (Aenderung {change_ratio:.2%}, "
                              f"Bewegung {motion_duration:.1f} s) -> Auswertung")
                        backgrounds = auto_bg  # Hintergrund VOR dem Wurf für die Auswertung
                        auto_bg = frames.copy()  # Bild MIT Pfeil = Hintergrund für den nächsten Pfeil
                        trigger_throw = True  # Löst unten die normale Wurfauswertung aus
                        set_auto_status("🔵 Werte Wurf aus ...")

                    auto_motion_active = False
                    auto_last_check = now

            elif not auto_mode and auto_was_active:
                # Zurück auf Manuell -> beim nächsten Einschalten frisch beginnen
                auto_was_active = False

            # --- TASTATUR & WEB-BUTTON ABFRAGE ---
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                system_active = False
                break

            elif key == ord('b') or trigger_background:
                backgrounds = frames.copy()
                print("Backgrounds gespeichert! Bereit fuer Wuerfe.")
                trigger_background = False  # Sofort zurücksetzen

                # Neuer Hintergrund = vorheriger Wurf ist abgeschlossen.
                # Alte Kameralinien verwerfen, damit kein alter Wurf mehr korrigiert werden kann
                # und beim nächsten Wurf alle Kameras wieder aktiv starten.
                global_app_state['lines_data'] = []
                update_result_board_global(is_correction=False)

            elif key == ord('t') or trigger_throw:
                trigger_throw = False  # Sofort zurücksetzen

                if not backgrounds:
                    print("FEHLER: Zuerst ein leeres Board speichern!")
                    continue

                print("\nAnalysiere Wurf...")
                global_app_state['lines_data'] = []
                debug_frames = []
                c_idx = 0
                t_total = time.perf_counter()  # NEU: Zeitmessung für den ganzen Wurf

                for cid in frames:
                    if cid in matrices and cid in backgrounds:
                        t_cam = time.perf_counter()  # NEU: Zeitmessung pro Kamera
                        line_pts, debug_img = process_camera_dart(
                            backgrounds[cid], frames[cid], matrices[cid], predictor, cid=cid
                        )
                        print(f"⏱️ Kamera {cid}: {time.perf_counter() - t_cam:.2f} s")
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

                print(f"⏱️ Auswertung gesamt: {time.perf_counter() - t_total:.2f} s (SAM2-Modell: {SAM2_MODEL_SIZE})")

                # NEU: Das ist ein echter Wurf -> Kein Korrektur-Flag
                update_result_board_global(is_correction=False)

                # NEU: Im Automatik-Modus wieder auf den nächsten Pfeil warten
                if auto_mode:
                    set_auto_status("🟢 Bereit – warte auf Wurf")

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