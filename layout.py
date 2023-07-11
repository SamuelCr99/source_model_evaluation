import PySimpleGUI as sg


def create_layout(stations):
    stations.sort()
    check_boxes1 = list(map(lambda s: [sg.Checkbox(s,default=True,visible=False,key=s,expand_x=True)],stations))
    check_boxes2 = list(map(lambda s: [sg.Checkbox(s,default=True,visible=False,key=f"{s}_1",expand_x=True)],stations))

    left_col = [[sg.Frame("Source",[[sg.Combo([[]], key="source_list", size=(30,30), enable_events=True, expand_x=True, p=20, readonly=True)]], expand_x=True)],
                [sg.Frame("Stations",[[sg.Column(check_boxes1, s=(300,300), scrollable=False, key="check_box_col", element_justification="left", expand_x=True, expand_y=True, p=20)],
                                      [sg.Column(check_boxes2, s=(300,300), scrollable=True, vertical_scroll_only = True, key="check_box_col_scroll", element_justification="left", expand_x=True, expand_y=True, p=20, visible=False)]],expand_x=True)],
                [sg.Frame("Band",[[sg.Radio("A","band", key='A_band', default=True),sg.Radio("B","band", key="B_band"),sg.Radio("C","band", key="C_band"),sg.Radio("D","band", key="D_band")]],expand_x=True)],
                [sg.VPush()],
                [sg.Push(),sg.Button("Plot",key="plot"),sg.Button("Cancel",key="cancel")]]

    menu = [["File", ["Open folder", "Exit"]],
            ["Help", "About..."]]

    layout = [[sg.Menu(menu, key="menu")],
              [sg.Column(left_col,expand_x=True,expand_y=True)]]

    return layout