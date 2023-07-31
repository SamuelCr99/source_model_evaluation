from math import sqrt


def calculate_flux(point, station_data, bands=[0, 1, 2, 3]):
    """
    Calculates the flux of a source at a given index in the data/datapoints.csv file.

    Parameters:
    index(int): The index of the source in general_data.
    general_data(DataFrame): DataFrame containing all observations
    station_data(DataFrame): DataFrame containing all stations
    bands(list): The bands to use (A=0, B=1...)

    Returns:
    list[float]: A list of the calculated fluxes for each band for the source at
    the given index.

    """

    # Change bands to a list if it was only given as a integer
    if not isinstance(bands, list):
        bands = [bands]

    # Constants to use
    int_time = point.int_time
    C = 0.617502
    stat1 = point.Station1
    stat2 = point.Station2

    flux = []

    for band in bands:
        band_letter = ["A","B","C","D","S","X"][band]

        # Band-specific constants to use
        SNR = point[f"{band_letter}_SNR"]
        band_width = point[f"{band_letter}_bw"]
        SEFD1 = float(
            station_data[f"{band_letter}_SEFD"].loc[station_data.name == stat1].iloc[0])
        SEFD2 = float(
            station_data[f"{band_letter}_SEFD"].loc[station_data.name == stat2].iloc[0])

        # Equation for flux density
        flux.append((SNR * sqrt(SEFD1 * SEFD2)) /
                    (C * sqrt(2*int_time*band_width)) if band_width != 0 else 0)

    return flux