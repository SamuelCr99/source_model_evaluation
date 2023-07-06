import netCDF4 as nc
import pandas as pd
import numpy as np

def bytes_to_string(bytes):
    string = ""
    for byte in bytes:
        string += byte.decode("utf-8")
    return string

def time_to_string(time):
    h = time[3]
    m = time[4]
    if h<10: h = f"0{h}"
    if m<10: m = f"0{m}"
    return f"{time[0]}/{time[1]}/{time[2]}-{h}:{m}"

def find_datapoints(dir):
    # time, source, station1, station2, el1, az1, el2, az2
    baseline_ds = nc.Dataset(f'{dir}Observables/Baseline.nc')
    timeutc_ds = nc.Dataset(f'{dir}Observables/TimeUTC.nc')
    source_ds = nc. Dataset(f'{dir}Observables/Source.nc')

    source = []
    for elem in np.ma.getdata(source_ds["Source"]).tolist():
        source.append(bytes_to_string(elem))
    time = []
    for elem in np.ma.getdata(timeutc_ds["YMDHM"]):
        time.append(time_to_string(elem))
    second = []
    for elem in np.ma.getdata(timeutc_ds["Second"]):
        second.append(elem)
    stat1 = []
    stat2 = []
    for elem in np.ma.getdata(baseline_ds["Baseline"]).tolist():
        stat1.append(bytes_to_string(elem[0]).replace(" ",""))
        stat2.append(bytes_to_string(elem[1]).replace(" ",""))

    stations = pd.read_csv(f'{dir}stations.csv')

    time_sec_list = list(map(lambda t,s: f"{t}:{s}",time,second))
    stat_time_df = pd.DataFrame({"stat1": stat1, "stat2": stat2, "time": time_sec_list})

    AzEl_dict = {}
    for station in stations.name:
        AzEl_ds = nc.Dataset(f'{dir}{station}/AzEl.nc')

        current_df = stat_time_df[(stat_time_df.stat1 == station) | (stat_time_df.stat2 == station)]
        current_df = current_df.drop_duplicates(subset=["time"])

        El = []
        Az = []
        for row in AzEl_ds["ElTheo"]:
            El.append(row[0])
        for row in AzEl_ds["AzTheo"]:
            Az.append(row[0])
        station_dict = {}

        for i, row in current_df.iterrows():
            station_dict[row.time] = {"El": El.pop(0), "Az": Az.pop(0)}

        AzEl_dict[station] = station_dict

    El1 = []
    Az1 = []
    El2 = []
    Az2 = []

    for i in range(len(stat1)):
        El1.append(AzEl_dict[stat1[i]][f"{time[i]}:{second[i]}"]["El"])
        Az1.append(AzEl_dict[stat1[i]][f"{time[i]}:{second[i]}"]["Az"])
        El2.append(AzEl_dict[stat2[i]][f"{time[i]}:{second[i]}"]["El"])
        Az2.append(AzEl_dict[stat2[i]][f"{time[i]}:{second[i]}"]["Az"])

    df = pd.DataFrame({"YMDHM": time,
                       "Second": second,
                       "Source": source,
                       "Station1": stat1,
                       "Station2": stat2,
                       "El1": El1,
                       "Az1": Az1,
                       "El2": El2,
                       "Az2": Az2})
    
    df.to_csv(f"{dir}datapoints.csv",index=False)

def find_stations(dir):
    # name, x, y, z, lat, lon
    xyz = nc.Dataset(f'{dir}Apriori/Station.nc')
    stations = []
    station_xyz = xyz['AprioriStationXYZ'][:]
    stations = list(xyz['AprioriStationList'][:].astype(str))
    for i, _ in enumerate(stations):
        stations[i] = ''.join(stations[i])

    df = pd.DataFrame(columns=['name', 'x', 'y', 'z', 'lat', 'lon'])
    df['name'] = stations
    df['name'] = df['name'].str.replace(' ', '')
    df['x'] = station_xyz[:,0]
    df['y'] = station_xyz[:,1]
    df['z'] = station_xyz[:,2]

    with open(f'{dir}stations.csv', 'w') as f:
        f.write(df.to_csv(index=False))

        

if __name__ == '__main__':
    find_stations('data/')
    find_datapoints("data/")