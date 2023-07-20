import PySimpleGUI as sg


def create_layout(stations):
    """
    Creates the layout for the GUI

    Parameters:
    stations(list): A list of all stations

    Returns:
    The finished layout
    """
    stations.sort()
    headings = ["Sel.", "Stations", "Obs.", "SEFD", "★"]
    col_widths = [4,10,4,10,4]
    table_col = sg.Table([], headings=headings, col_widths=col_widths, auto_size_columns=False, key="stations_table", enable_click_events=True, select_mode=sg.TABLE_SELECT_MODE_NONE,
                         expand_x=True, expand_y=True, p=20, alternating_row_color="grey25", justification="center")

    source_headings = ["Source", "Obs."]
    sources_col = sg.Table([], headings=source_headings, key="sources_table", enable_click_events=True, select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                         expand_x=True, expand_y=True, p=20, alternating_row_color="grey25", justification="center")

    # Currently the only column
    left_col = [[sg.Frame("Source", [[sources_col]], expand_x=True)],
                [sg.Frame("Band", [[sg.Radio("A", "band", key='A_band', enable_events=True, default=True), sg.Radio("B", "band", key="B_band", enable_events=True), sg.Radio(
                    "C", "band", key="C_band", enable_events=True), sg.Radio("D", "band", key="D_band", enable_events=True)]], expand_x=True)],
                [sg.Frame("Stations", [[table_col]],
                          expand_x=True, expand_y=True)],
                [sg.Text(text="", key="loading_text", text_color="white", font=("Andalde Mono", 16)), sg.Push(), sg.Button("Plot", key="plot"), sg.Button("Cancel", key="cancel")]]

    right_col = [[sg.Canvas(key="fig")],
                 [sg.Canvas(key="toolbar",s=(500,500))]]

    menu = [["&File", ["&Open folder", "&Save configuration", "&Restore", "&Exit"]],
            ["&Help", "&About..."]]

    layout = [[sg.MenubarCustom(menu, text_color="black", bar_background_color="white", background_color="white", bar_text_color="black")],
              [sg.Column(left_col, expand_x=True, expand_y=True),sg.Column([[sg.Frame("Figure", right_col)]])]]

    return layout
