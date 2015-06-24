import os
from collections import OrderedDict
import datetime
import arcpy

flightSchema = (('updateType', "STRING"),
                ('timestamp', "DATE"),
                ('altitude', "DOUBLE"),
                ('altitudeChange', "STRING"),
                ('altitudeStatus', "STRING"),
                ('groundspeed', "DOUBLE"),
                ('latitude', "FLOAT"),
                ('longitude', "FLOAT"))
flightSchema = OrderedDict(flightSchema)


def from_unix_timestamp(val):
    # Date/Time from FA = UTC
    return datetime.datetime.fromtimestamp(val).strftime("%Y-%m-%d %H:%M")


def convert(tracks, gdb, direction=""):
    ''' Take tracks (as a dict) and the target GDB to create point FC in.
        If a direction suffix is supplied, it will be appended to the FC name.
          eg. direction="_inb" (inbound|outbound) >> ICE818_inb or ACA794_outb
    '''

    def _makeTemplateFC():
        if arcpy.Exists("in_memory\\template"): return "in_memory\\template"
        else:
            templateFC = arcpy.CreateFeatureclass_management("in_memory", "template", "POINT", template="", has_m="DISABLED", has_z="ENABLED",
                                                             spatial_reference="GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]];-400 -400 1000000000;-100000 10000;-100000 10000;8.98315284119522E-09;0.001;0.001;IsHighPrecision")
            for key, value in flightSchema.iteritems():
                arcpy.AddField_management(templateFC, key, value)

            return templateFC

    tempFC = _makeTemplateFC()

    for key, value in tracks.iteritems():
        print("creating: {} ").format(key)
        fcName = key + direction
        fc = arcpy.CreateFeatureclass_management("in_memory", fcName, "POINT", tempFC, has_z="ENABLED",
                                                 spatial_reference="GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]];-400 -400 1000000000;-100000 10000;-100000 10000;8.98315284119522E-09;0.001;0.001;IsHighPrecision")

        cursor = arcpy.da.InsertCursor(fc, flightSchema.keys() + ["SHAPE@XYZ"])
        for row in value:
            try:
                # Get data into correct formats/position
                insert = [row[val] for val in flightSchema.keys()] + [(row['longitude'], row['latitude'], row['altitude']*100 * 0.3048)]
                insert[1] = from_unix_timestamp(insert[1])
                insert[2] = insert[2]*100  # Elevation(ft) is returned /100, so have to *. (note z-elevation is *0.3048 to create metres)
                cursor.insertRow(insert)
            except:
                print("!!![{0}] row: {1}").format(fcName, insert)

        del cursor
        arcpy.CopyFeatures_management(fc, os.path.join(gdb, fcName))

    return


def createGDB(location):

    gdbname = "FAtracks.gdb"
    gdbpath = os.path.join(location, gdbname)

    if not arcpy.Exists(gdbpath):
        gdb = arcpy.CreateFileGDB_management(location, os.path.splitext(gdbname)[0])

    return gdbpath or gdb


# Some code to load airtracks from disk and convert them.
# Note the hardcoded paths ...
if False:
    trackdata = r"D:\PythonProjects\FlightAwareToken\datamtl\departualTrack.txt"

    with open(trackdata, "r") as f:
        data = f.read()

    # ast convert string to dict
    import ast
    #gdblocation = createGDB(r"D:\PythonProjects\FlightAwareToken\data")
    gdblocation = r"D:\PythonProjects\FlightAwareToken\datamtl\FAtracks.gdb"
    convert(ast.literal_eval(data), gdblocation, "_outb")

'''flightSchema = {'updateType': "STRING",
               'timestamp': "DATE",
               'altitude': "DOUBLE",
               'altitudeChange': "STRING",
               'altitudeStatus': "STRING",
               'groundspeed': "DOUBLE",
               'latitude': "FLOAT",
               'longitude': "FLOAT"
               }
'''
