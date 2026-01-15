"""
Système à 2 caméras pour Through the Veil
Caméra 1 : Détection présence main (frontale)
Caméra 2 : Détection contact vitre (proche vitre)
"""
import cv2
import numpy as np
import time
from hand_detector import HandDetector
from config_manager import ConfigManager
from osc_sender import OSCSender

class DualCameraSystem:
    def __init__(self, cam1_id=0, cam2_id=1):
        print("\n" + "="*60)
        print("🎭 THROUGH THE VEIL - Dual Camera System")
        print("="*60 + "\n")
        
        # Configuration
        config_path = '../config/settings.json'
        self.config = ConfigManager(config_path)
        
        # OSC
        osc_config = self.config.get('osc')
        self.osc = OSCSender(osc_config['unreal_ip'], osc_config['unreal_port'])
        self.osc.set_send_rate(osc_config['send_rate'])
        
        # Caméra 1 : Détection présence (MediaPipe)
        self.cam1 = cv2.VideoCapture(cam1_id)
        self.hand_detector = HandDetector(max_hands=1)
        print(f"✅ Caméra 1 (Frontale) : ID {cam1_id}")
        
        # Caméra 2 : Détection contact
        self.cam2 = cv2.VideoCapture(cam2_id)
        print(f"✅ Caméra 2 (Vitre) : ID {cam2_id}")
        
        # État
        self.running = False
        self.fps = 0
        self.frame_count = 0
        self.last_fps_time = time.time()
        
        # Seuils pour détection contact (CAM2)
        self.contact_threshold = 100  # Luminosité minimale pour détecter contact
        self.min_contact_area = 500   # Aire minimale en pixels
        
        print("✅ Système initialisé\n")
    
    def detect_contact(self, frame):
        """
        Détecte le contact sur la vitre (Caméra 2)
        Retourne: (is_touching, x, y, area)
        """
        # Convertit en HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Détection de peau (teinte chair)
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)
        
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        
        # Filtre le bruit
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Trouve les contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) == 0:
            return False, 0, 0, 0
        
        # Plus grand contour
        max_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(max_contour)
        
        if area < self.min_contact_area:
            return False, 0, 0, 0
        
        # Centre du contact
        M = cv2.moments(max_contour)
        if M["m00"] == 0:
            return False, 0, 0, 0
        
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        
        # Dessine le contour (debug)
        cv2.drawContours(frame, [max_contour], -1, (0, 255, 0), 2)
        cv2.circle(frame, (cx, cy), 10, (0, 0, 255), -1)
        
        return True, cx, cy, area
    
    def run(self):
        """Boucle principale"""
        self.running = True
        
        # Fenêtres
        cv2.namedWindow('Camera 1 - Presence')
        cv2.namedWindow('Camera 2 - Contact')
        
        print("\n🚀 SYSTÈME DÉMARRÉ")
        print("="*60)
        print("CONTRÔLES:")
        print("  q - Quitter")
        print("  r - Reset")
        print("  + - Augmenter seuil contact")
        print("  - - Diminuer seuil contact")
        print("="*60 + "\n")
        
        while self.running:
            # ========== CAMÉRA 1 : DÉTECTION PRÉSENCE ==========
            ret1, frame1 = self.cam1.read()
            if not ret1:
                print("❌ Erreur Caméra 1")
                break
            
            # Détecte la présence de la main
            num_hands, hands_data = self.hand_detector.detect(frame1)
            hand_present = num_hands > 0
            
            # Affiche statut CAM1
            status1 = "✓ MAIN PRESENTE" if hand_present else "Pas de main"
            color1 = (0, 255, 0) if hand_present else (100, 100, 100)
            cv2.putText(frame1, status1, (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color1, 2)
            
            # ========== CAMÉRA 2 : DÉTECTION CONTACT ==========
            ret2, frame2 = self.cam2.read()
            if not ret2:
                print("❌ Erreur Caméra 2")
                break
            
            # Détecte le contact sur la vitre
            is_touching, contact_x, contact_y, area = self.detect_contact(frame2)
            
            # Affiche statut CAM2
            status2 = f"✓ CONTACT (area={area:.0f})" if is_touching else "Pas de contact"
            color2 = (0, 255, 0) if is_touching else (100, 100, 100)
            cv2.putText(frame2, status2, (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color2, 2)
            
            if is_touching:
                cv2.putText(frame2, f"Position: ({contact_x}, {contact_y})", (20, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # ========== LOGIQUE DE FUSION ==========
            if hand_present and is_touching:
                # Main présente ET contact détecté
                height2, width2 = frame2.shape[:2]
                norm_x = contact_x / width2
                norm_y = contact_y / height2
                
                # Envoie à Unreal
                self.osc.send_hand_data(True, norm_x, norm_y, intensity=1.0)
                
                # Indicateur visuel
                cv2.putText(frame1, ">>> ENVOI OSC <<<", (20, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                cv2.putText(frame2, ">>> ENVOI OSC <<<", (20, 120),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            else:
                # Pas de contact valide
                self.osc.send_hand_data(False, 0.5, 0.5, intensity=0.0)
            
            # FPS
            self.frame_count += 1
            self.update_fps()
            fps_text = f"FPS: {self.fps:.1f}"
            cv2.putText(frame1, fps_text, (frame1.shape[1] - 150, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 100), 2)
            cv2.putText(frame2, fps_text, (frame2.shape[1] - 150, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 100), 2)
            
            # Affiche
            cv2.imshow('Camera 1 - Presence', frame1)
            cv2.imshow('Camera 2 - Contact', frame2)
            
            # Contrôles
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                self.hand_detector.reset()
                print("🔄 Reset")
            elif key == ord('+'):
                self.min_contact_area += 100
                print(f"🔧 Aire minimale: {self.min_contact_area}")
            elif key == ord('-'):
                self.min_contact_area = max(100, self.min_contact_area - 100)
                print(f"🔧 Aire minimale: {self.min_contact_area}")
        
        self.cleanup()
    
    def update_fps(self):
        """Calcule FPS"""
        current_time = time.time()
        elapsed = current_time - self.last_fps_time
        if elapsed >= 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.last_fps_time = current_time
    
    def cleanup(self):
        """Nettoyage"""
        print("\n🧹 Nettoyage...")
        self.cam1.release()
        self.cam2.release()
        cv2.destroyAllWindows()
        print("✅ Terminé")


if __name__ == "__main__":
    # IDs des caméras (à ajuster selon ton système)
    system = DualCameraSystem(cam1_id=0, cam2_id=1)
    system.run()