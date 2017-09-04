# coding:utf-8
"""
美男报时
"""
from taobaoke.weixin_bot import WXBot
import time
from taobaoke.settings import red
import cPickle as pickle
from taobaoke.database import model
import random
while True:
    img_db = model.Img.query.all()[random.randint(0, 5)]

    # 时间 整点
    now_hour_min = time.strftime('%H:%M', time.localtime(time.time()))
    # 文案
    wen_an = "我是你们的老公彭于晏 现在是{} 么么哒".format(now_hour_min)
    # 点金圣手
    wx_id = 'wxid_3cimlsancyfg22'
    chat_room_id = '6362478985@chatroom'

    bot = WXBot()
    v_user_pickle = red.get('v_user_' + wx_id)
    v_user = pickle.loads(v_user_pickle)
    bot.send_text_msg(chat_room_id, wen_an, v_user)
    bot.send_img_msg(chat_room_id, v_user, img_db.url)
    time.sleep(60*5)


# url = 'http://img1.imgtn.bdimg.com/it/u=2174737423,1287229426&fm=214&gp=0.jpg'
# 7784635084@chatroom
# qr_img = open('img/qrcode.png', 'wb')
# qr_img.write(imgData)
# qr_img.close()
#
# time.sleep(1)
# img = Image.open('qrcode.png')
# img.show()