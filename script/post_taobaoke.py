# coding:utf-8
"""
淘宝客推送脚本
"""
import sys
# 脚本加入搜索路径 现在是hard code状态 看看有没有办法改
sys.path.append('/Users/hong/sourcecode/work/ipad_wechat_test/wx_pad_taobaoke')
sys.path.append('/home/ipad_wechat_test/wx_pad_taobaoke')
print(sys.path)
import requests
import json
from taobaoke.database import model
import time
from taobaoke import app


def post_taobaoke_url(gid, hid, username):
    # 发单人的wx_id, 群的id, 手机号
    data = {'gid': gid, 'hid': hid, 'username': username,
            'begin_time': '07:00',
            'end_time': '23:00'}
    data = json.dumps(data)
    # response = requests.post('http://s-prod-04.qunzhu666.com:8000/interact/push-product/', data=data)
    try:
        response = requests.post('http://s-prod-04.qunzhu666.com:8000/interact/push-product/', data=data)
        print(response.text)
    except Exception as e:
        print(e)


def select():
    with app.app_context():
        # 筛选出已经登录的User
        user_list = model.User.query.filter(model.User.login > 0).all()
        print([user.userame for user in user_list])
        for user in user_list:
            print("handling wxid {}, time {}".format(user.userame, time.time()))
            # 发单机器人id
            hid = user.userame
            # 通过 wx_id = hid 筛选出手机号
            qr_code_db = model.Qrcode.query.filter_by(Username=user.userame).all()
            for qr_code in qr_code_db:
                if qr_code.md_username is not None:
                    md_username = qr_code.md_username
                    break
            # 询问当前时间此用户是否需要推送
            rsp = requests.get("http://s-prod-07.qunzhu666.com:8000/api/tk/is-push?username={0}&wx_id={1}".format(md_username, hid), timeout=4)
            ret = json.loads(rsp.text)['ret']
            if ret == 1:
                # 筛选出激活群
                message_list = model.Message.query.filter(model.Message.Content == "激活",
                                                          model.Message.FromUserName == user.userame).all()
                group_set = set([message.ToUserName for message in message_list])
                for group in group_set:
                    # 发单人的wx_id, 群的id, 手机号
                    try:
                        contact_db = model.Contact.query.filter(model.Contact.NickName.contains("福利社"),
                                                                model.Contact.UserName == group).first()
                        if contact_db is not None:
                            print('昵称 {}, time {}'.format(contact_db.NickName, time.time()))
                            post_taobaoke_url(group, hid, md_username)
                    except Exception as e:
                        print(e)

if __name__ == "__main__":
    while True:
        user_list = model.User.query.filter(model.User.login > 0).all()
        user_len = len([user.userame for user in user_list])
        try:
            now_hour = int(time.strftime('%H', time.localtime(time.time())))
            if 7 <= now_hour <= 22:
                select()
            else:
                # 如果不在这个时间段 休眠长一点
                time.sleep(20 * 60)
        except Exception as e:
            print(e)

        time.sleep(60)
        # if 5 * 60 - 6 * user_len > 0:
        #     time.sleep(5 * 60 - 6 * user_len)
# msg1 = {
#     'type': 'img',
#     'content': p.get_img_msg(),
#     'host_id': '58cfde0f498fad001bed0af2',
#     'target_id': '58facc29cae2280020ca49a8',
# }
# msg2 = {
#     'type': 'text',
#     'content': p.get_text_msg(pid=pid),
#     'host_id': '58cfde0f498fad001bed0af2',
#     'target_id': '58facc29cae2280020ca49a8',
# }

# 推送商品
# 筛选出哪些机器人登陆了
# 筛选出哪些群需要发送
# import MySQLdb

# conn = MySQLdb.connect(
#     host='localhost',
#     port=3306,
#     user='root',
#     passwd='123456',
#     db='test',
# )
#
# cur = conn.cursor()
# for user in user_name_list:
#     group_id group_id
#     host_id uin
#     requests.post()

# requests.post('192.168.123.65:8000', data={'group_id': 'GID', 'host_id': 'HID', 'username': '15900000010'})
# import datetime

# now = datetime.datetime.now()
# delta = datetime.timedelta(hours=24)
# before = now - delta
# after = now + delta
