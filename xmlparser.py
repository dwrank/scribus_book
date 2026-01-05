import os
import xml.etree.ElementTree as ET


def parse_xml_file(path, fname):
    with open(os.path.join(path, fname), encoding='utf-8') as f:
        root = ET.fromstring(f.read())

    for inp in root.findall('import'):
        url = inp.attrib['url']
        #print(f'importing url: {url}')
        inp_elem = parse_xml_file(path, url)

        index = list(root).index(inp)
        root.remove(inp)
        root.insert(index, inp_elem)

    return root


if __name__ == '__main__':
    xml = parse_xml_file('.', 'ch1.xml')
    #print(ET.tostring(xml, encoding='unicode'))

