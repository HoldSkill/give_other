# coding:utf-8
from taobaoke.weixin_bot import WXBot
import pickle
from taobaoke.settings import red
from taobaoke.utils.common_utils import get_time_stamp
from Crypto.PublicKey import RSA

def try_sns_post(username):
    xml = """
        <TimelineObject>
          <id>12542129193584242947</id>
          <username>wxid_q093pm99ez4k12</username>
          <createTime>{}</createTime>
          <contentDesc>“羡慕那些一沾着枕头就能安睡的人和那些决心放手之后就不再回头的人”</contentDesc>
          <contentDescShowType>0</contentDescShowType>
          <contentDescScene>3</contentDescScene>
          <private>0</private>
          <sightFolded>0</sightFolded>
          <appInfo>
              <id></id>
              <version></version>
              <appName></appName>
              <installUrl></installUrl>
              <fromUrl></fromUrl>
              <isForceUpdate>0</isForceUpdate>
          </appInfo>
          <sourceUserName></sourceUserName>
          <sourceNickName></sourceNickName>
          <statisticsData></statisticsData>
          <statExtStr></statExtStr>
          <ContentObject>
              <contentStyle>2</contentStyle>
              <title></title>
              <description></description>
              <mediaList></mediaList>
              <contentUrl></contentUrl>
          </ContentObject>
          <actionInfo>
              <appMsg>
                  <messageAction></messageAction>
              </appMsg>
          </actionInfo>
          <location city="" poiClassifyId="" poiName="" poiAddress="" poiClassifyType="0"></location>
          <publicUserName></publicUserName>
        </TimelineObject>
        """.format(get_time_stamp())
    v_user_pickle = red.get('v_user_' + username)
    v_user = pickle.loads(v_user_pickle)
    bot.sns_post(v_user, xml)


def try_delete_chatroom_member(username, chatroom_id, wx_id):
    v_user_pickle = red.get('v_user_' + username)
    v_user = pickle.loads(v_user_pickle)
    bot.delete_chatroom_member(v_user, chatroom_id, wx_id)


def try_add_chatroom_member(username, chatroom_id, wx_id):
    v_user_pickle = red.get('v_user_' + username)
    v_user = pickle.loads(v_user_pickle)
    bot.add_chatroom_member(v_user, chatroom_id, wx_id)


def try_create_chatroom(username, wx_id):
    v_user_pickle = red.get('v_user_' + username)
    v_user = pickle.loads(v_user_pickle)
    bot.create_chatroom(v_user, wx_id)


def try_send_voice_msg(username, to_user_name, url):
    v_user_pickle = red.get('v_user_' + username)
    v_user = pickle.loads(v_user_pickle)
    bot.send_voice_msg(v_user, to_user_name)


# def rsa_function():

if __name__ == "__main__":
    bot = WXBot()
    # wx_user = "wxid_wpomnc6r4ahp22"
    # 7035453409@chatroom
    # bot.try_get_new_message(wx_user)
    # bot.try_sns_post('wxid_q093pm99ez4k12')
    # try_delete_chatroom_member('wxid_q093pm99ez4k12', '6362478985@chatroom', 'stella_lee_')
    # try_add_chatroom_member('wxid_q093pm99ez4k12', '6362478985@chatroom', 'stella_lee_')
    # try_create_chatroom('wxid_q093pm99ez4k12', 'wxid_q093pm99ez4k12,zhengyaohong0724,stella_lee_,wxid_kvxks7dxdqbz22')
    # bot.try_get_new_message("wxid_q093pm99ez4k12")
    bot.try_send_message("wxid_q093pm99ez4k12")
    # bot.login('15900000010')
