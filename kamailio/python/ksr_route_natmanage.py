# -*- coding: utf-8 -*-
import KSR
import re
# RTPEngine control and signaling updates for NAT traversal
def ksr_route_natmanage(self):
    if (KSR.siputils.is_request() > 0):
        if (KSR.siputils.has_totag() > 0) and (KSR.rr.check_route_param("nat=yes") > 0):
            KSR.setbflag(self.FLAGS['FLB_NATB'])
        elif (KSR.tmx.t_is_branch_route() > 0):
            if KSR.isdsturiset() and self.is_ip_internal(KSR.pv.getw("$dd")):
                KSR.xlog.xnotice("In DURI domain $dd is RFC1918. Mark for NAT")
                KSR.setbflag(self.FLAGS['FLB_NATB'])
            if self.is_ip_internal(KSR.pv.getw("$rd")):
                KSR.xlog.xnotice("In RURI domain $rd is RFC1918. Mark for NAT")
                KSR.setbflag(self.FLAGS['FLB_NATB'])

    if (KSR.siputils.is_reply() > 0):
        if (KSR.siputils.has_totag() > 0):
            KSR.setbflag(self.FLAGS['FLB_NATB'])
        elif (KSR.textops.has_body() > 0):
            if KSR.textops.search_body("127.0.0.2") > 0:
                # Патчим 200 ответы от астериска
                KSR.setbflag(self.FLAGS['FLB_NATB'])
            elif KSR.nathelper.nat_uac_test(9) > 0:
                KSR.setbflag(self.FLAGS['FLB_NATB'])

    if not (KSR.isflagset(self.FLAGS['FLT_NATS']) or KSR.isbflagset(self.FLAGS['FLB_NATB'])):
        return 1

    if (KSR.textops.has_body() > 0) or KSR.is_method("BYE|CANCEL") or (KSR.siputils.is_reply() > 0 and 300 <= KSR.pv.getw("$rs") <= 399):
        rtpengine_lp = "loop-protect "
        if self.GLOBALS['WITH_LOOPPROTECT_PATCH'] and (KSR.siputils.is_reply() > 0) and (KSR.textops.has_body() > 0) and (KSR.textops.search_body("a=rtpengine") > 0):
            KSR.xlog.xnotice("Client return looprotect param. Check SDP for our rtprngine IP " + self.GLOBALS['DEFINE_RTPENGINE_IP'])
            KSR.sdpops.sdp_get_line_startswith("$avp(cline)", "c=")
            KSR.sdpops.sdp_get_line_startswith("$avp(oline)", "o=")
            if not (self.GLOBALS['DEFINE_RTPENGINE_IP'] in KSR.pv.getw("$avp(cline)") or self.GLOBALS['DEFINE_RTPENGINE_IP'] in KSR.pv.getw("$avp(oline)")):
                KSR.xlog.xalert("In c/o param not found our rtprngine IP {}. Try to remove loop protect param for calls".format(self.GLOBALS['DEFINE_RTPENGINE_IP']))
                KSR.sdpops.remove_line_by_prefix("a=rtpengine", "")
                if (KSR.tmx.t_is_request_route() > 0) or (KSR.tmx.t_is_reply_route() > 0):
                    KSR.textopsx.msg_apply_changes()
                    # Сбрасываем флаг - IP адреса чужие, а клиент вернул
                    # нашу защиту от петли в rtpengine
                    rtpengine_lp = ""
        # Проверяем - необходимо пропустить через RTPProxy SDP?
        # 8 - The SDP is searched for occurrence of RFC1918 or RFC6598 addresses
        # 'c' = replace-session-connection
        # 'o' = replace-origin
        # trust-address (flag 'r' in rtpproxy) enabled by default. To disable it need to use
        # SIP-source-address - opposite for trust-address flag
        if KSR.nathelper.is_rfc1918("$rd") and KSR.pv.getw("$rd") != "127.0.0.1" and KSR.pv.getw("$rd") != "<null>" and KSR.pv.getw("$rd") != ""sip_dns"" and KSR.pv.getw("$rd") != "10.5.26.236" and KSR.pv.getw("$tU") != "location":
            KSR.rtpengine.rtpengine_manage(rtpengine_lp + "replace-session-connection external internal replace-origin SIP-source-address to-tag")
        else:
            KSR.rtpengine.rtpengine_manage(rtpengine_lp + "replace-session-connection external external replace-origin SIP-source-address to-tag")
        if KSR.pv.getw("$rc") < 0:
            KSR.xlog.xalert("Calling rtpengine_manage() cause troubles!")

    if (KSR.siputils.is_request() > 0) and not (KSR.siputils.has_totag() > 0) and (KSR.tmx.t_is_branch_route() > 0):
        KSR.rr.add_rr_param(";nat=yes")

    #if (KSR.siputils.is_reply() > 0) and KSR.isbflagset(self.FLAGS['FLB_NATB']) and (KSR.siputils.is_first_hop() > 0):
        #KSR.xlog.xinfo("Reply with FLB_NATB and first hop. Set contact alias")
    if (KSR.siputils.is_reply() > 0) and KSR.isbflagset(self.FLAGS['FLB_NATB']):
        KSR.nathelper.set_contact_alias()

    return 1
