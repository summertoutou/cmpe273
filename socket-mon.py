import psutil
from itertools import groupby

p=psutil.net_connections(kind='inet')
list = []
for conn in p:
    if conn.raddr:
        dict = {}

        dict['pid'] = conn.pid
        #print "laddr is "+conn.laddr
        dict['lad'] = conn.laddr[0]+"@"+str(conn.laddr[1])
        #print "raddr is " + conn.raddr
        dict['rad'] = conn.raddr[0]+"@"+str(conn.laddr[1])
        dict['status'] = conn.status
        list.append(dict)
newlist = sorted(list, key=lambda k: k['pid'])
print '"pid","laddr","raddr","status"'
for line in newlist:
    print '"'+str(line['pid'])+'","'+line['lad']+'","'+line['rad']+'","'+line['status']+'"'


