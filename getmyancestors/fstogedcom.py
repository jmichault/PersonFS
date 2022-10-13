#!/usr/bin/env python3
# coding: utf-8

# global imports
import os
import sys
from tkinter import (
    Tk,
    PhotoImage,
)

# local imports
from getmyancestors.classes.gui import (
    FStoGEDCOM,
)


def main():
    root = Tk()
    root.title("FamilySearch to GEDCOM")
    if sys.platform != "darwin":
        root.iconphoto(
            True,
            PhotoImage(file=os.path.join(os.path.dirname(__file__), "fstogedcom.png")),
        )
    fstogedcom = FStoGEDCOM(root)
    fstogedcom.mainloop()


if __name__ == "__main__":
    main()
