# -*- coding: utf-8 -*-
import KSR
def ksr_failure_manage(self, msg):
    if self.ksr_route_natmanage() == -255:
        return 1

    if KSR.tm.t_is_canceled() > 0:
        return 1

    return 1
