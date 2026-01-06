import xml.etree.ElementTree as ET
import scribus as scr

from xmlparser import parse_xml_file


log_en = False
log_en = True


FONT_GEORGIA_BOLD = 'Georgia Bold'
FONT_GEORGIA_REGULAR = 'Georgia Regular'
FONT_GEORGIA_ITALIC = 'Georgia Italic'

DEFAULT_STYLE_NAME = 'Default Character Style'
SUPERSCRIPT_STYLE_NAME = 'SuperscriptStyle'

INIT_TEXT_FIELD_HEIGHT = 0.2


def log(s):
    if log_en:
        print(s)


def create_super_script():
    scr.createCharStyle(
        name = SUPERSCRIPT_STYLE_NAME,
        features = 'superscript',
        fillcolor='Red',
        font = FONT_GEORGIA_REGULAR,
        fontsize = 10,
        baselineoffset = 0.25,
    )


def strip_text(text):
    s = ''
    sp = ''
    for line in text.strip().splitlines():
        s += sp + line.strip()
        sp = ' '
    return s


class FontSettings(object):
    def __init__(self, name, size):
        self.name = name
        self.size = size


def is_attrib(xml, name, val):
    return name in xml.attrib and xml.attrib[name] == val


def is_attrib_type(xml, val):
    return is_attrib(xml, 'type', val)


def is_container(xml):
    return is_attrib_type(xml, 'container')


def is_footnote_ref(xml):
    return is_attrib_type(xml, 'footnote')


class ScribusBook(object):
    def __init__(self, w, h):
        create_super_script()

        self.width = w
        self.height = h
        self.fonts = {
                'b1': FontSettings(FONT_GEORGIA_BOLD, 13),
                'b2': FontSettings(FONT_GEORGIA_BOLD, 12),
                'b3': FontSettings(FONT_GEORGIA_BOLD, 10),
                'b4': FontSettings(FONT_GEORGIA_BOLD, 9),
                'i3': FontSettings(FONT_GEORGIA_ITALIC, 10),
                't3': FontSettings(FONT_GEORGIA_REGULAR, 10),
                't4': FontSettings(FONT_GEORGIA_REGULAR, 9),
        }

        self.margins = [0.5604] * 4
        self.y = self.top_margin()

        self.note_x = 0.5604
        self.note_width = 1.0046

        self.es_text_x = 1.7548
        self.es_text_width = 3.0

        self.en_text_x = 4.9407
        self.en_text_width = 3.0

        self.page_size = scr.getPageSize()
        self.page_margins = scr.getPageMargins()

    def top_margin(self):
        return self.margins[0]

    def get_note_fonts(self):
        return self.fonts['b4'], self.fonts['t4']

    def get_font(self, xml):
        font = self.fonts['t3']
        try:
            font = self.fonts[xml.attrib['font']]
        except:
            pass
        return font

    def create_doc(self, path, fname):
        self.xml_path = path
        xml = parse_xml_file(path, fname)
        log(ET.tostring(xml, encoding='unicode'))
        self.create_book(xml)

    def create_book(self, xml):
        name = xml.attrib['name']
        log(f'\nBook Title: {name}')

        for part in xml.findall('part'):
            self.create_part(part)

    def create_part(self, xml):
        id = xml.attrib['id']
        log(f'\nPart: {id}')

        for chapter in xml.findall('chapter'):
            self.create_chapter(chapter)

    def create_chapter(self, xml):
        id = xml.attrib['id']
        log(f'\nChapter: {id}')

        for block in xml.findall('block'):
            self.create_block(block)

    def create_block(self, xml):
        log(f'\nBlock:')

        note_h = 0
        _, note_h = self.create_notes(xml)
        if note_h == 0:
            note_h = INIT_TEXT_FIELD_HEIGHT
        _, text_h = self.create_text(xml, note_h)

        self.y += max(note_h, text_h)

    def create_text(self, xml, init_height=1):
        eslist = xml.findall('es')
        enlist = xml.findall('en')
        T_es = self.create_text_field('Text', 'es', self.es_text_x, self.y,
                                   self.es_text_width, init_height, eslist)
        h = scr.getSize(T_es)[1]
        if h > init_height:
            init_height = h
        T_en = self.create_text_field('Text', 'en', self.en_text_x, self.y,
                                   self.en_text_width, init_height, enlist)

        w, h = scr.getSize(T_en)
        x, y = scr.getPosition(T_en)
        y_max = self.page_size[1] - self.page_margins[3]
        ov = y + h - y_max
        print(f'CHECK, ({x}, {y}): {w} x {h}, y_max: {y_max}, ov: {ov}')
        if ov > 0:
            h -= ov
            print(f'OVERFLOW, resize to {w} x {h}')
            scr.newPage(-1)
            self.y = self.top_margin()
            T_es2 = scr.createText(self.es_text_x, self.y, w, ov)
            T_en2 = scr.createText(self.en_text_x, self.y, w, ov)
            scr.linkTextFrames(T_es, T_es2)
            scr.linkTextFrames(T_en, T_en2)
            scr.sizeObject(w, h, T_es)
            scr.sizeObject(w, h, T_en)
            h = ov

        return w, h

    def create_text_field(self, name, ttype, x, y, w, h, elem_list):
        T = None
        if len(elem_list):
            T = scr.createText(x, y, w, h)

            log(f'\n{name}:')

            pos = 0
            for i in range(len(elem_list)):
                if i != 0:
                    scr.insertText(f'\n\n', -1, T)

                elem = elem_list[i]

                if is_container(elem):
                    pos = self.append_container_text(elem, pos, T)
                else:
                    font = self.get_font(elem)
                    pos = self.append_text_field(strip_text(elem.text), font, pos, T)

            scr.insertText('\n ', -1, T)

        if scr.textOverflows(T):
            fit_text_to_frame(T)

        return T

    def append_container_text(self, elem, pos, T):
        font = self.get_font(elem)
        text_elems = elem.findall('text')
        sp = ''
        for text_elem in text_elems:
            text_font = self.get_font(text_elem)
            if text_font is None:
                text_font = font

            is_superscript = is_footnote_ref(text_elem)
            if is_superscript:
                char_style = SUPERSCRIPT_STYLE_NAME
            else:
                char_style = None

            pos = self.append_text_field(
                    sp + strip_text(text_elem.text), text_font, pos, T, char_style=char_style)

            if is_superscript:
                sp = ' '
            else:
                sp = ''

        footnotes = elem.findall('footnote')

        if len(footnotes):
            scr.insertText(f'\n', -1, T)
            pos += 1

        for footnote in footnotes:
            text_font = self.get_font(footnote)
            if text_font is None:
                text_font = font
            fid = footnote.attrib['id']
            pos = self.append_text_field('\n' + fid, text_font, pos, T, char_style=SUPERSCRIPT_STYLE_NAME)
            pos = self.append_text_field(' ' + strip_text(footnote.text), text_font, pos, T)

        return pos

    def append_text_field(self, text, font, pos, T, char_style=None):
        log(f'Inserting text at {pos}, len: {len(text)}, font: {font.name} {font.size}, style: {char_style}\n{text}')

        scr.insertText(f'{text}', pos, T)
        scr.selectText(pos, len(text), T)
        if (char_style):
            scr.setCharacterStyle(char_style, T)
        else:
            scr.setCharacterStyle(DEFAULT_STYLE_NAME, T)
            scr.setFont(font.name, T)
            scr.setFontSize(font.size, T)
        scr.selectText(0, 0, T)
        scr.layoutText(T)

        return pos + len(text)

    def create_notes(self, xml, init_height=INIT_TEXT_FIELD_HEIGHT):
        xml_notes = xml.findall('notes')
        eslist = []
        enlist = []
        for xml_note in xml_notes:
            eslist += xml_note.findall('es')
            enlist += xml_note.findall('en')
        return self.create_note_field(eslist, enlist, init_height)

    def create_note_field(self, eslist, enlist, init_height):
        phrases = list(zip(eslist, enlist))

        pos = 0
        if len(phrases):
            has_text = False
            for i in range(len(phrases)):
                es, en = phrases[i]
                es = strip_text(es.text)
                en = strip_text(en.text)
                if es or en:
                    has_text = True

            if has_text:
                T = scr.createText(self.note_x, self.y, self.note_width, init_height)

                fonts = self.get_note_fonts()

                log(f'\nNotes:')
                for i in range(len(phrases)):
                    if i != 0:
                        scr.insertText(f'\n\n', -1, T)
                        pos += 2

                    es, en = phrases[i]
                    es = strip_text(es.text)
                    en = strip_text(en.text)

                    log(f'es: {es}')
                    log(f'en: {en}')

                    scr.insertText(f'{es}\n', pos, T)
                    scr.selectText(pos, len(es), T)
                    scr.setFont(fonts[0].name, T)
                    scr.setFontSize(fonts[0].size, T)
                    pos += len(es) + 1

                    scr.insertText(f'{en}', pos, T)
                    scr.selectText(pos, len(en), T)
                    scr.setFont(fonts[1].name, T)
                    scr.setFontSize(fonts[1].size, T)
                    pos += len(en)

                scr.insertText('\n ', -1, T)
                return fit_text_to_frame(T)

        return 0, 0


def fit_text_to_frame(T):
    w, h = scr.getSize(T)

    i = 0.5
    while scr.textOverflows(T):
        h += i
        #print(f'Text overflows, resizing to {w} {h}')
        scr.sizeObject(w, h, T)

    i = 0.1
    while not scr.textOverflows(T):
        h -= i
        #print(f'Text overflows, resizing to {w} {h}')
        scr.sizeObject(w, h, T)

    h += i
    scr.sizeObject(w, h, T)

    return w, h


if __name__ == '__main__':
    log_en = True
    book = ScribusBook()
    book.create_doc('book.xml')
