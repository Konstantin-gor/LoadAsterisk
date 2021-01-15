# -*- coding: utf-8 -*-
####### Routing Logic ########

import sys

sys.path.append('/etc/kamailio/python/')
sys.path.append('/usr/local/voip/etc/')
import KSR
import re
import requests
import redis

ROUTES = {
    'event_routes': ['ksr_event_dispatcher'],
    'ksr_branch_manage': ['ksr_branch_manage'],
    'ksr_failure_manage': ['ksr_failure_manage'],
    'ksr_route_async_processing': ['ksr_route_async_REGISTER', 'ksr_route_async_INVITE', 'ksr_route_async_auth'],
    'ksr_route_natdetect': ['ksr_route_natdetect'],
    'ksr_route_natmanage': ['ksr_route_natmanage'],
    'ksr_route_relay': ['ksr_route_relay'],
    'ksr_route_reqinit': ['ksr_route_reqinit'],
    'ksr_route_special': ['ksr_special_routing'],
    'ksr_route_withindlg': ['ksr_route_withindlg'],
    'ksr_x_route_location': ['ksr_x_route_location'],
    'request_route': ['ksr_request_route'],
    'KAMAILIO_DEFINE_HOST': ['DSIDS', 'FLAGS', 'GLOBALS'],
}

# global function to instantiate a kamailio class object
# -- executed when kamailio app_python module is initialized
def mod_init():
    KSR.info("===== from Python mod init\n")
    return kamailio()

# -- {start defining kamailio class}
class kamailio():
    def __init__(self):
        KSR.info('===== kamailio.__init__\n')
        # Re-import modules on reload
        for filename in ROUTES: # app_python3
            if filename in sys.modules:# app_python3
                KSR.info("Reload route:" + filename)# app_python3
                del sys.modules[filename] # app_python3
                exec("import " + filename) # app_python3

    # executed when kamailio child processes are initialized
    def child_init(self, rank):
        KSR.info('===== kamailio.child_init({})\n'.format(rank))
        return 0

    # SIP response handling
    # -- equivalent of reply_route{}
    def ksr_reply_route(self, msg):
        if KSR.is_method_in("IBR"):
            # (I)NVITE, (B)YE, (R)EGITER
            KSR.xlog.xinfo("Get reply $rs:$rr")
            self.append_uuid(KSR.pv.getw("$ci"))
        scode = KSR.pv.getw("$rs")
        if 100 <= scode or scode <= 299:
            self.ksr_route_natmanage()
        return 1
    
    def ksr_onsend_route(self, msg):
        return 1

    def is_ip_internal(self, host):
        #KSR.xlog.xinfo("Identify RFC1918 for host " + host)
        if KSR.ipops.is_pure_ip(host) > 0:
            if KSR.ipops.is_ip_rfc1918(host) > 0:
                return True
        else:
            KSR.ipops.dns_query(host, "resolved_ip")
            ip = KSR.pv.get("$dns(resolved_ip=>addr)")
            if ip:
                KSR.xlog.xnotice("{} resolved to:{}".format(host, ip))
                if KSR.ipops.is_ip_rfc1918(ip) > 0:
                    KSR.xlog.xnotice("RFC1918")
                    return True
            else:
                KSR.xlog.xerr("Can't resolve host. Return true for case when call can be established")
                return True
        return False

    def notify_asterisk(self, call_id, uuid_hdr, contact, server):
        try:
            # Добавляем в очередь на обработку
            r = redis.StrictRedis(host=server, port=6379, db=3, decode_responses=True)
            r.hmset(contact, { "target":call_id, "status":"registered", "type":"aor" , "uuid": uuid_hdr , "src":"app"})
            r.expire(contact, 60)
            KSR.xlog.xnotice("Generated 'aor' task with target {} for subscriber:{} on asterisk:{}".format(call_id, KSR.pv.getw("$fu"), server))
        except Exception as e_msg:
            KSR.xlog.xerr("Cant notify_asterisk:" + str(e_msg))

    def store_uuid(self, callid, uuid):
        try:
            r = redis.StrictRedis(host='127.0.0.1', port=6379, db=4, decode_responses=True)
            # Сохраняем на 5 минут call-id
            r.setex(callid, 300, uuid)
        except Exception as e_msg:
            KSR.xlog.xerr("Cant store UUID in redis:" + str(e_msg))

    def append_uuid(self, callid):
        if KSR.hdr.is_present("UUID") < 0:
            try:
                r = redis.StrictRedis(host='127.0.0.1', port=6379, db=4, decode_responses=True)
                KSR.xlog.xinfo("Appending uuid {}".format(r.get(callid)))
                KSR.hdr.append("UUID: {}\r\n".format(r.get(callid)))
            except Exception as e_msg:
                KSR.xlog.xerr("Cant get UUID from redis:" + str(e_msg))

    def manage_call_status(self, from_user, action='put'):
        from_user = from_user.lower()
        try:
            r = redis.StrictRedis(host='127.0.0.1', port=6379, db=1, decode_responses=True)
            if action == 'put':
                r.setex("call::{}".format(from_user), 600, 1)
            else:
                r.delete("call::{}".format(from_user))
        except Exception as e_msg:
            KSR.xlog.xerr("Cant get UUID from redis:" + str(e_msg))

    def check_registration_uri(self):
        uri = KSR.pv.getw("$fu")
        if len(uri.split(":")) == 2:
            uri += ":{}".format(KSR.pv.getw("$Rp"))
        try:
            # Добавляем в очередь на обработку
            r = redis.StrictRedis(host='127.0.0.1', port=6379, db=1, decode_responses=True)
            r0 = redis.StrictRedis(host='127.0.0.1', port=6379, db=0, decode_responses=True)
            Uri = KSR.pv.getw("$fU")
            call_id, uuid_hdr = r.hmget(uri, "target", "uuid")
            if r0.sismember("REGLISTEN",Uri) and KSR.pv.getw("$hdr(Expires)") != '0':
                ct = self.make_ct()
                r0.publish(Uri,ct)
            ### old logic
            if call_id :
                if 'ct' not in locals() :
                    ct = self.make_ct()
                self.notify_asterisk(call_id, uuid_hdr, ct, r.hget(uri, "server"))
        except Exception as e_msg:
            KSR.xlog.xerr("Cant check_registration_uri:" + str(e_msg))

    def send_registration_info_to_redis(self,registred,time):
        if KSR.pv.getw("$hdr(Expires)") == '0':
            return
        ua=KSR.pv.gete("$hdr(User-Agent)")
        if KSR.hdr.is_present("X-Call-Uuid") < 0 and not ('baresip' in ua or 'Beward' in ua):
            return
        try:
            key = "{}:{}".format(KSR.pv.getw("$ci"), time)
            value = { 
                "time":time,
                "account":KSR.pv.getw("$fu"),
                "uuid":KSR.pv.gete("$hdr(X-Call-Uuid)"),
                "device_id":KSR.pv.gete("$hdr(X-Device-Id)"),
                "register_success":registred,
            }
            r = redis.StrictRedis(host='127.0.0.1', port=6379, db=13, decode_responses=True)
            r.hmset(key, value)
            r.expire(key, 43200)
        except Exception as e:
            KSR.xlog.xerr("Cant send SIP_REGISTER " + str(e))

    def make_ct(self):
        m = re.search('^<([^>]+)(.*)', KSR.pv.get("$ct"))
        if m:
            ct = m.group(1)
        else:
            ct = KSR.pv.getw("$ct")
        if not KSR.pv.is_null("$avp(received)"):
            _, received_host, received_port = KSR.pv.getw("$avp(received)").split(":")
            if not "{}:{}".format(received_host, received_port) in ct:
                ct = "{};alias={}~{}~1".format(ct, received_host, received_port)
                KSR.xlog.xnotice("Generated URI with alias '{}'".format(ct))
        return ct

    # Import section
    for filename in ROUTES:
        for route in ROUTES[filename]:
            exec("from {} import {}".format(filename, route))

