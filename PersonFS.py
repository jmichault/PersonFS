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

import json
import email.utils

#-------------------------------------------------------------------------
#
# GTK modules
#
#-------------------------------------------------------------------------
from gi.repository import Gtk, Gdk

#------------------------------------------------------------------------
#
# Gramps modules
#
#------------------------------------------------------------------------
from gramps.gen.db import DbTxn
from gramps.gen.config import config
from gramps.gen.const import GRAMPS_LOCALE as glocale
from gramps.gen.datehandler import get_date
from gramps.gen.display.name import displayer as name_displayer
from gramps.gen.display.place import displayer as _pd
from gramps.gen.errors import WindowActiveError
from gramps.gen.lib import Date, EventRef, EventType, EventRoleType, Name, NameType, Person, StyledText, StyledTextTag, StyledTextTagType, Tag
from gramps.gen.plug import Gramplet, PluginRegister
from gramps.gen.utils.db import get_birth_or_fallback, get_death_or_fallback

from gramps.gui.dialog import OptionDialog, OkDialog
from gramps.gui.editors import EditPerson, EditEvent
from gramps.gui.listmodel import ListModel, NOSORT, COLOR, TOGGLE
from gramps.gui.viewmanager import run_plugin
from gramps.gui.widgets.buttons import IconButton
from gramps.gui.widgets.styledtexteditor import StyledTextEditor

# gedcomx biblioteko. Instalu kun `pip install gedcomx-v1`
import importlib
gedcomx_spec = importlib.util.find_spec("gedcomx")
if gedcomx_spec and gedcomx_spec.loader:
  import gedcomx
else:
  print ('gedcomx ne trovita')
  import pip
  pip.main(['install', '--user', 'gedcomx-v1'])
  import gedcomx

# lokaloj importadoj
from constants import GRAMPS_GEDCOMX_FAKTOJ
import fs_db
import komparo
import tree
import utila
import Importo
from utila import getfsid, get_grevent, get_fsfact, grdato_al_formal

import sys
import os
import time

try:
    _trans = glocale.get_addon_translator(__file__)
except ValueError:
    _trans = glocale.translation
_ = _trans.gettext

#from objbrowser import browse ;browse(locals())

#-------------------------------------------------------------------------
#
# configuration
#
#-------------------------------------------------------------------------

GRAMPLET_CONFIG_NAME = "PersonFS"
CONFIG = config.register_manager(GRAMPLET_CONFIG_NAME)
# salutnomo kaj pasvorto por FamilySearch
CONFIG.register("preferences.fs_sn", '')
CONFIG.register("preferences.fs_pasvorto", '') #
CONFIG.load()


class PersonFS(Gramplet):
  """
  " Interfaco kun familySearch
  """
  fs_sn = CONFIG.get("preferences.fs_sn")
  fs_pasvorto = ''
  fs_pasvorto = CONFIG.get("preferences.fs_pasvorto") #
  fs_Tree = None
  fs_TreeSercxo = None
  Sercxi = None
  Dup = None
  lingvo = None
  FSID = None
  try:
      lingvo = config.get('preferences.place-lang')
  except AttributeError:
      fmt = config.get('preferences.place-format')
      pf = _pd.get_formats()[fmt]
      lingvo = pf.language
  if len(lingvo) != 2:
      lingvo = 'fr'

  def aki_sesio():
    if not tree._FsSeanco:
      if PersonFS.fs_sn == '' or PersonFS.fs_pasvorto == '':
        import locale, os
        gtk = Gtk.Builder()
        gtk.set_translation_domain("addon")
        base = os.path.dirname(__file__)
        locale.bindtextdomain("addon", base + "/locale")
        glade_file = base + os.sep + "PersonFS.glade"
        gtk.add_from_file(glade_file)
        top = gtk.get_object("PersonFSPrefDialogo")
        top.set_transient_for(self.uistate.window)
        parent_modal = self.uistate.window.get_modal()
        if parent_modal:
          self.uistate.window.set_modal(False)
        fsid = gtk.get_object("fsid_eniro")
        fsid.set_text(PersonFS.fs_sn)
        fspv = gtk.get_object("fspv_eniro")
        fspv.set_text(PersonFS.fs_pasvorto)
        top.show()
        res = top.run()
        print ("res = " + str(res))
        top.hide()
        if res == -3:
          PersonFS.fs_sn = fsid.get_text()
          PersonFS.fs_pasvorto = fspv.get_text()
          CONFIG.set("preferences.fs_sn", PersonFS.fs_sn)
          #CONFIG.set("preferences.fs_pasvorto", PersonFS.fs_pasvorto) #
          CONFIG.save()
          #if self.vorteco >= 3:
          tree._FsSeanco = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, True, False, 2)
          #else :
          #tree._FsSeanco = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, False, False, 2)
        else :
          print("Vi devas enigi la ID kaj pasvorton")
      else:
        #if self.vorteco >= 3:
        tree._FsSeanco = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, True, False, 2)
        #else :
        #tree._FsSeanco = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, False, False, 2)
    return tree._FsSeanco


  def init(self):
    """
    " kreas GUI kaj konektas al FamilySearch
    """
    # FARINDAĴO : uzi PersonFS.lingvo

    self.gui.WIDGET = self.krei_gui()
    self.gui.get_container_widget().remove(self.gui.textview)
    self.gui.get_container_widget().add_with_viewport(self.gui.WIDGET)
    self.gui.WIDGET.show_all()

    if PersonFS.fs_sn == '' or PersonFS.fs_pasvorto == '':
      self.pref_clicked(None)
    else:
      self.konekti_FS()

  def konekti_FS(self):
    if not tree._FsSeanco:
      print("konektas al FS")
      #tree._FsSeanco = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, True, False, 2)
      tree._FsSeanco = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, False, False, 2)
    if not tree._FsSeanco.logged :
      return
    if not PersonFS.fs_Tree:
      PersonFS.fs_Tree = tree.Tree()
      PersonFS.fs_Tree._getsources = False

  def l_duobla_klako(self, treeview):
    (model, iter_) = treeview.get_selection().get_selected()
    if not iter_:
      return
    tipo=model.get_value(iter_, 7)
    handle = model.get_value(iter_, 8)
    if ( handle
         and ( tipo == 'infano' or tipo == 'patro'
            or tipo == 'patrino' or tipo == 'edzo')) :
      self.uistate.set_active(handle, 'Person')
    elif ( handle
         and (tipo == 'fakto' or tipo == 'edzoFakto')) :
      event = self.dbstate.db.get_event_from_handle(handle)
      try:
        EditEvent(self.dbstate, self.uistate, [], event)
      except WindowActiveError:
        pass



  def kopii_al_FS(self, treeview):
    print("kopii_al_FS")
    model = self.modelKomp.model
    active_handle = self.get_active('Person')
    grPersono = self.dbstate.db.get_person_from_handle(active_handle)
    iter_ = model.get_iter_first()
    fsT = gedcomx.Gedcomx()
    fsP = gedcomx.Person()
    while iter_ is not None:
      if model.get_value(iter_, 6) : 
        tipolinio = model.get_value(iter_, 7)
        if ( (tipolinio == 'fakto' or tipolinio == 'edzoFakto')
             and model.get_value(iter_, 8) ) :
          grHandle = model.get_value(iter_, 8)
          event = self.dbstate.db.get_event_from_handle(grHandle)
          titolo = str(EventType(event.type))
          grFaktoPriskribo = event.description or ''
          grFaktoDato = grdato_al_formal(event.date)
          if event.place and event.place != None :
            place = self.dbstate.db.get_place_from_handle(event.place)
            grFaktoLoko = _pd.display(self.dbstate.db,place)
          else :
            grFaktoLoko = ''
          # FARINDAĴO : norma loknomo
          if grFaktoLoko == '' :
            grValoro = grFaktoPriskribo
          else :
            grValoro = grFaktoPriskribo +' @ '+ grFaktoLoko
          fsFakto = gedcomx.Fact()
          grTag = int(event.type)
          if grTag:
            tipo = GRAMPS_GEDCOMX_FAKTOJ.get(grTag) or str(event.type)
          else :
            tipo = str(event.type)
          if tipo[:6] == 'http:/' or tipo[:6] == 'data:,' :
            fsFakto.type = tipo
          else :
            fsFakto.type = 'data:,'+tipo
          fsFakto.value = grFaktoPriskribo
          if grFaktoDato :
            fsFakto.date = gedcomx.Date()
            fsFakto.date.original = str (event.date)
            fsFakto.date.formal = gedcomx.DateFormal(grFaktoDato)
          if grFaktoLoko :
            fsFakto.place = gedcomx.PlaceReference()
            fsFakto.place.original = grFaktoLoko
          if tipolinio == 'fakto' :
            fsT.persons.add(fsP)
            fsP.facts.add(fsFakto)
          elif tipolinio == 'edzoFakto' :
            grFamilyHandle = model.get_value(iter_, 10)
            RSfsid = model.get_value(iter_, 11)
            grFamily = self.dbstate.db.get_family_from_handle(grFamilyHandle)
            fsRS = gedcomx.Relationship()
            fsRS.id = RSfsid
            fsRS.facts.add(fsFakto)
            fsT.relationships.add(fsRS)
        elif ( (tipolinio == 'nomo' )
             and model.get_value(iter_, 8) ) :
          grNomo = grPersono.primary_name
          strNomo = model.get_value(iter_, 8)
          if strNomo != str(grNomo) :
            for grNomo in grPersono.alternate_names :
              if strNomo == str(grNomo) : break
          fsNomoId = model.get_value(iter_, 9)
          fsNomo = gedcomx.Name()
          fsNomo.preferred = True
          if fsNomoId :
            fsNomo.id = fsNomoId
          if grNomo.type == NameType(NameType.MARRIED) :
            fsNomo.type = 'http://gedcomx.org/MarriedName'
          elif grNomo.type ==  NameType(NameType.AKA) :
            fsNomo.type = 'http://gedcomx.org/AlsoKnownAs'
          elif grNomo.type == NameType(NameType.BIRTH) :
             fsNomo.type = 'http://gedcomx.org/BirthName'
          else : 
            fsNomo.type = "http://gedcomx.org/BirthName"
          fsNF = gedcomx.NameForm()
          fsNP = gedcomx.NamePart()
          fsNP.type = "http://gedcomx.org/Surname"
          fsNP.value = grNomo.get_primary_surname().surname
          fsNF.parts.add (fsNP)
          fsNP = gedcomx.NamePart()
          fsNP.type = "http://gedcomx.org/Given"
          fsNP.value = grNomo.first_name
          fsNF.parts.add (fsNP)
          fsNomo.nameForms.add(fsNF)
          fsP.names.add(fsNomo)
          fsP.id = self.FSID
          fsT.persons.add(fsP)
          # grNomo.get_primary_surname().surname grNomo.first_name 
      # FARINDAĴO : edzoj, gepatroj, infanoj,…
      iter_ =  model.iter_next(iter_)
    #peto = {'persons' : [gedcomx.jsonigi(fsP)]}
    peto = gedcomx.jsonigi(fsT)
    jsonpeto = json.dumps(peto)
    if tipolinio == 'edzoFakto' :
      res = tree._FsSeanco.post_url( "/platform/tree/couple-relationships/"+RSfsid, jsonpeto )
    else :
      res = tree._FsSeanco.post_url( "/platform/tree/persons/"+self.FSID, jsonpeto )
    if res.status_code == 201 or res.status_code == 204:
      print("ĝisdatigo sukceso")
      self.ButRefresxigi_clicked(None)
    if res.status_code != 201 and res.status_code != 204 :
      print("ĝisdatigo rezulto :")
      print(" jsonpeto = "+jsonpeto)
      print(" res.status_code="+str(res.status_code))
      print (res.headers)
      print (res.text)
    
  def kopii_al_gramps(self, treeview):
    print("kopii_al_gramps")
    model = self.modelKomp.model
    iter_ = model.get_iter_first()
    active_handle = self.get_active('Person')
    grPersono = self.dbstate.db.get_person_from_handle(active_handle)
    fsPersono = gedcomx.Person._indekso.get(self.FSID) 
    with DbTxn(_("copy al gramps"), self.dbstate.db) as txn:
      while iter_ is not None:
        if model.get_value(iter_, 6) : 
          # FARINDAĴO : aliaj tipoj
          tipolinio = model.get_value(iter_, 7)
          if ( (tipolinio == 'fakto' )
             and model.get_value(iter_, 9) ) :
            fsFakto_id = model.get_value(iter_, 9)
            grFaktoH = model.get_value(iter_, 8)
            if fsPersono.facts:
              for fsFakto in fsPersono.facts :
                if fsFakto.id == fsFakto_id : break
              if fsFakto.id == fsFakto_id :
                print("importas fakto "+fsFakto_id)
                if grFaktoH :
                  event = self.dbstate.db.get_event_from_handle(grFaktoH)
                  Importo.updFakto(self.dbstate.db,txn,fsFakto,event)
                else :
                  event = Importo.aldFakto(self.dbstate.db,txn,fsFakto,grPersono)
                found = False
                for er in grPersono.get_event_ref_list():
                  if er.ref == event.handle:
                    found = True
                    break
                if not found:
                  er = EventRef()
                  er.set_role(EventRoleType.PRIMARY)
                  er.set_reference_handle(event.get_handle())
                  self.dbstate.db.commit_event(event, txn)
                  grPersono.add_event_ref(er)
                if event.type == EventType.BIRTH :
                  grPersono.set_birth_ref(er)
                elif event.type == EventType.DEATH :
                  grPersono.set_death_ref(er)
          elif ( (tipolinio == 'edzoFakto')
             and model.get_value(iter_, 9) 
             and model.get_value(iter_, 10) ) :
            grFaktoH = model.get_value(iter_, 8)
            fsFakto_id = model.get_value(iter_, 9)
            grParoH = model.get_value(iter_, 10)
            fsParo_id = model.get_value(iter_, 11)
            grParo = self.dbstate.db.get_family_from_handle(grParoH)
            fsParo = gedcomx.Relationship._indekso[fsParo_id]
            for fsFakto in fsParo.facts :
              if fsFakto.id == fsFakto_id : break
            event = Importo.aldFakto(self.dbstate.db, txn, fsFakto, grParo)
            found = False
            for er in grParo.get_event_ref_list():
              if er.ref == event.handle:
                found = True
                break
            if not found:
              er = EventRef()
              er.set_role(EventRoleType.FAMILY)
              er.set_reference_handle(event.get_handle())
              self.dbstate.db.commit_event(event, txn)
              grParo.add_event_ref(er)
      
            self.dbstate.db.commit_family(grParo,txn)


        iter_ =  model.iter_next(iter_)
      self.dbstate.db.commit_person(grPersono,txn)
      self.dbstate.db.transaction_commit(txn)
    self.ButRefresxigi_clicked(None)

  def l_dekstra_klako(self, treeview, event):
    menu = Gtk.Menu()
    menu.set_reserve_toggle_size(False)
    item  = Gtk.MenuItem(label=_('Kopii elekton de gramps al FS'))
    item.set_sensitive(1)
    item.connect("activate",lambda obj: self.kopii_al_FS(treeview))
    item.show()
    menu.append(item)
    item  = Gtk.MenuItem(label=_('Kopii elekton de FS al gramps'))
    item.set_sensitive(1)
    item.connect("activate",lambda obj: self.kopii_al_gramps(treeview))
    item.show()
    menu.append(item)
    self.menu = menu
    self.menu.popup(None, None, None, None, event.button, event.time)


  def krei_gui(self):
    """
    " kreas GUI interfacon.
    """
    import locale, os
    self.top = Gtk.Builder()
    self.top.set_translation_domain("addon")
    base = os.path.dirname(__file__)
    locale.bindtextdomain("addon", base + "/locale")
    glade_file = base + os.sep + "PersonFS.glade"
    self.top.add_from_file(glade_file)

    self.res = self.top.get_object("PersonFSTop")
    self.propKomp = self.top.get_object("propKomp")
    titles = [  
                (_('Koloro'), 1, 20,COLOR),
		( _('Propreco'), 2, 100),
		( _('Dato'), 3, 120),
                (_('Gramps Valoro'), 4, 300),
                (_('FS Dato'), 5, 120),
                (_('FS Valoro'), 6, 300),
                ('x', 7, 20, TOGGLE,True,self.toggled),
                (_('xTipo'), NOSORT, 0),
                (_('xGr'), NOSORT, 0),
                (_('xFs'), NOSORT, 0),
                (_('xGr2'), NOSORT, 0),
                (_('xFs2'), NOSORT, 0),
             ]
    self.modelKomp = ListModel(self.propKomp, titles
                 ,event_func=self.l_duobla_klako
                 ,right_click=self.l_dekstra_klako)
    self.top.connect_signals({
            "on_pref_clicked"      : self.pref_clicked,
            "on_ButEdzoj_clicked"      : self.ButEdzoj_clicked,
            "on_ButSercxi_clicked"      : self.ButSercxi_clicked,
            "on_ButDup_clicked"      : self.ButDup_clicked,
            "on_ButLancxi_clicked"      : self.ButLancxi_clicked,
            "on_ButAldoni_clicked"      : self.ButAldoni_clicked,
            "on_ButLigi_clicked"      : self.ButLigi_clicked,
            "on_ButRefresxigi_clicked"      : self.ButRefresxigi_clicked,
            "on_ButImporti_clicked"      : self.ButImporti_clicked,
            "on_ButBaskKonf_toggled"      : self.ButBaskKonf_toggled,
	})

    return self.res

  def toggled(self, path, val):
    row = self.modelKomp.model.get_iter((path,))
    tipo=self.modelKomp.model.get_value(row, 7)
    #if tipo != 'fakto' and tipo != 'edzoFakto' :
    if tipo != 'fakto' and tipo != 'edzoFakto' and tipo != 'nomo' :
      self.modelKomp.model.set_value(row, 6, False)
      OkDialog(_('Pardonu, nur eventaj linioj povas esti elektitaj.'))
      print("  toggled:tipo="+tipo)


  def ButBaskKonf_toggled(self, dummy):
   with DbTxn(_("FamilySearch tags"), self.dbstate.db) as txn:
    val = self.top.get_object("ButBaskKonf").get_active()
    tag_fs = self.dbstate.db.get_tag_from_name('FS_Konf')
    active_handle = self.get_active('Person')
    grPersono = self.dbstate.db.get_person_from_handle(active_handle)
    if not val and tag_fs.handle in grPersono.tag_list:
      grPersono.remove_tag(tag_fs.handle)
    if tag_fs and val and tag_fs.handle not in grPersono.tag_list:
      grPersono.add_tag(tag_fs.handle)
      dbPersono= fs_db.db_stato(self.dbstate.db,grPersono.handle)
      dbPersono.get()
      dbPersono.konf = val
      dbPersono.commit(txn)
    self.dbstate.db.commit_person(grPersono, txn, grPersono.change)
    self.dbstate.db.transaction_commit(txn)

  def ButRefresxigi_clicked(self, dummy):
    if self.FSID :
      fsPersono = gedcomx.Person._indekso.get(self.FSID)
      if fsPersono:
        for paro in fsPersono._paroj :
          paro.person1=None
          paro.person2=None
          paro.facts=set()
        fsPersono.facts=set()
        fsPersono.names=set()
        fsPersono._gepatroj =set()
        fsPersono._infanoj=set()
        fsPersono._paroj=set()
        fsPersono._infanojCP = set()
        fsPersono._gepatrojCP=set()
        fsPersono.sortKey = None
      PersonFS.fs_Tree._persons.pop(self.FSID)
      PersonFS.fs_Tree.add_persons([self.FSID])
    #rezulto = gedcomx.jsonigi(PersonFS.fs_Tree)
    #f = open('arbo2.out.json','w')
    #json.dump(rezulto,f,indent=2)
    #f.close()

    active_handle = self.get_active('Person')
    self.modelKomp.cid=None
    self.modelKomp.model.set_sort_column_id(-2,0)
    self.modelKomp.clear()
    if active_handle:
      self.kompariFs(active_handle,True)
      self.set_has_data(self.get_has_data(active_handle))
    else:
      self.set_has_data(False)
    return

  def ButImporti_clicked(self, dummy):
    gpr = PluginRegister.get_instance()
    plg = gpr.get_plugin('Importo de FamilySearch')
    run_plugin(plg,self.dbstate,self.uistate)
    return

  def ButAldoni_clicked(self, dummy):
    active_handle = self.get_active('Person')
    person = self.dbstate.db.get_person_from_handle(active_handle)
    fsPerso = gedcomx.Person()
    fsPerso.gender = gedcomx.Gender()
    fsPerso.living = False
    if person.get_gender() == Person.MALE :
      fsPerso.gender.type = "http://gedcomx.org/Male"
    elif person.get_gender() == Person.FEMALE :
      fsPerso.gender.type = "http://gedcomx.org/Female"
    else:
      fsPerso.gender.type = "http://gedcomx.org/Unknown"
    grNomo = person.primary_name
    nomo = gedcomx.Name()
    nomo.surname = None
    if grNomo.type == 3 :
      nomo.type = 'http://gedcomx.org/MarriedName'
    elif grNomo.type == 1 :
      nomo.type = 'http://gedcomx.org/AlsoKnownAs'
    else :
      nomo.type = 'http://gedcomx.org/BirthName'
    nf = gedcomx.NameForm()
    nomo.nameForms = set()
    nomo.nameForms.add(nf)
    nf.parts = set()
    np1=gedcomx.NamePart()
    np1.type = "http://gedcomx.org/Given"
    np1.value = grNomo.first_name
    nf.parts.add(np1)
    np2=gedcomx.NamePart()
    np2.type = "http://gedcomx.org/Surname"
    np2.value = grNomo.get_primary_surname().surname
    nf.parts.add(np2)
    nomo.preferred = True
    fsPerso.names.add(nomo)
    # FARINDAĴO : aliaj nomoj
    #grFaktoj = person.event_ref_list
    #for grFakto in grFaktoj :
    #  if int(grFakto.get_role()) != EventRoleType.PRIMARY:
    #    continue
    #  event = self.dbstate.db.get_event_from_handle(grFakto.ref)
    #  titolo = str(EventType(event.type))
    #  grFaktoPriskribo = event.description or ''
    #  grFaktoDato = grdato_al_formal(event.date)
    #  if event.place and event.place != None :
    #    place = self.dbstate.db.get_place_from_handle(event.place)
    #    grFaktoLoko = place.name.value
    #  else :
    #    grFaktoLoko = ''
    #  # FARINDAĴO : norma loknomo
    #  if grFaktoLoko == '' :
    #    grValoro = grFaktoPriskribo
    #  else :
    #    grValoro = grFaktoPriskribo +' @ '+ grFaktoLoko
    #  grTag = PERSONALCONSTANTEVENTS.get(int(event.type), "").strip() or event.type
    #  fsFakto = gedcomx.Fact()
    #  fsFakto.date = gedcomx.Date()
    #  fsFakto.date.original = grFaktoDato
    #  fsFakto.type = GRAMPS_GEDCOMX_FAKTOJ.get(grTag)
    #  fsFakto.place = grFaktoLoko
    #  fsFakto.value = grFaktoPriskribo
    #  fsPerso.facts.add(fsFakto)
    # FARINDAĴOJ : fontoj, …
    peto = {'persons' : [gedcomx.jsonigi(fsPerso)]}
    jsonpeto = json.dumps(peto)
    res = tree._FsSeanco.post_url( "/platform/tree/persons", jsonpeto )
    if res.status_code==201 and res.headers and "X-Entity-Id" in res.headers :
      fsid = res.headers['X-Entity-Id']
      utila.ligi_gr_fs(self.dbstate.db, person, fsid)
      self.FSID = fsid
      self.ButRefresxigi_clicked(None)
    else :
      print (res.headers)
    #  FARINDAĴO 
    return

  def ButLigi_clicked(self, dummy):
    model, iter_ = self.top.get_object("PersonFSResRes").get_selection().get_selected()
    if iter_ :
      fsid = model.get_value(iter_, 1)
      #print(fsid)
      active_handle = self.get_active('Person')
      grPersono = self.dbstate.db.get_person_from_handle(active_handle)
      utila.ligi_gr_fs(self.dbstate.db, grPersono, fsid)
      self.ButRefresxigi_clicked(None)
      self.Sercxi.hide()
    return

  def SerSelCxangxo(self, dummy):
    model, iter_ = self.top.get_object("PersonFSResRes").get_selection().get_selected()
    if iter_ :
      fsid = model.get_value(iter_, 1)
      #print(fsid)
      self.top.get_object("LinkoButonoSercxi").set_label(fsid)
      lien = 'https://familysearch.org/tree/person/' + fsid
      self.top.get_object("LinkoButonoSercxi").set_uri(lien)
    else :
      self.top.get_object("LinkoButonoSercxi").set_label('xxxx-xxx')
      self.top.get_object("LinkoButonoSercxi").set_uri('https://familysearch.org/')

  def SerDupCxangxo(self, dummy):
    model, iter_ = self.top.get_object("PersonFSDupRes").get_selection().get_selected()
    if iter_ :
      fsid = model.get_value(iter_, 1)
      #print(fsid)
      self.top.get_object("LinkoButonoDup").set_label(fsid)
      lien = 'https://familysearch.org/tree/person/' + fsid
      self.top.get_object("LinkoButonoDup").set_uri(lien)
      self.top.get_object("LinkoButonoKunfando").set_label(self.FSID+'+'+fsid)
      lien = 'https://familysearch.org/tree/person/merge/verify/' +self.FSID+'/'  + fsid
      self.top.get_object("LinkoButonoKunfando").set_uri(lien)
    else :
      self.top.get_object("LinkoButonoDup").set_label('xxxx-xxx')
      self.top.get_object("LinkoButonoDup").set_uri('https://familysearch.org/')
      self.top.get_object("LinkoButonoKunfando").set_label('………')
      self.top.get_object("LinkoButonoKunfando").set_uri('https://familysearch.org/')
    return

  def ButDup_clicked(self, dummy):
    if not self.Dup :
      self.Dup = self.top.get_object("PersonFSDup")
      self.Dup.set_transient_for(self.uistate.window)
      parent_modal = self.uistate.window.get_modal()
      if parent_modal:
        self.uistate.window.set_modal(False)
      TreeRes = self.top.get_object("PersonFSDupRes")
      titles = [  
                (_('score'), 1, 80),
                (_('FS Id'), 2, 90),
                (_('Nomo, antaŭnomo'), 3, 200),
                (_('Birth'), 4, 250),
                (_('Death'), 5, 250),
                (_('Parents'), 6, 250),
                (_('Spouses'), 7, 250),
             ]
      self.modelRes = ListModel(TreeRes, titles,self.SerDupCxangxo)
    active_handle = self.get_active('Person')
    person = self.dbstate.db.get_person_from_handle(active_handle)
    grNomo = person.primary_name

    if not PersonFS.fs_TreeSercxo:
      PersonFS.fs_TreeSercxo = tree.Tree()
      PersonFS.fs_TreeSercxo._getsources = False
    self.modelRes.cid=None
    self.modelRes.model.set_sort_column_id(-2,0)
    self.modelRes.clear()
    mendo = "/platform/tree/persons/"+self.FSID+"/matches"
    r = tree._FsSeanco.get_url(
                    mendo ,{"Accept": "application/x-gedcomx-atom+json", "Accept-Language": "fr"}
                )
    if r.status_code == 200 :
      self.DatRes(r.json())
      self.Dup.show()
      res = self.Dup.run()
      print ("res = " + str(res))
      self.Dup.hide()
    elif r.status_code == 204 :
      OkDialog(_('Neniuj verŝajnaj duplikatoj por la persono %s trovita de la retejo "FamilySearch".')% self.FSID)
    return

  def ButSercxi_clicked(self, dummy):
    if not self.Sercxi :
      self.Sercxi = self.top.get_object("PersonFSRes")
      self.Sercxi.set_transient_for(self.uistate.window)
      parent_modal = self.uistate.window.get_modal()
      if parent_modal:
        self.uistate.window.set_modal(False)
      TreeRes = self.top.get_object("PersonFSResRes")
      titles = [  
                (_('score'), 1, 80),
                (_('FS Id'), 2, 90),
                (_('Nomo, antaŭnomo'), 3, 200),
                (_('Birth'), 4, 250),
                (_('Death'), 5, 250),
                (_('Parents'), 6, 250),
                (_('Spouses'), 7, 250),
             ]
      self.modelRes = ListModel(TreeRes, titles,self.SerSelCxangxo)
    active_handle = self.get_active('Person')
    person = self.dbstate.db.get_person_from_handle(active_handle)
    grNomo = person.primary_name
    self.top.get_object("fs_nomo_eniro").set_text(person.primary_name.get_primary_surname().surname)
    self.top.get_object("fs_anomo_eniro").set_text(person.primary_name.first_name)
    if person.get_gender() == Person.MALE :
      self.top.get_object("fs_sekso_eniro").set_text('Male')
    elif person.get_gender() == Person.FEMALE :
      self.top.get_object("fs_sekso_eniro").set_text('Female')
    grBirth = get_grevent(self.dbstate.db, person, EventType(EventType.BIRTH))
    if grBirth :
      self.top.get_object("fs_birdo_eniro").set_text( grdato_al_formal(grBirth.date))
    else:
      self.top.get_object("fs_birdo_eniro").set_text( '')
    if grBirth and grBirth.place and grBirth.place != None :
      place = self.dbstate.db.get_place_from_handle(grBirth.place)
      self.top.get_object("fs_loko_eniro").set_text( place.name.value)
    else :
      self.top.get_object("fs_loko_eniro").set_text( '')

    self.ButLancxi_clicked(None)
    self.Sercxi.show()
    res = self.Sercxi.run()
    print ("res = " + str(res))
    self.Sercxi.hide()
    return

  def ButLancxi_clicked(self, dummy):
    if not PersonFS.fs_TreeSercxo:
      PersonFS.fs_TreeSercxo = tree.Tree()
      PersonFS.fs_TreeSercxo._getsources = False
    self.modelRes.cid=None
    self.modelRes.model.set_sort_column_id(-2,0)
    self.modelRes.clear()
    mendo = "/platform/tree/search?"
    grNomo = self.top.get_object("fs_nomo_eniro").get_text()
    if grNomo :
      mendo = mendo + "q.surname=%s&" % grNomo
    grANomo = self.top.get_object("fs_anomo_eniro").get_text()
    if grANomo :
      mendo = mendo + "q.givenName=%s&" % grANomo
    sekso = self.top.get_object("fs_sekso_eniro").get_text()
    if sekso :
      mendo = mendo + "q.sex=%s&" % sekso
    birdo = self.top.get_object("fs_birdo_eniro").get_text()
    if birdo :
      mendo = mendo + "q.birthLikeDate=%s&" % birdo
    loko = self.top.get_object("fs_loko_eniro").get_text()
    if loko :
      mendo = mendo + "q.anyPlace=%s&" % loko
    mendo = mendo + "offset=0&count=10"
    datumoj = tree._FsSeanco.get_jsonurl(
                    mendo ,{"Accept": "application/x-gedcomx-atom+json"}
                )
    if not datumoj :
      return
    #tot = datumoj["results"]
    #print ("nb résultats = "+str(tot))
    self.DatRes(datumoj)
    self.Sercxi.show()

  def DatRes(self,datumoj):
    for entry in datumoj["entries"] :
      #print (entry.get("id")+ ";  score = "+str(entry.get("score")))
      fsId = entry.get("id")
      data=entry["content"]["gedcomx"]
      # bizare, FamilySearch ne uzas gedcomx-formaton
      #gedcomx.maljsonigi(self.fs_TreeSercxo, data )
      if "places" in data:
        for place in data["places"]:
          if place["id"] not in self.fs_TreeSercxo._places:
            self.fs_TreeSercxo._places[place["id"]] = (
                                str(place["latitude"]),
                                str(place["longitude"]),
                            )
      father = None
      fatherId = None
      mother = None
      motherId = None
      if "persons" in data:
        for person in data["persons"]:
          self.fs_TreeSercxo._persons[person["id"]] = gedcomx.Person(person["id"], self.fs_TreeSercxo)
          gedcomx.maljsonigi(self.fs_TreeSercxo._persons[person["id"]],person)
        for person in data["persons"]:
          if "ascendancyNumber" in person["display"] and person["display"]["ascendancyNumber"] == 1 :
            if person["gender"]["type"] == "http://gedcomx.org/Female" :
              motherId=person["id"]
              mother=self.fs_TreeSercxo._persons[person["id"]]
            elif person["gender"]["type"] == "http://gedcomx.org/Male" :
              fatherId=person["id"]
              father=self.fs_TreeSercxo._persons[person["id"]]
      fsPerso = PersonFS.fs_TreeSercxo._persons.get(fsId) or gedcomx.Person()
      edzoj = ''
      if "relationships" in data:
        for rel in data["relationships"]:
          if rel["type"] == "http://gedcomx.org/Couple":
            person1Id = rel["person1"]["resourceId"]
            person2Id = rel["person2"]["resourceId"]
            edzoId = None
            if person2Id==fsId:
              edzoId = person1Id
            elif person1Id==fsId:
              edzoId = person2Id
            if edzoId:
              fsEdzo = PersonFS.fs_TreeSercxo._persons.get(edzoId) or gedcomx.Person()
              fsEdzoNomo = fsEdzo.akPrefNomo()
              if edzoj != '': edzoj = edzoj + "\n"
              edzoj = edzoj + fsEdzoNomo.akSurname() +  ', ' + fsEdzoNomo.akGiven()
          elif rel["type"] == "http://gedcomx.org/ParentChild":
            person1Id = rel["person1"]["resourceId"]
            person2Id = rel["person2"]["resourceId"]
            if person2Id == fsId :
              person1=self.fs_TreeSercxo._persons[person1Id]
              if not father and person1.gender.type == "http://gedcomx.org/Male" :
                father = person1
              elif not mother and person1.gender.type == "http://gedcomx.org/Female" :
                mother = person1
              
      fsNomo = fsPerso.akPrefNomo()
      fsBirth = get_fsfact (fsPerso, 'http://gedcomx.org/Birth' ) or gedcomx.Fact()
      fsBirthLoko = fsBirth.place 
      if fsBirthLoko :
        fsBirth = str(fsBirth.date or '') + ' \n@ ' +fsBirthLoko.original
      else :
        fsBirth = str(fsBirth.date or '')
      fsDeath = get_fsfact (fsPerso, 'http://gedcomx.org/Death' ) or gedcomx.Fact()
      fsDeathLoko = fsDeath.place 
      if fsDeathLoko :
        fsDeath = str(fsDeath.date or '') + ' \n@ ' +fsDeathLoko.original
      else :
        fsDeath = str(fsDeath.date or '')
      if father :
        fsPatroNomo = father.akPrefNomo()
      else:
        fsPatroNomo = gedcomx.Name()
      if mother :
        fsPatrinoNomo = mother.akPrefNomo()
      else:
        fsPatrinoNomo = gedcomx.Name()
      self.modelRes.add( ( 
		  str(entry.get("score"))
		, fsId
		, fsNomo.akSurname() +  ', ' + fsNomo.akGiven()
		, fsBirth
		, fsDeath
                , fsPatroNomo.akSurname() +  ', ' + fsPatroNomo.akGiven()
                   + '\n'+fsPatrinoNomo.akSurname() +  ', ' + fsPatrinoNomo.akGiven()
		, edzoj
		) )
    return

  def ButEdzoj_clicked(self, dummy):
    active_handle = self.get_active('Person')
    self.modelKomp.cid=None
    self.modelKomp.model.set_sort_column_id(-2,0)
    self.modelKomp.clear()
    if active_handle:
      self.kompariFs(active_handle,True)
      self.set_has_data(self.get_has_data(active_handle))
    else:
      self.set_has_data(False)
    return

  def pref_clicked(self, dummy):
    top = self.top.get_object("PersonFSPrefDialogo")
    top.set_transient_for(self.uistate.window)
    parent_modal = self.uistate.window.get_modal()
    if parent_modal:
      self.uistate.window.set_modal(False)
    fssn = self.top.get_object("fssn_eniro")
    fssn.set_text(PersonFS.fs_sn)
    fspv = self.top.get_object("fspv_eniro")
    fspv.set_text(PersonFS.fs_pasvorto)
    top.show()
    res = top.run()
    print ("res = " + str(res))
    top.hide()
    if res == -3:
      PersonFS.fs_sn = fssn.get_text()
      PersonFS.fs_pasvorto = fspv.get_text()
      CONFIG.set("preferences.fs_sn", PersonFS.fs_sn)
      #CONFIG.set("preferences.fs_pasvorto", PersonFS.fs_pasvorto) #
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
    self.modelKomp.cid=None
    self.modelKomp.model.set_sort_column_id(-2,0)
    self.modelKomp.clear()
    if active_handle:
      self.kompariFs(active_handle,False)
      self.set_has_data(self.get_has_data(active_handle))
    else:
      self.set_has_data(False)

  def kompariFs(self, person_handle, getfs):
    """
    " Komparas gramps kaj FamilySearch
    """
    fs_db.create_schema(self.dbstate.db)
    self.FSID = None
    grPersono = self.dbstate.db.get_person_from_handle(person_handle)
    tag_fs = self.dbstate.db.get_tag_from_name('FS_Konf')
    if tag_fs and tag_fs.handle in grPersono.tag_list :
      self.top.get_object("ButBaskKonf").set_active(True)
    else :
      self.top.get_object("ButBaskKonf").set_active(False)
      
    fsid = getfsid(grPersono)
    if fsid == '' :
      fsid = 'xxxx-xxx'
    self.top.get_object("LinkoButono").set_label(fsid)
    if fsid == '':
      lien = 'https://familysearch.org/'
    else :
      lien = 'https://familysearch.org/tree/person/' + fsid
    self.top.get_object("LinkoButono").set_uri(lien)
    # Se fsid ne estas specifita: nenio pli :
    if fsid == '' or fsid == 'xxxx-xxx' :
      return
    self.FSID = fsid

    # Se ĝi ne estas konektita al familysearch: nenio pli.
    if tree._FsSeanco == None or not tree._FsSeanco.logged:
      return
    #
    PersonFS.FSID = fsid
    # ŝarĝante individuan "FamilySearch" :
    PersonFS.fs_Tree.add_persons([fsid])
    #fsPerso = gedcomx.Person._indekso.get(fsid) 
    fsPerso = PersonFS.fs_Tree._persons.get(fsid)
    if not fsPerso :
      mendo = "/platform/tree/persons/"+fsid
      r = tree._FsSeanco.head_url( mendo )
      if r.status_code == 301 and 'X-Entity-Forwarded-Id' in r.headers :
        fsid = r.headers['X-Entity-Forwarded-Id']
        PersonFS.FSID = fsid
        utila.ligi_gr_fs(db, grPersono, fsid)
        mendo = "/platform/tree/persons/"+fsid
        r = tree._FsSeanco.head_url( mendo )
      datemod = int(time.mktime(email.utils.parsedate(r.headers['Last-Modified'])))
      etag = r.headers['Etag']
      PersonFS.fs_Tree.add_persons([fsid])
      fsPerso = gedcomx.Person._indekso.get(fsid) or gedcomx.Person()

    if getfs == True :
      PersonFS.fs_Tree.add_spouses([fsid])
      PersonFS.fs_Tree.add_children([fsid])
    
    kompRet = komparo.kompariFsGr(fsPerso, grPersono, self.dbstate.db, self.modelKomp)
    box1 = self.top.get_object("Box1")
    if ('FS_Esenco' in kompRet) :
      box1.override_background_color(Gtk.StateType.NORMAL, Gdk.RGBA(1.0, 0.0, 0.0, 1.0))
    else:
      box1.override_background_color(Gtk.StateType.NORMAL, Gdk.RGBA(0.0, 1.0, 0.0, 1.0))
    box2 = self.top.get_object("Box2")
    if ('FS_Gepatro' in kompRet) or ('FS_Familio' in kompRet) :
      box2.override_background_color(Gtk.StateType.NORMAL, Gdk.RGBA(1.0, 0.0, 0.0, 1.0))
    else:
      box2.override_background_color(Gtk.StateType.NORMAL, Gdk.RGBA(0.0, 1.0, 0.0, 1.0))
    box3 = self.top.get_object("Box3")
    if ('FS_Fakto' in kompRet) :
      box3.override_background_color(Gtk.StateType.NORMAL, Gdk.RGBA(1.0, 0.0, 0.0, 1.0))
    else:
      box3.override_background_color(Gtk.StateType.NORMAL, Gdk.RGBA(0.0, 1.0, 0.0, 1.0))


    return

  # FARINDAĴOJ : kopii, redundoj, esploro, …
