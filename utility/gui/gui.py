assert __name__ != '__main__', "Don't run this file, run main.py"

import os
import PySimpleGUI as sg
import matplotlib.pyplot as plt
import re
from tkinter.filedialog import askdirectory, askopenfilename
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from utility.calc.least_square_fit import least_square_fit
from utility.gui.layout import create_layout
from utility.plot.plot_source import plot_source
from utility.wrappers.source_model_wrapper import SourceModelWrapper
from utility.wrappers.data_wrapper import DataWrapper
from utility.wrappers.stations_config_wrapper import StationsConfigWrapper

ROOT_PATH = "/".join(os.path.dirname(__file__).replace("\\","/").split("/")[0:-2]) + "/"
FAVICON_PATH = ROOT_PATH + "images/favicon.ico"

def repack(widget, option):
    pack_info = widget.pack_info()
    pack_info.update(option)
    widget.pack(**pack_info)

def draw_fig(canvas, fig, canvas_toolbar):
    if canvas.children:
        for child in canvas.winfo_children():
            child.destroy()
    if canvas_toolbar.children:
        for child in canvas_toolbar.winfo_children():
            child.destroy()
    figure_canvas_agg = FigureCanvasTkAgg(fig, master=canvas)
    toolbar = Toolbar(figure_canvas_agg, canvas_toolbar)
    figure_canvas_agg.get_tk_widget().pack(side='right', fill='both', expand=1)
    figure_canvas_agg.draw()
    toolbar.update()

class Toolbar(NavigationToolbar2Tk):
    def __init__(self, *args, **kwargs):
        super(Toolbar, self).__init__(*args, **kwargs)

def update_station_table(config, stations, highlights, band):
    """
    Generates a table that can be used in the GUI

    Parameters:
    config(DataFrame): Information regarding *all* stations
    stations(dict): A dictionary with the wanted stations as keys

    Returns:
    A list of lists for the table
    """
    new_table = []
    for station in stations:
        activated = "X" if config.is_selected(station) else ""
        sefd = config.get_SEFD(station, band)
        highlight = "X" if station in highlights else ""
        new_table.append([activated, station, stations[station], sefd, highlight])
    return new_table

def update_sources_table(sources):
    new_table = []
    for source in sources: 
        new_table.append([source, sources[source]['observations']])
    return new_table

def run_gui():
    """
    Main function for the GUI. Creates the layout and runs the event loop.

    Parameters: 
    No parameters

    Returns:
    No return values
    """
    # Launch the GUI window
    sg.theme("DarkGrey5")
    sg.SetOptions(font=("Andalde Mono", 12))
    
    # Create the main GUI window
    layout = create_layout()
    main_window = sg.Window('Quasar Viewer', layout,
                            margins=[0, 0], resizable=True, finalize=True,
                            icon=FAVICON_PATH, enable_close_attempted_event=True)
    main_window.TKroot.minsize(1320, 895)
    main_window["scale_uv"].bind("<Return>", "_enter")
    main_window["scale_flux"].bind("<Return>", "_enter")

    # Fixes so the left column doesn't expand
    repack(main_window["left_col"].Widget, {'fill':'y', 'expand':0, 'before':main_window["right_col"].Widget})

    # Fixes issue with layout on Windows 11
    plt.figure()

    # Static variables for the event loop
    dir = ""
    data = None
    config = None
    source_dict = {}
    source = ""
    source_model = None
    source_model_type = "img"
    source_model_dir = ""
    band = 0
    sort_stat_reverse = [True, False, True, True, True]
    sort_source_reverse = [False, True]
    highlights = []
    fig1 = plt.figure(0)
    fig2 = plt.figure(1)
    fig3 = plt.figure(2)
    fig4 = plt.figure(3)

    # Event loop for the GUI
    while True:
        event, values = main_window.Read(timeout=25)

        #######################
        ### Menu bar events ###
        #######################

        # Open the vgosDB
        if event == "Open session":

            new_dir = askdirectory(initialdir=ROOT_PATH + "data/sessions")
            if new_dir != dir and new_dir:
                # Tell the user that we are loading data
                main_window["loading_text"].update(value="Loading...")
                main_window.set_title(f"Quasar Viewer - Loading...")
                main_window.refresh()

                # Load data (takes time)
                try:
                    data = DataWrapper(new_dir)
                    config = StationsConfigWrapper(session_dir=new_dir)
                except:
                    sg.Popup("Something went wrong! Please select a valid vgosDB directory.",
                             icon=FAVICON_PATH)
                    main_window["loading_text"].update(value="")
                    main_window.set_title(f"Quasar Viewer")
                    main_window.refresh()
                    continue

                # Update static variables
                dir = new_dir
                source = None
                source_dict = data.get_source_dict()
                highlights = []
                
                # Reset/update GUI
                main_window["stations_table"].update([])
                main_window["sources_table"].update(update_sources_table(source_dict))
                main_window.set_title(f"Quasar Viewer - {new_dir.split('/')[-1]}")
                main_window["loading_text"].update(value="")
                
                main_window["A_band"].update(visible=data.is_abcd)
                main_window["B_band"].update(visible=data.is_abcd)
                main_window["C_band"].update(visible=data.is_abcd)
                main_window["D_band"].update(visible=data.is_abcd)
                main_window["S_band"].update(visible=data.is_sx)
                main_window["X_band"].update(visible=data.is_sx)

                fig1.clf()
                fig2.clf()
                fig3.clf()
                fig4.clf()
                draw_fig(main_window["fig1"].TKCanvas, fig1, main_window["toolbar1"].TKCanvas)
                draw_fig(main_window["fig2"].TKCanvas, fig2, main_window["toolbar2"].TKCanvas)
                draw_fig(main_window["fig3"].TKCanvas, fig3, main_window["toolbar3"].TKCanvas)
                draw_fig(main_window["fig4"].TKCanvas, fig4, main_window["toolbar4"].TKCanvas)

                main_window.refresh()

        # Open fits file
        if event == "Open fits":
            new_dir = askopenfilename(initialdir=ROOT_PATH + "data/fits")

            # Tell the user that we are loading data
            main_window["loading_text"].update(value="Loading...")
            main_window.refresh()

            try:
                source_model = SourceModelWrapper(new_dir, model=source_model_type)
            except:
                sg.Popup("Something went wrong! Please select a valid fits file.",
                             icon=FAVICON_PATH)

            source_model_dir = new_dir
            main_window["loading_text"].update(value="")
            main_window["scale_uv"].update("1")
            main_window["scale_flux"].update("1")
            main_window.refresh()

            # Re-plot with new fits file
            main_window.write_event_value("plot", True)

        # Save the stations info config
        if event == "Save" and config:
            config.save()

        # Restore to saved stations info config
        if event == "Restore" and config:
            a = sg.popup_yes_no(
                "Restoring will remove all unsaved configurations. Do you wish to continue?",
                icon=FAVICON_PATH)
            if a == "Yes":
                config.restore()

                if source:
                    new_table = update_station_table(
                        config, source_dict[source]["stations"],
                        highlights, band)
                else:
                    new_table = []
                main_window["stations_table"].update(new_table)
                main_window.write_event_value("plot", True)
                main_window.refresh()
        
        # Delete configuration and re-generate config file
        if event == "Delete" and config:
            a = sg.popup_yes_no(
                "Deleting will remove all configurations set. Do you wish to continue?",
                icon=FAVICON_PATH)
            if a == "Yes":
                config.delete()

                if source:
                    new_table = update_station_table(
                        config, source_dict[source]["stations"],
                        highlights, band)
                else:
                    new_table = []
                main_window["stations_table"].update(new_table)
                main_window.write_event_value("plot", True)
                main_window.refresh()

        # Display about info
        if event == "About...":
            with open(ROOT_PATH + "LICENSE.txt", "r") as f:
                license = f.read()
                license = license.replace("\n\n", "\t")
                license = license.replace("\n", " ")
                license = license.replace("\t", "\n\n")
            sg.Popup("""GUI for finding optimal SEFD values based on VGOS DB sessions and source images. The program was developed at NVI Inc. by Filip Herbertsson and Samuel Collier Ryder during a summer internship in 2023.""" + "\n\n" + license,
                     icon=FAVICON_PATH)

        # Close the program and save config
        if event == sg.WIN_CLOSE_ATTEMPTED_EVENT or event == "Exit":
            if config and config.has_changed():
                a,_ = sg.Window("Unsaved changes", [[sg.Text("You have unsaved changes. Do you wish to save?")],
                                                    [sg.Button("Yes",k="Yes"),sg.Button("No",k="No"),sg.Button("Cancel",k="Cancel")]], finalize=True, icon=FAVICON_PATH, modal=True).read(close=True)
                if a == "Yes":
                    config.save()
                if a == "Cancel":
                    continue
            break

        ###############################
        ### Source selection events ###
        ###############################

        # Source selected
        if event[0] == "sources_table" and event[1] == "+CLICKED+":
            click_row, click_col = event[2]

            # Unusable clicks
            if click_row == None or click_col == None or click_col == -1:
                continue

            # Clicking when no data is in the table should do nothing
            elif all(not e for e in main_window["sources_table"].get()):
                continue

            elif click_row == -1:

                reverse = sort_source_reverse[click_col]

                # Sort by selected
                if click_col == 0:
                    source_dict = dict(sorted(source_dict.items(
                    ), key=lambda source: source[0], reverse=reverse))

                # Sort by name
                if click_col == 1:
                    source_dict = dict(sorted(source_dict.items(
                    ),key=lambda source: source[1]["observations"], reverse=reverse))

                reverse = not reverse
                sort_source_reverse = [False, True]
                sort_source_reverse[click_col] = reverse
                main_window["sources_table"].update(update_sources_table(source_dict))
                main_window.refresh()

            # Update the stations table
            else:
                highlights = []
                source = main_window["sources_table"].get()[click_row][0]
                new_table = update_station_table(
                    config, source_dict[source]["stations"],
                    highlights, band)
                main_window["stations_table"].update(new_table)
                main_window.write_event_value("plot", True)
                main_window.refresh()
        
        ############################
        ### Band selection event ###
        ############################
        
        if re.search("[A-DSX]_band",str(event)):
            band = ["A","B","C","D","S","X"].index(event.split("_")[0])

            # Update GUI (if table is set)
            if not all(not e for e in main_window["stations_table"].get()):
                new_table = update_station_table(
                    config, source_dict[source]["stations"],
                    highlights, band)
                main_window["stations_table"].update(new_table)
                main_window.write_event_value("plot", True)
                main_window.refresh()

        ################################
        ### Station selection events ###
        ################################

        if event[0] == "stations_table" and event[1] == "+CLICKED+":
            click_row, click_col = event[2]

            # Unusable clicks
            if click_row == None or click_col == None or click_col == -1:
                continue

            # Clicking when no data is in the table should do nothing
            if all(not e for e in main_window["stations_table"].get()):
                continue

            # Sort by columns
            elif click_row == -1:

                reverse = sort_stat_reverse[click_col]

                # Sort by selected
                if click_col == 0:
                    source_dict[source]["stations"] = dict(sorted(source_dict[source]["stations"].items(
                    ), key=lambda stat: config.is_selected(stat[0]), reverse=reverse))

                # Sort by name
                if click_col == 1:
                    source_dict[source]["stations"] = dict(sorted(
                        source_dict[source]["stations"].items(), key=lambda stat: stat[0], reverse=reverse))

                # Sort by observations
                if click_col == 2:
                    source_dict[source]["stations"] = dict(sorted(
                        source_dict[source]["stations"].items(), key=lambda stat: int(stat[1]), reverse=reverse))

                # Sort by SEFD
                if click_col == 3:
                    source_dict[source]["stations"] = dict(sorted(source_dict[source]["stations"].items(
                    ), key=lambda stat: config.get_SEFD(stat[0],band), reverse=reverse))

                # Sort by highlight
                if click_col == 4:
                    source_dict[source]["stations"] = dict(sorted(source_dict[source]["stations"].items(),
                                                                  key=lambda stat: stat[0] in highlights, reverse=reverse))

                # Update list
                sort_stat_reverse = [True, False, True, True, True]
                sort_stat_reverse[click_col] = not reverse

                # Update GUI
                new_table = update_station_table(
                    config, source_dict[source]["stations"],
                     highlights, band)
                main_window["stations_table"].update(new_table)
                main_window.refresh()

            # Select/deselect station
            elif click_col == 0:
                # Update selection
                selected_station = main_window["stations_table"].get()[click_row][1]
                config.toggle(selected_station)

                # Update GUI
                new_table = update_station_table(
                    config, source_dict[source]["stations"],
                     highlights, band)
                main_window["stations_table"].update(new_table)
                main_window.write_event_value("plot", True)
                main_window.refresh()

            # Edit SEFD values
            elif click_col == 3:
                # Get stats of the selected cell
                selected_station = main_window["stations_table"].get()[click_row][1]
                orig_SEFD = config.get_SEFD(selected_station,band)
                band_letter = ["A","B","C","D","S","X"][band]

                # Popup to ask user to fill in new value
                edit_popup = sg.Window("Edit...", [[sg.Text("Station:", s=(8, 1)), sg.Text(selected_station)],
                                                   [sg.Text("Band:", s=(8, 1)), sg.Text(
                                                       band_letter)],
                                                   [sg.Text("SEFD: ", s=(8, 1)), sg.Input(
                                                       default_text=orig_SEFD, key="new_SEFD_input"), sg.Button("Set", key="new_SEFD_set")],
                                                   [sg.Text("Invalid input!", key="invalid_input", visible=False, text_color="red")]], finalize=True, icon=FAVICON_PATH, modal=True)
                edit_popup["new_SEFD_input"].bind("<Return>", "_enter")
                edit_popup["invalid_input"].hide_row()
                edit_popup["new_SEFD_input"].set_focus()

                # Event loop for popup
                while True:
                    event, values = edit_popup.Read()

                    if event == "new_SEFD_set" or event == "new_SEFD_input_enter":
                        new_SEFD = values["new_SEFD_input"]

                        # Only allow numbers
                        try:
                            if new_SEFD.isdigit():
                                new_SEFD = str(int(new_SEFD))
                            else:
                                new_SEFD = str(float(new_SEFD))
                                SEFD_int, SEFD_frac = new_SEFD.split(".")
                                if not int(SEFD_frac):
                                    new_SEFD = int(SEFD_int)
                        except:
                            edit_popup["invalid_input"].update(visible=True)
                            edit_popup["invalid_input"].unhide_row()
                            edit_popup.refresh()
                            continue

                        # Set new SEFD
                        config.set_SEFD(selected_station,band,new_SEFD)
                        
                        # Update GUI
                        new_table = update_station_table(
                            config, source_dict[source]["stations"],
                            highlights, band)
                        main_window["stations_table"].update(new_table)
                        main_window.write_event_value("plot", True)
                        main_window.refresh()

                        # Close popup
                        edit_popup.close()
                    break

            # Select/deselect highlight
            elif click_col == 4:
                # Update selection
                selected_station = main_window["stations_table"].get()[click_row][1]

                if selected_station in highlights:
                    highlights.remove(selected_station)
                else:
                    # Check maximum two highlights
                    if len(highlights) > 1:
                        sg.Popup("You can only select two highlights!",
                                icon=FAVICON_PATH)
                        continue
                    highlights.append(selected_station)

                # Update GUI
                new_table = update_station_table(config, source_dict[source]["stations"],
                                                 highlights, band)
                main_window["stations_table"].update(new_table)
                main_window.write_event_value("plot", True)
                main_window.refresh()

        ####################
        ### Debug events ###
        ####################

        # Catch events when no model has been set
        if (event == "set_scale_uv" or event == "set_scale_flux" or event == "set_scale_flux_auto" or event == "fit_SEFD" or event == "gauss"):
            if not source:
                sg.Popup("No source selected.", icon=FAVICON_PATH)
                continue
            elif not source_model:
                sg.Popup("No fits file selected.", icon=FAVICON_PATH)
                continue

        if event == "set_scale_uv" or event == "scale_uv_enter":
            source_model.scale_uv = float(values["scale_uv"])
            main_window.write_event_value("plot", True)

        elif event == "set_scale_flux" or event == "scale_flux_enter":
            source_model.scale_flux = float(values["scale_flux"])
            main_window.write_event_value("plot", True)
        
        elif event == "set_scale_flux_auto":
            source_model.set_flux_scale(config, data.get(sources=source,ignored_stations=ignored_stations,bands=band))

            # Update GUI
            new_table = update_station_table(
                config, source_dict[source]["stations"],
                highlights, band)
            main_window["stations_table"].update(new_table)
            main_window["scale_flux"].update(value=source_model.scale_flux)
            main_window.write_event_value("plot", True)
            main_window.refresh()

        elif event == "model_type":
            source_model_type_new = "raw" if values["model_type"] == "QuasarModelRaw" else "img"

            if source_model_type_new != source_model_type:
                source_model_type = source_model_type_new

                if source_model:
                    try:
                        source_model = SourceModelWrapper(source_model_dir, model=source_model_type)
                        main_window["scale_uv"].update("1")
                        main_window["scale_flux"].update("1")
                        main_window.write_event_value("plot", True)
                    except:
                        pass

        elif event == "fit_SEFD":
            if source and source_model:
                least_square_fit(data.get(sources=source,ignored_stations=ignored_stations,bands=band), source_model, config)

                # Update GUI
                new_table = update_station_table(
                    config, source_dict[source]["stations"],
                    highlights, band)
                main_window["stations_table"].update(new_table)
                main_window.write_event_value("plot", True)
                main_window.refresh()

        elif event == "gauss":
            if source and source_model:
                sm = source_model.gauss_list[0]
                sg.Popup(f"a = {sm.a}\nb = {sm.b}\nA = {sm.amp}\nt = {sm.theta}\nx0 = {sm.x0}\ny0 = {sm.y0}")


        ##################
        ### Plot event ###
        ##################

        if event == "plot":
            # Check that user has selected a folder
            if not dir:
                continue

           # Check that user has selected a source
            if not source:
                continue

            # Find which band the user has selected, selected station will have
            # a value of True, all others False
            band = [values['A_band'], values['B_band'],
                    values['C_band'], values['D_band'],
                    values['S_band'], values['X_band']].index(True)

            # Check that the selected band is in the currently visible list
            if (data.is_abcd and band in [4,5]) or (data.is_sx and band in [0,1,2,3]):
                continue

            # Ignore the stations that were unselected in the GUI
            ignored_stations = config.get_deselected_stations()

            # Plot
            plot_source(
                source, data.get(sources=source, ignored_stations=ignored_stations, bands=band), config, source_model=source_model, highlighted_stations=highlights)

            # Display plots in canvases
            draw_fig(main_window["fig1"].TKCanvas, fig1, main_window["toolbar1"].TKCanvas)
            draw_fig(main_window["fig2"].TKCanvas, fig2, main_window["toolbar2"].TKCanvas)
            draw_fig(main_window["fig3"].TKCanvas, fig3, main_window["toolbar3"].TKCanvas)
            draw_fig(main_window["fig4"].TKCanvas, fig4, main_window["toolbar4"].TKCanvas)


