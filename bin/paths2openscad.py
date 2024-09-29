#!/usr/bin/env python3

# paths2openscad.py

# This is an Inkscape extension to output paths to extruded OpenSCAD polygons.
# The Inkscape objects must first be converted to paths (Path > Object to Path).
# Some paths may not work well -- the paths have to be polygons. As such,
# paths derived from text may meet with mixed results.

# Written by Daniel C. Newman ( dan dot newman at mtbaldy dot us )
# 10 June 2012

# 15 June 2012
#   Updated by Dan Newman to handle a single level of polygon nesting.
#   This is sufficient to handle most fonts.
#   If you want to nest two polygons, combine them into a single path
#   within Inkscape with "Path > Combine Path".

# 9 June 2017
#   Modified by Eric Van Albert to output complex polygons instead of
#   using OpenSCAD's difference()

# 29 Sept 2024
#   Updated to Python 3 and fixed deprecation issues:
#   - Replaced `cspsubdiv.maxdist` with `inkex.bezier.maxdist`
#   - Replaced `bezmisc.beziersplitatt` with `inkex.bezier.beziersplitatt`
#   - Updated to use `inkex.Transform` for matrix transformations.

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA

import math
import os.path
import inkex
import cubicsuperpath
import cspsubdiv
import inkex.bezier  # Import inkex.bezier for bezier operations
import re

DEFAULT_WIDTH = 100
DEFAULT_HEIGHT = 100

def parseLengthWithUnits(value):
    '''
    Parse an SVG value which may or may not have units attached.
    This version is simplified to handle: no units, units of px, and %.
    '''
    u = 'px'
    s = value.strip()
    if s.endswith('px'):
        s = s[:-2]
    elif s.endswith('%'):
        u = '%'
        s = s[:-1]
    try:
        v = float(s)
    except ValueError:
        return None, None
    return v, u

def pointInBBox(pt, bbox):
    '''
    Determine if the point pt=[x, y] lies on or within the bounding
    box bbox=[xmin, xmax, ymin, ymax].
    '''
    if (pt[0] < bbox[0]) or (pt[0] > bbox[1]) or (pt[1] < bbox[2]) or (pt[1] > bbox[3]):
        return False
    else:
        return True

def bboxInBBox(bbox1, bbox2):
    '''
    Determine if the bounding box bbox1 lies on or within the
    bounding box bbox2.
    '''
    if (bbox1[0] < bbox2[0]) or (bbox1[1] > bbox2[1]) or (bbox1[2] < bbox2[2]) or (bbox1[3] > bbox2[3]):
        return False
    else:
        return True

def pointInPoly(p, poly, bbox=None):
    '''
    Use a ray casting algorithm to see if the point p = [x, y] lies within
    the polygon poly = [[x1, y1], [x2, y2], ...].
    Returns True if the point is within poly, on an edge, or is a vertex.
    '''
    if (p is None) or (poly is None):
        return False

    if bbox is not None:
        if not pointInBBox(p, bbox):
            return False

    if p in poly:
        return True

    x = p[0]
    y = p[1]
    p1 = poly[0]
    p2 = poly[1]
    for i in range(len(poly)):
        if i != 0:
            p1 = poly[i-1]
            p2 = poly[i]
        if (y == p1[1]) and (p1[1] == p2[1]) and (x > min(p1[0], p2[0])) and (x < max(p1[0], p2[0])):
            return True

    n = len(poly)
    inside = False
    p1_x, p1_y = poly[0]
    for i in range(n + 1):
        p2_x, p2_y = poly[i % n]
        if y > min(p1_y, p2_y):
            if y <= max(p1_y, p2_y):
                if x <= max(p1_x, p2_x):
                    if p1_y != p2_y:
                        intersect = p1_x + (y - p1_y) * (p2_x - p1_x) / (p2_y - p1_y)
                        if x <= intersect:
                            inside = not inside
                    else:
                        inside = not inside
        p1_x, p1_y = p2_x, p2_y

    return inside

def polyInPoly(poly1, bbox1, poly2, bbox2):
    '''
    Determine if polygon poly2 contains polygon poly1.
    The bounding box information is optional and used for rejections.
    '''
    if (bbox1 is not None) and (bbox2 is not None):
        if not bboxInBBox(bbox1, bbox2):
            return False

    for p in poly1:
        if not pointInPoly(p, poly2, bbox2):
            return False

    return True

def subdivideCubicPath(sp, flat, i=1):
    '''
    Break up a bezier curve into smaller curves, each of which
    approximates a straight line within a given tolerance.
    Updated to use `inkex.bezier.maxdist`.
    '''
    while True:
        while True:
            if i >= len(sp):
                return

            p0 = sp[i - 1][1]
            p1 = sp[i - 1][2]
            p2 = sp[i][0]
            p3 = sp[i][1]

            b = (p0, p1, p2, p3)

            # Updated: Using inkex.bezier.maxdist for maximum distance calculation
            if inkex.bezier.maxdist(b) > flat:
                break

            i += 1

        # Updated: Using inkex.bezier.beziersplitatt to split the bezier curve
        one, two = inkex.bezier.beziersplitatt(b, 0.5)
        sp[i - 1][2] = one[1]
        sp[i][0] = two[2]
        p = [one[2], one[3], two[1]]
        sp[i:1] = [p]

class OpenSCAD(inkex.EffectExtension):
    def __init__(self):
        super().__init__()

        self.arg_parser.add_argument('--smoothness', type=float, default=0.02, help='Curve smoothing (less for more)')
        self.arg_parser.add_argument('--fname', default='~/inkscape.scad', help='Output filename for OpenSCAD')

        self.cx = float(DEFAULT_WIDTH) / 2.0
        self.cy = float(DEFAULT_HEIGHT) / 2.0
        self.xmin, self.xmax = (1.0E70, -1.0E70)
        self.ymin, self.ymax = (1.0E70, -1.0E70)

        self.paths = {}
        self.call_list = []
        self.pathid = int(0)

        self.f = None

        self.docWidth = float(DEFAULT_WIDTH)
        self.docHeight = float(DEFAULT_HEIGHT)
        self.docTransform = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]

        self.warnings = {}

    def getLength(self, name, default):
        '''
        Get the <svg> attribute with name "name" and convert to pixels.
        '''
        value = self.svg.get(name)
        if value:
            v, u = parseLengthWithUnits(value)
            if not v:
                return None
            elif u == 'mm':
                return float(v) * (90.0 / 25.4)
            elif u == 'cm':
                return float(v) * (90.0 * 10.0 / 25.4)
            elif u == 'm':
                return float(v) * (90.0 * 1000.0 / 25.4)
            elif u == 'in':
                return float(v) * 90.0
            elif u == 'ft':
                return float(v) * 12.0 * 90.0
            elif u == 'pt':
                return float(v) * (90.0 / 72.0)
            elif u == 'pc':
                return float(v) * (90.0 / 6.0)
            elif u == 'px':
                return float(v)
            else:
                return None
        else:
            return float(default)

    def getDocProps(self):
        '''
        Get the document's height and width attributes from the <svg> tag.
        '''
        self.docHeight = self.getLength('height', DEFAULT_HEIGHT)
        self.docWidth = self.getLength('width', DEFAULT_WIDTH)
        if (self.docHeight is None) or (self.docWidth is None):
            return False
        else:
            return True

    def handleViewBox(self):
        '''
        Set up the document-wide transform in case of an SVG viewbox.
        '''
        if self.getDocProps():
            viewbox = self.svg.get('viewBox')
            if viewbox:
                vinfo = viewbox.strip().replace(',', ' ').split(' ')
                if float(vinfo[2]) != 0 and float(vinfo[3]) != 0:
                    sx = self.docWidth / float(vinfo[2])
                    sy = self.docHeight / float(vinfo[3])
                    self.docTransform = inkex.Transform(f'scale({sx},{sy})').matrix

    def getPathVertices(self, path, node=None, transform=None):
        '''
        Decompose the path data into individual subpaths.
        '''
        if (not path) or (len(path) == 0):
            return None

        try:
            sp = inkex.Path(path).to_superpath()
        except Exception as e:
            inkex.utils.debug(f"Error parsing path: {e}")
            return None

        if transform:
            sp = inkex.Path(sp).transform(transform).to_superpath()

        subpath_list = []
        subpath_vertices = []

        for sub_path in sp:
            if len(subpath_vertices):
                subpath_list.append([subpath_vertices, [sp_xmin, sp_xmax, sp_ymin, sp_ymax]])

            subpath_vertices = []
            subdivideCubicPath(sub_path, float(self.options.smoothness))

            first_point = sub_path[0][1]
            subpath_vertices.append(first_point)
            sp_xmin = first_point[0]
            sp_xmax = first_point[0]
            sp_ymin = first_point[1]
            sp_ymax = first_point[1]

            n = len(sub_path)
            last_point = sub_path[n-1][1]
            if (first_point[0] == last_point[0]) and (first_point[1] == last_point[1]):
                n = n - 1

            for csp in sub_path[1:n]:
                pt = csp[1]
                subpath_vertices.append(pt)

                if pt[0] < sp_xmin:
                    sp_xmin = pt[0]
                elif pt[0] > sp_xmax:
                    sp_xmax = pt[0]
                if pt[1] < sp_ymin:
                    sp_ymin = pt[1]
                elif pt[1] > sp_ymax:
                    sp_ymax = pt[1]

            if sp_xmin < self.xmin:
                self.xmin = sp_xmin
            if sp_xmax > self.xmax:
                self.xmax = sp_xmax
            if sp_ymin < self.ymin:
                self.ymin = sp_ymin
            if sp_ymax > self.ymax:
                self.ymax = sp_ymax

        if len(subpath_vertices):
            subpath_list.append([subpath_vertices, [sp_xmin, sp_xmax, sp_ymin, sp_ymax]])

        if len(subpath_list) > 0:
            self.paths[node] = subpath_list

    def convertPath(self, node):
        '''
        Generate an OpenSCAD module for this path.
        '''
        path = self.paths.get(node)
        if (path is None) or (len(path) == 0):
            return

        contains = [[] for _ in range(len(path))]
        contained_by = [[] for _ in range(len(path))]

        for i in range(len(path)):
            for j in range(i + 1, len(path)):
                if polyInPoly(path[j][0], path[j][1], path[i][0], path[i][1]):
                    contains[i].append(j)
                    contained_by[j].append(i)
                elif polyInPoly(path[i][0], path[i][1], path[j][0], path[j][1]):
                    contains[j].append(i)
                    contained_by[i].append(j)

        id = node.get('id', '')
        if (id is None) or (id == ''):
            id = str(self.pathid) + 'x'
            self.pathid += 1
        else:
            id = re.sub('[^A-Za-z0-9_]+', '', id)

        scale = (1, -1)
        self.call_list.append(f'//polygon(points={id}_points, paths={id}_paths);\n')

        points = []
        paths = []

        for i in range(len(path)):
            if len(contained_by[i]) != 0:
                continue

            subpath = path[i][0]
            bbox = path[i][1]

            one_path = []
            for point in subpath:
                one_path.append(len(points))
                points.append((point[0] - self.cx, point[1] - self.cy))

            paths.append(one_path)

            if len(contains[i]) != 0:
                for j in contains[i]:
                    one_path = []
                    for point in path[j][0]:
                        one_path.append(len(points))
                        points.append((point[0] - self.cx, point[1] - self.cy))

                    paths.append(list(reversed(one_path)))

        points_str = "[{}]".format(", ".join(["[{:8f}, {:8f}]".format(x * scale[0], y * scale[1]) for (x, y) in points]))
        paths_str = "[{}]".format(", ".join(["[{}]".format(", ".join(["{:d}".format(i) for i in indices])) for indices in paths]))

        self.f.write(f'{id}_points = {points_str};\n')
        self.f.write(f'{id}_paths = {paths_str};\n')

    def recursivelyTraverseSvg(self, aNodeList, matCurrent=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], parent_visibility='visible'):
        '''
        Recursively walk the SVG document, building polygon vertex lists
        for each graphical element.
        '''
        for node in aNodeList:
            v = node.get('visibility', parent_visibility)
            if v == 'inherit':
                v = parent_visibility
            if v == 'hidden' or v == 'collapse':
                continue

            matNew = inkex.Transform(matCurrent) @ inkex.Transform(node.get("transform"))

            if node.tag == inkex.addNS('g', 'svg') or node.tag == 'g':
                self.recursivelyTraverseSvg(node, matNew, v)

            elif node.tag == inkex.addNS('path', 'svg'):
                path_data = node.get('d')
                if path_data:
                    self.getPathVertices(path_data, node, matNew)

    def effect(self):
        '''
        Main effect execution.
        '''
        self.handleViewBox()
        self.recursivelyTraverseSvg(self.svg.root, self.docTransform)
        self.cx = self.xmin + (self.xmax - self.xmin) / 2.0
        self.cy = self.ymin + (self.ymax - self.ymin) / 2.0

        try:
            self.f = open(os.path.expanduser(self.options.fname), 'w')
            self.f.write('''// Automatically generated using the Inkscape to OpenSCAD Converter
// Variable names are of the form <inkscape-path-id>_points and
// <inkscape-path-id>_paths. As a result, you can associate a polygon in this
// OpenSCAD program with the corresponding SVG element in the Inkscape document
// by looking for the XML element with the attribute id="inkscape-path-id".
''')

            for key in self.paths:
                self.f.write('\n')
                self.convertPath(key)

            self.f.write('\n')
            for call in self.call_list:
                self.f.write(call)
            self.f.close()
        except IOError:
            inkex.errormsg(f'Unable to open the file {self.options.fname}')

if __name__ == '__main__':
    e = OpenSCAD()
    e.run()
