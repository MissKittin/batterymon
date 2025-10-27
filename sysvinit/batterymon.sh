#!/bin/sh
### BEGIN INIT INFO
# Provides:          batterymon
# Required-Start:    bluetooth
# Required-Stop:
# Default-Start:     2 3 4 5
# Default-Stop:
# Short-Description: batterymon
### END INIT INFO

# Options
BATTERYMON="$(readlink -f "${0}")"; BATTERYMON="${BATTERYMON%/*}/.."
PIDFILE='/var/run/batterymon.pid'
DAEMON='/usr/bin/env'
DAEMON_OPTS='PYTHONPYCACHEPREFIX=/tmp/.batterymon-pyc '"${BATTERYMON}"'/batterymon.py'
USER='batterymon'
GROUP='batterymon'

PATH=/sbin:/bin:/usr/sbin:/usr/bin

. /lib/lsb/init-functions

case "$1" in
	'start')
		log_daemon_msg 'Starting batterymon' 'batterymon'

		if [ ! -e '/tmp/.batterymon-pyc' ]; then
			mkdir '/tmp/.batterymon-pyc'
			chown "${USER}:${GROUP}" '/tmp/.batterymon-pyc'
			chown 700 '/tmp/.batterymon-pyc'
		fi

		start-stop-daemon --start --quiet --background --chuid $USER:$GROUP --make-pidfile --pidfile $PIDFILE --exec $DAEMON -- $DAEMON_OPTS && log_end_msg 0 || log_end_msg 1
	;;
	'stop')
		log_daemon_msg 'Stopping batterymon' 'batterymon'
		if [ -e $PIDFILE ]; then
			daemon_pid=$(cat ${PIDFILE})
			start-stop-daemon --stop --quiet --pidfile $PIDFILE && rm $PIDFILE && \
			log_end_msg $?
		else
			log_end_msg 1
		fi
	;;
	'status')
		status_of_proc -p $PIDFILE $DAEMON "batterymon" && exit 0 || exit $?
	;;
	*)
		echo 'batterymon.sh start|stop|status'
		exit 1
	;;
esac

exit 0
