# -*- coding: utf-8 -*-
# (c) 2008,2014-2017 Andreas Motl <andreas.motl@elmyra.de>
import re
import sys


def decodeMatchToDict(match, key_suffix):
    result = {}

    if match:
        # transfer data from match groups to instance variable,
        # making all values uppercase
        for key, value in match.groupdict().iteritems():
            if key.endswith(key_suffix):
                key = key.replace(key_suffix, '')
                if value:
                    value = value.upper()
                result[key] = value

    return result


class IpcDecoder:
    raw = ''
    ipc = {}

    #PATTERN = '([A-Z])(\d\d)([A-Z])\s+(\d+)/(\d+)'
    #PATTERN = '([A-Z])(\d\d)?([A-Z])?\s*(?:(\d+))?(?:[/-](\d+))?'

    # remarks for example "C09D 163/00", also vice-versa "H01L0021677000"
    PATTERN = """
    (?P<section__1>[A-Z])         # C
    (?P<class__1>\d{1,2})?        # 09
    (?P<subclass__1>[A-Z])?       # D
    [\s]*                         # "suppress leading spaces before 'ipcr group'"
    (?:(?P<group__1>\d{1,4}))?    # 163
    (?:
        [/-]?                     # /
        (?P<subgroup__1>\d{1,6})  # 00
    )?
    """
    r = re.compile(PATTERN, re.IGNORECASE | re.VERBOSE)

    partnames = ['section', 'class', 'subclass', 'group', 'subgroup']

    def __init__(self, ipc_string='', ipc_dict={}):
        if ipc_string:
            self.raw = ipc_string
            self.decode()
            self.fix()
        elif ipc_dict:
            self.ipc = ipc_dict
            #self.fix()

    def decode(self):
        m = self.r.match(self.raw)
        self.ipc = decodeMatchToDict(m, '__1')
        if not self.ipc:
            raise ValueError, "IPCR class '%s' could not be decoded" % self.raw

    def fix(self):

        # add leading zeros to class
        #if self.ipc['class']:
        #    self.ipc['class'] = "%02d" % int(self.ipc['class'])

        # strip all leading zeros from group
        if self.ipc['group']:
            self.ipc['group'] = re.sub('^0*(\d+)', '\\1', self.ipc['group'])

        # strip trailing zeros from subgroup, but leave two digits even when zeros
        # => don't manipulate too much!
        if self.ipc['subgroup']:
            self.ipc['subgroup'] = re.sub('(\d\d+?)0*$', '\\1', self.ipc['subgroup'])

    def __str__(self):
        return str(self.ipc)

    def asDict(self):
        return self.ipc


    def formatFlexible(self, class_padding='', group_subgroup_delimiter='', group_padding='', subgroup_padding=''):
        if not self.ipc['section']:
            raise ValueError, "IPCR class '%s' could not be formatted" % self.raw

        ipc_serialized = self.ipc['section']

        if self.ipc['class']:
            ipc_serialized += self._pad_class(self.ipc['class'], class_padding)

        if self.ipc['subclass']:
            ipc_serialized += self.ipc['subclass']

            if self.ipc['group']:
                ipc_serialized += self._pad_group(self.ipc['group'], group_padding)

                if self.ipc['subgroup']:
                    ipc_serialized += group_subgroup_delimiter + self._pad_subgroup(self.ipc['subgroup'],
                        subgroup_padding)

        return ipc_serialized.upper()

    def formatDOCDB(self):
        return self.formatFlexible(group_subgroup_delimiter='/', group_padding=' ', subgroup_padding=' ')

    def formatIPCR(self):
        return self.formatFlexible(group_subgroup_delimiter='', group_padding='0', subgroup_padding='0')

    def formatLucene(self):
        return self.formatFlexible(group_subgroup_delimiter='', group_padding='0', subgroup_padding='')

    def formatOPS(self):
        return self.formatFlexible(class_padding='0', group_subgroup_delimiter='/', group_padding='', subgroup_padding='')

    def formatIPCR_EndOfRange(self):
        # pre-initialize empty group or subgroup
        if not self.ipc['group']:
            self.ipc['group'] = '9999'
        if not self.ipc['subgroup']:
            self.ipc['subgroup'] = '999999'

        # call with different subgroup_padding
        return self.formatFlexible(group_subgroup_delimiter='', group_padding='0', subgroup_padding='9')


    def _pad_class(self, value, padding):
        value = value.strip()
        value = padding * (2 - len(value)) + value
        return value

    def _pad_group(self, value, padding):
        value = value.strip()
        value = padding * (4 - len(value)) + value
        return value

    def _pad_subgroup(self, value, padding):
        value = value.strip()
        value = value + padding * (6 - len(value))
        return value


    def join(self, delimiter):
        list = []
        for part in self.partnames:
            list.append(self.ipc[part])
        return delimiter.join(list)

    @classmethod
    def getempty(cls):
        data = {}
        for partname in cls.partnames:
            data[partname] = None
        return data
