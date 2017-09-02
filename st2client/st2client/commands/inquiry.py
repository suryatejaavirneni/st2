# Licensed to the StackStorm, Inc ('StackStorm') under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging

from st2client.commands import resource
from st2client.formatters import table
from st2client.models.inquiry import Inquiry

LOG = logging.getLogger(__name__)

DEFAULT_SCOPE = 'system'


class InquiryBranch(resource.ResourceBranch):

    def __init__(self, description, app, subparsers, parent_parser=None):
        super(InquiryBranch, self).__init__(
            Inquiry, description, app, subparsers,
            parent_parser=parent_parser,
            commands={
                'list': InquiryListCommand,
                'get': InquiryGetCommand
            })

        # Registers extended commands
        self.commands['respond'] = InquiryRespondCommand(self.resource, self.app,
                                                         self.subparsers)

        # Remove unsupported commands
        # TODO: Refactor parent class and make it nicer
        del self.commands['create']
        del self.commands['update']


class InquiryListCommand(resource.ResourceCommand):

    # Omitting "schema" and "response", as it doesn't really show up in a table well.
    # The user can drill into a specific Inquiry to get this
    display_attributes = [
        'id',
        'parent',
        'roles',
        'users',
        'tag',
        'ttl'
    ]

    def __init__(self, resource, *args, **kwargs):

        self.default_limit = 20

        super(InquiryListCommand, self).__init__(
            resource, 'list', 'Get the list of the %s most recent %s.' %
            (self.default_limit, resource.get_plural_display_name().lower()),
            *args, **kwargs)

        self.resource_name = resource.get_plural_display_name().lower()
        self.parser.add_argument('-n', '--last', type=int, dest='last',
                                 default=self.default_limit,
                                 help=('List N most recent %s.' % self.resource_name))

        # Display options
        self.parser.add_argument('-a', '--attr', nargs='+',
                                 default=self.display_attributes,
                                 help=('List of attributes to include in the '
                                       'output. "all" will return all '
                                       'attributes.'))
        self.parser.add_argument('-w', '--width', nargs='+', type=int,
                                 default=None,
                                 help=('Set the width of columns in output.'))

    @resource.add_auth_token_to_kwargs_from_cli
    def run(self, args, **kwargs):
        return self.manager.query_with_count(limit=args.last, **kwargs)

    def run_and_print(self, args, **kwargs):
        instances, count = self.run(args, **kwargs)

        self.print_output(reversed(instances), table.MultiColumnTable,
                          attributes=args.attr, widths=args.width,
                          json=args.json,
                          yaml=args.yaml)


class InquiryGetCommand(resource.ResourceGetCommand):
    pk_argument_name = 'id'
    display_attributes = ['id', 'parent', 'roles', 'users', 'tag', 'ttl', 'schema']

    def __init__(self, kv_resource, *args, **kwargs):
        super(InquiryGetCommand, self).__init__(kv_resource, *args, **kwargs)

    @resource.add_auth_token_to_kwargs_from_cli
    def run(self, args, **kwargs):
        resource_name = getattr(args, self.pk_argument_name, None)
        return self.get_resource_by_id(id=resource_name, **kwargs)


class InquiryRespondCommand(resource.ResourceCommand):
    display_attributes = ['id', 'response']

    def __init__(self, resource, *args, **kwargs):
        super(InquiryRespondCommand, self).__init__(
            resource, 'respond',
            'Respond to an %s.' % resource.get_display_name().lower(),
            *args, **kwargs
        )

        self.parser.add_argument('id',
                                 metavar='id',
                                 help='Inquiry ID')
        self.parser.add_argument('response',
                                 metavar='response',
                                 help='response body (json)')

    @resource.add_auth_token_to_kwargs_from_cli
    def run(self, args, **kwargs):
        instance = Inquiry()
        instance.id = args.id
        instance.response = json.loads(args.response)

        return self.manager.update(instance, **kwargs)

    def run_and_print(self, args, **kwargs):
        instance = self.run(args, **kwargs)
        self.print_output(instance, table.PropertyValueTable,
                          attributes=self.display_attributes, json=args.json,
                          yaml=args.yaml)