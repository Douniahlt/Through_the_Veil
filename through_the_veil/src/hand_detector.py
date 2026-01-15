import cv2
import mediapipe as mp
import numpy as np
import os

class HandDetector:
    def __init__(self, max_hands=1, detection_con=0.7, track_con=0.5):
        """
        Initialise le modèle MediaPipe Hands avec l'API tasks (0.10+).
        """
        self.max_hands = max_hands
        
        # Chemin du modèle
        model_path = os.path.join(os.path.dirname(__file__), 'hand_landmarker.task')
        
        # Configuration avec la nouvelle API tasks
        base_options = mp.tasks.BaseOptions(model_asset_path=model_path)
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=max_hands,
            min_hand_detection_confidence=detection_con,
            min_hand_presence_confidence=detection_con,
            min_tracking_confidence=track_con,
            running_mode=mp.tasks.vision.RunningMode.VIDEO
        )
        
        self.detector = mp.tasks.vision.HandLandmarker.create_from_options(options)
        self.frame_timestamp_ms = 0
        
        # Indices des points pour calculer le centre de la paume (Barycentre)
        # 0: Poignet, 5: Index (racine), 17: Auriculaire (racine)
        self.palm_indices = [0, 5, 17]

    def detect_finger_mode(self, hand_landmarks):
        """
        Détecte si l'index est tendu seul (mode dessin)
        ou si la main est ouverte (mode effacement)
        
        Returns:
            (mode, position_landmark_index)
            mode: "draw" ou "erase"
        """
        # Landmarks clés
        index_tip = hand_landmarks[8]      # Bout index
        index_mcp = hand_landmarks[5]      # Base index
        middle_tip = hand_landmarks[12]    # Bout majeur
        middle_mcp = hand_landmarks[9]     # Base majeur
        ring_tip = hand_landmarks[16]      # Bout annulaire
        ring_mcp = hand_landmarks[13]      # Base annulaire
        
        # Vérifie si index est TENDU (bout plus haut que base)
        index_extended = index_tip.y < index_mcp.y - 0.03
        
        # Vérifie si les autres doigts sont REPLIÉS (bout plus bas que base)
        middle_folded = middle_tip.y > middle_mcp.y + 0.02
        ring_folded = ring_tip.y > ring_mcp.y + 0.02
        
        # Mode DESSIN : index seul tendu
        if index_extended and middle_folded and ring_folded:
            return "draw", 8  # Landmark 8 = bout index
        else:
            # Mode EFFACEMENT : main ouverte, on garde le barycentre
            return "erase", None

    def detect(self, frame, draw=True):
        """
        Détecte la main et retourne position + mode
        """
        # Conversion pour MediaPipe
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
        
        # Détection avec timestamp
        results = self.detector.detect_for_video(mp_image, self.frame_timestamp_ms)
        self.frame_timestamp_ms += 33

        hands_data = []
        h, w, c = frame.shape

        if results.hand_landmarks:
            for idx, hand_landmarks in enumerate(results.hand_landmarks):
                
                # Détecte le mode (dessin ou effacement)
                mode, target_landmark = self.detect_finger_mode(hand_landmarks)
                
                if mode == "draw":
                    # MODE DESSIN : Position de l'index
                    index_tip = hand_landmarks[8]
                    center_x_norm = index_tip.x
                    center_y_norm = index_tip.y
                    px = int(center_x_norm * w)
                    py = int(center_y_norm * h)
                else:
                    # MODE EFFACEMENT : Barycentre de la paume (ton code actuel)
                    x_coords = [hand_landmarks[i].x for i in self.palm_indices]
                    y_coords = [hand_landmarks[i].y for i in self.palm_indices]
                    center_x_norm = np.mean(x_coords)
                    center_y_norm = np.mean(y_coords)
                    px = int(center_x_norm * w)
                    py = int(center_y_norm * h)
                
                # Confiance
                confidence = 1.0
                if results.handedness and idx < len(results.handedness):
                    confidence = results.handedness[idx][0].score

                hands_data.append({
                    'x': px,
                    'y': py,
                    'confidence': confidence,
                    'mode': mode,              # NOUVEAU : "draw" ou "erase"
                    'landmarks': hand_landmarks
                })

                # Dessin visuel
                if draw:
                    # Dessine les landmarks
                    for landmark in hand_landmarks:
                        cx, cy = int(landmark.x * w), int(landmark.y * h)
                        cv2.circle(frame, (cx, cy), 3, (0, 255, 0), -1)
                    
                    # Dessine les connexions
                    connections = [
                        (0, 1), (1, 2), (2, 3), (3, 4),  # Pouce
                        (0, 5), (5, 6), (6, 7), (7, 8),  # Index
                        (5, 9), (9, 10), (10, 11), (11, 12),  # Majeur
                        (9, 13), (13, 14), (14, 15), (15, 16),  # Annulaire
                        (13, 17), (17, 18), (18, 19), (19, 20),  # Auriculaire
                        (0, 17)  # Paume
                    ]
                    for connection in connections:
                        start_idx, end_idx = connection
                        start = hand_landmarks[start_idx]
                        end = hand_landmarks[end_idx]
                        start_point = (int(start.x * w), int(start.y * h))
                        end_point = (int(end.x * w), int(end.y * h))
                        cv2.line(frame, start_point, end_point, (255, 255, 255), 2)
                    
                    # Indicateur visuel du mode
                    if mode == "draw":
                        # Mode dessin : petit cercle BLEU sur l'index
                        cv2.circle(frame, (px, py), 6, (255, 0, 0), -1)
                        cv2.putText(frame, "DRAW", (px + 15, py - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                    else:
                        # Mode effacement : grand cercle ROUGE sur la paume
                        cv2.circle(frame, (px, py), 10, (0, 0, 255), -1)
                        cv2.putText(frame, "ERASE", (px + 15, py - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        return len(hands_data), hands_data

    def reset(self):
        """Réinitialise le tracker si besoin (utile si lag)"""
        # Réinitialise le timestamp
        self.frame_timestamp_ms = 0