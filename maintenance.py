#!/usr/bin/env python

# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Example of using the Compute Engine API to watch for maintenance notices.

For more information, see the README.md under /compute.
"""

# [START all]

import argparse
import time

import requests

from subprocess import call

parser = argparse.ArgumentParser()

parser.add_argument("-o",
                    "--options",
                    dest = "options",
                    default = "",
                    help = "Additional options to pass into asinfo. Can be anything except commands, ie: \"-v $COMMAND\". Entire string must be quoted, eg: -o=\"-u admin -p admin\"")

args = parser.parse_args()

print args.options

METADATA_URL = 'http://metadata.google.internal/computeMetadata/v1/'
METADATA_HEADERS = {'Metadata-Flavor': 'Google'}
ASINFO = "/usr/bin/asinfo"


def wait_for_maintenance(callback):
    url = METADATA_URL + 'instance/maintenance-event'
    last_maintenance_event = None
    # [START hanging_get]
    last_etag = '0'

    while True:
        r = requests.get(
            url,
            params={'last_etag': last_etag, 'wait_for_change': True},
            headers=METADATA_HEADERS)

        # During maintenance the service can return a 503, so these should
        # be retried.
        if r.status_code == 503:
            time.sleep(1)
            continue
        # Any other response from metadata service will kill this script
        r.raise_for_status()

        last_etag = r.headers['etag']
        # [END hanging_get]

        if r.text == 'NONE':
            maintenance_event = None
        else:
            # Possible events:
            #   MIGRATE_ON_HOST_MAINTENANCE: instance will be migrated
            #   TERMINATE_ON_HOST_MAINTENANCE: instance will be shut down
            maintenance_event = r.text

        if maintenance_event != last_maintenance_event:
            last_maintenance_event = maintenance_event
            callback(maintenance_event)


def maintenance_callback(event):
    if event:
        # print('Undergoing host maintenance: {}'.format(event))
        # realistically, any sort of maintenence event should drain aerospike
        call([ASINFO, "-v", "quiesce:"].extend(args.options.split()))
    else:
        # print('Finished host maintenance')
        call([ASINFO, "-v", "quiesce-undo:"].extend(args.options.split()))


def main():
    wait_for_maintenance(maintenance_callback)


if __name__ == '__main__':
    main()
# [END all]
