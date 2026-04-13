#!/bin/sh

DAEMON="/usr/local/opnsense/scripts/OPNsense/NCLink/nclink_daemon.py"
PIDFILE="/var/run/nclink.pid"
LOGFILE="/var/log/nclink.log"
MODEL_FILE="/usr/local/etc/nclink/model.json"

case "$1" in
    start)
        echo "Starting NC-Link daemon..."
        mkdir -p /usr/local/etc/nclink
        /usr/local/bin/python3.11 ${DAEMON} >> ${LOGFILE} 2>&1 &
        echo $! > ${PIDFILE}
        ;;
    stop)
        echo "Stopping NC-Link daemon..."
        if [ -f ${PIDFILE} ]; then
            kill $(cat ${PIDFILE}) 2>/dev/null
            rm -f ${PIDFILE}
        fi
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        if [ -f ${PIDFILE} ] && kill -0 $(cat ${PIDFILE}) 2>/dev/null; then
            echo "NC-Link is running"
        else
            echo "NC-Link is stopped"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
