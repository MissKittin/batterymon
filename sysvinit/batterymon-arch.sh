#!/bin/sh
### BEGIN INIT INFO
# Provides:          batterymon-arch
# Required-Start:    batterymon
# Required-Stop:     batterymon
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: batterymon-arch
### END INIT INFO

if [ ! "${1}" = 'daemon' ]; then
	ENABLE_WATCHDOG='false'
	LOG='/var/run/.batterymon-restart.log'
	USER='batterymon'
	GROUP='batterymon'
	CUSTOM_PYTHON_PATH=''
	CUSTOM_PYTHON_CACHE_PATH='/tmp/.batterymon-pyc'
	BATTERYMON="$(readlink -f "${0}")"; BATTERYMON="${BATTERYMON%/*}/.."

	[ -f "${BATTERYMON}/sysvinit/batterymon.rc" ] && . "${BATTERYMON}/sysvinit/batterymon.rc"

	PIDFILE='/var/run/batterymon-arch.pid'
	DAEMON='/usr/bin/env'
	DAEMON_OPTS='PYTHONPYCACHEPREFIX='"${CUSTOM_PYTHON_CACHE_PATH}"' '"${BATTERYMON}"'/batterymon-arch.py'
	[ ! "${CUSTOM_PYTHON_PATH}" = '' ] && DAEMON_OPTS="PATH=${CUSTOM_PYTHON_PATH} ${DAEMON_OPTS}"
	PATH='/sbin:/bin:/usr/sbin:/usr/bin'

	. '/lib/lsb/init-functions'
fi

case "${1}" in
	'start')
		log_daemon_msg 'Starting batterymon-arch' 'batterymon-arch'

		if [ ! -e '/tmp/.batterymon-pyc' ]; then
			mkdir '/tmp/.batterymon-pyc'
			chown "${USER}:${GROUP}" '/tmp/.batterymon-pyc'
			chmod 700 '/tmp/.batterymon-pyc'
		fi

		if "${ENABLE_WATCHDOG}"; then
			if [ ! -e "${PIDFILE}.child" ]; then
				echo -n '' > "${PIDFILE}.child"
				chgrp "${GROUP}" "${PIDFILE}.child"
				chmod 664 "${PIDFILE}.child"
			fi

			if [ ! -e "${LOG}" ]; then
				echo -n '' > "${LOG}"
				chown "${USER}" "${LOG}"
				chmod 640 "${LOG}"
			fi

			start-stop-daemon --start --quiet --background --chuid "${USER}:${GROUP}" --make-pidfile --pidfile "${PIDFILE}" --exec "$(readlink -f ${0})" -- 'daemon' "${PIDFILE}.child" "${LOG}" "${DAEMON}" ${DAEMON_OPTS} && log_end_msg 0 || log_end_msg 1
		else
			start-stop-daemon --start --quiet --background --chuid "${USER}:${GROUP}" --make-pidfile --pidfile "${PIDFILE}" --exec "${DAEMON}" -- ${DAEMON_OPTS} && log_end_msg 0 || log_end_msg 1
		fi
	;;
	'stop')
		log_daemon_msg 'Stopping batterymon-arch' 'batterymon-arch'

		if [ -e "${PIDFILE}" ]; then
			start-stop-daemon --stop --quiet --pidfile "${PIDFILE}" && rm "${PIDFILE}"

			if "${ENABLE_WATCHDOG}"; then
				[ -f "${PIDFILE}.child" ] && kill -15 "$(cat "${PIDFILE}.child")" && rm "${PIDFILE}.child"
			fi

			log_end_msg $?
		else
			log_end_msg 1
		fi
	;;
	'status')
		if "${ENABLE_WATCHDOG}"; then
			status_of_proc -p "${PIDFILE}" "$(readlink -f ${0})" 'batterymon-arch' && exit 0 || exit $?
		else
			status_of_proc -p "${PIDFILE}" "${DAEMON}" 'batterymon-arch' && exit 0 || exit $?
		fi
	;;
	'restart')
		"${0}" stop
		"${0}" start

		exit $?
	;;
	'daemon')
		export PYTHONUNBUFFERED=1
		DAEMON_PIDFILE="${2}"
		LOG="${3}"
		DAEMON="${4}"

		shift 4

		"${DAEMON}" ${@} >> "${LOG}" &
		DAEMON_PID=$!
		echo "${DAEMON_PID}" > "${DAEMON_PIDFILE}"

		sleep 2

		if ! kill -0 "${DAEMON_PID}" > '/dev/null' 2>&1; then
			echo "$(date '+%Y-%m-%d %H:%M:%S') Daemon failed immediately, stopping batterymon-arch watchdog" >> "${LOG}"
			exit 1
		fi

		wait "${DAEMON_PID}"

		while :; do
			echo "$(date '+%Y-%m-%d %H:%M:%S') Restarting batterymon-arch" >> "${LOG}"
			sleep 1

			"${DAEMON}" ${@} >> "${LOG}" &

			DAEMON_PID=$!
			echo "${DAEMON_PID}" > "${DAEMON_PIDFILE}"
			wait "${DAEMON_PID}"
		done
	;;
	*)
		echo "${0##*/} start|stop|restart|status"
		exit 1
	;;
esac
