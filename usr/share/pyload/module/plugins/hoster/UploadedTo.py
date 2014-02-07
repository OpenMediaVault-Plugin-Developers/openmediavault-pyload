# -*- coding: utf-8 -*-

import re

from module.utils import html_unescape, parseFileSize

from module.plugins.Hoster import Hoster
from module.network.RequestFactory import getURL
from module.plugins.Plugin import chunks
from module.plugins.ReCaptcha import ReCaptcha

key = "bGhGMkllZXByd2VEZnU5Y2NXbHhYVlZ5cEE1bkEzRUw=".decode('base64')

def correctDownloadLink(url):
    url = re.sub("http://.*?/", "http://uploaded.to/",url, 1)
    url = re.sub("\\.to/.*?id=", ".to/file/", url, 1)

    if "/file/" not in url:
        url = url.replace("uploaded.to/", "uploaded.to/file/")

    parts = url.split("/")
    return "/".join(parts[:min(5,len(parts))]) + "/"

def getID(url):
    """ returns id of corrected url"""
    return re.search(r"uploaded.to/file/([^/]+)", url).group(1)

def getAPIData(urls):
        post = {"apikey" : key}

        idMap = {}

        for i, url in enumerate(urls):
            newUrl = correctDownloadLink(url)
            id = getID(newUrl)
            post["id_%s" % i] = id
            idMap[id] = url

        api = unicode(getURL("http://uploaded.to/api/filemultiple", post=post, decode=False), 'iso-8859-1')

        result = {}

        if api:
            for line in api.splitlines():
                data = line.split(",")
                if data[1] in idMap:
                    result[data[1]] = (data[0], data[2], data[4], data[3], idMap[data[1]])

        return result

def parseFileInfo(self, url = '', html = ''):
    if not html and hasattr(self, "html"): html = self.html
    name, size, status, found, fileid = url, 0, 3, None, None

    if re.search(self.FILE_OFFLINE_PATTERN, html):
        # File offline
        status = 1
    else:
        found = re.search(self.FILE_INFO_PATTERN, html)
        if found:
            name, fileid = html_unescape(found.group('N')), found.group('ID')
            size = parseFileSize(found.group('S'))
            status = 2

    return name, size, status, fileid

def getInfo(urls):
    for chunk in chunks(urls, 80):
        result = []

        api = getAPIData(chunk)

        for data in api.itervalues():
            if data[0] == "online":
                result.append((html_unescape(data[2]), data[1], 2, data[4]))

            elif data[0] == "offline":
                result.append((data[4], 0, 1, data[4]))

        yield result


class UploadedTo(Hoster):
    __name__ = "UploadedTo"
    __type__ = "hoster"
    __pattern__ = r"(http://[\w\.-]*?uploaded\.to/.*?(file/|\?id=|&id=)[\w]+/?)|(http://[\w\.]*?ul\.to/(\?id=|&id=)?[\w\-]+/.+)|(http://[\w\.]*?ul\.to/(\?id=|&id=)?[\w\-]+/?)"
    __version__ = "0.53"
    __description__ = """Uploaded.to Download Hoster"""
    __author_name__ = ("spoob", "mkaay")
    __author_mail__ = ("spoob@pyload.org", "mkaay@mkaay.de")

    FILE_INFO_PATTERN = r'<a href="file/(?P<ID>\w+)" id="filename">(?P<N>[^<]+)</a> &nbsp;\s*<small[^>]*>(?P<S>[^<]+)</small>'
    FILE_OFFLINE_PATTERN = r'<small class="cL">Error: 404</small>'

    def setup(self):
        self.html = None
        self.multiDL = False
        self.resumeDownload = False
        self.url = False
        self.chunkLimit = 1 # critical problems with more chunks
        if self.account:
            self.premium = self.account.getAccountInfo(self.user)["premium"]
            if self.premium:
                self.multiDL = True
                self.resumeDownload = True


        self.pyfile.url = correctDownloadLink(self.pyfile.url)
        self.fileID = getID(self.pyfile.url)

    def process(self, pyfile):
        self.req.cj.setCookie("uploaded.to", "lang", "en")

        api = getAPIData([pyfile.url])

        # TODO: fallback to parse from site, because api sometimes delivers wrong status codes

        if not api:
            self.logWarning("No response for API call")

            self.html = unicode(self.load(pyfile.url, decode = False), 'iso-8859-1')
            name, size, status, self.fileID = parseFileInfo(self)
            self.logDebug(name, size, status, self.fileID)
            if status == 1:
                self.offline()
            elif status == 2:
                pyfile.name, pyfile.size = name, size
            else:
                self.fail('Parse error - file info')
        elif api == 'Access denied':
            self.fail(_("API key invalid"))

        else:
            if self.fileID not in api:
                self.offline()

            self.data = api[self.fileID]
            if self.data[0] != "online":
                self.offline()

            pyfile.name = html_unescape(self.data[2])

        # self.pyfile.name = self.get_file_name()

        if self.premium:
            self.handlePremium()
        else:
            self.handleFree()


    def handlePremium(self):
        info = self.account.getAccountInfo(self.user, True)
        self.log.debug("%(name)s: Use Premium Account (%(left)sGB left)" % {"name" :self.__name__, "left" : info["trafficleft"]/1024/1024})
        if int(self.data[1])/1024 > info["trafficleft"]:
            self.log.info(_("%s: Not enough traffic left" % self.__name__))
            self.account.empty(self.user)
            self.resetAccount()
            self.fail(_("Traffic exceeded"))

        self.download("http://uploaded.to/file/%s/ddl" % self.fileID)


    def handleFree(self):
        self.html = self.load(self.pyfile.url, decode=True)

        wait = re.search(r"Current waiting period: <span>(\d+)</span> seconds", self.html).group(1)
        self.setWait(wait)

        js = self.load("http://uploaded.to/js/download.js", decode=True)

        challengeId = re.search(r'Recaptcha\.create\("([^"]+)', js)

        url = "http://uploaded.to/io/ticket/captcha/%s" % self.fileID
        downloadURL = ""

        for i in range(5):
            self.req.lastURL = str(self.url)
            re_captcha = ReCaptcha(self)
            challenge, result = re_captcha.challenge(challengeId.group(1))
            options = {"recaptcha_challenge_field" : challenge, "recaptcha_response_field": result}
            self.wait()

            result = self.load(url, post=options)
            self.logDebug("result: %s" % result)

            if "limit-size" in result:
                self.fail("File too big for free download")
            elif "limit-slot" in result: # Temporary restriction so just wait a bit
                self.setWait(30 * 60, True)
                self.wait()
                self.retry()
            elif "limit-parallel" in result:
                self.fail("Cannot download in parallel")
            elif "limit-dl" in result:
                self.setWait(30 * 60, True)
                self.wait()
                self.retry()
            elif 'err:"captcha"' in result:
                self.invalidCaptcha()
            elif "type:'download'" in result:
                self.correctCaptcha()
                downloadURL = re.search("url:'([^']+)", result).group(1)
                break

        if not downloadURL:
            self.fail("No Download url retrieved/all captcha attempts failed")

        self.download(downloadURL)