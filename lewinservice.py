# winservice.py
# code adapted from http://code.activestate.com/recipes/551780/

from os.path import splitext, abspath
from sys import modules
import win32event
import win32con
import winerror
import traceback
import win32api
import win32serviceutil
import win32service
import win32evtlog		
import win32evtlogutil
import leservice

class Service(win32serviceutil.ServiceFramework):
	_svc_name_ = 'LEService'
	_svc_display_name_ = 'Logentries Service'
	def __init__(self, *args):
		win32serviceutil.ServiceFramework.__init__(self, *args)
		self.log('init')
		self.stop_event = win32event.CreateEvent(None, 0, 0, None)
	def log(self, msg):
		import servicemanager
		servicemanager.LogInfoMsg(str(msg))
	def sleep(self, sec):
		win32api.Sleep(sec*1000, True)
	def SvcDoRun(self):
		self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
		try:
			self.ReportServiceStatus(win32service.SERVICE_RUNNING)
			self.log('start')
			self.start()
			self.log('wait')
			win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
			self.log('done')
		except Exception, x:
			self.log('Exception : %s' % x)
			self.SvcStop()
	def SvcStop(self):
		self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
		self.log('stopping')
		self.stop()
		self.log('stopped')
		win32event.SetEvent(self.stop_event)
		self.ReportServiceStatus(win32service.SERVICE_STOPPED)
	# to be overridden
	def start(self):
		self.log('Logentries start monitoring')
		leservice.cmd_monitor([])
	# to be overridden
	def stop(self): pass

	
	