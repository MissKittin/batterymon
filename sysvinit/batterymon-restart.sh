#!/bin/sh
### BEGIN INIT INFO
# Provides:          batterymon-restart
# Required-Start:
# Required-Stop:
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: batterymon-restart
### END INIT INFO

# Options
BATTERYMON_SCR="$(readlink -f "${0}")"
BATTERYMON="${BATTERYMON_SCR%/*}"
PIDFILE='/var/run/batterymon-restart.pid'
DAEMONS="${BATTERYMON}/batterymon.sh ${BATTERYMON}/batterymon-arch.sh"
LOG='/var/run/.batterymon-restart.log'

PATH=/sbin:/bin:/usr/sbin:/usr/bin

. /lib/lsb/init-functions

case "$1" in
	'daemon')
		while true; do
			for daemon in ${DAEMONS}; do
				"${daemon}" status && continue

				echo "$(date '+%Y-%m-%d %H:%M:%S') Restarting ${daemon}" >> "${LOG}"
				"${daemon}" start >> "${LOG}" 2>&1
			done

			sleep 60
		done
	;;
	'start')
		for daemon in ${DAEMONS}; do
			"${daemon}" start
		done

		log_daemon_msg 'Starting batterymon-restart' 'batterymon-restart'
		start-stop-daemon --start --quiet --background --make-pidfile --pidfile $PIDFILE --exec $BATTERYMON_SCR -- daemon && log_end_msg 0 || log_end_msg 1
	;;
	'stop')
		log_daemon_msg 'Stopping batterymon-restart' 'batterymon-restart'
		if [ -e $PIDFILE ]; then
			daemon_pid=$(cat ${PIDFILE})
			if start-stop-daemon --stop --quiet --pidfile $PIDFILE && rm $PIDFILE; then
				log_end_msg $?

				for daemon in ${DAEMONS}; do
					"${daemon}" stop
				done
			fi
		else
			log_end_msg 1
		fi
	;;
	'status')
		status_of_proc -p $PIDFILE $BATTERYMON_SCR "batterymon-restart" && exit 0 || exit $?
	;;
	*)
		echo 'batterymon-restart.sh start|stop|status'
		exit 1
	;;
esac

exit 0
