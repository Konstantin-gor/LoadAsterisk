# -*- coding: utf-8 -*-
import KSR
import requests
import re
import datetime
import time
import redis

def ksr_route_async_auth(self, msg):
    furi = KSR.pv.getw("$fu")
    ruri = KSR.pv.getw("$ru")
    if KSR.is_INVITE():
        KSR.xlog.xnotice("Do auth procedure for {} from {}:{}".format(ruri, furi, KSR.pv.getw("$si")))
    if KSR.auth_db.is_subscriber(furi, "subscriber", 2) > 0 and not KSR.isflagset(self.FLAGS['FLT_SKIP_AUTH']):
        if not KSR.is_REGISTER():
            KSR.xlog.xinfo("Request from local subscriber")
        KSR.setflag(self.FLAGS['FLT_FROM_SUBSCRIBER'])
    if KSR.auth_db.is_subscriber(ruri, "subscriber", 2) > 0:
        if not KSR.is_REGISTER():
            KSR.xlog.xinfo("Request to local subscriber")
        KSR.setflag(self.FLAGS['FLT_TO_SUBSCRIBER'])

    if KSR.isflagset(self.FLAGS['FLT_FROM_SUBSCRIBER']):
        if not KSR.isflagset(self.FLAGS['FLT_SKIP_AUTH']):
            res = KSR.auth_db.auth_check(KSR.pv.getw("$fd"), "subscriber", 1)
            if res < 0:
                if res == -2:
                    # -2 Wrong passworg
                    KSR.xlog.xnotice("Wrong password. From:$fU Auth user:$au")
                    KSR.sl.sl_send_reply(403, "You're not welcome here")
                    if KSR.is_REGISTER():
                        self.send_registration_info_to_redis('False',time.time())
                else:
                    KSR.auth.auth_challenge(KSR.pv.getw("$fd"), 0)
                return -255
            else:
                if KSR.is_REGISTER():
                    self.send_registration_info_to_redis('True',time.time())
                # user authenticated - remove auth header
                # if not KSR.is_method("REGISTER,PUBLISH") :
                KSR.auth.consume_credentials()
    elif not KSR.isflagset(self.FLAGS['FLT_SKIP_AUTH']):
        # Отпинываем нелокальных абонентов
        KSR.sl.send_reply(406, "Not acceptable")
        return -255

    if not KSR.isflagset(self.FLAGS['FLT_SKIP_AUTH']):
        # if caller is not local subscriber, then check if it calls
        # a local destination, otherwise deny, not an open relay here
        if (not KSR.is_myself(furi)
                and (not KSR.is_myself(ruri))):
            KSR.sl.sl_send_reply(403, "Not relaying")
            return -255
            # authentication not enabled - do not relay at all to foreign networks
        if not KSR.is_myself(ruri):
            KSR.sl.sl_send_reply(403, "Not relaying")
            return -255

    # Jump from async route, based on processing SIP method
    if self.GLOBALS['WITH_ASYNC_FRAMEWORK']:
        KSR.asynk.task_route('ksr_route_async_' + KSR.pv.getw("$rm"))
    else:
        # lambda will generate 500 error if something went wrong
        getattr(self, 'ksr_route_async_' + KSR.pv.getw("$rm"), lambda: -255)(msg)
    return -255

def ksr_route_async_INVITE(self, msg):
    if KSR.hdr.is_present("UUID") < 0:
        uuid = KSR.pv.getw("$uuid(g)")
        KSR.xlog.xinfo("Add hdr UUID: {}. Call from $fU@$fd:$si to $rU".format(uuid))
        KSR.hdr.append("UUID: {}\r\n".format(uuid))
    else:
        uuid = KSR.pv.getw("$hdr(UUID)")

    self.store_uuid(KSR.pv.getw("$ci"),uuid)
    self.manage_call_status(KSR.pv.getw("$fU"), 'put')
    
    if KSR.isflagset(self.FLAGS['FLT_FROM_ASTERISK']):
        if KSR.hdr.is_present("X-Kamailio-URI") > 0:
            KSR.hdr.append("X-Kamailio-Timestamp: {}\r\n".format(time.time()))
            if KSR.hdr.is_present("X-URI-Type") < 0:
                # Для звонков на aor/location/handset через RUser
                uri_type = KSR.pv.getw("$rU")
            else:
                uri_type = KSR.pv.getvs("$hdr(X-URI-Type)", "location")
            KSR.seturi(re.sub(r"(^<|>$)", "", KSR.pv.getw("$hdr(X-Kamailio-URI)")))
            if uri_type == "location":
                if self.ksr_x_route_location() == -255:
                    return -255
            elif uri_type == "handset":
                KSR.xlog.xwarn("Call to handset. Replace TURI with RURI:{}".format(KSR.pv.getw("$ru")))
                KSR.uac.uac_replace_to_uri(KSR.pv.getw("$ru"))
            else:
                if KSR.nathelper.handle_ruri_alias() > 0:
                    KSR.xlog.xnotice("Handling RURI alias. DURI:$du RURI:$ru from $fU")
        else:
            KSR.xlog.xnotice("From asterisk returned Unknow number. Drop it")
            KSR.sl.sl_send_reply(404, "Not here")
            return -255
    elif KSR.isflagset(self.FLAGS['FLT_FROM_GW']):
        r = redis.StrictRedis(host='127.0.0.1', port=6379, db=12, decode_responses=True)
        domophone_name = r.get(KSR.pv.getw("$tU"))
        if domophone_name:
            KSR.seturi('sip:' + str(domophone_name) + '@televoip.is74.ru:7777')
            KSR.xlog.xinfo("call from gw to domophone {}".format(domophone_name))
            if self.ksr_x_route_location() == -255:
                KSR.xlog.xerr("Lookup location error")
                return -255
        else:
            KSR.sl.sl_send_reply(404, "user not found")
            KSR.xlog.xinfo("domophone for call from gw not found")
            return -255
    elif not KSR.isflagset(self.FLAGS['FLT_TO_SUBSCRIBER']): # проверяем наличие флага
        if not self.ksr_special_routing(KSR.pv.getw("$rU")):
            # Re-route to asterisk
            KSR.dispatcher.ds_select_dst(self.DSIDS['MEDIASERVERS'], 4)
            KSR.setbflag(self.FLAGS['FLB_NATB'])
            KSR.xlog.xinfo("Unknown number. Send to Asterisk:$du")
    elif KSR.isflagset(self.FLAGS['FLT_FROM_SUBSCRIBER']) and KSR.isflagset(self.FLAGS['FLT_TO_SUBSCRIBER']):
        if KSR.pv.getw("$fU") == self.GLOBALS.get('TEST_ACCAUNT', False):
            KSR.xlog.xnotice("Direct call from test accaunt $fU to $rU")
            if self.ksr_x_route_location() == -255:
                KSR.xlog.xerr("Lookup location error")
                return -255
        else:
            # Лучше по максимуму сузить маску для дропа
            KSR.xlog.xwarn("Old LOGIC (dropping request)::Requested user $rU from $fU:$si")
            KSR.sl.sl_send_reply(403, "Forbidden direct call to user")
            KSR.set_drop()
            return -255



    KSR.rr.record_route()

    if self.ksr_route_relay() == -255:
        return -255
    return 1

def ksr_route_async_REGISTER(self, msg):
    if KSR.isflagset(self.FLAGS['FLT_NATS']):
        KSR.setbflag(self.FLAGS['FLB_NATB'])
        # do SIP NAT pinging
        KSR.setbflag(self.FLAGS['FLB_NATSIPPING'])
    if KSR.registrar.save("location", 0) < 0:
        KSR.xlog.xerr("Cant store AoR")
        KSR.sl.sl_reply_error()
    else:
        # Фильтруем УДАЧНЫЕ регистрации на предмет необходимости уведомлений
        self.check_registration_uri()
    return -255
