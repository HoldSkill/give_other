# _*_ coding:utf-8 _*_

import threading
import socket
import asynchat
import time
from datetime import datetime
from taobaoke.utils import common_utils

'''
async_chat & asyncore.dispatcher
    https://docs.python.org/2/library/asynchat.html
    https://docs.python.org/2/library/asyncore.html
'''


class WechatClient(asynchat.async_chat, object):
    def __init__(self, end_point_host, end_point_port, is_print_log=False):
        # set options
        self.is_print_log = is_print_log
        self.__notify_list = []

        self.__rec_package_dict = {}
        self.__lock = threading.Lock()

        # set end point address
        self.endpoint_host = end_point_host
        self.endpoint_port = end_point_port

        # set receive data buffer size
        self.ac_in_buffer_size = 81920
        self.set_terminator(None)
        self.asyn_rec_thread = threading.Thread(target=self.__asyn_rec)
        self.asyn_rec_thread.setDaemon(True)
        self.asyn_rec_thread.start()

        # set socket
        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        errcode = _socket.connect_ex((self.endpoint_host, self.endpoint_port))
        if errcode == 0:
            self.__print_log("socket connected")
        else:
            self.__print_log("error_code:{0}".format(errcode))
        super(WechatClient, self).__init__(_socket)
        # self.connect((self.endpoint_host, self.endpoint_port))

        # initial arg
        self.buffer_output = []
        self.rec_flag = False
        self.rec_len = 0
        self.total_len = 0
        self.seq = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_when_done()
        return

    def close_when_done(self):
        super(WechatClient, self).close_when_done()
        if self.socket is not None:
            self.socket.close()
            self.__print_log("close socket")

    def asyn_send(self, data):
        self.push(data)

    def sync_send_and_return(self, data, time_out=1, close_socket=False):
        self.asyn_send(data)
        seq = common_utils.read_int(data, 12)
        start_time = datetime.now()
        while True:
            buffers = self.get_packaget_by_seq(seq)
            if buffers is not None:
                if close_socket:
                    self.close_when_done()
                return buffers
            time.sleep(time_out)
            if (datetime.now() - start_time).seconds >= time_out*10:
                if close_socket:
                    self.close_when_done()
                break

    def __asyn_rec(self):
        while True:
            try:
                time.sleep(1)
                if self.connected is True:
                    self.handle_read()
                else:
                    break
            except Exception as e:
                print(e)

    def collect_incoming_data(self, data):
        if self.connected is False:
            return

        while len(data) != 0:
            cur_rec_len = len(data)
            self.__print_log("Receive Wx Server Block Buf length:{0}".format(cur_rec_len))
            if cur_rec_len > 0:
                # 检测头部是否有20字节的notify包
                if common_utils.read_int(data[:20], 0) == 20:
                    tmp_data = data[:20]
                    tmp_seq = common_utils.read_int(data, 12)
                    cmd = common_utils.read_int(tmp_data, 8)
                    selector = common_utils.read_int(tmp_data, 16)

                    self.__process_notify_package(tmp_data)

                    # cmd = 24的notify包就不存了
                    if tmp_seq not in self.__rec_package_dict.keys() and cmd != 24:
                        self.__rec_package_dict[tmp_seq] = data[:20]

                    data = data[20:]
                    self.__print_log("rec 20 bytes package from head**")
                    continue

                # 检测尾部
                if common_utils.read_int(data[-20:], 0) == 20:
                    tmp_data = data[-20:]
                    tmp_seq = common_utils.read_int(tmp_data, 12)
                    cmd = common_utils.read_int(tmp_data, 8)
                    selector = common_utils.read_int(tmp_data, 16)

                    self.__process_notify_package(tmp_data)

                    # cmd = 24的notify包就不存了
                    if tmp_seq not in self.__rec_package_dict.keys() and cmd != 24:
                        self.__rec_package_dict[tmp_seq] = data[-20:]

                    data = data[:-20]
                    self.__print_log("rec 20 bytes package from tail--")
                    continue

                if self.rec_flag is False:
                    self.seq = common_utils.read_int(data, 12)
                    self.__print_log("Receive Seq {0}".format(self.seq))
                    # 期望包总长度
                    self.total_len = common_utils.read_int(data, 0)
                    self.__print_log("WX say this package Total Length should be :{0}".format(self.total_len))
                    if self.total_len > 100000:
                        # total_len太长不正常直接过滤...
                        return
                    self.buffer_output = []
                else:
                    pass

                # 如果 期望包总长度 大于 之前已接收包长度，说明需要粘包拆包
                if self.total_len > self.rec_len:
                    # 如果 期望包总长度 小于 当前此包长度，需要自己拆包???????这段逻辑有问题
                    if self.total_len < cur_rec_len + self.rec_len:
                        self.__print_log("This time wx sent too much:{0}".format(self.total_len))
                        data_to_process = data[:self.total_len-self.rec_len]
                        # data_to_process = data[:self.total_len-self.rec_len]是否应该这么改
                        self.rec_len += self.total_len

                    # 如果 期望包总长度 大于或等于 当前此包长度，则代表还需要粘包
                    else:
                        data_to_process = data
                        self.rec_len += cur_rec_len

                    # buffer_output就是最终的包
                    self.buffer_output += data_to_process
                else:
                    self.__print_log("我想要的包，上次就接收够了，你这次还来")
                # 这句话好像没用
                data = data[self.rec_len:]

                # 如果期望包 等于 总接收包，说明ok了，可以将其放入package中
                if self.total_len == self.rec_len:
                    if self.__lock.acquire():
                        _buffers = common_utils.byte_list_to_byte_string(self.buffer_output)
                        # seq等于0的情况需要另处理
                        if self.seq == 0:
                            self.__process_notify_package(_buffers)
                        # 当前dict没有这个seq，放入
                        elif self.seq not in self.__rec_package_dict.keys():
                            self.__rec_package_dict[self.seq] = _buffers
                            self.__print_log("Receive Wx Server Buf length:{0}".format(self.total_len))
                            self.seq = 0
                        # 重置参数
                        self.rec_flag = False
                        self.rec_len = 0
                        self.total_len = 0
                        self.__lock.release()
                elif self.total_len > self.rec_len:
                    # self.total_len > self.rec_len那就继续等下个包接收
                    self.rec_flag = True
                    self.__print_log("on data, total_len is {}, rec_len is {}".format(self.total_len, self.rec_len))
                    # from author:排除在接收分包时候的notify 包的干扰 将之前累加的20字节封包在减去...
                    if self.seq > 0 and cur_rec_len == 20:
                        self.rec_len -= cur_rec_len
                else:
                    self.rec_flag = False
                    # self.total_len < self.rec_len说明出现问题了
                    self.__print_log("total_len {} should >= rec_len {}".format(self.total_len, self.rec_len))
                    return

    def __process_notify_package(self, data):
        # 处理不同cmd的包
        cmd = common_utils.read_int(data, 8)
        selector = common_utils.read_int(data, 16)
        print "cmd:{0},selector:{1}".format(cmd, selector)
        if cmd == 318 and len(self.__notify_list) != 0:
            self.__notify(data)
        if cmd == 24 and len(self.__notify_list) != 0 and len(data) == 20:
            self.__notify(data)
        if cmd != 24 and cmd != 318:
            self.__print_log("未知包CMD:{0} selector:{1} 过滤:{2}".format(cmd, selector, len(data)))

    def get_packaget_by_seq(self, seq):
        if self.__lock.acquire():
            if seq in self.__rec_package_dict.keys():
                _buf = self.__rec_package_dict[seq]
                self.__rec_package_dict.pop(seq)
                self.__lock.release()
                return _buf
            self.__lock.release()
            return None

    def push(self, data):
        self.ac_out_buffer_size = len(data)
        super(WechatClient, self).push(data)
        self.__print_log("push data length: " + str(len(data)))

    # found_terminator() must to override
    def found_terminator(self):
        pass

    def __notify(self, data):
        for func in self.__notify_list:
            try:
                threading.Thread(target=func, args=(data, )).start()
            except Exception as e:
                self.__print_log("exception:{0}".format(e.message))
                continue

    def register_notify(self, func):
        self.__notify_list.append(func)

    def __print_log(self, msg):
        if self.is_print_log is True:
            print msg

    @staticmethod
    def check_buffer_16_is_191(buffers):
        if buffers is None or ord(buffers[16]) is not 191:
            print("wrong wx return")
            return False
        else:
            print("right wx return")
            return True
