import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')

import PyQt5.QtCore
from PyQt5.QtWidgets import QApplication, QDialog, QWidget, QGridLayout, QGroupBox, \
    QLabel, QLineEdit, QListWidget, QListWidgetItem, \
    QPushButton, QHBoxLayout, QVBoxLayout, QTableWidget, QTableWidgetItem, QTabWidget, \
    QSizePolicy

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

data_absp = np.loadtxt('absorption.dat')
data_spon = np.loadtxt("spontaneous.dat")
data_levl = np.loadtxt("levels.dat")

def reorder_data():
    # reorder the data so that lower_level -> higher_level, i.e., E1 < E2
    idx = data_absp[:,8]<0              # find all rows of data with freq < 0
    data_absp[idx,8] = -data_absp[idx,8]
    data_absp[idx,9] = -data_absp[idx,9]
    data_absp[idx,10] = -data_absp[idx,10]
    tmp, data_absp[idx,0] = data_absp[idx,0], data_absp[idx,4]
    data_absp[idx,4] = tmp
    tmp, data_absp[idx,1] = data_absp[idx,1], data_absp[idx,5]
    data_absp[idx,5] = tmp
    tmp, data_absp[idx,2] = data_absp[idx,2], data_absp[idx,6]
    data_absp[idx,6] = tmp
    tmp, data_absp[idx,3] = data_absp[idx,3], data_absp[idx,7]
    data_absp[idx,7] = tmp

class TableWidget(QDialog):
    def __init__(self, sigSelected, parent=None):
        super().__init__(parent)
        self.sigSelected = sigSelected

        self.tableWidget = QTableWidget()
        self.button = QPushButton("Select")
        self.button.clicked.connect(self.on_button_clicked)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.tableWidget)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)
        self.setGeometry(300, 300, 1300, 900)

    def on_button_clicked(self):
        idx = self.tableWidget.currentRow()
        self.sigSelected.emit(idx)
        self.close()

    def update_data(self, data, header):
        self.tableWidget.clear()
        (n_row, n_col) = np.shape(data)
        self.tableWidget.setRowCount(n_row)
        self.tableWidget.setColumnCount(n_col)
        self.tableWidget.setHorizontalHeaderLabels(header)
        for i in range(n_row):
            for j in range(n_col):
                self.tableWidget.setItem(i, j, QTableWidgetItem(str(data[i, j])))

class ParamsPanel(QWidget):
    def __init__(self, sigParamSet, parent=None):
        super().__init__(parent)
        self.sigParamSet = sigParamSet

        self.lblTHzFreq = QLabel("THz frequency range (THz):")
        self.lblDash = QLabel("-")
        #
        self.edtTHzFreqLower = QLineEdit()
        self.edtTHzFreqUpper = QLineEdit()
        self.btnTHz = QPushButton("Search...")
        self.btnTHz.clicked.connect(self.on_btnTHz_clicked)
        #
        self.layoutTHz = QHBoxLayout()
        self.layoutTHz.addWidget(self.lblTHzFreq)
        self.layoutTHz.addWidget(self.edtTHzFreqLower)
        self.layoutTHz.addWidget(self.lblDash)
        self.layoutTHz.addWidget(self.edtTHzFreqUpper)
        self.layoutTHz.addWidget(self.btnTHz)
        #
        self.groupTHz = QGroupBox('THz Parameters - searching in "absorption.dat":')
        self.groupTHz.setLayout(self.layoutTHz)
        #
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.groupTHz)

        self.setLayout(self.layout)

    def on_btnTHz_clicked(self):
        self.sigParamSet.emit()

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=6, height=4):
        fig = Figure(figsize=(width, height), dpi=100)
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.ax = self.figure.add_subplot(1, 1, 1)

    def plot(self, data):
        self.ax.cla()
        # draw levels of upper and lower Rydberg levels
        self.ax.hlines(data.lower_rydberg_level[4], data.lower_rydberg_level[1]-0.2, data.lower_rydberg_level[1]+0.2, colors='k')
        self.ax.hlines(data.upper_rydberg_level[4], data.upper_rydberg_level[1]-0.2, data.upper_rydberg_level[1]+0.2, colors='k')
        
        if data.exci_path: # if the list is not empty
            for i, path in enumerate(data.exci_path):
                # draw levels of exci_path
                self.ax.hlines(path[4], path[1]-0.2, path[1]+0.2, colors='r')
                # draw transitions of exci_path
                if i == 0:
                    self.ax.plot([path[1], data.lower_rydberg_level[1]], [path[4], data.lower_rydberg_level[4]], 'r')
                else:
                    self.ax.plot([path[1], data.exci_path[i-1][1]], [path[4], data.exci_path[i-1][4]], 'r')
        
        if data.spon_path: # if the list is not empty
            for i, path in enumerate(data.spon_path):
                # draw levels of spon_path
                self.ax.hlines(path[3], path[1]-0.2, path[1]+0.2, colors='g')
                # draw transitions of spon_path
                if i == 0:
                    self.ax.plot([data.upper_rydberg_level[1], path[1]], [data.upper_rydberg_level[4], path[3]], 'g')
                else:
                    self.ax.plot([data.spon_path[i-1][1], path[1]], [data.spon_path[i-1][3], path[3]], 'g')

        self.ax.set_xlabel('l number')
        self.ax.set_ylabel('Energy (eV)')
        self.draw()

class SchemeData():

    def __init__(self):
        self.reset()

    def reset(self):
        self.lower_rydberg_level = []
        self.upper_rydberg_level = []
        self.exci_path = []
        self.spon_path = []


class ResultsPanel(QWidget):
    def __init__(self, sigExciPathSelected, sigSponPathSelected, parent=None):
        super().__init__(parent)
        self.sigExciPathSelected = sigExciPathSelected
        self.sigSponPathSelected = sigSponPathSelected

        self.lblTHzDetect = QLabel('')

        self.lblRydLevUpper = QLabel("Upper Rydberg level")
        self.lblRydLevLower = QLabel("Lower Rydberg level")

        self.btnRydLevUpper = QPushButton('Select fluorescence transition...')
        self.btnRydLevUpper.setEnabled(False)
        self.btnRydLevUpper.clicked.connect(self.on_btnRydLevUpper_clicked)
        self.btnRydLevLower = QPushButton('Select excitation path(s)...')
        self.btnRydLevLower.setEnabled(False)
        self.btnRydLevLower.clicked.connect(self.on_btnRydLevLower_clicked)

        self.layout = QGridLayout()

        self.layout.addWidget(self.lblTHzDetect,   0, 0, 1, 1)
        self.layout.addWidget(self.lblRydLevUpper, 1, 0, 1, 3)
        self.layout.addWidget(self.btnRydLevUpper, 1, 3, 1, 1)
        self.layout.addWidget(self.lblRydLevLower, 2, 0, 1, 3)
        self.layout.addWidget(self.btnRydLevLower, 2, 3, 1, 1)

        self.tabPaths = QTabWidget()

        self.lblSponPaths = QLabel('')
        self.layoutSponPaths = QGridLayout()
        self.layoutSponPaths.addWidget(self.lblSponPaths, 1, 0, 1, 3)
        self.btnSponPaths = QPushButton('Add...')
        self.btnSponPaths.setVisible(False)
        self.btnSponPaths.clicked.connect(self.on_btnSponPaths_clicked)
        self.layoutSponPaths.addWidget(self.btnSponPaths, 2, 0, 1, 1)
        self.panelSponPaths = QWidget()
        self.panelSponPaths.setLayout(self.layoutSponPaths)
        self.tabPaths.addTab(self.panelSponPaths, 'Spon paths')                
        
        self.lblExciPaths = QLabel('')
        self.layoutExciPaths = QGridLayout()
        self.layoutExciPaths.addWidget(self.lblExciPaths, 1, 0, 1, 3)
        self.btnExciPaths = QPushButton('Add...')
        self.btnExciPaths.setVisible(False)
        self.btnExciPaths.clicked.connect(self.on_btnExciPaths_clicked)
        self.layoutExciPaths.addWidget(self.btnExciPaths, 2, 0, 1, 1)
        self.panelExciPaths = QWidget()
        self.panelExciPaths.setLayout(self.layoutExciPaths)
        self.tabPaths.addTab(self.panelExciPaths, 'Exci paths')

        self.layout.addWidget(self.tabPaths, 3, 0, 1, 2)

        self.canvas = PlotCanvas(self)
        self.layout.addWidget(self.canvas, 3, 2, 1, 2)

        self.setLayout(self.layout)
    
    def add_exci_path(self, levels):
        labelText = '\n'
        for i, level in enumerate(levels):
            labelText += 'Exci path ' + str(i) + ': (' + \
                str(int(level[0])) + ', ' + \
                str(int(level[1])) + ', ' + \
                str(level[2]) + ', ' + \
                str(level[3]) + ')\n'
            labelText += '@' + str(level[6]) + ' nm (' + str(level[7]) + ')\n'
        self.lblExciPaths.setText(labelText)
        self.btnExciPaths.setVisible(True)

    def add_spon_path(self, levels):
        labelText = '\n'
        for i, level in enumerate(levels):
            labelText += 'Spon path ' + str(i) + ': (' + \
                str(int(level[0])) + ', ' + \
                str(int(level[1])) + ', ' + \
                str(level[2]) + ')\n'
            labelText += '@' + str(level[5]) + ' nm (' + str(level[6]) + ')\n'
        self.lblSponPaths.setText(labelText)
        self.btnSponPaths.setVisible(True)

    def on_btnRydLevUpper_clicked(self):
        self.sigSponPathSelected.emit('seek-spon-0')

    def on_btnRydLevLower_clicked(self):
        self.sigExciPathSelected.emit('seek-exci-0')

    def on_btnSponPaths_clicked(self):
        self.sigSponPathSelected.emit('seek-spon')

    def on_btnExciPaths_clicked(self):
        self.sigExciPathSelected.emit('seek-exci')

    def clear(self):
        self.lblExciPaths.setText('\n')
        self.lblSponPaths.setText('\n')
        self.btnExciPaths.setVisible(False)
        self.btnSponPaths.setVisible(False)

    def updateCanvas(self, data):
        self.canvas.plot(data)
        pass

def get_energy_and_lifetime(n, l, j):
    line = data_levl[(data_levl[:,0]==n) & (data_levl[:,1]==l) & (data_levl[:,2]==j)][0]
    return line[3], line[4]


class MainWidget(QWidget):
    # signals
    signal_level_selected = PyQt5.QtCore.pyqtSignal(int) # table of level list
    signal_param_set = PyQt5.QtCore.pyqtSignal() # panel of parameters
    signal_exci_path_selected = PyQt5.QtCore.pyqtSignal(str)
    signal_spon_path_selected = PyQt5.QtCore.pyqtSignal(str)
    

    def __init__(self, parent=None):
        super().__init__(parent)

        self.data = SchemeData()
        self.curr_status = 'init'

        self.signal_level_selected.connect(self.on_level_selected)
        self.signal_param_set.connect(self.on_param_set)
        self.signal_exci_path_selected.connect(self.list_exci_paths)
        self.signal_spon_path_selected.connect(self.list_spon_radiation)

        self.on_level_selected_at_stage = {\
            'init':self.on_thz_levels_ready, \
            'thz-ready':self.selc_step_2, \
            'seek-exci-0':self.on_exci_src_level_found, \
            'seek-spon-0':self.on_spon_des_level_found, \
            'seek-exci':self.on_exci_src_level_found, \
            'seek-spon':self.on_spon_des_level_found}
        
        self.panelParams = ParamsPanel(self.signal_param_set, self)
        self.panelResults = ResultsPanel(self.signal_exci_path_selected, self.signal_spon_path_selected, self)
        self.dlgTHzSelcTable = TableWidget(self.signal_level_selected, self)
        self.dlgSponTransTable = TableWidget(self.signal_level_selected, self)
        self.dlgExciTransTable = TableWidget(self.signal_level_selected, self)

        self.layoutMain = QVBoxLayout()
        self.layoutMain.addWidget(self.panelParams)
        self.layoutMain.addWidget(self.panelResults)

        self.setLayout(self.layoutMain)      

    def set_THz_range(self):
        self.curr_status = 'init'
        self.data.reset()
        self.panelResults.clear()
        freq_lower = float(self.panelParams.edtTHzFreqLower.text())
        freq_upper = float(self.panelParams.edtTHzFreqUpper.text())
        freq = abs(data_absp[:,8])
        lines = data_absp[(freq>freq_lower) & (freq<freq_upper)]
        self.data_tblTHz = np.delete(lines, 9, 1) # remove the column of 'wavelength'
        header = ['n_lower', 'l_lower', 'j_lower', 'mj_lower', 'n_upper', 'l_upper', 'j_upper', 'mj_upper', 'Freq. (THz)', 'dipole']
        self.dlgTHzSelcTable.update_data(self.data_tblTHz, header)
        self.dlgTHzSelcTable.show()
    
    def on_param_set(self):
        self.set_THz_range()

    def on_level_selected(self, idx):
        self.on_level_selected_at_stage[self.curr_status](idx)
        print('table clicked - curr_status: ', self.curr_status)
        print('exci_path:', self.data.exci_path)
        print('spon_path:', self.data.spon_path)
        print('--------------------------')

    def on_thz_levels_ready(self, idx):
        self.curr_status = 'thz-ready'

        self.panelResults.lblTHzDetect.setText('Available THz detection: ' + \
            str(self.data_tblTHz[idx,8]) + ' THz (' + str(self.data_tblTHz[idx,9]) + ')')

        n, l, j, mj = self.data_tblTHz[idx,4:8]
        self.panelResults.lblRydLevUpper.setText('Upper Rydberg level: (' + \
            str(int(n)) + ', ' + str(int(l)) + ', ' + str(j) + ', ' + str(mj) + ')')
        energy, lifetime = get_energy_and_lifetime(n, l, j)
        self.data.upper_rydberg_level = [n, l, j, mj, energy, lifetime]

        n, l, j, mj = self.data_tblTHz[idx,:4]
        self.panelResults.lblRydLevLower.setText('Lower Rydberg level: (' + \
            str(int(n)) + ', ' + str(int(l)) + ', ' + str(j) + ', ' + str(mj) + ')')
        energy, lifetime = get_energy_and_lifetime(n, l, j)
        self.data.lower_rydberg_level = [n, l, j, mj, energy, lifetime]

        self.panelResults.btnRydLevUpper.setEnabled(True)
        self.panelResults.btnRydLevLower.setEnabled(True)

        self.panelResults.updateCanvas(self.data)

    def selc_step_2(self, idx):
        print('selc_step_2')

    def on_exci_src_level_found(self, idx):
        # when close the table of absorption transtion, with level selected and curr_status = seek-exci-0 or seek-exci
        print('exci_src_level_found:', idx)
        if self.curr_status == 'seek-exci-0':
            self.data.exci_path = []

        n, l, j, mj = self.data_tblExci[idx,0:4].tolist()
        energy, lifetime = get_energy_and_lifetime(n, l, j)
        wavelength, dipole = self.data_tblExci[idx,8], self.data_tblExci[idx,9]
        self.data.exci_path.append([n, l, j, mj, energy, lifetime, wavelength, dipole])
        self.panelResults.add_exci_path(self.data.exci_path)
        self.panelResults.updateCanvas(self.data)

    def on_spon_des_level_found(self, idx):
        # when close the table of spontaneous transtion, with level selected and curr_status = seek-spon-0 or seek-spon
        print('spon_des_level_found:', idx)
        if self.curr_status == 'seek-spon-0':
            self.data.spon_path = []

        n, l, j = self.data_tblSpon[idx,3:6].tolist()
        energy, lifetime = get_energy_and_lifetime(n, l, j)
        wavelength, rate = self.data_tblSpon[idx,6], self.data_tblSpon[idx,7]
        self.data.spon_path.append([n, l, j, energy, lifetime, wavelength, rate])
        self.panelResults.add_spon_path(self.data.spon_path)
        self.panelResults.updateCanvas(self.data)

    def list_spon_radiation(self, status):
        # when 'Select fluorescence transition...' or 'Add...' button in the 'Spon path' tab 
        # is clicked, show the transition table
        self.curr_status = status
        if self.curr_status == 'seek-spon-0':
            n, l, j = self.data.upper_rydberg_level[:3]
        elif self.curr_status == 'seek-spon':
            n, l, j = self.data.spon_path[-1][:3]
        else:
            print('Unknown curr_status')
        print('n', n, 'l', l, 'j', j)

        lines = data_spon[(data_spon[:,0]==n) & (data_spon[:,1]==l) & (data_spon[:,2]==j)]
        self.data_tblSpon = np.delete(lines, 6, 1) # remove the column of 'Freq.'
        header = ['n_upper', 'l_upper', 'j_upper', 'n_lower', 'l_lower', 'j_lower', 'λ (nm)', 'rate']
        self.dlgSponTransTable.update_data(self.data_tblSpon, header)
        self.dlgSponTransTable.show()

    def list_exci_paths(self, status):
        # when 'Select excitation path(s)...' or 'Add...' button in the 'Exci path' tab 
        # is clicked, show the transition table
        self.curr_status = status
        if self.curr_status == 'seek-exci-0':
            n, l, j, mj = self.data.lower_rydberg_level[:4]
        elif self.curr_status == 'seek-exci':
            n, l, j, mj = self.data.exci_path[-1][:4]
        else:
            print('Unknown curr_status')
        print('n', n, 'l', l, 'j', j, 'mj', mj)

        lines = data_absp[(data_absp[:,4]==n) & (data_absp[:,5]==l) & (data_absp[:,6]==j) & (data_absp[:,7]==mj)]
        self.data_tblExci = np.delete(lines, 8, 1) # remove the column of 'Freq.'
        header = ['n_lower', 'l_lower', 'j_lower', 'mj_lower', 'n_upper', 'l_upper', 'j_upper', 'mj_upper', 'λ (nm)', 'dipole']
        self.dlgExciTransTable.update_data(self.data_tblExci, header)
        self.dlgExciTransTable.show()


if __name__ == '__main__':

    reorder_data()

    app = QApplication([])
    mainWidget = MainWidget()
    mainWidget.show()
    app.exec_()