# -*- coding: utf-8 -*-

from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster

class RehostTo(MultiHoster):
    __name__ = "RehostTo"
    __version__ = "0.4"
    __type__ = "hook"

    __config__ = [("activated", "bool", "Activated", "False")]

    __description__ = """rehost.to hook plugin"""
    __author_name__ = ("RaNaN")
    __author_mail__ = ("RaNaN@pyload.org")

    replacements = [("freakshare.net", "freakshare.com")]

    def getHoster(self):

        page = getURL("http://rehost.to/api.php?cmd=get_supported_och_dl&long_ses=%s" % self.long_ses)
        return [x.strip() for x in page.replace("\"", "").split(",")]


    def coreReady(self):

        self.account = self.core.accountManager.loadClass("accounts", "RehostTo")

        user = self.account.selectAccount()[0]

        if not user:
            self.log.error("Rehost.to: "+ _("Please add your rehost.to account first and restart pyLoad"))
            return

        data = self.account.getAccountInfo(user)
        self.ses = data["ses"]
        self.long_ses = data["long_ses"]

        return MultiHoster.coreReady(self)
