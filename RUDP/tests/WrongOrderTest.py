import random

from tests.BasicTest import BasicTest

"""
乱序到达测试
将in_queue随机排序
"""
class WrongOrderTest(BasicTest):
    def __init__(self, forwarder, input_file):
        super(WrongOrderTest, self).__init__(forwarder, input_file)

    def handle_packet(self):
        if len(self.forwarder.in_queue) >= 5:
            random.shuffle(self.forwarder.in_queue)
            for p in self.forwarder.in_queue:
                self.forwarder.out_queue.append(p)

            # empty out the in_queue
            self.forwarder.in_queue = []
