"""
Système à 2 caméras pour Through the Veil
Caméra 1 (Vue de HAUT) : Détecte si la main traverse un seuil (vitre)
Caméra 0 (Vue de FACE) : S'active quand la main traverse, pour interaction précise
"""
import cv2
import numpy as np
import time
from hand_detector import HandDetector
from config_manager import ConfigManager
from osc_sender import OSCSender

class DualCameraThreshold:
    def __init__(self, cam_top_id=1, cam_front_id=0):
        print("\n" + "="*60)
        print("🎭 THROUGH THE VEIL - Dual Camera Threshold System")
        print("="*60 + "\n")
        
        # Configuration
        config_path = '../config/settings.json'
        self.config = ConfigManager(config_path)
        
        # OSC
        osc_config = self.config.get('osc')
        self.osc = OSCSender(osc_config['unreal_ip'], osc_config['unreal_port'])
        self.osc.set_send_rate(osc_config['send_rate'])
        
        # Caméra 1 : Vue du HAUT (surveillance du seuil)
        self.cam_top = cv2.VideoCapture(cam_top_id)
        self.detector_top = HandDetector(max_hands=1, detection_con=0.6, track_con=0.5)
        print(f"✅ Caméra 1 (Vue du HAUT) : ID {cam_top_id}")
        
        # Caméra 0 : Vue de FACE (interaction précise)
        self.cam_front = cv2.VideoCapture(cam_front_id)
        self.detector_front = HandDetector(max_hands=1, detection_con=0.7, track_con=0.5)
        print(f"✅ Caméra 0 (Vue de FACE) : ID {cam_front_id}")
        
        # Configure les caméras
        camera_config = self.config.get('camera')
        for cam in [self.cam_top, self.cam_front]:
            cam.set(cv2.CAP_PROP_FRAME_WIDTH, camera_config['width'])
            cam.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_config['height'])
            cam.set(cv2.CAP_PROP_FPS, camera_config['fps'])
        
        # État du système
        self.running = False
        self.fps = 0
        self.frame_count = 0
        self.last_fps_time = time.time()
        
        # SEUIL DE POSITION (à ajuster selon votre setup)
        # Position X normalisée (0.0 à 1.0) où la vitre se trouve
        self.threshold_x = 0.5  # Par défaut au milieu
        
        # État de franchissement
        self.hand_crossed_threshold = False
        self.front_camera_active = False
        
        # Lissage de position
        self.smoothing = 0.3
        self.smooth_x = 0.5
        self.smooth_y = 0.5
        
        print(f"🎯 Seuil de franchissement: X = {self.threshold_x:.2f}")
        print("✅ Système initialisé\n")
    
    def set_threshold(self, threshold_x):
        """Définit le seuil de franchissement (0.0 à 1.0)"""
        self.threshold_x = max(0.0, min(1.0, threshold_x))
        print(f"🎯 Nouveau seuil: X = {self.threshold_x:.2f}")
    
    def normalize_position(self, x, y, width, height):
        """Normalise les coordonnées (0.0 à 1.0) avec lissage"""
        norm_x = x / width
        norm_y = y / height
        
        # Applique le lissage
        self.smooth_x = self.smooth_x * self.smoothing + norm_x * (1 - self.smoothing)
        self.smooth_y = self.smooth_y * self.smoothing + norm_y * (1 - self.smoothing)
        
        return self.smooth_x, self.smooth_y
    
    def check_threshold_crossing(self, norm_x):
        """
        Vérifie si la main a franchi le seuil
        Retourne True si la main est au-delà du seuil (vers la vitre)
        """
        # Vous pouvez ajuster la logique selon l'orientation de votre caméra
        # Par exemple : > threshold si la vitre est à droite
        # ou < threshold si la vitre est à gauche
        return norm_x > self.threshold_x
    
    def draw_threshold_line(self, frame):
        """Dessine la ligne de seuil sur la frame"""
        height, width = frame.shape[:2]
        threshold_x_pixel = int(self.threshold_x * width)
        
        # Ligne rouge pour le seuil
        cv2.line(frame, (threshold_x_pixel, 0), (threshold_x_pixel, height), 
                 (0, 0, 255), 3)
        
        # Texte
        cv2.putText(frame, "VITRE", (threshold_x_pixel + 10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        return frame
    
    def draw_ui(self, frame, camera_name, num_hands, hands_data, norm_x, norm_y):
        """Dessine l'interface utilisateur sur la frame"""
        height, width = frame.shape[:2]
        
        # Nom de la caméra
        cv2.putText(frame, camera_name, (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Status main
        if num_hands > 0:
            status_color = (0, 255, 0)
            status_text = "✓ MAIN"
        else:
            status_color = (100, 100, 100)
            status_text = "Pas de main"
        
        cv2.putText(frame, status_text, (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        # Position si main détectée
        if num_hands > 0:
            hand = hands_data[0]
            mode = hand.get('mode', 'erase')
            
            # Info
            cv2.putText(frame, f"Pos: ({hand['x']}, {hand['y']})", (20, 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.putText(frame, f"Mode: {mode.upper()}", (20, 125),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Réticule
            screen_x = int(norm_x * width)
            screen_y = int(norm_y * height)
            
            color = (255, 0, 0) if mode == "draw" else (0, 0, 255)
            cv2.circle(frame, (screen_x, screen_y), 20, color, 2)
            cv2.circle(frame, (screen_x, screen_y), 3, color, -1)
        
        # FPS
        cv2.putText(frame, f"FPS: {self.fps:.1f}", (width - 120, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 2)
        
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
        
        # Fenêtres
        cv2.namedWindow('Camera TOP (Surveillance)')
        cv2.namedWindow('Camera FRONT (Interaction)')
        
        print("\n🚀 SYSTÈME DÉMARRÉ")
        print("="*60)
        print("CONTRÔLES:")
        print("  q - Quitter")
        print("  r - Reset détecteurs")
        print("  + - Augmenter seuil")
        print("  - - Diminuer seuil")
        print("="*60 + "\n")
        
        while self.running:
            # ===== CAMÉRA TOP (Vue du haut - surveillance) =====
            ret_top, frame_top = self.cam_top.read()
            if not ret_top:
                print("❌ Erreur caméra TOP")
                break
            
            height_top, width_top = frame_top.shape[:2]
            
            # Détection sur caméra TOP
            num_hands_top, hands_data_top = self.detector_top.detect(frame_top)
            
            # Vérification du franchissement du seuil
            if num_hands_top > 0:
                hand_top = hands_data_top[0]
                raw_x_top = hand_top['x']
                raw_y_top = hand_top['y']
                
                # Normalise
                norm_x_top, norm_y_top = self.normalize_position(
                    raw_x_top, raw_y_top, width_top, height_top
                )
                
                # Vérifie le franchissement
                self.hand_crossed_threshold = self.check_threshold_crossing(norm_x_top)
                
                # Envoie position de surveillance
                self.osc.send_custom("/camera_top/detected", 1)
                self.osc.send_custom("/camera_top/position", [float(norm_x_top), float(norm_y_top)])
                self.osc.send_custom("/threshold/crossed", 1 if self.hand_crossed_threshold else 0)
            else:
                self.hand_crossed_threshold = False
                self.osc.send_custom("/camera_top/detected", 0)
                self.osc.send_custom("/threshold/crossed", 0)
                norm_x_top = self.smooth_x
                norm_y_top = self.smooth_y
            
            # Dessine UI et ligne de seuil
            frame_top = self.draw_threshold_line(frame_top)
            frame_top = self.draw_ui(frame_top, "CAM TOP (Surveillance)", 
                                      num_hands_top, hands_data_top, norm_x_top, norm_y_top)
            
            # Indicateur de franchissement
            if self.hand_crossed_threshold:
                cv2.putText(frame_top, ">>> SEUIL FRANCHI <<<", (width_top//2 - 150, height_top - 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
            
            # ===== CAMÉRA FRONT (Vue de face - interaction) =====
            ret_front, frame_front = self.cam_front.read()
            if not ret_front:
                print("❌ Erreur caméra FRONT")
                break
            
            height_front, width_front = frame_front.shape[:2]
            
            # Active la caméra FRONT seulement si seuil franchi
            if self.hand_crossed_threshold:
                self.front_camera_active = True
                
                # Détection sur caméra FRONT
                num_hands_front, hands_data_front = self.detector_front.detect(frame_front)
                
                if num_hands_front > 0:
                    hand_front = hands_data_front[0]
                    raw_x_front = hand_front['x']
                    raw_y_front = hand_front['y']
                    mode = hand_front.get('mode', 'erase')
                    confidence = hand_front['confidence']
                    
                    # Normalise
                    norm_x_front, norm_y_front = self.normalize_position(
                        raw_x_front, raw_y_front, width_front, height_front
                    )
                    
                    # Envoie données d'interaction
                    self.osc.send_custom("/hand/detected", 1)
                    self.osc.send_custom("/hand/position", [float(norm_x_front), float(norm_y_front)])
                    self.osc.send_custom("/hand/mode", 0 if mode == "draw" else 1)
                    self.osc.send_custom("/hand/radius", 0.02 if mode == "draw" else 0.15)
                    self.osc.send_custom("/hand/confidence", float(confidence))
                else:
                    self.osc.send_custom("/hand/detected", 0)
                    norm_x_front = self.smooth_x
                    norm_y_front = self.smooth_y
                    hands_data_front = []
                    num_hands_front = 0
                
                # Dessine UI
                frame_front = self.draw_ui(frame_front, "CAM FRONT (ACTIVE)", 
                                            num_hands_front, hands_data_front, 
                                            norm_x_front, norm_y_front)
                
                # Indicateur ACTIF
                cv2.rectangle(frame_front, (0, 0), (width_front, height_front), (0, 255, 0), 5)
            else:
                # Caméra FRONT inactive
                self.front_camera_active = False
                self.osc.send_custom("/hand/detected", 0)
                
                # Overlay "INACTIVE"
                overlay = frame_front.copy()
                cv2.rectangle(overlay, (0, 0), (width_front, height_front), (50, 50, 50), -1)
                frame_front = cv2.addWeighted(frame_front, 0.3, overlay, 0.7, 0)
                
                cv2.putText(frame_front, "CAMERA INACTIVE", (width_front//2 - 200, height_front//2),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (100, 100, 100), 3)
                cv2.putText(frame_front, "Franchissez le seuil pour activer", 
                            (width_front//2 - 250, height_front//2 + 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 100), 2)
            
            # Affiche les deux frames
            cv2.imshow('Camera TOP (Surveillance)', frame_top)
            cv2.imshow('Camera FRONT (Interaction)', frame_front)
            
            # FPS
            self.frame_count += 1
            self.update_fps()
            
            # Contrôles
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                self.detector_top.reset()
                self.detector_front.reset()
                print("🔄 Détecteurs réinitialisés")
            elif key == ord('+') or key == ord('='):
                self.set_threshold(self.threshold_x + 0.05)
            elif key == ord('-') or key == ord('_'):
                self.set_threshold(self.threshold_x - 0.05)
        
        self.cleanup()
    
    def cleanup(self):
        """Nettoyage"""
        print("\n🧹 Nettoyage...")
        self.cam_top.release()
        self.cam_front.release()
        cv2.destroyAllWindows()
        print("✅ Terminé")


if __name__ == "__main__":
    # Créer le système
    # cam_top_id = 1 (caméra du haut)
    # cam_front_id = 0 (caméra de face)
    system = DualCameraThreshold(cam_top_id=1, cam_front_id=0)
    
    # Ajuster le seuil si nécessaire (0.0 à 1.0)
    # system.set_threshold(0.6)  # Par exemple
    
    # Lancer
    system.run()
