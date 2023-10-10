import random

from tests.BasicTest import BasicTest

"""
发送数据包和ACK数据错误测试
修改类型、顺序号、数据和检验和
"""


class CorruptTest(BasicTest):
    def __init__(self, forwarder, input_file):
        super(CorruptTest, self).__init__(forwarder, input_file)

    def handle_packet(self):
        for p in self.forwarder.in_queue:
            choice = random.randint(0,5)
            if choice == 0:
                p.msg_type = 'other'
            elif choice == 1:
                p.seqno = random.randint(0,100)
            elif choice == 2:
                p.data = 'These data are corrupted!!!'
            elif choice == 3:
                p.checksum = 114514
            else:       # 1/3概率正确
                pass
            self.forwarder.out_queue.append(p)

        # empty out the in_queue
        self.forwarder.in_queue = []

    def start(self):
        pass
