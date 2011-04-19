import sys

# ...
# ModuleFinder can't handle runtime changes to __path__, but win32com uses them
try:
    # py2exe 0.6.4 introduced a replacement modulefinder.
    # This means we have to add package paths there, not to the built-in
    # one.  If this new modulefinder gets integrated into Python, then
    # we might be able to revert this some day.
    # if this doesn't work, try import modulefinder
    try:
        import py2exe.mf as modulefinder
    except ImportError:
        import modulefinder
    import win32com
    for p in win32com.__path__[1:]:
        modulefinder.AddPackagePath("win32com", p)
    for extra in ["win32com.shell"]: #,"win32com.mapi"
        __import__(extra)
        m = sys.modules[extra]
        for p in m.__path__[1:]:
            modulefinder.AddPackagePath(extra, p)
except ImportError:
    # no build path setup, no worries.
    pass


buildservice = True
if '--no-service' in sys.argv[1:]:
        buildservice = False
        sys.argv = [k for k in sys.argv if k != '--no-service']
        print sys.argv
       
from distutils.core import setup
import os
import py2exe
import glob
import shutil
 
sys.path.insert(0,os.getcwd())
 
def getFiles(dir):
        
        # dig looking for files
        a= os.walk(dir)
        b = True
        filenames = []
 
        while (b):
                try:
                        (dirpath, dirnames, files) = a.next()
                        filenames.append([dirpath, tuple(files)])
                except:
                        b = False
        return filenames
 
DESCRIPTION = 'Logentries Winbdows Service Install'
NAME = 'LEService'
 
 
class Target:
        def __init__(self,**kw):
                        self.__dict__.update(kw)
                        self.version        = "6.0.1"
                        self.compay_name    = "JLizard"
                        self.copyright      = "(c) JLizard 2011"
                        self.name           = NAME
                        self.description    = DESCRIPTION
 
my_com_server_target = Target(
                description    = DESCRIPTION,
                service = ["lewinservice"],
                modules = ["lewinservice"],
                create_exe = True,
                create_dll = True)
 
if not buildservice:
        #print 'Compilando como ejecutable de windows...'
        setup(
            name = NAME ,
            description = DESCRIPTION,
            version = '1.00.00',
            console = ['lewinservice.py'],
                zipfile=None,
                options = {
                                "py2exe":{"packages":"encodings",
                                        "includes":"win32com,win32service,win32serviceutil,win32event",
                                        "optimize": '2'
                                        },
                                },
        )
else:
        #print 'Compilando como servicio de windows...'
        setup(
            name = NAME,
            description = DESCRIPTION,
            version = '1.00.00',
                service = [{'modules':["lewinservice"], 'cmdline':'pywin32'}],
                zipfile=None,
                options = {
                                "py2exe":{"packages":"encodings",
                                        "includes":"win32com,win32service,win32serviceutil,win32event",
                                        "optimize": '2'
                                        },
                                },
        )
 