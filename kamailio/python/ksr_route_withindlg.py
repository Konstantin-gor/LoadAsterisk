# -*- coding: utf-8 -*-
import KSR
# Handle requests within SIP dialogs
def ksr_route_withindlg(self):
    if KSR.siputils.has_totag() < 0:
        return 1

    # sequential request withing a dialog should
    # take the path determined by record-routing
    if KSR.rr.loose_route() > 0:
        if not KSR.isdsturiset():
            KSR.nathelper.handle_ruri_alias()
        if KSR.is_ACK():
            # ACK is forwarded statelessly
            if self.ksr_route_natmanage() == -255:
                return -255
        elif KSR.is_NOTIFY():
            # Add Record-Route for in-dialog NOTIFY as per RFC 6665.
            KSR.rr.record_route()
        elif KSR.is_INVITE():
            KSR.xlog.xinfo("Hande reINVITE")
            KSR.rr.record_route()

        self.ksr_route_relay()
        return -255

    if KSR.is_ACK():
        if KSR.tm.t_check_trans() > 0:
            # no loose-route, but stateful ACK
            # must be an ACK after a 487
            # or e.g. 404 from upstream server
            self.ksr_route_relay()
            return -255
        else:
            # ACK without matching transaction ... ignore and discard
            return -255

    KSR.sl.sl_send_reply(404, "Not here")
    return -255
