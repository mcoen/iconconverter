# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import os
import re

from collections import OrderedDict

import tinycss
from PIL import Image, ImageFont, ImageDraw
from six import unichr


class IconFontConverter(object):
    """Base class that represents web icon font"""
    def __init__(self, cssFile, ttfFile, keepPrefix=False):
        """
        :param cssFile: path to icon font CSS file
        :param ttfFile: path to icon font TTF file
        :param keepPrefix: whether to keep common icon prefix
        """
        self.cssFile = cssFile
        self.ttfFile = ttfFile
        self.keepPrefix = keepPrefix
        self.cssIcons, self.commonPrefix = self.loadCSS()

    def loadCSS(self):
        """
        Creates a dict of all icons available in CSS file, and finds out
        what's their common prefix.

        :returns sorted icons dict, common icon prefix
        """
        icons = dict()
        commonPrefix = None
        parser = tinycss.make_parser()
        stylesheet = parser.parse_stylesheet_file(self.cssFile)

        isIcon = re.compile("\.(.*):before,?")

        for rule in stylesheet.rules:
            selector = rule.selector.as_css()
#
            # Skip CSS classes that are not icons
            if not isIcon.match(selector):
                continue

            # Find out what the common prefix is
            if commonPrefix is None:
                commonPrefix = selector[1:]
            else:
                commonPrefix = os.path.commonprefix((commonPrefix,
                                                      selector[1:]))

            for match in isIcon.finditer(selector):
                name = match.groups()[0].strip(':')
                for declaration in rule.declarations:
                    if declaration.name == "content":
                        val = declaration.value.as_css()
                        # Strip quotation marks
                        if re.match("^['\"].*['\"]$", val):
                            val = val[1:-1]
                        icons[name] = unichr(int(val[1:], 16))

        commonPrefix = commonPrefix or ''

        # Remove common prefix
        if not self.keepPrefix and len(commonPrefix) > 0:
            nonPrefixedIcons = {}
            for name in icons.keys():
                nonPrefixedIcons[name[len(commonPrefix):]] = icons[name]
            icons = nonPrefixedIcons

        sortedIcons = OrderedDict(sorted(icons.items(), key=lambda t: t[0]))

        return sortedIcons, commonPrefix

    def exportIcon(self, icon, size, color='#5DADE2', scale='auto',
                    filename=None, exportDir='output'):
        """
        Exports given icon with provided parameters.

        If the desired icon size is less than 150x150 pixels, we will first
        create a 150x150 pixels image and then scale it down, so that
        it's much less likely that the edges of the icon end up cropped.

        :param icon: valid icon name
        :param filename: name of the output file
        :param size: icon size in pixels
        :param color: color name or hex value
        :param scale: scaling factor between 0 and 1,
                      or 'auto' for automatic scaling
        :param exportDir: path to export directory
        """

        print(self.cssIcons[icon])

        orgSize = size
        size = max(200, size)

        image = Image.new("RGBA", (size, size), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        if scale == 'auto':
            scaleFactor = 1
        else:
            scaleFactor = float(scale)

        font = ImageFont.truetype(self.ttfFile, int(size * scaleFactor))

        height = 0
        width = draw.textlength(self.cssIcons[icon], font)

        # If auto-scaling is enabled, we need to make sure the resulting
        # graphic fits inside the boundary. The values are rounded and may be
        # off by a pixel or two, so we may need to do a few iterations.
        # The use of a decrementing multiplication factor protects us from
        # getting into an infinite loop.
        if scale == 'auto':
            iteration = 0
            factor = 1

            while True:
 #               width, height = draw.textsize(self.cssIcons[icon], font=font)
                width = draw.textlength(self.cssIcons[icon], font)

                # Check if the image fits
                dim = max(width, height)
                if dim > size:
                    font = ImageFont.truetype(self.ttfFile,
                                              int(size * size/dim * factor))
                else:
                    break

                # Adjust the factor every two iterations
                iteration += 1
                if iteration % 2 == 0:
                    factor *= 0.99

        draw.text((float(size - width) / 2, float(size - height) / 4),
                  self.cssIcons[icon], font=font, fill=color)

        # Create an alpha mask
        imageMask = Image.new("L", (size, size), 0)
        drawMask = ImageDraw.Draw(imageMask)

        # Draw the icon on the mask
        drawMask.text((float(size - width) / 2, float(size - height) / 4),
                       self.cssIcons[icon], font=font, fill=255)

        # Create a solid color image and apply the mask
        iconImage = Image.new("RGBA", (size, size), color)
        iconImage.putalpha(imageMask)

        border_w = 0
        border_h = 0

        # Create output image
        outImage = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        outImage.paste(iconImage, (border_w, border_h))

        # If necessary, scale the image to the target size
        if orgSize != size:
            outImage = outImage.resize((orgSize, orgSize), Image.ANTIALIAS)

        # Make sure export directory exists
        if not os.path.exists(exportDir):
            os.makedirs(exportDir)

        # Default filename
        if not filename:
            filename = icon + '.png'

        # Save file
        outImage.save(os.path.join(exportDir, filename))
