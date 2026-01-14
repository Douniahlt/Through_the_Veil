"""
Test de détection SANS caméra
On crée des images synthétiques pour tester
"""
import cv2
import numpy as np

print(" THROUGH THE VEIL - Test détection simple")
print("=" * 60)

# Crée une image noire (comme un fond)
width, height = 640, 480
frame = np.zeros((height, width, 3), dtype=np.uint8)

print("✅ Image créée : {}x{}".format(width, height))

# Simule une "main" = un cercle blanc
hand_x, hand_y = 320, 240  # Centre de l'image
hand_radius = 50

cv2.circle(frame, (hand_x, hand_y), hand_radius, (255, 255, 255), -1)

print("✅ 'Main' simulée à la position ({}, {})".format(hand_x, hand_y))

# Convertit en niveaux de gris (comme pour la détection)
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

# Trouve les contours (zones blanches)
contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

print("✅ Nombre de contours détectés : {}".format(len(contours)))

if len(contours) > 0:
    # Prend le plus grand contour
    biggest_contour = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(biggest_contour)
    
    # Calcule le centre
    M = cv2.moments(biggest_contour)
    if M["m00"] != 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        
        print("✅ Centre détecté : ({}, {})".format(cx, cy))
        print("✅ Aire : {} pixels".format(int(area)))
        
        # Normalise les coordonnées (0.0 à 1.0)
        norm_x = cx / width
        norm_y = cy / height
        
        print("✅ Position normalisée : x={:.3f}, y={:.3f}".format(norm_x, norm_y))
        
        # Dessine le résultat
        cv2.circle(frame, (cx, cy), 10, (0, 255, 0), -1)
        cv2.putText(frame, "Main detectee", (cx - 50, cy - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

# Sauvegarde l'image
cv2.imwrite('test_detection.png', frame)
print("\n✅ Image sauvegardée : test_detection.png")

print("\n" + "=" * 60)
print("🎉 Test terminé avec succès !")
print("=" * 60)