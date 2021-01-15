import http.client

def getIp():
    conn = http.client.HTTPConnection("ifconfig.me")
    conn.request("GET", "/ip")
    ip = conn.getresponse().read().decode("utf-8")
    return ip
