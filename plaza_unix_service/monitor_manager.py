import threading
import logging
import os
import json
import re
import time

FREQ_RE = re.compile('^(\d+)([smhd])$')
SUFFIX_TO_SEC_MULTIPLIER = {
    's': 1,
    'm': 60,
    'h': 60 * 60,
    'd': 60 * 60 * 24
}

def parse_freq(s_freq):
    m = FREQ_RE.match(s_freq)
    return int(m.group(1)) * SUFFIX_TO_SEC_MULTIPLIER[m.group(2)]

class MonitorManager(threading.Thread):
    def __init__(self, block, unix_service):
        threading.Thread.__init__(self)
        self.id = block["id"]
        self.unix_service = unix_service
        self.block = block

    def run(self):
        freq = parse_freq(self.block.get('frequency', '1m'))
        logging.info("[{}] Running {} every {} seconds".format(self.block["id"],
                                                               self.block["command"],
                                                               freq))
        logging.debug("[{}] 5 seconds for startup".format(self.block["id"]))
        time.sleep(5)
        while True:
            result = self.unix_service.run_block(self.block, (), None).strip()

            logging.debug("[{}] Result: {}".format(self.block["id"],
                                                  result))
            self.process(result)
            time.sleep(freq)

    def process(self, buff):
        try:
            data = json.loads(buff)
        except:
            data = buff

        self.unix_service.emit_event(self.id, data)
