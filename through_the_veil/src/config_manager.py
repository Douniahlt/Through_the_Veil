"""
Gestion de la configuration du projet
"""
import json
import os

class ConfigManager:
    def __init__(self, config_path='config/settings.json'):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self):
        """Charge la configuration depuis le fichier JSON"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def get(self, *keys):
        """
        Accède à une valeur de configuration
        Usage: config.get('osc', 'unreal_port')
        """
        value = self.config
        for key in keys:
            value = value[key]
        return value
    
    def save(self):
        """Sauvegarde les modifications"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def update(self, keys, value):
        """
        Met à jour une valeur
        Usage: config.update(['osc', 'unreal_port'], 8001)
        """
        target = self.config
        for key in keys[:-1]:
            target = target[key]
        target[keys[-1]] = value