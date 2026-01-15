import cv2

print("🔍 TEST DE LA CAMÉRA")
print("=" * 60)

# Essaye d'ouvrir la caméra
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Impossible d'ouvrir la caméra")
    print("   Vérifie qu'elle est branchée")
    print("   Essaye camera_id = 1 ou 2 si ça ne marche pas")
    exit()

# Récupère les infos
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))

print(f"✅ Caméra détectée !")
print(f"   Résolution : {width}x{height}")
print(f"   FPS : {fps}")
print(f"\n📸 Fenêtre ouverte - Appuie sur 'q' pour quitter\n")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Erreur de lecture")
        break
    
    # Affiche les infos sur l'image
    cv2.putText(frame, f"{width}x{height} @ {fps}fps", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    cv2.imshow('Test Camera', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

print("\n✅ Test terminé")