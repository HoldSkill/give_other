# _*_ coding:utf-8 _*_
import re
import socket
from datetime import datetime
import time
import requests
import struct
import md5
# from pyv8 import PyV8
#
#
# def run_js(s):
#     ctxt = PyV8.JSContext()
#     ctxt.enter()
#     func = ctxt.eval("function asciiConvertNative(s){var asciicode=s.split(\"\\\\u\");var nativeValue=asciicode[0];for(var i=1;i<asciicode.length;i++){var code=asciicode[i];nativeValue+=String.fromCharCode(parseInt(\"0x\"+code.substring(0,4)));if(code.length>4){nativeValue+=code.substring(4,code.length)}}return nativeValue};")
#     print func(s)


def get_md5(s):
    # 32位16进制md5 也就是128位2进制md5
    if s == '' or s is None:
        return "74237af20c724e36316cf39ddce7a97c"
    m1 = md5.new()
    m1.update(s)
    return m1.hexdigest()


def get_time_stamp():
    ret = datetime.now().timetuple()
    return int(time.mktime(ret))


def byte_list_to_byte_string(byte_list):
    byte_string = ''
    for byte in byte_list:
        byte_string += byte
    return byte_string


def get_public_ip():
    # r = requests.get("http://1212.ip138.com/ic.asp")
    # reg = "\[(.*?)\]"
    # ip = re.findall(reg, r.text, re.M)[0]
    # return ip.replace('[', '').replace(']', '')
    return '119.23.149.138'


def usc2ascii(s):
    asciicode = s.split(r"\\u")
    nativeValue = asciicode[0]
    for i in range(1, len(asciicode)):
        code = asciicode[i]
        nativeValue += unichr(int('0x'+code[:4], 16))
        if len(code) > 4:
            nativeValue += code[4:]
    return nativeValue

# def read_int(byte_list, index):
#     if len(byte_list) >= 16:
#         seqBuf = byte_list[index:index + 4]
#         # str_to_convert = ''
#         # for byte in seqBuf:
#         #     print(byte)
#         #     str_to_convert += str(ord(byte))
#         # print(str_to_convert)
#         # # 32位正整数从网络序转换成主机字节序，整数与ip地址互换
#         # seq_int = struct.unpack('i', str_to_convert)[0]
#         seq_int = struct.unpack('I', seqBuf)[0]
#         return socket.ntohl(seq_int)
#     return 1
def read_int(byte_string_list, index):
    if len(byte_string_list) >= 16:
        seqBuf = byte_string_list[index:index + 4]
        seq_int = struct.unpack('I', seqBuf)[0]
        return socket.ntohl(seq_int)
    return 1


def int_list_convert_to_byte_list(int_list):
    # each num in int_list must lower than 256
    byte_str = ''
    for int_num in int_list:
        byte_str = byte_str + chr(int_num)
    return byte_str


def char_to_str(char_lst):
    s = ''
    for i in char_lst:
        s = s + i
    return s


def check_buffer_16_is_191(buffers):
    if buffers is None:
        print('buffer is None')
        return False
    if ord(buffers[16]) is not 191:
        print("wrong wx return")
        return False
    else:
        print("right wx return")
        return True


def str_to_byte_list(s):
    byte_list = []
    for i in s:
        byte_list.append(ord(i))
    return byte_list


def check_grpc_response(ret):
    if ret >= 10000001:
        print "grpc error"


def timestamp_to_time(timestamp):
    print time.localtime(timestamp)


if __name__ == "__main__":
    # byte_list = range(1, 20)
    # print(read_int(byte_list, 10))
    # byte_list = ['\x00', '\x00', 'A', '\xbe', '\x00', '\x10', '\x00', '\x01']
    # print char_to_str(byte_list)
    # print(get_md5(str(time.time())))
    # timestamp_to_time(1503371850)
    # print(get_md5())
    # print(get_time_stamp())
    import re
    pattern = re.compile(r'(\w+)')
    m = pattern.match('wwwwww')
    print(m.group(1))
    from datetime import datetime
    print(get_md5('dabaiceo'))
