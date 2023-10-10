import random

from tests.BasicTest import BasicTest

"""
End Test
"""
class EndTest(BasicTest):
    def __init__(self, forwarder, input_file):
        super(EndTest, self).__init__(forwarder, input_file)
        self.count = 0

    def handle_packet(self):
        for p in self.forwarder.in_queue:
            if p.msg_type == 'end' and self.count <= 10:
                self.count += 1
            else:
                self.forwarder.out_queue.append(p)

        # empty out the in_queue
        self.forwarder.in_queue = []
