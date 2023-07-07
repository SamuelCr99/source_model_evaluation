import matplotlib.pyplot as plt
from find_station_baseline_match import find_station_baseline_match
from to_uv import convert_uv
import pandas as pd
import netCDF4 as nc
import numpy as np
from calculate_flux import calculate_flux
import random

def plot_source(source,baseline):
    ref_freq = np.ma.getdata(nc.Dataset(f'data/Observables/RefFreq_bX.nc', 'r')["RefFreq"]).tolist()[0]
    uv_data = np.ma.getdata(nc.Dataset(f'data/ObsDerived/UVFperAsec_bX.nc', 'r')['UVFperAsec']).tolist()
    data = pd.read_csv("data/datapoints.csv")

    baseline_matches = find_station_baseline_match(source,baseline)

    coords_u = []
    coords_v = []
    flux = []

    for point in baseline_matches:
        u_orig,v_orig = uv_data[point][0]*206264.81, uv_data[point][1]*206264.81

        A_freq = data.A_freq.iloc[point]
        B_freq = data.B_freq.iloc[point]
        C_freq = data.C_freq.iloc[point]
        D_freq = data.D_freq.iloc[point]

        u_A,v_A = convert_uv(u_orig,v_orig,ref_freq,A_freq)
        u_B,v_B = convert_uv(u_orig,v_orig,ref_freq,B_freq)
        u_C,v_C = convert_uv(u_orig,v_orig,ref_freq,C_freq)
        u_D,v_D = convert_uv(u_orig,v_orig,ref_freq,D_freq)

        coords_u.extend([u_A,u_B,u_C,u_D,-u_A,-u_B,-u_C,-u_D])
        coords_v.extend([v_A,v_B,v_C,v_D,-v_A,-v_B,-v_C,-v_D])

        flux.extend(calculate_flux(point))
    
    # Only dots
    plt.scatter(coords_u,coords_v,c=flux, marker=".")
    plt.show()

if __name__ == '__main__':
    source = "1803+784"
    baseline = "GGAO12M/ISHIOKA"
    plot_source(source,baseline)

