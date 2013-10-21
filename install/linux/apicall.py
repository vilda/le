#import json
#import sys

a = {'widgets': [{
            'descriptor_id': 'le.plot-pie-descriptor'
            'options': {
                'title': 'Process activity'
                'tags_to_show': [
                    'Kernel - Process Killed'
                    'Kernel - Process Started'
                    'Kernel - Process Stopped'
                    'Kernel - Process Terminated'
                    ],
                'position': {
                    'width': 1,
                    'height': 1,
                    'row': 1,
                    'column': 1
                    }
                }
            },
            {
            'descriptor_id': 'le.plot-bars',
            'options': {
                'title': 'SSH Access',
                'tags_to_show': [
                    'User Logged In',
                    'Error'
                    ],
                'position': {
                    'width': 1,
                    'height': 1,
                    'row': 1,
                    'column': 1
                    }
                }
            }]
}

#print json.dumps(a)
