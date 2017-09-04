# -*- coding: utf-8 -*-
import oss2
import requests
import codecs

oss_config = {
    'END_POINT': 'http://oss-cn-shenzhen.aliyuncs.com',
    'ACCESS_KEY_ID': 'LTAIjkzLt8KXZLjV',
    'ACCESS_KEY_SECRET': 'IOZgRYmZVgMxYa36K9Y00Mzw3iARaI',
    'BUCKET_NAME': 'wechat-bot',
    'URL_BASE': 'http://wechat-bot.oss-cn-shenzhen.aliyuncs.com/'
}

auth = oss2.Auth(oss_config['ACCESS_KEY_ID'], oss_config['ACCESS_KEY_SECRET'])
bucket = oss2.Bucket(auth, oss_config['END_POINT'], oss_config['BUCKET_NAME'])


def put_file_to_oss(fn, data):
    """
    内部方法，用来直接将字符串数据存储到OSS的指定文件中
    :param fn: 文件的相对路径
    :param data: 文件的内容
    :return: 文件的外部地址
    """
    bucket.put_object_from_file(fn, data)
    return oss_config['URL_BASE'] + fn


def put_object_to_oss(fn, data):
    bucket.put_object(fn, data)
    return oss_config['URL_BASE'] + fn


if __name__ == "__main__":
    img_path = '../img/qrcode.png'
    with codecs.open(img_path, 'rb') as img_file:
        data = img_file.read()
        oss_path = put_object_to_oss("wxpad/qrcode3.png", data)
    print(oss_path)
