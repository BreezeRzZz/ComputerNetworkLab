import getopt
import socket
import sys
import time
import base64

import Checksum


class Connection():
    def __init__(self, host, port, start_seq, debug=False):
        self.debug = debug
        self.updated = time.time()      # 获取当前时间，作为计时器
        self.current_seqno = start_seq - 1  # expect to ack from the start_seqno
        self.host = host
        self.port = port
        self.max_buf_size = 5
        self.outfile = open("%s.%d" % (host, port), "wb")
        self.seqnums = {}  # enforce single instance of each seqno

    def ack(self, seqno, data, sackMode=False):
        res_data = []
        sacks = []
        self.updated = time.time()      # 更新计时器
        if self.current_seqno < seqno <= self.current_seqno + self.max_buf_size:  # 若顺序号在接收窗口内，缓存
            self.seqnums[seqno] = data
            for n in sorted(self.seqnums.keys()):           # 将接收窗口按顺序号排序并遍历
                if n == self.current_seqno + 1:             # 如果该顺序号是希望接收的顺序号
                    self.current_seqno += 1                 # 希望接收的顺序号+1
                    res_data.append(self.seqnums[n])        # 把对应的数据添加到实际收到的部分
                    del self.seqnums[n]                     # 把对应数据从缓存中删除
                else:
                    break  # when we find out of order seqno, quit and move on

        if self.debug:
            print("Receiver.py:next seqno should be %d" % (self.current_seqno + 1))

        # note: we return the /next/ sequence number we're expecting
        if sackMode:
            for n in sorted(self.seqnums.keys()):
                sacks.append(n)
            return "%s;%s" % (self.current_seqno + 1, ','.join(map(str, sacks))), res_data
        else:
            return str(self.current_seqno + 1), res_data

    def record(self, data):         # 把收到的数据写到文件上
        # 将data通过base64转码
        data = data.encode()                       # str -> bytes
        data = base64.b64decode(data)              # bytes -> bytes
        self.outfile.write(data)
        self.outfile.flush()

    def end(self):
        self.outfile.close()


class Receiver():
    def __init__(self, listenport=33122, debug=False, timeout=10, sackMode=False):
        self.debug = debug
        self.timeout = timeout
        self.sackMode = sackMode
        self.last_cleanup = time.time()
        self.port = listenport
        self.host = ''
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.settimeout(timeout)
        self.s.bind((self.host, self.port))
        self.connections = {}  # schema is {(address, port) : Connection}
        self.MESSAGE_HANDLER = {            # 对于不同的消息类型作不同处理
            'start': self._handle_start,
            'data': self._handle_data,
            'end': self._handle_end,
            'ack': self._handle_ack
        }

    def start(self):
        while True:
            try:
                message, address = self.receive()
                message = message.decode()
                msg_type, seqno, data, checksum = self._split_message(message)
                try:
                    seqno = int(seqno)
                except:
                    raise ValueError
                if debug:
                    print("Receiver.py: received %s|%d|%s|%s" % (msg_type, seqno, data[:5], checksum))
                if Checksum.validate_checksum(message):         # 检查检验和是否正确，如果正确按消息类型作不同处理
                    self.MESSAGE_HANDLER.get(msg_type, self._handle_other)(seqno, data, address)
                elif self.debug:
                    print("Receiver.py: checksum failed: %s|%d|%s|%s" % (msg_type, seqno, data[:5], checksum))

                if time.time() - self.last_cleanup > self.timeout:      # 定期检查超时情况
                    self._cleanup()
            except socket.timeout:
                self._cleanup()
            except (KeyboardInterrupt, SystemExit):
                exit()
            except ValueError as e:
                if self.debug:
                    print("Receiver.py:" + str(e))
                pass  # ignore

    # waits until packet is received to return
    def receive(self):          # socket API接收数据
        return self.s.recvfrom(4096)

    # sends a message to the specified address. Addresses are in the format:
    #   (IP address, port number)
    def send(self, message, address):
        self.s.sendto(message.encode(), address)

    # this sends an ack message to address with specified seqno
    def _send_ack(self, seqno, address):
        if self.sackMode:
            m = "sack|%s|" % seqno
        else:
            m = "ack|%s|" % seqno
        checksum = Checksum.generate_checksum(m)
        message = "%s%s" % (m, checksum)
        if self.debug:
            print("Receiver.py: send ack %s" % m)
        self.send(message, address)

    def _handle_start(self, seqno, data, address):  # 对于start消息的处理
        if not address in self.connections:     # 如果地址没有建立过连接，新添加到connections数组
            self.connections[address] = Connection(address[0], address[1], seqno, self.debug)
        conn = self.connections[address]
        ackno, res_data = conn.ack(seqno, data, self.sackMode)  # 获取期待接收的顺序号和收到的数据
        for l in res_data:      # 调用record()函数，把收到的数据写到文件里
            # if self.debug:
            #    print data
            conn.record(l)
        self._send_ack(ackno, address)  # 发ACK

    # ignore packets from uninitiated connections
    def _handle_data(self, seqno, data, address):
        if address in self.connections:
            conn = self.connections[address]
            ackno, res_data = conn.ack(seqno, data, self.sackMode)
            for l in res_data:
                # if self.debug:
                #    print l
                conn.record(l)
            self._send_ack(ackno, address)

    # handle end packets
    def _handle_end(self, seqno, data, address):
        if address in self.connections:
            conn = self.connections[address]
            ackno, res_data = conn.ack(seqno, data, self.sackMode)
            for l in res_data:
                # if self.debug:
                #    print l
                conn.record(l)
            self._send_ack(ackno, address)

    # I'll do the ack-ing here, buddy
    def _handle_ack(self, seqno, data, address):        # 这个应该只是凑数的
        pass

    # handler for packets with unrecognized type
    def _handle_other(self, seqno, data, address):      # debug用，大概
        pass

    def _split_message(self, message):      # 将消息拆分成4个部分
        pieces = message.split('|')
        msg_type, seqno = pieces[0:2]  # first two elements always treated as msg type and seqno
        checksum = pieces[-1]  # last is always treated as checksum
        data = '|'.join(pieces[2:-1])  # everything in between is considered data
        return msg_type, seqno, data, checksum

    def _cleanup(self):     # 定期检查
        if self.debug:
            print("Receiver.py: clean up time")
        now = time.time()       # 更新计时器
        new_connections = self.connections.copy()   # 把连接复制过来
        for address in self.connections.keys():
            conn = self.connections[address]
            if now - conn.updated > self.timeout:       # 检查超时情况，如果超时直接中断该连接
                if self.debug:
                    print("Receiver.py: killed connection to %s (%.2f old)" % (address, now - conn.updated))
                conn.end()
                del new_connections[address]
        self.connections = new_connections  # 更新完后，更新连接
        self.last_cleanup = now     # 更新清理时间


if __name__ == "__main__":
    def usage():
        print("RUDP Receiver")
        print("-p PORT | --port=PORT The listen port, defaults to 33122")
        print("-t TIMEOUT | --timeout=TIMEOUT Receiver timeout in seconds")
        print("-d | --debug Print debug messages")
        print("-h | --help Print this usage message")
        print("-k | --sack Enable selective acknowledgement mode")


    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "p:dt:k", ["port=", "debug=", "timeout=", "sack="])
    except:
        usage()
        exit()

    port = 33122
    debug = False
    timeout = 10
    sackMode = False

    for o, a in opts:
        if o in ("-p", "--port="):
            port = int(a)
        elif o in ("-t", "--timeout="):
            timeout = int(a)
        elif o in ("-d", "--debug="):
            debug = True
        elif o in ("-k", "--sack="):
            sackMode = True
        else:
            usage()
            exit()
    r = Receiver(port, debug, timeout, sackMode)
    r.start()
