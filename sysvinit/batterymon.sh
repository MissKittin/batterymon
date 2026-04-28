#!/bin/sh
### BEGIN INIT INFO
# Provides:          batterymon
# Required-Start:    bluetooth
# Required-Stop:     bluetooth
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: batterymon
### END INIT INFO

USER='batterymon'
GROUP='batterymon'
CUSTOM_PYTHON_PATH=''
CUSTOM_PYTHON_CACHE_PATH='/tmp/.batterymon-pyc'
BATTERYMON="$(readlink -f "${0}")"; BATTERYMON="${BATTERYMON%/*}/.."

[ -f "${BATTERYMON}/sysvinit/batterymon.rc" ] && . "${BATTERYMON}/sysvinit/batterymon.rc"

PIDFILE='/var/run/batterymon.pid'
DAEMON='/usr/bin/env'
DAEMON_OPTS='PYTHONPYCACHEPREFIX='"${CUSTOM_PYTHON_CACHE_PATH}"' '"${BATTERYMON}"'/batterymon.py'
[ ! "${CUSTOM_PYTHON_PATH}" = '' ] && DAEMON_OPTS="PATH=${CUSTOM_PYTHON_PATH} ${DAEMON_OPTS}"
PATH='/sbin:/bin:/usr/sbin:/usr/bin'

. '/lib/lsb/init-functions'

case "${1}" in
	'start')
		log_daemon_msg 'Starting batterymon' 'batterymon'

		if [ ! -e '/tmp/.batterymon-pyc' ]; then
			mkdir '/tmp/.batterymon-pyc'
			chown "${USER}:${GROUP}" '/tmp/.batterymon-pyc'
			chmod 700 '/tmp/.batterymon-pyc'
		fi

		start-stop-daemon --start --quiet --background --chuid "${USER}:${GROUP}" --make-pidfile --pidfile "${PIDFILE}" --exec "${DAEMON}" -- ${DAEMON_OPTS} && log_end_msg 0 || log_end_msg 1
	;;
	'stop')
		log_daemon_msg 'Stopping batterymon' 'batterymon'

		if [ -e "${PIDFILE}" ]; then
			start-stop-daemon --stop --quiet --pidfile "${PIDFILE}" && rm "${PIDFILE}"
			log_end_msg $?
		else
			log_end_msg 1
		fi
	;;
	'status')
		status_of_proc -p "${PIDFILE}" "${DAEMON}" 'batterymon' && exit 0 || exit $?
	;;
	'restart')
		"${0}" stop
		"${0}" start

		exit $?
	;;
	*)
		echo "${0##*/} start|stop|restart|status"
		exit 1
	;;
esac
