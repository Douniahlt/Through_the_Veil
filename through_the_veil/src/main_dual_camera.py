"""
Application principale Through the Veil - Version Dual Camera
Détecte avec 2 caméras:
- Caméra TOP (vue du haut): surveillance du franchissement de seuil
- Caméra FRONT (vue de face): interaction précise quand seuil franchi
"""
import cv2
import numpy as np
import time
import sys
import os

# Ajoute le chemin parent pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dual_camera_threshold import DualCameraThreshold

def main():
    print("\n" + "="*70)
    print("🎭 THROUGH THE VEIL - Dual Camera Threshold System")
    print("="*70)
    print("\nConfiguration:")
    print("  📹 Caméra 1 (TOP) - Vue du HAUT : Surveillance du seuil")
    print("  📹 Caméra 0 (FRONT) - Vue de FACE : Interaction précise")
    print("\nFonctionnement:")
    print("  1. La caméra TOP surveille en permanence")
    print("  2. Quand la main franchit le seuil (ligne rouge)")
    print("  3. La caméra FRONT s'active pour l'interaction")
    print("  4. Mode DRAW (index) ou ERASE (main ouverte)")
    print("="*70 + "\n")
    
    # Demande les IDs des caméras
    print("Configuration des caméras:")
    try:
        cam_top_id = int(input("ID Caméra TOP (vue du haut) [défaut: 1]: ") or "1")
        cam_front_id = int(input("ID Caméra FRONT (vue de face) [défaut: 0]: ") or "0")
        threshold = float(input("Seuil de franchissement (0.0-1.0) [défaut: 0.5]: ") or "0.5")
    except ValueError:
        print("❌ Valeur invalide, utilisation des valeurs par défaut")
        cam_top_id = 1
        cam_front_id = 0
        threshold = 0.5
    
    print(f"\n✅ Configuration: TOP={cam_top_id}, FRONT={cam_front_id}, Seuil={threshold}")
    
    # Créer et lancer le système
    system = DualCameraThreshold(cam_top_id=cam_top_id, cam_front_id=cam_front_id)
    system.set_threshold(threshold)
    system.run()


if __name__ == "__main__":
    main()
