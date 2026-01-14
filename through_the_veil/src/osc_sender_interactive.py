"""
Émetteur OSC interactif
Lance APRÈS le récepteur dans un autre terminal
"""
import cv2
import numpy as np
import time
from pythonosc import udp_client

print("\n" + "=" * 60)
print("📡 ÉMETTEUR OSC - Through the Veil")
print("=" * 60)

# Configuration OSC
UNREAL_IP = "127.0.0.1"
UNREAL_PORT = 8000

# Crée le client OSC
try:
    client = udp_client.SimpleUDPClient(UNREAL_IP, UNREAL_PORT)
    print("✅ Client OSC créé")
    print("   Destination : {}:{}".format(UNREAL_IP, UNREAL_PORT))
except Exception as e:
    print("❌ Erreur création client OSC : {}".format(e))
    exit()

# Configuration fenêtre
WIDTH, HEIGHT = 800, 600
BRUSH_SIZE = 60
SEND_RATE = 30  # Hz

# Canvas
canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

# État
hand_detected = False
hand_x, hand_y = WIDTH // 2, HEIGHT // 2
frame_count = 0
messages_sent = 0
start_time = time.time()
last_send_time = time.time()

def mouse_callback(event, x, y, flags, param):
    """Gère les événements souris"""
    global hand_detected, hand_x, hand_y
    
    hand_x, hand_y = x, y
    
    if flags & cv2.EVENT_FLAG_LBUTTON:
        hand_detected = True
    else:
        hand_detected = False

cv2.namedWindow('OSC Sender - Interactive')
cv2.setMouseCallback('OSC Sender - Interactive', mouse_callback)

print("\nCONTRÔLES :")
print("  - Bouge la souris")
print("  - Maintiens clic gauche = envoie données")
print("  - 'q' = quitter")
print("=" * 60 + "\n")
print("✅ Prêt à envoyer !\n")

while True:
    # Efface
    canvas[:] = 30
    
    # Grille
    for i in range(0, WIDTH, 100):
        cv2.line(canvas, (i, 0), (i, HEIGHT), (50, 50, 50), 1)
    for i in range(0, HEIGHT, 100):
        cv2.line(canvas, (0, i), (WIDTH, i), (50, 50, 50), 1)
    
    # Normalise
    norm_x = hand_x / WIDTH
    norm_y = hand_y / HEIGHT
    
    # Vérifie si on peut envoyer (rate limiting)
    current_time = time.time()
    can_send = (current_time - last_send_time) >= (1.0 / SEND_RATE)
    
    # Envoie les données OSC
    if can_send:
        try:
            # Envoie l'état de détection
            client.send_message("/hand/detected", int(hand_detected))
            
            # Si main détectée, envoie position et intensité
            if hand_detected:
                client.send_message("/hand/position", [float(norm_x), float(norm_y)])
                client.send_message("/hand/intensity", 1.0)
                messages_sent += 3
            else:
                messages_sent += 1
            
            last_send_time = current_time
            
            # Indicateur visuel d'envoi
            if hand_detected:
                cv2.circle(canvas, (WIDTH - 50, 50), 15, (0, 255, 0), -1)
        
        except Exception as e:
            print("❌ Erreur envoi OSC : {}".format(e))
    
    # Dessine la main
    if hand_detected:
        color = (0, 255, 0)
        status = "MAIN DÉTECTÉE - ENVOI OSC"
        cv2.circle(canvas, (hand_x, hand_y), BRUSH_SIZE, color, -1)
        cv2.circle(canvas, (hand_x, hand_y), BRUSH_SIZE + 5, (255, 255, 255), 2)
    else:
        color = (100, 100, 100)
        status = "Pas de main"
        cv2.circle(canvas, (hand_x, hand_y), BRUSH_SIZE, color, 2)
    
    # Croix
    cv2.line(canvas, (hand_x - 10, hand_y), (hand_x + 10, hand_y), (255, 255, 255), 2)
    cv2.line(canvas, (hand_x, hand_y - 10), (hand_x, hand_y + 10), (255, 255, 255), 2)
    
    # Infos à l'écran
    cv2.putText(canvas, status, (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    
    cv2.putText(canvas, "Position: ({}, {})".format(hand_x, hand_y), (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    cv2.putText(canvas, "Normalisé: x={:.3f}, y={:.3f}".format(norm_x, norm_y), (20, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    cv2.putText(canvas, "Messages OSC envoyés: {}".format(messages_sent), (20, 140),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
    
    # FPS
    frame_count += 1
    elapsed = time.time() - start_time
    fps = frame_count / elapsed if elapsed > 0 else 0
    
    cv2.putText(canvas, "FPS: {:.1f}".format(fps), (WIDTH - 120, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 100), 2)
    
    # OSC Info
    cv2.putText(canvas, "OSC -> {}:{}".format(UNREAL_IP, UNREAL_PORT), (20, HEIGHT - 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    
    # Affiche
    cv2.imshow('OSC Sender - Interactive', canvas)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

cv2.destroyAllWindows()

print("\n" + "=" * 60)
print("📊 STATISTIQUES")
print("=" * 60)
print("Frames totales : {}".format(frame_count))
print("Messages OSC envoyés : {}".format(messages_sent))
print("FPS moyen : {:.1f}".format(fps))
print("=" * 60)
print("✅ Émetteur arrêté")