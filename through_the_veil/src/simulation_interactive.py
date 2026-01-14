"""
Simulation interactive - Bouge la souris pour simuler la main
"""
import cv2
import numpy as np
import time

print("\n🎭 THROUGH THE VEIL - Simulation Interactive")
print("=" * 60)
print("CONTRÔLES :")
print("  - Bouge la souris pour simuler la main")
print("  - Clic gauche maintenu = main détectée")
print("  - 'q' = quitter")
print("  - 's' = screenshot")
print("=" * 60 + "\n")

# Configuration
WIDTH, HEIGHT = 800, 600
BRUSH_SIZE = 60

# Création du canvas
canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

# État
hand_detected = False
hand_x, hand_y = WIDTH // 2, HEIGHT // 2
frame_count = 0
start_time = time.time()

def mouse_callback(event, x, y, flags, param):
    """Appelé quand la souris bouge"""
    global hand_detected, hand_x, hand_y
    
    # Met à jour la position
    hand_x, hand_y = x, y
    
    # Détecte si bouton gauche pressé
    if flags & cv2.EVENT_FLAG_LBUTTON:
        hand_detected = True
    else:
        hand_detected = False

# Crée la fenêtre
cv2.namedWindow('Simulation Interactive')
cv2.setMouseCallback('Simulation Interactive', mouse_callback)

print("✅ Fenêtre créée - Bouge ta souris !\n")

while True:
    # Efface le canvas
    canvas[:] = 30  # Gris très sombre
    
    # Grille de fond
    for i in range(0, WIDTH, 100):
        cv2.line(canvas, (i, 0), (i, HEIGHT), (50, 50, 50), 1)
    for i in range(0, HEIGHT, 100):
        cv2.line(canvas, (0, i), (WIDTH, i), (50, 50, 50), 1)
    
    # Normalise la position (0.0 à 1.0)
    norm_x = hand_x / WIDTH
    norm_y = hand_y / HEIGHT
    
    # Dessine la "main"
    if hand_detected:
        color = (0, 255, 0)  # Vert si détectée
        status = "MAIN DÉTECTÉE"
        
        # Cercle plein
        cv2.circle(canvas, (hand_x, hand_y), BRUSH_SIZE, color, -1)
        # Contour
        cv2.circle(canvas, (hand_x, hand_y), BRUSH_SIZE + 5, (255, 255, 255), 2)
        
    else:
        color = (100, 100, 100)  # Gris si pas détectée
        status = "Pas de main"
        
        # Juste un contour
        cv2.circle(canvas, (hand_x, hand_y), BRUSH_SIZE, color, 2)
    
    # Croix au centre
    cv2.line(canvas, (hand_x - 10, hand_y), (hand_x + 10, hand_y), (255, 255, 255), 2)
    cv2.line(canvas, (hand_x, hand_y - 10), (hand_x, hand_y + 10), (255, 255, 255), 2)
    
    # Affiche le statut
    cv2.putText(canvas, status, (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    
    # Affiche les coordonnées
    coord_text = "Position: ({}, {})".format(hand_x, hand_y)
    cv2.putText(canvas, coord_text, (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    
    norm_text = "Normalisé: x={:.3f}, y={:.3f}".format(norm_x, norm_y)
    cv2.putText(canvas, norm_text, (20, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    
    # Calcule les FPS
    frame_count += 1
    elapsed = time.time() - start_time
    fps = frame_count / elapsed if elapsed > 0 else 0
    
    fps_text = "FPS: {:.1f}".format(fps)
    cv2.putText(canvas, fps_text, (WIDTH - 120, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 100), 2)
    
    # Aide en bas
    cv2.putText(canvas, "Maintiens clic gauche pour détecter", (20, HEIGHT - 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
    cv2.putText(canvas, "'q' = quitter | 's' = screenshot", (20, HEIGHT - 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
    
    # Simule l'envoi OSC (juste affichage pour l'instant)
    if hand_detected:
        osc_text = "OSC: /hand/position [{:.3f}, {:.3f}]".format(norm_x, norm_y)
        cv2.putText(canvas, osc_text, (20, HEIGHT - 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    
    # Affiche
    cv2.imshow('Simulation Interactive', canvas)
    
    # Gestion clavier
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        print("\n👋 Fermeture...")
        break
    elif key == ord('s'):
        filename = 'screenshot_{}.png'.format(int(time.time()))
        cv2.imwrite(filename, canvas)
        print("📸 Screenshot sauvegardé : {}".format(filename))

cv2.destroyAllWindows()

print("\n✅ Simulation terminée")
print("   Total frames : {}".format(frame_count))
print("   FPS moyen : {:.1f}".format(fps))
print("\n" + "=" * 60)