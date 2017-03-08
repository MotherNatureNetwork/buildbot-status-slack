import time
import warnings
import json
from distutils.version import LooseVersion
import requests

from future.utils import iteritems
from twisted.internet import defer
from twisted.internet.protocol import ProcessProtocol
from twisted.python import log

from buildbot.process.results import EXCEPTION
from buildbot.process.results import FAILURE
from buildbot.process.results import RETRY
from buildbot.process.results import SUCCESS
from buildbot.process.results import WARNINGS
from buildbot.process.results import SKIPPED
from buildbot.process.results import CANCELLED
from buildbot.process.results import Results
from buildbot.reporters import utils
from buildbot.util import service


class SlackStatusPush(service.BuildbotService):
    name = "SlackStatusPush"

    def reconfigService(self, endpoint=None):
        self.endpoint = endpoint

    @defer.inlineCallbacks
    def startService(self):
        yield service.BuildbotService.startService(self)
        startConsuming = self.master.mq.startConsuming
        self._buildCompleteConsumer = yield startConsuming(
            self.buildStarted,
            ('builds', None, 'finished'))

        self._buildStartedConsumer = yield startConsuming(
            self.buildStarted,
            ('builds', None, 'new'))

    def stopService(self):
        self._buildCompleteConsumer.stopConsuming()
        self._buildStartedConsumer.stopConsuming()

    @defer.inlineCallbacks
    def buildStarted(self, key, build):
        yield self.getBuildDetails(build)

        msg, color = self.createStatusString(build)
        payload = {
            "username": "buildbot",
            "attachments": [
                {
                    "color": color,
                    "text": msg,
                    "mrkdwn_in": ["text"]
                }
            ]
        }

        log.msg(build)
        yield requests.post(self.endpoint, json=payload)

    @defer.inlineCallbacks
    def buildComplete(self, key, build):
        yield self.getBuildDetails(build)

    @defer.inlineCallbacks
    def getBuildDetails(self, build):
        br = yield self.master.data.get(("buildrequests", build['buildrequestid']))
        buildset = yield self.master.data.get(("buildsets", br['buildsetid']))
        yield utils.getDetailsForBuilds(self.master, buildset, [build], wantProperties=True)

    def createStatusString(self, build):
        state = ('unknown', 'good')
        if build['complete']:
            state = {
                SUCCESS: ('success', 'good'),
                WARNINGS: ('success', 'good'),
                FAILURE: ('failure', 'danger'),
                SKIPPED: ('success', 'good'),
                EXCEPTION: ('error', 'danger'),
                RETRY: ('pending', 'warning'),
                CANCELLED: ('error', 'danger')
            }.get(build['results'], ('error', 'danger'))

        build_date = build['started_at'].strftime('%x %X')
        if build['complete']:
            build_date = build['complete_at'].strftime('%x %X')

        msg = '{} build for {} on {}.'.format(build['state_string'], build['builder']['name'], build_date)
        if build['complete']:
            msg += ' Build ended in {}'.format(state[0])
        return msg, state[1]
