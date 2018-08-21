# Converter for schedules from SoftLayer notices

import sys
import re
import datetime
import pytz
from dateutil.parser import parse
from dateutil.tz import gettz

###################################################
# Debugging functions

errorCount = 0

#debugFlags = 0xffff
debugFlags = 0x1

DEBUG_PARSEERROR = 0x1
DEBUG_PARSEINPUT = 0x2
DEBUG_PARSETIME = 0x4
DEBUG_OUTPUT = 0x8

def debug(flags, string):
    if (debugFlags & flags):
        print string

def error(string):
    global errorCount
    errorCount += 1
    print "*** " + string

###################################################
# Parsing

slDatePattern = re.compile('([0-9]{1,2})-(AUG|SEP)')
slPodPattern = re.compile('(?i)([A-Z]{3}[0-9]{2})\\s+(POD\\s+[0-9]{1,2})\\s+([0-9]{1,2}:[0-9]{2}\\s+(AM|PM)\\s+CDT)')

UTC = pytz.timezone("UTC")
CDT = pytz.timezone("US/Central")

dt = datetime.datetime.today()
debug(DEBUG_PARSETIME, "CDT=%s  utcoffset=%s" % (str(CDT), str(CDT.utcoffset(dt))))

def parseTime(input, format="", default=None):
   try:
        
        tzinfos = { "CDT": gettz("US/Central")}
        parsed = parse(input, tzinfos=tzinfos, default=default)
        debug(DEBUG_PARSETIME, 'parseTime("%s", "%s") -> %s /  %s' % (input, format, 
            parsed.isoformat(),
            parsed.astimezone(UTC).isoformat(),
            ))
        return parsed
   except Exception as e:
        error('parseTime("%s", "%s") -> Exception: %s' % (input, format, str(e)))
        
if 0:   # testing
    parseTime("6:00", "%I:%M")
    parseTime("6:00   PM", "%I:%M %p")
    parseTime("6:00 PM CDT", "%I:%M %p CDT")
    parseTime("6:00 PM CST", "%I:%M %p CDT")
    exit()

###################################################
# Data model

class Pod:
    def __init__(self, timestamp, podname):
        self.timestamp = timestamp
        self.podname = podname

allPodTimes = []
allPods = {}

###################################################
# Main program

### Parse the input
currentDate = None
defaultDate = datetime.datetime.combine(datetime.datetime.today(), datetime.datetime.min.time())
for line in sys.stdin:
    input = line.strip()
    if input == "":
        continue

    dateMatch = slDatePattern.match(input)
    if dateMatch:
#        currentDate = datetime.datetime.strptime(input, "%d-%b")
        currentDate = parse(input, default=defaultDate)
        datestr = currentDate.isoformat()
        debug(DEBUG_PARSEINPUT, 'Input: "' + input + '" --> date: ' + datestr)
        debug(DEBUG_OUTPUT, '<b>%s</b>' % (currentDate.strftime('%B %d')))
        continue

    slPodMatch = slPodPattern.match(input)
    if slPodMatch:
        dc = slPodMatch.group(1)
        pod = slPodMatch.group(2)
        timeInput = slPodMatch.group(3)
        timeval = parseTime(timeInput, default=currentDate)
        timestr = timeval.isoformat()
        timeutc = timeval.astimezone(UTC)
        debug(DEBUG_PARSEINPUT, 'Input:  "' + input + '" --> pod: dc=%s  pod=%s  time=%s' % (dc, pod, timestr))
        podname = ('%s    %s' % (dc, pod)).upper()
        debug(DEBUG_OUTPUT, "Output: %s %s UTC" % (podname, timeutc.strftime('%H:%M')))
        allPodTimes.append(Pod(timeutc, podname))
        if podname in allPods:
            error("Found multiple entries for " + podname)
        allPods[podname] = timeutc
        continue
    
    error('Input: "' + input + '" --> UNMATCHED')

### Generate output
currentDate = datetime.datetime(1900, 1, 1)
firstTime = True
for p in allPodTimes:
    theDate = datetime.datetime(p.timestamp.year, p.timestamp.month, p.timestamp.day)
    if theDate != currentDate:
        currentDate = theDate
        if not firstTime:
            print("</div>")
            print("<br/>")
            print
        firstTime = False
        print('<strong>%s</strong>' % (currentDate.strftime('%B %d')))
        print('<div class="pod-schedule">')
    print('%s    %s UTC' % (p.podname, p.timestamp.strftime('%H:%M')))
print("</div>")

### End
if errorCount > 0:
    print "***** %d Errors during processing" % errorCount


