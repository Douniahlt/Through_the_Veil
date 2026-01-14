from pythonosc import udp_client
import time

client = udp_client.SimpleUDPClient("193.54.159.61", 9000)

print("=" * 50)
print("Envoi messages OSC vers Unreal")
print("Port: 9000")
print("Appuie sur Ctrl+C pour arreter")
print("=" * 50)

counter = 0
try:
    while True:
        client.send_message("/test", counter)
        print(f"Envoye : /test {counter}")
        
        # Envoie aussi les messages hand
        client.send_message("/hand/detected", 1)
        client.send_message("/hand/position", [0.5, 0.5])
        
        counter += 1
        time.sleep(1)
except KeyboardInterrupt:
    print("\nArret")