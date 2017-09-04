# coding:utf-8
import time
from grpc import ssl_channel_credentials, secure_channel
import random
from WechatProto_pb2_grpc import WechatStub
from taobaoke.settings import ROOT_CERTIFICATES, REMOTE_SERVER, APP_ID, APP_KEY

channel_credential = ssl_channel_credentials(root_certificates=ROOT_CERTIFICATES)
channel_option_dict = ("grpc.ssl_target_name_override", "wechat@root")
channel = secure_channel(REMOTE_SERVER[0], channel_credential, options=[channel_option_dict])
client = WechatStub(channel)
auth_meta = (('appid', APP_ID), ('appkey', APP_KEY))

'''
document:
    https://grpc.io/grpc/python/index.html
'''


#
# def get_notify(call):
#     print call.name
#
#
# status = channel.subscribe(get_notify, try_to_connect=True)

# https://stackoverflow.com/questions/45071567/how-to-send-custom-header-metadata-with-python-grpc


def send(req):
    """
    一个很丑的实现 如果有exception就不停重试
    :param req: 
    :return: 
    """
    global client
    global channel
    exception_flag = True
    random_no = 0

    while exception_flag:
        try:
            rsp = client.HelloWechat(req, metadata=auth_meta)
            exception_flag = False
        except Exception as e:
            print("[{0}]{1}".format(REMOTE_SERVER[random_no], e))
            time.sleep(5)
            random_no = random.randint(0, len(REMOTE_SERVER) - 1)
            channel = secure_channel(REMOTE_SERVER[random_no], channel_credential,
                                     options=[channel_option_dict])
            client = WechatStub(channel)
    return rsp
