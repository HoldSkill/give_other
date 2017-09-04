# _*_ coding:utf-8 _*_
import pickle

from taobaoke import weixin_bot
from taobaoke.database import model
from taobaoke import app
from taobaoke.settings import red
from taobaoke.utils import common_utils

import time
import threading

from taobaoke.utils import oss_utils


class HeartBeatManager(object):
    heartbeat_thread_dict = {}

    def __init__(self):
        pass

    def run(self):
        t = threading.Thread(target=self.__start_thread_pool)
        t.setDaemon(True)
        t.start()

    @staticmethod
    def __print_log(msg, title='heart_beat'):
        print '[{}]'.format(title) + msg

    @staticmethod
    def begin_heartbeat(vx_username):
        if vx_username in HeartBeatManager.heartbeat_thread_dict.keys():
            t = HeartBeatManager.heartbeat_thread_dict[vx_username]
            if t.isAlive():
                return

        t = threading.Thread(target=HeartBeatManager.heartbeat, name=vx_username, args=(vx_username,))
        HeartBeatManager.heartbeat_thread_dict[vx_username] = t
        t.setDaemon(True)
        t.start()

    def __start_thread_pool(self):
        with app.app_context():
            online_user_list = model.User.query.filter(model.User.login > 0).all()
            print([user.userame for user in online_user_list])
            for user in online_user_list:
                HeartBeatManager.begin_heartbeat(user.userame)
        # # test
        # with app.app_context():
        #     online_user_list = ["wxid_3cimlsancyfg22", "wxid_fh235f4nylp22", 'wxid_q093pm99ez4k12', 'wxid_mynvgzqgnb5x22']
        #     # online_user_list = ['wxid_mynvgzqgnb5x22']
        #     print(online_user_list)
        #     for username in online_user_list:
        #         HeartBeatManager.begin_heartbeat(username)

    def __detect_thread_pool(self):
        # TODO:定时检测线程是否异常
        pass

    @classmethod
    def heartbeat(cls, wx_username):
        is_first = True
        wx_bot = weixin_bot.WXBot()
        wx_bot.set_user_context(wx_username)
        wx_bot.open_notify_callback()
        # 微信有新消息就会往socket推20字节的notify包
        # 防止该socket断开，每30秒发一次同步消息包
        while True:
            try:
                with app.app_context():
                    user = model.User.query.filter_by(userame=wx_username).first()
                    if user is not None:
                        # 用户退出登陆,退出线程
                        if user.login == 0:
                            cls.__print_log("[{0}:{1}]user logout,heartbeat thread exit".format(user.userame, user.nickname))
                            # 登出时需要把socket断开，否则会一直收到退出登陆的消息
                            wx_bot.wechat_client.close_when_done()
                            return

                if not wx_bot.wechat_client.connected:
                    # 测试过后发现好像没有哪个包能阻止socket断开，断开只是时间问题
                    # 检测一下socket有没断开，如果断开，重新起一个socket即可
                    # oss_utils.beary_chat("{} heart_beat socket 断开, 准备重新链接".format(wx_username), user='fatphone777')
                    cls.__print_log("{0} socket state:{1}".format(wx_username, wx_bot.wechat_client.connected))

                    wx_bot.wechat_client.close_when_done()

                    # 再一次初始化
                    is_first = True
                    wx_bot = weixin_bot.WXBot()
                    wx_bot.set_user_context(wx_username)
                    wx_bot.open_notify_callback()

                v_user = pickle.loads(red.get('v_user_' + wx_username))
                if is_first:
                    UUid = u"667D18B1-BCE3-4AA2-8ED1-1FDC19446567"
                    DeviceType = u"<k21>TP_lINKS_5G</k21><k22>中国移动</k22><k24>c1:cd:2d:1c:5b:11</k24>"
                    if wx_bot.auto_auth(v_user, UUid, DeviceType, False):
                        # oss_utils.beary_chat("{} auto_auth success in heartbeat".format(wx_username),
                        #                    user='fatphone777')
                        cls.__print_log("{} auto_auth success in heartbeat".format(wx_username))
                    else:
                        oss_utils.beary_chat("{} auto_auth failed in heartbeat".format(wx_username),
                                           user='fatphone777')
                        cls.__print_log("{} auto_auth failed in heartbeat, thread exit".format(wx_username))
                        wx_bot.logout_bot(v_user)
                    is_first = False

                # c# demo 中的heart_beat包，能延长socket的持续时间
                # 但始终会断开
                wx_bot.heart_beat(v_user)

                # print "{} heart best finished".format(wx_username)
                time.sleep(30)
            except Exception as e:
                print "[{0}]heartbeat exception:{1}".format(wx_username, e.message)
                continue

