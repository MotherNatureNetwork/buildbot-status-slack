from twisted.internet import defer
from twisted.python import log

from buildbot import config
from buildbot.process.results import statusToString
from buildbot.reporters import utils
from buildbot.reporters.http import HttpStatusPushBase
import json

class SlackStatusPush(service.BuildbotService):
    neededDetails = dict()

    def checkConfig(self, *args, **kwargs):
        service.BuildbotService.checkConfig(self)
        if not isinstance(kwargs.get('builders'), (type(None), list)):
            config.error("builders must be a list or None")

    @defer.inlineCallbacks
    def reconfigService(self, builders=None, **kwargs):
        yield service.BuildbotService.reconfigService(self)
        self.builders = builders
        self.endpoint = kwargs.get('endpoint')
        for k, v in iteritems(kwargs):
            if k.startswith("want"):
                self.neededDetails[k] = v

    @defer.inlineCallbacks
    def startService(self):
        yield service.BuildbotService.startService(self)

        startConsuming = self.master.mq.startConsuming
        self._buildCompleteConsumer = yield startConsuming(
            self.buildFinished,
            ('builds', None, 'finished'))

        self._buildStartedConsumer = yield startConsuming(
            self.buildStarted,
            ('builds', None, 'new'))

    def stopService(self):
        self._buildCompleteConsumer.stopConsuming()
        self._buildStartedConsumer.stopConsuming()

    def buildStarted(self, key, build):
        return self.getMoreInfoAndSend(build)

    def buildFinished(self, key, build):
        return self.getMoreInfoAndSend(build)

    def filterBuilds(self, build):
        if self.builders is not None:
            return build['builder']['name'] in self.builders
        return True

    @defer.inlineCallbacks
    def getMoreInfoAndSend(self, build):
        yield utils.getDetailsForBuild(self.master, build, **self.neededDetails)
        yield self.send(build)

    @abc.abstractmethod
    def send(self, build):
        requests.post(self.endpoint, data=json.dumps(build))
