import os
import fileinput
import sys
import getToken
import getIpAdress
import getpass
 
def itsYouIp(typeIP="", ip = getIpAdress.getIp()):
    print("Это Ваш " + typeIP + " адрес - " + ip + " ? (Y/N)")
    ans = input()
    if(ans.lower() == 'yes' or ans.lower() == 'y'):
        return ip
    elif(ans.lower() == 'no' or ans.lower() == 'n'):
        getIp = createAdress(typeIP + " адресс.")
        return getIp
def replaceAll(file,searchExp,replaceExp):
    for line in fileinput.input(file, inplace=1):
        if searchExp in line:
            line = line.replace(searchExp,replaceExp)
        sys.stdout.write(line)
def createAdress(text):
    while(True):
        print(f'Введите ' + text)
        adr = input().replace(' ', '')
        print('Вы уверены что хотите указать ' + adr + '? (YES/NO)')
        ans = input()
        if(ans.lower() == 'yes' or ans.lower() == 'y'): return adr
def fromTextToArray(path):
    with open(path) as file:
        array = [row.strip() for row in file]
        return array
def availabilityToken(crmAdress):
    while(True):
        print("Имеется токен авторизации? (Yes/no)")
        ans = input()
        if(ans.lower() == 'y' or ans.lower() == 'yes'):
            token = createAdress("токен авторизации")
            testAnsw = getToken.testToken(crmAdress, token)
            if(testAnsw == 200): 
                return token
                break
            else:
                print("Что-то не так, ошибка #" + testAnsw)
        elif(ans.lower() == 'n' or ans.lower() == 'no'): 
            login = createAdress("Логин от администратора: ")
            password = getpass.getpass('Пароль от администратора: ')
            buyerId = createAdress("ID от администратора: ")
            token = getToken.takeToken(crmAdress, buyerId, login, password) 
            print("Ваш токен: " + token)
            return token
            break

array = fromTextToArray('paths.txt')

externalIp = itsYouIp("ВНЕШНИЙ IP") # ip внешка
internalIp = itsYouIp("ВНУТРЕННИЙ IP", externalIp) # внутренний ip
sip_dns = itsYouIp("DNS (sip-dns)", externalIp)
crm_dns = createAdress("DNS от ЦРМ (crm-dns)")
token = availabilityToken(crm_dns)

for item in array:
    replaceAll(item, '"external_ip"', externalIp)
    replaceAll(item, '"sip_ip"', externalIp)
    replaceAll(item, '"internal_ip"', internalIp)
    replaceAll(item, '"sip_dns"', sip_dns)
    replaceAll(item, '"crm_dns"', crm_dns)
    print('Выполняем замену в файле: ' + item)
replaceAll('voip/etc/td_config.json', 'TKN', token)
