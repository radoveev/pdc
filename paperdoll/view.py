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


class VSliders(VWidget):
    '''The sliders controlling animation settings.'''
    def __init__(self):
        VWidget.__init__(self)
        self.sliders = {}
        # create layout
        layout = QtWidgets.QFormLayout()
        self.setLayout(layout)
        # connect simple signals
        sisi.connect(self.on__initialize_animations,
                     signal="initialize animations")
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
        # connect Qt signals
        slider.valueChanged.connect(self.on_slider_valueChanged)
        # add to layout
        self.sliders[slidername] = slider
        self.layout().addRow(aniname, self.sliders[slidername])
        return slider

    @QtCore.pyqtSlot(int)
    def on_slider_valueChanged(self, sliderval):
        slidername = self.sender().objectName()
        aniname = slidername[:-7]
        data = {"field": aniname, "value": sliderval}
        sisi.send(signal="set state", channel="editor", sender=self, data=data)

    def on__set_state(self, sender, data):
        if sender is not self:
            aniname = data["field"]
            value = data["value"]
            slider = self.sliders[aniname + "_slider"]
            slider.setValue(value)

    def on__initialize_animations(self, data):
        # create animation controls
        animation_names = [(a.name, a) for a in data]
        for aniname, ani in sorted(animation_names):
            self.add_slider(aniname, ani.default_state)


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
    def __init__(self):
        VBaseWindow.__init__(self)
        self.svgdoc = None  # the SVG document of the currently displayed doll
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
        # connect Qt signals
        self.exportsvg.triggered.connect(self.on_exportsvg_triggered)
        self.objectlist.clicked.connect(self.on_objectlist_clicked)
        # create layout
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.doll, stretch=5)
        hbox.addWidget(self.sliders)
        hbox.addWidget(self.objectlist)
        self.central.setLayout(hbox)
        self.setCentralWidget(self.central)
        # connect simple signals
        sisi.connect(self.on__state_changed, signal="state changed",
                     channel="editor")
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

    def on__state_changed(self):
        sisi.send(signal="draw doll")

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


# --------------------------------------------------------------------------- #
# Declare module globals
# --------------------------------------------------------------------------- #
log = logging.getLogger(__name__)
version = None  # the application version; set in __main__.py
app = None  # the QApplication instance of this application; set in __main__.py
gui = None  # the main window of this application; set in __main__.py
