import random

from tests.BasicTest import BasicTest

"""
重复发送数据包测试
"""
class DupMessageTest(BasicTest):
    def __init__(self, forwarder, input_file):
        super(DupMessageTest, self).__init__(forwarder, input_file)

    def handle_packet(self):
        for p in self.forwarder.in_queue:
            for i in range(5):
                self.forwarder.out_queue.append(p)


        # empty out the in_queue
        self.forwarder.in_queue = []
