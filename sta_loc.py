#!/usr/bin/env python3
import sys
from obspy import UTCDateTime, Stream, read_events
from obspy.geodetics.base import gps2dist_azimuth, kilometer2degrees
from obspy.clients.fdsn import Client
from obspy.taup import TauPyModel
import argparse

parser = argparse.ArgumentParser(description='Get Predicted Phase Arrivals')

parser.add_argument("-e", action="store", dest="event_id",
                    required=False, help='Event ID from USGS Catalog')

parser.add_argument("-n", "--net", action="store", dest="nets",
                    required=True, help="Network for Phase Arrivals")

parser.add_argument("-s", "--stas", action="store", dest="stations",
                    required=True, help="Stations for Phase Arrivals")

parser.add_argument("-p", "--phase", action="store", dest="phases",
                    nargs='+', required=False, default=False)

parser.add_argument("-l", "--loc", action="store", dest="loc",
                    required=False, default="00")

parser.add_argument("-c", "--chan", action="store", dest="chan",
                    required=False, default="LHZ")

args = parser.parse_args()
print(args.phases)

ev_client = Client('USGS')

try:
        cat = ev_client.get_events(eventid = args.event_id)
except:
        sys.exit('No event available')
timestring = cat[0].origins[0].time.strftime("%Y-%m-%d %H:%M:%S")
timestring = "Event: {} {}".format(timestring[0], timestring[1].split('.')[0])
locstring = "{:.2f}, {:.2f}, {:.2f}".format(cat[0].origins[0].latitude,
        cat[0].origins[0].longitude, cat[0].origins[0].depth/1000)
print("{} {}".format(timestring, locstring))

st_client = Client('IRIS')
stas = st_client.get_stations(network=args.nets, station=args.stations,
        level='response', starttime=cat[0].origins[0].time)

model = TauPyModel(model='iasp91')

for net in stas:
    for sta in net:
        coords = stas.get_coordinates("{}.{}.{}.{}".format(net.code, sta.code, args.loc, args.chan))
        (dis, azi, bazi) = gps2dist_azimuth(coords['latitude'], coords['longitude'],
                cat[0].origins[0].latitude, cat[0].origins[0].longitude)
        deg = kilometer2degrees(dis/1000.)
        if args.phases:
            arrivals = model.get_travel_times(source_depth_in_km = cat[0].origins[0].depth/1000.,
                    distance_in_degree=deg, phase_list=args.phases,
                    receiver_depth_in_km = coords['local_depth']/1000.)
        else:
            arrivals = model.get_travel_times(source_depth_in_km = cat[0].origins[0].depth/1000.,
                    distance_in_degree=deg, receiver_depth_in_km = coords['local_depth']/1000.)

        if len(arrivals) > 0:
            print("{}_{} Arrivals\n---------------------".format(net.code, sta.code))
            for arrival in arrivals:
                atime = cat[0].origins[0].time + arrival.time
                timestring = str(atime).split('T')
                print("Arrival: {} Time: {} {}".format(arrival.name, timestring[0],
                        timestring[1].split('.')[0]))
            print("\n")
