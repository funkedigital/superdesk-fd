# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

import datetime
import logging
import lxml.html
import html
import requests
import re
import superdesk

from flask import current_app as app
from superdesk.errors import ParserError
from superdesk.io.registry import register_feed_parser
from superdesk.io.feed_parsers import XMLFeedParser
from superdesk.media.renditions import update_renditions
from superdesk.metadata.item import ITEM_TYPE, CONTENT_TYPE, GUID_FIELD
from superdesk.metadata.utils import is_normal_package
from superdesk.utc import utc
from lxml import etree
from superdesk.io.feeding_services.rss import RSSFeedingService, generate_tag_from_url

logger = logging.getLogger(__name__)


class SpotonFeedParser(XMLFeedParser):
    """ Feed Parser for SpotOn """

    NAME = 'spoton'

    label = 'SpotOn Parser'

    def can_parse(self, xml):
        return xml.tag == 'NewsML'

    def parse(self, xml, provider=None):
        items = {'associations': {}}
         
        try:
            self.parse_metadata(items, xml)
            self.parse_content(items, xml)
            return items
        except Exception as ex:
            logger.info(ex)
    
    def parse_metadata(self, items, xml):
        meta_elements = self.parse_elements(xml.find('Meta'))

        author = [{
                    'name':  meta_elements.get('Author', ''),
                    'role': 'writer',
                    'avatar_url': 'https://api.adorable.io/avatars/285/abott@adorable.png'
            }]
        items['author'] = author
        
        if meta_elements.get('Revision') != None:
            items['version'] = int(meta_elements.get('Revision'))

        if meta_elements.get('Priority') != None:
            items['priority'] = int(meta_elements.get('Priority'))

        items['format'] = meta_elements.get('Format', 'html')

        items['type'] = meta_elements.get('Type', 'text')

        keywords_elem = xml.find('Meta/Keywords')
        keywords = []
        if len(keywords_elem) > 0:
            for k in keywords_elem:
                keywords.append(k.text)
        items['keywords'] = keywords

        revision_created = meta_elements.get('RevisionCreated', '')
        if len(revision_created) > 0:
            items['versioncreated'] = self.datetime(revision_created)

    def parse_content(self, items, xml):
        pass


    def parse_elements(self, tree):
        parsed = {}
        for item in tree:
            # read the value for the items
            parsed[item.tag] = item.text
        # remove empty objects
        parsed = {k: '' if not v else v for k, v in parsed.items()}
        return parsed

    def datetime(self, string):
        # Escenic datetime format from CE(S)T
        local_dt = datetime.datetime.strptime(string, '%a, %d %b %Y %H:%M:%S %z')
        return local_dt

register_feed_parser(SpotonFeedParser.NAME, SpotonFeedParser())