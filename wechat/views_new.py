# -*- coding: utf-8 -*-
# @Time     : 2018/2/28 16:32
# @Author   : woodenrobot

from io import StringIO

import requests
from django.db.models import Q
from lxml import etree
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from wechat.models import Wechat, Topic, Word, Proxy
from wechat.serializers import WechatSerializer, TopicSerializer, WordSerializer


def search_wechat(query):
    p = Proxy.objects.filter(kind=Proxy.KIND_SEARCH, status=Proxy.STATUS_SUCCESS).order_by('?').first()
    if p:
        proxies = {
            'http': 'http://%s:%s' % (p.host, p.port)
        }
    else:
        proxies = {}
    print(proxies)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/41.0.2272.118 Safari/537.36'
    }
    rsp = requests.get("http://weixin.sogou.com/weixin",
                       params={"type": 1, "query": query},
                       proxies=proxies, headers=headers
                       )
    rsp.close()
    rsp.encoding = rsp.apparent_encoding
    # print rsp.content
    htmlparser = etree.HTMLParser()
    tree = etree.parse(StringIO(rsp.text), htmlparser)
    nodes = tree.xpath('//ul[@class="news-list2"]/li')
    wechats = []
    for node in nodes:
        name = ''.join([x for x in node.find(".//p[@class='tit']/a").itertext() if x not in ["red_beg", "red_end"]])
        avatar = node.find(".//div[@class='img-box']/a/img").attrib['src']
        qrcode = node.find(".//div[@class='ew-pop']/span/img").attrib['src']
        wechatid = node.find(".//label[@name='em_weixinhao']").text
        intro_node = node.find(".//dl[1]/dd")
        intro = ''.join([x for x in intro_node.itertext() if x not in ["red_beg", "red_end"]])

        wechats.append({
            "name": name,
            "wechatid": wechatid,
            "avatar": avatar,
            "qrcode": qrcode,
            "intro": intro
        })

    return wechats


class WechatViewSet(viewsets.ModelViewSet):
    queryset = Wechat.objects.all()
    serializer_class = WechatSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def get_queryset(self):
        datas = super().get_queryset()
        status = self.request.query_params.get('status')
        if status:
            datas = datas.filter(status=status)
        return datas

    @detail_route()
    def topic(self, request, *args, **kwargs):
        wechat = self.get_object()
        topics = Topic.objects.filter(wechat=wechat)
        serializers = TopicSerializer(topics, many=True)
        return Response(serializers.data)

    @list_route()
    def search(self, request, *args, **kwargs):
        query = request.GET.get('query')
        wechats = search_wechat(query)
        serializers = WechatSerializer(wechats, many=True)
        return Response(serializers.data, status=status.HTTP_200_OK)


class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def get_queryset(self):
        keywords = self.request.query_params.get('keywords', '')
        order = self.request.query_params.get('order', '-publish_time')
        available = self.request.query_params.get('available')
        q = Q()
        if keywords:
            q.add(Q(title__contains=keywords.strip()), Q.AND)
        if available and available == 1:
            q.add(Q(available='可用'), Q.AND)

        return super().get_queryset().filter(q).order_by(order)


class WordViewSet(viewsets.ModelViewSet):
    queryset = Word.objects.all()
    serializer_class = WordSerializer
    permission_classes = (permissions.IsAuthenticated, )


