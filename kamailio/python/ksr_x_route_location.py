# -*- coding: utf-8 -*-
import KSR

def ksr_x_route_location (self):
    KSR.xlog.xnotice("Search AOR $ru: do lookup location.")
    res = KSR.registrar.lookup("location")
    if (res < 0):
        KSR.tm.t_newtran()
        if -1 == res:
            KSR.sl.send_reply(404, "AoR not found")
        elif -2 == res:
            KSR.sl.send_reply(405, "Method Not Allowed")
        elif -3 == res:
            KSR.xlog.xerr("Internal error during lookup location for {}".format(KSR.pv.getw("$ru")))
            KSR.sl.sl_reply_error()
        return -255
    KSR.xlog.xnotice("AOR found. Retrun to main logic.")
    return 1
