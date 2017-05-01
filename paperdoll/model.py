# -*- coding: utf-8 -*-
'''Paperdoll editor application state module.
'''

# --------------------------------------------------------------------------- #
# Import libraries
# --------------------------------------------------------------------------- #
import logging
import copy
import xml.etree.ElementTree as ET
from pathlib import Path
import pdb
trace = pdb.set_trace

import svglib
from svglib import round_decimal
import simplesignals as sisi


# --------------------------------------------------------------------------- #
# Define classes
# --------------------------------------------------------------------------- #
class MBase(object):
    '''Base class for models, which handle state and data structures.
    '''
    def __init__(self):
        pass


class MPaperdollEditor(MBase):
    '''Represents the state of the paperdoll editor application.
    '''
    def __init__(self):
        MBase.__init__(self)
        self.descfile = svglib.DescriptionFile("../paperdoll/linedoll.xml")
        self.state = {}
        self.layers = []
        self.dollgeometry = {}  # the geometry that was drawn last
        self.modified_styles = {}
        # parse paperdoll description file
        self.descfile.load_connectivity()
        self.descfile.load_geometry()
        self.descfile.load_animations()
        # load layers
        log.info("Load layers")
        xmllayers = self.descfile.tree.find("layers")
        for xmlelem in xmllayers:
            name = xmlelem.get("name", None)
            layercontent = []
            for layerchild in xmlelem:
                if layerchild.tag == "conform":
                    geom = layerchild.get("geometry", None)
                    basegeom = layerchild.get("base_geometry", None)
                    layercontent.append({"geometry": geom,
                                         "base_geometry": basegeom})
#                elif layerchild.tag == "animation":
#                    animname = layerchild.get("name", None)
#                    layercontent.append({"animation": animname})
                elif layerchild.tag == "geometry":
                    geom = layerchild.get("id", None)
                    layercontent.append({"geometry": geom})
                else:
                    data = layerchild.attrib.copy()
                    data["tag"] = layerchild.tag
                    layercontent.append(data)
            self.layers.append({"name": name,
                                "content": layercontent})
        # initialize animation state
        for animname in self.animations:
            self.state[animname] = 40
        # connect simple signals
        sisi.connect(self.on__set_state, signal="set state")
        sisi.connect(self.on__draw_doll, signal="draw doll")
        sisi.connect(self.on__export_doll, signal="export doll")
        sisi.connect(self.on__set_style, signal="set style")

    @property
    def animations(self):
        return self.descfile.animations

    @property
    def frames(self):
        '''Returns the animation frames corresponding to the current state.'''
        frames = []
        for animname, animstate in self.state.items():
            anim = self.animations[animname]
            if isinstance(anim, svglib.CombinedAnimation):
                frame = anim.get_frame(animstate, self.state.copy())
            else:
                frame = anim.get_frame(animstate)
            frames.append(frame)
        return frames

    @property
    def connectivity(self):
        return self.descfile.connectivity

    def load_geometry(self, geomid):
        geomelem = self.descfile.geometry.get(geomid, None)
        if geomelem is None:
            geomelem = self.dollgeometry[geomid]
        delta = getattr(geomelem, "delta", None)
        if delta is not None:
            targetid = delta.trgtelem.connectivity
            targetelem = self.load_geometry(targetid)
            geomelem = delta.conform(geomid, targetelem)
        return geomelem

    def print_geometry(self):
        print()
        for label, elem in self.descfile.geometry.items():
            if isinstance(elem, svglib.SvgPath):
                print(elem.prettystring(), "\n")
            else:
                for path in elem:
                    if path.elemid.endswith("_l"):
                        print(path.prettystring(), "\n")
        print()

    def trace_outline(self, geomelem, elemid, start=0, end=-1):
        '''Creates a line along geomelem.

        elemid is the element id of the newly created line
        start is the command index where the line should start
        end is the command index where the line should end.
        '''
        return svglib.SvgPath.from_path(geomelem, elemid, start, end)

    #TODO when modifying the group structure of elements, transforms
    #TODO and styles from removed parent groups should be applied to children
    def draw(self, width=400, height=700, viewbox="-200 0 400 700"):
        '''Returns a SVG drawing in a string.'''
        self.dollgeometry = {}
        # calculate the geometry elements that should be drawn from the
        # current animation frames
        animationelems = {}
        for layer in self.layers:
#            log.info("Collapse layer %s", layer["name"])
            for content in layer["content"]:
                contenttag = content.get("tag", None)
                if contenttag == "animation":
                    anim = self.animations[content["name"]]
                    animstate = self.state[anim.name]
                    if isinstance(anim, svglib.CombinedAnimation):
                        frame = anim.get_frame(animstate, self.state.copy())
                    else:
                        frame = anim.get_frame(animstate)
                    # add geometry elements that should be drawn to the doll
                    for elem in frame.iterate():
                        elid = elem.elemid
                        assert elid not in self.dollgeometry, elid
                        self.dollgeometry[elid] = elem
                        try:
                            animationelems[anim.name].append(elem)
                        except KeyError:
                            animationelems[anim.name] = [elem]
        # add outlines
        for layer in self.layers:
#            log.info("Retrace layer %s", layer["name"])
            for content in layer["content"]:
                contenttag = content.get("tag", None)
                if contenttag == "trace_outline":
                    base_geometry_id = content["base_geometry"]
                    base_geometry = self.load_geometry(base_geometry_id)
                    elemid = content["id"]
                    start = int(content["start"])
                    end = int(content["end"])
#                    print("trace", base_geometry, "for", elemid)
                    elem = self.trace_outline(base_geometry, elemid,
                                              start, end)
                    assert elemid not in self.dollgeometry
                    self.dollgeometry[elemid] = elem
        # add geometry elements in layers to svg document in draw order
        svgelem = svglib.SvgDocument()
        svgelem.elemid = "paperdoll1"
        svgelem.width = width
        svgelem.height = height
        svgelem.viewbox = viewbox
        for layer in self.layers:
            # create layer element
            layerelem = svglib.SvgGroup()
            layerelem.elemid = "layer_" + layer["name"].lower()
            layerelem.xmlattrib = {"inkscape:label": layer["name"],
                                   "inkscape:groupmode": "layer"}
            svgelem.append(layerelem)
            # add geometry elements
            for content in layer["content"]:
                contenttag = content.get("tag", None)
                if contenttag == "animation":
                    elemlist = animationelems[content["name"]]
                    for unified_elem in elemlist:
                        layerelem.append(unified_elem)
                elif contenttag == "trace_outline":
                    unified_elem = self.dollgeometry[content["id"]]
                    layerelem.append(unified_elem)
                else:
                    group = self.load_geometry(content["geometry"])
                    # create a copy of the group and remove all children
                    groupelem = group.copy()
                    groupelem.children = []
                    layerelem.append(groupelem)
                    # add all geometry elements to the new group
                    for elem in group.iterate():
                        if isinstance(elem, svglib.SvgGeometryElement):
                            # reload elements so conforming paths can adjust
                            delta = getattr(elem, "delta", None)
                            if delta is not None:
                                elem = self.load_geometry(elem.elemid)
                            # add element to new group
                            groupelem.append(elem)
        # add defs to svg document
        xmldefselem = ET.Element("defs", {"id": "defs_paperdoll1"})
        datafile = self.descfile.svgfile
        datasvgelem = datafile.tree.getroot()
        datadefselem = datasvgelem.find(datafile.svgns("defs"))
        for filterelem in datadefselem.findall(datafile.svgns("filter")):
            xmldefselem.append(copy.deepcopy(filterelem))
        for radialelem in datadefselem.findall(
                datafile.svgns("radialGradient")):
            xmldefselem.append(copy.deepcopy(radialelem))
        for linearelem in datadefselem.findall(
                datafile.svgns("linearGradient")):
            xmldefselem.append(copy.deepcopy(linearelem))
        svgelem.defs = xmldefselem
        # adjust style of elements
        for layerelem in svgelem:
            layername = layerelem.xmlattrib["inkscape:label"]
            for elem in layerelem.iterate():
                if elem.elemid.startswith("line_"):
                    elem.style = linestyle.copy()
                elif elem.elemid.startswith("shadow_"):
                    elem.style = shadowstyle.copy()
                elif elem.elemid.startswith("outline_"):
                    elem.style = outlinestyle.copy()
                elif elem.elemid in {"eye_lower_l", "eye_upper_l", "eye_lid_l",
                                        "eye_lower_r", "eye_upper_r", "eye_lid_r"}:
                    elem.style = bodystyle.copy()
                elif layername in {"face", "arms", "legs", "boobs", "torso"}:
                    elem.style = bodystyle.copy()
    #            if layername in {"boobs", "torso"}:
    #                elem.style = torsostyle.copy()
#                # make invisible elements visible
#                if (elem.style is not None and
#                    elem.elemid not in self.modified_styles):
#                    if elem.style.visible is not None:
#                        elem.style.visible = True
                # adjust style as specified by the user
                #TODO replace this hack by implementing style propagation
                if elem.elemid in self.modified_styles:
                    elem.style = self.modified_styles[elem.elemid]
            if layerelem.elemid in self.modified_styles:
                layerelem.style = self.modified_styles[layerelem.elemid]
        # round coordinates of all geometry elements
        for elem in [el for el in svgelem.iterate()
                     if isinstance(el, svglib.SvgGeometryElement)]:
            for cmd in elem.commands:
                for point in cmd.parameters:
                    point.x = round_decimal(point.x, 3)
                    point.y = round_decimal(point.y, 3)
        # add labels to nodes
#            # determine how many commands need labels
#            cmdcount = len(elem.commands)
#            if isinstance(elem, SvgPath):
#                closed = elem.is_closed()
#                circular = elem.is_circular()
#                if closed and circular:
#                    # if the second last point actually closes the path and the
#                    # path has a Z command nevertheless, the last two commands
#                    # do not get a label
#                    cmdcount -= 2
#                elif closed or circular:
#                    # the close path command does not get a label
#                    # the last point of a circular path is identical to its first
#                    # point; therefore, the last command does not get a label
#                    cmdcount -= 1
#            if (isinstance(geomobj, svglib.SvgPath) and
#                geomobj.elemid in {"line_boob_l"}):
#                for cmd in geomobj.commands:
#                    if cmd.nodeid is not None:
#                        pos = cmd.endpoint()
#                        xmltext = ET.Element("text")
#                        xmltext.set("x", str(pos.x + 2))
#                        xmltext.set("y", str(pos.y))
#                        xmltext.text = cmd.nodeid
#                        xmllayerelem.append(xmltext)
        # create element tree from svg document


#        # add geometry elements to list in draw order
#        completelayers = []
#        for layer in self.layers:
#            # add geometry elements that are not part of animations
#            for content in layer["content"]:
#                contenttag = content.get("tag", None)
#                if "animation" in content:
#                    elemlist = animationelems[content["animation"]]
#                    for unified_elem in elemlist:
#                        layerdata = {"name": layer["name"],
#                                     "geometry": unified_elem}
#                        completelayers.append(layerdata)
#                elif contenttag == "trace_outline":
#                    unified_elem = self.dollgeometry[content["id"]]
#                    layerdata = {"name": layer["name"],
#                                 "geometry": unified_elem}
#                    completelayers.append(layerdata)
#                else:
#                    group = self.load_geometry(content["geometry"])
#                    for elem in group.iterate():
#                        # reload elem so conforming paths can adjust
#                        delta = getattr(elem, "delta", None)
#                        if delta is not None:
#                            elem = self.load_geometry(elem.elemid)
#                        layerdata = {"name": layer["name"],
#                                     "geometry": elem}
#                        completelayers.append(layerdata)
#            # add animated geometry elements
#            completelayers.extend(layermap.get(layer["name"], []))

#        # prepare svg element
#        datafile = self.descfile.svgfile
#        datasvgelem = datafile.tree.getroot()
#        xmlsvgelem = ET.Element("svg")
#        xmlsvgelem.set("id", "paperdoll1")
#        xmlsvgelem.set("width", str(width))
#        xmlsvgelem.set("height", str(height))
#        xmlsvgelem.set("viewBox", viewbox)
#        # define name spaces
#        for prefix, uri in datafile.svgnamespaces.items():
#            if prefix == "svg":
#                ET.register_namespace("", uri)
#            else:
#                ET.register_namespace(prefix, uri)
#        xmlsvgelem.set("xmlns:svg", "http://www.w3.org/2000/svg")
##        print("attribs")
##        for key, val in datasvgelem.attrib.items():
##            print(key, val)
#        # add defs
#        xmldefselem = ET.Element("defs", {"id": "defs_paperdoll1"})
#        datadefselem = datasvgelem.find(datafile.svgns("defs"))
#        for filterelem in datadefselem.findall(datafile.svgns("filter")):
#            xmldefselem.append(copy.deepcopy(filterelem))
#        for radialelem in datadefselem.findall(
#                datafile.svgns("radialGradient")):
#            xmldefselem.append(copy.deepcopy(radialelem))
#        for linearelem in datadefselem.findall(
#                datafile.svgns("linearGradient")):
#            xmldefselem.append(copy.deepcopy(linearelem))
#        xmlsvgelem.append(xmldefselem)
#        # prepare layers
#        layerelems = {}
#        layerorder = []
#        for layer in completelayers:
#            layername = layer["name"]
#            # fetch layer element
#            xmllayerelem = layerelems.get(layername, None)
#            if xmllayerelem is None:
#                # create layer element
#                xmlattrib = {"inkscape:label": layername,
#                             "inkscape:groupmode": "layer",
#                             "id": "layer_%s" % layername.lower()}
#                xmllayerelem = ET.Element("g", attrib=xmlattrib)
#                layerelems[layername] = xmllayerelem
#                layerorder.append(layername)
#            # adjust style of geometry element
#            geomobj = layer["geometry"]
#            if geomobj.elemid.startswith("line_"):
#                geomobj.style = linestyle
#            elif geomobj.elemid.startswith("shadow_"):
#                geomobj.style = shadowstyle
#            elif geomobj.elemid.startswith("outline_"):
#                geomobj.style = outlinestyle
#            elif geomobj.elemid in {"eye_lower_l", "eye_upper_l", "eye_lid_l",
#                                    "eye_lower_r", "eye_upper_r", "eye_lid_r"}:
#                geomobj.style = bodystyle
#            elif layername in {"face", "arms", "legs", "boobs", "torso"}:
#                geomobj.style = bodystyle
##            if layername in {"boobs", "torso"}:
##                geomobj.style = torsostyle
#            # make invisible elements visible
#            if hasattr(geomobj, "style"):
#                if "display:none;" in geomobj.style:
#                    geomobj.style = geomobj.style.replace("display:none;", "")
#                elif "display:none" in geomobj.style:
#                    geomobj.style = geomobj.style.replace("display:none", "")
#            # add geometry element to layer
#            xmlgeomelem = geomobj.to_xml()
#            xmllayerelem.append(xmlgeomelem)
#        # add layers
#        for layername in layerorder:
#            xmllayerelem = layerelems[layername]
#            xmlsvgelem.append(xmllayerelem)
        return svgelem

    def save_to_file(self, filepath):
        '''Write the current state of the paperdoll to a SVG file.'''
        log.info("Write paperdoll to: %s", filepath)
        # draw the paperdoll
        svgdoc = self.draw()
        # create an element tree from the svg document
        xmlsvgelem = svgdoc.to_xml()
        # create bytes from xml object
        xml = ET.tostring(xmlsvgelem)
        # add whitespace and linebreaks to SVG
#        pretty_xml = vkb.xml(xml.decode("utf-8"), shift=2)
#        xml = pretty_xml.encode("utf-8")
        # save pretty xml to file
        dollpath = Path(filepath)
        with dollpath.open("w") as f:
#            f.write(pretty_xml)
            f.write(xml.decode("utf-8"))

    def on__set_state(self, data):
        animname = data["field"]
        new = data["value"]
        old = self.state[animname]
        #TODO limit change
        # ignore if operation doesn't change anything
        if old == new:
            return
        # update internal state
        self.state[animname] = new
        # inform the world about state change
        data = {"field": animname, "old": old, "new": new}
        sisi.send(signal="state changed", channel="editor", data=data)

    def on__draw_doll(self):
        sisi.send(signal="doll drawn", data=self.draw())

    def on__export_doll(self, data):
        self.save_to_file(data["path"])

    def on__set_style(self, data):
        self.modified_styles[data["elemid"]] = data["style"]


# --------------------------------------------------------------------------- #
# Declare module globals
# --------------------------------------------------------------------------- #
log = logging.getLogger(__name__)
linestyle = svglib.Style("fill:none;stroke:#000000;stroke-width:0.58405101;" +
             "stroke-linecap:butt;stroke-linejoin:miter;" +
             "stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1")
shadowstyle = svglib.Style("display:inline;fill:none;stroke:#000000;stroke-width:7;" +
       "stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;" +
       "stroke-dasharray:none;stroke-opacity:1;filter:url(#filter6343)")
outlinestyle = svglib.Style("display:inline;opacity:0.5;fill:none;stroke:#000000;" +
        "stroke-width:0.07;stroke-linecap:butt;stroke-linejoin:miter;" +
        "stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1")
torsostyle = svglib.Style("display:inline;fill:#eac6b6;fill-opacity:1;" +
              "fill-rule:evenodd;stroke:#000000;stroke-width:0.37795276;" +
              "stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1;" +
              "stroke-miterlimit:4;stroke-dasharray:none;")
bodystyle = svglib.Style("display:inline;fill:#eac6b6;fill-opacity:1;" +
             "fill-rule:evenodd;stroke:none;")
