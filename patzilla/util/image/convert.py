# -*- coding: utf-8 -*-
# (c) 2011-2018 Andreas Motl <andreas.motl@ip-tools.org>
import os
import where
import logging
import datetime
import StringIO
import subprocess
from six import BytesIO
from tempfile import NamedTemporaryFile
from cornice.util import to_list
from patzilla.util.python.decorators import memoize
from patzilla.util.python.system import run_command

logger = logging.getLogger(__name__)


def to_png(tiff, width=None, height=None):
    """
    Convert image to PNG format with optional resizing.

    :param tiff: A stream buffer object like BytesIO
    :param width: The width of the image in pixels (optional)
    :param height: The height of the image in pixels (optional)
    :return: A BytesIO object instance containing image data
    """


    """
    The PIL module didn't properly support TIFF images with G4 compression::

        Failure: exceptions.IOError: decoder group4 not available
        Maybe patch: http://mail.python.org/pipermail/image-sig/2003-July/002354.html

    Nowadays, this should be supported by Pillow on recent platforms:
    https://pillow.readthedocs.io/en/latest/releasenotes/5.0.0.html#compressed-tiff-images
    """
    try:
        from PIL import Image

        # Read image
        image = Image.open(tiff)

        if width and height:

            # Convert image to grayscale
            image = image.convert('L')

            # Resize image
            image.thumbnail((width, height), Image.LANCZOS)

        # Save image into a stream buffer
        png = BytesIO()
        image.save(png, 'PNG')

        # Readers should start reading at the beginning of the stream
        png.seek(0)

        return png

    except Exception as ex:
        logger.warning('Image conversion using "Pillow" failed: {}'.format(ex))


    """
    However, if the conversion using "Pillow" fails for some reason,
    let's try to use the "convert" utility from ImageMagick.


    Instructions for installing ImageMagick on Debian::

        apt install imagemagick

    Instructions for installing ImageMagick on Windows::

        https://www.imagemagick.org/script/download.php#windows

    Instructions for building ImageMagick on Debian::

        # https://packages.debian.org/source/wheezy/imagemagick
        aptitude install build-essential checkinstall ghostscript libbz2-dev libexif-dev fftw-dev libfreetype6-dev libjasper-dev libjpeg-dev liblcms2-dev liblqr-1-0-dev libltdl-dev libpng-dev librsvg2-dev libtiff-dev libx11-dev libxext-dev libxml2-dev zlib1g-dev liblzma-dev libpango1.0-dev

        ./configure --prefix=/opt/imagemagick-7.0.2
        wget http://www.imagemagick.org/download/ImageMagick.tar.gz
        # untar and cd
        make -j6 && make install

    """

    more_args = []

    # Compute value for "resize" parameter
    size = ''
    if width or height:

        if width:
            size += str(width)

        # Use "x" for separating "width" and "height" when resizing
        size += 'x'

        if height:
            size += str(height)

        more_args += ['-resize', size]

    convert = find_convert()
    if not convert:
        message = 'Could not find ImageMagick program "convert", please install from e.g. https://imagemagick.org/'
        logger.error(message)
        raise AssertionError(message)

    command = [
        convert,
        '+set', 'date:create', '+set', 'date:modify',
        '-colorspace', 'rgb', '-flatten', '-depth', '8',
        '-antialias', '-quality', '100', '-density', '300',
        # '-level', '30%,100%',

        # Debugging
        # (see "convert -list debug")
        #'-verbose',
        #'-debug', 'All',

        ] \
        + more_args + \
        [

        # Convert from specific format
        #'{0}:-'.format(format),

        # Convert from any format
        '-',

        # Convert to PNG format
        'png:-',
    ]

    command_string = ' '.join(command)
    try:
        logger.debug('Converting image using "{}"'.format(command_string))
        return run_imagemagick(command, tiff.read())

    except Exception as ex:
        logger.error('Image conversion using ImageMagicks "convert" program failed: {}'.format(ex))
        raise


def run_imagemagick(command, input=None):
    output = run_command(command, input)
    if 'ImageMagick' in output.read()[:200]:
        command_string = ' '.join(command)
        message = 'Image conversion failed, found "ImageMagick" in STDOUT. Command was "{}"'.format(command_string)
        logger.error(message)
        raise RuntimeError(message)
    output.seek(0)
    return output


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


def pdf_join(pages):
    # pdftk in1.pdf in2.pdf cat output out1.pdf
    # pdftk in.pdf dump_data output report.txt
    # pdftk in.pdf update_info in.info output out.pdf
    # pdftk in.pdf update_info_utf8 in.info output out.pdf
    # pdftk in.pdf attach_files table1.html table2.html to_page 6 output out.pdf

    pdftk = find_pdftk()
    if not pdftk:
        message = 'Could not find program "pdftk", please install it'
        logger.error(message)
        raise AssertionError(message)

    # Build shellout command
    command = [pdftk]
    tmpfiles = []
    for page in pages:
        tmpfile = NamedTemporaryFile()
        tmpfile.write(page)
        tmpfile.flush()

        tmpfiles.append(tmpfile)
        command.append(tmpfile.name)

    command += ['cat', 'output', '-']

    #logger.info('command={0}'.format(' '.join(command)))

    cmddebug = ' '.join(command)
    stdout = stderr = ''

    try:
        proc = subprocess.Popen(
            command,
            shell = (os.name == 'nt'),
            #shell = True,
            stdin = subprocess.PIPE,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
        )

        stdout, stderr = proc.communicate()
        if proc.returncode is not None and proc.returncode != 0:
            logger.error('pdftk joining failed, command={0}, stderr={1}, returncode={2}'.format(cmddebug, stderr, proc.returncode))

    except Exception as ex:
        logger.error('pdftk joining failed, command={0}, exception={1}, stderr={2}'.format(cmddebug, ex, stderr))

    finally:
        for tmpfile in tmpfiles:
            try:
                tmpfile.close()
            except Exception as ex:
                logger.warn('Unable to delete temporary file "%s": %s', tmpfile.name, ex)

    return stdout


def pdf_set_metadata(pdf_payload, metadata):

    # scdsc
    # PDF Producer: BNS/PXI/BPS systems of the EPO
    # Content creator: -
    # Mod-date: -
    # Author: -
    # Subject: -
    # Title: EP        0666666A2 I
    pass

    tmpfile = NamedTemporaryFile(delete=False)
    tmpfile.write(metadata)
    tmpfile.flush()

    """
    command = [find_pdftk(), '-', 'dump_data', 'output', '-']
    proc = subprocess.Popen(
        command,
        shell = (os.name == 'nt'),
        #shell = True,
        stdin = subprocess.PIPE,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
    )
    stdout, stderr = proc.communicate(pdf_payload)
    print stdout
    #sys.exit()
    """


    command = [find_pdftk(), '-', 'update_info', tmpfile.name, 'output', '-']

    #logger.info('command={0}'.format(' '.join(command)))

    cmddebug = ' '.join(command)
    stdout = stderr = ''

    try:

        proc = subprocess.Popen(
            command,
            shell = (os.name == 'nt'),
            #shell = True,
            stdin = subprocess.PIPE,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
        )

        stdout, stderr = proc.communicate(pdf_payload)
        if proc.returncode is not None and proc.returncode != 0:
            logger.error('pdftk metadata store failed, command={0}, stderr={1}'.format(cmddebug, stderr))
            raise Exception()

    except Exception as ex:
        logger.error('pdftk metadata store failed, command={0}, exception={1}, stderr={2}'.format(cmddebug, ex, stderr))
        raise

    return stdout


def pdf_make_metadata(title, producer, pagecount, page_sections=None):

    page_sections = page_sections and to_list(page_sections) or []

    date = pdf_now()

    tpl = """
InfoBegin
InfoKey: Title
InfoValue: {title}
InfoBegin
InfoKey: Producer
InfoValue: {producer}
InfoBegin
InfoKey: Creator
InfoValue:
InfoBegin
InfoKey: ModDate
InfoValue:
InfoBegin
InfoKey: CreationDate
InfoValue: {date}

NumberOfPages: {pagecount}
"""

    metadata = tpl.format(**locals())

    # https://stackoverflow.com/questions/2969479/merge-pdfs-with-pdftk-with-bookmarks/20333267#20333267
    bookmark_tpl = """
BookmarkBegin
BookmarkTitle: {title}
BookmarkLevel: {level}
BookmarkPageNumber: {start_page}
"""

    for page_section in page_sections:
        name = page_section['@name']
        start_page = page_section['@start-page']
        if name == 'SEARCH_REPORT':
            title = 'Search-report'
        else:
            title = name.title()
        level = 1

        metadata += bookmark_tpl.format(**locals())

    return metadata


def pdf_now():
    # D:20150220033046+01'00'
    now = datetime.datetime.now().strftime("D:%Y%m%d%H%M%S+01'00'")
    return now


@memoize
def find_convert():
    """
    Debian: aptitude install imagemagick
    /usr/bin/convert

    Mac OS X with Homebrew
    /usr/local/bin/convert

    Mac OS X with Macports
    /opt/local/bin/convert

    Self-compiled
    /opt/imagemagick/bin/convert
    /opt/imagemagick-7.0.2/bin/convert
    """

    # Some nailed location candidates
    candidates = [
        '/opt/imagemagick-7.0.2/bin/convert',
        '/opt/imagemagick/bin/convert',
        '/usr/local/bin/convert',
        '/opt/local/bin/convert',
        '/usr/bin/convert',
    ]

    # More location candidates from the system
    candidates += where.where('convert')

    # Find location of "convert" program
    convert_path = find_program_candidate(candidates)

    logger.info('Found "convert" program at {}'.format(convert_path))
    return convert_path

@memoize
def find_pdftk():
    """
    Debian: aptitude install pdftk
    /usr/bin/pdftk

    Mac OS X
    /opt/pdflabs/pdftk/bin/pdftk

    Self-compiled
    /usr/local/bin/pdftk
    """

    candidates = [
        '/opt/pdflabs/pdftk/bin/pdftk',
        '/usr/local/bin/pdftk',
        '/usr/bin/pdftk',
    ]

    # More location candidates from the system
    candidates += where.where('pdftk')

    return find_program_candidate(candidates)

def find_program_candidate(candidates):
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
