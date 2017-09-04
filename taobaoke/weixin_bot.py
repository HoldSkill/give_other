# _*_ coding:utf-8 _*_
import json
import threading

import requests
import base64
import pickle
import time
import urllib2
from datetime import datetime
import settings
from WechatProto_pb2 import WechatMsg, BaseMsg, User
from grpc_module import grpc_client
from settings import CONST_PROTOCOL_DICT
from settings import red
from taobaoke import app, db
from taobaoke.database import model
from taobaoke.utils import common_utils
from tcp_module import WechatClient
from utils import grpc_utils
from utils import oss_utils
from utils.common_utils import get_time_stamp, read_int, int_list_convert_to_byte_list, char_to_str, \
    check_buffer_16_is_191, get_public_ip, check_grpc_response, get_md5, usc2ascii
from rule import action_rule


class WXBot(object):
    def __init__(self):
        self.long_host = settings.LONG_SERVER
        self.short_host = settings.SHORT_SERVER
        # self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)
        self.wechat_client = None
        # 随机MD5
        self.deviceId = get_md5(str(time.time()))

        # 是否在同步中
        self.__is_async_check = False
        self.__lock = threading.Lock()

    def set_user_context(self, wx_username):
        # TODO：self.wx_username 不该在这初始化，待修改
        self.wx_username = wx_username
        with app.app_context():
            bot_param = model.BotParam.query.filter_by(Username=wx_username).first()
            if bot_param:
                self.long_host = bot_param.LongHost
                self.short_host = bot_param.ShortHost
        self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)

    def open_notify_callback(self):
        # 注册回调
        self.wechat_client.register_notify(self.process_notify_package)

    def process_notify_package(self, data):
        # 接收到notify包时的回调处理
        cmd = common_utils.read_int(data, 8)
        if cmd == 318:
            print "cmd 318"
            # 这里decode出来的都是微信的官网的html，所以没必要print出来了
            # v_user = pickle.loads(red.get('v_user_' + self.wx_username))
            # if v_user is not None:
            #     threading.Thread(target=self.decode_cmd_318, args=(v_user, data,)).start()

        if data is not None and len(data) >= 4:
            selector = common_utils.read_int(data, 16)
            if selector > 0:
                print "selector:{0} start sync thread".format(selector)

                # TODO：在 set_user_context 中定义的wx_username, 这么写不好, 待修改
                if self.wx_username is not None and self.wx_username != "":
                    if self.__lock.acquire():
                        # 确保只有一个线程在执行async_check，否则会接受多次相同的消息
                        if not self.__is_async_check:
                            self.__is_async_check = True
                            self.__lock.release()
                        else:
                            print "*********skip async check*********"
                            self.__lock.release()
                            return

                    # 拉取消息之前先查询是否是登陆状态
                    # 因为用户ipad登陆的同时登陆其他平台，socket仍然会收到notify包
                    with app.app_context():
                        user_db = model.User.query.filter_by(userame=self.wx_username).first()
                        is_login = user_db.login == 1

                    if is_login:
                        bot = WXBot()
                        v_user = pickle.loads(red.get('v_user_' + self.wx_username))
                        bot.async_check(v_user)
                    self.__is_async_check = False

    def logout_bot(self, v_user):
        # 退出机器人，并非退出微信登陆
        with app.app_context():
            user_db = model.User.query.filter_by(userame=v_user.userame).first()
            user_db.login = 0
            db.session.commit()

    def get_qrcode(self, md_username):
        """
        获取qrcode
        :return: 
        """
        # session_key = '5326451F200E0D130CE4AE27262B5897'.decode('hex')
        # 构造qrcode请求
        self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)
        self.deviceId = get_md5(md_username)

        qrcode_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=502,
                user=User(
                    sessionKey=int_list_convert_to_byte_list(CONST_PROTOCOL_DICT['random_encry_key']),
                    deviceId=self.deviceId
                )
            )
        )
        qrcode_rsp = grpc_client.send(qrcode_req)
        check_grpc_response(qrcode_rsp.baseMsg.ret)
        (buffers, seq) = grpc_utils.get_seq_buffer(qrcode_rsp)
        data = self.wechat_client.sync_send_and_return(buffers)
        qrcode_req.baseMsg.cmd = -502
        qrcode_req.baseMsg.payloads = char_to_str(data)
        qrcode_rsp = grpc_client.send(qrcode_req)

        buffers = qrcode_rsp.baseMsg.payloads
        # 保存二维码图片
        qr_code = json.loads(buffers)
        imgData = base64.b64decode(qr_code['ImgBuf'])
        uuid = qr_code['Uuid']

        with app.app_context():
            model.save_qr_code(qr_code)

        try:
            oss_path = oss_utils.put_object_to_oss(uuid + ".png", imgData)
            print("oss_path is: {}".format(oss_path))
        except Exception as e:
            print(e)
            print('upload oss err by uuid:{}'.format(uuid))
        return oss_path, qrcode_rsp, self.deviceId

    def check_qrcode_login(self, qrcode_rsp, device_id):
        """
        检测扫描是否登陆
        :param qr_code: 
        :return: 
        """
        buffers = qrcode_rsp.baseMsg.payloads
        qr_code = json.loads(buffers)
        uuid = qr_code['Uuid']
        notify_key_str = base64.b64decode(qr_code['NotifyKey'].encode('utf-8'))
        long_head = qrcode_rsp.baseMsg.longHead
        start_time = datetime.now()
        self.deviceId = device_id
        while qr_code['Status'] is not 2:
            # 构造扫描确认请求
            check_qrcode_grpc_req = WechatMsg(
                token=CONST_PROTOCOL_DICT['machine_code'],
                version=CONST_PROTOCOL_DICT['version'],
                timeStamp=get_time_stamp(),
                iP=get_public_ip(),
                baseMsg=BaseMsg(
                    cmd=503,
                    longHead=long_head,
                    payloads=str(uuid),
                    user=User(
                        sessionKey=int_list_convert_to_byte_list(CONST_PROTOCOL_DICT['random_encry_key']),
                        deviceId=self.deviceId,
                        maxSyncKey=notify_key_str
                    )
                )
            )

            checkqrcode_grpc_rsp = grpc_client.send(check_qrcode_grpc_req)
            (buffers, seq) = grpc_utils.get_seq_buffer(checkqrcode_grpc_rsp)
            buffers = self.wechat_client.sync_send_and_return(buffers)
            check_buffer_16_is_191(buffers)

            # 将微信包传给grpc服务器，进行一次解包操作
            checkqrcode_grpc_rsp.baseMsg.cmd = -503
            checkqrcode_grpc_rsp.baseMsg.payloads = char_to_str(buffers)
            checkqrcode_grpc_rsp_2 = grpc_client.send(checkqrcode_grpc_rsp)
            payloads = checkqrcode_grpc_rsp_2.baseMsg.payloads
            if 'unpack err' not in payloads:
                qr_code = json.loads(payloads)

            if qr_code['Status'] is 2:
                # save qr_code
                with app.app_context():
                    qr_code_db = model.Qrcode.query.filter_by(Uuid=uuid).order_by(model.Qrcode.id.desc()).first()
                    model.update_qr_code(qr_code, qr_code_db)
                # 成功登陆
                return qr_code
            elif qr_code['Status'] is 0:
                # 未扫描等待扫描
                pass
            elif qr_code['Status'] is 1:
                # 已扫描未确认
                pass
            elif qr_code['Status'] is 4:
                # 已取消扫描
                pass
            # 等待5s再检测
            time.sleep(5)
            # 如果3分钟都没有正常返回status 2 返回False
            if (datetime.now() - start_time).seconds >= 60 * 3:
                return False

    def confirm_qrcode_login(self, qr_code, keep_heart_beat):
        # 重置longHost
        with app.app_context():
            bot_param = model.BotParam.query.filter_by(Username=qr_code['Username']).first()
            if bot_param and bot_param.LongHost is not None and bot_param.LongHost != "":
                self.long_host = bot_param.LongHost
                self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)

        # 微信确认登陆模块
        UUid = u"667D18B1-BCE3-4AA2-8ED1-1FDC19446567"
        DeviceType = u"<k21>TP_lINKS_5G</k21><k22>中国移动</k22><k24>c1:cd:2d:1c:5b:11</k24>"
        payLoadJson = "{\"Username\":\"" + qr_code['Username'] + "\",\"PassWord\":\"" + qr_code[
            'Password'] + "\",\"UUid\":\"" + UUid + "\",\"DeviceType\":\"" + DeviceType + "\"}"

        qrcode_login_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=1111,
                user=User(
                    sessionKey=int_list_convert_to_byte_list(CONST_PROTOCOL_DICT['random_encry_key']),
                    deviceId=self.deviceId
                ),
                payloads=payLoadJson.encode('utf-8')
            )
        )

        qrcode_login_rsp = grpc_client.send(qrcode_login_req)
        (buffers, seq) = grpc_utils.get_seq_buffer(qrcode_login_rsp)
        buffers = self.wechat_client.sync_send_and_return(buffers)
        check_buffer_16_is_191(buffers)

        # 解微信包
        qrcode_login_rsp.baseMsg.cmd = -1001
        qrcode_login_rsp.baseMsg.payloads = char_to_str(buffers)
        qrcode_login_rsp = grpc_client.send(qrcode_login_rsp)
        with app.app_context():
            bot_param_db = model.BotParam.query.filter_by(Username=qr_code['Username']).first()
            if bot_param_db is None:
                model.save_bot_param(qr_code['Username'], self.deviceId, qrcode_login_rsp.baseMsg.longHost,
                                     qrcode_login_rsp.baseMsg.shortHost)
            else:
                model.update_bot_param(bot_param_db, qr_code['Username'], self.deviceId,
                                       qrcode_login_rsp.baseMsg.longHost,
                                       qrcode_login_rsp.baseMsg.shortHost)
        if qrcode_login_rsp.baseMsg.ret == -301:
            # 返回-301代表重定向
            self.wechat_client.close_when_done()
            # 在user表写上gg，麻烦重新登录吧
            return False
        elif qrcode_login_rsp.baseMsg.ret == 0:
            # 返回0代表登陆成功
            print('login successful')
            # 将User赋值
            v_user = qrcode_login_rsp.baseMsg.user
            # 存下v_user
            with app.app_context():
                model.save_user(v_user)

            with app.app_context():
                try:
                    user_db = model.User.query.filter_by(userame=v_user.userame).first()
                    user_db.login = 1
                    db.session.commit()
                except Exception as e:
                    print(e)

            # if keep_heart_beat:
            # 登陆成功，维持心跳
            #     asyn_rec_thread = threading.Thread(target=self, WXBot.heart_beat(v_user))
            #     asyn_rec_thread.start()

            red.set('v_user_' + str(v_user.userame), pickle.dumps(v_user))
            self.wechat_client.close_when_done()
            return True
        else:
            print("qrcode_login_rsp.baseMsg.ret is {}".format(qrcode_login_rsp.baseMsg.ret))
            print("原因是{}".format(qrcode_login_rsp.baseMsg.payloads))
            return False

    def heart_beat(self, v_user):
        """
        30到60s的定时心跳包
        主要用来维持socket的链接状态
        :param v_user: 
        :return: 
        """
        sync_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=205,
                user=v_user
            )
        )
        sync_rsp = grpc_client.send(sync_req)
        (buffers, seq) = grpc_utils.get_seq_buffer(sync_rsp)
        buffers = self.wechat_client.sync_send_and_return(buffers)
        if buffers is None:
            return False

        ret_code = ord(buffers[16])
        if ret_code is not 191:
            selector = read_int(buffers, 16)
            print "--heartbeat() selector is:{}--".format(selector)
            # if selector == -1:
            #     print "user logout when heartbeat"
            #
            # if selector > 0:
            #     v_user = pickle.loads(red.get('v_user_' + v_user.username))
            #     self.async_check(v_user)

        return True
        # selector = read_int(buffers, 16)
        # 更新user状态
        # with app.app_context():
        #     try:
        #         user_db = model.User.query.filter_by(userame=v_user.userame).first()
        #         user_db.login = selector
        #         db.session.commit()
        #     except Exception as e:
        #         print(e)
        # return selector < 0

    def auto_auth(self, v_user, uuid, device_type, new_socket=True):
        with app.app_context():
            bot_param = model.BotParam.query.filter_by(Username=v_user.userame).first()
            if bot_param:
                self.long_host = bot_param.LongHost
                if new_socket:
                    self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)

        pay_load = "{\"UUid\":\"" + uuid + "\",\"DeviceType\":\"" + device_type + "\"}"
        auto_auth_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=702,
                user=v_user,
                payloads=pay_load.encode('utf-8')
            )
        )

        auto_auth_rsp = grpc_client.send(auto_auth_req)
        (buffers, seq) = grpc_utils.get_seq_buffer(auto_auth_rsp)
        buffers = self.wechat_client.sync_send_and_return(buffers, close_socket=new_socket)
        self.wechat_client.check_buffer_16_is_191(buffers)

        auto_auth_rsp.baseMsg.cmd = -702
        auto_auth_rsp.baseMsg.payloads = buffers
        auto_auth_rsp_2 = grpc_client.send(auto_auth_rsp)
        if auto_auth_rsp_2.baseMsg.ret == 0:
            user = auto_auth_rsp_2.baseMsg.user
            print("二次登陆成功")
            v_user_pickle = pickle.dumps(user)
            red.set('v_user_' + v_user.userame, v_user_pickle)
            return True
        elif auto_auth_rsp_2.baseMsg.ret == -100 or auto_auth_rsp_2.baseMsg.ret == -2023:
            print("二次登陆失败，重新扫码吧朋友")

            ret_reason = ''
            try:
                payload = auto_auth_rsp_2.baseMsg.payloads
                start = "<Content><![CDATA["
                end = "]]></Content>"
                ret_reason = payload[payload.find(start) + len(start):payload.find(end)]
            except Exception as e:
                ret_reason = "未知"

            # oss_utils.beary_chat("淘宝客：{0} 已掉线,原因:{1}".format(v_user.nickname, ret_reason))
            self.wechat_client.close_when_done()
            return False
        else:
            print("二次登陆未知返回码")
            ret_code = auto_auth_rsp_2.baseMsg.ret
            # oss_utils.beary_chat("淘宝客：{0} 已掉线,未知返回码:{1}".format(v_user.nickname, ret_code))
            self.wechat_client.close_when_done()
            return False

    def async_check(self, v_user, new_socket=True):
        with app.app_context():
            bot_param = model.BotParam.query.filter_by(Username=v_user.userame).first()
            if bot_param:
                self.long_host = bot_param.LongHost
                if new_socket:
                    self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)

        sync_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=138,
                user=v_user
            )
        )
        sync_rsp = grpc_client.send(sync_req)
        (buffers, seq) = grpc_utils.get_seq_buffer(sync_rsp)
        buffers = self.wechat_client.sync_send_and_return(buffers, close_socket=new_socket)
        if not check_buffer_16_is_191(buffers):
            try:
                # TODO:uuid 和 devicetype 存起来？
                UUid = u"667D18B1-BCE3-4AA2-8ED1-1FDC19446567"
                DeviceType = u"<k21>TP_lINKS_5G</k21><k22>中国移动</k22><k24>c1:cd:2d:1c:5b:11</k24>"
                if self.auto_auth(v_user, UUid, DeviceType, new_socket=new_socket):
                    v_user = pickle.loads(red.get('v_user_' + v_user.userame))
                    self.async_check(v_user, new_socket=new_socket)
                    return True

                self.logout_bot(v_user)

                print(read_int(buffers, 18))
                if read_int(buffers, 18) == -13:
                    print("Session Time out 离线或用户取消登陆 需执行二次登录")
            except Exception as e:
                print(e)
            return False
        else:
            sync_rsp.baseMsg.cmd = -138
            sync_rsp.baseMsg.payloads = char_to_str(buffers)
            sync_rsp = grpc_client.send(sync_rsp)
            # 刷新用户信息
            v_user = sync_rsp.baseMsg.user

            v_user_pickle = pickle.dumps(v_user)
            red.set('v_user_' + v_user.userame, v_user_pickle)

            msg_list = json.loads(sync_rsp.baseMsg.payloads)
            if msg_list is not None:
                for msg_dict in msg_list:
                    try:
                        if msg_dict['MsgType'] == 2:
                            with app.app_context():
                                model.save_contact(msg_dict)
                        elif msg_dict['Status'] is not None:
                            try:
                                action_rule.filter_keyword_rule(v_user.userame, msg_dict)
                            except Exception as e:
                                print(e)
                            with app.app_context():
                                model.save_message(msg_dict)
                        else:
                            print(msg_dict)
                    except Exception as e:
                        print(e)
                        print(msg_dict)
                self.async_check(v_user, new_socket=new_socket)
            else:
                print "sync 完成"

    def new_init(self, v_user):
        """
        登陆初始化
        :param v_user: 
        :return: 
        """
        with app.app_context():
            bot_param = model.BotParam.query.filter_by(Username=v_user.userame).first()
            if bot_param:
                self.long_host = bot_param.LongHost
                self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)
        new_init_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=1002,
                user=v_user
            )
        )
        new_init_rsp = grpc_client.send(new_init_req)
        (buffers, seq) = grpc_utils.get_seq_buffer(new_init_rsp)
        buffers = self.wechat_client.sync_send_and_return(buffers, time_out=3)
        if not check_buffer_16_is_191(buffers):
            print("未知包 init")
            self.wechat_client.close_when_done()
            return False
        else:
            new_init_rsp.baseMsg.cmd = -1002
            new_init_rsp.baseMsg.payloads = char_to_str(buffers)
            new_init_rsp = grpc_client.send(new_init_rsp)
            # 打印出同步消息的结构体
            msg_list = json.loads(new_init_rsp.baseMsg.payloads)
            if msg_list is not None:
                for msg_dict in msg_list:
                    # save msg
                    # print(msg_dict)
                    if msg_dict['MsgType'] == 2:
                        with app.app_context():
                            model.save_contact(msg_dict)
                    else:
                        print(msg_dict)
            v_user = new_init_rsp.baseMsg.user
            v_user_pickle = pickle.dumps(v_user)
            red.set('v_user_' + v_user.userame, v_user_pickle)
            if new_init_rsp.baseMsg.ret == 8888:
                print("同步完成")
                self.wechat_client.close_when_done()
            else:
                self.wechat_client.close_when_done()
                self.new_init(v_user)
            return True

    def send_text_msg(self, user_name, content, v_user):
        """
        参考btn_SendMsg_Click
        :param user_name: 
        :param content: 
        :param at_user_list: 
        :param v_user: 
        :return: 
        """
        with app.app_context():
            bot_param = model.BotParam.query.filter_by(Username=v_user.userame).first()
            if bot_param:
                self.long_host = bot_param.LongHost
                self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)
        payLoadJson = "{\"ToUserName\":\"" + user_name + "\",\"Content\":\"" + content + "\",\"Type\":0,\"MsgSource\":\"\"}"
        send_text_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=522,
                user=v_user,
                payloads=payLoadJson.encode('utf-8')
            )
        )
        send_text_rsp = grpc_client.send(send_text_req)

        (buffers, seq) = grpc_utils.get_seq_buffer(send_text_rsp)
        import binascii
        print(binascii.b2a_hex(buffers))
        buffers = self.wechat_client.sync_send_and_return(buffers)
        if not check_buffer_16_is_191(buffers):
            if read_int(buffers, 18) == -13:
                print("Session Time out 离线或用户取消登陆 需执行二次登录")
            return False
        self.wechat_client.close_when_done()
        return True

    def send_voice_msg(self, v_user, to_user_name, url):
        """
        发送语音 btn_SendVoice_Click
        :param v_user: 
        :param url: 
        :return: 
        """
        with app.app_context():
            bot_param = model.BotParam.query.filter_by(Username=v_user.userame).first()
            if bot_param:
                self.long_host = bot_param.LongHost
                self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)
        voice_path = 'img/test.mp3'
        with open(voice_path, 'rb') as voice_file:
            data = voice_file.read()
        payload = {
            'ToUserName': to_user_name,
            'Offset': 0,
            'Length': len(data),
            'EndFlag': 1,
            'Data': data,
            'VoiceFormat': 0
        }
        payload_json = json.dumps(payload)
        send_voice_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=127,
                user=v_user,
                payloads=payload_json.encode('utf-8')
            )
        )
        send_voice_rsp = grpc_client.send(send_voice_req)
        (buffers, seq) = grpc_utils.get_seq_buffer(send_voice_rsp)
        buffers = self.wechat_client.sync_send_and_return(buffers)
        self.wechat_client.close_when_done()
        return check_buffer_16_is_191(buffers)

    def send_img_msg(self, user_name, v_user, url):
        """
        btn_SendMsgimg_Click
        :param user_name: 
        :param v_user: 
        :return: 
        """
        with app.app_context():
            bot_param = model.BotParam.query.filter_by(Username=v_user.userame).first()
            if bot_param:
                self.long_host = bot_param.LongHost
                self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)
        data = urllib2.urlopen(url).read()
        # img_path = 'img/no.png'
        # with codecs.open(img_path, 'rb') as img_file:
        #     data = img_file.read()
        # with open(img_path, 'rb') as img_file:
        #     data = img_file.read()
        # 起始位置
        start_pos = 0
        # 数据分块长度
        data_len = 16535
        # 总长度
        data_total_length = len(data)
        print('preparing sent img length length {}'.format(data_total_length))
        # 客户图像id
        client_img_id = v_user.userame + "_" + str(get_time_stamp())
        while start_pos != data_total_length:
            # 每次最多只传65535
            count = 0
            if data_total_length - start_pos > data_len:
                count = data_len
            else:
                count = data_total_length - start_pos
            upload_data = base64.b64encode(data[start_pos:start_pos + count])

            payLoadJson = {
                'ClientImgId': client_img_id.encode('utf-8'),
                'ToUserName': user_name.encode('utf-8'),
                'StartPos': start_pos,
                'TotalLen': data_total_length,
                'DataLen': len(data[start_pos:start_pos + count]),
                'Data': upload_data
            }
            pay_load_json = json.dumps(payLoadJson)
            start_pos = start_pos + count
            print("Send Img Block {}".format(count))
            print("start_pos is {}".format(start_pos))
            print("data_total_length is {}".format(data_total_length))
            img_msg_req = WechatMsg(
                token=CONST_PROTOCOL_DICT['machine_code'],
                version=CONST_PROTOCOL_DICT['version'],
                timeStamp=get_time_stamp(),
                iP=get_public_ip(),
                baseMsg=BaseMsg(
                    cmd=110,
                    user=v_user,
                    payloads=pay_load_json.encode('utf-8'),
                )
            )

            img_msg_rsp = grpc_client.send(img_msg_req)
            (buffers, seq) = grpc_utils.get_seq_buffer(img_msg_rsp)
            buffers = self.wechat_client.sync_send_and_return(buffers, time_out=3)
            check_buffer_16_is_191(buffers)
        self.wechat_client.close_when_done()
        return True

    def search_contact(self, user_name, v_user):
        payLoadJson = "{\"Username\":\"" + user_name + "\"}"
        search_contact_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=106,
                user=v_user,
                payloads=payLoadJson.encode('utf-8')
            )
        )
        search_contact_rsp = grpc_client.send(search_contact_req)
        (buffers, seq) = grpc_utils.get_seq_buffer(search_contact_rsp)
        buffers = self.wechat_client.sync_send_and_return(buffers)
        check_buffer_16_is_191(buffers)
        search_contact_rsp.baseMsg.cmd = -106
        search_contact_rsp.baseMsg.payloads = char_to_str(buffers)
        payloads = grpc_client.send(search_contact_rsp)
        print(payloads)

    def get_chatroom_detail(self, v_user, room_id):
        """
        获取群的信息
        :param room_id: 
        :param v_user: 
        :return: 
        """
        with app.app_context():
            bot_param = model.BotParam.query.filter_by(Username=v_user.userame).first()
            if bot_param:
                self.short_host = bot_param.ShortHost
        pay_load_json = "{\"Chatroom\":\"" + room_id + "\"}"
        get_room_detail_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=551,
                user=v_user,
                payloads=pay_load_json.encode('utf-8')
            )
        )
        get_room_detail_rsp = grpc_client.send(get_room_detail_req)
        # (buffers, seq) = grpc_utils.get_seq_buffer(get_room_detail_rsp)
        body = get_room_detail_rsp.baseMsg.payloads

        buffers = requests.post("http://" + self.short_host + get_room_detail_rsp.baseMsg.cmdUrl, body)

        get_room_detail_rsp.baseMsg.cmd = -551
        get_room_detail_rsp.baseMsg.payloads = buffers.content
        get_room_detail_rsp = grpc_client.send(get_room_detail_rsp)
        buffers = get_room_detail_rsp.baseMsg.payloads
        print buffers.encode('utf-8')

    def get_contact(self, v_user, wx_id_list):
        """
        TODO 根据联系人wxid，获取contact
        private void btn_GetContact_Click(object sender, EventArgs e)
        :param wx_id_list: 
        :param v_user: 
        :return: 
        """
        payLoadJson = "{\"UserNameList\":\"" + wx_id_list + "\"}"

        contacts_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=182,
                user=v_user,
                payloads=payLoadJson
            )
        )
        get_contacts_rsp = grpc_client.send(contacts_req)

        (buffers, seq) = grpc_utils.get_seq_buffer(get_contacts_rsp)
        buffers = self.wechat_client.sync_send_and_return(buffers)

        if not check_buffer_16_is_191(buffers):
            print("未知包 init")
        else:
            get_contacts_rsp.baseMsg.cmd = -182
            get_contacts_rsp.baseMsg.payloads = char_to_str(buffers)
            get_contacts_rsp = grpc_client.send(get_contacts_rsp)

        print(get_contacts_rsp.baseMsg.payloads)
        print('获取联系人成功')

    def create_chatroom(self, v_user, wx_id_list):
        """
        建群        private void btn_CreateChatRoom_Click(object sender, EventArgs e)
        :param v_user: 
        :param wx_id_list: 
        :return: 
        """
        with app.app_context():
            bot_param = model.BotParam.query.filter_by(Username=v_user.userame).first()
            if bot_param:
                self.long_host = bot_param.LongHost
                self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)
        payload_json = "{\"Membernames\":\"" + wx_id_list + "\"}"
        create_chatroom_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=119,
                user=v_user,
                payloads=payload_json.encode('utf-8')
            )
        )
        create_chatroom_rsp = grpc_client.send(create_chatroom_req)
        (buffers, seq) = grpc_utils.get_seq_buffer(create_chatroom_rsp)
        buffers = self.wechat_client.sync_send_and_return(buffers)
        check_buffer_16_is_191(buffers)
        create_chatroom_rsp.baseMsg.cmd = -119
        create_chatroom_rsp.baseMsg.payloads = char_to_str(buffers)
        payloads = grpc_client.send(create_chatroom_rsp)
        chatroom_detail = json.loads(payloads.baseMsg.payloads)
        chatroom_id = chatroom_detail['Roomeid']
        print('新建的群id是{}'.format(chatroom_id))
        self.send_text_msg(chatroom_id, "欢迎进群", v_user)

    def modify_chatroom_name(self, v_user, chatroom_id, room_name):
        with app.app_context():
            bot_param = model.BotParam.query.filter_by(Username=v_user.userame).first()
            if bot_param:
                self.short_host = bot_param.ShortHost
        payload_json = "{\"Cmdid\":27,\"ChatRoom\":\"" + chatroom_id + "\",\"Roomname\":\"" + room_name + "\"}"
        modify_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=681,
                user=v_user,
                payloads=payload_json.encode('utf-8')
            )
        )
        modify_rsp = grpc_client.send(modify_req)
        (buffers, seq) = grpc_utils.get_seq_buffer(modify_rsp)
        buffers = requests.post("http://" + self.short_host + modify_rsp.baseMsg.cmdUrl, data=buffers)
        self.wechat_client.close_when_done()
        return check_buffer_16_is_191(buffers)

    def invite_chatroom(self, v_user, chatroom_id, wx_id):
        """
        邀请进群:
        向指定用户发送群名片进行邀请
        :param v_user: 
        :param chatroom_id: 
        :param wx_id: 
        :return: 
        """
        with app.app_context():
            bot_param = model.BotParam.query.filter_by(Username=v_user.userame).first()
            if bot_param:
                self.short_host = bot_param.ShortHost
        payloadJson = "{\"ChatRoom\":\"" + chatroom_id + "\",\"Username\":\"" + wx_id + "\"}"
        req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=610,
                user=v_user,
                payloads=payloadJson.encode('utf-8')
            )
        )
        rsp = grpc_client.send(req)
        (buffers, seq) = grpc_utils.get_seq_buffer(rsp)
        buffers = requests.post("http://" + self.short_host + rsp.baseMsg.cmdUrl, data=buffers)

        # 似乎每次登陆后的返回都不一样
        if not ord(buffers.text[0]) == 191:
            print "invite_chatroom_member 返回码{0}".format(ord(buffers.text[0]))
        return True

    def add_chatroom_member(self, v_user, chatroom_id, wx_id):
        """
        添加微信群成员为好友 btn_AddChatRoomMember_Click
        :param v_user: 
        :param wxid: 
        :return: 
        """
        with app.app_context():
            bot_param = model.BotParam.query.filter_by(Username=v_user.userame).first()
            if bot_param:
                self.long_host = bot_param.LongHost
                self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)
        payloadJson = "{\"Roomeid\":\"" + chatroom_id + "\",\"Membernames\":\"" + wx_id + "\"}"
        req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=120,
                user=v_user,
                payloads=payloadJson.encode('utf-8')
            )
        )

        rsp = grpc_client.send(req)
        (buffers, seq) = grpc_utils.get_seq_buffer(rsp)
        buffers = self.wechat_client.sync_send_and_return(buffers)
        check_buffer_16_is_191(buffers)
        rsp.baseMsg.cmd = -120
        rsp.baseMsg.payloads = char_to_str(buffers)
        payloads = grpc_client.send(rsp)

    def delete_chatroom_member(self, v_user, chatroom_id, wx_id):
        """
        踢出微信群 btn_DelChatRoomUser_Click
        :param v_user: 
        :param wxid: 
        :return: 
        """
        with app.app_context():
            bot_param = model.BotParam.query.filter_by(Username=v_user.userame).first()
            if bot_param:
                self.short_host = bot_param.ShortHost

        payloadJson = "{\"ChatRoom\":\"" + chatroom_id + "\",\"Username\":\"" + wx_id + "\"}"
        req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=179,
                user=v_user,
                payloads=payloadJson.encode('utf-8')
            )
        )

        rsp = grpc_client.send(req)
        (buffers, seq) = grpc_utils.get_seq_buffer(rsp)
        buffers = requests.post("http://" + self.short_host + rsp.baseMsg.cmdUrl, buffers)
        # 检测buffers[0] == 191
        if not ord(buffers.text.encode('utf-8')[0]):
            print "delete_chatroom_member 未知包"
            return False
        else:
            return True

    def decode_cmd_318(self, v_user, data):
        with app.app_context():
            bot_param = model.BotParam.query.filter_by(Username=v_user.userame).first()
            if bot_param:
                self.short_host = bot_param.ShortHost
                self.long_host = bot_param.LongHost
                self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)

        # send notify_req
        notify_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=-318,
                user=v_user,
                payloads=data
            )
        )
        notify_rsp = grpc_client.send(notify_req)
        body = notify_rsp.baseMsg.payloads.encode('utf-8')
        add_msg_digest = json.loads(body)
        print add_msg_digest
        payload_dict = {
            "ChatroomId": add_msg_digest['ChatRoomId'],
            "MsgSeq": add_msg_digest['NewMsgSeq']
        }
        payload_dict_json = json.dumps(payload_dict)

        # get chatroom req
        get_chatroom_msg_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=805,
                user=v_user,
                payloads=payload_dict_json.encode('utf-8')
            )
        )
        get_chatroom_msg_rsp = grpc_client.send(get_chatroom_msg_req)
        body = get_chatroom_msg_rsp.baseMsg.payloads
        upload_url = get_chatroom_msg_rsp.baseMsg.cmdUrl
        buffers = requests.post("http://" + self.short_host + upload_url, data=body)
        print buffers.text

        if buffers is None or buffers.text.encode('utf-8')[0] == 191:
            # TODO:hextostr
            print ("unknown package:{0}".format(buffers))
            return False

        # send grpc and decode again
        get_chatroom_msg_rsp.baseMsg.cmd = -805
        get_chatroom_msg_rsp.baseMsg.payloads = buffers.text.encode('utf-8')
        get_chatroom_msg_rsp = grpc_client.send(get_chatroom_msg_rsp)
        buffers = get_chatroom_msg_rsp.baseMsg.payloads
        print buffers
        return True

    def sns_post(self, v_user, xml):
        """
        TODO 发送朋友圈 btn_SnsPost_Click
        :param v_user:
        :return: 
        """
        with app.app_context():
            bot_param = model.BotParam.query.filter_by(Username=v_user.userame).first()
            if bot_param:
                self.long_host = bot_param.LongHost
                self.short_host = bot_param.ShortHost
                self.wechat_client = WechatClient.WechatClient(self.long_host, 80, True)
        pay_load = "{\"Content\":\"" + xml + "\"}"
        sns_post_req = WechatMsg(
            token=CONST_PROTOCOL_DICT['machine_code'],
            version=CONST_PROTOCOL_DICT['version'],
            timeStamp=get_time_stamp(),
            iP=get_public_ip(),
            baseMsg=BaseMsg(
                cmd=209,
                user=v_user,
                payloads=pay_load.encode('utf-8')
            )
        )

        sns_post_rsp = grpc_client.send(sns_post_req)
        (buffers, seq) = grpc_utils.get_seq_buffer(sns_post_rsp)
        buffers = self.wechat_client.sync_send_and_return(buffers)
        if not self.wechat_client.check_buffer_16_is_191(buffers):
            print "sns post 未知包"
            return False
        else:
            return True

    def check_and_confirm_and_load(self, qrcode_rsp, device_id):
        qr_code = self.check_qrcode_login(qrcode_rsp, device_id)
        if qr_code is not False:
            if self.confirm_qrcode_login(qr_code, keep_heart_beat=False):
                v_user_pickle = red.get('v_user_' + str(qr_code['Username']))
                v_user = pickle.loads(v_user_pickle)
                if self.new_init(v_user):
                    v_user = pickle.loads(red.get('v_user_' + str(qr_code['Username'])))
                    self.async_check(v_user)
                    from taobaoke.heartbeat_manager import HeartBeatManager
                    HeartBeatManager.begin_heartbeat(str(qr_code['Username']))

    def login(self, md_username):
        (oss_path, qrcode_rsp, device_id) = self.get_qrcode(md_username)
        self.check_and_confirm_and_load(qrcode_rsp, device_id)

    def try_send_message(self, username):
        v_user_pickle = red.get('v_user_' + username)
        v_user = pickle.loads(v_user_pickle)
        # self.send_text_msg(u"7784635084@chatroom", u"咚咚咚 现在是12点咯 我是你们的老公彭于晏 大家吃了吗", v_user)
        self.send_text_msg(u"zhengyaohong0724", u"11111", v_user)
        # self.send_text_msg(u"6670703819@chatroom", u"。", v_user)

    def try_new_init(self, username):
        v_user_pickle = red.get('v_user_' + username)
        v_user = pickle.loads(v_user_pickle)
        # v_user = self.auto_auth(v_user, 'Q-z_hUogcAFKCP8rWgdF', '')
        self.new_init(v_user)

    def try_get_new_message(self, username):
        v_user_pickle = red.get('v_user_' + username)
        v_user = pickle.loads(v_user_pickle)
        self.async_check(v_user)
        return True

    def try_heart_beat(self, username):
        v_user_pickle = red.get('v_user_' + username)
        v_user = pickle.loads(v_user_pickle)
        return self.heart_beat(v_user)

    def try_re_login(self, username):
        v_user_pickle = red.get('v_user_' + username)
        v_user = pickle.loads(v_user_pickle)
        self.auto_auth(v_user, 'Q-z_hUogcAFKCP8rWgdF', '')

    def try_search_contact(self, username):
        v_user_pickle = red.get('v_user_' + username)
        v_user = pickle.loads(v_user_pickle)
        self.search_contact("zhengyaohong0724", v_user)

    def try_room_detail(self, username, roomid):
        v_user_pickle = red.get('v_user_' + username)
        v_user = pickle.loads(v_user_pickle)
        self.get_chatroom_detail(v_user, roomid)

    def try_sleep_send(self, time_delay, user_name, content, v_user):
        time.sleep(time_delay)
        self.send_text_msg(user_name, content, v_user)


if __name__ == "__main__":
    # login()
    wx_bot = WXBot()
    # wx_bot.login('15900000010')

    while True:
        try:
            # wx_user = "wxid_ceapoyxs555k22"
            wx_user = "wxid_fh235f4nylp22"  # 小小
            # wx_user = "wxid_kj1papird5kn22"
            # wx_user = "wxid_3cimlsancyfg22"  # 点金
            # wxid_sygscg13nr0g21
            # wx_user = "wxid_5wrnusfmt26932"
            # wxid_mynvgzqgnb5x22
            # wx_user = "wxid_sygscg13nr0g21"
            print "**************************"
            print "enter cmd :{}".format(wx_user)
            print "**************************"
            cmd = input()
            if cmd == 0:
                wx_bot.set_user_context(wx_user)

                v_user_pickle = red.get('v_user_' + wx_user)
                v_user = pickle.loads(v_user_pickle)
                UUid = u"667D18B1-BCE3-4AA2-8ED1-1FDC19446567"
                DeviceType = u"<k21>TP_lINKS_5G</k21><k22>中国移动</k22><k24>c1:cd:2d:1c:5b:11</k24>"
                wx_bot.auto_auth(v_user, UUid, DeviceType, False)

            elif cmd == 1:
                # wxid_ceapoyxs555k22
                v_user_pickle = red.get('v_user_' + wx_user)
                # v_user_pickle = red.get('v_user_' + 'wxid_3cimlsancyfg22')
                v_user = pickle.loads(v_user_pickle)
                # wx_bot.send_text_msg('fat-phone', '112233', v_user)
                wx_bot.send_text_msg('8043482794@chatroom', '112233', v_user)

            elif cmd == 2:
                v_user_pickle = red.get('v_user_' + wx_user)
                # v_user_pickle = red.get('v_user_' + 'wxid_3cimlsancyfg22')
                v_user = pickle.loads(v_user_pickle)
                wx_bot.send_img_msg('fat-phone', v_user,
                                    "http://imgsrc.baidu.com/forum/w%3d580/sign=92e50f14c2cec3fd8b3ea77de68ad4b6/dd92b1fd5266d01622d36cf0962bd40737fa35ed.jpg")

            elif cmd == 3:
                v_user_pickle = red.get('v_user_' + wx_user)
                # v_user_pickle = red.get('v_user_' + 'wxid_3cimlsancyfg22')
                v_user = pickle.loads(v_user_pickle)
                wx_bot.async_check(v_user, False)

            elif cmd == 4:
                v_user_pickle = red.get('v_user_' + wx_user)
                # v_user_pickle = red.get('v_user_' + 'wxid_3cimlsancyfg22')
                v_user = pickle.loads(v_user_pickle)
                wx_bot.heart_beat(v_user)
                # break

            elif cmd == 5:
                wx_bot.login('15900000010')

            elif cmd == 6:
                v_user = pickle.loads(red.get('v_user_' + wx_user))
                # # wx_bot.invite_chatroom(v_user, '8043482794@chatroom', 'wxid_e1kvkvgi873521')
                wx_bot.get_chatroom_detail(v_user, '8043482794@chatroom')
                print "socket status:{0}".format(wx_bot.wechat_client.connected)

        except Exception as e:
            print e.message