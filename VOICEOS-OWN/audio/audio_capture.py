import time
import queue
import wave
import tempfile
import numpy as np
import sounddevice as sd
import logging
from typing import Optional, Callable, List, Dict, Any

logger = logging.getLogger("VoiceOS.AudioCapture")

class AudioCaptureService:
    """
    Captures microphone input using sounddevice (WASAPI on Windows)
    and computes real-time volume updates for UI waveforms.
    Equivalent to VoiceOS microphone-capture.exe.
    """
    def __init__(self, sample_rate: int = 48000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_recording = False
        self._stream: Optional[sd.InputStream] = None
        self._audio_queue = queue.Queue()
        self._recorded_frames: List[np.ndarray] = []
        self._on_volume_update: Optional[Callable[[float], None]] = None

    def set_volume_callback(self, callback: Callable[[float], None]):
        self._on_volume_update = callback

    @staticmethod
    def get_devices() -> List[Dict[str, Any]]:
        """Returns available input audio devices."""
        devices = []
        try:
            for idx, dev in enumerate(sd.query_devices()):
                if dev.get("max_input_channels", 0) > 0:
                    devices.append({
                        "id": idx,
                        "name": dev.get("name", f"Device {idx}"),
                        "host_api": dev.get("hostapi"),
                        "channels": dev.get("max_input_channels")
                    })
        except Exception as e:
            logger.error(f"Error querying audio devices: {e}")
        return devices

    def start_recording(self, device_id: Optional[int] = None) -> bool:
        if self.is_recording:
            return True

        self._recorded_frames = []
        self.is_recording = True

        def _callback(indata, frames, time_info, status):
            if status:
                logger.debug(f"Audio status: {status}")
            if self.is_recording:
                # Copy frame
                frame = indata.copy()
                self._recorded_frames.append(frame)

                # Compute RMS volume (0.0 to 1.0 scale)
                if self._on_volume_update:
                    rms = np.sqrt(np.mean(frame**2))
                    # Normalizing for UI wave (boosted scale)
                    vol = min(1.0, float(rms * 10))
                    try:
                        self._on_volume_update(vol)
                    except Exception:
                        pass

        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                device=device_id,
                callback=_callback,
                dtype="float32"
            )
            self._stream.start()
            logger.info("Microphone capture started.")
            return True
        except Exception as e:
            logger.error(f"Failed to start audio stream: {e}")
            self.is_recording = False
            return False

    def stop_recording(self) -> Optional[str]:
        """
        Stops recording and returns path to saved temporary .wav file.
        """
        if not self.is_recording:
            return None

        self.is_recording = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        if not self._recorded_frames:
            return None

        try:
            # Concatenate all frames
            audio_data = np.concatenate(self._recorded_frames, axis=0)
            # Convert float32 to int16 PCM
            audio_int16 = (audio_data * 32767).astype(np.int16)

            temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            with wave.open(temp_wav.name, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2) # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_int16.tobytes())

            logger.info(f"Recorded audio saved to: {temp_wav.name}")
            return temp_wav.name
        except Exception as e:
            logger.error(f"Error finalizing audio recording: {e}")
            return None

    def cancel_recording(self):
        """Discards active recording."""
        self.is_recording = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        self._recorded_frames = []
