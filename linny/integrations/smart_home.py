"""
Smart Home Integration Subsystem (Tapo L530E/L510 & TP-Link Kasa Devices).
Features:
- Fix for Tapo TPAP / KLAP protocol negotiation on HTTP Port 80
- Local LAN Subnet Smart Device Scanner
- Asynchronous non-blocking control for Turn On/Off, Brightness, Colors, and Presets
- Explicit device type picker & Tapo cloud authentication with clear 403 diagnostics
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from typing import Any, Dict, List, Optional, Tuple

from ..core.config import LinnyConfig
from ..core.events import EventBus, EventType
from ..core.logger import get_logger

logger = get_logger("smarthome")

# Patch python-kasa TPAP -> KLAP mapping
try:
    import kasa.deviceconfig
    _orig_from_values = kasa.deviceconfig.DeviceConnectionParameters.from_values

    def _patched_from_values(device_family, encryption_type, *args, **kwargs):
        if str(encryption_type).upper() in ("TPAP", "KLAP"):
            encryption_type = "KLAP"
        return _orig_from_values(device_family, encryption_type, *args, **kwargs)

    kasa.deviceconfig.DeviceConnectionParameters.from_values = _patched_from_values
except Exception as patch_err:
    logger.debug(f"Could not patch kasa deviceconfig: {patch_err}")

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

DEVICE_FAMILIES = {
    "Tapo Smart Bulb (L530E/L510/L520)": "SMART.TAPOBULB",
    "Tapo Smart Plug (P100/P110)": "SMART.TAPOPLUG",
    "Kasa Smart Bulb (KL110/KL125/KL130)": "IOT.SMARTBULB",
    "Kasa Smart Plug (KP115/HS100/HS110)": "IOT.SMARTPLUGSWITCH",
    "Auto-Detect / Generic": "AUTO",
}


class SmartDeviceManager:
    """Non-blocking, thread-safe manager for Kasa and Tapo smart devices."""

    def __init__(self, config: LinnyConfig) -> None:
        self.config = config
        self._device = None
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=3, thread_name_prefix="LinnySmartHome")
        self._event_bus = EventBus()
        self._connected = False
        self._connecting = False

        if self.config.smart_bulb_enabled:
            self._async_connect()

    def close(self) -> None:
        """Shutdown background thread workers."""
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
        """Initiate non-blocking connection in worker thread."""
        if self._connecting:
            return
        self._connecting = True
        self._executor.submit(self._connect_sync)

    def _connect_sync(self) -> bool:
        """Connect to device using python-kasa with Tapo/Kasa protocol routing."""
        self._connecting = True
        try:
            from kasa import Credentials, Device, DeviceConfig, DeviceConnectionParameters, DeviceEncryptionType, DeviceFamily, Discover

            ip = self.config.smart_bulb_ip.strip()
            if not ip or ip in ("<BULB_IP>", "0.0.0.0"):
                logger.info("Smart bulb IP not configured")
                self._connected = False
                self._connecting = False
                return False

            logger.info(f"Connecting to smart device at {ip} (Family: {self.config.smart_bulb_family})...")

            async def _connect_task() -> Any:
                creds = None
                if self.config.tapo_email and self.config.tapo_password:
                    creds = Credentials(
                        username=self.config.tapo_email,
                        password=self.config.tapo_password,
                    )

                # Route 1: Tapo Devices (KLAP HTTP Port 80)
                is_tapo = "TAPO" in self.config.smart_bulb_family or self.config.smart_bulb_family == "SMART.TAPOBULB"
                if is_tapo:
                    family = DeviceFamily.SmartTapoBulb if "BULB" in self.config.smart_bulb_family else DeviceFamily.SmartTapoPlug
                    params = DeviceConnectionParameters(
                        device_family=family,
                        encryption_type=DeviceEncryptionType.Klap,
                        login_version=2,
                        https=False,
                        http_port=80,
                    )
                    cfg = DeviceConfig(host=ip, credentials=creds, connection_type=params)
                    try:
                        dev = await Device.connect(config=cfg)
                        await dev.update()
                        return dev
                    except Exception as e:
                        err_str = str(e).lower()
                        if "403" in err_str or "auth" in err_str:
                            logger.warning("Tapo Authentication Required: Please enter your Tapo email and password in Settings.")
                        else:
                            logger.debug(f"Direct Tapo connection error: {e}")

                # Route 2: Discover Single
                try:
                    dev = await Discover.discover_single(ip, credentials=creds, timeout=4)
                    if dev:
                        await dev.update()
                        return dev
                except Exception as e:
                    logger.debug(f"Discover single error: {e}")

                # Route 3: Standard Kasa IOT device (port 9999) only if NOT Tapo
                if not is_tapo:
                    cfg = DeviceConfig(host=ip, credentials=creds)
                    dev = await Device.connect(config=cfg)
                    await dev.update()
                    return dev

                return None

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                self._device = loop.run_until_complete(_connect_task())
                self._connected = bool(self._device is not None)
                if self._connected:
                    logger.info(f"Connected to smart device: {self._device.alias} ({self._device.model})")
                    self._event_bus.publish(
                        EventType.SMART_HOME_UPDATE,
                        {"state": "connected", "alias": self._device.alias, "model": self._device.model},
                    )
                else:
                    logger.warning(f"Could not reach smart device at {ip}")
            finally:
                loop.close()

            self._connecting = False
            return self._connected
        except Exception as e:
            logger.warning(f"Smart bulb connection failed: {e}")
            self._device = None
            self._connected = False
            self._connecting = False
            return False

    def scan_network_devices(self, timeout: float = 4.0) -> List[Dict[str, Any]]:
        """
        Scan local network for TP-Link Kasa and Tapo smart devices.
        Returns list of dicts with {ip, alias, model, family, mac}.
        """
        logger.info("Scanning local network for smart devices...")
        discovered_list: List[Dict[str, Any]] = []

        try:
            from kasa import Credentials, Discover

            creds = None
            if self.config.tapo_email and self.config.tapo_password:
                creds = Credentials(username=self.config.tapo_email, password=self.config.tapo_password)

            async def _scan() -> Dict[str, Any]:
                return await Discover.discover(credentials=creds, timeout=int(timeout))

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                results = loop.run_until_complete(_scan())
                for ip, dev in results.items():
                    discovered_list.append({
                        "ip": ip,
                        "alias": getattr(dev, "alias", "Smart Device"),
                        "model": getattr(dev, "model", "Unknown"),
                        "family": getattr(dev, "device_type", "SMART.TAPOBULB"),
                        "mac": getattr(dev, "mac", ""),
                    })
            finally:
                loop.close()

        except Exception as e:
            logger.warning(f"Network discovery scan error: {e}")

        if not discovered_list:
            if self.config.smart_bulb_ip and self.config.smart_bulb_ip not in ("<BULB_IP>", "0.0.0.0"):
                discovered_list.append({
                    "ip": self.config.smart_bulb_ip,
                    "alias": "Configured Bulb",
                    "model": "Tapo / Kasa",
                    "family": self.config.smart_bulb_family,
                    "mac": "",
                })

        logger.info(f"Scan complete: Found {len(discovered_list)} device(s)")
        return discovered_list

    def _run_device_action(self, action_coro_fn) -> bool:
        """Execute an asynchronous device action in the executor."""
        if not self._connected or not self._device:
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
            logger.warning(f"Turn on error: {e}")
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
            logger.warning(f"Turn off error: {e}")
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
