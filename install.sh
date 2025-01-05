#! /usr/bin/env bash
#
# Install the kiosk software
# this can run either directly on a pi, and install locally, or
# on a unix (linux/MacOS/cygwin) machine and install to a remote pi
# if installing remotely, the pi must be running openssh or something
# else which supports sftp
#
progname=$0
BROWSER="chromium"

function usage() {
    echo "Before running this script, configure a Raspberry Pi"
    echo "with a fresh 'lite' (no desktop) installation"
    echo
    echo "For a Pi Zero it is recommended to use the legacy Bullsye 32bit."
    echo
    echo "Usage: '$progname --pi <pi> [--browser <browser>]'"
    echo "<browser> can be either 'chromium' (default) or 'midori'"
    echo "If no <pi> is specified, it is a assumed to be running directly"
    echo "on the kiosk machine"
    echo 
    exit 0
}    

function confirm() {
    while /bin/true; do
	echo -n $1 " Confirm (y/n): "
	read response
	case $response in
	    "y" | "Y" | "yes")
		return
		;;
	    "n" | "N" | "no")
		exit 1
		;;
	esac
    done
}

# Copy a file either to the local or remote machine
#
function cp_kiosk() {
    F=$1
    PI=$2

    if [ "$PI" = "" ]; then
	cp $F ~/kiosk
	chmod +x ~/kiosk/$F
    else
	scp $F $PI:kiosk/$F
	ssh $PI "chmod +x kiosk/$F"
    fi
}

# exec a command either locally or on the remote system
#
function exec_kiosk() {
    CMD=$1
    PI=$2
    if [ "$PI" = "" ] ; then
	(cd ~/kiosk; $CMD )
    else
	ssh $PI "cd kiosk; $CMD "
    fi
}

while [ "$1" != "" ]; do
    case $1 in
	--pi)
	    shift
	    PI=$1
	    ;;
	--browser)
	    shift
	    BROWSER=$1
	    ;;
	*)
	    usage
	    ;;
    esac
    shift
done

if [ "$PI" = "" ]; then
    echo 
    echo '*****'
    confirm "Installing on local machine."

    rm -rf ~/kiosk
    mkdir ~/kiosk

else
    ssh $PI "rm -rf kiosk; mkdir kiosk"
fi

for x in kiosk-setup *.py do_reboot index.html kiosk_browser; do
    cp_kiosk "$x" "$PI"
done

exec_kiosk "./kiosk-setup $BROWSER" $PI


