# coding:utf8

import datetime
import pymongo
import time

from bs4 import BeautifulSoup
from bson import ObjectId
from spider.mongo_db.crawl_ipr_tbl import CrawlIPRData
from spider.intellectual_property_right.crawl_ipr_list import crawl_data_once

def begin_crawl():
    print "开始处理详情"
    while True:
        try:
            print "————————————————————— 一千条详情开始处理 —————————————————————"
            docs = CrawlIPRData.find_none_doc()
            if docs.count(with_limit_and_skip=True) == 0:
                break
            for doc in docs:
                print str(datetime.datetime.now()) + "开始更新docId是: " + str(doc["_id"]) + "的文书"
                doc_data = crawl_data_once("http://ipr.court.gov.cn" + str(doc["caseHref"]), False, timeout=10)
                time.sleep(4)
                if doc_data == False:
                    continue
                if doc_data == "delete":
                    CrawlIPRData.remove_not_found_data(ObjectId(doc['_id']))
                    print "删除404的数据"
                    continue
                soup = BeautifulSoup(doc_data, 'html5lib')
                text = soup.find("td", id='content').decode_contents(formatter="html")
                if text == "":
                    text = u"文书内容为空"
                CrawlIPRData.update_doc_data(ObjectId(doc['_id']), text)
                print str(datetime.datetime.now()) + "docId是: " + str(doc["_id"]) + "的文书更新完成"
                # time.sleep(0.3)
        except pymongo.errors, e:
            print "捕获mongo异常"
            print e
            continue
        except StandardError, e:
            print "捕获了standard异常"
            print e
            continue
        except Exception, e:
            print e
            continue
    print "抓取详情结束"



if __name__ == "__main__":
    begin_crawl()