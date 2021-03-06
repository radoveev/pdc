# -*- coding: utf-8 -*-
'''Paperdoll editor GUI module.
'''


# --------------------------------------------------------------------------- #
# Import libraries
# --------------------------------------------------------------------------- #
import logging

import xml.etree.ElementTree as ET
from PyQt5 import QtWidgets, QtGui, QtCore, QtSvg, QtWebEngineWidgets
from PyQt5.QtCore import Qt

import svglib
import simplesignals as sisi


# --------------------------------------------------------------------------- #
# Define classes
# --------------------------------------------------------------------------- #
class DrawSchedule(QtCore.QObject):
    '''Initiates a redraw when no state change has happened for some time.
    '''
    def __init__(self, delay=10, parent=None):
        QtCore.QObject.__init__(self, parent=parent)
        # the time in milliseconds we wait for state changes
        # before we start a redraw
        self.delay = delay
        # the number of changes that occurred
        self.changecount = 0
        # connect simple signals
        sisi.connect(self.on__state_changed, signal="state changed",
                     channel="editor")

    @QtCore.pyqtSlot()
    def attempt_redraw(self):
        '''Start a redraw if changeid is the id of the last state change.'''
        # the delay for the first change is up, so we update the changecount
        self.changecount -= 1
        # has the time delay for all changes passed?
        if self.changecount is 0:
            sisi.send(signal="draw doll")

    def on__state_changed(self):
        # remember that a change occurred
        self.changecount += 1
        # each time the state is changed we start waiting again
        QtCore.QTimer.singleShot(self.delay, self.attempt_redraw)
#        timer = QtCore.QTimer(self)
#        timer.timeout.connect(self.attempt_redraw)
#        timer.setSingleShot(True)
#        timer.start(self.delay)
#        t = threading.Timer(self.delay, self.attempt_redraw, [self.changeid])
#        t.start()


class VBase(object):
    '''Base class for views, which are classes displaying data in a widget.
    '''
    def __init__(self):
        pass


class VWidget(VBase, QtWidgets.QWidget):
    '''Base class for views acting like a QWidget.
    '''
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        VBase.__init__(self)


class VPaperDoll(VWidget):
    '''Displays a paperdoll composed of layered SVG paths.
    '''
    def __init__(self):
        VWidget.__init__(self)
        self.webview = QScrollingWebView()
#        self.lastpos = None
        # create layout
        self.setMinimumWidth(50)
        self.setMinimumHeight(50)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.webview)
        self.setLayout(vbox)


class VDial(VWidget):
    '''Controls one or more animation states.

     #TODO feature proposal: dial
     A dial is a layer of abstraction between animation states and the GUI.
     Each dial has a specified range of integer values, usually from 1 to 100
     and is controlled by the user via a slider. When the dial values changes
     by one the states of the animations effected by that dial are modified.
     The change in dial values does not have to translate 1:1 to the change
     in animation state.
     <dial name="boobs" start="1" end="100">
         <animation name="" min="1" init="30" max="100"/>
     </dial>
     '''
    def __init__(self, model):
        VWidget.__init__(self)
        self.model = model
        self.label = QtWidgets.QLabel(self.model.name)
        self.slider = QtWidgets.QSlider(Qt.Horizontal)
        self.lineedit = QtWidgets.QLineEdit()
        # configure widgets
        self.slider.setMinimum(self.model.minimum)
        self.slider.setMaximum(self.model.maximum)
        intval = QtGui.QIntValidator(self.model.minimum, self.model.maximum)
        self.lineedit.setValidator(intval)
#        self.slider.setTracking(False)
        # create layout
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.label)
        hbox.addWidget(self.slider)
        hbox.addWidget(self.lineedit)
        self.setLayout(hbox)
        # connect Qt signals
        self.slider.valueChanged.connect(self.on_slider_valueChanged)
        self.lineedit.editingFinished.connect(self.on_lineedit_editingFinished)
        # connect simple signals
        sisi.connect(self.on__update_dial_state, signal="update dial state",
                     sender=self.model)
#
#    @property
#    def minimum(self):
#        return self.slider.minimum()
#
#    @property
#    def maximum(self):
#        return self.slider.maximum()

    @QtCore.pyqtSlot(int)
    def on_slider_valueChanged(self, newval):
        newval = self.model.change_value(newval)
        self.on__update_dial_state(self, newval)  # update the dial GUI

    @QtCore.pyqtSlot()
    def on_lineedit_editingFinished(self):
        newval = int(self.lineedit.text())
        newval = self.model.change_value(newval)
        self.on__update_dial_state(self, newval)  # update the dial GUI

    def on__update_dial_state(self, sender, data):
        self.slider.valueChanged.disconnect(self.on_slider_valueChanged)
        self.slider.setValue(data)
        self.slider.valueChanged.connect(self.on_slider_valueChanged)
        self.lineedit.setText(str(data))


class VSliders(VWidget):
    '''The sliders controlling animation settings.'''
    def __init__(self):
        VWidget.__init__(self)
        self.sliders = {}
        self.lastval = {}
        # create layout
        layout = QtWidgets.QFormLayout()
        self.setLayout(layout)
        # connect simple signals
        sisi.connect(self.on__set_state, signal="set state", channel="editor")

    def add_slider(self, aniname, value=50):
        slider = QtWidgets.QSlider(Qt.Horizontal)
        slidername = aniname + "_slider"
        # configure widgets
        slider.setObjectName(slidername)
#        self.slider.setTracking(False)
        slider.setMinimum(0)
        slider.setMaximum(100)
        slider.setValue(value)
        self.lastval[slidername] = value
        # connect Qt signals
        slider.valueChanged.connect(self.on_slider_valueChanged)
        # add to layout
        self.sliders[slidername] = slider
        self.layout().addRow(aniname, self.sliders[slidername])
        return slider

    @QtCore.pyqtSlot(int)
    def on_slider_valueChanged(self, sliderval):
        slidername = self.sender().objectName()
        slider = self.sliders[slidername]
        slider.setValue(self.lastval[slidername])

    def on__set_state(self, sender, data):
        if sender is not self:
            aniname = data["field"]
            value = data["value"]
            slidername = aniname + "_slider"
            slider = self.sliders[slidername]
            self.lastval[slidername] = value
            slider.setValue(value)


# define window classes
class VBaseWindow(VBase, QtWidgets.QMainWindow):
    '''Base class for top-level windows, views based on QMainWindow.
    '''
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        VBase.__init__(self)
        # create widgets
        self.toolbar = QtWidgets.QToolBar()
        # create actions
        self.quit = self.toolbar.addAction("quit")
        # connect Qt signals
        self.quit.triggered.connect(self.on_quit_triggered)
        # create layout
        self.toolbar.addSeparator()
#        self.toolbar.setOrientation(QtNS.Vertical)
        self.addToolBar(Qt.RightToolBarArea, self.toolbar)

    def resizeToScreen(self, width=0.8, height=0.8):
        '''Resizes the window to a fraction of the screen size.'''
        # get the size of the primary screen and resize main window
        desktop = QtWidgets.QDesktopWidget()
        freespace = desktop.availableGeometry(desktop.primaryScreen())
        freewidth, freeheigth = (freespace.width(), freespace.height())
        self.resize(int(freewidth * width), int(freeheigth * height))

    def centerOnScreen(self):
        '''Centers the window on the screen.'''
        desktop = QtWidgets.QDesktopWidget()
        screen = desktop.screenGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def hideToolbar(self):
        action = self.toolbar.toggleViewAction()
        action.setChecked(True)
        action.trigger()

    def showToolbar(self, toolbar):
        action = self.toolbar.toggleViewAction()
        action.setChecked(False)
        action.trigger()

    @QtCore.pyqtSlot()
    def on_quit_triggered(self):
        log.info("Closing all windows")
        app.closeAllWindows()


class VEditorWindow(VBaseWindow):
    '''The main window of the paperdoll editor application.
    '''
    def __init__(self, model):
        VBaseWindow.__init__(self)
        self.model = model
        self.svgdoc = None  # the SVG document of the currently displayed doll
        self.dials = []
        # create widgets
        self.central = QtWidgets.QWidget()
        self.doll = VPaperDoll()
        self.sliders = VSliders()
        self.objectlist = QtWidgets.QTreeView()
        # create actions
        self.exportsvg = self.toolbar.addAction("export")
        # configure widgets
        self.setWindowTitle("Paperdoll editor {}".format(version))
        self.objectlist.setHeaderHidden(True)
        self.objectlist.setIndentation(20)
        # create animation controls
        diallist = [(d.name, d) for d in self.model.dials.values()]
        for dialname, dialmodel in sorted(diallist):
            self.dials.append(VDial(dialmodel))
        animation_names = [(a.name, a) for a in self.model.animations.values()]
        for aniname, ani in sorted(animation_names):
            self.sliders.add_slider(aniname, ani.default_state)
        # connect Qt signals
        self.exportsvg.triggered.connect(self.on_exportsvg_triggered)
        self.objectlist.clicked.connect(self.on_objectlist_clicked)
        # create layout
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.doll, stretch=5)
        hbox.addWidget(self.objectlist)
        dialbox = QtWidgets.QVBoxLayout()
        for dialview in self.dials:
            dialbox.addWidget(dialview)
        dialbox.addStretch()
        hbox.addLayout(dialbox)
        hbox.addWidget(self.sliders)
        self.central.setLayout(hbox)
        self.setCentralWidget(self.central)
        # connect simple signals
        sisi.connect(self.on__doll_drawn, signal="doll drawn")

    def render_doll(self):
        # create an element tree from the svg document
        xmlsvgelem = self.svgdoc.to_xml()
        # create bytes from xml object
        xml = ET.tostring(xmlsvgelem)
        # update paperdoll webview
        self.doll.webview.setContent(xml, "image/svg+xml")

    @QtCore.pyqtSlot()
    def on_exportsvg_triggered(self):
        # ask user where we should save the svg file
        path, filetypefilter = QtWidgets.QFileDialog.getSaveFileName(self,
            "Export paperdoll SVG file", "./paperdoll.svg",
            "SVG Files (*.svg)")
        if path:
            # ask model to save the doll to disk
            sisi.send(signal="export doll", data={"path": path})

    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def on_objectlist_clicked(self, idx):
        model = self.objectlist.model()
        item = model.itemFromIndex(idx)
#        elemid = model.elemidmap[item.index()]
        elemid = item.text()
        elem = self.svgdoc.idmap[elemid]
        if elem.style is None:
            elem.style = svglib.Style("display:inline")
        # toggle visibility
        if elem.style.visible is True:
            elem.style.visible = False
        else:
            elem.style.visible = True
        data = {"elemid": elem.elemid, "style": elem.style}
        sisi.send(signal="set style", data=data)
        # set visibility of subelements
        #TODO replace this hack by implementing style propagation
        if isinstance(elem, svglib.SvgGroup):
            for subelem in elem.iterate():
                if subelem.style is not None:
                    subelem.style.visible = elem.style.visible
                    data = {"elemid": subelem.elemid, "style": subelem.style}
                    sisi.send(signal="set style", data=data)
        sisi.send(signal="draw doll")
        #TODO fix making lines invisible (their style does not have "display")

    def on__doll_drawn(self, data):
        # update current model
        self.svgdoc = data
        # update object list
        model = self.objectlist.model()
        if model is None:
            model = QSvgDocumentModel(self.svgdoc)
            self.objectlist.setModel(model)
        else:
            model.update(self.svgdoc)
        self.render_doll()


# define application class
class Application(QtWidgets.QApplication):
    '''This class will have only one instance.'''
    def __init__(self, *args, **kwargs):
        QtWidgets.QApplication.__init__(self, *args, **kwargs)
        # connect Qt signals
        self.aboutToQuit.connect(self.on_aboutToQuit)

    @QtCore.pyqtSlot()
    def on_aboutToQuit(self):
        log.info("Quitting now")


# define new widgets
class QFixedSvgWidget(QtSvg.QSvgWidget):
    '''A QSvgWidget that preserves aspect ratio.
    '''
    def __init__(self, *args, **kwargs):
        QtSvg.QSvgWidget.__init__(self, *args, **kwargs)

    def paintEvent(self, paint_event):
        svgsize = self.renderer().defaultSize()
        svgsize.scale(self.size(), Qt.KeepAspectRatio)
        rect = QtCore.QRectF(0, 0, svgsize.width(), svgsize.height())
        self.renderer().render(QtGui.QPainter(self), rect)


class QSvgDocumentModel(QtGui.QStandardItemModel):
    '''A model for a Qt tree view based on a SvgDocument.
    '''
    def __init__(self, svgdoc, *args, **kwargs):
        QtGui.QStandardItemModel.__init__(self, *args, **kwargs)
#        self.setColumnCount(2)
        self.itemmap = {}  # maps element ids to Qt items
        self.modified_style = {}

#    @property
#    def elemidmap(self):
#        return {v: k for k, v in self.itemmap.items()}

    def update(self, svgdoc):
        root = self.invisibleRootItem()
        self.updateTree(svgdoc, root)

    def updateTree(self, elem, parentItem):
        for child in elem:
            if child.elemid in self.itemmap:
                item = self.itemmap[child.elemid]
                #TODO implement updating the model
            else:
                item = QtGui.QStandardItem(child.elemid)
                assert child.elemid not in self.itemmap
                self.itemmap[child.elemid] = item
                parentItem.appendRow(item)
#                idx = item.index()
#                parent = self.itemFromIndex(idx.parent())
#                print("add item", child.elemid, "at", idx.row(), idx.column(), parent==parentItem)
#                # add visibility item
#                visitem = QtGui.QStandardItem("v")
#                self.setItem(item.index().row(), 1, visitem)
            if isinstance(child, svglib.SvgGroup):
                self.updateTree(child, item)

#    def toggleVisibility(self, item):
#        elemid = item.text()
#        elem = self.svgdoc.idmap[elemid]
##        opacity = elem.style.get("opacity", "1")
##        print("style before", str(elem.style))
##        for key in ("opacity", "fill-opacity", "stroke-opacity"):
##            if key in elem.style:
##                if elem.style[key] == "0":
##                    elstyle[key] = "1"
##                elif elem.style[key] == "1":
##                    elstyle[key] = "0"
#        if elem.style is not None:
#            if elem.style.visible is not None:
#                if elem.style.visible is True:
#                    elem.style.visible = False
#                else:
#                    elem.style.visible = True
#        # if elem has subelements, change their visibility too
#        if isinstance(elem, svglib.SvgGroup):
#            if elem.style is None:
#                groupvis = False
#                elem.style = svglib.Style("display:none")
#            else:
#                groupvis = elem.style.visible
#            for subelem in elem.iterate():
#                if subelem.style is not None:
#                    subelem.style.visible = groupvis
##        print("style after", str(elem.style), type(elem.style))
#        self.modified_style[elem.elemid] = elem.style
#        #TODO modify the model via signals, do not store state here


class QScrollingWebView(QtWebEngineWidgets.QWebEngineView):
    def __init__(self, *args, **kwargs):
        QtWebEngineWidgets.QWebEngineView.__init__(self, *args, **kwargs)

    def wheelEvent(self, event):
        angledelta = event.angleDelta().y()
        pos = event.pos()
        evx, evy = pos.x(), pos.y()
#        if angledelta > 0:
#            scrollstep = 10
#        else:
#            scrollstep = -10
        page = self.page()
        if event.modifiers() == Qt.ControlModifier:
            zoom = self.zoomFactor()
            if angledelta > 0:
                zoom = min(zoom + 0.125, 5.0)
            else:
                zoom = max(zoom - 0.125, 0.25)
            self.setZoomFactor(zoom)
            page.runJavaScript("window.scrollTo(%s, %s);" % (evx, evy))
#        elif event.modifiers() == Qt.ShiftModifier:
#            page.runJavaScript("window.scrollBy(%s, 0);" % scrollstep)
#        else:
#            page.runJavaScript("window.scrollBy(0, %s);" % scrollstep)
        event.accept()


# --------------------------------------------------------------------------- #
# Declare module globals
# --------------------------------------------------------------------------- #
log = logging.getLogger(__name__)
draw_schedule = DrawSchedule()
version = None  # the application version; set in __init__.py
app = None  # the QApplication instance of this application; set in __init__.py
gui = None  # the main window of this application; set in __init__.py
