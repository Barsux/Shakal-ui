class Styles:
    cancel_button_style = "QPushButton {"\
                           "    background-color:  rgb(255, 100, 0);"\
                           "    border: none;"\
                           "    border-radius: 5;"\
                           "}"\
                           "QPushButton:pressed {"\
                           "    background-color:  rgb(148, 56, 0);"\
                           "    border: none;"\
                           "    border-radius: 5;"\
                           "}"\
                           "QPushButton:hover:!pressed {"\
                           "    background-color: rgb(255, 100, 0);"\
                           "    border: 2px solid;"\
                           "    border-color: rgb(255, 255, 255);"\
                           "    border-radius: 5;"\
                           "}"\
                           "QPushButton:disabled {"\
                           "    background-color:  rgb(148, 56, 0);"\
                           "    border: none;"\
                           "    border-radius: 5;"\
                           "}"\

    box_style = "border: 2px solid;" \
                "background-color: rgb(110, 110, 110);" \
                "border-color: rgb(255, 170, 0);" \
                "border-top-left-radius: 5;" \
                "border-bottom-left-radius: 5;" \
                "border-bottom-right-radius: 5;" \

    page_settings_style = "border: 2px solid;" \
                          "background-color: rgb(121, 121, 121);" \
                          "border-color: rgb(255, 170, 0);" \
                          "border-top-right-radius: 5;" \
                          "border-bottom-right-radius: 5;" \

    mainwindow_style = "background-color: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:0," \
                       "stop:0 rgba(121, 121, 121, 255), stop:1 rgba(0, 0, 0, 255));"

    default_button_style = "QPushButton {" \
                           "    background-color: rgb(255, 170, 0);" \
                           "    border: none;" \
                           "    border-radius: 5;" \
                           "}" \
                           "QPushButton:pressed {" \
                           "    background-color: rgb(195, 130, 0);" \
                           "    border: none;" \
                           "    border-radius: 5;" \
                           "}" \
                           "QPushButton:hover:!pressed {" \
                           "    background-color: rgb(255, 170, 0);" \
                           "    border: 2px solid;" \
                           "    border-color: rgb(255, 255, 255);" \
                           "    border-radius: 5;" \
                           "}" \
                           "QPushButton:disabled {" \
                           "    background-color: rgb(145, 97, 0);" \
                           "    color: rgb(145, 97, 0);" \
                           "    border: none;" \
                           "    border-radius: 5;" \
                           "} " \
                           ""

    default_finished_button_style = "background-color: #c2ffe0; border-radius: 5; color: #c2ffe0"
