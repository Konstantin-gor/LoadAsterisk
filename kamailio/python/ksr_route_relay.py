# -*- coding: utf-8 -*-
import KSR
# wrapper around tm relay function
def ksr_route_relay(self):
    KSR.nathelper.handle_ruri_alias()
    # enable additional event routes for forwarded requests
    # - serial forking, RTP relaying handling, a.s.o.
    if KSR.is_method("INVITE|BYE|SUBSCRIBE|UPDATE") and (KSR.tm.t_is_set("branch_route") < 0):
        KSR.tm.t_on_branch("ksr_branch_manage")

    #if KSR.is_method("INVITE|BYE|SUBSCRIBE|UPDATE") and (KSR.tm.t_is_set("onreply_route") < 0):
    #    KSR.tm.t_on_reply("ksr_onreply_manage")

    if KSR.is_INVITE() and (KSR.tm.t_is_set("failure_route") < 0):
        KSR.tm.t_on_failure("ksr_failure_manage")

    if KSR.isflagset(self.FLAGS['FLT_FROM_ASTERISK']):
        KSR.textops.remove_hf_re("^X-")

    if KSR.tm.t_relay() < 0:
        KSR.xlog.xerr("Cant relay request. Send error.")
        KSR.sl.sl_reply_error()
        return -255
    else:
        return 1
