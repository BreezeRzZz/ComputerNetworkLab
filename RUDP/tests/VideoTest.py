import random

from tests.BasicTest import BasicTest

"""
发送图片测试
"""
class VideoTest(BasicTest):
    def __init__(self, forwarder, input_file):
        super(VideoTest, self).__init__(forwarder, input_file)

    def handle_packet(self):
        for p in self.forwarder.in_queue:
            self.forwarder.out_queue.append(p)

        # empty out the in_queue
        self.forwarder.in_queue = []
