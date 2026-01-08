from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl, QPropertyAnimation, QObject, Property, QEasingCurve
import os

class AudioManager(QObject):
    def __init__(self):
        super().__init__()
        
        # 1. BGM Channel (Dual for Cross-fade)
        self.player_bgm_a = QMediaPlayer()
        self.output_bgm_a = QAudioOutput()
        self.player_bgm_a.setAudioOutput(self.output_bgm_a)
        self.player_bgm_a.errorOccurred.connect(lambda e, s: print(f"[Audio BGM A Error] {e}: {s}"))
        
        self.player_bgm_b = QMediaPlayer()
        self.output_bgm_b = QAudioOutput()
        self.player_bgm_b.setAudioOutput(self.output_bgm_b)
        self.player_bgm_b.errorOccurred.connect(lambda e, s: print(f"[Audio BGM B Error] {e}: {s}"))
        
        self.bgm_active = "A" # A or B
        self._bgm_master_volume = 1.0 # 0.0 to 1.0

        # 2. SFX Channel
        self.player_sfx = QMediaPlayer()
        self.output_sfx = QAudioOutput()
        self.player_sfx.setAudioOutput(self.output_sfx)
        self.player_sfx.errorOccurred.connect(lambda e, s: print(f"[Audio SFX Error] {e}: {s}"))
        self._sfx_volume = 1.0

        # 2.1 SFX Loop Channel (Ambience)
        self.player_sfx_loop = QMediaPlayer()
        self.output_sfx_loop = QAudioOutput()
        self.player_sfx_loop.setAudioOutput(self.output_sfx_loop)
        self.player_sfx_loop.errorOccurred.connect(lambda e, s: print(f"[Audio Loop Error] {e}: {s}"))

        # 3. Voice/Other Channel
        self.player_voice = QMediaPlayer()
        self.output_voice = QAudioOutput()
        self.player_voice.setAudioOutput(self.output_voice)
        self.player_voice.errorOccurred.connect(lambda e, s: print(f"[Audio Voice Error] {e}: {s}"))
        self._voice_volume = 1.0

    # --- Volume Properties for UI ---
    def set_bgm_volume(self, val: float):
        """Sets master volume for BGM (0.0 - 1.0). affects both players."""
        self._bgm_master_volume = val
        self.output_bgm_a.setVolume(val) 
        self.output_bgm_b.setVolume(val)

    def set_sfx_volume(self, val: float):
        self._sfx_volume = val
        self.output_sfx.setVolume(val)
        self.output_sfx_loop.setVolume(val)

    def set_voice_volume(self, val: float):
        self._voice_volume = val
        self.output_voice.setVolume(val)

    # --- Playback Methods ---

    # Properties for Animation (Cross-fade internal logic)
    # We rename to explicit internal volumes to avoid confusion with master volume
    def get_fade_vol_a(self): return self.output_bgm_a.volume()
    def set_fade_vol_a(self, v): self.output_bgm_a.setVolume(v * self._bgm_master_volume)
    
    def get_fade_vol_b(self): return self.output_bgm_b.volume()
    def set_fade_vol_b(self, v): self.output_bgm_b.setVolume(v * self._bgm_master_volume)
        
    # Expose for PropertyAnimation
    fade_a = Property(float, get_fade_vol_a, set_fade_vol_a)
    fade_b = Property(float, get_fade_vol_b, set_fade_vol_b)

    def play_bgm(self, file_path: str, fade_duration: int = 2000):
        abs_path = os.path.abspath(file_path)
        url = QUrl.fromLocalFile(abs_path)
        
        if self.bgm_active == "A":
            # Switch to B
            target_player = self.player_bgm_b
            target_prop = b"fade_b"
            fade_out_prop = b"fade_a"
            self.bgm_active = "B"
        else:
            # Switch to A
            target_player = self.player_bgm_a
            target_prop = b"fade_a"
            fade_out_prop = b"fade_b"
            self.bgm_active = "A"
            
        target_player.stop() # Ensure stopped before changing source
        target_player.setSource(url)
        target_player.setLoops(QMediaPlayer.Loops.Infinite) # BGM always loops
        
        # Start silent (relative to master)
        if self.bgm_active == "A": self.set_fade_vol_a(0)
        else: self.set_fade_vol_b(0)
        target_player.play()
        
        # Animate
        self.anim_in = QPropertyAnimation(self, target_prop)
        self.anim_in.setDuration(fade_duration)
        self.anim_in.setStartValue(0.0)
        self.anim_in.setEndValue(1.0) # This 1.0 is multiplier for master volume
        
        self.anim_out = QPropertyAnimation(self, fade_out_prop)
        self.anim_out.setDuration(fade_duration)
        self.anim_out.setStartValue(1.0)
        self.anim_out.setEndValue(0.0)
        
        self.anim_in.start()
        self.anim_out.start()

    def play_sfx(self, file_path: str, loop: bool = False):
        abs_path = os.path.abspath(file_path)
        url = QUrl.fromLocalFile(abs_path)
        
        # Check existence explicitly for debug
        if not os.path.exists(abs_path):
            print(f"[Audio] Error: SFX file not found at {abs_path}")
            return

        if loop:
            self.player_sfx_loop.stop() # Stop before reloading
            self.player_sfx_loop.setSource(url)
            self.output_sfx_loop.setVolume(self._sfx_volume)
            self.player_sfx_loop.setLoops(QMediaPlayer.Loops.Infinite)
            self.player_sfx_loop.play()
        else:
            self.player_sfx.stop() # Stop before reloading
            self.player_sfx.setSource(url)
            self.output_sfx.setVolume(self._sfx_volume)
            self.player_sfx.setLoops(1)
            self.player_sfx.play()

    def stop_looping_sfx(self):
        self.player_sfx_loop.stop()
        
    def stop_sfx(self):
        """Stops all SFX playback (one-shot and loop)."""
        self.player_sfx.stop()
        self.player_sfx_loop.stop()

    def play_voice(self, file_path: str):
        abs_path = os.path.abspath(file_path)
        self.player_voice.stop() # Stop before reloading
        self.player_voice.setSource(QUrl.fromLocalFile(abs_path))
        self.output_voice.setVolume(self._voice_volume)
        self.player_voice.play()

    def stop_bgm(self):
        """Stops all BGM playback immediately."""
        self.player_bgm_a.stop()
        self.player_bgm_b.stop()
