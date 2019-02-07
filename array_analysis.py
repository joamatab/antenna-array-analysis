# -*- coding: utf-8 -*-
"""
    Antenna Array Analysis
    Copyright (C) 2019  Zhengyu Peng

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import sys
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtCore import QThread

from linear_array import Linear_Array

import pyqtgraph as pg
#pg.setConfigOption('background', 'w')
#pg.setConfigOption('foreground', 'k')
#pg.setConfigOption('antialias', True)
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)


class MyApp(QtWidgets.QMainWindow):
    def __init__(self):
        super(QtWidgets.QMainWindow, self).__init__()
        self.ui = uic.loadUi('array_analysis.ui', self)

        self.pgCanvas = pg.GraphicsLayoutWidget()
        self.figureLayout.addWidget(self.pgCanvas)
        self.plotView = self.pgCanvas.addPlot()
        self.pgFigure = pg.PlotDataItem()
        self.pgFigure.setDownsampling(auto=True, method='peak')
        self.plotView.setXRange(-90, 90)
        self.plotView.setYRange(-80, 0)

        self.plotView.addItem(self.pgFigure)
        self.plotView.setLabel(axis='bottom', text='Angle', units='°')
        self.plotView.setLabel(
            axis='left', text='Normalized amplitude', units='dB')
        self.plotView.showGrid(x=True, y=True, alpha=0.5)

        self.initUI()

        self.ui.spinBox_ArraySize.valueChanged.connect(
            self.arraySizeValueChanged)

        self.ui.doubleSpinBox_Spacing.valueChanged.connect(
            self.spacingValueChanged)

        self.ui.doubleSpinBox_Step.valueChanged.connect(
            self.plotStepValueChanged)

        self.ui.doubleSpinBox_SteeringAngle.valueChanged.connect(
            self.steeringAngleValueChanged)
        self.ui.horizontalSlider_SteeringAngle.valueChanged.connect(
            self.steeringAngleSliderMoved)

        self.ui.comboBox_Window.currentIndexChanged.connect(
            self.windowComboBoxChanged)

        self.ui.spinBox_SLL.valueChanged.connect(self.sllValueChange)
        self.ui.horizontalSlider_SLL.valueChanged.connect(self.sllSliderMoved)

        self.ui.spinBox_nbar.valueChanged.connect(self.nbarValueChange)
        self.ui.horizontalSlider_nbar.valueChanged.connect(
            self.nbarSliderMoved)

        self.linear_array = Linear_Array()
        self.linear_array_thread = QThread()
        self.linear_array.patternReady.connect(self.updatePattern)
        self.linear_array_thread.started.connect(
            self.linear_array.calculatePattern)
        self.linear_array.moveToThread(self.linear_array_thread)
        self.linear_array_thread.start()

        self.updateLinearArrayParameter()
        self.ui.show()

    def initUI(self):
        self.ui.spinBox_SLL.setVisible(False)
        self.ui.label_SLL.setVisible(False)
        self.ui.horizontalSlider_SLL.setVisible(False)
        self.ui.spinBox_nbar.setVisible(False)
        self.ui.label_nbar.setVisible(False)
        self.ui.horizontalSlider_nbar.setVisible(False)

        self.ui.comboBox_Window.addItems(
            ['Square', 'Chebyshev', 'Taylor', 'Hamming', 'Hann'])

    def arraySizeValueChanged(self, value):
        self.updateLinearArrayParameter()

    def spacingValueChanged(self, value):
        self.updateLinearArrayParameter()

    def plotStepValueChanged(self):
        self.updateLinearArrayParameter()

    def steeringAngleValueChanged(self, value):
        self.ui.horizontalSlider_SteeringAngle.setValue(
            self.ui.doubleSpinBox_SteeringAngle.value() * 10)
        self.updateLinearArrayParameter()

    def steeringAngleSliderMoved(self, value):
        self.ui.doubleSpinBox_SteeringAngle.setValue(value / 10)
        self.updateLinearArrayParameter()

    def windowComboBoxChanged(self, value):
        if value == 0:
            self.ui.spinBox_SLL.setVisible(False)
            self.ui.label_SLL.setVisible(False)
            self.ui.horizontalSlider_SLL.setVisible(False)
            self.ui.spinBox_nbar.setVisible(False)
            self.ui.label_nbar.setVisible(False)
            self.ui.horizontalSlider_nbar.setVisible(False)
        elif value == 1:
            self.ui.spinBox_SLL.setVisible(True)
            self.ui.label_SLL.setVisible(True)
            self.ui.horizontalSlider_SLL.setVisible(True)
            self.ui.spinBox_nbar.setVisible(False)
            self.ui.label_nbar.setVisible(False)
            self.ui.horizontalSlider_nbar.setVisible(False)
        elif value == 2:
            self.ui.spinBox_SLL.setVisible(True)
            self.ui.label_SLL.setVisible(True)
            self.ui.horizontalSlider_SLL.setVisible(True)
            self.ui.spinBox_nbar.setVisible(True)
            self.ui.label_nbar.setVisible(True)
            self.ui.horizontalSlider_nbar.setVisible(True)
        elif value == 3:
            self.ui.spinBox_SLL.setVisible(False)
            self.ui.label_SLL.setVisible(False)
            self.ui.horizontalSlider_SLL.setVisible(False)
            self.ui.spinBox_nbar.setVisible(False)
            self.ui.label_nbar.setVisible(False)
            self.ui.horizontalSlider_nbar.setVisible(False)
        elif value == 4:
            self.ui.spinBox_SLL.setVisible(False)
            self.ui.label_SLL.setVisible(False)
            self.ui.horizontalSlider_SLL.setVisible(False)
            self.ui.spinBox_nbar.setVisible(False)
            self.ui.label_nbar.setVisible(False)
            self.ui.horizontalSlider_nbar.setVisible(False)
        self.updateLinearArrayParameter()

    def sllValueChange(self, value):
        self.ui.horizontalSlider_SLL.setValue(self.ui.spinBox_SLL.value())
        self.updateLinearArrayParameter()

    def sllSliderMoved(self, value):
        self.ui.spinBox_SLL.setValue(value)
        self.updateLinearArrayParameter()

    def nbarValueChange(self, value):
        self.ui.horizontalSlider_nbar.setValue(self.ui.spinBox_nbar.value())
        self.updateLinearArrayParameter()

    def nbarSliderMoved(self, value):
        self.ui.spinBox_nbar.setValue(value)
        self.updateLinearArrayParameter()

    def updateLinearArrayParameter(self):
        self.array_size = self.ui.spinBox_ArraySize.value()
        self.spacing = self.ui.doubleSpinBox_Spacing.value()
        self.beam_loc = self.ui.doubleSpinBox_SteeringAngle.value()
        self.plot_step = self.ui.doubleSpinBox_Step.value()
        self.window_type = self.ui.comboBox_Window.currentIndex()
        self.window_sll = self.ui.spinBox_SLL.value()
        self.window_nbar = self.ui.spinBox_nbar.value()

        self.linear_array.updateData(
            self.array_size, self.spacing, self.beam_loc, self.plot_step,
            self.window_type, self.window_sll, self.window_nbar)

    def updatePattern(self, angle, pattern):
        self.pgFigure.setData(angle, pattern)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
