from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsItem
from PySide6.QtCore import QObject, QPropertyAnimation, QPointF, QEasingCurve, Property, Qt
from PySide6.QtGui import QPixmap
import os
import json

# Helper Wrapper to make QGraphicsPixmapItem animatable via QPropertyAnimation
class SpriteItem(QObject, QGraphicsPixmapItem):
    def __init__(self, pixmap):
        QObject.__init__(self)
        QGraphicsPixmapItem.__init__(self, pixmap)
        self.face_item = None
    
    def set_face(self, face_pixmap: QPixmap):
        if not self.face_item:
            self.face_item = QGraphicsPixmapItem(self) # Parent is self
            self.face_item.setPos(0, 0)
        
        self.face_item.setPixmap(face_pixmap)

    def get_pos(self):
        return QGraphicsPixmapItem.pos(self)
    
    def set_pos(self, pos):
        QGraphicsPixmapItem.setPos(self, pos)
        
    # Property for QPropertyAnimation
    pos = Property(QPointF, get_pos, set_pos)

class BackgroundItem(QObject, QGraphicsPixmapItem):
    def __init__(self, pixmap=None):
        QObject.__init__(self)
        if pixmap:
            QGraphicsPixmapItem.__init__(self, pixmap)
        else:
            QGraphicsPixmapItem.__init__(self)

    def get_opacity(self):
        return self.opacity()
    
    def set_opacity(self, opacity):
        self.setOpacity(opacity)
        
    opacity = Property(float, get_opacity, set_opacity)

class VisualManager(QObject):
    def __init__(self, scene: QGraphicsScene):
        super().__init__()
        self.scene = scene
        
        # Layers
        self.bg_layer_1 = BackgroundItem()
        self.bg_layer_2 = BackgroundItem()
        self.sprite_layer = {} # name -> item
        
        # Setup Backgrounds (Double Buffering)
        # Z-Value: -100 (Far back)
        self.scene.addItem(self.bg_layer_1)
        self.scene.addItem(self.bg_layer_2)
        self.bg_layer_1.setZValue(-100)
        self.bg_layer_2.setZValue(-99) # Slightly above for crossfade
        
        self.active_bg = 1 # 1 or 2
        self.bg_layer_2.setOpacity(0) # Start invisible
        
        # Load Presets
        self.presets = {}
        self.load_presets()
        
        # Load Character Map
        self.char_map = {}
        self.load_char_map()
        
        # Load Background Map
        self.bg_map = {}
        self.load_bg_map()

    def load_presets(self):
        try:
            with open("assets/presets.json", "r", encoding="utf-8") as f:
                self.presets = json.load(f)
        except Exception as e:
            print(f"[VisualManager] Failed to load presets: {e}")

    def load_char_map(self):
        try:
            with open("assets/character_map.json", "r", encoding="utf-8") as f:
                self.char_map = json.load(f)
        except Exception as e:
            print(f"[VisualManager] Failed to load character map: {e}")

    def load_bg_map(self):
        try:
            with open("assets/background_map.json", "r", encoding="utf-8") as f:
                self.bg_map = json.load(f)
        except Exception as e:
            print(f"[VisualManager] Failed to load background map: {e}")
            
    # ... join_character ...

    def join_character(self, char_name: str, preset: str = "pos_center"):
        """
        Spawns a character using their default body/expression from the map.
        """
        if char_name not in self.char_map:
            print(f"[VisualManager] Cannot join {char_name}: Not in map.")
            return

        char_data = self.char_map[char_name]
        body_path = char_data.get("body")
        
        # Pick default face (first one or specific 'default' key)
        face_path = None
        if "expressions" in char_data and char_data["expressions"]:
            if "default" in char_data["expressions"]:
                face_path = char_data["expressions"]["default"]
            else:
                # Pick first available
                face_path = list(char_data["expressions"].values())[0]
        
        # Add character
        self.add_character(char_name, body_path, face_path)
        
        # Apply initial preset (position)
        if preset:
            self.apply_preset(char_name, preset)

    def set_expression(self, char_name: str, expression: str):
        """
        Changes the face of a character using the character map.
        """
        if char_name not in self.char_map:
            print(f"[VisualManager] Character not found in map: {char_name}")
            return
            
        char_data = self.char_map[char_name]
        
        if expression not in char_data["expressions"]:
            print(f"[VisualManager] Expression '{expression}' not found for {char_name}")
            return
            
        face_path = char_data["expressions"][expression]
        
        if char_name in self.sprite_layer:
            item = self.sprite_layer[char_name]
            if isinstance(item, SpriteItem):
                if os.path.exists(face_path):
                    item.set_face(QPixmap(face_path))
                else:
                    print(f"[VisualManager] Face file missing: {face_path}")
        else:
            # Auto-add character if not present
            body_path = char_data.get("body")
            if body_path and os.path.exists(body_path):
                self.add_character(char_name, body_path, face_path)
            else:
                print(f"[VisualManager] Cannot spawn {char_name}, body missing.")

    def apply_preset(self, sprite_name: str, preset_name: str):
        """
        Applies a named preset from assets/presets.json to a sprite.
        """
        if sprite_name not in self.sprite_layer:
            return
        
        if preset_name not in self.presets:
            print(f"[VisualManager] Preset not found: {preset_name}")
            return
            
        data = self.presets[preset_name]
        
        x = data.get("x")
        y = data.get("y")
        scale = data.get("scale")
        
        self.set_sprite_transform(sprite_name, x, y, scale)

    def set_background(self, image_path: str, fade_duration: int = 1000):
        """
        Cross-fades to new background. 
        image_path can be a file path OR a key in background_map.json.
        """
        # 1. Lookup in Map
        if image_path in self.bg_map:
            real_path = self.bg_map[image_path]["file"]
        else:
            real_path = image_path

        # 2. Check Existence
        if not os.path.exists(real_path):
            # Try prepending assets/bg/ if simple filename provided
            fallback_path = os.path.join("assets/bg", real_path)
            if os.path.exists(fallback_path):
                real_path = fallback_path
            else:
                print(f"[VisualManager] BG not found: {real_path} (Key: {image_path})")
                return

        pixmap = QPixmap(real_path)
        
        if self.active_bg == 1:
            target_item = self.bg_layer_2
            current_item = self.bg_layer_1
            self.active_bg = 2
        else:
            target_item = self.bg_layer_1
            current_item = self.bg_layer_2
            self.active_bg = 1
            
        target_item.setPixmap(pixmap)
        target_item.setOpacity(0)
        
        self.anim_in = QPropertyAnimation(target_item, b"opacity")
        self.anim_in.setDuration(fade_duration)
        self.anim_in.setStartValue(0.0)
        self.anim_in.setEndValue(1.0)
        self.anim_in.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        self.anim_out = QPropertyAnimation(current_item, b"opacity")
        self.anim_out.setDuration(fade_duration)
        self.anim_out.setStartValue(1.0)
        self.anim_out.setEndValue(0.0)
        self.anim_out.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        self.anim_in.start()
        self.anim_out.start()

    def add_sprite(self, name: str, image_path: str, x: int, y: int, z_value: float = 0.0, scale: float = 1.0):
        self.add_character(name, image_path, None, x, y, z_value, scale)

    def add_character(self, name: str, body_path: str, face_path: str = None, x: int = 0, y: int = 0, z_value: float = 0.0, scale: float = 1.0):
        if name in self.sprite_layer:
            self.scene.removeItem(self.sprite_layer[name])
            del self.sprite_layer[name]
        
        if not os.path.exists(body_path):
            print(f"[VisualManager] Body not found: {body_path}")
            return

        item = SpriteItem(QPixmap(body_path))
        
        if face_path:
            if os.path.exists(face_path):
                item.set_face(QPixmap(face_path))
            else:
                print(f"[VisualManager] Face not found: {face_path}")

        item.setPos(x, y)
        item.setScale(scale)
        item.setZValue(z_value)
        
        self.scene.addItem(item)
        self.sprite_layer[name] = item

    def set_sprite_transform(self, name: str, x: float = None, y: float = None, scale: float = None):
        if name not in self.sprite_layer:
            return
            
        item = self.sprite_layer[name]
        
        if x is not None or y is not None:
            current_pos = item.pos
            new_x = x if x is not None else current_pos.x()
            new_y = y if y is not None else current_pos.y()
            item.setPos(new_x, new_y)
            
        if scale is not None:
            item.setScale(scale)

    def remove_sprite(self, name: str):
        if name in self.sprite_layer:
            self.scene.removeItem(self.sprite_layer[name])
            del self.sprite_layer[name]

    def clear_all_sprites(self):
        for name in list(self.sprite_layer.keys()):
            self.remove_sprite(name)

    def animate_sprite(self, name: str, animation_type: str):
        if name not in self.sprite_layer:
            return
            
        item = self.sprite_layer[name]
        
        if animation_type == "shake":
            anim = QPropertyAnimation(item, b"pos")
            anim.setDuration(500)
            start_pos = item.pos
            anim.setKeyValueAt(0, start_pos)
            anim.setKeyValueAt(0.1, start_pos + QPointF(10, 0))
            anim.setKeyValueAt(0.2, start_pos + QPointF(-10, 0))
            anim.setKeyValueAt(0.3, start_pos + QPointF(10, 0))
            anim.setKeyValueAt(0.4, start_pos + QPointF(-10, 0))
            anim.setKeyValueAt(1.0, start_pos)
            item.active_animation = anim
            anim.start()
            
        elif animation_type == "jump":
            anim = QPropertyAnimation(item, b"pos")
            anim.setDuration(600)
            start_pos = item.pos
            anim.setKeyValueAt(0, start_pos)
            anim.setKeyValueAt(0.5, start_pos + QPointF(0, -50))
            anim.setKeyValueAt(1.0, start_pos)
            anim.setEasingCurve(QEasingCurve.Type.OutQuad)
            item.active_animation = anim
            anim.start()