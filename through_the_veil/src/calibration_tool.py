"""
Outil de Calibration - Through the Veil
Permet de définir les 4 coins de la zone interactive sur la vitre
et calcule l'homographie pour mapper correctement la position de la main
"""
import cv2
import numpy as np
import json
import os

class CalibrationTool:
    def __init__(self, camera_id=0):
        print("\n" + "="*60)
        print("🎯 CALIBRATION TOOL - Through the Veil")
        print("="*60 + "\n")
        
        # Caméra
        self.camera = cv2.VideoCapture(camera_id)
        if not self.camera.isOpened():
            raise Exception(f"❌ Impossible d'ouvrir la caméra {camera_id}")
        
        print(f"✅ Caméra {camera_id} ouverte")
        
        # Points de calibration (4 coins de la vitre)
        self.calibration_points = []
        self.max_points = 4
        
        # Points cibles (normalisés 0-1)
        # Ordre : Top-Left, Top-Right, Bottom-Right, Bottom-Left
        self.target_points = np.array([
            [0, 0],     # Top-Left
            [1, 0],     # Top-Right
            [1, 1],     # Bottom-Right
            [0, 1]      # Bottom-Left
        ], dtype=np.float32)
        
        # Homographie
        self.homography_matrix = None
        
        # État
        self.calibration_done = False
        self.current_frame = None
        
        print("\n📋 INSTRUCTIONS:")
        print("  1. Clique sur les 4 COINS de la zone interactive")
        print("     dans cet ordre :")
        print("     - Coin HAUT-GAUCHE")
        print("     - Coin HAUT-DROIT")
        print("     - Coin BAS-DROIT")
        print("     - Coin BAS-GAUCHE")
        print("  2. Appuie sur 'c' pour confirmer")
        print("  3. Appuie sur 'r' pour recommencer")
        print("  4. Appuie sur 'q' pour quitter sans sauvegarder")
        print("="*60 + "\n")
    
    def mouse_callback(self, event, x, y, flags, param):
        """Callback pour les clics souris"""
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(self.calibration_points) < self.max_points:
                self.calibration_points.append([x, y])
                print(f"✅ Point {len(self.calibration_points)}/4 ajouté : ({x}, {y})")
                
                if len(self.calibration_points) == self.max_points:
                    print("\n🎯 4 points définis ! Appuie sur 'c' pour confirmer")
    
    def draw_points(self, frame):
        """Dessine les points de calibration sur la frame"""
        # Labels pour chaque point
        labels = ["TOP-LEFT", "TOP-RIGHT", "BOTTOM-RIGHT", "BOTTOM-LEFT"]
        colors = [(0, 255, 0), (0, 255, 255), (255, 0, 0), (255, 0, 255)]
        
        for i, point in enumerate(self.calibration_points):
            x, y = point
            color = colors[i]
            
            # Cercle
            cv2.circle(frame, (x, y), 10, color, -1)
            cv2.circle(frame, (x, y), 12, (255, 255, 255), 2)
            
            # Numéro
            cv2.putText(frame, str(i+1), (x-5, y+5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Label
            cv2.putText(frame, labels[i], (x+15, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Dessine les lignes entre les points
        if len(self.calibration_points) >= 2:
            for i in range(len(self.calibration_points)):
                pt1 = tuple(self.calibration_points[i])
                pt2 = tuple(self.calibration_points[(i+1) % len(self.calibration_points)])
                cv2.line(frame, pt1, pt2, (0, 255, 0), 2)
        
        return frame
    
    def calculate_homography(self):
        """Calcule la matrice d'homographie"""
        if len(self.calibration_points) != 4:
            print("❌ Il faut exactement 4 points")
            return False
        
        # Convertit en numpy array
        src_points = np.array(self.calibration_points, dtype=np.float32)
        
        # Calcule l'homographie
        self.homography_matrix, status = cv2.findHomography(src_points, self.target_points)
        
        if self.homography_matrix is not None:
            print("\n✅ Homographie calculée !")
            print("Matrice :")
            print(self.homography_matrix)
            self.calibration_done = True
            return True
        else:
            print("❌ Erreur lors du calcul de l'homographie")
            return False
    
    def test_homography(self, x, y):
        """Teste l'homographie en transformant un point"""
        if self.homography_matrix is None:
            return None, None
        
        # Point source
        point = np.array([[[x, y]]], dtype=np.float32)
        
        # Transforme
        transformed = cv2.perspectiveTransform(point, self.homography_matrix)
        
        # Extrait
        u, v = transformed[0][0]
        
        return u, v
    
    def save_calibration(self, filepath='calibration.json'):
        """Sauvegarde la calibration"""
        if self.homography_matrix is None:
            print("❌ Pas de calibration à sauvegarder")
            return False
        
        data = {
            'calibration_points': self.calibration_points,
            'homography_matrix': self.homography_matrix.tolist(),
            'target_points': self.target_points.tolist()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n✅ Calibration sauvegardée : {filepath}")
        return True
    
    def run(self):
        """Lance l'outil de calibration"""
        cv2.namedWindow('Calibration Tool')
        cv2.setMouseCallback('Calibration Tool', self.mouse_callback)
        
        print("🎥 Fenêtre ouverte - Clique sur les 4 coins de la zone interactive\n")
        
        while True:
            ret, frame = self.camera.read()
            if not ret:
                print("❌ Erreur de capture")
                break
            
            self.current_frame = frame.copy()
            
            # Dessine les points
            display_frame = self.draw_points(frame)
            
            # Instructions
            height, width = frame.shape[:2]
            
            if len(self.calibration_points) < 4:
                status_text = f"Clique sur le coin {len(self.calibration_points)+1}/4"
                color = (0, 255, 255)
            elif not self.calibration_done:
                status_text = "Appuie sur 'c' pour confirmer"
                color = (0, 255, 0)
            else:
                status_text = "Calibration OK ! Appuie sur 's' pour sauvegarder"
                color = (0, 255, 0)
            
            cv2.putText(display_frame, status_text, (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            # Contrôles
            cv2.putText(display_frame, "c: Confirmer | r: Reset | s: Sauvegarder | q: Quitter", 
                        (20, height - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            # Si calibration faite, teste en temps réel
            if self.calibration_done:
                # Affiche la zone transformée
                h, w = frame.shape[:2]
                test_point = (w//2, h//2)  # Centre de l'image
                u, v = self.test_homography(test_point[0], test_point[1])
                
                if u is not None:
                    cv2.circle(display_frame, test_point, 8, (255, 0, 255), -1)
                    cv2.putText(display_frame, f"Test: ({u:.2f}, {v:.2f})", 
                                (test_point[0]+15, test_point[1]-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)
            
            cv2.imshow('Calibration Tool', display_frame)
            
            # Gestion clavier
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("\n👋 Annulation de la calibration")
                break
            
            elif key == ord('r'):
                print("\n🔄 Reset des points")
                self.calibration_points = []
                self.homography_matrix = None
                self.calibration_done = False
            
            elif key == ord('c'):
                if len(self.calibration_points) == 4 and not self.calibration_done:
                    if self.calculate_homography():
                        print("✅ Calibration confirmée !")
                else:
                    print("❌ Il faut 4 points pour calibrer")
            
            elif key == ord('s'):
                if self.calibration_done:
                    self.save_calibration()
                    print("\n✅ Calibration sauvegardée !")
                    print("Tu peux maintenant quitter (appuie sur 'q')")
                else:
                    print("❌ Fais d'abord la calibration (appuie sur 'c')")
        
        self.cleanup()
    
    def cleanup(self):
        """Nettoyage"""
        print("\n🧹 Nettoyage...")
        self.camera.release()
        cv2.destroyAllWindows()
        print("✅ Terminé")


def load_calibration(filepath='calibration.json'):
    """Charge une calibration depuis un fichier"""
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    return {
        'homography_matrix': np.array(data['homography_matrix'], dtype=np.float32),
        'calibration_points': data['calibration_points'],
        'target_points': np.array(data['target_points'], dtype=np.float32)
    }


def apply_homography(x, y, homography_matrix):
    """Applique l'homographie à un point"""
    point = np.array([[[x, y]]], dtype=np.float32)
    transformed = cv2.perspectiveTransform(point, homography_matrix)
    u, v = transformed[0][0]
    return u, v


if __name__ == "__main__":
    # Lance l'outil de calibration
    tool = CalibrationTool(camera_id=0)
    tool.run()