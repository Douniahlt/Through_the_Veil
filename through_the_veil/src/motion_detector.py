"""
Détection de mouvement avec lissage temporel
"""
import cv2
import numpy as np

class MotionDetector:
    def __init__(self, min_area=1000, sensitivity=20):
        self.min_area = min_area
        self.sensitivity = sensitivity
        self.previous_frame = None
        
        # Lissage temporel
        self.detection_history = []
        self.history_size = 5
        
        print(f"🔍 MotionDetector initialisé (min_area={min_area}, sensitivity={sensitivity})")
    
    def detect(self, frame):
        """
        Détecte le mouvement dans une frame avec lissage temporel
        Retourne: (detected, x, y, area)
        """
        # Convertit en niveaux de gris
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # Première frame : initialise
        if self.previous_frame is None:
            self.previous_frame = gray
            self.detection_history.append(False)
            return False, 0, 0, 0
        
        # Calcule la différence
        frame_delta = cv2.absdiff(self.previous_frame, gray)
        thresh = cv2.threshold(frame_delta, self.sensitivity, 255, cv2.THRESH_BINARY)[1]
        
        # Dilate pour combler les trous
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Trouve les contours
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Met à jour la frame précédente
        self.previous_frame = gray
        
        # Trouve le plus grand contour
        if len(contours) == 0:
            self.detection_history.append(False)
            if len(self.detection_history) > self.history_size:
                self.detection_history.pop(0)
            return False, 0, 0, 0
        
        max_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(max_contour)
        
        if area < self.min_area:
            self.detection_history.append(False)
            if len(self.detection_history) > self.history_size:
                self.detection_history.pop(0)
            return False, 0, 0, 0
        
        # Calcule le centre
        M = cv2.moments(max_contour)
        if M["m00"] == 0:
            self.detection_history.append(False)
            if len(self.detection_history) > self.history_size:
                self.detection_history.pop(0)
            return False, 0, 0, 0
        
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        
        # Lissage temporel
        self.detection_history.append(True)
        if len(self.detection_history) > self.history_size:
            self.detection_history.pop(0)
        
        # Considère détecté si au moins 60% des dernières frames détectent
        ratio_detected = sum(self.detection_history) / len(self.detection_history)
        
        if ratio_detected >= 0.6:
            return True, cx, cy, area
        else:
            return False, 0, 0, 0
    
    def reset(self):
        """Réinitialise le détecteur"""
        self.previous_frame = None
        self.detection_history = []
    
    def set_sensitivity(self, value):
        """Change la sensibilité (0-255)"""
        self.sensitivity = value
    
    def set_min_area(self, value):
        """Change l'aire minimale"""
        self.min_area = value