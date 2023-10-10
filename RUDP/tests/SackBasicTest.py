import random

from tests.BasicTest import BasicTest

"""
重复发送测试
"""
class SackBasicTest(BasicTest):
    def __init__(self, forwarder, input_file):
        super(SackBasicTest, self).__init__(forwarder, input_file,sackMode = True)

    def handle_packet(self):
        for p in self.forwarder.in_queue:
            self.forwarder.out_queue.append(p)

        # empty out the in_queue
        self.forwarder.in_queue = []
