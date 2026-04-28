#!/bin/sh
### BEGIN INIT INFO
# Provides:          batterymon-restart
# Required-Start:    bluetooth
# Required-Stop:     bluetooth
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: batterymon-restart
### END INIT INFO

BATTERYMON_SCR="$(readlink -f "${0}")"
BATTERYMON="${BATTERYMON_SCR%/*}"
DAEMONS="${BATTERYMON}/batterymon.sh ${BATTERYMON}/batterymon-arch.sh"

if [ "${1}" = 'daemon' ]; then
	LOG='/var/run/.batterymon-restart.log'
else
	PIDFILE='/var/run/batterymon-restart.pid'
	PATH='/sbin:/bin:/usr/sbin:/usr/bin'

	. '/lib/lsb/init-functions'
fi

case "${1}" in
	'start')
		for daemon in ${DAEMONS}; do
			"${daemon}" start
		done

		log_daemon_msg 'Starting batterymon-restart' 'batterymon-restart'
		start-stop-daemon --start --quiet --background --make-pidfile --pidfile "${PIDFILE}" --exec "${BATTERYMON_SCR}" -- 'daemon' && log_end_msg 0 || log_end_msg 1
	;;
	'stop')
		log_daemon_msg 'Stopping batterymon-restart' 'batterymon-restart'

		if [ -e "${PIDFILE}" ]; then
			if start-stop-daemon --stop --quiet --pidfile "${PIDFILE}" && rm "${PIDFILE}"; then
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
		status_of_proc -p "${PIDFILE}" "${BATTERYMON_SCR}" 'batterymon-restart' && exit 0 || exit $?
	;;
	'restart')
		"${0}" stop
		"${0}" start

		exit $?
	;;
	'daemon')
		nb_sleep()
		{
			local i=0

			while [ "${i}" -lt "${1}" ]; do
				sleep 1
				i=$((i+1))
			done
		}

		while :; do
			for daemon in ${DAEMONS}; do
				"${daemon}" 'status' && continue

				if [ ! -e "${LOG}" ]; then
					echo -n '' > "${LOG}"
					chmod 640 "${LOG}"
				fi

				echo "$(date '+%Y-%m-%d %H:%M:%S') Restarting ${daemon}" >> "${LOG}"
				"${daemon}" 'start' >> "${LOG}" 2>&1
			done

			nb_sleep '60'
		done
	;;
	*)
		echo "${0##*/} start|stop|restart|status"
		exit 1
	;;
esac
