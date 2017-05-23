from datetime import datetime


def log(msg):
    msg = get_timestamp() + msg
    __log.write(msg)
    __log.flush()
    print(msg)


def get_timestamp():
    return '[' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '] '


__log = open('GLaDOS.log', 'w')
log('\n==========================================================\n'
    'Log Opened, {}\n'
    '=========================================================='.format(
    get_timestamp().strip('[]')
))
