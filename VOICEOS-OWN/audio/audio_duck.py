import logging
from typing import Optional

logger = logging.getLogger("VoiceOS.AudioDuck")

class AudioDucker:
    """
    Ducks (attenuates) system background audio during user dictation or assistant speech.
    Equivalent to VoiceOS audio-duck.exe.
    """
    def __init__(self, duck_factor: float = 0.3):
        self.duck_factor = duck_factor
        self._original_volume: Optional[float] = None
        self._is_ducked = False

    def duck(self):
        """Reduces master or endpoint volume."""
        if self._is_ducked:
            return
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from comtypes import CLSCTX_ALL
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)
            self._original_volume = volume.GetMasterVolumeLevelScalar()
            # Duck volume by factor
            ducked_vol = max(0.05, self._original_volume * self.duck_factor)
            volume.SetMasterVolumeLevelScalar(ducked_vol, None)
            self._is_ducked = True
            logger.info(f"Audio ducked to {ducked_vol:.2f} (from {self._original_volume:.2f})")
        except Exception as e:
            logger.debug(f"Audio ducking not available or failed: {e}")

    def unduck(self):
        """Restores original volume."""
        if not self._is_ducked or self._original_volume is None:
            return
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from comtypes import CLSCTX_ALL
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)
            volume.SetMasterVolumeLevelScalar(self._original_volume, None)
            self._is_ducked = False
            logger.info("Audio volume restored.")
        except Exception as e:
            logger.debug(f"Audio unducking error: {e}")
        finally:
            self._is_ducked = False
            self._original_volume = None
