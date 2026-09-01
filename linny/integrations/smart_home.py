"""
Smart Home Integration Subsystem (Tapo L530E/L535E/L510 & TP-Link Kasa Devices).
Architecture:
- Dedicated persistent background asyncio event loop thread
- 100% non-blocking async execution for Turn On/Off, Brightness, Colors, and Presets
- Tapo KLAP HTTP Port 80 connection routing with credentials support
- Real-time diagnostic connection tester that never hangs
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple

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
    "Tapo Smart Bulb (L530E/L535E/L510)": "SMART.TAPOBULB",
    "Tapo Smart Plug (P100/P110)": "SMART.TAPOPLUG",
    "Kasa Smart Bulb (KL110/KL125/KL130)": "IOT.SMARTBULB",
    "Kasa Smart Plug (KP115/HS100/HS110)": "IOT.SMARTPLUGSWITCH",
    "Auto-Detect / Generic": "AUTO",
}


class SmartDeviceManager:
    """Non-blocking, persistent asyncio-loop manager for Kasa and Tapo smart devices."""

    def __init__(self, config: LinnyConfig) -> None:
        self.config = config
        self._device = None
        self._event_bus = EventBus()
        self._connected = False
        self._is_connecting = False

        # Dedicated persistent event loop running in a daemon thread
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="SmartHomeEventLoop")
        self._thread.start()

        if self.config.smart_bulb_enabled:
            self._async_connect()

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def close(self) -> None:
        """Shutdown background thread workers cleanly."""
        try:
            async def _shutdown():
                if self._device and hasattr(self._device, "disconnect"):
                    try:
                        await self._device.disconnect()
                    except Exception:
                        pass
                self._device = None
                self._connected = False

            future = asyncio.run_coroutine_threadsafe(_shutdown(), self._loop)
            try:
                future.result(timeout=1.0)
            except Exception:
                pass
            self._loop.call_soon_threadsafe(self._loop.stop)
        except Exception:
            pass

    def reload(self, config: LinnyConfig) -> None:
        """Reload configuration and reconnect asynchronously."""
        self.config = config
        self._connected = False
        if self.config.smart_bulb_enabled:
            self._async_connect()

    def _async_connect(self, callback: Optional[Callable[[bool, str], None]] = None) -> None:
        """Initiate non-blocking connection on the persistent event loop."""
        asyncio.run_coroutine_threadsafe(self._connect_task(callback), self._loop)

    async def _connect_task(self, callback: Optional[Callable[[bool, str], None]] = None) -> bool:
        if self._is_connecting:
            return self._connected
        self._is_connecting = True
        msg = ""
        try:
            from kasa import Credentials, Device, DeviceConfig, DeviceConnectionParameters, DeviceEncryptionType, DeviceFamily, Discover

            ip = self.config.smart_bulb_ip.strip()
            if not ip or ip in ("<BULB_IP>", "0.0.0.0"):
                self._connected = False
                self._is_connecting = False
                if callback:
                    callback(False, "IP address not configured.")
                return False

            logger.info(f"Connecting to smart device at {ip} (Family: {self.config.smart_bulb_family})...")

            creds = None
            if self.config.tapo_email and self.config.tapo_password:
                creds = Credentials(
                    username=self.config.tapo_email,
                    password=self.config.tapo_password,
                )

            # Route 1: Tapo Devices via HTTP Port 80 KLAP
            is_tapo = "TAPO" in self.config.smart_bulb_family or self.config.smart_bulb_family in ("SMART.TAPOBULB", "AUTO")
            dev = None

            if is_tapo:
                family = DeviceFamily.SmartTapoBulb if "BULB" in self.config.smart_bulb_family or self.config.smart_bulb_family == "AUTO" else DeviceFamily.SmartTapoPlug
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
                except Exception as e:
                    err_str = str(e).lower()
                    if "403" in err_str or "auth" in err_str:
                        msg = "Tapo Authentication Failed (403): Check Tapo password / Device Account in Tapo App."
                        logger.warning(msg)
                    else:
                        logger.debug(f"Direct Tapo connection: {e}")

            # Route 2: Discover single device
            if not dev:
                try:
                    dev = await Discover.discover_single(ip, credentials=creds, timeout=3)
                    if dev:
                        await dev.update()
                except Exception as e:
                    logger.debug(f"Discover single: {e}")

            # Route 3: Standard Kasa IOT device (port 9999) only if not Tapo
            if not dev and not is_tapo:
                try:
                    cfg = DeviceConfig(host=ip, credentials=creds)
                    dev = await Device.connect(config=cfg)
                    await dev.update()
                except Exception as e:
                    logger.debug(f"Kasa connect: {e}")

            if dev:
                self._device = dev
                self._connected = True
                msg = f"Connected to {dev.alias or 'Smart Device'} ({dev.model})"
                logger.info(msg)
                self._event_bus.publish(
                    EventType.SMART_HOME_UPDATE,
                    {"state": "connected", "alias": dev.alias, "model": dev.model},
                )
                if callback:
                    callback(True, msg)
                return True
            else:
                self._device = None
                self._connected = False
                if not msg:
                    msg = f"Could not reach device at {ip}."
                logger.warning(msg)
                if callback:
                    callback(False, msg)
                return False

        except Exception as e:
            logger.warning(f"Smart device connection error: {e}")
            self._device = None
            self._connected = False
            if callback:
                callback(False, str(e))
            return False
        finally:
            self._is_connecting = False

    def scan_network_devices(self, timeout: float = 4.0) -> List[Dict[str, Any]]:
        """Scan local network for smart devices on the persistent loop."""
        logger.info("Scanning local network for smart devices...")
        discovered_list: List[Dict[str, Any]] = []

        async def _scan():
            from kasa import Credentials, Discover
            creds = None
            if self.config.tapo_email and self.config.tapo_password:
                creds = Credentials(username=self.config.tapo_email, password=self.config.tapo_password)
            try:
                results = await Discover.discover(credentials=creds, timeout=int(timeout))
                for ip, dev in results.items():
                    discovered_list.append({
                        "ip": ip,
                        "alias": getattr(dev, "alias", "Smart Device"),
                        "model": getattr(dev, "model", "Unknown"),
                        "family": getattr(dev, "device_type", "SMART.TAPOBULB"),
                        "mac": getattr(dev, "mac", ""),
                    })
            except Exception as e:
                logger.warning(f"Network discovery error: {e}")

        future = asyncio.run_coroutine_threadsafe(_scan(), self._loop)
        try:
            future.result(timeout=timeout + 2)
        except Exception:
            pass

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

    def _execute_device_action(self, action_fn, success_callback: Optional[Callable[[], None]] = None) -> None:
        """Execute a device action asynchronously on the persistent event loop (100% non-blocking)."""
        async def _runner():
            if not self._connected or not self._device:
                connected = await self._connect_task()
                if not connected or not self._device:
                    return

            try:
                await action_fn(self._device)
                if success_callback:
                    success_callback()
            except Exception as e:
                logger.warning(f"Smart home action error: {e}")
                self._connected = False

        asyncio.run_coroutine_threadsafe(_runner(), self._loop)

    def turn_on(self, callback: Optional[Callable[[bool], None]] = None) -> bool:
        """Turn on the smart light (Non-blocking)."""
        if not self._connected or not self._device:
            if callback:
                callback(False)
            return False

        async def _action(dev: Any):
            await dev.turn_on()
            await dev.update()
            logger.info("Smart light turned ON")
            self._event_bus.publish(EventType.SMART_HOME_UPDATE, {"state": "on"})
            if callback:
                callback(True)

        self._execute_device_action(_action)
        return True

    def turn_off(self, callback: Optional[Callable[[bool], None]] = None) -> bool:
        """Turn off the smart light (Non-blocking)."""
        if not self._connected or not self._device:
            if callback:
                callback(False)
            return False

        async def _action(dev: Any):
            await dev.turn_off()
            await dev.update()
            logger.info("Smart light turned OFF")
            self._event_bus.publish(EventType.SMART_HOME_UPDATE, {"state": "off"})
            if callback:
                callback(True)

        self._execute_device_action(_action)
        return True

    def set_brightness(self, level: int) -> bool:
        """Set brightness level 1-100% (Non-blocking)."""
        if not self._connected or not self._device:
            return False

        clamped = max(1, min(100, int(level)))

        async def _action(dev: Any):
            from kasa import Module
            light = dev.modules.get(Module.Light) if hasattr(dev, "modules") else None
            if not light and hasattr(dev, "modules"):
                light = dev.modules.get("Light")

            if light and hasattr(light, "set_brightness"):
                await light.set_brightness(clamped)
            elif hasattr(dev, "set_brightness"):
                await dev.set_brightness(clamped)
            await dev.update()
            logger.info(f"Smart light brightness set to {clamped}%")
            self._event_bus.publish(EventType.SMART_HOME_UPDATE, {"brightness": clamped})

        self._execute_device_action(_action)
        return True

    def set_color_temp(self, temp_kelvin: int) -> bool:
        """Set white color temperature (Non-blocking)."""
        if not self._connected or not self._device:
            return False

        async def _action(dev: Any):
            from kasa import Module
            light = dev.modules.get(Module.Light) if hasattr(dev, "modules") else None
            if not light and hasattr(dev, "modules"):
                light = dev.modules.get("Light")

            if light and hasattr(light, "set_color_temp"):
                await light.set_color_temp(temp_kelvin)
            elif hasattr(dev, "set_color_temp"):
                await dev.set_color_temp(temp_kelvin)
            await dev.update()

        self._execute_device_action(_action)
        return True

    def set_hsv(self, h: int, s: int, v: int) -> bool:
        """Set HSV color (Non-blocking)."""
        if not self._connected or not self._device:
            return False

        async def _action(dev: Any):
            from kasa import Module
            light = dev.modules.get(Module.Light) if hasattr(dev, "modules") else None
            if not light and hasattr(dev, "modules"):
                light = dev.modules.get("Light")

            if light and hasattr(light, "set_hsv"):
                await light.set_hsv(h, s, v)
            elif hasattr(dev, "set_hsv"):
                await dev.set_hsv(h, s, v)
            await dev.update()

        self._execute_device_action(_action)
        return True

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
        return False

    def test_connection_async(self, callback: Callable[[bool, str], None]) -> None:
        """Dedicated test connection runner with detailed diagnostics."""
        async def _test():
            try:
                from kasa import Credentials, Device, DeviceConfig, DeviceConnectionParameters, DeviceEncryptionType, DeviceFamily, Discover

                ip = self.config.smart_bulb_ip.strip()
                if not ip or ip in ("<BULB_IP>", "0.0.0.0"):
                    callback(False, "IP address not configured.")
                    return

                creds = None
                if self.config.tapo_email and self.config.tapo_password:
                    creds = Credentials(username=self.config.tapo_email, password=self.config.tapo_password)

                dev = None
                family = DeviceFamily.SmartTapoBulb if "BULB" in self.config.smart_bulb_family or self.config.smart_bulb_family == "AUTO" else DeviceFamily.SmartTapoPlug
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
                except Exception as e:
                    err_str = str(e).lower()
                    if "403" in err_str or "auth" in err_str:
                        callback(False, "Authentication Failed (403): Check Tapo password / Device Account in Tapo App.")
                        return
                    logger.debug(f"Direct test connect: {e}")

                if not dev:
                    try:
                        dev = await Discover.discover_single(ip, credentials=creds, timeout=3)
                        if dev:
                            await dev.update()
                    except Exception as e:
                        logger.debug(f"Discover test connect: {e}")

                if dev:
                    self._device = dev
                    self._connected = True
                    callback(True, f"Connected to {dev.alias or 'Smart Device'} ({dev.model})")
                else:
                    callback(False, f"Device at {ip} could not be reached.")

            except Exception as ex:
                callback(False, f"Connection error: {ex}")

        asyncio.run_coroutine_threadsafe(_test(), self._loop)

    def is_connected(self) -> bool:
        return self._connected
