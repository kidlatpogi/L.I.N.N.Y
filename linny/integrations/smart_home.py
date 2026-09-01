"""
Smart Home Integration Subsystem (Tapo L530E & TP-Link Kasa Devices).
Uses modern python-kasa with asynchronous execution, credential-based auth,
and non-blocking background workers.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from typing import Any, Dict, Optional, Tuple

from ..core.config import LinnyConfig
from ..core.events import EventBus, EventType
from ..core.logger import get_logger

logger = get_logger("smarthome")

# Color Presets (HSV: Hue 0-360, Sat 0-100, Val 0-100)
COLOR_PRESETS: Dict[str, Tuple[int, int, int]] = {
    "red": (0, 100, 100),
    "crimson": (348, 90, 90),
    "blue": (240, 100, 100),
    "cyan": (180, 100, 100),
    "green": (120, 100, 100),
    "violet": (270, 100, 100),
    "purple": (280, 100, 80),
    "yellow": (60, 100, 100),
    "orange": (30, 100, 100),
    "pink": (330, 70, 100),
}


class SmartDeviceManager:
    """Non-blocking, thread-safe manager for Kasa and Tapo smart devices."""

    def __init__(self, config: LinnyConfig) -> None:
        self.config = config
        self._device = None
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="LinnySmartHome")
        self._event_bus = EventBus()
        self._connected = False
        self._connecting = False

        if self.config.smart_bulb_enabled:
            self._async_connect()

    def close(self) -> None:
        """Shutdown thread executor and background workers."""
        try:
            self._executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass

    def reload(self, config: LinnyConfig) -> None:
        """Reload configuration and reconnect."""
        self.config = config
        self._device = None
        self._connected = False
        if self.config.smart_bulb_enabled:
            self._async_connect()

    def _async_connect(self) -> None:
        """Initiate non-blocking connection to smart bulb."""
        if self._connecting:
            return
        self._connecting = True
        self._executor.submit(self._connect_sync)

    def _connect_sync(self) -> bool:
        """Connect to device using asyncio."""
        self._connecting = True
        try:
            from kasa import Credentials, Discover

            ip = self.config.smart_bulb_ip.strip()
            if not ip or ip in ("<BULB_IP>", "192.168.1.100", "0.0.0.0"):
                logger.info("Smart bulb IP not configured or set to placeholder")
                self._connected = False
                self._connecting = False
                return False

            logger.info(f"Connecting to smart bulb at {ip}...")

            async def _discover() -> Any:
                creds = None
                if self.config.tapo_email and self.config.tapo_password:
                    creds = Credentials(
                        username=self.config.tapo_email,
                        password=self.config.tapo_password,
                    )
                dev = await Discover.discover_single(ip, credentials=creds, timeout=4)
                if dev:
                    await dev.update()
                return dev

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                self._device = loop.run_until_complete(_discover())
                self._connected = bool(self._device is not None)
                if self._connected:
                    logger.info(f"Connected to smart bulb: {self._device.alias} ({self._device.model})")
                    self._event_bus.publish(EventType.SMART_HOME_UPDATE, {"state": "connected", "alias": self._device.alias})
                else:
                    logger.warning(f"Could not reach smart bulb at {ip}")
            finally:
                loop.close()

            self._connecting = False
            return self._connected
        except Exception as e:
            logger.warning(f"Smart bulb connection failed ({e})")
            self._device = None
            self._connected = False
            self._connecting = False
            return False

    def _run_device_action(self, action_coro_fn) -> bool:
        """Execute an asynchronous device action in the executor."""
        if not self._connected or not self._device:
            # Try to connect once if not connected
            if not self._connect_sync() or not self._device:
                return False

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(action_coro_fn(self._device))
                return True
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Smart home action error: {e}")
            self._connected = False
            return False

    def turn_on(self) -> bool:
        """Turn on the smart light."""
        async def _action(dev: Any) -> None:
            await dev.turn_on()
            await dev.update()

        future = self._executor.submit(self._run_device_action, _action)
        try:
            res = future.result(timeout=5)
            if res:
                logger.info("Smart light turned ON")
                self._event_bus.publish(EventType.SMART_HOME_UPDATE, {"state": "on"})
            return res
        except Exception as e:
            logger.warning(f"Turn on timeout or error: {e}")
            return False

    def turn_off(self) -> bool:
        """Turn off the smart light."""
        async def _action(dev: Any) -> None:
            await dev.turn_off()
            await dev.update()

        future = self._executor.submit(self._run_device_action, _action)
        try:
            res = future.result(timeout=5)
            if res:
                logger.info("Smart light turned OFF")
                self._event_bus.publish(EventType.SMART_HOME_UPDATE, {"state": "off"})
            return res
        except Exception as e:
            logger.warning(f"Turn off timeout or error: {e}")
            return False

    def set_brightness(self, level: int) -> bool:
        """Set brightness level (1-100%)."""
        clamped = max(1, min(100, int(level)))

        async def _action(dev: Any) -> None:
            from kasa import Module
            light = dev.modules.get(Module.Light) if hasattr(dev, "modules") else None
            if not light and hasattr(dev, "modules"):
                light = dev.modules.get("Light")

            if light and hasattr(light, "set_brightness"):
                await light.set_brightness(clamped)
            elif hasattr(dev, "set_brightness"):
                await dev.set_brightness(clamped)
            await dev.update()

        future = self._executor.submit(self._run_device_action, _action)
        try:
            res = future.result(timeout=5)
            if res:
                logger.info(f"Smart light brightness set to {clamped}%")
                self._event_bus.publish(EventType.SMART_HOME_UPDATE, {"brightness": clamped})
            return res
        except Exception as e:
            logger.warning(f"Set brightness error: {e}")
            return False

    def set_color_temp(self, temp_kelvin: int) -> bool:
        """Set white color temperature (2500K - 6500K)."""
        async def _action(dev: Any) -> None:
            from kasa import Module
            light = dev.modules.get(Module.Light) if hasattr(dev, "modules") else None
            if not light and hasattr(dev, "modules"):
                light = dev.modules.get("Light")

            if light and hasattr(light, "set_color_temp"):
                await light.set_color_temp(temp_kelvin)
            elif hasattr(dev, "set_color_temp"):
                await dev.set_color_temp(temp_kelvin)
            await dev.update()

        future = self._executor.submit(self._run_device_action, _action)
        try:
            return future.result(timeout=5)
        except Exception as e:
            logger.warning(f"Set color temp error: {e}")
            return False

    def set_hsv(self, h: int, s: int, v: int) -> bool:
        """Set HSV color."""
        async def _action(dev: Any) -> None:
            from kasa import Module
            light = dev.modules.get(Module.Light) if hasattr(dev, "modules") else None
            if not light and hasattr(dev, "modules"):
                light = dev.modules.get("Light")

            if light and hasattr(light, "set_hsv"):
                await light.set_hsv(h, s, v)
            elif hasattr(dev, "set_hsv"):
                await dev.set_hsv(h, s, v)
            await dev.update()

        future = self._executor.submit(self._run_device_action, _action)
        try:
            return future.result(timeout=5)
        except Exception as e:
            logger.warning(f"Set HSV color error: {e}")
            return False

    def set_color(self, color_name: str) -> bool:
        """Set color by name."""
        name = color_name.lower().strip()
        if name in ("warm", "warm white"):
            return self.set_color_temp(2700)
        elif name in ("daylight", "cool", "cool white", "white"):
            return self.set_color_temp(5500)
        elif name in COLOR_PRESETS:
            h, s, v = COLOR_PRESETS[name]
            return self.set_hsv(h, s, v)
        return False

    def set_mode(self, mode: str) -> bool:
        """
        Set lighting mode preset:
        - Focus: 6000K, 100% Brightness
        - Movie: 2500K, 30% Brightness
        - Gaming: Purple HSV(280, 100, 75)
        - Night: 2200K, 10% Brightness
        - Relax: Warm 2700K, 50% Brightness
        """
        mode_lower = mode.lower().strip()
        if "focus" in mode_lower:
            self.set_brightness(100)
            return self.set_color_temp(6000)
        elif "movie" in mode_lower or "cinema" in mode_lower:
            self.set_brightness(30)
            return self.set_color_temp(2500)
        elif "gaming" in mode_lower or "game" in mode_lower:
            return self.set_hsv(280, 100, 75)
        elif "night" in mode_lower or "sleep" in mode_lower:
            self.set_brightness(10)
            return self.set_color_temp(2200)
        elif "relax" in mode_lower or "chill" in mode_lower:
            self.set_brightness(50)
            return self.set_color_temp(2700)
        else:
            logger.warning(f"Unknown light mode preset: {mode}")
            return False

    def is_connected(self) -> bool:
        return self._connected
