"""
Application principale Through the Veil avec Calibration
Détecte 1 main et applique l'homographie pour mapper correctement la vitre
"""
import cv2
import numpy as np
import time
import sys
import os
import json

# Ajoute le chemin parent pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_manager import ConfigManager
from osc_sender import OSCSender
from hand_detector import HandDetector

class ThroughTheVeilCalibrated:
    def __init__(self, calibration_file='calibration.json'):
        print("\n" + "="*60)
        print("🎭 THROUGH THE VEIL - Interactive Installation (Calibrated)")
        print("="*60 + "\n")
        
        # Charge la configuration
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.json')
        self.config = ConfigManager(config_path)
        
        # Initialise OSC
        osc_config = self.config.get('osc')
        self.osc = OSCSender(osc_config['unreal_ip'], osc_config['unreal_port'])
        self.osc.set_send_rate(osc_config['send_rate'])
        
        # Initialise le détecteur de main (1 seule main)
        self.detector = HandDetector(max_hands=1)
        
        # Charge la calibration
        self.homography_matrix = None
        self.calibration_points = None
        self.load_calibration(calibration_file)
        
        # État
        self.running = False
        self.camera = None
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()
        
        # Lissage de position
        self.smoothing = 0.3
        self.smooth_x = 0.5
        self.smooth_y = 0.5
        
        print("✅ Initialisation terminée\n")
    
    def load_calibration(self, filepath):
        """Charge la calibration depuis un fichier JSON"""
        if not os.path.exists(filepath):
            print(f"⚠️  Pas de fichier de calibration trouvé : {filepath}")
            print("   Lance d'abord calibration_tool.py pour calibrer")
            print("   L'application fonctionnera sans mapping (coordonnées brutes)")
            return False
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.homography_matrix = np.array(data['homography_matrix'], dtype=np.float32)
            self.calibration_points = data['calibration_points']
            
            print("✅ Calibration chargée !")
            print(f"   Points de calibration : {self.calibration_points}")
            return True
        
        except Exception as e:
            print(f"❌ Erreur lors du chargement de la calibration : {e}")
            return False
    
    def init_camera(self, camera_id=0):
        """Initialise la caméra"""
        camera_config = self.config.get('camera')
        
        self.camera = cv2.VideoCapture(camera_id)
        
        if not self.camera.isOpened():
            print("❌ Impossible d'ouvrir la caméra")
            return False
        
        # Configure la caméra
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, camera_config['width'])
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_config['height'])
        self.camera.set(cv2.CAP_PROP_FPS, camera_config['fps'])
        
        print(f"✅ Caméra initialisée (ID: {camera_id})")
        return True
    
    def apply_homography(self, x, y):
        """Applique l'homographie à un point (x, y) → (u, v)"""
        if self.homography_matrix is None:
            # Pas de calibration, retourne les coordonnées brutes normalisées
            height, width = self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT), self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)
            return x / width, y / height
        
        # Applique la transformation perspective
        point = np.array([[[x, y]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(point, self.homography_matrix)
        u, v = transformed[0][0]
        
        # Clamp entre 0 et 1
        u = max(0.0, min(1.0, u))
        v = max(0.0, min(1.0, v))
        
        return u, v
    
    def normalize_position(self, x, y):
        """Normalise les coordonnées avec homographie et lissage"""
        # Applique l'homographie
        norm_x, norm_y = self.apply_homography(x, y)
        
        # Applique le lissage
        self.smooth_x = self.smooth_x * self.smoothing + norm_x * (1 - self.smoothing)
        self.smooth_y = self.smooth_y * self.smoothing + norm_y * (1 - self.smoothing)
        
        return self.smooth_x, self.smooth_y
    
    def draw_calibration_zone(self, frame):
        """Dessine la zone de calibration sur la frame"""
        if self.calibration_points is None:
            return frame
        
        # Dessine les points de calibration
        for i, point in enumerate(self.calibration_points):
            x, y = int(point[0]), int(point[1])  # Convertit en int
            cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
            cv2.putText(frame, str(i+1), (x+10, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Dessine le quadrilatère
        points = np.array(self.calibration_points, dtype=np.int32)
        cv2.polylines(frame, [points], True, (0, 255, 0), 2)
        
        return frame
    
    def draw_ui(self, frame, num_hands, hands_data, norm_x, norm_y):
        """Dessine l'interface utilisateur sur la frame"""
        height, width = frame.shape[:2]
        
        # Dessine la zone de calibration
        frame = self.draw_calibration_zone(frame)
        
        # Status
        if num_hands > 0:
            status_color = (0, 255, 0)
            status_text = "✓ MAIN DÉTECTÉE"
        else:
            status_color = (100, 100, 100)
            status_text = "Pas de main"
        
        cv2.putText(frame, status_text, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
        
        # Calibration status
        if self.homography_matrix is not None:
            calib_text = "Calibration: ON"
            calib_color = (0, 255, 0)
        else:
            calib_text = "Calibration: OFF (raw coords)"
            calib_color = (0, 165, 255)
        
        cv2.putText(frame, calib_text, (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, calib_color, 2)
        
        # Position de la main si détectée
        if num_hands > 0:
            hand = hands_data[0]
            
            # Info main
            cv2.putText(frame, f"Raw: ({hand['x']}, {hand['y']})", (20, 110),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            cv2.putText(frame, f"Mapped: ({norm_x:.3f}, {norm_y:.3f})", (20, 135),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            
            cv2.putText(frame, f"Mode: {hand['mode'].upper()}", (20, 160),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Réticule sur position brute
            raw_x = hand['x']
            raw_y = hand['y']
            
            cv2.circle(frame, (raw_x, raw_y), 20, (0, 255, 255), 2)
            cv2.circle(frame, (raw_x, raw_y), 3, (0, 255, 255), -1)
            
            # Affiche les coordonnées mappées
            cv2.putText(frame, f"UV: ({norm_x:.2f}, {norm_y:.2f})", 
                        (raw_x - 80, raw_y - 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        
        # FPS
        cv2.putText(frame, f"FPS: {self.fps:.1f}", (width - 150, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 100), 2)
        
        # OSC Status
        osc_text = f"OSC: {self.osc.ip}:{self.osc.port}"
        cv2.putText(frame, osc_text, (20, height - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
        
        return frame
    
    def update_fps(self):
        """Calcule les FPS"""
        current_time = time.time()
        elapsed = current_time - self.last_fps_time
        if elapsed >= 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.last_fps_time = current_time
    
    def run(self):
        """Boucle principale"""
        self.running = True
        
        cv2.namedWindow('Through the Veil - Calibrated')
        
        print("\n🚀 APPLICATION DÉMARRÉE")
        print("="*60)
        print("CONTRÔLES:")
        print("  q - Quitter")
        print("  r - Reset détecteur")
        print("  s - Screenshot")
        print("="*60 + "\n")
        
        while self.running:
            # Capture frame
            ret, frame = self.camera.read()
            if not ret:
                print("❌ Erreur de capture")
                break
            
            height, width = frame.shape[:2]
            
            # Détection (1 seule main)
            num_hands, hands_data = self.detector.detect(frame)
            
            # Si main détectée
            if num_hands > 0:
                hand = hands_data[0]
                raw_x = hand['x']
                raw_y = hand['y']
                confidence = hand['confidence']
                mode = hand['mode']
                
                # Normalise avec homographie
                norm_x, norm_y = self.normalize_position(raw_x, raw_y)
                
                # Envoie position MAPPÉE
                self.osc.send_custom("/hand/position", [float(norm_x), float(norm_y)])
                self.osc.send_custom("/hand/detected", 1)
                
                # Envoie le mode
                if mode == "draw":
                    self.osc.send_custom("/hand/mode", 0)  # 0 = dessin précis
                    self.osc.send_custom("/hand/radius", 0.02)  # Petit rayon
                else:
                    self.osc.send_custom("/hand/mode", 1)  # 1 = effacement large
                    self.osc.send_custom("/hand/radius", 0.15)  # Grand rayon
            else:
                # Pas de main
                norm_x, norm_y = self.smooth_x, self.smooth_y
                confidence = 0.0
                
                # Envoie état "pas de main"
                self.osc.send_custom("/hand/detected", 0)
            
            # UI
            frame = self.draw_ui(frame, num_hands, hands_data, norm_x, norm_y)
            
            # Affiche
            cv2.imshow('Through the Veil - Calibrated', frame)
            
            # FPS
            self.frame_count += 1
            self.update_fps()
            
            # Contrôles
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                self.detector.reset()
                print("🔄 Détecteur réinitialisé")
            elif key == ord('s'):
                filename = f'screenshot_{int(time.time())}.png'
                cv2.imwrite(filename, frame)
                print(f"📸 Screenshot: {filename}")
        
        self.cleanup()
    
    def cleanup(self):
        """Nettoyage"""
        print("\n🧹 Nettoyage...")
        if self.camera is not None:
            self.camera.release()
        cv2.destroyAllWindows()
        print("✅ Terminé")


if __name__ == "__main__":
    app = ThroughTheVeilCalibrated()
    
    # Initialise avec la vraie caméra (ID 0)
    if not app.init_camera(0):
        print("❌ Impossible d'initialiser la caméra")
        exit()
    
    # Lance l'application
    app.run()