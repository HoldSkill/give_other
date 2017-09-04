# coding=utf-8
import json

import cPickle as pickle
import sys
from datetime import timedelta
from flask import current_app, jsonify, make_response
from flask import request
from functools import wraps, update_wrapper

from taobaoke import app, db
from taobaoke import weixin_bot
from taobaoke.database.model import User, Qrcode
from taobaoke.weixin_bot import WXBot

reload(sys)
sys.setdefaultencoding("utf-8")


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)

    return decorator


def support_jsonp(f):
    """Wraps JSONified output for JSONP"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + str(f().data) + ')'
            return current_app.response_class(content, mimetype='application/json')
        else:
            return f(*args, **kwargs)

    return decorated_function


@app.route('/', methods=['GET'])
@support_jsonp
def helloworld():
    return jsonify({"ret": "helloworld"})


@app.route('/qrcode', methods=['GET'])
@support_jsonp
def get_qrcode():
    """
    获取二维码接口
    传参 usename 也就是 手机号
    :return: 
    """
    md_username = request.args.get('username', '')
    wx_bot = WXBot()
    (oss_path, qrcode_rsp, deviceId) = wx_bot.get_qrcode(md_username)

    try:
        buffers = qrcode_rsp.baseMsg.payloads
        qr_code = json.loads(buffers)
        uuid = qr_code['Uuid']
        qr_code_db = Qrcode.query.filter_by(Uuid=uuid).order_by(Qrcode.id.desc()).first()
        qr_code_db.md_username = md_username
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)

    # new thread to check check_qrcode_login async
    import thread
    thread.start_new_thread(wx_bot.check_and_confirm_and_load, (qrcode_rsp, deviceId))

    return jsonify({"qrcode_url": oss_path, "uuid": uuid})


@app.route('/send_msg', methods=['GET'])
@support_jsonp
def send_msg():
    """
    发送消息接口 传入wx_id 群id 内容，异步操作。只返回接收成功，不保证操作成功
    :return: 
    """
    wx_id = request.args.get('wx_id', '')
    to_wx_id = request.args.get('to_wx_id', '')
    text = request.args.get('text', '')
    # img or text
    type = request.args.get('type', '')
    delay_time = request.args.get('delay_time', 0)
    # find wxid by uin
    v_user_pickle = weixin_bot.red.get('v_user_' + wx_id)
    v_user = pickle.loads(v_user_pickle)

    wx_bot = WXBot()
    return_msg = "1"
    if type == 'img':
        import thread
        thread.start_new_thread(wx_bot.send_img_msg, (to_wx_id, v_user, text))
    elif type == 'text':
        # 请求grpc 必须替换这些字符
        if '\n' in text or '\r' in text:
            print('include n or r')
            # 类似发单群
            text = text.replace('\r', '\\r').replace('\n', '\\r')
            import thread
            thread.start_new_thread(wx_bot.try_sleep_send, (int(delay_time), to_wx_id, text, v_user))
        else:
            wx_bot.send_text_msg(to_wx_id, text, v_user)
    else:
        return_msg = 'type error, should be img or text'
    return jsonify({"ret": return_msg})


@app.route('/is_logon')
def is_logon():
    """
    登陆接口 返回 昵称 群名
    # http://localhost:5000/is_logon?username=15900000010
    :return: 
    """
    username = request.args.get('username', '')
    if 'username' == '':
        return jsonify({"ret": str(0), "name": "未登录"})
    ret = 0
    name = ''
    with app.app_context():
        try:
            # username是手机号
            qr_code_db = Qrcode.query.filter_by(md_username=username).order_by(Qrcode.id.desc()).all()
            for qr_code in qr_code_db:
                if qr_code.Username != '':
                    wx_username = qr_code.Username
            # 筛选出wx_username
            print(wx_username)

            # 筛选出wx用户昵称
            user_db = User.query.filter_by(userame=wx_username).first()
            ret = user_db.login
            name = user_db.nickname
        except Exception as e:
            print(e)
    return jsonify({"ret": str(ret), "name": name})


@app.route('/is-uuid-login')
def is_uuid_login():
    """
    检测该UUID是否被扫描登陆
    # http://localhost:5000/is-uuid-login?qr-uuid=gZF8miqrkksZ9mrRk7mc
    :return:返回登陆的微信 nickname 和 login 状态
    """
    uuid = request.args.get('uuid', '')
    if uuid == '':
        return jsonify({"ret": str(0), "name": "uuid 为空"})
    ret = 0
    name = ''
    with app.app_context():
        try:
            # username是手机号
            qr_code_db = Qrcode.query.filter_by(Uuid=uuid).first()
            if qr_code_db is not None and qr_code_db.Username != '':
                wx_username = qr_code_db.Username
                # 筛选出wx_username
                print(wx_username)

                # 筛选出wx用户昵称
                user_db = User.query.filter_by(userame=wx_username).first()
                ret = user_db.login
                name = user_db.nickname
        except Exception as e:
            print(e)
    return jsonify({"ret": str(ret), "name": name})
