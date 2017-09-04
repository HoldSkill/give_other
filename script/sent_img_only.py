# coding:utf-8
import pickle
import sys
import requests
from random import random
# 脚本加入搜索路径 现在是hard code状态 看看有没有办法改
sys.path.append('/Users/hong/sourcecode/work/ipad_wechat_test/wx_pad_taobaoke')
sys.path.append('/home/ipad_wechat_test/wx_pad_taobaoke')
from taobaoke.weixin_bot import WXBot
from taobaoke.settings import red
import time
import MySQLdb
import random
bot = WXBot()


def get_img_url():
    try:
        db = MySQLdb.connect(
            host='s_prod_02.shequn365.com',
            port=50001,
            user='root',
            passwd='Xiaozuanfeng',
            db='taobaoke',
        )
        url = ''
        cursor = db.cursor()
        sql = "SELECT img_url from broadcast_product WHERE entry_ptr_id={}"
        cursor.execute(sql.format(random.randint(10000, 40000)))
        ret = cursor.fetchall()
        url = ret[0][0]
    except Exception as e:
        print(e)
    finally:
        db.close()
        return url.replace('w_600', 'w_400')

while True:
    try:
        v_user_pickle = red.get('v_user_' + 'wxid_y3prhve9avxk22')
        v_user = pickle.loads(v_user_pickle)
        bot.send_img_msg(u"8043482794@chatroom", v_user, get_img_url())
    except Exception as e:
        print(e)
    finally:
        time.sleep(300)