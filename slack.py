from twisted.internet import defer
from twisted.python import log

from buildbot import config
from buildbot.process.results import statusToString
from buildbot.reporters import utils
from buildbot.reporters.http import HttpStatusPushBase


class SlackStatusPush(HttpStatusPushBase):
    name = "SlackStatusPush"
    neededDetails = dict(wantProperties=True)

    def checkConfig(self, endpoint="https://slack.com", **kwargs):
        if not isinstance(endpoint, basestring):
            config.error('endpoint must be a string')

    @defer.inlineCallbacks
    def reconfigService(self, endpoint="https://slack.com", **kwargs):
        yield HttpStatusPushBase.reconfigService(self, **kwargs)
        self.endpoint = endpoint

    @defer.inlineCallbacks
    def buildStarted(self, key, build):
        yield self.send(build, key[2])

    @defer.inlineCallbacks
    def buildFinished(self, key, build):
        yield self.send(build, key[2])

    @defer.inlineCallbacks
    def getBuildDetailsAndSendMessage(self, build, key):
        yield utils.getDetailsForBuild(self.master, build, **self.neededDetails)
        message = yield self.getMessage(build, key)
        postData = { "text": message }        
        extra_params = yield self.getExtraParams(build, key)
        postData.update(extra_params)
        defer.returnValue(postData)

    def getMessage(self, build, event_name):
        event_messages = {
            'new': 'Buildbot started build %s here: %s' % (build['builder']['name'], build['url']),
            'finished': 'Buildbot finished build %s with result %s here: %s'
                        % (build['builder']['name'], statusToString(build['results']), build['url'])
        }
        return event_messages.get(event_name, '')

    # use this as an extension point to inject extra parameters into your postData
    def getExtraParams(self, build, event_name):
        return {}

    @defer.inlineCallbacks
    def send(self, build, key):
        postData = yield self.getBuildDetailsAndSendMessage(build, key)
        if not postData or 'text' not in postData or not postData['text']:
            return

        response = yield self.session.post(url, postData)
        if response.status_code != 200:
            log.msg("%s: unable to upload status: %s" %
                    (response.status_code, response.content))
