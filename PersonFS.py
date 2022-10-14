#
# Gramplet - fs (interfaco por familysearch)
#
# Kopirajto © 2022 Jean Michault
# Licenco «GPL-3.0-or-later»
#
# Ĉi tiu programo estas libera programaro; vi povas redistribui ĝin kaj/aŭ modifi
# ĝi laŭ la kondiĉoj de la Ĝenerala Publika Permesilo de GNU kiel eldonita de
# la Free Software Foundation; ĉu versio 3 de la Licenco, aŭ
# (laŭ via elekto) ajna posta versio.
#
# Ĉi tiu programo estas distribuata kun la espero, ke ĝi estos utila,
# sed SEN AJN GARANTIO; sen eĉ la implicita garantio de
# KOMERCEBLECO aŭ TAĜECO POR APARTA CELO. Vidu la
# GNU Ĝenerala Publika Permesilo por pliaj detaloj.
#
# Vi devus esti ricevinta kopion de la Ĝenerala Publika Permesilo de GNU
# kune kun ĉi tiu programo; se ne, skribu al 
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"""
fs Gramplet.
"""

#-------------------------------------------------------------------------
#
# GTK modules
#
#-------------------------------------------------------------------------
from gi.repository import Gtk

#------------------------------------------------------------------------
#
# Gramps modules
#
#------------------------------------------------------------------------
from gramps.gen.config import config
from gramps.gen.const import GRAMPS_LOCALE as glocale
from gramps.gen.datehandler import get_date
from gramps.gen.display.name import displayer as name_displayer
from gramps.gen.errors import WindowActiveError
from gramps.gen.lib import StyledText, StyledTextTag, StyledTextTagType
from gramps.gen.plug import Gramplet
from gramps.gen.utils.db import get_birth_or_fallback, get_death_or_fallback

from gramps.gui.dialog import OptionDialog
from gramps.gui.editors import EditPerson
from gramps.gui.listmodel import ListModel, NOSORT
from gramps.gui.widgets.buttons import IconButton
from gramps.gui.widgets.styledtexteditor import StyledTextEditor

# lokaloj 
# from session import Session
from getmyancestors.classes.session import Session
from getmyancestors.classes.tree import Tree

import sys
import os
import time



_ = glocale.translation.gettext


#-------------------------------------------------------------------------
#
# configuration
#
#-------------------------------------------------------------------------

GRAMPLET_CONFIG_NAME = "PersonFS"
CONFIG = config.register_manager(GRAMPLET_CONFIG_NAME)
CONFIG.register("preferences.fs_userid", '')
CONFIG.register("preferences.fs_passwd", '')
CONFIG.load()



class PersonFS(Gramplet):
  """
  Gramplet to display ancestors of the active person.
  """
  def init(self):
    self.fs_userid = CONFIG.get("preferences.fs_userid")
    self.fs_passwd = CONFIG.get("preferences.fs_passwd")

    self.gui.WIDGET = self.krei_gui()
    self.gui.get_container_widget().remove(self.gui.textview)
    self.gui.get_container_widget().add_with_viewport(self.gui.WIDGET)
    self.gui.WIDGET.show_all()
    self.fs = Session(self.fs_userid, self.fs_passwd, False, False, 10)
    self.tree = Tree(self.fs)


  def krei_gui(self):
    """
    krei GUI interfaco.
    """
    grid = Gtk.Grid()
    tags = [StyledTextTag(StyledTextTagType.LINK, 'https://familysearch.org', [(0, len('family search'))])]
    textelien = StyledText('family search', tags)
    self.label = StyledTextEditor()
    self.label.set_editable(False)
    self.label.set_text(textelien)
    self.label.set_halign(Gtk.Align.START)
    self.propGr = StyledTextEditor()
    self.propGr.set_editable(False)
    self.propGr.set_halign(Gtk.Align.START)
    self.propFs = StyledTextEditor()
    self.propFs.set_editable(False)


    grid.add(self.label)
    button = IconButton( self.pref_clicked, None, 'gtk-preferences')
    grid.attach(button, 4, 0, 1, 2)
    grid.attach(self.propGr, 1, 2, 1, 1)
    grid.attach(self.propFs, 3, 2, 1, 1)
    return grid

  def pref_clicked(self, obj, event, handle):
    print ("clicked")
    # dialog = OptionDialog("Préférences de PersonFS", "Préférences",
    #                              "Sauvegarder",None, "Annuler",None)
    # texteNom = StyledText('compte family search', None)
    # self.labelNom = StyledTextEditor()
    # self.labelNom.set_editable(False)
    # self.labelNom.set_text(textelien)
    # dialog.
    # res = dialog.run()
    # print ("res = " + str(res))
    

  def get_has_data(self, active_handle):
    """
    " Return True if the gramplet has data, else return False.
    """
    if active_handle:
      person = self.dbstate.db.get_person_from_handle(active_handle)
      family_handle = person.get_main_parents_family_handle()
      if family_handle:
        family = self.dbstate.db.get_family_from_handle(family_handle)
        if family and (family.get_father_handle() or
                       family.get_mother_handle()):
          return True
    return False

  def db_changed(self):
    self.update()

  def active_changed(self, handle):
    self.update()

  def update_has_data(self):
    active_handle = self.get_active('Person')
    if active_handle:
      self.set_has_data(self.get_has_data(active_handle))
    else:
      self.set_has_data(False)

  def main(self):
    active_handle = self.get_active('Person')
    self.propGr.set_text(StyledText('',None))
    self.propFs.set_text(StyledText('',None))
    if active_handle:
      self.compareFs(active_handle)
      self.set_has_data(self.get_has_data(active_handle))
    else:
      self.set_has_data(False)

  def compareFs(self, person_handle):
    """
    Komparu gramps kaj FamilySearch
    """

    person = self.dbstate.db.get_person_from_handle(person_handle)
    fsid = ''
    for attr in person.get_attribute_list():
      if attr.get_type() == '_FSFTID':
        fsid = attr.get_value()
    lien = ''
    tags = None
    lien = 'https://familysearch.org/tree/person/' + fsid
    text = name_displayer.display(person)
    if fsid == '':
      text = 'family search'
    tags = [StyledTextTag(StyledTextTagType.LINK, lien, [(0, len(text))])]
    textelien = StyledText(text, tags)
    self.label.set_text(textelien)
    if fsid == '':
      return

    self.tree.add_indis([fsid])
    endGr = self.propGr.textbuffer.get_end_iter()
    endFs = self.propFs.textbuffer.get_end_iter()
    name = person.primary_name
    self.propGr.textbuffer.insert( endGr, name.get_primary_surname().surname + ', ' + name.first_name+'\n')
    self.propFs.textbuffer.insert( endFs, self.tree.indi[fsid].name.surname +  ', ' + self.tree.indi[fsid].name.given+'\n')

    return
