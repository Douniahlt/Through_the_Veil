"""
Test OSC ultra simple - Envoie "Hello World" à Unreal
"""
from pythonosc import udp_client
import time

# Configuration
UNREAL_IP = "127.0.0.1"
UNREAL_PORT = 8000

print("\n" + "="*60)
print("🧪 TEST OSC ULTRA SIMPLE")
print("="*60)
print(f"Cible : {UNREAL_IP}:{UNREAL_PORT}")
print("Message : /test/hello avec 'Hello World'")
print("="*60 + "\n")

# Crée le client
client = udp_client.SimpleUDPClient(UNREAL_IP, UNREAL_PORT)

print("⏳ Attente 2 secondes (lance Unreal maintenant)...\n")
time.sleep(2)

# Envoie 10 messages
for i in range(10):
    message = f"Hello World {i+1}"
    
    # Envoie sur l'adresse /test/hello
    client.send_message("/test", message)
    
    print(f"📤 Envoyé [{i+1}/10] : {message}")
    time.sleep(1)  # 1 seconde entre chaque message

print("\n✅ Test terminé - Vérifie Output Log dans Unreal !")
