"""
Outil de Calibration AUTOMATIQUE - Through the Veil
Détecte automatiquement les 4 paillettes rouges aux coins de la vitre
"""
import cv2
import numpy as np
import json
import os

class AutoCalibrationTool:
    def __init__(self, camera_id=0):
        print("\n" + "="*60)
        print("🟢 AUTO CALIBRATION TOOL - Through the Veil")
        print("="*60 + "\n")
        
        # Caméra
        self.camera = cv2.VideoCapture(camera_id)
        if not self.camera.isOpened():
            raise Exception(f"❌ Impossible d'ouvrir la caméra {camera_id}")
        
        print(f"✅ Caméra {camera_id} ouverte")
        
        # Seuils de détection pour le VERT (HSV)
        # VERT : Teinte entre 40-80 en HSV
        # Vert clair/vif : 40-70
        # Vert foncé : 70-90
        self.lower_green = np.array([35, 50, 50])   # Vert large
        self.upper_green = np.array([85, 255, 255]) # Jusqu'au cyan
        
        # Paramètres de détection
        self.min_area = 50  # Aire minimale des paillettes (en pixels)
        self.max_area = 5000  # Aire maximale
        
        # Points détectés
        self.detected_points = []
        self.calibration_points = []  # Les 4 coins triés
        
        # Points cibles (normalisés 0-1)
        self.target_points = np.array([
            [0, 0],     # Top-Left
            [1, 0],     # Top-Right
            [1, 1],     # Bottom-Right
            [0, 1]      # Bottom-Left
        ], dtype=np.float32)
        
        # Homographie
        self.homography_matrix = None
        self.calibration_done = False
        
        print("\n📋 INSTRUCTIONS:")
        print("  1. Place 4 paillettes VERTES aux 4 coins de ta zone")
        print("  2. L'outil les détecte automatiquement")
        print("  3. Appuie sur 'c' pour confirmer la calibration")
        print("  4. Appuie sur 'a' pour ajuster les seuils de détection")
        print("  5. Appuie sur 's' pour sauvegarder")
        print("="*60 + "\n")
    
    def detect_green_points(self, frame):
        """Détecte tous les points verts dans l'image"""
        # Convertit en HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Crée le masque pour le vert
        mask = cv2.inRange(hsv, self.lower_green, self.upper_green)
        
        # Filtre le bruit
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Trouve les contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        points = []
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Filtre par aire
            if self.min_area < area < self.max_area:
                # Calcule le centre
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    points.append({
                        'x': cx,
                        'y': cy,
                        'area': area,
                        'contour': contour
                    })
        
        return points, mask
    
    def sort_corners(self, points):
        """
        Trie les 4 points dans l'ordre : Top-Left, Top-Right, Bottom-Right, Bottom-Left
        """
        if len(points) != 4:
            return None
        
        # Convertit en numpy array
        pts = np.array([[p['x'], p['y']] for p in points], dtype=np.float32)
        
        # Trouve le centre
        center = pts.mean(axis=0)
        
        # Trie par angle depuis le centre
        def angle_from_center(point):
            return np.arctan2(point[1] - center[1], point[0] - center[0])
        
        # Calcule les angles
        angles = [angle_from_center(pt) for pt in pts]
        
        # Trie par angle (de -π à π)
        sorted_indices = np.argsort(angles)
        
        # Réorganise pour avoir : Top-Left, Top-Right, Bottom-Right, Bottom-Left
        # L'ordre dépend de l'angle de départ, on ajuste
        sorted_pts = pts[sorted_indices]
        
        # Trouve le point le plus en haut à gauche (plus petit x+y)
        sums = sorted_pts.sum(axis=1)
        top_left_idx = np.argmin(sums)
        
        # Réorganise en commençant par top-left
        sorted_pts = np.roll(sorted_pts, -top_left_idx, axis=0)
        
        return sorted_pts.tolist()
    
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
            self.calibration_done = True
            return True
        else:
            print("❌ Erreur lors du calcul de l'homographie")
            return False
    
    def test_homography(self, x, y):
        """Teste l'homographie en transformant un point"""
        if self.homography_matrix is None:
            return None, None
        
        point = np.array([[[x, y]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(point, self.homography_matrix)
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
    
    def draw_detection(self, frame, points, mask):
        """Dessine les points détectés"""
        height, width = frame.shape[:2]
        
        # Affiche le masque dans un coin
        mask_resized = cv2.resize(mask, (width//4, height//4))
        mask_rgb = cv2.cvtColor(mask_resized, cv2.COLOR_GRAY2BGR)
        frame[0:height//4, 0:width//4] = mask_rgb
        
        cv2.putText(frame, "Mask", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Dessine tous les points détectés
        for i, point in enumerate(points):
            x, y = point['x'], point['y']
            area = point['area']
            
            # Cercle
            cv2.circle(frame, (x, y), 10, (0, 255, 0), 2)
            cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)
            
            # Info
            cv2.putText(frame, f"{i+1}", (x+15, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            cv2.putText(frame, f"A:{int(area)}", (x+15, y+10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        
        # Si 4 points triés, dessine le quadrilatère
        if self.calibration_points and len(self.calibration_points) == 4:
            pts = np.array(self.calibration_points, dtype=np.int32)
            cv2.polylines(frame, [pts], True, (0, 255, 255), 3)
            
            # Labels
            labels = ["TL", "TR", "BR", "BL"]
            for i, (pt, label) in enumerate(zip(self.calibration_points, labels)):
                x, y = int(pt[0]), int(pt[1])
                cv2.putText(frame, label, (x-30, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        
        return frame
    
    def adjust_thresholds_window(self):
        """Crée une fenêtre pour ajuster les seuils HSV"""
        def nothing(x):
            pass
        
        cv2.namedWindow('Adjust Thresholds')
        
        # Trackbars pour HSV du VERT
        # Hue pour vert : 35-85
        cv2.createTrackbar('H_min', 'Adjust Thresholds', 35, 179, nothing)
        cv2.createTrackbar('S_min', 'Adjust Thresholds', 50, 255, nothing)
        cv2.createTrackbar('V_min', 'Adjust Thresholds', 50, 255, nothing)
        
        cv2.createTrackbar('H_max', 'Adjust Thresholds', 85, 179, nothing)
        cv2.createTrackbar('S_max', 'Adjust Thresholds', 255, 255, nothing)
        cv2.createTrackbar('V_max', 'Adjust Thresholds', 255, 255, nothing)
        
        cv2.createTrackbar('Min Area', 'Adjust Thresholds', 50, 1000, nothing)
        cv2.createTrackbar('Max Area', 'Adjust Thresholds', 500, 10000, nothing)
        
        print("\n🎛️  Fenêtre d'ajustement ouverte")
        print("   Ajuste les trackbars pour améliorer la détection")
        print("   Ferme la fenêtre quand terminé")
        
        return True
    
    def update_thresholds_from_trackbars(self):
        """Met à jour les seuils depuis les trackbars"""
        try:
            h_min = cv2.getTrackbarPos('H_min', 'Adjust Thresholds')
            s_min = cv2.getTrackbarPos('S_min', 'Adjust Thresholds')
            v_min = cv2.getTrackbarPos('V_min', 'Adjust Thresholds')
            
            h_max = cv2.getTrackbarPos('H_max', 'Adjust Thresholds')
            s_max = cv2.getTrackbarPos('S_max', 'Adjust Thresholds')
            v_max = cv2.getTrackbarPos('V_max', 'Adjust Thresholds')
            
            self.lower_green = np.array([h_min, s_min, v_min])
            self.upper_green = np.array([h_max, s_max, v_max])
            
            self.min_area = cv2.getTrackbarPos('Min Area', 'Adjust Thresholds')
            self.max_area = cv2.getTrackbarPos('Max Area', 'Adjust Thresholds')
        except:
            pass
    
    def run(self):
        """Lance l'outil de calibration automatique"""
        cv2.namedWindow('Auto Calibration Tool')
        
        print("🎥 Détection automatique des paillettes vertes...\n")
        
        adjust_mode = False
        
        while True:
            ret, frame = self.camera.read()
            if not ret:
                print("❌ Erreur de capture")
                break
            
            # Met à jour les seuils si mode ajustement
            if adjust_mode:
                self.update_thresholds_from_trackbars()
            
            # Détecte les points verts
            points, mask = self.detect_green_points(frame)
            
            # Si exactement 4 points, trie-les
            if len(points) == 4:
                sorted_points = self.sort_corners(points)
                if sorted_points:
                    self.calibration_points = sorted_points
            else:
                self.calibration_points = []
            
            # Dessine
            display_frame = self.draw_detection(frame, points, mask)
            
            # Status
            height, width = frame.shape[:2]
            
            if len(points) == 0:
                status = "❌ Aucune paillette détectée"
                color = (0, 0, 255)
            elif len(points) < 4:
                status = f"⚠️  {len(points)}/4 paillettes détectées"
                color = (0, 165, 255)
            elif len(points) > 4:
                status = f"⚠️  Trop de paillettes ! ({len(points)})"
                color = (0, 165, 255)
            else:
                if not self.calibration_done:
                    status = "✅ 4 paillettes OK ! Appuie sur 'c'"
                    color = (0, 255, 0)
                else:
                    status = "✅ CALIBRATION OK ! Appuie sur 's'"
                    color = (0, 255, 0)
            
            cv2.putText(display_frame, status, (width//4 + 20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            # Contrôles
            cv2.putText(display_frame, "c:Confirmer | a:Ajuster | s:Sauver | q:Quitter", 
                        (20, height - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            cv2.imshow('Auto Calibration Tool', display_frame)
            
            # Gestion clavier
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("\n👋 Fermeture")
                break
            
            elif key == ord('a'):
                if not adjust_mode:
                    self.adjust_thresholds_window()
                    adjust_mode = True
                else:
                    cv2.destroyWindow('Adjust Thresholds')
                    adjust_mode = False
            
            elif key == ord('c'):
                if len(self.calibration_points) == 4:
                    if self.calculate_homography():
                        print("✅ Calibration confirmée !")
                        print(f"   Points détectés : {self.calibration_points}")
                else:
                    print(f"❌ Il faut 4 paillettes (actuellement {len(points)})")
            
            elif key == ord('s'):
                if self.calibration_done:
                    self.save_calibration()
                    print("\n✅ Calibration sauvegardée ! Tu peux quitter")
                else:
                    print("❌ Fais d'abord la calibration (appuie sur 'c')")
        
        self.cleanup()
    
    def cleanup(self):
        """Nettoyage"""
        print("\n🧹 Nettoyage...")
        self.camera.release()
        cv2.destroyAllWindows()
        print("✅ Terminé")


if __name__ == "__main__":
    # Lance l'outil de calibration automatique
    tool = AutoCalibrationTool(camera_id=0)
    tool.run()