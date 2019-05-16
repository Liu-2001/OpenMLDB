#! /bin/sh
#
# start.sh
CURDIR=`pwd`
cd "$(dirname "$0")"/../
RTIDBPIDFILE="./bin/tablet.pid"
mkdir -p "$(dirname "$RTIDBPIDFILE")"
LOGDIR=`grep log_dir ./conf/tablet.flags | awk -F '=' '{print $2}'`
mkdir -p $LOGDIR
case $1 in
    start)
        echo -n "Starting tablet ... "
        if [ -f "$RTIDBPIDFILE" ]; then
            if kill -0 `cat "$RTIDBPIDFILE"` > /dev/null 2>&1; then
                echo tablet already running as process `cat "$RTIDBPIDFILE"`.
                exit 0
            fi
        fi
        ./bin/mon ./bin/boot.sh -d -s 10 -l $LOGDIR/rtidb_mon.log -m $RTIDBPIDFILE
        if [ $? -eq 0 ]
        then
            sleep 1
            echo STARTED
        else
            echo SERVER DID NOT START
            exit 1
        fi
        ;;
    stop)
        echo -n "Stopping tablet ... "
        if [ ! -f "$RTIDBPIDFILE" ]
        then
             echo "no tablet to stop (could not find file $RTIDBPIDFILE)"
        else
            kill $(cat "$RTIDBPIDFILE")
            rm "$RTIDBPIDFILE"
            echo STOPPED
        fi    
        ;;
    restart)
        shift
        cd $CURDIR
        sh "$0" stop ${@}
        sleep 5
        sh "$0" start ${@}
        ;;
    *)
        echo "Usage: $0 {start|stop|restart}" >&2
esac    
