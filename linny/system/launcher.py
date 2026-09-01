"""
Smart Application and Website Launcher.
Supports web URLs, protocol handlers, standard executables, and multi-argument launch commands.
"""

from __future__ import annotations

import os
import subprocess
import webbrowser
from typing import Dict, Tuple

from ..core.logger import get_logger

logger = get_logger("launcher")


class AppLauncher:
    """Intelligent multi-mode process and URL launcher with alias resolution."""

    def __init__(self, aliases: Dict[str, str]) -> None:
        self.aliases = {k.lower().strip(): v for k, v in aliases.items()}

    def update_aliases(self, aliases: Dict[str, str]) -> None:
        self.aliases = {k.lower().strip(): v for k, v in aliases.items()}

    def resolve_target(self, app_name: str) -> str:
        """Resolve friendly name or alias to actionable target."""
        clean_name = app_name.lower().strip()
        return self.aliases.get(clean_name, clean_name)

    def launch(self, app_name: str) -> Tuple[bool, str]:
        """
        Execute target with smart 3-case strategy:
        Case 1: Web URL (http/https/www) -> Default browser
        Case 2: Simple binary / protocol (no flags) -> os.startfile
        Case 3: Complex command line with flags -> subprocess.Popen
        """
        clean_name = app_name.strip()
        if not clean_name:
            return False, "No application specified."

        target = self.resolve_target(clean_name)
        logger.info(f"Launching request: '{app_name}' -> Target: '{target}'")

        try:
            # Case 1: Web URL
            if target.startswith(("http://", "https://", "www.")):
                url = target if not target.startswith("www.") else f"https://{target}"
                webbrowser.open(url)
                logger.info(f"Opened URL: {url}")
                return True, f"Opening {clean_name} in your browser."

            # Case 2: Protocol handler or standard executable without args
            has_arguments = any(flag in target for flag in ["--", " /", " -"])
            if not has_arguments and (os.path.exists(target) or ":" in target or target.isalnum()):
                try:
                    os.startfile(target)
                    logger.info(f"Started file/protocol: {target}")
                    return True, f"Opening {clean_name}."
                except Exception as e:
                    logger.debug(f"os.startfile failed for '{target}': {e}, falling back to subprocess")

            # Case 3: Complex command with flags (e.g. Riot Client, VS Code args)
            # Use subprocess with proper detached process creation
            creation_flags = 0
            if os.name == "nt":
                creation_flags = subprocess.CREATE_NO_WINDOW if "riotclient" not in target.lower() else 0

            subprocess.Popen(
                target,
                shell=True,
                creationflags=creation_flags,
                stdout=subprocess.DEVNULL if "riotclient" not in target.lower() else None,
                stderr=subprocess.DEVNULL if "riotclient" not in target.lower() else None,
            )
            logger.info(f"Spawned process: {target}")
            return True, f"Launching {clean_name}."

        except Exception as e:
            logger.error(f"Failed to launch '{app_name}' ({target}): {e}", exc_info=True)
            return False, f"Could not find or open {clean_name}."
