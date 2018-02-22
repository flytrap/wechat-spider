# -*- coding: utf-8 -*-
# __author__ = 'yijingping'
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta

import django
from django.conf import settings

# 加载django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'wechatspider.settings'
django.setup()

from wechat.constants import KIND_NORMAL, KIND_KEYWORD
from wechat.models import Wechat, Word
from wechatspider.util import get_redis



logger = logging.getLogger()


class Scheduler(object):
    def run(self):
        r = get_redis()
        if settings.CRAWLER_DEBUG:
            r.delete(settings.CRAWLER_CONFIG["downloader"])

        while True:
            now = datetime.now()
            # 获取要抓取的公众号
            wechats = Wechat.objects.filter(frequency__gt=0, next_crawl_time__lt=now,
                                            status=Wechat.STATUS_DEFAULT).order_by('-id')
            for item in wechats:
                data = {
                    'kind': KIND_NORMAL,
                    'wechat_id': item.id,
                    'wechatid': item.wechatid
                }

                r.lpush(settings.CRAWLER_CONFIG["downloader"], json.dumps(data))

                # 更新index_rule
                item.next_crawl_time = now + timedelta(minutes=item.frequency)
                # item.next_crawl_time = now + timedelta(seconds=item.frequency)
                item.save()

                logging.debug(data)

            # 获取要抓取的关键词
            keywords = Word.objects.filter(frequency__gt=0, next_crawl_time__lt=now).order_by('-id')
            for item in keywords:
                data = {
                    'kind': KIND_KEYWORD,
                    'word': item.text
                }

                r.lpush(settings.CRAWLER_CONFIG["downloader"], json.dumps(data))

                # 更新index_rule
                item.next_crawl_time = now + timedelta(minutes=item.frequency)
                # item.next_crawl_time = now + timedelta(seconds=item.frequency)
                item.save()

                logging.debug(data)

            time.sleep(1)


if __name__ == '__main__':
    scheduler = Scheduler()
    scheduler.run()
