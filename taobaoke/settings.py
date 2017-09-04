# _*_ coding:utf-8 _*_
import redis

APP_ID = "dabaiceo"
APP_KEY = "a4d230c750c5116a65a07ad976e5d6d5"
# APP_ID = "test11"
# APP_KEY = "b614773532869704e980e7e1e4f30bec"

# REMOTE_SERVER = ["122.114.187.166:10086"]
# , "122.114.187.166:10086", "122.114.187.166:12580"]"122.112.211.25:12580",
REMOTE_SERVER = ["123.58.7.124:12580", "115.159.69.236:12580"]
LONG_SERVER = "long.weixin.qq.com"
SHORT_SERVER = "short.weixin.qq.com"

channel_option_name = "grpc.ssl_target_name_override"
channel_option_value = "wechat@root"
red = redis.Redis(host='s-poc-01.qunzhu666.com', port=50002)

ROOT_CERTIFICATES = r'''-----BEGIN CERTIFICATE-----
MIIFLjCCAxYCAQEwDQYJKoZIhvcNAQELBQAwXTELMAkGA1UEBhMCQ04xCzAJBgNV
BAgMAkpTMQswCQYDVQQHDAJaSjENMAsGA1UECgwEc2lubzEPMA0GA1UECwwGd2Vj
aGF0MRQwEgYDVQQDDAt3ZWNoYXRAcm9vdDAeFw0xNzA1MDcxNTM4NDFaFw0xODA1
MDcxNTM4NDFaMF0xCzAJBgNVBAYTAkNOMQswCQYDVQQIDAJKUzELMAkGA1UEBwwC
WkoxDTALBgNVBAoMBHNpbm8xDzANBgNVBAsMBndlY2hhdDEUMBIGA1UEAwwLd2Vj
aGF0QHJvb3QwggIiMA0GCSqGSIb3DQEBAQUAA4ICDwAwggIKAoICAQDOAe/tUzP6
5kwObDONJlyLXLhvV7rxjsnon3B3q8simDoYtTPT2sgBcKmAjWe4rwpRoifKgw8t
T7uvKg8qJLPmCb2b88S6T/fcykiDavTaBCevf05+9ua3+onfbJmwFzeo6yIkFt9H
sUOUCsFTKq5E35bk7Dvlv/U0Wx3G4pYc0OnaQlCSeeGj1KSrOb7xaYS8uySEYWQ9
0jC+IEu3S/GYe3EvvFP/vnVQCMh+wZvtdbh/Ks/s/8YFXVhfaKdvNzhXr8mI0h6q
kyRU9JUCujzbDRFk0xew2ddhGZVNVampb37DuhX7ytXp0FFl8daJkH2KpmM7GVLk
u5bNe4e6vw4J2QgsOiU2XaaFHpPmuNODwbO3QWnBSJFxQiDbcWxSf2+Mpnf057Nm
5xA7LQE0WlUEp7k+HuIHL3tUDAbX16Mx1A+fpS3W0SYBqnQGubJNf0UybNca3BkH
RHFvUcB3c87fQKu/ql2xJvTKxw3pY/EtpqZGpPTEX1YoeweSG3Ljms4dJpOqMMb3
uPTLde27dNogIB6z0bkNLYR7wUYe3eWy3NESSrKYhnVxITcetI3e1rVvMRKDiksn
DsVpg+2jGee2PMI4DXvmYRR9mE9j/LiBQOxJFMQJFgOfPmB6cVgcvZIBqLI3QTc1
RoJCQ4SkyXXGBQ6SD3tCChD7D+Ef4uB5jwIDAQABMA0GCSqGSIb3DQEBCwUAA4IC
AQCH6r1yN70XPMgc4VFdCOJo/+hsdedbMQNfLCuf/ehbmSz/3+n8VnkyySrABlJ1
bsL5Zsm9t3LvNsG/ZoVQMncH2+x0A4eRAu+oH7lZrI4f+9AXxys3d5I78RX0mO2Q
Vs0zsDT0nAERuvZwYpjYtXhJXHgvPArhenLYOu6AyfxM4qAX/igAd8Kp4FOhf7jp
/+pPQARRba4Ifig1PbHMIxjOX5U6BySzC+h1hiGjFX8NVRUTYuXZEytoVCwH5JgI
J+tCcSi/AndTHm1dEKxFKeaX14UEhIk24JXdqoVvbYEFHuAKukhuQkSGhwRDs+QX
E3L+xHzKFE97ZGy+d6xRy7rVi8yeXjG1/cAKQ0/6PzfJOoMKBGm86EpB77QBg7my
KTz3OFZI8+LYBQhN7b4HGkNOCORHVAUP2b1DC6RPZH1fbSjWoojrwlWxlh972eWw
+WCYXU6Qo/6wj4hbZM+3KHJbCRKXnPs+aOlJSYyrXLqpvU2YCuwozuXBJtztUWe/
Xl7DYTH9Ssogvak/dZCpQkh1t7OPWWeHqytuCmKvwcxxaMWaWIZTmPsEis8blSRM
+CVF4UZmuhmovepQUdKSEeif4JNBcR5tGEVRBolFG6gkxSrHMEdRSlN+ok35Y4Dx
gwxovjAkCy0J1v8ik0z+87PacxygmgRjk7StkhqugaMEDg==
-----END CERTIFICATE-----'''

CONST_PROTOCOL_DICT = {
    "version": "6.5.12",
    # 替换自己的授权码
    # "machine_code": "708fbb64cce3fe5f37887945a24edb43",
    "machine_code": "e2b15a1a62075149e21d31f4dba27d0a",
    # 初始化key 此key由授权人员分配
    "random_encry_key": [80, 117, 128, 85, 2, 55, 180, 126, 141, 93, 185, 220, 112, 142, 15, 128],
    # 在不知道用户设备的id的的时候固定或者随机 但必须保持 单一账号使用同一个设备id同一个设备ID 不建议多号登陆 一封就封一批 建议登陆账号的md5作为设备id 或wxid 的md5作为设备id
    "deviceId": "1cdb5ab6695376cf6049c2d6c4445bc"
}
