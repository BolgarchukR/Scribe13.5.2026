# scribe/app_launcher.py
import logging
import subprocess
import platform
import shlex
import json
import os
import sys

logger = logging.getLogger(__name__)

class CrossPlatformAppLauncher:
    """
    Handles launching applications in a cross-platform manner.
    """

    def launch(self, app_info_str: str):
        """
        Launches an application based on its info dictionary serialized as a JSON string.
        :param app_info_str: A JSON string containing application details.
        """
        system = platform.system()
        
        try:
            app_info = json.loads(app_info_str)
        except json.JSONDecodeError:
            logger.warning(f"Could not decode app info string, treating as plain path: {app_info_str}")
            self._launch_path(app_info_str)
            return

        app_name = app_info.get('name', 'Unknown App')
        path = app_info.get('path')
        args = app_info.get('args', '')

        try:
            if system == "Windows":
                appid = app_info.get("appid")

                if appid:
                    # UWP/Store app. Arguments are not applicable.
                    if args:
                        logger.warning(f"Arguments are not supported for modern app launches. Ignoring '{args}'.")

                    command = rf"shell:Appsfolder\{appid}"
                    logger.info(f"Launching modern Windows app with command: {command}")
                    
                    win_ver = sys.getwindowsversion()

                    # For Win 10/11, explorer.exe is reliable.
                    if win_ver.major >= 10:
                        logger.debug("Using 'explorer.exe' method for Windows 10/11.")
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        startupinfo.wShowWindow = subprocess.SW_HIDE
                        subprocess.Popen(['explorer.exe', command], startupinfo=startupinfo, creationflags=subprocess.CREATE_NO_WINDOW)
                    # For Win 8.0/8.1, os.startfile is the correct method.
                    elif win_ver.major == 6 and win_ver.minor >= 2:
                        logger.debug("Using 'os.startfile' method for Windows 8/8.1.")
                        os.startfile(command)
                    else:
                        logger.error(f"Unsupported Windows version ({win_ver.major}.{win_ver.minor}) for appid launch.")
                        raise OSError("Cannot launch modern apps on this version of Windows.")

                elif path:
                    # Standard executable.
                    self._launch_path(path, args)
                else:
                    raise ValueError(f"Missing 'appid' or 'path' for launching '{app_name}' on Windows.")

            elif system == "Darwin": # macOS
                if not path:
                    raise ValueError(f"Missing 'path' for launching '{app_name}' on macOS.")
                self._launch_path_darwin(path, args)

            elif system == "Linux":
                desktop_id = app_info.get("desktop_id")
                wm_class = app_info.get("wm_class")

                # Try to launch with gtk-launch first
                launched_with_id = False
                ids_to_try = []
                if desktop_id:
                    ids_to_try.append(desktop_id)
                if wm_class and wm_class not in ids_to_try:
                    ids_to_try.append(wm_class)
                
                if ids_to_try:
                    for app_id in ids_to_try:
                        try:
                            command = ['gtk-launch', app_id]
                            logger.info(f"Attempting to launch on Linux via gtk-launch with ID: '{app_id}'")
                            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                            logger.info(f"Successfully launched '{app_name}' using gtk-launch with ID '{app_id}'.")
                            launched_with_id = True
                            break 
                        except FileNotFoundError:
                            logger.warning("gtk-launch not found. Falling back to direct path.")
                            break
                        except subprocess.CalledProcessError as e:
                            error_message = e.stderr.decode().strip() if e.stderr else "(no stderr)"
                            logger.warning(f"gtk-launch failed for ID '{app_id}': {error_message}")
                        except Exception as e:
                            logger.error(f"An unexpected error occurred with gtk-launch for ID '{app_id}': {e}")
                
                if launched_with_id:
                    return

                # Fallback to direct path execution
                if not path:
                    raise ValueError(f"Missing 'path' for launching '{app_name}' on Linux after all other methods failed.")

                self._launch_path(path, args)

            else:
                logger.warning(f"Unsupported operating system: {system}")

        except Exception as e:
            logger.error(f"Failed to launch application '{app_name}'. Error: {e}", exc_info=True)
            raise
    
    def _launch_path(self, path: str, args: str = ""):
        """Launches a standard executable from a path (for Windows and Linux)."""
        logger.info(f"Launching from path: '{path}' with args: '{args}'")
        try:
            if platform.system() == 'Windows':
                if not args:
                    os.startfile(path)
                else:
                    command = [path] + shlex.split(args)
                    subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW)
            else: # Linux
                command = [path]
                if args:
                    command.extend(shlex.split(args))
                subprocess.Popen(command)
        except Exception as e:
            logger.error(f"Failed to launch from path '{path}'. Error: {e}", exc_info=True)
            raise

    def _launch_path_darwin(self, path: str, args: str = ""):
        """Launches an application on macOS using the 'open' command."""
        logger.info(f"Launching on macOS: '{path}' with args: '{args}'")
        try:
            command = ['open', path]
            if args:
                command.extend(['--args'] + shlex.split(args))
            subprocess.Popen(command)
        except Exception as e:
            logger.error(f"Failed to launch '{path}' on macOS. Error: {e}", exc_info=True)
            raise