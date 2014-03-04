import sys
import urllib2

try:
	import json
except ImportError:
	try:
		import simplejson
	except ImportError:
		print 'Please install json or simplejson python module'
		sys.exit(0)

TAG_NAMES=['Kernel  Process Terminated', 'Kernel - Process Killed', 'Kernel - Process Started', 'Kernel - Process Stopped', 'User Logged In', 'Invalid User Login attempt', 'POSSIBLE BREAK-IN ATTEMPT', 'Error']
TAG_PATTERNS=['/terminated with status 100/', '/Killed process/', '/\/proc\/kmsg started/', '/Kernel logging (proc) stopped/', '/Accepted publickey for/', '/Invalid user/', '/POSSIBLE BREAK-IN ATTEMPT/', '/probe of rtc_cmos failed/']
EVENT_COLOR=['ff0000', 'ff9933', '009900', '663333', '66ff66', '333333', '000099', '0099ff']
TAG_ID=[]
USER_KEY=''
LOG_KEY=''
# Standard boilerplate to call the main() function to begin
# the program.



def createLabel(name, color):
	request = {
		'name': name,
		'title': name,
		'description': ' ',
		'appearance': {
			'color': color
		},
		'request': 'create',
		'account': USER_KEY,
		'acl': USER_KEY
	}
	req = urllib2.Request('https://api.logentries.com/v2/tags')
	req.add_header('Content-Type','application/json')
	response = urllib2.urlopen(req, json.dumps(request))
	response_dict = json.loads(response.read())
	return response_dict['sn']

def createTagAction(label_id):
	request = {
			'type': 'tagit',
			'rate_count': 0,
			'rate_range': 'day',
			'limit_count': 0,
			'limit_range': 'day',
			'schedule': [],
			'type': 'tagit',
			'args': {
				'sn': label_id,
				'tag_sn': label_id
			},
			'request': 'create',
			'account': USER_KEY,
			'acl': USER_KEY
		}
	req = urllib2.Request('https://api.logentries.com/v2/actions')
	req.add_header('Content-Type', 'application/json')
	response = urllib2.urlopen(req, json.dumps(request))
	response_dict = json.loads(response.read())
	return response_dict['id']


def createHerokuSeedData():
	for idx, val in enumerate(TAG_NAMES):
		label_id = createLabel(TAG_NAMES[idx], EVENT_COLOR[idx])
		tagActionId = createTagAction(label_id)
		createHook(TAG_NAMES[idx], TAG_PATTERNS[idx], tagActionId)

def createHook(name, trigger, tagId):
	request = {
		'name': name,
		'triggers': [
			trigger
		],
		'sources': [
			LOG_KEY
		],
		'groups': [],
		'actions': [
			tagId
		],
		'request': 'create',
		'account': USER_KEY,
		'acl': USER_KEY
	}
	req = urllib2.Request('https://api.logentries.com/v2/hooks')
	req.add_header('Content-Type', 'application/json')
	response = urllib2.urlopen(req, json.dumps(request))
	response_dict = json.loads(response.read())
	print response_dict['status']

if __name__ == '__main__':
	# Map command line arguments to function arguments.

	if sys.argv[1] == 'createEvent':
		USER_KEY=sys.argv[2]
		LOG_KEY=sys.argv[3]
		createHerokuSeedData()
