# Système Dual Caméra - Through the Veil

## Architecture

### Vue d'ensemble
Le système utilise **2 caméras** pour créer une interaction en deux étapes :

1. **Caméra TOP (ID 1)** - Vue du HAUT
   - Surveille en permanence la position de la main
   - Détecte quand la main franchit un seuil (la "vitre")
   - Vue de haut vers le bas

2. **Caméra FRONT (ID 0)** - Vue de FACE
   - S'active uniquement quand le seuil est franchi
   - Permet l'interaction précise (dessin/effacement)
   - Vue frontale standard

## Fonctionnement

```
┌──────────────────────────────────────────┐
│  CAMÉRA TOP (Vue du haut)                │
│  🎥 Surveillance permanente              │
│                                           │
│  ┌─────┐  Position X                     │
│  │ ✋  │  ───────────────> Détection     │
│  └─────┘                                  │
│    │                                      │
│    │ Franchit seuil ?                    │
│    ▼                                      │
│  [ X > threshold ? ]                     │
│         │                                 │
│         │ OUI                             │
│         ▼                                 │
│  ┌─────────────────────┐                 │
│  │ ACTIVE CAMÉRA FRONT │                 │
│  └─────────────────────┘                 │
└──────────────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────┐
│  CAMÉRA FRONT (Vue de face)              │
│  🎥 Interaction précise                  │
│                                           │
│  Détecte mode :                          │
│  • Index seul → Mode DRAW (précis)       │
│  • Main ouverte → Mode ERASE (large)     │
│                                           │
│  Envoie OSC vers Unreal Engine           │
└──────────────────────────────────────────┘
```

## Installation

### 1. Environnement virtuel (déjà fait)
```bash
cd /home/romaric/Bureau/PourRomaric/through_the_veil
source venv/bin/activate
```

### 2. Vérifier les dépendances
```bash
pip install -r requirements.txt
```

## Utilisation

### Mode Production (2 caméras)
```bash
cd /home/romaric/Bureau/PourRomaric/through_the_veil/src
source ../venv/bin/activate
python dual_camera_threshold.py
```

system = DualCameraThreshold(cam_top_id=1, cam_front_id=0) ça donne les nom des deux caméra

pour trouver les nom des caméra faut faire :
```bash 
ls /dev/video*
```

ou teste de changer les valeurs de la ligne

system = DualCameraThreshold(cam_top_id=0, cam_front_id=1)

## Contrôles Clavier

| Touche | Action |
|--------|--------|
| `q` | Quitter l'application |
| `r` | Réinitialiser les détecteurs |
| `+` | Augmenter le seuil de franchissement |
| `-` | Diminuer le seuil de franchissement |

## Configuration du Seuil

Le **seuil** est une valeur entre **0.0** et **1.0** qui représente la position X normalisée :
- `0.0` = bord gauche de l'image
- `0.5` = milieu de l'image (défaut)
- `1.0` = bord droit de l'image

### Ajustement
- En temps réel avec `+` et `-`
- Ou modifier dans le code :
```python
system.set_threshold(0.6)  # 60% de la largeur
```

## Messages OSC Envoyés

### Caméra TOP (Surveillance)
```
/camera_top/detected      1 ou 0 (main détectée)
/camera_top/position      [x, y] (position normalisée)
/threshold/crossed        1 ou 0 (seuil franchi)
```

### Caméra FRONT (Interaction) - actif seulement si seuil franchi
```
/hand/detected           1 ou 0 (main détectée)
/hand/position           [x, y] (position normalisée)
/hand/mode               0 (draw) ou 1 (erase)
/hand/radius             0.02 (petit) ou 0.15 (grand)
/hand/confidence         0.0 à 1.0 (confiance détection)
```

### Recommandations
- **Caméra TOP** : Réglez `detection_con=0.6` (plus permissif)
- **Caméra FRONT** : Gardez `detection_con=0.7` (précis)
- Ajustez l'éclairage pour améliorer la détection

### Caméra non détectée
```bash
# Lister les caméras disponibles
ls /dev/video*
# Ou
v4l2-ctl --list-devices
```

### Performance faible
- Réduire la résolution dans `config/settings.json`
- Réduire le FPS
- Vérifier l'éclairage

### Détection instable en vue de haut
- Augmenter l'éclairage
- Baisser `detection_con` à 0.5
- Vérifier que la main est bien visible
- Positionner la caméra plus haut

### Changer la logique de franchissement
Dans `dual_camera_threshold.py`, méthode `check_threshold_crossing()` :
```python
# Par défaut : main à droite du seuil
return norm_x > self.threshold_x

# Pour inverser : main à gauche du seuil
return norm_x < self.threshold_x

# Pour seuil en Y (haut/bas) :
return norm_y > self.threshold_y
```

### Modifier les modes de détection
Dans `hand_detector.py`, méthode `detect_finger_mode()` :
- Ajuster les seuils de détection des doigts
- Ajouter d'autres gestes
- Changer la logique draw/erase