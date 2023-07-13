'''
Script Name: Apply Text TimelineFX to Segments
Written By: Kieran Hanrahan

Script Version: 1.1.0
Flame Version: 2021.1

URL: http://github.com/khanrahan/apply-text-timelinefx-to-segments

Creation Date: 06.23.23
Update Date: 07.09.23

Description:

    Find specific segments in the selected sequences then apply Text TimelineFX and load
    Text setups based on a token pattern.

    Put simply... its for loading text setups in bulk!

Menus:

    Right-click selected items on the Desktop --> Apply... --> Text TimelineFX to
        Segments
    Right-click selected items in the Media Panel --> Apply... --> Text TimelineFX to
        Segments

To Install:

    For all users, copy this file to:
    /opt/Autodesk/shared/python

    For a specific user, copy this file to:
    /opt/Autodesk/user/<user name>/python
'''

from __future__ import print_function
import os
import re
import datetime as dt
from functools import partial
import flame
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

TITLE = 'Apply Text TimelineFX to Segments'
VERSION_INFO = (1, 1, 0)
VERSION = '.'.join([str(num) for num in VERSION_INFO])
TITLE_VERSION = '{} v{}'.format(TITLE, VERSION)
MESSAGE_PREFIX = '[PYTHON HOOK]'

SETUPS = '/opt/Autodesk/project'
DEFAULT_PATTERN = '/opt/Autodesk/project/<project>/text/flame/<name>.ttg'


class FlameButton(QtWidgets.QPushButton):
    '''
    Custom Qt Flame Button Widget v2.1

    button_name: button text [str]
    connect: execute when clicked [function]
    button_color: (optional) normal, blue [str]
    button_width: (optional) default is 150 [int]
    button_max_width: (optional) default is 150 [int]

    Usage:

        button = FlameButton(
            'Button Name', do_something__when_pressed, button_color='blue')
    '''

    def __init__(self, button_name, connect, button_color='normal', button_width=150,
                 button_max_width=150):
        super(FlameButton, self).__init__()

        self.setText(button_name)
        self.setMinimumSize(QtCore.QSize(button_width, 28))
        self.setMaximumSize(QtCore.QSize(button_max_width, 28))
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.clicked.connect(connect)
        if button_color == 'normal':
            self.setStyleSheet('''
                QPushButton {
                    color: rgb(154, 154, 154);
                    background-color: rgb(58, 58, 58);
                    border: none;
                    font: 14px "Discreet"}
                QPushButton:hover {
                    border: 1px solid rgb(90, 90, 90)}
                QPushButton:pressed {
                    color: rgb(159, 159, 159);
                    background-color: rgb(66, 66, 66);
                    border: 1px solid rgb(90, 90, 90)}
                QPushButton:disabled {
                    color: rgb(116, 116, 116);
                    background-color: rgb(58, 58, 58);
                    border: none}
                QToolTip {
                    color: rgb(170, 170, 170);
                    background-color: rgb(71, 71, 71);
                    border: 10px solid rgb(71, 71, 71)}''')
        elif button_color == 'blue':
            self.setStyleSheet('''
                QPushButton {
                    color: rgb(190, 190, 190);
                    background-color: rgb(0, 110, 175);
                    border: none;
                    font: 12px "Discreet"}
                QPushButton:hover {
                    border: 1px solid rgb(90, 90, 90)}
                QPushButton:pressed {
                    color: rgb(159, 159, 159);
                    border: 1px solid rgb(90, 90, 90)
                QPushButton:disabled {
                    color: rgb(116, 116, 116);
                    background-color: rgb(58, 58, 58);
                    border: none}
                QToolTip {
                    color: rgb(170, 170, 170);
                    background-color: rgb(71, 71, 71);
                    border: 10px solid rgb(71, 71, 71)}''')


class FlameLabel(QtWidgets.QLabel):
    '''
    Custom Qt Flame Label Widget v2.1

    label_name:  text displayed [str]
    label_type:  (optional) select from different styles:
                 normal, underline, background. default is normal [str]
    label_width: (optional) default is 150 [int]

    Usage:

        label = FlameLabel('Label Name', 'normal', 300)
    '''

    def __init__(self, label_name, label_type='normal', label_width=150):
        super(FlameLabel, self).__init__()

        self.setText(label_name)
        self.setMinimumSize(label_width, 28)
        self.setMaximumHeight(28)
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        # Set label stylesheet based on label_type

        if label_type == 'normal':
            self.setStyleSheet('''
                QLabel {
                    color: rgb(154, 154, 154);
                    font: 14px "Discreet"}
                QLabel:disabled {
                    color: rgb(106, 106, 106)}''')
        elif label_type == 'underline':
            self.setAlignment(QtCore.Qt.AlignCenter)
            self.setStyleSheet('''
                QLabel {
                    color: rgb(154, 154, 154);
                    border-bottom: 1px inset rgb(40, 40, 40);
                    font: 14px "Discreet"}
                QLabel:disabled {
                    color: rgb(106, 106, 106)}''')
        elif label_type == 'background':
            self.setStyleSheet('''
                QLabel {
                    color: rgb(154, 154, 154);
                    background-color: rgb(30, 30, 30);
                    padding-left: 5px;
                    font: 14px "Discreet"}
                QLabel:disabled {
                    color: rgb(106, 106, 106)}''')


class FlameLineEdit(QtWidgets.QLineEdit):
    '''
    Custom Qt Flame Line Edit Widget v2.1

    Main window should include this: window.setFocusPolicy(QtCore.Qt.StrongFocus)

    text: text show [str]
    width: (optional) width of widget. default is 150. [int]
    max_width: (optional) maximum width of widget. default is 2000. [int]

    Usage:

        line_edit = FlameLineEdit('Some text here')
    '''

    def __init__(self, text, width=150, max_width=2000):
        super(FlameLineEdit, self).__init__()

        self.setText(text)
        self.setMinimumHeight(28)
        self.setMinimumWidth(width)
        self.setMaximumWidth(max_width)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setStyleSheet('''
            QLineEdit {
                color: rgb(154, 154, 154);
                background-color: rgb(55, 65, 75);
                selection-color: rgb(38, 38, 38);
                selection-background-color: rgb(184, 177, 167);
                border: 1px solid rgb(55, 65, 75);
                padding-left: 5px;
                font: 14px "Discreet"}
            QLineEdit:focus {background-color: rgb(73, 86, 99)}
            QLineEdit:hover {border: 1px solid rgb(90, 90, 90)}
            QLineEdit:disabled {
                color: rgb(106, 106, 106);
                background-color: rgb(55, 55, 55);
                border: 1px solid rgb(55, 55, 55)}
            QToolTip {
                color: rgb(170, 170, 170);
                background-color: rgb(71, 71, 71);
                border: none}''')


class FlameProgressWindow(QtWidgets.QDialog):
    '''
    Custom Qt Flame Progress Window

    FlameProgressWindow(window_title, num_to_do[, text=None, enable_done_button=False,
                        parent=None])

    window_title: text shown in top left of window ie. Rendering... [str]
    num_to_do: total number of operations to do [int]
    text: message to show in window [str]
    enable_cancel_button: enable cancel button, default is False [bool]

    Examples:

        To create window:

            self.progress_window = FlameProgressWindow(
                'Rendering...', 10,
                text='Rendering: Batch 1 of 5',
                enable_done_button=True)

        To update progress bar:

            self.progress_window.set_progress_value(number_of_things_done)

        To enable or disable done button - True or False:

            self.progress_window.enable_done_button(True)
    '''

    def __init__(
            self,
            window_title,
            num_to_do,
            text='',
            window_bar_color='blue',
            enable_cancel_button=True,
            parent=None):

        super(FlameProgressWindow, self).__init__()

        self.cancelled = False

        # Check argument types

        if not isinstance(window_title, str):
            raise TypeError('FlameProgressWindow: window_title must be a string')
        if not isinstance(num_to_do, int):
            raise TypeError('FlameProgressWindow: num_to_do must be an integer')
        if not isinstance(text, str):
            raise TypeError('FlameProgressWindow: text must be a string')
        if not isinstance(enable_cancel_button, bool):
            raise TypeError('FlameProgressWindow: enable_done_button must be a boolean')
        if window_bar_color not in ['blue', 'red', 'green', 'yellow', 'gray', 'teal']:
            raise ValueError('FlameWindow: Window Bar Color must be one of: '
                             'blue, red, green, yellow, gray, teal.')

        self.window_bar_color = window_bar_color

        # Build window

        # Mac needs this to close the window
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.setWindowFlags(
                QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setMinimumSize(QtCore.QSize(500, 330))
        self.setMaximumSize(QtCore.QSize(500, 330))
        self.setStyleSheet('background-color: rgb(36, 36, 36)')

        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.move((resolution.width() / 2) - (self.frameSize().width() / 2),
                  (resolution.height() / 2) - (self.frameSize().height() / 2))

        self.setParent(parent)

        self.grid = QtWidgets.QGridLayout()

        self.main_label = FlameLabel(window_title, label_width=500)
        self.main_label.setStyleSheet('''
            color: rgb(154, 154, 154);
            font: 18px "Discreet"''')
        self.message_text_edit = QtWidgets.QTextEdit('')
        self.message_text_edit.setDisabled(True)
        self.message_text_edit.setStyleSheet('''
            QTextEdit {
                color: rgb(154, 154, 154);
                background-color: rgb(36, 36, 36);
                selection-color: rgb(190, 190, 190);
                selection-background-color: rgb(36, 36, 36);
                border: none;
                padding-left: 20px;
                padding-right: 20px;
                font: 12px "Discreet"}''')
        self.message_text_edit.setText(text)

        # Progress bar

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMaximum(num_to_do)
        self.progress_bar.setMaximumHeight(5)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet('''
            QProgressBar {
                color: rgb(154, 154, 154);
                background-color: rgb(45, 45, 45);
                font: 14px "Discreet";
                border: none}
            QProgressBar:chunk {
                background-color: rgb(0, 110, 176)}''')

        self.cancel_button = FlameButton(
                'Cancel',
                self.cancel,
                button_color='normal',
                button_width=110)
        self.cancel_button.setEnabled(enable_cancel_button)
        self.cancel_button.setVisible(enable_cancel_button)

        # Layout

        self.grid.addWidget(self.main_label, 0, 0)
        self.grid.setRowMinimumHeight(1, 30)
        self.grid.addWidget(self.message_text_edit, 2, 0, 1, 4)
        self.grid.addWidget(self.progress_bar, 8, 0, 1, 7)
        self.grid.setRowMinimumHeight(9, 30)
        self.grid.addWidget(self.cancel_button, 10, 6)
        self.grid.setRowMinimumHeight(11, 30)

        self.setLayout(self.grid)
        self.show()

    def set_text(self, text):

        self.message_text_edit.setText(text)

    def set_progress_value(self, value):

        self.progress_bar.setValue(value)

    def enable_cancel_button(self, value):

        if value:
            self.cancel_button.setEnabled(True)
        else:
            self.cancel_button.setEnabled(False)

    def cancel(self):

        self.cancelled = True
        self.close()

    def paintEvent(self, event):

        painter = QtGui.QPainter(self)
        if self.window_bar_color == 'blue':
            bar_color = QtGui.QColor(0, 110, 176)
        elif self.window_bar_color == 'red':
            bar_color = QtGui.QColor(200, 29, 29)
        elif self.window_bar_color == 'green':
            bar_color = QtGui.QColor(0, 180, 13)
        elif self.window_bar_color == 'yellow':
            bar_color = QtGui.QColor(251, 181, 73)
        elif self.window_bar_color == 'gray':
            bar_color = QtGui.QColor(71, 71, 71)
        elif self.window_bar_color == 'teal':
            bar_color = QtGui.QColor(14, 110, 106)

        # painter.setPen(QtGui.QPen(QtGui.QColor(71, 71, 71), .5, QtCore.Qt.SolidLine))
        # painter.drawLine(0, 40, 500, 40)

        # Draw line below title that goes from side bar color to grey

        gradient = QtGui.QLinearGradient(0, 0, 500, 40)
        gradient.setColorAt(1, QtGui.QColor(71, 71, 71))
        gradient.setColorAt(0, bar_color)
        painter.setPen(QtGui.QPen(gradient, .5, QtCore.Qt.SolidLine))
        painter.drawLine(0, 40, 500, 40)

        # Draw bar on left side of window

        painter.setPen(QtGui.QPen(bar_color, 6, QtCore.Qt.SolidLine))
        painter.drawLine(0, 0, 0, 330)

    def mousePressEvent(self, event):

        self.oldPosition = event.globalPos()

    def mouseMoveEvent(self, event):

        try:
            delta = QtCore.QPoint(event.globalPos() - self.oldPosition)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPosition = event.globalPos()
        except:
            pass


class FlameTokenPushButton(QtWidgets.QPushButton):
    '''
    Custom Qt Flame Token Push Button Widget v2.1

    button_name: Text displayed on button [str]
    token_dict: Dictionary defining tokens. {'Token Name': '<Token>'} [dict]
    token_dest: LineEdit that token will be applied to [object]
    button_width: (optional) default is 150 [int]
    button_max_width: (optional) default is 300 [int]

    Usage:

        token_dict = {'Token 1': '<Token1>', 'Token2': '<Token2>'}
        token_push_button = FlameTokenPushButton('Add Token', token_dict, token_dest)
    '''

    def __init__(self, button_name, token_dict, token_dest, button_width=110,
                 button_max_width=300):
        super(FlameTokenPushButton, self).__init__()

        self.setText(button_name)
        self.setMinimumHeight(28)
        self.setMinimumWidth(button_width)
        self.setMaximumWidth(button_max_width)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setStyleSheet('''
            QPushButton {
                color: rgb(154, 154, 154);
                background-color: rgb(45, 55, 68);
                border: none;
                font: 14px "Discreet";
                padding-left: 6px;
                text-align: left}
            QPushButton:hover {
                border: 1px solid rgb(90, 90, 90)}
            QPushButton:disabled {
                color: rgb(106, 106, 106);
                background-color: rgb(45, 55, 68);
                border: none}
            QPushButton::menu-indicator {
                subcontrol-origin: padding;
                subcontrol-position: center right}
            QToolTip {
                color: rgb(170, 170, 170);
                background-color: rgb(71, 71, 71);
                border: 10px solid rgb(71, 71, 71)}''')

        def token_action_menu():

            def insert_token(token):
                for key, value in token_dict.items():
                    if key == token:
                        token_name = value
                        token_dest.insert(token_name)

            # the lambda sorts aAbBcC instead of ABCabc
            for key, value in sorted(token_dict.items(), key=lambda v: v[0].upper()):
                del value
                token_menu.addAction(key, partial(insert_token, key))

        token_menu = QtWidgets.QMenu(self)
        token_menu.setFocusPolicy(QtCore.Qt.NoFocus)
        token_menu.setStyleSheet('''
            QMenu {
                color: rgb(154, 154, 154);
                background-color: rgb(45, 55, 68);
                border: none; font: 14px "Discreet"}
            QMenu::item:selected {
                color: rgb(217, 217, 217);
                background-color: rgb(58, 69, 81)}''')

        self.setMenu(token_menu)
        token_action_menu()


class FlameTableWidget(QtWidgets.QTableWidget):
    '''
    Custom Qt Widget Flame Table Widget v1.0.0

    Attributes:

        column_headers: list of headers for the table

    Usage:

        flame_table = FlameTableWidget(['header1', 'header2'])
    '''

    def __init__(self, column_headers):
        super(FlameTableWidget, self).__init__()

        self.setMinimumSize(500, 250)
        self.setColumnCount(len(column_headers))
        self.setRowCount(1)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setHorizontalHeaderLabels(column_headers)
        self.setStyleSheet('''
            QTableWidget {
                background-color: rgb(33, 33, 33);
                alternate-background-color: rgb(36, 36, 36);
                color: rgb(190, 190, 190);
                font: 14px "Discreet";
                gridline-color: rgb(33, 33, 33)}
            QTableWidget::item {
                border: 0px 10px 0px 0px;
                padding: 0px 15px 0px 5px}
            QTableWidget::item:selected {
                color: #d9d9d9;
                background-color: #474747}
            QHeaderView::section {
                color: black;
                font: 14px "Discreet"}''')

        self.header_horiz = self.horizontalHeader()
        self.header_horiz.setDefaultAlignment(QtCore.Qt.AlignLeft)
        self.header_horiz.setStyleSheet('''
            ::section {
                border: 0px;
                color: rgb(177, 177, 177);
                background-color: rgb(19, 21, 23);
                padding: 3px 3px 0px 8px}''')

        self.header_vert = self.verticalHeader()
        self.header_vert.setDefaultSectionSize(24)
        self.header_vert.setVisible(False)
        self.header_vert.setStyleSheet('''
                ::section {
                    border: 0px;
                    padding 0px}''')

    def add_item(self, row, column, item):
        '''Add row if necessary, then add item to column.'''

        if row + 1 > self.rowCount():
            self.insertRow(row)

        self.setItem(row, column, QtWidgets.QTableWidgetItem(item))

    def get_data_by_row_number(self, row_num):
        '''
        Convenience method to get data from specific row number.

        Returns:
            A list of the data per column.
        '''

        data = []

        for column in range(self.columnCount()):
            data.append(self.model().data(self.model().index(row_num, column)))

        return data

    def get_selected_row_data(self):
        '''
        Convenience method to get data from selected rows.

        Returns:
            A list containing a list for each selected row.
        '''

        data = []

        for row in self.selectionModel().selectedRows():
            row_data = []

            for column in range(self.columnCount()):
                row_data.append(
                        self.model().data(self.model().index(row.row(), column)))
            data.append(row_data)

        return data


class FindSegmentApplyText(object):
    '''
    Find specific segments in a selection, assemble a Text TimelineFX setup path using
    tokens, then load the setup to the specified segments.
    '''

    def __init__(self, selection):

        self.selection = selection

        self.message(TITLE_VERSION)
        self.message('Script called from {}'.format(__file__))

        self.segments = []
        self.find_segments()

        self.now = dt.datetime.now()
        self.segment_tokens = {}

        self.table_columns = [
                'Segment #', 'Sequence', 'Segment', 'Record In', 'Record Out',
                'Filename']

        self.main_window()

    @staticmethod
    def message(string):
        '''Print message to shell window and append global MESSAGE_PREFIX.'''

        print(' '.join([MESSAGE_PREFIX, string]))

    @staticmethod
    def get_parent_sequence(child):
        '''Returns object of the container sequence for the given flame object.'''

        parents = []

        while child:
            if isinstance(child, flame.PySequence):
                break
            child = child.parent
            parents.append(child)

        parent_sequence = parents[-1]
        return parent_sequence

    @staticmethod
    def get_setups_path(root_path):
        '''Standard path for project text setups.'''

        project = flame.project.current_project.name
        path = os.path.join(root_path, project, 'text', 'flame')
        return path

    def find_segments(self):
        '''Assemble list of all PySegments in selected Sequences.'''

        self.message('Scanning for segments...')

        for sequence in self.selection:
            for version in sequence.versions:
                for track in version.tracks:
                    for segment in track.segments:
                        if segment.type == 'Gap':  # too many gaps in the results IMHO
                            pass
                        else:
                            self.segments.append(segment)

        self.message('Found {} segments'.format(len(self.segments)))

    def generate_segment_tokens(self, segment):
        '''Populate the token list.'''

        self.segment_tokens['am/pm'] = [
                '<pp>', self.now.strftime('%p').lower()]
        self.segment_tokens['AM/PM'] = [
                '<PP>', self.now.strftime('%p').upper()]
        self.segment_tokens['Day'] = [
                '<DD>', self.now.strftime('%d')]
        self.segment_tokens['Hour (12hr)'] = [
                '<hh>', self.now.strftime('%I')]
        self.segment_tokens['Hour (24hr)'] = [
                '<HH>', self.now.strftime('%H')]
        self.segment_tokens['Minute'] = [
                '<mm>', self.now.strftime('%M')]
        self.segment_tokens['Month'] = [
                '<MM>', self.now.strftime('%m')]
        self.segment_tokens['Project'] = [
                '<project>', flame.project.current_project.name]
        self.segment_tokens['Segment Name'] = [
                '<segment name>', segment.name.get_value()]
        self.segment_tokens['Sequence Name'] = [
                '<name>', self.get_parent_sequence(segment).name.get_value()]
        self.segment_tokens['User'] = [
                '<user>', flame.users.current_user.name]
        self.segment_tokens['Year'] = [
                '<YYYY>', self.now.strftime('%Y')]

    def resolve_tokens(self, pattern):
        '''Replace tokens with values.'''

        result = pattern

        for token, values in self.segment_tokens.items():
            del token
            result = re.sub(values[0], values[1], result)

        return result

    def apply_text_fx_to_segment(self, segment, text_setup):
        '''Apply Text TimelineFX to segment, then load setup.'''

        for effect in segment.effects:
            if effect.type == 'Text':
                flame.delete(effect)

        segment_text_fx = segment.create_effect('Text')

        self.message('Loading {}'.format(text_setup))

        if os.path.isfile(text_setup):
            try:
                # load_setup will not take utf-8, only ascii
                segment_text_fx.load_setup(text_setup.encode('ascii', 'ignore'))
            except RuntimeError:
                self.message('Error loading setup!')
            else:
                self.message('Successfully loaded!')
        else:
            self.message('File does not exist!')

    def main_window(self):
        '''The main GUI.'''

        def okay_button():
            '''Close window and process the artist's selected selection.'''

            self.window.close()

            row_data = self.segments_table.get_selected_row_data()

            self.progress_window = FlameProgressWindow(
                    'Progress', len(row_data))

            for row in row_data:
                if self.progress_window.cancelled:
                    break

                self.message('Proceeding with {} in {} at {}'.format(
                    row[2], row[1], row[3]))

                self.progress_window.set_text(
                        'Apply Text TimlineFX to {} in {} at {}'.format(
                             row[2], row[1], row[3]))

                self.apply_text_fx_to_segment(self.segments[int(row[0]) - 1], row[5])

                self.progress_window.set_progress_value(
                        row_data.index(row) + 1)

            self.progress_window.close()

            if self.progress_window.cancelled:
                self.message('Cancelled!')
            else:
                self.message('Done!')

        def cancel_button():
            '''Cancel python hook and close UI.'''

            self.window.close()
            self.message('Cancelled!')

        def filter_table():
            '''Updates the table when anything is typed in the Find bar.'''

            for num in range(self.segments_table.rowCount()):
                if (self.find.text() in
                        self.segments_table.get_data_by_row_number(num)[2]):
                    self.segments_table.showRow(num)
                else:
                    self.segments_table.hideRow(num)

        def update_filename_column():
            '''Update the filename column when the filename line edit is changed.'''

            for count, segment in enumerate(self.segments):
                self.generate_segment_tokens(segment)
                self.segments_table.add_item(
                        count, 5, self.resolve_tokens(self.pattern.text()))

        def verify_filename_column_exists():
            '''Check if filename for text setup exists, if not, color cell text red.'''

            for row in range(self.segments_table.rowCount()):
                if not os.path.isfile(
                        self.segments_table.get_data_by_row_number(row)[5]):
                    self.segments_table.item(row, 5).setData(
                            QtCore.Qt.ForegroundRole, QtGui.QColor(190, 34, 34))

        def pattern_changed():
            '''Everything to refresh when the pattern line edit is changed.'''

            update_filename_column()
            self.segments_table.resizeColumnsToContents()
            verify_filename_column_exists()

        def populate_table():
            '''Fill in the table.'''

            for count, segment in enumerate(self.segments):
                self.generate_segment_tokens(segment)
                self.segments_table.add_item(
                        count, 0, str(count + 1).zfill(4))
                self.segments_table.add_item(
                        count, 1, self.get_parent_sequence(segment).name.get_value())
                self.segments_table.add_item(
                        count, 2, segment.name.get_value())
                self.segments_table.add_item(
                        count, 3, segment.record_in.timecode)
                self.segments_table.add_item(
                        count, 4, segment.record_out.timecode)
                self.segments_table.add_item(
                        count, 5, self.resolve_tokens(self.pattern.text()))

            verify_filename_column_exists()
            self.segments_table.resizeColumnsToContents()

        self.window = QtWidgets.QWidget()

        self.window.setMinimumSize(1400, 600)
        self.window.setStyleSheet('background-color: #272727')
        self.window.setWindowTitle(TITLE_VERSION)

        # Mac needs this to close the window
        self.window.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # FlameLineEdit class needs this
        self.window.setFocusPolicy(QtCore.Qt.StrongFocus)

        # Center Window
        resolution = QtWidgets.QDesktopWidget().screenGeometry()

        self.window.move(
                (resolution.width() / 2) - (self.window.frameSize().width() / 2),
                (resolution.height() / 2) - (self.window.frameSize().height() / 2))

        # Label
        self.find_label = FlameLabel('Find Segment')
        self.pattern_label = FlameLabel('Filename Pattern')

        # Line Edit
        self.find = FlameLineEdit('')
        self.find.textChanged.connect(filter_table)

        self.pattern = FlameLineEdit(DEFAULT_PATTERN)
        self.pattern.textChanged.connect(pattern_changed)

        # Table
        self.segments_table = FlameTableWidget(self.table_columns)
        populate_table()

        # Buttons
        self.tokens_btn = FlameTokenPushButton(
            'Add Token',
            # self.segment_tokens is a dict with a nested set for each key
            # FlameTokenPushButton wants a dict that is only {token_name: token}
            # so need to simplify it with a dict comprehension
            {key: values[0] for key, values in self.segment_tokens.items()},
            self.pattern)
        self.ok_btn = FlameButton('Ok', okay_button, button_color='blue')
        self.ok_btn.setAutoDefault(True)  # doesnt make Enter key work

        self.cancel_btn = FlameButton('Cancel', cancel_button)

        # Layout
        self.grid = QtWidgets.QGridLayout()
        self.grid.setHorizontalSpacing(10)
        self.grid.setVerticalSpacing(10)

        self.grid.addWidget(self.find_label, 0, 0)
        self.grid.addWidget(self.find, 0, 1)
        self.grid.addWidget(self.pattern_label, 1, 0)
        self.grid.addWidget(self.pattern, 1, 1)
        self.grid.addWidget(self.tokens_btn, 1, 2)

        self.hbox = QtWidgets.QHBoxLayout()
        self.hbox.addWidget(self.segments_table)

        self.hbox2 = QtWidgets.QHBoxLayout()
        self.hbox2.addStretch(1)
        self.hbox2.addWidget(self.cancel_btn)
        self.hbox2.addWidget(self.ok_btn)

        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setMargin(20)
        self.vbox.addLayout(self.grid)
        self.vbox.insertSpacing(1, 20)
        self.vbox.addLayout(self.hbox)
        self.vbox.insertSpacing(3, 20)
        self.vbox.addLayout(self.hbox2)

        self.window.setLayout(self.vbox)

        self.window.show()
        return self.window


def scope_timeline(selection):

    for item in selection:
        if isinstance(item, flame.PyClip):
            return True
    return False


def get_media_panel_custom_ui_actions():

    return [{'name': 'Apply...',
             'actions': [{'name': 'Text TimelineFX to Segments',
                          'isVisible': scope_timeline,
                          'execute': FindSegmentApplyText,
                          'minimumVersion': '2021.1'}]
            }]
