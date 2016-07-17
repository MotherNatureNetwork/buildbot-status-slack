import re

from twisted.internet import defer
from twisted.python import log

from buildbot.process.properties import Interpolate
from buildbot.process.properties import Properties
from buildbot.process.results import CANCELLED
from buildbot.process.results import EXCEPTION
from buildbot.process.results import FAILURE
from buildbot.process.results import RETRY
from buildbot.process.results import SKIPPED
from buildbot.process.results import SUCCESS
from buildbot.process.results import WARNINGS
from buildbot.reporters import http


class SlackStatusPush(http.HttpStatusPushBase):
    name = "SlackStatusPush"
    neededDetails = dict(wantProperties=True)

    def checkConfig(self, endpoint, **kwargs):
        HttpStatusPushBase.checkConfig(self, **kwargs)
        if not baseUrl:
            config.error("BaseURL cannot be empty")

    @defer.inlineCallbacks
    def reconfigService(self, endpoint=None, **kwargs):
        yield http.HttpStatusPushBase.reconfigService(self, **kwargs)
        self.endpoint = endpoint

    @defer.inlineCallbacks
    def send(self, build):
        response = yield self.session.post(self.endpoint, json=build)
        if response.status_code != 200:
            log.msg("%s: unable to upload status: %s" %
                    (response.status_code, response.content))
            