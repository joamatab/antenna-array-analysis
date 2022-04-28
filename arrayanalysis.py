"""
    Antenna Array Analysis

    Copyright (C) 2019  Zhengyu Peng
    E-mail: zpeng.me@gmail.com
    Website: https://zpeng.me

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

    `                      `
    -:.                  -#:
    -//:.              -###:
    -////:.          -#####:
    -/:.://:.      -###++##:
    ..   `://:-  -###+. :##:
           `:/+####+.   :##:
    .::::::::/+###.     :##:
    .////-----+##:    `:###:
     `-//:.   :##:  `:###/.
       `-//:. :##:`:###/.
         `-//:+######/.
           `-/+####/.
             `+##+.
              :##:
              :##:
              :##:
              :##:
              :##:
               .+:

"""

import sys
import res_rc
import webbrowser
from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtCore import QThread

import numpy as np
import matplotlib.cm as cm

from calpattern import CalPattern

import pyqtgraph as pg
import pyqtgraph.opengl as gl

# pg.setConfigOption('background', 'w')
# pg.setConfigOption('foreground', 'k')
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)


class AntArrayAnalysis(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        super(QtWidgets.QMainWindow, self).__init__()

        """Constants"""
        self.window_list = ['Square', 'Chebyshev', 'Taylor', 'Hamming', 'Hann']
        self.plot_list = ['3D (Az-El-Amp)', '2D Cartesian', '2D Polar',
                          'Array layout']
        self.array_config = {}
        self.fix_azimuth = False

        """Load UI"""
        self.ui = uic.loadUi('ui_array_analysis.ui', self)

        """Antenna array configuration"""
        self.calpattern = CalPattern()
        self.calpattern_thread = QThread()
        self.calpattern.patternReady.connect(self.update_figure)
        self.calpattern_thread.started.connect(
            self.calpattern.cal_pattern)
        self.calpattern.moveToThread(self.calpattern_thread)
        self.calpattern_thread.start()

        """Init UI"""
        self.init_ui()
        self.init_figure()

        self.new_params()
        self.ui.show()

    def init_ui(self):
        """Array config"""
        self.ui.sb_sizex.valueChanged.connect(self.new_params)
        self.ui.sb_sizey.valueChanged.connect(self.new_params)
        self.ui.dsb_spacingx.valueChanged.connect(self.new_params)
        self.ui.dsb_spacingy.valueChanged.connect(self.new_params)

        """Windows"""
        self.ui.cb_windowx.addItems(self.window_list)
        self.ui.cb_windowy.addItems(self.window_list)
        self.windowx_config(0)
        self.windowy_config(0)
        self.ui.cb_windowx.currentIndexChanged.connect(self.windowx_config)
        self.ui.cb_windowx.currentIndexChanged.connect(self.new_params)
        self.ui.cb_windowy.currentIndexChanged.connect(self.windowy_config)
        self.ui.cb_windowy.currentIndexChanged.connect(self.new_params)
        self.ui.sb_sidelobex.valueChanged.connect(self.new_params)
        self.ui.sb_sidelobey.valueChanged.connect(self.new_params)
        self.ui.sb_adjsidelobex.valueChanged.connect(self.new_params)
        self.ui.sb_adjsidelobey.valueChanged.connect(self.new_params)

        """Steering"""
        self.ui.dsb_angleaz.valueChanged.connect(self.az_changed)
        self.ui.hs_angleaz.valueChanged.connect(self.az_hs_moved)
        self.ui.dsb_angleel.valueChanged.connect(self.el_changed)
        self.ui.hs_angleel.valueChanged.connect(self.el_hs_moved)

        """Plot"""
        self.ui.cb_plottype.addItems(self.plot_list)
        self.ui.cb_plottype.currentIndexChanged.connect(self.plot_type_changed)

        self.ui.rb_azimuth.clicked.connect(self.rb_azimuth_clicked)

        self.ui.rb_elevation.clicked.connect(self.rb_elevation_clicked)

        self.ui.rbsb_azimuth.valueChanged.connect(self.fix_az_changed)
        self.ui.rbhs_azimuth.valueChanged.connect(self.fix_az_hs_moved)
        self.ui.rbsb_elevation.valueChanged.connect(self.fix_el_changed)
        self.ui.rbhs_elevation.valueChanged.connect(self.fix_el_hs_moved)

        self.ui.spinBox_polarMinAmp.valueChanged.connect(
            self.polar_min_amp_value_changed)
        self.ui.horizontalSlider_polarMinAmp.valueChanged.connect(
            self.polar_min_amp_slider_moved)

        self.ui.label_polarMinAmp.setVisible(False)
        self.ui.spinBox_polarMinAmp.setVisible(False)
        self.ui.horizontalSlider_polarMinAmp.setVisible(False)

        self.ui.actionExport_array_config.triggered.connect(
            self.export_array_config)
        self.ui.actionExport_pattern_data.triggered.connect(
            self.export_pattern)

        self.ui.actionQuit.triggered.connect(QtWidgets.qApp.quit)

        # self.ui.actionReset_config.triggered.connect(self.reset_config)

        self.ui.actionHelp.triggered.connect(self.help)
        self.ui.actionAbout.triggered.connect(self.about)

    def init_figure(self):
        """Init figures"""
        self.canvas2d_cartesian = pg.GraphicsLayoutWidget()
        self.canvas2d_polar = pg.GraphicsLayoutWidget()
        self.canvas3d = gl.GLViewWidget()
        self.canvas3d_array = pg.GraphicsLayoutWidget()

        self.ui.layout_canvas.addWidget(self.canvas3d)
        self.ui.layout_canvas.addWidget(self.canvas3d_array)
        self.ui.layout_canvas.addWidget(self.canvas2d_cartesian)
        self.ui.layout_canvas.addWidget(self.canvas2d_polar)

        self.plot_type_changed(self.ui.cb_plottype.currentIndex())

        """Surface view"""
        self.cmap = cm.get_cmap('jet')
        self.minZ = -100
        self.maxZ = 0

        self.surface_plot = gl.GLSurfacePlotItem(computeNormals=False)
        self.surface_plot.translate(0, 0, 100)

        self.axis = gl.GLAxisItem()
        self.canvas3d.addItem(self.axis)
        self.axis.setSize(x=150, y=150, z=150)

        self.xzgrid = gl.GLGridItem()
        self.yzgrid = gl.GLGridItem()
        self.xygrid = gl.GLGridItem()
        self.canvas3d.addItem(self.xzgrid)
        self.canvas3d.addItem(self.yzgrid)
        self.canvas3d.addItem(self.xygrid)
        self.xzgrid.setSize(x=180, y=100, z=0)
        self.xzgrid.setSpacing(x=10, y=10, z=10)
        self.yzgrid.setSize(x=100, y=180, z=0)
        self.yzgrid.setSpacing(x=10, y=10, z=10)
        self.xygrid.setSize(x=180, y=180, z=0)
        self.xygrid.setSpacing(x=10, y=10, z=10)

        # rotate x and y grids to face the correct direction
        self.xzgrid.rotate(90, 1, 0, 0)
        self.xzgrid.translate(0, -90, 50)
        self.yzgrid.rotate(90, 0, 1, 0)
        self.yzgrid.translate(-90, 0, 50)

        self.canvas3d.addItem(self.surface_plot)
        self.canvas3d.setCameraPosition(distance=300)

        """Array view"""
        self.array_view = pg.PlotItem()
        self.array_plot = pg.ScatterPlotItem()
        self.canvas3d_array.addItem(self.array_view)
        self.array_view.addItem(self.array_plot)

        self.array_view.setAspectLocked()
        self.array_view.setLabel(axis='bottom', text='Horizontal x', units='λ')
        self.array_view.setLabel(
            axis='left', text='Vertical y', units='λ')
        self.array_view.showGrid(x=True, y=True)

        self.array_plot.setPen(pg.mkPen(color=(244, 143, 177, 120), width=1))
        self.array_plot.setBrush(pg.mkBrush(244, 143, 177, 200))

        """Cartesian view"""
        self.cartesianView = pg.PlotItem()
        self.cartesianPlot = pg.PlotDataItem()
        self.cartesianPlotHold = pg.PlotDataItem()

        self.canvas2d_cartesian.addItem(self.cartesianView)

        self.penActive = pg.mkPen(color=(244, 143, 177), width=1)
        self.penHold = pg.mkPen(color=(158, 158, 158), width=1)

        self.cartesianPlot.setPen(self.penActive)
        self.cartesianPlotHold.setPen(self.penHold)
        self.cartesianView.addItem(self.cartesianPlot)

        self.cartesianView.setXRange(-90, 90)
        self.cartesianView.setYRange(-80, 0)
        self.cartesianView.setLabel(axis='bottom', text='Angle', units='°')
        self.cartesianView.setLabel(
            axis='left', text='Normalized amplitude', units='dB')
        self.cartesianView.showGrid(x=True, y=True, alpha=0.5)
        self.cartesianView.setLimits(
            xMin=-90, xMax=90, yMin=-110, yMax=1, minXRange=0.1, minYRange=0.1)

        """Polar view"""
        self.polarView = pg.PlotItem()
        self.polarPlot = pg.PlotDataItem()
        self.polarPlotHold = pg.PlotDataItem()
        self.canvas2d_polar.addItem(self.polarView)

        self.circleList = []
        self.circleLabel = []

        self.polarAmpOffset = 60

        self.polarPlot.setPen(self.penActive)
        self.polarPlotHold.setPen(self.penHold)
        self.polarView.addItem(self.polarPlot)

        self.polarView.setAspectLocked()
        self.polarView.hideAxis('left')
        self.polarView.hideAxis('bottom')

        self.circleLabel.append(pg.TextItem('0 dB'))
        self.polarView.addItem(self.circleLabel[0])
        self.circleLabel[0].setPos(self.polarAmpOffset, 0)
        for circle_idx in range(6):
            self.circleList.append(
                QtGui.QGraphicsEllipseItem(
                    -self.polarAmpOffset + self.polarAmpOffset / 6 *
                    circle_idx,
                    -self.polarAmpOffset + self.polarAmpOffset / 6 *
                    circle_idx,
                    (self.polarAmpOffset - self.polarAmpOffset / 6 *
                     circle_idx) * 2,
                    (self.polarAmpOffset - self.polarAmpOffset / 6 *
                     circle_idx) * 2))
            self.circleList[circle_idx].setStartAngle(2880)
            self.circleList[circle_idx].setSpanAngle(2880)
            self.circleList[circle_idx].setPen(pg.mkPen(0.2))
            self.polarView.addItem(self.circleList[circle_idx])

            self.circleLabel.append(
                pg.TextItem(str(-self.polarAmpOffset / 6 * (circle_idx + 1))))
            self.circleLabel[circle_idx + 1].setPos(
                self.polarAmpOffset - self.polarAmpOffset / 6 * (
                    circle_idx + 1), 0)
            self.polarView.addItem(self.circleLabel[circle_idx + 1])

        self.polarView.addLine(x=0, pen=0.6)
        self.polarView.addLine(y=0, pen=0.6)
        self.polarView.addLine(y=0, pen=0.3).setAngle(45)
        self.polarView.addLine(y=0, pen=0.3).setAngle(-45)
        self.polarView.setMouseEnabled(x=False, y=False)

    def az_changed(self, value):
        self.ui.hs_angleaz.setValue(value * 10)
        self.new_params()

    def el_changed(self, value):
        self.ui.hs_angleel.setValue(value * 10)
        self.new_params()

    def az_hs_moved(self, value):
        self.ui.dsb_angleaz.setValue(value / 10)
        self.new_params()

    def el_hs_moved(self, value):
        self.ui.dsb_angleel.setValue(value / 10)
        self.new_params()

    def fix_az_changed(self, value):
        self.ui.rbhs_azimuth.setValue(value * 10)
        self.new_params()

    def fix_el_changed(self, value):
        self.ui.rbhs_elevation.setValue(value * 10)
        self.new_params()

    def fix_az_hs_moved(self, value):
        self.ui.rbsb_azimuth.setValue(value / 10)
        self.new_params()

    def fix_el_hs_moved(self, value):
        self.ui.rbsb_elevation.setValue(value / 10)
        self.new_params()

    def windowx_combobox_changed(self, value):
        self.windowx_change_config[value]()
        self.new_params()

    def windowy_combobox_changed(self, value):
        self.windowy_change_config[value]()
        self.new_params()

    def rb_azimuth_clicked(self):
        self.fix_azimuth = True
        self.ui.rbhs_azimuth.setEnabled(True)
        self.ui.rbsb_azimuth.setEnabled(True)
        self.ui.rb_elevation.setChecked(False)
        self.ui.rbsb_elevation.setEnabled(False)
        self.ui.rbhs_elevation.setEnabled(False)
        self.nfft_az = 1
        self.nfft_el = 4096
        self.cartesianView.setLabel(axis='bottom', text='Elevation', units='°')
        self.new_params()

    def rb_elevation_clicked(self):
        self.fix_azimuth = False
        self.ui.rbhs_elevation.setEnabled(True)
        self.ui.rbsb_elevation.setEnabled(True)
        self.ui.rb_azimuth.setChecked(False)
        self.ui.rbsb_azimuth.setEnabled(False)
        self.ui.rbhs_azimuth.setEnabled(False)
        self.nfft_az = 4096
        self.nfft_el = 1
        self.cartesianView.setLabel(axis='bottom', text='Azimuth', units='°')
        self.new_params()

    def polar_min_amp_value_changed(self, value):
        self.ui.horizontalSlider_polarMinAmp.setValue(value)
        self.polarAmpOffset = -value
        self.new_params()

    def polar_min_amp_slider_moved(self, value):
        self.ui.spinBox_polarMinAmp.setValue(value)
        self.polarAmpOffset = -value
        self.new_params()

    def new_params(self):
        self.array_config['sizex'] = self.ui.sb_sizex.value()
        self.array_config['sizey'] = self.ui.sb_sizey.value()
        self.array_config['spacingx'] = self.ui.dsb_spacingx.value()
        self.array_config['spacingy'] = self.ui.dsb_spacingy.value()
        self.array_config['beam_az'] = self.ui.dsb_angleaz.value()
        self.array_config['beam_el'] = self.ui.dsb_angleel.value()
        self.array_config['windowx'] = self.ui.cb_windowx.currentIndex()
        self.array_config['windowy'] = self.ui.cb_windowy.currentIndex()
        self.array_config['sllx'] = -self.ui.sb_sidelobex.value()
        self.array_config['slly'] = -self.ui.sb_sidelobey.value()
        self.array_config['nbarx'] = self.ui.sb_adjsidelobex.value()
        self.array_config['nbary'] = self.ui.sb_adjsidelobey.value()
        self.array_config['nfft_az'] = self.nfft_az
        self.array_config['nfft_el'] = self.nfft_el
        self.array_config['plot_az'] = self.ui.rbsb_azimuth.value()
        self.array_config['plot_el'] = self.ui.rbsb_elevation.value()

        self.calpattern.update_config(self.array_config)

    def update_figure(self, azimuth, elevation, pattern, x, y, weight):
        self.exp_config = np.zeros((np.shape(x)[0], 4))
        self.exp_config[:, 0] = x
        self.exp_config[:, 1] = y
        self.exp_config[:, 2] = np.abs(weight)
        self.exp_config[:, 3] = np.angle(weight)/np.pi*180

        el_grid, az_grid = np.meshgrid(elevation, azimuth)
        el_ravel = el_grid.ravel()
        az_ravel = az_grid.ravel()
        self.exp_pattern = np.zeros((np.shape(el_ravel)[0], 3))
        self.exp_pattern[:, 0] = az_ravel
        self.exp_pattern[:, 1] = el_ravel
        self.exp_pattern[:, 2] = pattern.ravel()

        if self.plot_list[self.plot_type_idx] == '3D (Az-El-Amp)':
            rgba_img = self.cmap((pattern-self.minZ)/(self.maxZ - self.minZ))
            self.surface_plot.setData(
                x=azimuth, y=elevation, z=pattern, colors=rgba_img)
        elif self.plot_list[self.plot_type_idx] == '2D Cartesian':
            if self.fix_azimuth:
                self.cartesianPlot.setData(elevation, pattern)
            else:
                self.cartesianPlot.setData(azimuth, pattern)
        elif self.plot_list[self.plot_type_idx] == '2D Polar':
            pattern = pattern + self.polarAmpOffset
            pattern[np.where(pattern < 0)] = 0
            if self.fix_azimuth:
                x = pattern * np.sin(elevation / 180 * np.pi)
                y = pattern * np.cos(elevation / 180 * np.pi)
            else:
                x = pattern * np.sin(azimuth / 180 * np.pi)
                y = pattern * np.cos(azimuth / 180 * np.pi)

            self.circleLabel[0].setPos(self.polarAmpOffset, 0)
            for circle_idx in range(6):
                self.circleList[circle_idx].setRect(
                    -self.polarAmpOffset + self.polarAmpOffset / 6 *
                    circle_idx,
                    -self.polarAmpOffset + self.polarAmpOffset / 6 *
                    circle_idx,
                    (self.polarAmpOffset - self.polarAmpOffset / 6 *
                     circle_idx) * 2,
                    (self.polarAmpOffset - self.polarAmpOffset / 6 *
                     circle_idx) * 2)
                self.circleLabel[circle_idx + 1].setText(
                    str(round(-self.polarAmpOffset / 6 * (circle_idx + 1), 1)))
                self.circleLabel[circle_idx + 1].setPos(
                    self.polarAmpOffset - self.polarAmpOffset / 6 * (
                        circle_idx + 1), 0)
            self.polarPlot.setData(x, y)
        elif self.plot_list[self.plot_type_idx] == 'Array layout':
            self.array_plot.setData(x=x, y=y, size=6)

    def windowx_config(self, window_idx):
        if self.window_list[window_idx] is 'Chebyshev':
            self.ui.sb_sidelobex.setVisible(True)
            self.ui.label_sidelobex.setVisible(True)
            self.ui.hs_sidelobex.setVisible(True)
            self.ui.sb_adjsidelobex.setVisible(False)
            self.ui.label_adjsidelobex.setVisible(False)
            self.ui.hs_adjsidelobex.setVisible(False)
        elif self.window_list[window_idx] is 'Taylor':
            self.ui.sb_sidelobex.setVisible(True)
            self.ui.label_sidelobex.setVisible(True)
            self.ui.hs_sidelobex.setVisible(True)
            self.ui.sb_adjsidelobex.setVisible(True)
            self.ui.label_adjsidelobex.setVisible(True)
            self.ui.hs_adjsidelobex.setVisible(True)
        else:
            self.ui.sb_sidelobex.setVisible(False)
            self.ui.label_sidelobex.setVisible(False)
            self.ui.hs_sidelobex.setVisible(False)
            self.ui.sb_adjsidelobex.setVisible(False)
            self.ui.label_adjsidelobex.setVisible(False)
            self.ui.hs_adjsidelobex.setVisible(False)

    def windowy_config(self, window_idx):
        if self.window_list[window_idx] is 'Chebyshev':
            self.ui.sb_sidelobey.setVisible(True)
            self.ui.label_sidelobey.setVisible(True)
            self.ui.hs_sidelobey.setVisible(True)
            self.ui.sb_adjsidelobey.setVisible(False)
            self.ui.label_adjsidelobey.setVisible(False)
            self.ui.hs_adjsidelobey.setVisible(False)
        elif self.window_list[window_idx] is 'Taylor':
            self.ui.sb_sidelobey.setVisible(True)
            self.ui.label_sidelobey.setVisible(True)
            self.ui.hs_sidelobey.setVisible(True)
            self.ui.sb_adjsidelobey.setVisible(True)
            self.ui.label_adjsidelobey.setVisible(True)
            self.ui.hs_adjsidelobey.setVisible(True)
        else:
            self.ui.sb_sidelobey.setVisible(False)
            self.ui.label_sidelobey.setVisible(False)
            self.ui.hs_sidelobey.setVisible(False)
            self.ui.sb_adjsidelobey.setVisible(False)
            self.ui.label_adjsidelobey.setVisible(False)
            self.ui.hs_adjsidelobey.setVisible(False)

    def plot_type_changed(self, plot_idx):
        self.plot_type_idx = plot_idx
        if self.plot_list[plot_idx] == '3D (Az-El-Amp)':
            self.canvas2d_cartesian.setVisible(False)
            self.canvas2d_polar.setVisible(False)
            self.canvas3d_array.setVisible(False)
            self.canvas3d.setVisible(True)

            self.ui.rb_azimuth.setEnabled(False)
            self.ui.rbsb_azimuth.setEnabled(False)
            self.ui.rbhs_azimuth.setEnabled(False)
            self.ui.rb_elevation.setEnabled(False)
            self.ui.rbsb_elevation.setEnabled(False)
            self.ui.rbhs_elevation.setEnabled(False)

            self.ui.label_polarMinAmp.setVisible(False)
            self.ui.spinBox_polarMinAmp.setVisible(False)
            self.ui.horizontalSlider_polarMinAmp.setVisible(False)
            self.nfft_az = 512
            self.nfft_el = 512
            self.new_params()
        elif self.plot_list[plot_idx] == '2D Cartesian':
            self.canvas2d_polar.setVisible(False)
            self.canvas3d.setVisible(False)
            self.canvas3d_array.setVisible(False)
            self.canvas2d_cartesian.setVisible(True)

            if self.fix_azimuth:
                self.ui.rb_azimuth.setChecked(True)
                self.ui.rb_azimuth.setEnabled(True)
                self.ui.rbsb_azimuth.setEnabled(True)
                self.ui.rbhs_azimuth.setEnabled(True)
                self.ui.rb_elevation.setEnabled(True)
                self.ui.rb_elevation.setChecked(False)
                self.ui.rbsb_elevation.setEnabled(False)
                self.ui.rbhs_elevation.setEnabled(False)
                self.nfft_az = 1
                self.nfft_el = 4096
                self.cartesianView.setLabel(
                    axis='bottom', text='Elevation', units='°')
            else:
                self.ui.rb_azimuth.setChecked(False)
                self.ui.rb_azimuth.setEnabled(True)
                self.ui.rbsb_azimuth.setEnabled(False)
                self.ui.rbhs_azimuth.setEnabled(False)
                self.ui.rb_elevation.setEnabled(True)
                self.ui.rb_elevation.setChecked(True)
                self.ui.rbsb_elevation.setEnabled(True)
                self.ui.rbhs_elevation.setEnabled(True)
                self.nfft_az = 4096
                self.nfft_el = 1
                self.cartesianView.setLabel(
                    axis='bottom', text='Azimuth', units='°')

            self.ui.label_polarMinAmp.setVisible(False)
            self.ui.spinBox_polarMinAmp.setVisible(False)
            self.ui.horizontalSlider_polarMinAmp.setVisible(False)
            self.new_params()
        elif self.plot_list[plot_idx] == '2D Polar':
            self.canvas2d_cartesian.setVisible(False)
            self.canvas3d.setVisible(False)
            self.canvas3d_array.setVisible(False)
            self.canvas2d_polar.setVisible(True)

            if self.fix_azimuth:
                self.ui.rb_azimuth.setChecked(True)
                self.ui.rb_azimuth.setEnabled(True)
                self.ui.rbsb_azimuth.setEnabled(True)
                self.ui.rbhs_azimuth.setEnabled(True)
                self.ui.rb_elevation.setEnabled(True)
                self.ui.rb_elevation.setChecked(False)
                self.ui.rbsb_elevation.setEnabled(False)
                self.ui.rbhs_elevation.setEnabled(False)
                self.nfft_az = 1
                self.nfft_el = 4096
            else:
                self.ui.rb_azimuth.setChecked(False)
                self.ui.rb_azimuth.setEnabled(True)
                self.ui.rbsb_azimuth.setEnabled(False)
                self.ui.rbhs_azimuth.setEnabled(False)
                self.ui.rb_elevation.setEnabled(True)
                self.ui.rb_elevation.setChecked(True)
                self.ui.rbsb_elevation.setEnabled(True)
                self.ui.rbhs_elevation.setEnabled(True)
                self.nfft_az = 4096
                self.nfft_el = 1

            self.ui.label_polarMinAmp.setVisible(True)
            self.ui.spinBox_polarMinAmp.setVisible(True)
            self.ui.horizontalSlider_polarMinAmp.setVisible(True)
            self.new_params()
        elif self.plot_list[plot_idx] == 'Array layout':
            self.canvas2d_cartesian.setVisible(False)
            self.canvas2d_polar.setVisible(False)
            self.canvas3d.setVisible(False)
            self.canvas3d_array.setVisible(True)

            self.ui.rb_azimuth.setEnabled(False)
            self.ui.rbsb_azimuth.setEnabled(False)
            self.ui.rbhs_azimuth.setEnabled(False)
            self.ui.rb_elevation.setEnabled(False)
            self.ui.rbsb_elevation.setEnabled(False)
            self.ui.rbhs_elevation.setEnabled(False)

            self.ui.label_polarMinAmp.setVisible(False)
            self.ui.spinBox_polarMinAmp.setVisible(False)
            self.ui.horizontalSlider_polarMinAmp.setVisible(False)
        self.new_params()

    def export_array_config(self):
        fileName = QtGui.QFileDialog.getSaveFileName(
            self, 'Export array config ...', 'array_config.csv',
            'All Files (*);;CSV files (*.csv)')
        if fileName[0] or fileName[1]:
            np.savetxt(fileName, self.exp_config, fmt='%1.8e', delimiter=',',
                       header='x (wavelength), y (wavelength), \
                    amplitude (linear), phase (degree)')

    def export_pattern(self):
        fileName = QtGui.QFileDialog.getSaveFileName(
            self, 'Export pattern ...', 'pattern.csv',
            'All Files (*);;CSV files (*.csv)')
        if fileName[0] or fileName[1]:
            np.savetxt(fileName, self.exp_pattern, fmt='%1.8e', delimiter=',',
                       header='azimuth (degree), elevation (degree), \
                           pattern (dB)')

    def help(self):
        webbrowser.open(
            'https://github.com/rookiepeng/antenna-array-analysis/issues')

    def about(self):
        msg = QtWidgets.QMessageBox()

        msg.setText('<h1>Antenna Array Analysis</h1>')
        msg.setTextFormat(QtCore.Qt.RichText)
        msg.setInformativeText(
            '<p>A simple GUI tool for antenna array analysis.</p><p>&nbsp;</p>\
                <p><strong>Dr. Zhengyu Peng</strong></p><p><a \
                    href=''https://zpeng.me'' target=''_blank'' \
                        class=''url''>https://zpeng.me</a></p>')
        msg.setWindowTitle("About")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)

        retval = msg.exec_()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = AntArrayAnalysis()
    window.show()
    sys.exit(app.exec_())
