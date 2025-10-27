Link batterymon.sh and batterymon-arch.sh to /etc/init.d and insserv
OR
Link batterymon-restart.sh to /etc/init.d and insserv

You can insserv batterymon-faststart.sh instead of batterymon-restart.sh
This will allow batterymon to start very early in the system boot process
Rename batterymon-faststart.sh.example to batterymon-faststart.sh, edit, link to /etc/init.d and insserv
