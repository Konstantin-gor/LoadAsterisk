# -*- coding: utf-8 -*-
import KSR
import re
# Per SIP request initial checks
def ksr_route_reqinit(self):
    if KSR.is_INVITE():
        KSR.xlog.xinfo("REQINIT. Check request $ru from $fu:$si")

    if KSR.is_method("PUBLISH|SUBSCRIBE"):
        # Drop unsupported methods
        KSR.sl.sl_send_reply(404, "Pool is closed due to aids.")
        return -255

    if KSR.is_OPTIONS() and re.match("friendly-scanner|sipcli|VaxSIPUserAgent", KSR.pv.getw("$ua")):
        # silent drop for scanners - uncomment next line if want to reply
        # KSR.sl.sl_send_reply(200, "OK")
        KSR.sl.sl_send_reply(503, "There is no money, but you hang in there. Best wishes! Cheers!")
        return -255

    if KSR.maxfwd.process_maxfwd(10) < 0:
        KSR.sl.sl_send_reply(483, "Too Many Hops")
        return -255

    if KSR.is_OPTIONS():
        KSR.sl.sl_send_reply(200, "Keepalive")
        return -255
    
    if (int(KSR.siputils.is_request()) > 0) and (int(KSR.textops.has_body()) < 0) and (int(KSR.hdr.is_present("Content-Length")) < 0):
        KSR.xlog.xwarn("Malformed SIP message from $si:$sp - unpresent Body and no Content-Length header. User agent:$ua - Append hdr")
        KSR.hdr.append("Content-Length: 0\r\n")
        KSR.textopsx.msg_apply_changes()
        
    if "null" in KSR.pv.getw("$ct"):
        KSR.xlog.xalert("Null in contact:{} Patch it".format(KSR.pv.getw("$ct")))
        KSR.hdr.remove("Contact")
        KSR.hdr.append("Contact: sip:{}@{}:{}\r\n".format(KSR.pv.getw("$fU"), KSR.pv.getw("$si"), KSR.pv.getw("$sp")))
        KSR.textopsx.msg_apply_changes()
        KSR.xlog.xalert("Contact now:{}".format(KSR.pv.getw("$ct")))

    if KSR.sanity.sanity_check(1511, 7) < 0:
        KSR.xlog.xerr("Malformed SIP message from $si:$sp")
        return -255

    if not KSR.pv.is_null("$au") and re.match("(\=)|(\-\-)|(')|(\#)|(\%27)|(\%24)", KSR.pv.getw("$au")):
        KSR.xlog.xalert("SQL Injection in authorization username from IP:$si:$sp - $au")
        KSR.sl.sl_send_reply(503, "There is no money, but you hang in there. Best wishes! Cheers!")
        return -255

    if KSR.is_INVITE() and re.match("(\=)|(\-\-)|(')|(\#)|(\%27)|(\%24)", KSR.pv.getw("$ru")):
        KSR.xlog.xalert("SQL Injection in RURI in INVITE from IP:$si:$sp - $ru")
        KSR.sl.sl_send_reply(503, "There is no money, but you hang in there. Best wishes! Cheers!")
        return -255
    return 1
