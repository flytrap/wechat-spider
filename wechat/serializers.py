# -*- coding: utf-8 -*-
# @Time     : 2018/2/28 10:21
# @Author   : woodenrobot

from rest_framework import serializers

from wechat.models import Wechat, Topic, Word


class WechatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wechat
        fields = (
            'avatar', 'qrcode', 'wechatid', 'intro', 'frequency', 'next_crawl_time', 'create_time',
            'update_time', 'status', 'id', 'name'
                  )


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = (
            'available', 'update_time', 'create_time', 'publish_time', 'like_num', 'read_num', 'source', 'id',
            'content', 'abstract', 'author', 'origin_title', 'title', 'avatar', 'url', 'words', 'unique_id', 'wechat'
                  )


class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = (
            'create_time', 'next_crawl_time', 'frequency', 'intro', 'text', 'kind', 'id'
        )