# coding:utf8

import datetime
import requests
import time
import pymongo

from bs4 import BeautifulSoup
from spider.mongo_db.crawl_ipr_tbl import CrawlIPRData
# crawl_date: 2018-02-01/


#wshz
#  http://ipr.court.gov.cn/zzqhljqwshz/: 著作权和邻接权    http://ipr.court.gov.cn/sbqwshz/：商标权  http://ipr.court.gov.cn/zlqwshz/：专利权  http://ipr.court.gov.cn/zwxpzwshz/：植物新品种
#  http://ipr.court.gov.cn/bzdjzwshz/：不正当竞争   http://ipr.court.gov.cn/jshtwshz/：技术合同   http://ipr.court.gov.cn/ldwshz/：垄断  http://ipr.court.gov.cn/qtwshz/：其他
#  http://ipr.court.gov.cn/zxws/ 最新文书    http://ipr.court.gov.cn/sdjdws/：经典文书
urls = ["zzqhljqwshz","sbqwshz","zlqwshz","zwxpzwshz","bzdjzwshz","jshtwshz","ldwshz","qtwshz","zxws","sdjdws"]

def is_contain_chinese(check_str):
    for ch in check_str.decode('utf-8'):
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False

def crawl_data_once(url, fail_flag, **kwargs):
    try:
        for i in range(0, 3):
            print str(datetime.datetime.now()) + "开始发送网络请求,url是：" + str(url)
            resp = requests.get(url)
            if resp.status_code == 404:
                print "delete"
                return "delete"
            elif resp.status_code != 200:
                print "返回码不是200" + "是：" + str(resp.status_code)
                return fail_flag
            else:
                result = resp.content
                if not is_contain_chinese(result):
                    return fail_flag
                time.sleep(1)
                return result
        return fail_flag
    except Exception, e:
        print e
        return fail_flag

def crawl_data(crawl_url):
    for i in range(1, 10):
        print str(datetime.datetime.now()) + "进行第" + str(i) + "次抓取"
        result = crawl_data_once(crawl_url, False, timeout=20)
        if result != '' and result != False:
            print str(datetime.datetime.now()) + "第" + str(i) + "次抓取成功"
            return result
        print str(datetime.datetime.now()) + "第" + str(i) + "次抓取失败"
    return False

def extract_page(page):
    soup = BeautifulSoup(page, "html5lib")
    wrappers = soup.find("td", class_="zxbian").find("table").find_all("tr")
    for wrapper in wrappers:
        try:
            case_info = wrapper.find_all("td")[1].find("a")
            case_title = case_info["title"]
            case_href = case_info["href"].replace("..", "")
            target_info = {}
            target_info["案件名称"] = case_title
            target_info["caseHref"] = case_href
            target_info["hasDoc"] = False
            target_info["crawlDate"] = datetime.datetime.now().strftime('%Y-%m-%d')
            try:
                CrawlIPRData.ipr_list_insert_one(target_info)
            except pymongo.errors.DuplicateKeyError:
                pass
        except pymongo.errors:
            print "其他异常捕获"
            pass
        except Exception, e:
            print e
            pass



def get_total_page(url):
    while True:
        page = crawl_data(url)
        if page is False:
            continue
        soup = BeautifulSoup(page,"html5lib")
        total_page = soup.find("td",{"class":"zxbian"}).find("script").get_text().split("(")[1].split(",")[0]
        return total_page



def begin_crawl(url):
    print "开始抓取：" + url
    total_page = get_total_page(url)
    print "共" + str(total_page) + "页"
    for i in range(0,int(total_page)):
        print i
        if i == 0:
            result = crawl_data(url + "index.html")
        else:
            result = crawl_data(url + "index_" + str(i) + ".html")
        if result is False:
            break
        extract_page(result)
        print "插入数据库成功"
    print url + " 抓取结束"



if __name__ == "__main__":
    for url in urls:
        begin_crawl("http://ipr.court.gov.cn/" + url + "/")