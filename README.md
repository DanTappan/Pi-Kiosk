# Pi-Kiosk

PI Kiosk is yet another kiosk application for the Raspberry Pi. The main features are:
- A simple installation script for installing on a Raspberry Pi
- Includes a password protected web page for controling the kiosk
- Can be configured to use either Chromium or Midori as the kiosk browser

Applications include:
- Digital Signage
- Displaying a test pattern image or GIF
- Displaying the output of [H2R Graphics](https://h2r.graphics/) as an overlay input on a BlackMagic ATEM

## Supported devices

This package works on any Raspberry Pi model. It will probably work on any similar single-board-computer running a variant of DFebian, but the installations scripts may need to be tweaked.

Lower end models, like a Pi Zero W with only 512MB of memory, will not be able to display dynamic web pages, for example a moving GIF image, but can handle static images. For a Pi Zero it is recommended to use the Legacy Bullseye image, or older, to save memory. To save additional memory, use Midori instead of Chromium. Chromium is not supported on the 32 bit Bookworm image.

It is recommended to install this on a fresh copy of the Raspberry Pi OS Lite image (32 or 64 bit, depending on the model)

## How to install
There are two ways to install
1. using ssh from another machine
2. directly on a Pi

### Installation using ssh

use git clone, or download the files as a zip file to a local directory 
Run the script install.sh and specify the name of a newly installed Raspberry Pi
```
git clone https://github.com/DanTappan/Pi-Kiosk
cd Pi-Kiosk
./install.sh --pi *KioskPi* [ --browser *browser* ]
```

This will install the package on *KioskPi*, selecting the selected browser. The *--browser* argument is optional, options are:
- *chromium* (default)
- *midori*

It is recommended to set up the Pi user account on *KioskPi* to use public key login for ssh. If the user name on *KioskPi* is different from the current user on the installation machine, use *.ssh/config* to select a user name, or specify as *user*@*KioskPi*

Toward the end, the script will prompt for a password to protect the kiosk control web page. When running over ssh, it will echo the password. Deal with it.

### Installation directly on a Pi

```
git clone https://github.com/DanTappan/Pi-Kiosk
cd Pi-Kiosk
./install.sh [ --browser *browser* ]
```

Again, the script will prompt for a password for the kiosk control web page.

### Post installation

With either installation method:
- Use *raspi-config* to configure the Kiosk Pi to automatically log in on the console
- Reboot the Kiosk Pi to start the kiosk

## Usage

Once the installation is complete it will have created:
- a subdirectory, *kiosk*, of the home directory of the pi user, containing the necessary files
- an openbox configuration that will autostart the kiosk when the Pi reboots

The default webpage to display is a placeholder. To configure the kiosk, connect to the kiosk Pi using a web browser. This will display the following webpage

![Screenshot of the Pi Kiosk control webpage](https://dantappan.net/wp-content/uploads/2024/12/KioskPage.png)


- The **Password** field is required on all commands, enter the password which was set during the install
- To select a new URL to display, enter it into the **Kiosk URL** field and hit the **[Set URL]** button
- The program also supports an optional dropdown menu to select pre-configured URLs. See the instructions in [index.html](https://github.com/DanTappan/Pi-Kiosk/blob/main/index.html) for how to modify or remove the dropdown menu
- The **[Restart Kiosk Browser]** button will reload the currently selected URL
- The **[Reboot Kiosk]** button will reboot the kiosk
- The **[Shutdown Kiosk]** button will shut down the kiosk



