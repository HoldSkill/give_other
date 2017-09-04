# coding=utf-8
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
app = Flask("weixin_bot")
# 修改为utf8mb4
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Xiaozuanfeng@s-poc-01.qunzhu666.com:50001/koeltest?charset=utf8'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)
from taobaoke.controller import taobaoke_api
