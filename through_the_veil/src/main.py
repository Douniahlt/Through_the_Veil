"""
Application principale Through the Veil
Détecte 1 main
"""
import cv2
import numpy as np
import time
import sys
import os

# Ajoute le chemin parent pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_manager import ConfigManager
from osc_sender import OSCSender
from hand_detector import HandDetector

class ThroughTheVeil:
    def __init__(self):
        print("\n" + "="*60)
        print("🎭 THROUGH THE VEIL - Interactive Installation")
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
    
    def normalize_position(self, x, y, width, height):
        """Normalise les coordonnées (0.0 à 1.0)"""
        norm_x = x / width
        norm_y = y / height
        
        # Applique le lissage
        self.smooth_x = self.smooth_x * self.smoothing + norm_x * (1 - self.smoothing)
        self.smooth_y = self.smooth_y * self.smoothing + norm_y * (1 - self.smoothing)
        
        return self.smooth_x, self.smooth_y
    
    def draw_ui(self, frame, num_hands, hands_data, norm_x, norm_y):
        """Dessine l'interface utilisateur sur la frame"""
        height, width = frame.shape[:2]
        
        # Status
        if num_hands > 0:
            status_color = (0, 255, 0)
            status_text = "✓ MAIN DÉTECTÉE"
        else:
            status_color = (100, 100, 100)
            status_text = "Pas de main"
        
        cv2.putText(frame, status_text, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
        
        # Position de la main si détectée
        if num_hands > 0:
            hand = hands_data[0]
            
            # Info main
            cv2.putText(frame, f"Position: ({hand['x']}, {hand['y']})", (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            cv2.putText(frame, f"Confiance: {hand['confidence']:.2f}", (20, 110),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Réticule sur position normalisée
            screen_x = int(norm_x * width)
            screen_y = int(norm_y * height)
            
            cv2.circle(frame, (screen_x, screen_y), 30, (0, 255, 255), 3)
            cv2.circle(frame, (screen_x, screen_y), 5, (0, 255, 255), -1)
            cv2.line(frame, (screen_x - 40, screen_y), (screen_x + 40, screen_y), (0, 255, 255), 2)
            cv2.line(frame, (screen_x, screen_y - 40), (screen_x, screen_y + 40), (0, 255, 255), 2)
            
            cv2.putText(frame, f"OSC: x={norm_x:.3f}, y={norm_y:.3f}", 
                        (screen_x - 100, screen_y - 50),
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
        
        cv2.namedWindow('Through the Veil')
        
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
                mode = hand['mode']  # NOUVEAU
                
                # Normalise
                norm_x, norm_y = self.normalize_position(raw_x, raw_y, width, height)
                
                # Envoie position
                self.osc.send_custom("/hand/position", [float(norm_x), float(norm_y)])
                self.osc.send_custom("/hand/detected", 1)
                
                # NOUVEAU : Envoie le mode
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
            cv2.imshow('Through the Veil', frame)
            
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
    app = ThroughTheVeil()
    
    # Initialise avec la vraie caméra (ID 0)
    if not app.init_camera(0):
        print("❌ Impossible d'initialiser la caméra")
        exit()
    
    # Lance l'application
    app.run()