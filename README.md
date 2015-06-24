# FlightAwareRest
Gather flight tracks from FlightAware and turn into ArcGIS featureclass

The following scripts require a developer API Key from [FlightAware](http://flightaware.com/). To get a key you need a creditcard. IE. To use these script it'll cost you money.

The **getFlights.py** acts as a master script calling fa.py and convertArcGIS.py. 
  * *fa.py* will collect arrivals and departure flights from a given airport. The JSON can be saved to disk.
  * *convertArcGIS.py* will convert the JSON to fGDB featureclass as Z-aware points.

Explore the flight aware [docs regarding pricing](http://flightaware.com/commercial/flightxml/pricing_class.rvt) before using these scripts.
Running getFlights.py, as-is, will request 14 arrivals and 14 departures for Montreal. This will cost about $0.30 (30 cents)

Another important note: A request to the departed/arrived endpoints generate the list of flights. This query returns the **newest** flights, both arriving and departing. The results you'd get by running this script at 10am would be different than running it at 9pm. Departed flights may not have landed at their destination yet. There are methods to get a flight by time, but this has not been implemented. 

You will need [ArcGIS Desktop](http://www.esri.com/software/arcgis/arcgis-for-desktop) or ArcGIS Server on the machine to create fgdb-FC. Alternatively you could write your own conversion to a different format.

