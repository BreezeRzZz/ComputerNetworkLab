import sys
import socket
import random

import Checksum

'''
This is the basic sender class. Your sender will extend this class and will
implement the start() method.
'''
# debug:是否debug
# dest:目标地址
# dport:目标端口
# sock:发送端socket
# infile:用于输入的文件(若无则为stdin)
class BasicSender(object):
    def __init__(self,dest,port,filename,debug=False):
        self.debug = debug
        self.dest = dest
        self.dport = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(None)  # blocking
        self.sock.bind(('',random.randint(10000,40000)))            # 随机选一个端口
        if filename == None:
            self.infile = sys.stdin
        else:
            self.infile = open(filename,"rb")       # 注意，为了读取图片等非文本，我们需要以二进制读取内容！

    # Waits until packet is received to return.
    def receive(self, timeout=None):
        self.sock.settimeout(timeout)
        try:
            return self.sock.recv(4096)
        except (socket.timeout, socket.error):
            return None

    # Sends a packet to the destination address.
    def send(self, message, address=None):
        if address is None:
            address = (self.dest,self.dport)
        self.sock.sendto(message.encode(), address)     # 数据被二进制发送

    # Prepares a packet
    def make_packet(self,msg_type,seqno,msg):
        body = "%s|%d|%s|" % (msg_type,seqno,msg)
        checksum = Checksum.generate_checksum(body)
        packet = "%s%s" % (body,checksum)
        return packet

    def split_packet(self, message):
        pieces = message.split('|')
        msg_type, seqno = pieces[0:2] # first two elements always treated as msg type and seqno
        checksum = pieces[-1] # last is always treated as checksum
        data = '|'.join(pieces[2:-1]) # everything in between is considered data
        return msg_type, seqno, data, checksum

    # Main sending loop.
    def start(self):
        raise NotImplementedError
