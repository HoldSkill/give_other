# coding:utf-8
from taobaoke import db
import requests
import json


class Img(db.Model):
    __tablename__ = 'img'
    __table_args__ = {"useexisting": True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    url = db.Column(db.String(400), unique=True)
    type = db.Column(db.String(20))

    def __init__(self, name, url, type):
        self.name = name
        self.url = url
        self.type = type


class Contact(db.Model):
    __tablename__ = 'contact'
    __table_args__ = {"useexisting": True}
    id = db.Column(db.Integer, primary_key=True)
    MsgType = db.Column(db.String(200))
    UserName = db.Column(db.String(400), unique=True)
    NickName = db.Column(db.String(200))
    Signature = db.Column(db.String(200))
    SmallHeadImgUrl = db.Column(db.String(200))
    BigHeadImgUrl = db.Column(db.String(200))
    Province = db.Column(db.String(200))
    City = db.Column(db.String(200))
    Remark = db.Column(db.String(200))
    Alias = db.Column(db.String(200))
    Sex = db.Column(db.String(200))
    ContactType = db.Column(db.String(200))
    ChatRoomOwner = db.Column(db.String(200))
    ExtInfo = db.Column(db.String(10000))
    Ticket = db.Column(db.String(200))
    ChatroomVersion = db.Column(db.String(200))

    def __init__(self, MsgType, UserName, NickName, Signature, SmallHeadImgUrl, BigHeadImgUrl, Province, City, Remark,
                 Alias, Sex, ContactType, ChatRoomOwner, ExtInfo, Ticket, ChatroomVersion):
        # 这些字段 是登陆成功后的返回
        self.MsgType = MsgType
        self.UserName = UserName
        self.NickName = NickName
        self.Signature = Signature
        self.SmallHeadImgUrl = SmallHeadImgUrl
        self.BigHeadImgUrl = BigHeadImgUrl
        self.Province = Province
        self.City = City
        self.Remark = Remark
        self.Alias = Alias
        self.Sex = Sex
        self.ContactType = ContactType
        self.ChatRoomOwner = ChatRoomOwner
        self.ExtInfo = ExtInfo
        self.Ticket = Ticket
        self.ChatroomVersion = ChatroomVersion


class Qrcode(db.Model):
    __tablename__ = 'qrcode'
    __table_args__ = {"useexisting": True}

    id = db.Column(db.Integer, primary_key=True)
    CheckTime = db.Column(db.String(200))
    ExpiredTime = db.Column(db.String(400))
    HeadImgUrl = db.Column(db.String(200))
    Nickname = db.Column(db.String(200))
    NotifyKey = db.Column(db.String(200))
    Password = db.Column(db.String(200))
    RandomKey = db.Column(db.String(200))
    Status = db.Column(db.String(200))
    Username = db.Column(db.String(200))
    Uuid = db.Column(db.String(200))
    md_username = db.Column(db.String(200))

    def __init__(self, CheckTime, ExpiredTime, HeadImgUrl, Nickname, NotifyKey, Password, RandomKey, Status, Username,
                 Uuid, md_username):
        # 这些字段 是登陆成功后的返回
        self.CheckTime = CheckTime
        self.ExpiredTime = ExpiredTime
        self.HeadImgUrl = HeadImgUrl
        self.Nickname = Nickname
        self.NotifyKey = NotifyKey
        self.Password = Password
        self.RandomKey = RandomKey
        self.Status = Status
        self.Username = Username
        self.Uuid = Uuid
        self.md_username = md_username


class BotParam(db.Model):
    __tablename__ = 'bot_param'
    __table_args__ = {"useexisting": True}

    id = db.Column(db.Integer, primary_key=True)
    Username = db.Column(db.String(200), unique=True)
    DeviceId = db.Column(db.String(200))
    LongHost = db.Column(db.String(200))
    ShortHost = db.Column(db.String(200))

    def __init__(self, Username, DeviceId, LongHost, ShortHost):
        # 这些字段 是登陆成功后的返回
        self.Username = Username
        self.DeviceId = DeviceId
        self.LongHost = LongHost
        self.ShortHost = ShortHost


class User(db.Model):
    __tablename__ = 'user'
    __table_args__ = {"useexisting": True}

    id = db.Column(db.Integer, primary_key=True)
    autoAuthKey = db.Column(db.String(200))
    cookies = db.Column(db.String(200))
    currentsyncKey = db.Column(db.String(400))
    deviceId = db.Column(db.String(200))
    deviceName = db.Column(db.String(200))
    deviceType = db.Column(db.String(200))
    maxSyncKey = db.Column(db.String(200))
    nickname = db.Column(db.String(200))
    sessionKey = db.Column(db.String(200))
    uin = db.Column(db.String(200), unique=True)
    userExt = db.Column(db.String(400))
    userame = db.Column(db.String(400))
    login = db.Column(db.Integer)

    def __init__(self, autoAuthKey, cookies, currentsyncKey, deviceId, deviceName, deviceType, maxSyncKey, nickname,
                 sessionKey, uin, userExt, userame, login):
        # 这些字段 是登陆成功后的返回
        self.autoAuthKey = str(autoAuthKey)
        self.cookies = str(cookies)
        self.currentsyncKey = str(currentsyncKey)
        self.deviceId = str(deviceId)
        self.deviceName = str(deviceName)
        self.deviceType = str(deviceType)
        self.maxSyncKey = str(maxSyncKey)
        self.nickname = str(nickname)
        self.sessionKey = str(sessionKey)
        self.uin = str(uin)
        self.userExt = str(userExt)
        self.userame = str(userame)
        self.login = login

    def __repr__(self):
        return '<user %r>' % self.username


class Message(db.Model):
    __tablename__ = 'message'
    __table_args__ = {"useexisting": True}

    id = db.Column(db.Integer, primary_key=True)
    Content = db.Column(db.String(2000))
    CreateTime = db.Column(db.String(400))
    FromUserName = db.Column(db.String(200))
    ImgBuf = db.Column(db.String(200))
    ImgStatus = db.Column(db.String(200))
    MsgId = db.Column(db.String(200), unique=True)
    MsgSource = db.Column(db.String(200))
    MsgType = db.Column(db.String(200))
    NewMsgId = db.Column(db.String(200))
    PushContent = db.Column(db.String(200))
    Status = db.Column(db.String(200))
    ToUserName = db.Column(db.String(200))

    def __init__(self, Content, CreateTime, FromUserName, ImgBuf, ImgStatus, MsgId, MsgSource, MsgType, NewMsgId,
                 PushContent, Status, ToUserName):
        self.Content = Content
        self.CreateTime = CreateTime
        self.FromUserName = FromUserName
        self.ImgBuf = ImgBuf
        self.ImgStatus = ImgStatus
        self.MsgId = MsgId
        self.MsgSource = MsgSource
        self.MsgType = MsgType
        self.NewMsgId = NewMsgId
        self.PushContent = PushContent
        self.Status = Status
        self.ToUserName = ToUserName


def save_qr_code(qr_code):
    try:
        qrcode_db = Qrcode(qr_code['CheckTime'], qr_code['ExpiredTime'], qr_code['HeadImgUrl'],
                           qr_code['Nickname'],
                           qr_code['NotifyKey'], qr_code['Password'], qr_code['RandomKey'],
                           qr_code['Status'],
                           qr_code['Username'], qr_code['Uuid'], '')
        db.session.add(qrcode_db)
        db.session.commit()
    except Exception as e:
        print("save_qr_code error")
        print e


def update_qr_code(qrcode, qrcode_db):
    try:
        for k in qrcode:
            if qrcode[k] is not None:
                # 登陆上的时候，微信返回的Uuid会为空，这种情况下就不update
                if k == 'Uuid' and (qrcode_db.Uuid is not None or qrcode_db.Uuid != ""):
                    continue
                setattr(qrcode_db, k, qrcode[k])
        db.session.commit()
    except Exception as e:
        print(e)
        print('update qrcode')


def save_user(v_user):
    try:
        user = User(
            # v_user.autoAuthKey, v_user.cookies,
            '', '', v_user.currentsyncKey, v_user.deviceId, v_user.deviceName,
            v_user.deviceType, v_user.maxSyncKey, v_user.nickname, v_user.sessionKey, v_user.uin,
            v_user.userExt, v_user.userame, -1)
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        print('save_user error')
        print e


def save_contact(msg_dict):
    try:
        contact_db = Contact(msg_dict['MsgType'], msg_dict['UserName'], msg_dict['NickName'],
                             msg_dict['Signature'],
                             msg_dict['SmallHeadImgUrl'], msg_dict['BigHeadImgUrl'],
                             msg_dict['Province'],
                             msg_dict['City'], msg_dict['Remark'], msg_dict['Alias'],
                             msg_dict['Sex'],
                             msg_dict['ContactType'], msg_dict['ChatRoomOwner'],
                             msg_dict['ExtInfo'],
                             msg_dict['Ticket'], msg_dict['ChatroomVersion'])
        db.session.add(contact_db)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)


def save_message(msg_dict):
    try:
        msg_db = Message(msg_dict['Content'], msg_dict['CreateTime'], msg_dict['FromUserName'],
                         # msg_dict['ImgBuf'],
                         '',
                         msg_dict['ImgStatus'], msg_dict['MsgId'],
                         msg_dict['MsgSource'], msg_dict['MsgType'], msg_dict['NewMsgId'],
                         msg_dict['PushContent'], msg_dict['Status'], msg_dict['ToUserName'])
        db.session.add(msg_db)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)


def save_bot_param(user_name, device_id, long_host, short_host):
    try:
        bot_param_db = BotParam(user_name, device_id, long_host, short_host)
        db.session.add(bot_param_db)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)


def update_bot_param(bot_param_db, user_name, device_id, long_host, short_host):
    try:
        bot_param_db.Username = user_name
        bot_param_db.DeviceId = device_id
        bot_param_db.LongHost = long_host
        bot_param_db.ShortHost = short_host
        db.session.commit()
    except Exception as e:
        print(e)
        print('update qrcode')


if __name__ == '__main__':
    rsp = requests.get(
        'https://image.baidu.com/search/acjson?tn=resultjson_com&ipn=rj&ct=201326592&is=&fp=result&queryWord=%E5%BD%AD%E4%BA%8E%E6%99%8F&cl=2&lm=-1&ie=utf-8&oe=utf-8&adpicid=&st=&z=&ic=&word=%E5%BD%AD%E4%BA%8E%E6%99%8F&s=&se=&tab=&width=&height=&face=&istype=&qc=&nc=&fr=&pn=120&rn=30&gsm=78&1502422711634=')
    dic = json.loads(rsp.text)
    for data in dic['data']:
        try:
            for replaceUrl in data['replaceUrl']:
                try:
                    rsp = requests.get(replaceUrl['ObjURL'])
                    if len(rsp.text) > 30000:
                        img = Img('彭于晏', replaceUrl['ObjURL'],'1')
                        db.session.add(img)
                        db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(e)
        except Exception as e:
            print(e)
    pass
    # contact_db = Contact.query.filter(Contact.NickName.contains("福利社"), Contact.UserName == "7498315793@chatroom").first()
    # is_not = contact_db is not None
    # bot_param_db = BotParam.query.filter_by(Username="wxid_q093pm99ez4k12 ").first()
    # print(contact_db.UserName)
    # 建表
    # db.create_all()
    # 新增
    # user1 = Host(u'几点几分', 'abc@124.com', 'abc', 'abc@124.com', 'abc', 'abc', 'abc@124.com')
    # db.session.add(user1)
    # db.session.commit()
    # mes = Message('a', 'a', 'a','a', 'a', 'a','a', 'a', 'a','a', 'a', 'a')
    # db.session.add(mes)
    # db.session.commit()
    # mes = Contact(2, '7799726565@chatroom', '\xee\x88\x99\xe7\xbb\xb4\xe8\xaf\xba\xef\xbc\x88\xf0\x9f\x88\xb2\xe8\xa8\x80\xef\xbc\x89\xe8\xaf\x9a\xe4\xbf\xa1\xe6\x8e\xa5\xe5\x8d\x95\xee\x88\x9c \xe7\xbe\xa4', '', '', '', '', '', '', '', 0, 0, 'wxid_dlmu21188ycr22', 'wxid_xps6e7mlzhs412,wxid_695ujxbbc0b922,wxid_y1reyk9ultwi22,wxid_9ku8el0kpjmv22,wxid_143qx7xzs3il22,wxid_s6mvx8cdh76j22,wxid_d4ix9mvpu72m22,wxid_1zbk ... (8371 characters truncated) ... ed7wt9x22,wxid_by87d9bz9ke722,wxid_odqk7a7snq1222,wxid_9cn5k1boys2l22,wxid_zbgju51vypml22,wxid_um6wzvk05ajx22,wxid_vu2my95rzyih22,wxid_hv9bettcl8od22', '', 700005710)
    # db.session.add(mes)
    # db.session.commit()
    # 查询
    # users = Host.query.all()[0]
    # print(users.uin)
    #
    # admin = Qrcode.query.filter_by(Username='wxid_q093pm99ez4k12').order_by(Qrcode.id.desc()).first()
    # print admin.id
    #
    # qr_code_db = Qrcode.query.filter_by(md_username='15900000010').order_by(Qrcode.id.desc()).all()
    # for qr_code in qr_code_db:
    #     if qr_code.Username != '':
    #         wx_username = qr_code.Username
    #         print(wx_username)
    #         break
    # print(admin)
    #
    # 删除
    # u3 = Host.query.first()
    # db.session.delete(u3)
    # db.session.commit()
    #
    # 修改
    # u4 = Host.query.first()
    # u4.username = u'专升本'  # 中文必须为unicode类型，而不是str类型
    # db.session.commit()
