# -*- coding: utf-8 -*-
from __future__ import with_statement

import re

from module.plugins.Hoster import Hoster
from module.plugins.ReCaptcha import ReCaptcha

from module.common.json_layer import json_loads
from module.network.RequestFactory import getURL
from module.utils import parseFileSize


def getInfo(urls):
    reg = r"<td>(http://(?:www\.)?fileserve\.com/file/.+(?:[\r\n\t]+)?)</td>[\r\n\t ]+<td>(.*?)</td>[\r\n\t ]+<td>(.*?)</td>[\r\n\t ]+<td>(Available|Not available)(?:\&nbsp;)?(?:<img|</td>)"
    url = "http://fileserve.com/link-checker.php"

    #get all at once, shows strange behavior otherwise
    html = getURL(url, post={"submit": "Check Urls", "urls": "\n".join(urls)}, decode=True)

    match = re.findall(reg, html, re.IGNORECASE + re.MULTILINE)

    result = []
    for url, name, size, status in match:
        result.append((name, parseFileSize(size), 1 if status == "Not available" else 2, url))

    yield result


class FileserveCom(Hoster):
    __name__ = "FileserveCom"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?fileserve\.com/file/[a-zA-Z0-9]+"
    __version__ = "0.43"
    __description__ = """Fileserve.Com File Download Hoster"""
    __author_name__ = ("jeix", "mkaay", "paul king")
    __author_mail__ = ("jeix@hasnomail.de", "mkaay@mkaay.de", "")

    FILE_ID_KEY = r"fileserve\.com/file/(?P<id>\w+)"
    FILE_CHECK_KEY = r"<td>http://www.fileserve\.com/file/(?P<id>\w+)</td>.*?<td>(?P<name>.*?)</td>.*?<td>(?P<units>.*?) (?P<scale>.B)</td>.*?<td>(?P<online>.*?)</td>"
    CAPTCHA_KEY_PATTERN = r"var reCAPTCHA_publickey='(?P<key>.*?)';"
    LONG_WAIT_PATTERN = r"You need to wait (\d+) seconds to start another download"

    def init(self):
        if not self.premium:
            self.multiDL = False
            self.resumeDownload = False
            self.chunkLimit = 1

    def process(self, pyfile):
        self.checkFile()
        if self.account and self.premium:
            self.handlePremium()
        else:
            self.handleFree()

    def checkFile(self):
        self.file_id = re.search(self.FILE_ID_KEY, self.pyfile.url).group("id")
        self.logDebug("file id is %s" % self.file_id)

        self.pyfile.url = "http://www.fileserve.com/file/" + self.file_id

        linkCheck = self.load("http://www.fileserve.com/link-checker.php",
                              post={"urls": self.pyfile.url},
                              ref=False, cookies=False if self.account else True, decode=True)

        linkMatch = re.search(self.FILE_CHECK_KEY, linkCheck.replace("\r\n", ""))
        if not linkMatch:
            self.logDebug("couldn't extract file status")
            self.offline()

        if linkMatch.group("online").find("Available"):
            self.logDebug("file is not available : %s" % linkMatch.group("online"))
            self.offline()

        self.pyfile.name = linkMatch.group("name")


    def handlePremium(self):
        # TODO: handle login timeouts
        self.download(self.pyfile.url)

        check = self.checkDownload({"login": '<form action="/login.php" method="POST">'})

        if check == "login":
            self.account.relogin(self.user)
            self.retry(reason=_("Not logged in."))


    def handleFree(self):
        self.html = self.load(self.pyfile.url)
        action = self.load(self.pyfile.url, post={"checkDownload": "check"}, decode=True)
        action = json_loads(action.replace(u"\ufeff", ""))
        self.logDebug("action is : %s" % action)

        if "fail" in action:
            if action["fail"] == "timeLimit":
                html = self.load(self.pyfile.url,
                                 post={"checkDownload": "showError",
                                       "errorType": "timeLimit"},
                                 decode=True)
                wait = re.search(self.LONG_WAIT_PATTERN, html)
                if wait:
                    wait = int(wait.group(1))
                else:
                    wait = 720
                self.setWait(wait, True)
                self.wait()
                self.retry()

            elif action["fail"] == "parallelDownload":
                self.logWarning(_("Parallel download error, now waiting 60s."))
                self.retry(wait_time=60, reason="parallelDownload")

            else:
                self.fail("Download check returned %s" % action["fail"])

        if action["success"] == "showCaptcha":
            self.doCaptcha()
            self.doTimmer()
        elif action["success"] == "showTimmer":
            self.doTimmer()

        # show download link
        response = self.load(self.pyfile.url, post={"downloadLink": "show"}, decode=True)
        self.logDebug("show downloadLink response : %s" % response)
        if not response.find("fail"):
            self.fail("Couldn't retrieve download url")

        # this may either download our file or forward us to an error page
        self.download(self.pyfile.url, post={"download": "normal"})

        check = self.checkDownload({"expired": "Your download link has expired",
                                    "wait": re.compile(self.LONG_WAIT_PATTERN),
                                    "limit": "Your daily download limit has been reached"})

        if check == "expired":
            self.logDebug("Download link was expired")
            self.retry()
        elif check == "wait":
            wait_time = 720
            if self.lastCheck is not None:
                wait_time = int(self.lastCheck.group(1))
            self.setWait(wait_time + 3, True)
            self.wait()
            self.retry()
        elif check == "limit":
            #download limited reached for today (not a exact time known)

            self.setWait(180 * 60, True) # wait 3 hours
            self.wait()
            self.retry(max_tries=0)

        self.thread.m.reconnecting.wait(3) # Ease issue with later downloads appearing to be in parallel

    def doTimmer(self):
        wait = self.load(self.pyfile.url,
                         post={"downloadLink": "wait"},
                         decode=True).replace(u"\ufeff", "") # remove UTF8 BOM
        self.logDebug("wait response : %s" % wait)

        if not wait.find("fail"):
            self.fail("Failed getting wait time")

        self.setWait(int(wait)) # remove UTF8 BOM
        self.wait()

    def doCaptcha(self):
        captcha_key = re.search(self.CAPTCHA_KEY_PATTERN, self.html).group("key")
        recaptcha = ReCaptcha(self)

        for i in range(5):
            challenge, code = recaptcha.challenge(captcha_key)

            response = json_loads(self.load("http://www.fileserve.com/checkReCaptcha.php",
                                            post={'recaptcha_challenge_field': challenge,
                                                  'recaptcha_response_field': code,
                                                  'recaptcha_shortencode_field': self.file_id}).replace(u"\ufeff", ""))
            self.logDebug("reCaptcha response : %s" % response)
            if not response["success"]:
                self.invalidCaptcha()
            else:
                self.correctCaptcha()
                break
     
