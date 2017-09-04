# coding:utf8
import requests
from taobaoke import app
from taobaoke.database import model


def filter_keyword_rule(wx_id, msg_dict):
    # http://s-prod-04.qunzhu666.com:8000/search-product-pad?username=15900000010&keyword=鞋子&gid=7682741189@chatroom
    # http://s-prod-04.qunzhu666.com:8000/interact/search-product-pad/?username=wxid_3cimlsancyfg22&keyword=%E9%9E%8B%E5%AD%90&gid=6362478985@chatroom
    # 条件1 文字符合要求
    keyword = find_buy_start(msg_dict['Content'])
    if keyword and keyword is not '':
        # FromUserName 跟 ToUserName 是相对机器人来说的
        # 机器人在群里说话，FromUserName是机器人的wx_id，ToUserName是gid
        # 但其他人在群里说话，ToUserName是机器人的wx_id，FromUserName是gid
        # 群是淘宝客群，找XX才生效
        is_taobao_group = False
        gid = ''
        # 情况分类1 机器人自己说找XX
        if msg_dict['FromUserName'] == wx_id and "@chatroom" in msg_dict['ToUserName']:
            gid = msg_dict['ToUserName']
            is_taobao_group = True
        # 情况分类2 群成员说找XX
        elif "@chatroom" in msg_dict['FromUserName'] and msg_dict['ToUserName'] == wx_id:
            gid = msg_dict['FromUserName']
            is_taobao_group = True
        # gid名称是福利社
        with app.app_context():
            contact_db = model.Contact.query.filter(model.Contact.NickName.contains("福利社"),
                                                    model.Contact.UserName == gid).first()
        gid_name_is = contact_db is not None
        if is_taobao_group and gid_name_is:
            # 根据id找到username
            with app.app_context():
                qrcode_db = model.Qrcode.query.filter_by(Username=wx_id).first()
                username = qrcode_db.md_username
                print("username={}&keyword={}&gid={}".format(username, keyword, gid))
                url = "http://s-prod-04.qunzhu666.com:8000/interact/search-product-pad/?username={}&keyword={}&gid={}&uin={}".format(username, keyword, gid, wx_id)
                rsp = requests.get(url)
                print(rsp.text)


def find_buy_start(s):
    # 一个中文字符等于三个字节 允许有十个字符
    if len(s) < 40:
        lst = s.split("找")
        if len(lst) > 1:
            return lst[1]
        lst = s.split("买")
        if len(lst) > 1:
            return lst[1]
    return False


if __name__ == "__main__":
    print(find_buy_start("我要找拖鞋找拖鞋1"))
    print(find_buy_start("我要找拖鞋"))
    print(find_buy_start("我要买拖鞋"))
