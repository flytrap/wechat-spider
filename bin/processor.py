# -*- coding: utf-8 -*-
# __author__ = 'yijingping'

import json
import logging
import os
import sys

import django
# from django.utils.encoding import smart_str, smart_unicode
from django.conf import settings

# 加载django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'wechatspider.settings'
django.setup()

from wechat.models import Topic
from wechat.processors import DjangoModelBackend
from wechatspider.util import get_redis


logger = logging.getLogger()


class Processor():
    def __init__(self):
        self.pools = {}

    def get_backends(self):
        backend = DjangoModelBackend(Topic)
        return [backend]

    def process(self, data):
        backends = self.get_backends()
        for backend in backends:
            backend.process(data)

    def run(self):
        r = get_redis()
        if settings.CRAWLER_DEBUG:
            r.delete(settings.CRAWLER_CONFIG["processor"])
        while True:
            try:
                rsp = r.brpop(settings.CRAWLER_CONFIG["processor"])
            except Exception as e:
                print(e)
                continue

            data = json.loads(rsp[1])
            logger.info(json.dumps(data, ensure_ascii=False))
            self.process(data)


if __name__ == '__main__':
    processor = Processor()
    processor.run()
