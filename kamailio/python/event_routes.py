# -*- coding: utf-8 -*-
import KSR
def ksr_event_dispatcher(self, msg, event):
  host = KSR.pv.getw("$rd")
  if event == "dispatcher:dst-down":
    KSR.xlog.xerr("Destination down: {}".format(host))
  elif event == "dispatcher:dst-up":
    KSR.xlog.xnotice("Destination up: {}".format(host))
  else:
    KSR.xlog.xerr("Unknnown dispatcher event: {}".format(event))
  return 1
