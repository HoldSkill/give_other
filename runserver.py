# coding=utf-8
from taobaoke import app
from taobaoke.heartbeat_manager import HeartBeatManager

if __name__ == "__main__":
    HeartBeatManager().run()
    app.run(host='0.0.0.0')
    # app.run()
