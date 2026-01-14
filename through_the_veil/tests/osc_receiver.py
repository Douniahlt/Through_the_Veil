"""
Récepteur OSC - Affiche les messages reçus
Lance ce script EN PREMIER dans un terminal
"""
from pythonosc import dispatcher, osc_server
import time

PORT = 8000

print("\n" + "=" * 60)
print("🎧 RÉCEPTEUR OSC - Through the Veil")
print("=" * 60)
print("Port d'écoute : {}".format(PORT))
print("En attente de messages...")
print("Ctrl+C pour arrêter")
print("=" * 60 + "\n")

# Compteur de messages
message_count = 0
last_position = [0, 0]

def handle_detected(address, *args):
    """Reçoit l'état de détection"""
    global message_count
    message_count += 1
    
    detected = args[0]
    status = "✓ DÉTECTÉE" if detected else "✗ Absente"
    
    print("[{}] Main : {}".format(message_count, status))

def handle_position(address, *args):
    """Reçoit la position"""
    global last_position
    x, y = args[0], args[1]
    last_position = [x, y]
    
    print("       └─> Position : x={:.3f}, y={:.3f}".format(x, y))

def handle_intensity(address, *args):
    """Reçoit l'intensité"""
    intensity = args[0]
    print("       └─> Intensité : {:.3f}".format(intensity))

# Configure le dispatcher (routeur de messages)
disp = dispatcher.Dispatcher()
disp.map("/hand/detected", handle_detected)
disp.map("/hand/position", handle_position)
disp.map("/hand/intensity", handle_intensity)

# Crée le serveur
server = osc_server.ThreadingOSCUDPServer(("127.0.0.1", PORT), disp)

print("✅ Serveur démarré\n")

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\n\n" + "=" * 60)
    print("📊 STATISTIQUES")
    print("=" * 60)
    print("Messages reçus : {}".format(message_count))
    print("Dernière position : x={:.3f}, y={:.3f}".format(
        last_position[0], last_position[1]))
    print("=" * 60)
    print("✅ Serveur arrêté")