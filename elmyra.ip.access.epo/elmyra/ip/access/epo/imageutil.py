# -*- coding: utf-8 -*-
# (c) 2011 ***REMOVED***
# (c) 2013 Andreas Motl, Elmyra UG <andreas.motl@elmyra.de>

import os, sys
import StringIO
import subprocess

def tiff_to_png(tiff_payload):

    # unfortunately, PIL can not handle G4 compression ...
    # Failure: exceptions.IOError: decoder group4 not available
    # maybe patch: http://mail.python.org/pipermail/image-sig/2003-July/002354.html
    """
    import Image
    png = StringIO.StringIO()
    try:
        Image.open(StringIO.StringIO(tiff_payload)).save(png, 'PNG')
        png.seek(0)
    except Exception, e:
        print "ERROR (PIL+G4)!", e
        pass
    """


    # ... so use ImageMagick! ;-(
    # http://www.imagemagick.org/pipermail/magick-users/2003-May/008869.html
    #convert_bin = os.path.join(os.path.dirname(__file__), 'imagemagick', 'convert.exe')
    #command = ['convert', 'tif:-', '+set', 'date:create', '+set', 'date:modify', 'png:-']
    command = ['convert', 'tif:-',
                '+set', 'date:create', '+set', 'date:modify',
                # FIXME: make this configurable
                '-resize', '457x',
                '-colorspace', 'rgb', '-flatten', '-depth', '8',
                '-antialias', '-quality', '100', '-density', '300',
                'png:-']

    #print command

    proc = subprocess.Popen(
        command,
        shell = (os.name == 'nt'),
        #shell = True,
        stdin = subprocess.PIPE,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
    )

    stdout = stderr = ''

    def log_error():
        sys.stderr.write("ERROR: TIFF to PNG conversion failed; command was: '%s'\n" % command)
        sys.stderr.write("ERROR: TIFF to PNG conversion failed; len(tiff_payload) was: %s\n" % len(tiff_payload))
        sys.stderr.write("ERROR: TIFF to PNG conversion failed; left(STDOUT, 1000)  was:\n%s\n" % stdout[:1000])
        sys.stderr.write("ERROR: TIFF to PNG conversion failed; STDERR was:\n%s\n" % stderr)
        sys.stderr.write("ERROR: Maybe the 'convert' tool (from ImageMagick) is not available on PATH\n")

    try:
        stdout, stderr = proc.communicate(tiff_payload)
    except:
        log_error()
        return None

    print stderr

    if stdout and not 'ImageMagick' in stdout[:200]:
        #print stdout
        return stdout

    else:
        log_error()
        return None
        #raise RuntimeError, 'TIF to PNG conversion failed, please see the logs.'


def png_resize(png_payload, width):

    image = Image.open(StringIO.StringIO(png_payload)).convert('RGB')

    image_width = image.size[0]
    image_height = image.size[1]

    #aspect = float(image_width) / float(image_height)
    #print "aspect:", aspect

    scale_factor = float(image_width) / float(width)
    #print "scale_factor:", scale_factor

    #size = (int(width), int(image_height * aspect))
    size = (int(width), int(image_height / scale_factor))
    #print "size:", size
    print "Resizing image from %s to %s" % (image.size, size)

    image.thumbnail(size, Image.ANTIALIAS)
    #image.resize(size, Image.ANTIALIAS)
    #print "thumbnail done"

    png = StringIO.StringIO()
    image.save(png, 'PNG')
    #print "image saved to memory"

    png_payload_resized = png.getvalue()
    #print "got payload"

    return png_payload_resized
