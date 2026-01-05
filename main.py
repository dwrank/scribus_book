#!/usr/bin/env python3

import scribus as scr

from book import ScribusBook


def create_doc(xmldir, xmlbook):
    if scr.haveDoc():
        u  = scr.getUnit()                                # Get the units of the document
        al = scr.getActiveLayer()                         # Identify the working layer
        scr.setUnit(scr.UNIT_INCHES)                     # Set the document units to mm,                                            
        (w, h) = scr.getPageSize()                         # needed to set the text box size

        scr.createLayer("c")
        scr.setActiveLayer("c")

        book = ScribusBook(w, h)
        book.create_doc(xmldir, xmlbook)

        scr.setUnit(u)                                   # return to original document units
        scr.setActiveLayer(al)                           # return to the original active layer


if __name__ == '__main__':
    #create_doc("/home/drank/dev/books/side-by-side/the_dialog", "book.xml")
    create_doc("/home/drank/dev/books/side-by-side/dark_night", "book.xml")
