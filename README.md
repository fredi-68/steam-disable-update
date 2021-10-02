# Steam Disable Updates

This script tricks the steam client into thinking an app is up to date, even if an old version is installed.
This allows one to launch the app without having to start steam in offline mode. It further allows one to
fully disable automatic updates (for the current patch).

## Installation

Clone or download the repo, then run

`pip install -U -r requirements.txt`

to install required packages. If you'd rather use a venv you probably already know what you are doing anyways.

## Usage

To block an update for a game of app, run the following command:

`python main.py <appid>`

where `appid` is the ID of the game or app you are trying to modify. You can look this up in the manifest file
or a website such as steamdb.

## Security Considerations

The script will ask for your username and password, as well as potential 2FA or email codes for verification
purposes during execution. This is required as depot manifests can only be accessed if you own a license for
the software. This script only downloads the depot manifest listings to obtain the newest manifest GID and 
nothing else. Your credentials are NOT stored (unfortunately, which means that you have to reauthenticate
every time. TODO: Fix this).

## Platform Compatibility

Currently this only works on Windows as it uses the registry to find the installation path of the game (and
thus the local manifest file). Linux support is planned.