import getopt
import sys
import time
import base64

import BasicSender
import Checksum

'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''


# __init__()函数:为Sender类定义一些通用属性并初始化，便于后续处理使用。
# 一些实现仿照Receiver.py完成
# window:发送窗口。缓存了一定范围的数据。下标是顺序号，内容是数据部分(data)和消息类型(type)。对于sack，还有发送时的时间(time)
# windowSize:窗口大小
# base:窗口起始处，窗口范围为[base,base+WINDOW_SIZE-1]
# msg_type:类型
# seqno:当前序列号
# msg:消息主体
# next_msg:下一条消息
# packetSize:每次发送的数据大小
# timelimit:超时界限
# dup_ack:重传计数器。当到达3时，重传窗口内容。
# last_ack:最新收到的ack
# end:标识是否真正结束，因为end消息也可能重传，不能直接拿来当结束判据。当end消息被确实发送后，end=True.
class Sender(BasicSender.BasicSender):
    def __init__(self, dest, port, filename, debug=False, sackMode=False):
        super(Sender, self).__init__(dest, port, filename, debug)
        self.sackMode = sackMode
        self.window = {}
        self.windowSize = 5
        self.base = 0
        self.msg_type = None
        self.seqno = 0
        self.msg = None
        self.next_msg = None
        self.packetSize = 500
        self.timelimit = 0.5
        self.dup_ack = 0
        self.last_ack = 0
        self.end = False

    # Main sending loop.
    # 执行Go Back N算法，两种需要注意的情况：
    # 1. 结束消息发在了窗口外就断开连接了，这样接收方收不到结束消息
    # 2. 窗口满了，此时不应该继续读下一个msg，否则会丢失掉中间的信息
    # 选择重传算法的大体框架与GBN类似
    def start(self):
        self.msg = self.infile.read(self.packetSize)
        # 当发送完所有数据包，且发送窗口也为空时，断开连接
        while not self.end or self.window != {}:
            # 一次发送所有能发的分组，以加快速度
            # 缺点：在丢包严重时重发更多分组，因为窗口总是很满
            while self.base <= self.seqno < self.base + self.windowSize and not self.end:
                self.next_msg = self.infile.read(self.packetSize)
                self.msg_type = 'data'
                if self.seqno == 0:
                    self.msg_type = 'start'
                elif len(self.next_msg) == 0:
                    self.msg_type = 'end'

                self.handle_send()
            self.handle_response()

        self.infile.close()
        self.log("Sender.py:CLOSED!!!")

    def handle_send(self):
        self.handle_base64()
        if self.msg_type == 'end':
            self.end = True
        packet = self.make_packet(self.msg_type, self.seqno, self.msg)
        self.send(packet)
        print("sent: %s" % packet)
        if self.sackMode:
            self.window[self.seqno] = [self.msg_type, self.msg, time.time()]
        else:
            self.window[self.seqno] = (self.msg_type, self.msg)
        if self.debug:
            print("\n\n\nSender.py:---------------window content------------------")
            for i in self.window:
                print("%d %s" % (i, self.window[i][0]))
            print("---------------------------------------------------------\n\n\n")
        # 发送成功(无关是否接收到)的话，将序列号+1
        self.msg = self.next_msg
        self.seqno += 1

    def handle_response(self):
        response = self.receive(self.timelimit)
        try:
            response = response.decode()
        except AttributeError:
            if self.sackMode:
                current = time.time()
                for n in sorted(self.window.keys()):
                    if current - self.window[n][2] > self.timelimit:
                        self.log("Sender.py:seq %d timeout %f s,RETRANSMIT!!!!!!!!!!!!" % (n,current-self.window[n][2]))
                        self.handle_timeout_sack(n)
            else:
                self.handle_timeout()
                self.log("Sender.py:timeout,RETRANSMIT!!!!!!!!!!!!")

        if Checksum.validate_checksum(response):
            print("recv: %s" % response)
            if self.sackMode:
                ack_type, ack_seq, ack_data, ack_checksum = self.split_packet(response)
                pieces = ack_seq.split(';')
                cum_ack = int(pieces[0])
                ackpieces = pieces[-1].split(',')
                if cum_ack == self.last_ack:
                    self.handle_dup_sack(ackpieces)
                elif cum_ack > self.last_ack:
                    self.last_ack = cum_ack
                    self.handle_new_sack(cum_ack, ackpieces)
            else:
                ack_type, ack_seq, ack_data, ack_checksum = self.split_packet(response)
                ack_seq = int(ack_seq)
                if ack_seq == self.last_ack:
                    self.handle_dup_ack()
                elif ack_seq > self.last_ack:
                    self.last_ack = ack_seq
                    self.handle_new_ack(ack_seq)

    # 超时处理
    # 需要重传当前窗口内的所有数据包
    def handle_timeout(self):
        for n in sorted(self.window.keys()):
            re_type = self.window[n][0]
            re_message = self.window[n][1]
            re_packet = self.make_packet(re_type, n, re_message)
            self.send(re_packet)

    # 发送端收到新ACK时
    # 将对应序列号之前的消息从发送窗口中删除，并更新base
    def handle_new_ack(self, ack):
        for n in sorted(self.window.keys()):
            if n < ack:
                del self.window[n]
        self.base = ack

    # 发送端收到重复ACK时
    # 将重复计数器+1，到达3时当作超时处理，重传发送窗口所有数据包
    def handle_dup_ack(self):
        self.dup_ack += 1
        self.log("Sender.py:Duplicate ACKs:%d" % self.dup_ack)
        if self.dup_ack >= 3:
            self.handle_timeout()
            self.dup_ack = 0
            self.log("Sender.py:3 or More Duplicate ACKs,RETRANSIMIT!!!!!!!!!")

    # sack超时处理
    # 选择重传下，每个分组都有独立计时器
    # 分组超时时重传该分组，并更新该分组计时器
    def handle_timeout_sack(self, sack):
        re_type = self.window[sack][0]
        re_message = self.window[sack][1]
        re_packet = self.make_packet(re_type, sack, re_message)
        self.send(re_packet)
        self.window[sack][2] = time.time()

    # 处理sack
    # 将对应序列号之前的消息从发送窗口中删除，并更新base为累计ACK
    # 将各ack对应的消息也删除
    def handle_new_sack(self, cum_ack, SACKs):
        for n in sorted(self.window.keys()):
            if n < cum_ack:
                del self.window[n]
        self.base = cum_ack
        for i in SACKs:
            try:
                del self.window[int(i)]
            except ValueError:
                pass
            except KeyError:
                pass

    # 多个重复sack
    # 3次时重发对应消息
    # 同时也要将收到的各ack删除
    def handle_dup_sack(self,SACKs):
        self.dup_ack += 1
        self.log("Sender.py:Duplicate ACKs:%d" % self.dup_ack)
        if self.dup_ack >= 3:
            self.handle_timeout_sack(self.last_ack)
            self.dup_ack = 0
            self.log("Sender.py:3 or More Duplicate ACKs,RETRANSIMIT!!!!!!!!!")
        for i in SACKs:
            try:
                del self.window[int(i)]
            except ValueError:
                pass
            except KeyError:
                pass

    # 为了传输非文本，将data部分用base64转换，这样在encode、decode时才不会丢失内容
    def handle_base64(self):
        self.msg = base64.b64encode(self.msg)               # msg应该是bytes类型，base64encode后仍为bytes类型
        self.msg = self.msg.decode()                        # 转换为str类型，方便后续处理

    def log(self, msg):
        if self.debug:
            print(msg)


'''
This will be run if you run this script from the command line. You should not
change any of this; the grader may rely on the behavior here to test your
submission.
'''
if __name__ == "__main__":
    def usage():
        print("RUDP Sender")
        print("-f FILE | --file=FILE The file to transfer; if empty reads from STDIN")
        print("-p PORT | --port=PORT The destination port, defaults to 33122")
        print("-a ADDRESS | --address=ADDRESS The receiver address or hostname, defaults to localhost")
        print("-d | --debug Print debug messages")
        print("-h | --help Print this usage message")
        print("-k | --sack Enable selective acknowledgement mode")


    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "f:p:a:dk", ["file=", "port=", "address=", "debug=", "sack="])
    except:
        usage()
        exit()

    port = 33122
    dest = "localhost"
    filename = None
    debug = False
    sackMode = False

    for o, a in opts:
        if o in ("-f", "--file="):
            filename = a
        elif o in ("-p", "--port="):
            port = int(a)
        elif o in ("-a", "--address="):
            dest = a
        elif o in ("-d", "--debug="):
            debug = True
        elif o in ("-k", "--sack="):
            sackMode = True

    s = Sender(dest, port, filename, debug, sackMode)
    try:
        s.start()
    except (KeyboardInterrupt, SystemExit):
        exit()
