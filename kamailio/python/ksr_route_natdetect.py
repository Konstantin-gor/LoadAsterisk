# -*- coding: utf-8 -*-
import KSR
# Caller NAT detection
def ksr_route_natdetect(self):
    KSR.force_rport()
    if KSR.nathelper.nat_uac_test(19) > 0:
        KSR.xlog.xdbg("Client behind NAT.")
        if KSR.is_REGISTER():
            KSR.nathelper.fix_nated_register()
        elif KSR.siputils.is_first_hop() > 0:
            KSR.nathelper.set_contact_alias()

        KSR.setflag(self.FLAGS['FLT_NATS'])
    else:
        KSR.xlog.xdbg("NAT not detected.")

    return 1
