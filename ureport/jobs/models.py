from django.conf import settings
from django.core.cache import cache
import feedparser
import HTMLParser

from dash.orgs.models import Org
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.html import strip_tags

from smartmin.models import SmartModel

RSS_JOBS_FEED_CACHE_TIME = getattr(settings, 'RSS_JOBS_FEED_CACHE_TIME', 60 * 60 * 6)
RSS_JOBS_KEY = 'jobsource:%d:%d'

class JobSource(SmartModel):
    TWITTER = 'T'
    FACEBOOK = 'F'
    RSS = 'R'
    SOURCE_TYPES = ((TWITTER, 'Twitter'), (FACEBOOK, 'Facebook'), (RSS, 'RSS'))

    title = models.CharField(max_length=100, help_text=_("The title or name to reference this Job source."))
    source_type = models.CharField(max_length=1, choices=SOURCE_TYPES,
                                   help_text=_("Choose the type for the Job source. Twitter, Facebook or RSS feed"))
    source_url = models.URLField(help_text=_("The full URL to navigate to this Job source."))
    widget_id = models.CharField(max_length=50, blank=True, null=True,
                                 help_text=_("For Twitter, a widget Id is required to embed tweets on the website. "
                                             "Read carefully the instructions above on how to get the right widget Id"))
    is_featured = models.BooleanField(default=False,
                                      help_text=_("Featured job sources are shown first on the jobs page."))
    org = models.ForeignKey(Org,
                            help_text=_("The organization this job source is for"))

    def __unicode__(self):
        return self.title

    def get_feed(self, reload=False):
        if self.source_type != JobSource.RSS:
            return None

        key = RSS_JOBS_KEY % (self.org.id, self.id)

        if not reload:
            cache_value = cache.get(key)

            if cache_value is not None:
                return cache_value

        feed = feedparser.parse(self.source_url)
        cache.set(key, dict(entries=feed['entries']), RSS_JOBS_FEED_CACHE_TIME)

        return feed

    def get_entries(self):
        entries = []

        try:
            feed = self.get_feed()
            entries = feed['entries']
        except Exception as e:
            # clear the cache so we try again
            key = RSS_JOBS_KEY % (self.org.id, self.id)
            cache.delete(key)
            pass

        html_parser = HTMLParser.HTMLParser()
        for entry in entries:
            summary = entry['summary']
            entry['summary'] = strip_tags(html_parser.unescape(html_parser.unescape(summary)))
        return entries

    def get_return_page(self):
        if self.source_type in [JobSource.FACEBOOK, JobSource.TWITTER]:
            return self.source_url
        return '/'.join(self.source_url.split('/')[:3])

    def get_username(self):
        if self.source_type in [JobSource.FACEBOOK, JobSource.TWITTER]:
            return self.source_url.split('/')[3]
        return None
