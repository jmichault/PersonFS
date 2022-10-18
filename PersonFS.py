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
from gramps.gen.lib import Date, EventType, EventRoleType, Person, StyledText, StyledTextTag, StyledTextTagType
from gramps.gen.lib.date import gregorian
from gramps.gen.plug import Gramplet
from gramps.gen.utils.db import get_birth_or_fallback, get_death_or_fallback

from gramps.gui.dialog import OptionDialog
from gramps.gui.editors import EditPerson
from gramps.gui.listmodel import ListModel, NOSORT, COLOR
from gramps.gui.widgets.buttons import IconButton
from gramps.gui.widgets.styledtexteditor import StyledTextEditor

# lokaloj 
from getmyancestors.classes.session import Session
from getmyancestors.classes.constants import FACT_TAGS
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
CONFIG.register("preferences.fs_id", '')
CONFIG.register("preferences.fs_pasvorto", '')
CONFIG.load()


def grdato_al_formal( dato) :
  res=''
  gdato = gregorian(dato)
  if gdato.modifier == Date.MOD_ABOUT :
    res = 'A'
  elif gdato.modifier == Date.MOD_BEFORE:
    res = '/'
  if gdato.dateval[Date._POS_YR] < 0 :
    res = res + '-'
  else :
    res = res + '+'
  if gdato.dateval[Date._POS_DAY] > 0 :
    val = "%04d-%02d-%02d" % (
                gdato.dateval[Date._POS_YR], gdato.dateval[Date._POS_MON],
                gdato.dateval[Date._POS_DAY])
  elif gdato.dateval[Date._POS_MON] > 0 :
    val = "%04d-%02d" % (
                gdato.dateval[Date._POS_YR], gdato.dateval[Date._POS_MON])
  elif gdato.dateval[Date._POS_YR] > 0 :
    val = "%04d" % ( gdato.dateval[Date._POS_YR] )
  else :
    res = gdato.text
    val=''
  res = res+val
  if gdato.modifier == Date.MOD_AFTER:
    res = res + '/'
  # à faire : range ?  estimate ? calculate ?
  
  return res

class PersonFS(Gramplet):
  """
  Gramplet to display ancestors of the active person.
  """
  def init(self):
    self.fs_id = CONFIG.get("preferences.fs_id")
    self.fs_pasvorto = CONFIG.get("preferences.fs_pasvorto")

    self.gui.WIDGET = self.krei_gui()
    self.gui.get_container_widget().remove(self.gui.textview)
    self.gui.get_container_widget().add_with_viewport(self.gui.WIDGET)
    self.gui.WIDGET.show_all()
    if self.fs_id == '' or self.fs_pasvorto == '':
      self.pref_clicked(None)
    else:
      self.konekti_FS()

  def konekti_FS(self):
    self.fs = Session(self.fs_id, self.fs_pasvorto, False, False, 2)
    if not self.fs.logged:
      return
    self.tree = Tree(self.fs)

  def krei_gui(self):
    """
    krei GUI interfaco.
    """
    self.top = Gtk.Builder()
    base = os.path.dirname(__file__)
    glade_file = base + os.sep + "PersonFS.glade"
    self.top.add_from_file(glade_file)

    self.res = self.top.get_object("PersonFSRes")
    self.propKomp = self.top.get_object("propKomp")
    titles = [  
                (_('Coloro'), 1, 10,COLOR),
		( _('Propreco'), 2, 100),
                (_('Gramps Valoro'), 3, 200),
                (_('FS Valoro'), 4, 200),
             ]
    self.modelKomp = ListModel(self.propKomp, titles)
    self.top.connect_signals({
            "on_pref_clicked"      : self.pref_clicked,
	})

    return self.res

  def pref_clicked(self, dummy):
    print ("clicked")
    top = self.top.get_object("PersonFSPrefDialogo")
    top.set_transient_for(self.uistate.window)
    parent_modal = self.uistate.window.get_modal()
    if parent_modal:
      self.uistate.window.set_modal(False)
    fsid = self.top.get_object("fsid_eniro")
    fsid.set_text(self.fs_id)
    fspv = self.top.get_object("fspv_eniro")
    fspv.set_text(self.fs_pasvorto)
    top.show()
    res = top.run()
    print ("res = " + str(res))
    top.hide()
    if res == -3:
      self.fs_id = fsid.get_text()
      self.fs_pasvorto = fspv.get_text()
      CONFIG.set("preferences.fs_id", self.fs_id)
      CONFIG.set("preferences.fs_pasvorto", self.fs_pasvorto)
      CONFIG.save()
      self.konekti_FS()
    

  def get_has_data(self, active_handle):
    """
    " Return True if the gramplet has data, else return False.
    """
    if active_handle:
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
    self.modelKomp.clear()
    if active_handle:
      self.compareFs(active_handle)
      self.set_has_data(self.get_has_data(active_handle))
    else:
      self.set_has_data(False)

  def get_grevent(self, person, event_type):
    """
    Liveras la unuan eventon de la donita tipo.
    """
    for event_ref in person.get_event_ref_list():
      if int(event_ref.get_role()) == EventRoleType.PRIMARY:
        event = self.dbstate.db.get_event_from_handle(event_ref.ref)
        if event.get_type() == event_type:
          return event
    return None

  def get_fsfact(self, person, fact_tipo):
    """
    Liveras la unuan fakton de la donita tipo.
    """
    for fact in person.facts :
      if fact.type == fact_tipo :
        return fact
    return None

  def compareFs(self, person_handle):
    """
    Kompari gramps kaj FamilySearch
    """

    person = self.dbstate.db.get_person_from_handle(person_handle)
    fsid = 'xxxx-xxx'
    for attr in person.get_attribute_list():
      if attr.get_type() == '_FSFTID':
        fsid = attr.get_value()
    self.top.get_object("LinkoButono").set_label(fsid)
    if fsid == '':
      lien = 'https://familysearch.org/'
    else :
      lien = 'https://familysearch.org/tree/person/' + fsid
    self.top.get_object("LinkoButono").set_uri(lien)
    
    if fsid == '':
      return

    if not self.fs.logged:
      return

    self.tree.add_indis([fsid])

    fsPerso = self.tree.indi[fsid]

    grName = person.primary_name
    fsName = fsPerso.name
    coloro = "orange"
    if (grName.get_primary_surname().surname == fsName.surname) and (grName.first_name == fsName.given) :
      coloro = "green"
    self.modelKomp.add( ( coloro , _('Nomo:')
		, grName.get_primary_surname().surname + ', ' + grName.first_name 
		, fsName.surname +  ', ' + fsName.given
		) )

    if person.get_gender() == Person.MALE :
      grSekso = _("male")
    elif person.get_gender() == Person.FEMALE :
      grSekso = _("female")
    else :
      grSekso = _("unknown")
    if fsPerso.gender == "M" :
      fsSekso = _("male")
    elif fsPerso.gender == "F" :
      fsSekso = _("female")
    else :
      fsSekso = _("unknown")
    coloro = "orange"
    if (grSekso == fsSekso) :
      coloro = "green"
    self.modelKomp.add( ( coloro , _('Sekso:')
		, grSekso
		, fsSekso
		) )

    self.addFactKomp( person, fsPerso, EventType.BIRTH , "http://gedcomx.org/Birth")
    self.addFactKomp( person, fsPerso, EventType.BAPTISM , "http://gedcomx.org/Baptism")
    self.addFactKomp( person, fsPerso, EventType.DEATH , "http://gedcomx.org/Death")
    self.addFactKomp( person, fsPerso, EventType.BURIAL , "http://gedcomx.org/Burial")

    family_handle = person.get_main_parents_family_handle()
    if family_handle:
      family = self.dbstate.db.get_family_from_handle(family_handle)
      handle = family.get_father_handle()
      if handle:
        father = self.dbstate.db.get_person_from_handle(handle)
        father_name = name_displayer.display(father)
      else:
        father_name = ''
      handle = family.get_mother_handle()
      if handle:
        mother = self.dbstate.db.get_person_from_handle(handle)
        mother_name = name_displayer.display(mother)
      else:
        mother_name = ''
    else:
      father_name = ''
      mother_name = ''

    if len(fsPerso.parents) > 0 :
      fs_parents = next(iter(fsPerso.parents))
      fsfather_id = fs_parents[0] 
      fsmother_id = fs_parents[1] 
      self.tree.add_indis([fsfather_id,fsmother_id])
      fsFather = self.tree.indi[fsfather_id]
      fs_father_name = fsFather.name.surname + ', ' + fsFather.name.given
      fsMother = self.tree.indi[fsmother_id]
      fs_mother_name = fsMother.name.surname + ', ' + fsMother.name.given
    else :
      fsfather_id = ''
      fsmother_id = ''
      fs_father_name = ''
      fs_mother_name = ''

    coloro = "orange"
    if (father_name == fs_father_name) :
      coloro = "green"
    self.modelKomp.add( ( coloro , _('Father')
		, father_name
		, fs_father_name
		) )
    coloro = "orange"
    if (mother_name == fs_mother_name) :
      coloro = "green"
    self.modelKomp.add( ( coloro , _('Mother')
		, mother_name
		, fs_mother_name
		) )


    return

  def addFactKomp(self, person, fsPerso, grEvent , fsFact ) :
    grNasko = self.get_grevent(person, EventType(grEvent))
    titolo = str(EventType(grEvent))
    if grNasko != None :
      grNaskoDato = grdato_al_formal(grNasko.date)
      if grNasko.place and grNasko.place != None :
        place = self.dbstate.db.get_place_from_handle(grNasko.place)
        grNaskoLoko = place.name.value
      else :
        grNaskoLoko = ''
    else :
      grNaskoDato = ''
      grNaskoLoko = ''

    fsNasko = self.get_fsfact (fsPerso, fsFact )
    fsNaskoDato = ''
    fsNaskoLoko = ''
    if fsNasko != None :
      if fsNasko.date :
        fsNaskoDato = fsNasko.date
      if fsNasko.place :
        fsNaskoLoko = fsNasko.place
    coloro = "orange"
    if (grNaskoDato == fsNaskoDato) :
      coloro = "green"
    if grNaskoDato == '' and grNaskoLoko == '' and fsNaskoDato == '' and fsNaskoLoko == '' :
      return
    self.modelKomp.add( ( coloro , titolo
		, grNaskoDato +' ; ' + grNaskoLoko
		, fsNaskoDato +' ; ' + fsNaskoLoko
		) )

    return
