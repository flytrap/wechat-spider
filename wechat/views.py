# -*- coding: utf-8 -*-
# __author__ = 'yijingping'

import json
from datetime import datetime
from io import StringIO

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required as django_login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView
from lxml import etree

from wechat.constants import KIND_DETAIL
from wechatspider.util import get_redis, login_required
from .extractors import download_to_oss
from .forms import WechatForm, WechatConfigForm
from .models import Wechat, Topic, Proxy, Word

CRAWLER_CONFIG = settings.CRAWLER_CONFIG

import logging

logging.basicConfig()


class LoginRequiredMixin(object):
    """
    登陆限定，并指定登陆url
    """

    @classmethod
    def as_view(cls, **initkwargs):
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        return django_login_required(view, login_url=settings.LOGIN_URL)


class IndexView(LoginRequiredMixin, ListView):
    model = Wechat
    template_name = 'wechat/index.html'
    context_object_name = 'wechats'
    ordering = ['-update_time']
    paginate_by = 50

    def get_queryset(self):
        datas = super().get_queryset()
        status = self.request.GET.get('status')
        if status:
            datas = datas.filter(status=status)
        return datas

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        r = get_redis()
        # 获取代理状态
        proxies = Proxy.objects.filter(kind=Proxy.KIND_DOWNLOAD, status=Proxy.STATUS_SUCCESS)[:1]
        if len(proxies) > 0:
            dt = datetime.now() - proxies[0].update_time
            _proxy_status = '正常' if dt.total_seconds() < 3600 else '异常'
        else:
            _proxy_status = '异常'
        context.update({
            "active_nav": "wechats",
            "params": self.request.GET,
            "downloader": r.llen(CRAWLER_CONFIG['downloader']) or 0,
            "antispider": r.get(CRAWLER_CONFIG['antispider']) or 0,
            "proxy_status": _proxy_status

        })
        # print(context)
        return context


def add(request):
    if request.method == 'POST':
        form = WechatForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            if settings.OSS2_ENABLE:
                obj.avatar = download_to_oss(obj.avatar, settings.OSS2_CONFIG["IMAGES_PATH"])
                obj.qrcode = download_to_oss(obj.qrcode, settings.OSS2_CONFIG["IMAGES_PATH"])
            obj.save()
            messages.success(request, '保存成功.')
            return redirect(reverse('wechat.index'))
        else:
            messages.error(request, '添加失败,请重试. 错误: %s' % form.errors)
            return redirect(reverse('wechat.index'))


@login_required
def edit(request, id_):
    wechat = get_object_or_404(Wechat, pk=id_)
    if request.method == 'GET':
        context = {}
        # 编辑信息
        form = WechatConfigForm(instance=wechat)
        context.update({
            "active_nav": "wechats",
            "wechat": wechat,
            "form": form
        })
        return render(request, 'wechat/edit.html', context)
    elif request.method == 'POST':
        form = WechatConfigForm(request.POST, instance=wechat)
        if form.is_valid():
            obj = form.save(commit=False)
            if obj.frequency > 0:
                obj.next_crawl_time = datetime.now()
            else:
                print(obj.status)
                if obj.status == Wechat.STATUS_DEFAULT:
                    obj.status = Wechat.STATUS_DISABLE
            obj.save()
            messages.success(request, '保存成功.')
            return redirect(reverse('wechat.edit', kwargs={"id_": id_}))

        else:
            messages.error(request, '保存失败,请重试. 错误: %s' % form.errors)
            return redirect(reverse('wechat.edit', kwargs={"id_": id_}))


@login_required
def wechat_delete(request, id_):
    wechat = get_object_or_404(Wechat, pk=id_)
    wechat.status = Wechat.STATUS_DELETE
    wechat.save()
    next_page = request.GET.get('next')
    return redirect(next_page)


class TopicView(LoginRequiredMixin, ListView):
    model = Topic
    template_name = 'wechat/topic_list.html'
    context_object_name = 'topics'
    paginate_by = 50

    def get_queryset(self):
        keywords = self.request.GET.get('keywords', '')
        order = self.request.GET.get('order', '-publish_time')
        return super().get_queryset().filter(title__contains=keywords.strip()).order_by(order)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        context.update({
            "active_nav": "topics",
            "params": self.request.GET
        })
        return context


class TopicAvailableView(LoginRequiredMixin, ListView):
    model = Topic
    template_name = 'wechat/topic_available_list.html'
    context_object_name = 'topics'
    paginate_by = 50
    ordering = ['-publish_time']

    def get_queryset(self):
        return super().get_queryset().filter(available='可用')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        context.update({
            "active_nav": "topics_available",
            "params": self.request.GET
        })
        return context


class WechatTopicView(LoginRequiredMixin, ListView):
    model = Topic
    template_name = 'wechat/wechat_topics.html'
    context_object_name = "topics"
    paginate_by = 50
    ordering = ['-update_time']

    def get_queryset(self):
        wechat = get_object_or_404(Wechat, pk=self.kwargs.get('id_'))
        self.extra_context = {'wechat': wechat}
        return super().get_queryset().filter(wechat=wechat)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        context.update({
            "active_nav": "wechats",
            "params": self.request.GET
        })
        return context


@csrf_exempt
@login_required
def topic_detail(request, id_):
    topic = get_object_or_404(Topic, pk=id_)
    return render(request, 'wechat/topic_detail.html', context={"topic": topic})


@csrf_exempt
@login_required
def topic_edit(request, id_):
    topic = get_object_or_404(Topic, pk=id_)
    if request.method == 'POST':
        available = request.POST.get('available')
        topic.available = available
        topic.save()
        return JsonResponse({
            'ret': 0,
            'msg': available
        })


@login_required
def topic_add(request):
    url = request.POST.get('url', '')
    if url.startswith('http://mp.weixin.qq.com/') or url.startswith('https://mp.weixin.qq.com/'):
        data = {
            'kind': KIND_DETAIL,
            'url': url
        }

        r = get_redis()
        r.rpush(settings.CRAWLER_CONFIG["downloader"], json.dumps(data))
        messages.success(request, '链接已经提交给爬虫,稍后查看爬取结果.')
    else:
        messages.error(request, 'url 错误, 添加失败')
    return redirect(reverse('wechat.topic_list'))


def search(request):
    query = request.GET.get('query')
    wechats = search_wechat(query)
    return render(request, 'wechat/search_content.html', context={"wechats": wechats})


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


class KeywordsView(LoginRequiredMixin, ListView):
    model = Word
    template_name = 'wechat/keywords_list.html'
    context_object_name = "keywords"
    paginate_by = 50
    ordering = ['-id']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        context.update({
            "active_nav": "keywords",
            "params": self.request.GET
        })
        return context


@csrf_exempt
def proxy_edit(request, id_):
    proxy = get_object_or_404(Proxy, pk=id_)
    if request.method == 'POST':
        print(proxy.host, request.POST['host'])
        print(proxy.port, request.POST['port'])
        if proxy.host != request.POST['host'] or proxy.port != int(request.POST['port']):
            proxy.host = request.POST['host']
            proxy.port = request.POST['port']
            proxy.save()
        return HttpResponse('proxy change success')


@csrf_exempt
def proxy_status(request):
    proxies = Proxy.objects.filter(kind=Proxy.KIND_DOWNLOAD, status=Proxy.STATUS_SUCCESS)[:1]
    if len(proxies) > 0:
        return JsonResponse({
            'ret': 0,
            'update_time': str(proxies[0].update_time),
            'timestamp': int(proxies[0].update_time.strftime('%s'))
        })
    else:
        return JsonResponse({
            'ret': 1,
            'message': '没有有效的下载代理'
        })


# api 接口
def api_search(request):
    query = request.GET.get('query')
    wechats = search_wechat(query)
    print(wechats)
    return JsonResponse({
        'ret': 0,
        'data': wechats
    })


@csrf_exempt
def api_topic_add(request):
    url = request.POST.get('url', '')
    logging.error(url)
    if url.startswith('http://mp.weixin.qq.com/') or url.startswith('https://mp.weixin.qq.com/'):
        data = {
            'kind': KIND_DETAIL,
            'url': url
        }

        r = get_redis()
        r.rpush(settings.CRAWLER_CONFIG["downloader"], json.dumps(data))
        return JsonResponse({
            'ret': 0,
            'message': '提交成功,链接已经提交给爬虫,稍后查看爬取结果'
        })
    else:
        return JsonResponse({
            'ret': 1,
            'message': '提交失败,url必须以 http://mp.weixin.qq.com/ 开头'
        })


@csrf_exempt
def api_add(request):
    if request.method == 'POST':
        P = request.POST
        wechatid = P.get('wechatid')
        frequency = int(P.get('frequency'))
        wechats = search_wechat(wechatid)
        if not wechats:
            return JsonResponse({
                'ret': 1,
                'message': '公众号不存在'
            })
        else:
            info = wechats[0]

        if settings.OSS2_ENABLE:
            avatar = download_to_oss(info.get('avatar'), settings.OSS2_CONFIG["IMAGES_PATH"])
            qrcode = download_to_oss(info.get('qrcode'), settings.OSS2_CONFIG["IMAGES_PATH"])
        else:
            avatar = info.get('avatar')
            qrcode = info.get('qrcode')

        obj, created = Wechat.objects.update_or_create(wechatid=wechatid, defaults={
            'name': info.get('name', ''),
            'intro': info.get('intro', ''),
            'avatar': avatar,
            'qrcode': qrcode,
            'frequency': frequency,
            'next_crawl_time': datetime.now()
        })
        if created:
            return JsonResponse({
                'ret': 0,
                'message': '已添加'
            })
        else:
            return JsonResponse({
                'ret': 0,
                'message': '已更新'
            })
