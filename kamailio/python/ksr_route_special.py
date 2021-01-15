# -*- coding: utf-8 -*-
import KSR
import requests
import re

# список тестовых домофонов, звонки с них будут заворачиваться на тестовый сервер (test_asterisk)
test_domofones = ["1868823020cf", "186882308537",]
test_asterisk = "sip:td-asterisk1-chel1.is74.ru:5060"


def ksr_special_routing (self, r_user):
    if r_user == "SOS":
        KSR.dispatcher.ds_select_dst(self.DSIDS['MEDIASERVERS'], 4)
        KSR.setbflag(self.FLAGS['FLB_NATB'])
        KSR.xlog.xwarn("Pressed SOS button. Redirect to asterisk for recording. DURI set to:$du")
        return True
    elif r_user == "7298886":
        KSR.xlog.xwarn("Zhilservice")
        KSR.seturi("sip:00573517298886@gw1-chel1.is74.ru")
        # Просто так From нельзя менять.
        KSR.uac.uac_replace_from_uri("sip:2479872@televoip.is74.ru")
        KSR.setbflag(self.FLAGS['FLB_NATB'])
        return True
    elif r_user == "VR":
        KSR.hdr.append("X-Route-to: VoiceRecognition\r\n")
        KSR.dispatcher.ds_select_dst(self.DSIDS['MEDIASERVERS'], 4)
        KSR.setbflag(self.FLAGS['FLB_NATB'])
        KSR.xlog.xinfo("Call for voice recognition redirected to Asterisk. DURI set to:$du")
        return True
    elif re.search("^instruction", r_user):
        KSR.dispatcher.ds_select_dst(self.DSIDS['MEDIASERVERS'], 4)
        KSR.setbflag(self.FLAGS['FLB_NATB'])
        KSR.xlog.xinfo("Call redirected to mediaserver. DURI set to:$du RURI:$ru")
        return True
    elif re.search("^STP_", r_user):
        KSR.seturi("sip:{}@interphone.is74.ru:5060".format(r_user))
        KSR.hdr.append("X-Route-to: STP\r\n")
        KSR.setbflag(self.FLAGS['FLB_NATB'])
        KSR.xlog.xinfo("Call redirected to Interphone. RURI set to:$ru")
        return True
    elif KSR.pv.getw("$fU").lower() in test_domofones:
        direct_call = False # Тестовый звонок напрямую на пользователя
        KSR.setbflag(self.FLAGS['FLB_NATB'])
        if direct_call:
            KSR.setuser("id206670") # Подставить выбранного пользователя
            if self.ksr_x_route_location() == -255:
                exit()
        else:
            KSR.setdsturi(test_asterisk) # Маршрутизируем в какой либо сервер принудительно
        KSR.setbflag(self.FLAGS['FLB_NATB'])
        KSR.xlog.xinfo("Test call from $fU to $rU apartment. RURI: $ru DURI: $du")
        return True
    elif re.search("^(.+)\.vd\.is74\.ru$", r_user):
        handset = r_user.split('.')
        uri = 'sip:' + handset.pop(0) + '@' + '.'.join(handset)
        KSR.xlog.xinfo("STP call from $fU to $rU, setting RURI to {}".format(uri))
        KSR.seturi(uri)
        # Просто так From нельзя менять.
        KSR.uac.uac_replace_to_uri(uri)
        KSR.setbflag(self.FLAGS['FLB_NATB'])
        return True
    return False
