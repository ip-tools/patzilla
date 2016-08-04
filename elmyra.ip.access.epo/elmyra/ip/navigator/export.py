# -*- coding: utf-8 -*-
# (c) 2016 Andreas Motl, Elmyra UG
import os
import json
import types
import string
import logging
import pandas
import numpy
import html2text
from io import BytesIO
from textwrap import dedent
from lxml import etree as ET
from bunch import bunchify, Bunch
from json.encoder import JSONEncoder
from zipfile import ZipFile, ZIP_DEFLATED
from collections import OrderedDict
from xlsxwriter.worksheet import Worksheet
from elmyra.ip.access.epo.core import pdf_universal_multi
from elmyra.ip.access.epo.ops import ops_description, get_ops_biblio_data, ops_register, ops_claims, ops_family_inpadoc
from elmyra.ip.access.generic.exceptions import ignored
from elmyra.ip.util.date import humanize_date_english
from elmyra.ip.util.numbers.common import decode_patent_number, encode_epodoc_number
from elmyra.ip.util.python import exception_traceback

log = logging.getLogger(__name__)

class Dossier(object):

    summary_template = dedent(u"""
        Summary

        The research about »{project_name}«
        started on {project_created} and was
        most recently updated on {project_modified}.

        {queries_count} search queries were conducted
        across {datasource_count} data sources ({datasource_list})
        and yielded {total_search_count} hits in total.

        {total_review_count} documents were reviewed:
            {rated_count} documents have been rated, {dismissed_count} have been dismissed and
            {seen_count} documents were visited without putting any rating on them.

        {comments_count} comments were made.
        """).strip()

    def __init__(self, data):
        self.data = bunchify(data)
        self.prepare_dataframes()
        self.make_metadata()

    def make_metadata(self):

        self.metadata = ReportMetadata()

        # Project metadata
        self.metadata.set('project_name',     self.data.project.name)
        self.metadata.set('project_created',  humanize_date_english(self.data.project.created))
        self.metadata.set('project_modified', humanize_date_english(self.data.project.modified))
        if 'user' in self.data and self.data.user:
            if 'fullname' in self.data.user:
                self.metadata.set('author_name',  self.data.user.fullname)
            if 'username' in self.data.user:
                self.metadata.set('author_email', self.data.user.username)

        # Project-associated metadata
        self.metadata.set('queries_count',    len(self.data.project.queries))
        self.metadata.set('comments_count',   len(self.data.comments))

        # Collection metadata
        self.metadata.set('rated_count',      len(self.data.collections.rated))
        self.metadata.set('dismissed_count',  len(self.data.collections.dismissed))
        self.metadata.set('seen_count',       len(self.data.collections.seen))

        # Unique list of data sources
        datasources = list(self.df_queries.datasource.unique())
        self.metadata.set('datasource_list', ', '.join(datasources))
        self.metadata.set('datasource_count', len(datasources))

        # Totals
        self.metadata.set('total_search_count', int(self.df_queries.hits.sum()))
        self.metadata.set('total_review_count',
            self.metadata['rated_count'] + self.metadata['dismissed_count'] + self.metadata['seen_count'])

        #print 'metadata:'; pprint(self.metadata)

    def prepare_dataframes(self):

        # Main DataFrame for aggregating sub results
        self.df_documents = pandas.DataFrame()

        # Aggregate all results
        for collection_name in ['rated', 'dismissed', 'seen']:

            # Wrap entries into DataFrame
            entries = self.data.collections[collection_name]
            df = pandas.DataFrame(entries, columns=['number', 'score', 'dismiss', 'seen', 'timestamp', 'url'])
            df.rename(columns={'number': 'document'}, inplace=True)

            # Aggregate all DateFrame items
            self.df_documents = self.df_documents.append(df)

        # Amend "NaN" boolean values to "False"
        self.df_documents['seen'].fillna(value=False, inplace=True)
        self.df_documents['dismiss'].fillna(value=False, inplace=True)

        # Cast to boolean type
        self.df_documents['seen']      = self.df_documents['seen'].astype('bool')
        self.df_documents['dismiss']   = self.df_documents['dismiss'].astype('bool')


        # Queries
        queries = map(self.query_criteria_smoother, self.data.get('queries', []))
        self.df_queries = pandas.DataFrame(queries, columns=['criteria', 'query_expression', 'result_count', 'datasource', 'created'])
        self.df_queries.rename(columns={'query_expression': 'expression', 'result_count': 'hits', 'created': 'timestamp'}, inplace=True)


        # Comments
        self.df_comments = pandas.DataFrame(self.data.get('comments'), columns=['parent', 'text', 'modified'])
        self.df_comments.rename(columns={'parent': 'document', 'text': 'comment', 'modified': 'timestamp'}, inplace=True)


    @staticmethod
    def query_criteria_smoother(entry):
        criteria = entry.get('query_data', {}).get('criteria')
        entry['criteria'] = json.dumps(criteria)
        try:
            entry['result_count'] = int(entry['result_count'])
        except:
            pass
        return entry

    def format_with_metadata(self, template):
        return string.Formatter().vformat(template, (), self.metadata)

    def generate_with_metadata(self, template, **more_kwargs):
        metadata = self.metadata.copy()
        metadata.update(more_kwargs)
        formatter = EmphasizingFormatterGenerator()
        return formatter.vgenerate(template, (), metadata)

    def get_summary(self):
        output = self.format_with_metadata(self.summary_template)
        return output

    def get_author(self):
        return self.format_with_metadata(u'Author: {author_name} <{author_email}>\nCreated: {project_created}\nUpdated: {project_modified}')

    @staticmethod
    def to_csv(dataframe):
        # Serialize as CSV
        buffer = BytesIO()
        dataframe.to_csv(buffer, index=False)
        payload = buffer.getvalue()
        return payload

    @staticmethod
    def to_json(dataframe):
        return json.dumps(dataframe.to_dict(), indent=4, cls=PandasJSONEncoder)
        return dataframe.to_json()

    def to_zip(self, options=None):
        """
         u'options': {u'media': {u'biblio': False,
                                 u'claims': False,
                                 u'description': False,
                                 u'pdf': True,
                                 u'register': False},
                      u'report': {u'csv': True,
                                  u'json': True,
                                  u'pdf': False,
                                  u'xlsx': False}},
        """

        # TODO: Text representations for biblio, register, family
        # TODO: PDF Extracts

        options = options or bunchify({'report': {}, 'media': {}})
        filtered = self.df_documents[(self.df_documents.seen == False)]
        documents = list(filtered.document)

        buffer = BytesIO()
        with ZipFile(buffer, 'w', ZIP_DEFLATED) as zipfile:

            # FIXME
            #zipfile.writestr('readme.txt', 'Intentionally left blank.')

            # Add text summary
            zipfile.writestr('@metadata.txt', self.get_author().encode('utf-8'))
            zipfile.writestr('@summary.txt', self.get_summary().encode('utf-8'))

            # Report files
            # ------------

            # Add Workbook
            if options.report.xlsx:
                zipfile.writestr('report/@dossier.xlsx', DossierXlsx(self.data).create())

            # Add CSV
            if options.report.csv:
                zipfile.writestr('report/csv/01-queries.csv', self.to_csv(self.df_queries))
                zipfile.writestr('report/csv/02-documents.csv', self.to_csv(self.df_documents))
                zipfile.writestr('report/csv/03-comments.csv', self.to_csv(self.df_comments))

            # Add JSON
            if options.report.json:
                zipfile.writestr('report/json/01-queries.json', self.to_json(self.df_queries))
                zipfile.writestr('report/json/02-documents.json', self.to_json(self.df_documents))
                zipfile.writestr('report/json/03-comments.json', self.to_json(self.df_comments))


            # Media files
            # -----------

            # Add full PDF documents
            if options.media.pdf:
                pdf_universal_multi(zipfile, documents, path='media/pdf')

            # Add XML data
            # TODO: Add @report.txt for reflecting missing documents, differentiate between different XML kinds.
            # TODO: Add more TEXT formats (.abstract.txt, .biblio.txt, .register.txt)
            status = OrderedDict()
            for document in documents:

                status.setdefault(document, OrderedDict())

                # Add XML "bibliographic" data (full-cycle)
                if options.media.biblio:
                    try:
                        biblio_payload = get_ops_biblio_data(document, True)
                        zipfile.writestr('media/xml/{document}.biblio.xml'.format(document=document), biblio_payload)
                        status[document]['biblio'] = True
                    except:
                        log.warning('Could not fetch XML bibliographic data for {document}. Exception:\n{trace}'.format(document=document, trace=exception_traceback()))
                        status[document]['biblio'] = False

                # Add XML "description" full text data
                if options.media.description:
                    try:
                        # Write XML
                        document_number = encode_epodoc_number(decode_patent_number(document))
                        description_payload = ops_description(document_number, True)
                        zipfile.writestr('media/xml/{document}.description.xml'.format(document=document), description_payload)
                        status[document]['description'] = True

                        # Write TEXT
                        with ignored():
                            text_payload = self.get_fulltext(description_payload, 'description')
                            if text_payload:
                                zipfile.writestr('media/txt/{document}.description.txt'.format(document=document), text_payload)

                    except:
                        log.warning('Could not fetch XML description data for {document}. Exception:\n{trace}'.format(document=document, trace=exception_traceback()))
                        status[document]['description'] = False

                # Add XML "claims" full text data
                if options.media.claims:
                    try:
                        # Write XML
                        document_number = encode_epodoc_number(decode_patent_number(document))
                        claims_payload = ops_claims(document_number, True)
                        zipfile.writestr('media/xml/{document}.claims.xml'.format(document=document), claims_payload)
                        status[document]['claims'] = True

                        # Write TEXT
                        with ignored():
                            text_payload = self.get_fulltext(claims_payload.replace('<claim-text>', '<p>').replace('</claim-text>', '</p>'), 'claims')
                            if text_payload:
                                zipfile.writestr('media/txt/{document}.claims.txt'.format(document=document), text_payload)

                    except:
                        log.warning('Could not fetch XML claims data for {document}. Exception:\n{trace}'.format(document=document, trace=exception_traceback()))
                        status[document]['claims'] = False

                # Add XML register data
                if options.media.register:
                    try:
                        document_number = encode_epodoc_number(decode_patent_number(document))
                        register_payload = ops_register('publication', document_number, 'biblio', True)
                        zipfile.writestr('media/xml/{document}.register.xml'.format(document=document), register_payload)
                        status[document]['register'] = True
                    except:
                        log.warning('Could not fetch XML register data for {document}. Exception:\n{trace}'.format(document=document, trace=exception_traceback()))
                        status[document]['register'] = False


                # Add XML family data
                if options.media.family:
                    try:
                        document_number = encode_epodoc_number(decode_patent_number(document), {'nokind': True})
                        family_payload = ops_family_inpadoc('publication', document_number, 'biblio', True)
                        zipfile.writestr('media/xml/{document}.family.xml'.format(document=document), family_payload)
                        status[document]['family'] = True
                    except:
                        log.warning('Could not fetch XML family data for {document}. Exception:\n{trace}'.format(document=document, trace=exception_traceback()))
                        status[document]['family'] = False


            #print '====== status:'; pprint(status)

            # TODO: Format more professionally incl. generator description
            # TODO: Unify with "pdf_universal_multi"

            # Generate report
            delivered_items = []
            missing_items = []
            for document, kinds in status.iteritems():
                delivered = []
                missing = []
                for kind, ok in kinds.iteritems():
                    if ok:
                        delivered.append(kind)
                    else:
                        missing.append(kind)

                if delivered:
                    item = u'{document:20}{delivered}'.format(document=document, delivered=u', '.join(delivered))
                    delivered_items.append(item)
                if missing:
                    item = u'{document:20}{missing}'.format(document=document, missing=u', '.join(missing))
                    missing_items.append(item)

            if delivered_items or missing_items:

                report_template = dedent("""
                Delivered files ({delivered_count}):
                {delivered_files}

                Missing files ({missing_count}):
                {missing_files}
                """).strip()

                report = report_template.format(
                    delivered_count=len(delivered_items),
                    missing_count=len(missing_items),
                    delivered_files='\n'.join(delivered_items),
                    missing_files='\n'.join(missing_items),
                )
                log.info('Export report:\n{report}'.format(report=report))
                zipfile.writestr('media/xml/@report.txt', report)

        payload = buffer.getvalue()

        return payload

    @staticmethod
    def get_fulltext(payload, what):

        xpath_lang = '/ops:world-patent-data/ftxt:fulltext-documents/ftxt:fulltext-document/ftxt:{what}/@lang'.format(what=what)
        xpath_content = '/ops:world-patent-data/ftxt:fulltext-documents/ftxt:fulltext-document/ftxt:{what}'.format(what=what)
        namespaces = {'ops': 'http://ops.epo.org', 'ftxt': 'http://www.epo.org/fulltext'}

        tree = ET.parse(BytesIO(payload))
        #print 'tree:'; pprint(tree)

        lang = tree.xpath(xpath_lang, namespaces=namespaces)
        #print 'lang:', lang

        elements = tree.xpath(xpath_content, namespaces=namespaces)
        if elements:
            return html2text.html2text(ET.tostring(elements[0]))


class PandasJSONEncoder(JSONEncoder):

    def default(self, o):
        """Implement this method in a subclass such that it returns
        a serializable object for ``o``, or calls the base implementation
        (to raise a ``TypeError``).

        For example, to support arbitrary iterators, you could
        implement default like this::

            def default(self, o):
                try:
                    iterable = iter(o)
                except TypeError:
                    pass
                else:
                    return list(iterable)
                # Let the base class default method raise the TypeError
                return JSONEncoder.default(self, o)

        """
        if isinstance(o, (numpy.bool_,)):
            return bool(o)

        raise TypeError(repr(o) + " is not JSON serializable")

class DossierXlsx(Dossier):

    def __init__(self, data):
        super(DossierXlsx, self).__init__(data)
        self.writer = pandas.ExcelWriter('temp.xlsx', engine='xlsxwriter')
        self.workbook = self.writer.book
        add_worksheet_monkeypatch(self.workbook)

        self.format_wrap_top = self.workbook.add_format()
        self.format_wrap_top.set_text_wrap()
        self.format_wrap_top.set_align('top')

        self.format_small_font = self.workbook.add_format({'align': 'vcenter', 'font_size': 9})
        self.format_small_font_align_top = self.workbook.add_format({'align': 'top', 'font_size': 9})

    def create(self):

        # A memory buffer as ExcelWriter storage backend
        buffer = BytesIO()
        self.workbook.filename = buffer

        # Create "cover" sheet
        self.write_cover_sheet()

        # Create "queries" sheet
        self.write_queries_sheet()

        # Create numberlist sheets
        self.write_numberlist_sheets()

        # Create "comments" sheet
        self.write_comments_sheet()

        # Save/persist ExcelWriter model
        self.writer.save()

        # Get hold of buffer content
        payload = buffer.getvalue()
        return payload

    def set_header_footer(self, worksheet):
        # http://xlsxwriter.readthedocs.io/example_headers_footers.html
        header = u'&LElmyra IP Suite Navigator&RSearch report'
        worksheet.set_header(header)
        footer = u'&L&L&D &T&C&A&RPage &P of &N'
        worksheet.set_footer(footer)

    def write_cover_sheet(self):

        # TODO: Histogram of data source distribution
        """
        metadata_value_map = {}
        for key, value in metadata.iteritems():
            metadata_value_map[key] = value['value']
        """

        cover_sheet = self.workbook.add_worksheet('cover')
        self.set_header_footer(cover_sheet)

        title = u'Dossier »{name}«'.format(name=self.data.project.name)
        title_format = self.workbook.add_format({'align': 'center', 'valign': 'vcenter', 'font_size': 17, 'bold': True})
        cover_sheet.merge_range('A1:I2', title, title_format)

        subtitle = self.get_author()
        subtitle_format = self.workbook.add_format({'align': 'left', 'valign': 'vcenter', 'indent': 2, 'top': 7, 'bottom': 7})
        cover_sheet.merge_range('B4:H7', subtitle, subtitle_format)

        # http://xlsxwriter.readthedocs.io/example_merge_rich.html
        red = self.workbook.add_format({'color': 'red'})
        blue = self.workbook.add_format({'color': 'blue'})
        cell_format = self.workbook.add_format({'align': 'left', 'valign': 'vcenter', 'indent': 2, 'top': 7, 'bottom': 7})
        cover_sheet.merge_range('B10:H28', "", cell_format)


        footnote_format = self.workbook.add_format({'font_size': 9})
        footnote = dedent(u"""
        Please have a look at the other worksheets in
        this workbook for more detailed information about
        all queries, comments and document numbers
        aggregated throughout the research process.
        """).strip()

        summary = self.generate_with_metadata(self.summary_template, emphasis=blue)

        args = list(summary) + ['\n'] + [footnote_format, u'\n\n' + footnote]
        args.append(cell_format)
        cover_sheet.write_rich_string('B10', *args)

        """
        metadata_row = 20
        for key, entry in metadata.iteritems():
            report_sheet.write(metadata_row, 0, entry['label'])
            report_sheet.write(metadata_row, 1, entry['value'])
            metadata_row += 1
        """

    def write_numberlist_sheets(self):
        sheets = OrderedDict()
        sheets['rated']     = self.data.get('collections', {}).get('rated')
        sheets['dismissed'] = self.data.get('collections', {}).get('dismissed')
        sheets['seen']      = self.data.get('collections', {}).get('seen')
        for sheet_name, entries in sheets.iteritems():

            #print 'entries:'; pprint(entries)

            if entries:
                first = entries[0]
            else:
                first = {}

            # Create pandas DataFrame
            if type(first) in types.StringTypes:
                df = pandas.DataFrame(entries, columns=['PN'])

            elif isinstance(first, (types.DictionaryType, Bunch)):
                df = pandas.DataFrame(entries, columns=['number', 'score', 'timestamp', 'url'])
                df.rename(columns={'number': 'document', 'url': 'display'}, inplace=True)

            # Export DataFrame to Excel
            df.to_excel(self.writer, sheet_name=sheet_name, index=False)

            # Set column widths
            wks = self.worksheet_set_column_widths(sheet_name, 18, 10, 19, 18)
            wks.set_column('C:C', width=19, cell_format=self.format_small_font)
            self.set_header_footer(wks)

    def write_queries_sheet(self):

        # TODO: Add direct url links to queries

        self.df_queries.to_excel(self.writer, sheet_name='queries', index=False)
        wks = self.worksheet_set_column_widths('queries', 35, 35, 8, 10, 19, cell_format=self.format_wrap_top)
        wks.set_landscape()
        wks.set_column('E:E', width=19, cell_format=self.format_small_font_align_top)
        wks.set_default_row(height=50)
        wks.set_row(0, height=16)
        self.set_header_footer(wks)

        #self.autofit_height(wks, df.comment, default=default_row_height)
        #inch = 2.54  # centimeters
        #wks.set_margins(left=1.0/inch, right=1.0/inch, top=1.0/inch, bottom=1.0/inch)

    def write_comments_sheet(self):
        self.df_comments.to_excel(self.writer, sheet_name='comments', index=False)

        #format_vcenter = self.workbook.add_format({'align': 'vcenter'})
        #wks.set_row(0, cell_format=format_vcenter)

        wks = self.worksheet_set_column_widths('comments', 18, 68, 19, cell_format=self.format_wrap_top)
        wks.set_column('C:C', width=19, cell_format=self.format_small_font_align_top)
        wks.set_landscape()
        self.set_header_footer(wks)

        default_row_height = 50
        wks.set_default_row(height=default_row_height)
        wks.set_row(0, height=16)

        self.autofit_height(wks, self.df_comments.comment, default=default_row_height)

        #ws.set_column('B:B', width=70, cell_format=format_wrap)
        #ws.set_column('A:C', cell_format=format_wrap)

    def autofit_height(self, wks, items, default=16):
        font_size_estimated = 11
        line_height_estimated = font_size_estimated / 10
        for index, content in enumerate(items):
            newline_count = content.count('\n') + 2
            row_height = (font_size_estimated + line_height_estimated) * newline_count
            row_height = max(row_height, default)
            wks.set_row(index + 1, height=row_height)

    def worksheet_set_column_widths(self, sheet_name, *widths, **kwargs):

        #format_wrap = self.writer.book.add_format()
        #format_wrap.set_text_wrap()

        if 'cell_format' in kwargs:
            cell_format = kwargs['cell_format']
        else:
            cell_format = self.writer.book.add_format()
            #cell_format.set_text_wrap()
            cell_format.set_align('vcenter')

        # Set column widths
        worksheet = self.writer.sheets[sheet_name]
        for index, width in enumerate(widths):
            colname = chr(65 + index)
            colrange = '{0}:{0}'.format(colname)

            worksheet.set_column(colrange, width=width, cell_format=cell_format)
            #worksheet.set_column(colrange, width=width, cell_format=format_wrap)

        return worksheet


class ReportMetadata(OrderedDict):

    def set(self, key, value):
        self[key] = value

    # https://stackoverflow.com/questions/17215400/python-format-string-unused-named-arguments/17215533#17215533
    def __missing__(self, key):
        return u'n/a'


# Machinery for monkeypatching XlsxWriter's Worksheet's ``write_url`` method
# to deduce a link title from the url automatically using ``os.path.basename(url)``.

# Save vanilla method
Worksheet.write_url_dist = Worksheet.write_url

def write_url_deduce_title(self, row, col, url, cell_format=None, string=None, tip=None):
    if string is None:
        string = os.path.basename(url)
    if tip is None:
        tip = 'Open "{name}" in Patent Navigator'.format(name=string)
    return self.write_url_dist(row, col, url, cell_format=cell_format, string=string, tip=tip)

def workbook_add_sheet_hook(self, name=None):
    worksheet = self._add_sheet(name, is_chartsheet=False)
    # Patch "write_url" function
    worksheet.write_url = lambda *args, **kwargs: write_url_deduce_title(worksheet, *args, **kwargs)
    return worksheet

def add_worksheet_monkeypatch(workbook):
    workbook.add_worksheet = lambda *args, **kwargs: workbook_add_sheet_hook(workbook, *args, **kwargs)



class EmphasizingFormatterGenerator(string.Formatter):

    def vgenerate(self, format_string, args, kwargs):
        used_args = set()
        result = self._vgenerate(format_string, args, kwargs, used_args, 2)
        self.check_unused_args(used_args, args, kwargs)
        return result

    def _vgenerate(self, format_string, args, kwargs, used_args, recursion_depth):
        if recursion_depth < 0:
            raise ValueError('Max string recursion exceeded')

        for literal_text, field_name, format_spec, conversion in\
        self.parse(format_string):

            # output the literal text
            if literal_text:
                yield literal_text

            # if there's a field, output it
            if field_name is not None:
                # this is some markup, find the object and do
                #  the formatting

                # given the field_name, find the object it references
                #  and the argument it came from
                obj, arg_used = self.get_field(field_name, args, kwargs)
                used_args.add(arg_used)

                # do any conversion on the resulting object
                obj = self.convert_field(obj, conversion)

                # expand the format spec, if needed
                format_spec = self._vformat(format_spec, args, kwargs,
                    used_args, recursion_depth-1)

                # format the object and append to the result
                if 'emphasis' in kwargs:
                    yield kwargs['emphasis']

                yield self.format_field(obj, format_spec)

