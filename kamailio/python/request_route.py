# -*- coding: utf-8 -*-
import KSR
import datetime
import redis
'''
Main SIP request routing logic
 * - processing of any incoming SIP request starts with this route
 * - note: this is the same as route { ... }
'''
def ksr_request_route(self, msg):
    # per request initial checks
    if self.ksr_route_reqinit() == -255:
        return 1

    # NAT detection
    if self.ksr_route_natdetect() == -255:
        return 1

    # CANCEL processing
    if KSR.is_CANCEL():
        self.manage_call_status(KSR.pv.getw("$fU"), 'del')
        KSR.xlog.xinfo("CANCELing request from $fU:$si")
        if KSR.tm.t_check_trans() > 0:
            self.ksr_route_relay()
        return 1

    if KSR.is_BYE():
        self.manage_call_status(KSR.pv.getw("$fU"), 'del')

    # handle requests within SIP dialogs
    if self.ksr_route_withindlg() == -255:
        return 1

    # handle retransmissions
    if (not KSR.is_ACK()) and (KSR.tmx.t_precheck_trans() > 0):
        KSR.tm.t_check_trans()
        return 1

    if KSR.tm.t_check_trans() == 0:
        return 1

    ### only initial requests (no To tag)

    # record routing for dialog forming requests (in case they are routed)
    # - remove preloaded route headers
    KSR.hdr.remove("Route")
    #if KSR.is_method_in("IS") :
    #    KSR.rr.record_route()

    if KSR.is_INVITE() and KSR.pv.is_null("$rU"):
        KSR.sl.sl_send_reply(484, "Address Incomplete")
        return 1

    if KSR.is_method_in("IR"):
        #r = redis.StrictRedis(host='127.0.0.1', port=6379, db=10, password='4yAbW35mqmcv9An')
        r = redis.StrictRedis(host='127.0.0.1', port=6379, db=10, decode_responses=True)
        if r.get("{}:{}".format(KSR.pv.getw("$fU"), KSR.pv.getw("$rU"))) or r.get(KSR.pv.getw("$rU")) or r.get(KSR.pv.getw("$tU")):
            KSR.sl.sl_send_reply(503, "There is no money.")
            return -255
        if KSR.is_INVITE():
            if (KSR.dispatcher.ds_is_from_list(self.DSIDS['MEDIASERVERS']) > 0 or KSR.dispatcher.ds_is_from_list(self.DSIDS['CALLERS']) > 0):
                KSR.setflag(self.FLAGS['FLT_FROM_ASTERISK'])
                KSR.setflag(self.FLAGS['FLT_SKIP_AUTH'])
            if (KSR.dispatcher.ds_is_from_list(self.DSIDS['GW']) > 0):
                KSR.setflag(self.FLAGS['FLT_FROM_GW'])
                KSR.setflag(self.FLAGS['FLT_SKIP_AUTH'])
        if self.GLOBALS['WITH_ASYNC_FRAMEWORK']:
            KSR.asynk.task_route("ksr_route_async_auth")
        else:
            if self.ksr_route_async_auth(msg) == -255:
                return 1
    else:
        KSR.xlog.xerr("Запрос $ru от $fu :: $si дошел до конца request_route и не был обработан")
        KSR.sl.sl_send_reply("404", "Out of order")
    return 1
