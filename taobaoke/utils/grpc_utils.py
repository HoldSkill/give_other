# coding:utf-8
import common_utils


def get_seq_buffer(response):
    head = response.baseMsg.longHead
    body = response.baseMsg.payloads
    import binascii
    print(binascii.b2a_hex(head))
    print(binascii.b2a_hex(body))
    buffers = head + body

    seq = common_utils.read_int(head, 12)

    return buffers, seq
