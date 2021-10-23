# Steam Disable Updates

This script tricks the steam client into thinking an app is up to date, even if an old version is installed.
This allows one to launch the app without having to start steam in offline mode. It further allows one to
fully disable automatic updates (for the current patch).

## Installation

Clone or download the repo, then run

`pip install -U -r requirements.txt`

to install required packages. If you'd rather use a venv you probably already know what you are doing anyways.

## Usage

**WARNING: ALWAYS BACKUP YOUR MANIFEST FILES AND/OR GAME FILES BEFORE USING THIS SCRIPT!!!**
The script automatically creates a backup of the manifest file in case things break but you should
NEVER rely on this. *ALWAYS MAKE YOUR OWN BACKUPS, IF SOMETHING DOES NOT WORK CORRECTLY YOU ARE ON YOUR OWN.*

The script will attempt to close steam if it is running automatically. If this for some reason does not work,
the command will abort with an error. In this case please close steam manually to proceed.
To block an update for a game or app run the following command:

`python main.py <appid>`

where `appid` is the ID of the game or app you are trying to modify, which you can find in the updates tab of your apps properties (Inside the steam library manager, rightclick the app, then click `Properties...` > `Updates`. The App ID should be at the bottom). Alternatively, you can look this up in the manifest file
or a website such as steamdb.

## Security Considerations

The script will ask for your username and password, as well as potential 2FA or email codes for verification
purposes during execution. This is required as depot manifests can only be accessed if you own a license for
the software. This script only downloads the depot manifest listings to obtain the newest manifest GID and 
nothing else. Your credentials are NOT stored by default. Should you wish to fully automate this process,
you may pass the `-s` flag when running the script. This will write your username and login key to a json file
in the current directory and use it during subsequent calls instead of having you reauthenticate. If the key
expires you will have to reauthenticate. Note that your password or 2FA secrets are NEVER stored by this script.

## Platform Compatibility

Currently this works on both Windows and Linux(tested on Arch).
