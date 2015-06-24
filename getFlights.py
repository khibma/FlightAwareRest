# Calls fa.py and convertArcGIS.py to gather flight tracks from FlightAware
#  and turns the tracks into featureclasses inside an fGDB.
# Provide a username, apikey, airport code (4digit) and folder to create items.
# Note the FlightAware costs are generally based on 15 responses per query. A 
#  request of more than 15 will incur a cost as if more than 1 single query was made.
# Consult the FlightAware website for information on billing.
# This script can be used WITHOUT ArcGIS if the last conversion to fGDB is not done.
#
# Note that the getDepartures and getArrivals and initializing of howMany is hardcoded 
#  to 15 requests per query. As such, this value would need to be changed in each
#  function call if the initialization value is changed.

import os
import fa as FlightAware
import convertArcGIS as ARC


USERNAME = '<your username>'
KEY = '<your key>'
TARGETAIRPORT =  'CYUL'
DIRLOCATION = r'<path to folder>'
SAVETXTFILES = True
PRINTCOST = True
FLIGHTMAX = 14


def w2d(stuff, fname, location=DIRLOCATION):
    with open(os.path.join(location, fname), "w") as f:
        f.write(str(stuff))


# Initialize with max of 15. More than 15 means I need to fix the cost logic
fa = FlightAware.FA_REST(USERNAME, KEY, 15)

# Collect the list of departures from the target airport
print("Collecting departures")
fa.getDepartures(TARGETAIRPORT, 0, FLIGHTMAX, 15)
if SAVETXTFILES: w2d(fa.departures, "departures.txt")
if PRINTCOST: print("Counts: {0} / Cost: {1} ").format(sum(fa.reqCt.values()), fa.money)

# Collect the list of arrivals to the target airport
print("Collecting arrivals")
fa.getArrivals(TARGETAIRPORT, 0, FLIGHTMAX, 15)
if SAVETXTFILES: w2d(fa.arrivals, "arrivals.txt")
if PRINTCOST: print("Counts: {0} / Cost: {1} ").format(sum(fa.reqCt.values()), fa.money)


# Get all arriving flight tracks
print("Getting arrival tracks")
arrivalTracks = {}
for flight in fa.arrivals:
    fltdt = fa.getFlightLastTrack(flight['ident'])
    try:
        flttrk = fltdt['GetLastTrackResult']['data']
        arrivalTracks[flight['ident']] = flttrk
    except:
        pass
if SAVETXTFILES: w2d(arrivalTracks, "arrivalTrack.txt")
if PRINTCOST: print("Counts: {0} / Cost: {1} ").format(sum(fa.reqCt.values()), fa.money)


# Get all departing flight tracks
print("Getting departure tracks")
depaturalTracks = {}
for flight in fa.departures:
    fltdt = fa.getFlightLastTrack(flight['ident'])
    try:
        flttrk = fltdt['GetLastTrackResult']['data']
        depaturalTracks[flight['ident']] = flttrk
    except:
        pass
if SAVETXTFILES: w2d(depaturalTracks, "departualTrack.txt")
if PRINTCOST: print("Counts: {0} / Cost: {1} ").format(sum(fa.reqCt.values()), fa.money)

## Now turn the data into fgdb-fc data (requires ArcGIS)

# Create the GDB
print("Creating data gdb")
gdblocation = ARC.createGDB(DIRLOCATION)

# Create fGDB-FC: arrivals
ARC.convert(arrivalTracks, gdblocation, "_inb")

# Create fGDB-FC: departures
ARC.convert(depaturalTracks, gdblocation, "_outb")

print("all done")
