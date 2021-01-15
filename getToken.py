import os
import requests
import json


def takeToken(crmAdress, buyerId, login, password):
    request = requests.post(f'https://{crmAdress}/api/auth',data={'BUYER_ID':buyerId,'LOGIN':login,'PASS':password})
    return request.json()['TOKEN']
def testToken(crmAdress, token):
    if crmAdress == None:
        crmAdress = createAdress("адресс Вашей ЦРМ, к примеру - crm.tele-plus.ru, указывать протокол (по типу http) не нужно.")
    request = requests.get(f'https://{crmAdress}/api/entrances', headers={'Authorization':'Bearer ' + token})
    return request.status_code
 
 
 