"""
Communication OSC vers Unreal Engine
"""
from pythonosc import udp_client
import time

class OSCSender:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.client = udp_client.SimpleUDPClient(ip, port)
        self.last_send_time = time.time()
        self.send_rate = 60  # Hz
        
        print(f"📡 OSC Sender initialisé : {ip}:{port}")
    
    def set_send_rate(self, rate):
        """Définit la fréquence d'envoi en Hz"""
        self.send_rate = rate
    
    def can_send(self):
        """Vérifie si on peut envoyer (rate limiting)"""
        current_time = time.time()
        if current_time - self.last_send_time >= 1.0 / self.send_rate:
            self.last_send_time = current_time
            return True
        return False
    
    def send_hand_detected(self, detected):
        """Envoie l'état de détection (0 ou 1)"""
        try:
            self.client.send_message("/hand/detected", int(detected))
            return True
        except Exception as e:
            print(f"❌ Erreur OSC: {e}")
            return False
    
    def send_hand_position(self, x, y):
        """
        Envoie la position de la main
        x, y doivent être normalisés entre 0.0 et 1.0
        """
        try:
            self.client.send_message("/hand/position", [float(x), float(y)])
            return True
        except Exception as e:
            print(f"❌ Erreur OSC: {e}")
            return False
    
    def send_hand_data(self, detected, x, y, intensity=1.0, velocity=0.0):
        """
        Envoie un paquet complet de données
        """
        if not self.can_send():
            return False
        
        try:
            self.client.send_message("/hand/detected", int(detected))
            if detected:
                self.client.send_message("/hand/position", [float(x), float(y)])
                self.client.send_message("/hand/intensity", float(intensity))
                self.client.send_message("/hand/velocity", float(velocity))
            return True
        except Exception as e:
            print(f"❌ Erreur OSC: {e}")
            return False
    
    def send_custom(self, address, value):
        """Envoie un message personnalisé"""
        try:
            self.client.send_message(address, value)
            return True
        except Exception as e:
            print(f"❌ Erreur OSC: {e}")
            return False