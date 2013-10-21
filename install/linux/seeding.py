import sys
import urllib
import urllib2
import json

TAG_NAMES=["Kernel - Process Terminated", "Kernel - Process Killed", "Kernel - Process Started", "Kernel - Process Stopped", "User Logged In", "Invalid User Login attempt", "POSSIBLE BREAK-IN ATTEMPT", "Error"]
TAG_PATTERNS=["/terminated with status 100/", "/Killed process/", "/\/proc\/kmsg started/", "/Kernel logging (proc) stopped/", "/Accepted publickey for/", "/Invalid user/", "/POSSIBLE BREAK-IN ATTEMPT/", "/probe of rtc_cmos failed/"]
EVENT_COLOR=["ff0000", "ff9933", "009900", "663333", "66ff66", "333333", "000099", "0099ff"]
TAG_ID=[]
USER_KEY=""
LOG_KEY=""
# Standard boilerplate to call the main() function to begin
# the program.



def createEvent():
	print "checkTags"
	if accountEventsAlreadyExist():
		print "tags exist"
	else:
		for idx, val in enumerate(TAG_NAMES):
			params = urllib.urlencode ({
				'request':'set_tag',
				'user_key':USER_KEY,
				'tag_id': '',
				'name': TAG_NAMES[idx],
				'title': TAG_NAMES[idx],
				'desc':TAG_NAMES[idx],
				'color':EVENT_COLOR[idx],
				'vtype':'bar'

			})
			response = urllib2.urlopen("http://api.logentries.com", params)
			response_dict = json.loads(response.read())
			print response_dict['tag_id']
			TAG_ID.append(response_dict['tag_id'])
	createTag()


def accountEventsAlreadyExist():
	params = urllib.urlencode ({
		'request':'list_tags',
		'user_key':USER_KEY,
		'id':'init_menu'
	})
	response = urllib2.urlopen("http://api.logentries.com", params)
	response_dict = json.loads(response.read())
	for id in TAG_NAMES:
		for item in response_dict['tags']:
			if item['title'] == id:
				print item['id']
				TAG_ID.append(item['id'])
	if len(TAG_ID) == 0:
		return False
	else:
		return True

def createTag():
	for idx, val in enumerate(TAG_ID):
		params = urllib.urlencode({
			'request':'set_tagfilter',
			'user_key':USER_KEY,
			'log_key': LOG_KEY,
			'name': TAG_NAMES[idx],
			'pattern': TAG_PATTERNS[idx],
			'tags': TAG_ID[idx],
			'tagfilter_key':''

		})
		response = urllib.urlopen("http://api.logentries.com", params)
		print "Creating tag " + TAG_NAMES[idx]
if __name__ == '__main__':
    # Map command line arguments to function arguments.

    if sys.argv[1] == "createEvent":
    	USER_KEY=sys.argv[2]
    	LOG_KEY=sys.argv[3]
    	createEvent()
