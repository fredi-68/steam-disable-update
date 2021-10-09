import argparse
import os
import sys
import subprocess
import logging
from pathlib import Path
from collections import OrderedDict
import time
from typing import Dict, List
import json
import psutil
if sys.platform.startswith("win32"):
    import winreg

from steam.client import SteamClient
from steam.client.cdn import CDNClient, CDNDepotManifest
import steamfiles.acf

def get_game_location(appid: int) -> Path:

    #Thank you kinsi55 for this trick
    #https://github.com/kinsi55/BeatSaber_UpdateSkipper/blob/master/Form1.cs
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Steam App %i" % appid)
    path = winreg.QueryValueEx(key, "InstallLocation")[0]
    winreg.CloseKey(key)
    return Path(path)

def get_steam_location():

    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Valve\\Steam")
    except OSError as e:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\WOW6432Node\\Valve\\Steam")
    path = winreg.QueryValueEx(key, "InstallPath")[0]
    winreg.CloseKey(key)
    return Path(path)

def get_manifest_location(appid: int) -> Path:

    return get_game_location(appid).parent.parent / ("appmanifest_%i.acf" % appid)

def load_credentials():

    with open("./.auth", "r") as f:
        data = json.load(f)
    return (data["user"], data["key"])

def save_credentials(user: str, key: str):

    with open("./.auth", "w") as f:
        json.dump({"user": user, "key": key}, f)

def kill_steam():
    """Closes steam

    Raises:
        RuntimeError: if steam is running, but not closed

    Returns:
        False: if steam is not running
        True: if steam is killed
    """
    logger = logging.getLogger("process_management")
    
    # startsWith because windows has .exe
    steam_processes = [p for p in psutil.process_iter() if p.name().startswith('steam')]

    if not steam_processes:
        logger.debug("Steam is not running")
        return False
    
    # Killing the main steam process should
    # automatically kill all children
    steam_process = steam_processes[0]
    try:
        steam_process.terminate()
    except psutil.NoSuchProcess:
        logger.error("Steam was running, but dissapeared before being terminated.")
    except psutil.AccessDenied as e:
        raise RuntimeError("Unable to automatically close steam: %s. Please ensure steam is closed before attempting to run this script." % str(e))

    try:
        steam_process.wait(10)
    except psutil.TimeoutExpired:
        logger.debug("Steam did not terminate in 10 seconds, killing")
        steam_process.kill()

    logger.debug("Success!")
    return True

def disable_updates(appid: int, launch_game=False, disable_auto_update=False, persist_auth=False):

    logger = logging.getLogger("patcher")

    logger.debug("Preparing...")
    manifest_path = get_manifest_location(appid)
    logger.debug("Manifest location is %s" % manifest_path)

    #Shutdown steam if it is running
    steam_need_restart = kill_steam()

    logger.info("Downloading latest patch data...")
    logger.debug("Signing into steam...")
    client = SteamClient()
    client.set_credential_location(".")
    user = ""
    if persist_auth:
        try:
            user, key = load_credentials()
        except OSError:
            pass
    if not client.relogin_available:
        if user:
            try:
                logging.debug("Trying to log in with persistent key...")
                client.login(user, login_key=key)
            except:
                logger.warning("Not possible to relogin, user needs to provide credentials.")
        if not client.logged_on:
            client.cli_login() #TODO: Replace with better login handler
            if user:
                key = ""

    if persist_auth and not key:
        client.wait_event("new_login_key", timeout=5)
        save_credentials(client.username, client.login_key)
    cdn = CDNClient(client)
    logger.debug("Fetching manifest listings for app %i from depot..." % appid)
    patches: List[CDNDepotManifest] = cdn.get_manifests(appid)
    logger.debug("Got %i manifest entries: %s" % (len(patches), patches))

    logger.info("Loading manifest...")
    with open(manifest_path, "r") as f:
        manifest = steamfiles.acf.load(f, wrapper=OrderedDict)
    app_state = manifest["AppState"]
    logger.debug("Detected game: '%s'" % app_state["name"])
    installed_depots = app_state.get("InstalledDepots", {})
    mounted_depots = app_state.get("MountedDepots", {})

    logger.info("Patching game manifest...")
    for patch in patches:
        if patch.depot_id in installed_depots or mounted_depots:
            logger.debug("Rewriting depot %i..." % patch.depot_id)
        else:
            logger.debug("Adding new depot %i..." % patch.depot_id)
        installed_depots[str(patch.depot_id)] = {"manifest": str(patch.gid), "size": "0"}
        mounted_depots[str(patch.depot_id)] = str(patch.gid)
    logger.debug("Rewriting manifest update state...")
    app_state["ScheduledAutoUpdate"] = "0"
    app_state["LastUpdated"] = str(int(time.time()))
    app_state["StateFlags"] = "4"
    app_state["UpdateResult"] = "0"
    if disable_auto_update:
        app_state["AutoUpdateBehavior"] = "1"
    
    logger.info("Writing manifest...")
    logger.debug("Creating backup...")
    with open(manifest_path, "rb") as f:
        with open(manifest_path.with_suffix(".acf.bak"), "wb") as g:
            g.write(f.read())
    logger.debug("Writing...")
    with open(manifest_path, "w") as f:
        steamfiles.acf.dump(manifest, f)

    logger.info("Done!")

    #Relaunch steam
    if steam_need_restart:
        p = get_steam_location() / "steam.exe"
        try:
            os.spawnl(os.P_NOWAIT, p, p)
        except OSError as e:
            logger.warning("Failed to restart steam: %s" % str(e))
    #TODO: If requested, launch game

parser = argparse.ArgumentParser()

parser.add_argument("appid", type=int)
parser.add_argument("-l", "--launch", action="store_true")
parser.add_argument("--disable-auto-update", action="store_true")
parser.add_argument("-v", "--verbose", action="store_true")
parser.add_argument("-s", "--persist-auth", action="store_true")

args = parser.parse_args()

logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

disable_updates(args.appid, args.launch, args.disable_auto_update, args.persist_auth)