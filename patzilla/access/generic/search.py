# -*- coding: utf-8 -*-
# (c) 2015-2018 Andreas Motl <andreas.motl@ip-tools.org>
import time
import logging
from pprint import pprint
from collections import defaultdict
from patzilla.util.data.container import SmartBunch
from patzilla.util.numbers.normalize import normalize_patent
from patzilla.access.generic.exceptions import SearchException

log = logging.getLogger(__name__)

class GenericSearchClient(object):

    def lm(self, message):
        message = u'{backend_name}: {message}'.format(message=message, **self.__dict__)
        return message

    def search_failed(self, message=None, response=None, user_info=None, ex=None, meta=None):

        # Compute user info
        user_info = user_info or u'Search failed with unknown reason, please report this error to us.'
        meta = meta or {}

        # Compute reason and status
        message = message or u'unknown'
        if ex:
            message = u'{}: {}'.format(ex.__class__.__name__, ex.message)

        # Compute and emit log message
        log_message = u'{backend_name}: Search failed. message={message}'.format(message=message, **self.__dict__)
        if meta:
            log_message += u', meta=' + unicode(meta)
        if response:
            status = unicode(response.status_code) + u' ' + response.reason
            log_message += u', status={status}, response=\n{response}'.format(status=status, response=response.content.decode('utf-8'))
        log.error(log_message)

        # Return exception object
        return SearchException(message, user_info=user_info)

    def crawl(self, constituents, expression, chunksize):

        if constituents not in ['pub-number', 'biblio']:
            raise ValueError('constituents "{0}" invalid or not implemented yet'.format(constituents))

        real_constituents = constituents
        if constituents == 'pub-number':
            constituents = ''

        # fetch first chunk (1-chunksize) from upstream
        #first_chunk = self.search(expression, 0, chunksize)
        first_chunk = self.search_method(expression, SmartBunch({'offset': 0, 'limit': chunksize}))
        #print first_chunk

        #total_count = int(first_chunk['meta'].get('pager', {}).get('totalEntries', 0))
        count_total = first_chunk.meta.navigator.count_total
        log.info(self.lm('Crawl count_total: {}'.format(count_total)))

        # Limit maximum size
        count_total = min(count_total, self.crawl_max_count)

        """
        # SIP:
        pointer_total_count = JsonPointer('/meta/MemCount')
        total_count = int(pointer_total_count.resolve(first_chunk))
        log.info('SipClient.crawl total_count: %s', total_count)

        # Limit maximum size
        # TODO: make configurable, put into instance variable
        count_total = min(count_total, 5000)
        """

        # collect upstream results
        begin_second_chunk = chunksize
        chunks = [first_chunk]
        log.info(self.lm('Crawling {count_total} items with {chunksize} per request'.format(
            count_total=count_total, chunksize=chunksize)))
        for offset in range(begin_second_chunk, count_total, chunksize):

            # Don't hammer the upstream data source
            time.sleep(1)

            log.info(self.lm('Crawling from offset {offset}'.format(offset=offset)))
            chunk = self.search_method(expression, SmartBunch({'offset': offset, 'limit': chunksize}))
            chunks.append(chunk)


        # Merge chunks into single result
        all_numbers = []
        all_details = []
        # TODO: summarize elapsed_time
        for chunk in chunks:
            #print 'chunk:', chunk
            all_numbers += chunk['numbers']
            all_details += chunk['details']


        # Report about result
        result_count = len(all_details)
        log.info(self.lm('Crawling finished. result count: {result_count}'.format(result_count=result_count)))


        # Bulk response
        response = None
        if real_constituents == 'pub-number':
            response = first_chunk
            response['meta'] = {'Success': 'true', 'MemCount': str(len(all_numbers))}
            response['numbers'] = all_numbers
            del response['details']

        elif real_constituents == 'biblio':
            response = first_chunk
            #print 'all_details:', all_details
            response['meta'] = {'Success': 'true', 'MemCount': str(len(all_numbers))}
            response['details'] = all_details
            #del response['details']

        if not response:
            raise ValueError('constituents "{0}" invalid or not implemented yet'.format(constituents))

        return response


class GenericSearchResponse(object):

    def __init__(self, input, options=None):

        # Input data and options
        self.input = input
        self.options = options and SmartBunch.bunchify(options) or SmartBunch()

        # Setup data structures
        self.setup()

        # Read input information
        self.read()

        # Run data munging actions
        if 'feature_family_remove' in self.options and self.options.feature_family_remove:
            self.remove_family_members()

    def setup(self):

        # Documents from upstream data source
        self.documents = []

        # Metadata information, upstream (raw) and downstream (unified)
        self.meta = SmartBunch.bunchify({
            'navigator': {},
            'upstream': {},
        })

        # Output information, upstream (raw) and downstream (unified)
        self.output = SmartBunch.bunchify({
            'meta': {},
            'numbers': [],
            'details': [],
            'navigator': {},
        })

    def read_documents(self):
        for document in self.documents:
            try:
                number = self.document_to_number(document)
            except (KeyError, TypeError):
                number = None

            # Whether kindcodes should be fixed on number normalization
            normalize_fix_kindcode = 'normalize_fix_kindcode' in self.options and self.options.normalize_fix_kindcode

            # Apply number normalization
            # TODO: Check how we can decouple from "for_ops=True" here
            number_normalized = normalize_patent(number, fix_kindcode=normalize_fix_kindcode, for_ops=True)

            # Be graceful if this didn't work
            if number_normalized:
                number = number_normalized

            document[u'publication_number'] = number
            document[u'upstream_provider'] = self.meta.upstream.name

    def render(self):

        if True or self.meta.navigator.count_total:
            self.output.meta = self.meta
            self.output.numbers = self.get_numberlist()
            self.output.details = self.get_entries()

        return self.output

    def get_entries(self):
        return self.documents

    def get_length(self):
        return len(self.get_entries())

    def get_numberlist(self):
        numbers = []
        for result in self.get_entries():
            number = result['publication_number']
            numbers.append(number)
        return numbers


    def remove_family_members(self):

        # Filtering mechanics: Deduplicate by family id
        seen = {}
        removed = []
        removed_map = defaultdict(list)
        stats = SmartBunch(removed = 0)
        def family_remover(item):

            fam = self.document_to_family_id(item)

            # Sanity checks on family id
            # Do not remove documents without valid family id
            if not fam or fam in [u'0', u'-1']:
                return True

            # "Seen" filtering logic
            if fam in seen:
                stats.removed += 1
                removed.append(item)
                removed_map[fam].append(item)
                return False
            else:
                seen[fam] = True
                #print 'representative: {rep} [{fam}]'.format(rep=item['publication_number'], fam=fam)
                return True

        # Update metadata and content

        # 1. Apply family cleansing filter to main documents response
        self.documents = filter(family_remover, self.documents)
        #print 'removed_map:'; pprint(removed_map)

        # 2. Add list of removed family members to output
        self.output.navigator.family_members = {'removed': removed}
        #self.output['family-members-removed'] = removed

        # 3. Update metadata
        self.meta.navigator.postprocess.action = 'feature_family_remove'
        self.meta.navigator.postprocess.info   = stats
