#!/usr/bin/env python3

import argparse
import json
import pprint

class DiffAction(argparse.Action):
    """Execute the diff action"""

    def __call__(self, parser, namespace, values, option_string=None):
        diff = TemplateDiff(values[0], values[1])
        print('Removed fields')
        pprint.pprint(diff.removed_fields)
        print('Added fields')
        pprint.pprint(diff.added_fields)
        print('Removed data')
        pprint.pprint(diff.removed_data)
        print('Added data')
        pprint.pprint(diff.added_data)
        print('Changed data')
        pprint.pprint(diff.changed_data)
        print('Order changes')
        pprint.pprint(diff.order_changes)

class PprintAction(argparse.Action):
    """Execute the pprint action"""

    def __call__(self, parser, namespace, values, option_string=None):
        with values as f:
            file_json = json.load(f);
        print(json.dumps(file_json, indent=4))

class CompileAction(argparse.Action):
    """Execute the compile action"""

    def __call__(self, parser, namespace, values, option_string=None):
        with values as f:
            file_json = json.load(f);
        # compile by removing indentation and removing whitespace before and after separators
        print(json.dumps(file_json, separators=(',', ':')))

class TemplateDiff():
    """ Diff between two Tropy templates """

    def __init__(self, from_file, to_file):
        self.removed_fields = {}
        self.added_fields = {}
        self.removed_data = {}
        self.added_data = {}
        self.changed_data = {}
        self.from_properties = []
        self.to_properties = []
        self.order_changes = []
        self.from_fields = self.get_fields(from_file)
        self.to_fields = self.get_fields(to_file)
        self.set_diff()

    def get_fields(self, file):
        with file as f:
            file_json = json.load(f);
        return {field['property']: field for field in file_json['field']}

    def set_diff(self):
        # Get removed fields, removed data, and changed data.
        for property_uri, field in self.from_fields.items():
            self.from_properties.append(property_uri)
            if property_uri not in self.to_fields:
                # Field has been removed.
                self.removed_fields[property_uri] = field
            else:
                for from_key, from_value in field.items():
                    try:
                        to_value = self.to_fields[property_uri][from_key];
                    except KeyError:
                        # Data has been removed.
                        if property_uri not in self.removed_data:
                            self.removed_data[property_uri] = {}
                        self.removed_data[property_uri][from_key] = from_value
                        continue
                    if to_value != from_value:
                        # Data has changed.
                        if property_uri not in self.changed_data:
                            self.changed_data[property_uri] = {}
                        self.changed_data[property_uri][from_key] = (from_value, to_value)
        # Get added fields and added data.
        for property_uri, field in self.to_fields.items():
            self.to_properties.append(property_uri)
            if property_uri not in self.from_fields:
                # Field has been added.
                self.added_fields[property_uri] = field
            else:
                for to_key, to_value in field.items():
                    try:
                        from_value = self.from_fields[property_uri][to_key];
                    except KeyError:
                        # Data has been added.
                        if property_uri not in self.added_data:
                            self.added_data[property_uri] = {}
                        self.added_data[property_uri][to_key] = to_value
        # Get order difference.
        for to_index, property_uri in enumerate(self.to_properties):
            try:
                from_index = self.from_properties.index(property_uri)
            except ValueError:
                from_index = None
            self.order_changes.append((property_uri, None if from_index is None else to_index - from_index))

parser = argparse.ArgumentParser(description='Perform actions on Tropy templates')
subparsers = parser.add_subparsers(help='')

parser_diff = subparsers.add_parser('diff', help='get difference between two templates')
parser_diff.add_argument('filename', nargs=2, type=argparse.FileType('r'), action=DiffAction, help='from filename and to filename')

parser_pprint = subparsers.add_parser('pprint', help='pretty print a template')
parser_pprint.add_argument('filename', type=argparse.FileType('r'), action=PprintAction, help='filename')

parser_compile = subparsers.add_parser('compile', help='compile a template')
parser_compile.add_argument('filename', type=argparse.FileType('r'), action=CompileAction, help='filename')

args = parser.parse_args()
