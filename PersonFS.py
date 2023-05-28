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

from gramps.gui.dialog import OptionDialog, OkDialog , WarningDialog
from gramps.gui.editors import EditPerson, EditEvent
#from gramps.gui.listmodel import ListModel, NOSORT, COLOR, TOGGLE
from mialistmodel import ListModel, NOSORT, COLOR, TOGGLE
from gramps.gui.viewmanager import run_plugin
from gramps.gui.widgets.buttons import IconButton
from gramps.gui.widgets.styledtexteditor import StyledTextEditor

try:
    _trans = glocale.get_addon_translator(__file__)
except ValueError:
    _trans = glocale.translation
_ = _trans.gettext

# gedcomx biblioteko. Instalu kun `pip install gedcomx-v1`
mingedcomx="1.0.13"
import importlib
from importlib.metadata import version
try:
  v = version('gedcomx-v1')
except :
  v="0.0.0"
from packaging.version import parse
if parse(v) < parse(mingedcomx) :
  print (_('gedcomx ne trovita aŭ < %s' % mingedcomx))
  import pip
  pip.main(['install', '--user', '--upgrade', 'gedcomx-v1'])
import gedcomx

# lokaloj importadoj
from constants import GRAMPS_GEDCOMX_FAKTOJ
import fs_db
import komparo
import tree
import utila
import Importo
from utila import get_fsftid, get_grevent, get_fsfact, grdato_al_formal

import sys
import os
import time


#from objbrowser import browse ;browse(locals())
#import pdb; pdb.set_trace()

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
CONFIG.register("preferences.fs_etikedado", '') #
CONFIG.load()


class PersonFS(Gramplet):
  """
  " Interfaco kun familySearch
  """
  fs_sn = CONFIG.get("preferences.fs_sn")
  fs_pasvorto = ''
  fs_pasvorto = CONFIG.get("preferences.fs_pasvorto") #
  # fs_etikedado = True se ne definita
  fs_etikedado = not CONFIG.get("preferences.fs_etikedado") == 'False'
  print("fs_etikedado="+str(fs_etikedado))
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
      lingvo = lingvo[:2]
  if not lingvo :
    lingvo = glocale.language[0]

  def aki_sesio(vokanto):
    if not tree._FsSeanco:
      if PersonFS.fs_sn == '' or PersonFS.fs_pasvorto == '':
        import locale, os
        gtk = Gtk.Builder()
        gtk.set_translation_domain("addon")
        base = os.path.dirname(__file__)
        glade_file = base + os.sep + "PersonFS.glade"
        if os.name == 'win32' or os.name == 'nt' :
          import xml.etree.ElementTree as ET
          xtree = ET.parse(glade_file)
          for node in xtree.iter() :
            if 'translatable' in node.attrib :
              node.text = _(node.text)
          xml_text = ET.tostring(xtree.getroot(),encoding='unicode',method='xml')
          gtk.add_from_string(xml_text)
        else:
          locale.bindtextdomain("addon", base + "/locale")
          gtk.add_from_file(glade_file)

        top = gtk.get_object("PersonFSPrefDialogo")
        top.set_transient_for(vokanto.uistate.window)
        parent_modal = vokanto.uistate.window.get_modal()
        if parent_modal:
          vokanto.uistate.window.set_modal(False)
        xfsid = gtk.get_object("fssn_eniro")
        xfsid.set_text(PersonFS.fs_sn)
        fspv = gtk.get_object("fspv_eniro")
        fspv.set_text(PersonFS.fs_pasvorto)
        fsetik = gtk.get_object("fsetik_eniro")
        fsetik.set_active(PersonFS.fs_etikedado)
        top.show()
        res = top.run()
        top.hide()
        if res == -3:
          PersonFS.fs_sn = xfsid.get_text()
          PersonFS.fs_pasvorto = fspv.get_text()
          PersonFS.fs_etikedado = fsetik.get_active()
          print("PersonFS.fs_etikedado="+str(PersonFS.fs_etikedado))
          CONFIG.set("preferences.fs_sn", PersonFS.fs_sn)
          #CONFIG.set("preferences.fs_pasvorto", PersonFS.fs_pasvorto) #
          CONFIG.set("preferences.fs_etikedado", str(PersonFS.fs_etikedado))
          CONFIG.save()
          #if self.vorteco >= 3:
          tree._FsSeanco = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, True, False, 2, PersonFS.lingvo)
          #else :
          #tree._FsSeanco = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, False, False, 2, PersonFS.lingvo)
        else :
          print("Vi devas enigi la ID kaj pasvorton")
      else:
        #if self.vorteco >= 3:
        tree._FsSeanco = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, True, False, 2, PersonFS.lingvo)
        #else :
        #tree._FsSeanco = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, False, False, 2, PersonFS.lingvo)
      print(" langage session FS = "+tree._FsSeanco.lingvo);
      if tree._FsSeanco.stato == gedcomx.fs_session.STATO_PASVORTA_ERARO :
         WarningDialog(_('Pasvorta erraro. La funkcioj de FamilySearch ne estos disponeblaj.'))
      elif not tree._FsSeanco.logged :
        WarningDialog(_('Malsukcesa konekto. La funkcioj de FamilySearch ne estos disponeblaj.'))

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
      #tree._FsSeanco = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, True, False, 2, PersonFS.lingvo)
      tree._FsSeanco = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, False, False, 2, PersonFS.lingvo)
    if tree._FsSeanco.stato == gedcomx.fs_session.STATO_PASVORTA_ERARO :
      WarningDialog(_('Pasvorta eraro. La funkcioj de FamilySearch ne estos disponeblaj.'))
      return
    elif not tree._FsSeanco.logged :
      WarningDialog(_('Malsukcesa konekto. La funkcioj de FamilySearch ne estos disponeblaj.'))
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
    fsTP = gedcomx.Gedcomx()
    fsTR = gedcomx.Gedcomx()
    fsP = gedcomx.Person()
    for x in model:
     l = [x]
     l.extend(x.iterchildren())
     for linio in l :
      if linio[6] : 
        tipolinio = linio[7]
        if ( (tipolinio == 'fakto' or tipolinio == 'edzoFakto')
             and linio[8] ) :
          grHandle = linio[8]
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
            fsFakto.date.original = event.date.text
            if not fsFakto.date.original or fsFakto.date.original=='' :
              fsFakto.date.original = get_date(event)
            fsFakto.date.formal = gedcomx.DateFormal(grFaktoDato)
            if str(fsFakto.date.formal) == '' :
              fsFakto.date.formal = None
          if grFaktoLoko :
            fsFakto.place = gedcomx.PlaceReference()
            fsFakto.place.original = grFaktoLoko
          if tipolinio == 'fakto' :
            fsTP.persons.add(fsP)
            fsP.facts.add(fsFakto)
          elif tipolinio == 'edzoFakto' :
            fsTR = gedcomx.Gedcomx()
            grFamilyHandle = linio[10]
            RSfsid = linio[11]
            grFamily = self.dbstate.db.get_family_from_handle(grFamilyHandle)
            fsRS = gedcomx.Relationship()
            fsRS.id = RSfsid
            fsRS.facts.add(fsFakto)
            fsTR.relationships.add(fsRS)
            peto = gedcomx.jsonigi(fsTR)
            jsonpeto = json.dumps(peto)
            res = tree._FsSeanco.post_url( "/platform/tree/couple-relationships/"+RSfsid, jsonpeto )
            if res.status_code == 201 or res.status_code == 204:
              print("ĝisdatigo sukceso")
            if res.status_code != 201 and res.status_code != 204 :
              print("ĝisdatigo rezulto :")
              print(" jsonpeto = "+jsonpeto)
              print(" res.status_code="+str(res.status_code))
              print (res.headers)
              print (res.text)
        elif ( (tipolinio == 'nomo' or tipolinio == 'nomo1')
             and linio[8] ) :
          strNomo = linio[8]
          grSurname = linio[10]
          grGiven = linio[11]
          fsNomoId = linio[9]
          if tipolinio == 'nomo1' :
            grNomo = grPersono.primary_name
          else :
            grNomo = None
            for grN in grPersono.alternate_names :
              if strNomo == str(grN) :
                grNomo = grN
                break
            if not grNomo :
              for grNomo in grPersono.alternate_names :
                if (     grNomo.get_primary_surname().surname == grSurname
                     and grNomo.first_name == grGiven) :
                  break
          fsNomo = gedcomx.Name()
          if tipolinio == 'nomo1':
            fsNomo.preferred = True
          else:
            fsNomo.preferred = False
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
          fsNP.value = grSurname
          fsNF.parts.add (fsNP)
          fsNP = gedcomx.NamePart()
          fsNP.type = "http://gedcomx.org/Given"
          fsNP.value = grGiven
          fsNF.parts.add (fsNP)
          fsNomo.nameForms.add(fsNF)
          fsP.names.add(fsNomo)
          fsP.id = self.FSID
          fsTP.persons.add(fsP)
        elif ( (tipolinio == 'edzo' )
             and linio[8] ) :
          grEdzo = self.dbstate.db.get_person_from_handle(linio[8])
          fsTR = gedcomx.Gedcomx()
          grFamilyHandle = linio[10]
          RSfsid = linio[11]
          grFamily = self.dbstate.db.get_family_from_handle(grFamilyHandle)
          fsRS = gedcomx.Relationship()
          fsRS.person1 = gedcomx.ResourceReference()
          fsRS.person2 = gedcomx.ResourceReference()
          fsRS.id = RSfsid
          fsRS.type = "http://gedcomx.org/Couple"
          if grEdzo.get_gender() == Person.MALE :
            fsRS.person1.resourceId = get_fsftid(grEdzo)
            fsRS.person2.resourceId = get_fsftid(grPersono)
          else:
            fsRS.person2.resourceId = get_fsftid(grEdzo)
            fsRS.person1.resourceId = get_fsftid(grPersono)
          fsRS.person1.resource = "https://api.familysearch.org/platform/tree/persons/" + fsRS.person1.resourceId
          fsRS.person2.resource = "https://api.familysearch.org/platform/tree/persons/" + fsRS.person2.resourceId
          fsTR.relationships.add(fsRS)
          peto = gedcomx.jsonigi(fsTR)
          jsonpeto = json.dumps(peto)
          if RSfsid and RSfsid != '' :
            res = tree._FsSeanco.post_url( "/platform/tree/couple-relationships/"+RSfsid, jsonpeto )
          else :
            res = tree._FsSeanco.post_url( "/platform/tree/relationships", jsonpeto )
          if res.status_code == 201 or res.status_code == 204:
            print("ĝisdatigo sukceso")
          if res.status_code != 201 and res.status_code != 204 :
            print("ĝisdatigo rezulto :")
            print(" jsonpeto = "+jsonpeto)
            print(" res.status_code="+str(res.status_code))
            print (res.headers)
            print (res.text)
      # FARINDAĴO : gepatroj, infanoj,…

    if len(fsTP.persons) >0 :
      peto = gedcomx.jsonigi(fsTP)
      jsonpeto = json.dumps(peto)
      res = tree._FsSeanco.post_url( "/platform/tree/persons/"+self.FSID, jsonpeto )
      if res.status_code == 201 or res.status_code == 204:
        print("ĝisdatigo sukceso")
      if res.status_code != 201 and res.status_code != 204 :
        print("ĝisdatigo rezulto :")
        print(" jsonpeto = "+jsonpeto)
        print(" res.status_code="+str(res.status_code))
        print (res.headers)
        print (res.text)
    if len(fsTP.persons) >0 or len(fsTR.relationships) >0 :
      self.ButRefresxigi_clicked(None)
    
  def kopii_al_gramps(self, treeview):
    print("kopii_al_gramps")
    model = self.modelKomp.model
    active_handle = self.get_active('Person')
    grPersono = self.dbstate.db.get_person_from_handle(active_handle)
    fsPersono = gedcomx.Person._indekso.get(self.FSID) 
    if self.dbstate.db.transaction :
      print("??? transaction en cours ???")
      self.dbstate.db.transaction_commit(self.dbstate.db.transaction)
    #  intr = True
    #  txn=self.dbstate.db.transaction
    #else :
    #  intr = False
    #  txn = DbTxn(_("kopii al gramps"), self.dbstate.db)
    with DbTxn(_("kopii al gramps"), self.dbstate.db) as txn:
    #if txn :
      for x in model:
       l = [x]
       l.extend(x.iterchildren())
       for linio in l :
        if linio[6] : 
          # FARINDAĴO : aliaj tipoj
          tipolinio = linio[7]
          if ( (tipolinio == 'fakto' )
             and linio[9] ) :
            fsFakto_id = linio[9]
            grFaktoH = linio[8]
            if fsPersono.facts:
              for fsFakto in fsPersono.facts :
                if fsFakto.id == fsFakto_id : break
              if fsFakto.id == fsFakto_id :
                print("importas fakto "+fsFakto_id+" por "+self.FSID)
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
             and linio[9] 
             and linio[10] ) :
            grFaktoH = linio[8]
            fsFakto_id = linio[9]
            grParoH = linio[10]
            fsParo_id = linio[11]
            grParo = self.dbstate.db.get_family_from_handle(grParoH)
            fsParo = gedcomx.Relationship._indekso[fsParo_id]
            for fsFakto in fsParo.facts :
              if fsFakto.id == fsFakto_id : break
            if grFaktoH :
              event = self.dbstate.db.get_event_from_handle(grFaktoH)
              Importo.updFakto(self.dbstate.db,txn,fsFakto,event)
            else :
              event = Importo.aldFakto(self.dbstate.db,txn,fsFakto,grParo)
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
          elif ( (tipolinio == 'nomo' or tipolinio == 'nomo1')
             and linio[9] ) :
            grNomo_str = linio[8]
            fsNomo_id = linio[9]
            for fsNomo in fsPersono.names :
              if fsNomo.id == fsNomo_id : break
            Importo.aldNomo(self.dbstate.db, txn, fsNomo, grPersono)
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
    import locale,gettext, os
    self.top = Gtk.Builder()
    self.top.set_translation_domain("addon")
    base = os.path.dirname(__file__)
    glade_file = base + os.sep + "PersonFS.glade"
    if os.name == 'win32' or os.name == 'nt' :
      import xml.etree.ElementTree as ET
      xtree = ET.parse(glade_file)
      for node in xtree.iter() :
        if 'translatable' in node.attrib :
          node.text = _(node.text)
      xml_text = ET.tostring(xtree.getroot(),encoding='unicode',method='xml')
      self.top.add_from_string(xml_text)
    else:
      locale.bindtextdomain("addon", base + "/locale")
      self.top.add_from_file(glade_file)

    self.res = self.top.get_object("PersonFSTop")
    self.propKomp = self.top.get_object("propKomp")
    titles = [  
                (_('Koloro'), 1, 40,COLOR),
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
    self.modelKomp = ListModel(self.propKomp, titles, list_mode="tree"
                 ,event_func=self.l_duobla_klako
                 ,right_click=self.l_dekstra_klako)
    self.top.connect_signals({
            "on_pref_clicked"      : self.pref_clicked,
            "on_ButImp1K_clicked"      : self.ButImp1K_clicked,
            "on_kopii_clicked"      : self.ButKopii_clicked,
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
    if tipo != 'fakto' and tipo != 'edzoFakto' and tipo != 'nomo' and tipo != 'nomo1' and tipo != 'edzo' :
      self.modelKomp.model.set_value(row, 6, False)
      OkDialog(_('Pardonu, nur edzaj, eventaj or nomaj linioj povas esti elektitaj.'))
      print("  toggled:tipo="+tipo)


  def ButBaskKonf_toggled(self, dummy):
   with DbTxn(_("FamilySearch etikedoj"), self.dbstate.db) as txn:
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
      if self.FSID in PersonFS.fs_Tree._persons :
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

  def ButImporti_clicked(self, dummy):
    gpr = PluginRegister.get_instance()
    plg = gpr.get_plugin('Importo de FamilySearch')
    run_plugin(plg,self.dbstate,self.uistate)

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
    if res :
      if res.status_code==201 and res.headers and "X-Entity-Id" in res.headers :
        fsid = res.headers['X-Entity-Id']
        utila.ligi_gr_fs(self.dbstate.db, person, fsid)
        self.FSID = fsid
        self.ButRefresxigi_clicked(None)
        self.Sercxi.hide()
      else :
        print (res.headers)
    #  FARINDAĴOJ :
    #     1-  mettre à jour avec les noms et faits
    #     2-  lier aux parents
    #     3-  lier aux conjoints
    #     4-  lier aux enfants
    return

  def ButKopii_clicked(self, dummy):
    #self.FSID
    clipboard = Gtk.Clipboard.get_for_display(Gdk.Display.get_default(),
                        Gdk.SELECTION_CLIPBOARD)
    clipboard.set_text(self.FSID, -1)
    clipboard = Gtk.Clipboard.get_for_display(Gdk.Display.get_default(),
                        Gdk.SELECTION_PRIMARY)
    clipboard.set_text(self.FSID, -1)

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
                (_trans.gettext('score'), 1, 80),
                (_('FS Id'), 2, 90),
                (_('Nomo, antaŭnomo'), 3, 200),
                (_trans.gettext('Birth'), 4, 250),
                (_trans.gettext('Death'), 5, 250),
                (_trans.gettext('Parents'), 6, 250),
                (_trans.gettext('Spouses'), 7, 250),
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
                    mendo ,{"Accept": "application/x-gedcomx-atom+json"}
                )
    if r == None :
      OkDialog(_('Eraro: neniuj datumoj.'))
    elif r.status_code == 200 :
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
                (_trans.gettext('score'), 1, 80),
                (_('FS Id'), 2, 90),
                (_('Nomo, antaŭnomo'), 3, 200),
                (_trans.gettext('Birth'), 4, 250),
                (_trans.gettext('Death'), 5, 250),
                (_trans.gettext('Parents'), 6, 250),
                (_trans.gettext('Spouses'), 7, 250),
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
    if grBirth == None or grBirth.date == None or grBirth.date.is_empty() :
      grBirth = get_grevent(self.dbstate.db, person, EventType(EventType.CHRISTEN))
    if grBirth == None or grBirth.date == None or grBirth.date.is_empty() :
      grBirth = get_grevent(self.dbstate.db, person, EventType(EventType.ADULT_CHRISTEN))
    if grBirth == None or grBirth.date == None or grBirth.date.is_empty() :
      grBirth = get_grevent(self.dbstate.db, person, EventType(EventType.BAPTISM))
    if grBirth and grBirth.date and not grBirth.date.is_empty() :
      naskoDato = grdato_al_formal(grBirth.date)
      if len(naskoDato) >0 and naskoDato[0] == 'A' : naskoDato = naskoDato[1:]
      if len(naskoDato) >0 and naskoDato[0] == '/' : naskoDato = naskoDato[1:]
      posOblikvo = naskoDato.find('/')
      if posOblikvo > 1 : naskoDato = naskoDato[:posOblikvo]
      self.top.get_object("fs_nasko_eniro").set_text( naskoDato)
    else:
      self.top.get_object("fs_nasko_eniro").set_text( '')

    grDeath = get_grevent(self.dbstate.db, person, EventType(EventType.DEATH))
    if grDeath == None or grDeath.date == None or grDeath.date.is_empty() :
      grDeath = get_grevent(self.dbstate.db, person, EventType(EventType.BURIAL))
    if grDeath == None or grDeath.date == None or grDeath.date.is_empty() :
      grDeath = get_grevent(self.dbstate.db, person, EventType(EventType.CREMATION))
    if grDeath and grDeath.date and not grDeath.date.is_empty() :
      mortoDato = grdato_al_formal(grDeath.date)
      if len(mortoDato) >0 and mortoDato[0] == 'A' : mortoDato = mortoDato[1:]
      if len(mortoDato) >0 and mortoDato[0] == '/' : mortoDato = mortoDato[1:]
      posOblikvo = mortoDato.find('/')
      if posOblikvo > 1 : mortoDato = mortoDato[:posOblikvo]
      self.top.get_object("fs_morto_eniro").set_text( mortoDato)
    else:
      self.top.get_object("fs_morto_eniro").set_text( '')

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
    nasko = self.top.get_object("fs_nasko_eniro").get_text()
    if nasko :
      mendo = mendo + "q.birthLikeDate=%s&" % nasko
    morto = self.top.get_object("fs_morto_eniro").get_text()
    if morto :
      mendo = mendo + "q.deathLikeDate=%s&" % morto
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
            if 'latitude' in place and 'longitude' in place :
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

  def ButImp1K_clicked(self, dummy):
    active_handle = self.get_active('Person')
    grPersono = self.dbstate.db.get_person_from_handle(active_handle)
    importilo = Importo.FsAlGr()
    fsid = get_fsftid(grPersono)
    importilo.importi(self, fsid)
    #import cProfile
    #cProfile.runctx('importilo.importi(self, fsid)',globals(),locals())
    self.uistate.set_active(active_handle, 'Person')

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
    fsetik = self.top.get_object("fsetik_eniro")
    print("fs_etikedado="+str(PersonFS.fs_etikedado))
    fsetik.set_active(PersonFS.fs_etikedado)
    top.show()
    res = top.run()
    top.hide()
    if res == -3:
      PersonFS.fs_sn = fssn.get_text()
      PersonFS.fs_pasvorto = fspv.get_text()
      PersonFS.fs_etikedado = fsetik.get_active()
      print("fs_etikedado="+str(PersonFS.fs_etikedado))
      CONFIG.set("preferences.fs_sn", PersonFS.fs_sn)
      #CONFIG.set("preferences.fs_pasvorto", PersonFS.fs_pasvorto) #
      CONFIG.set("preferences.fs_etikedado", str(PersonFS.fs_etikedado))
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
    if PersonFS.fs_etikedado :
      fs_db.create_tags(self.dbstate.db)
    self.FSID = None
    grPersono = self.dbstate.db.get_person_from_handle(person_handle)
    tag_fs = self.dbstate.db.get_tag_from_name('FS_Konf')
    if tag_fs and tag_fs.handle in grPersono.tag_list :
      self.top.get_object("ButBaskKonf").set_active(True)
    else :
      self.top.get_object("ButBaskKonf").set_active(False)
      
    fsid = get_fsftid(grPersono)
    self.FSID = fsid
    if fsid == '' :
      fsid = 'xxxx-xxx'
      lien = 'https://familysearch.org/'
    else :
      lien = 'https://familysearch.org/tree/person/' + fsid
    self.top.get_object("LinkoButono").set_label(fsid)
    self.top.get_object("LinkoButono").set_uri(lien)
    ## Se fsid ne estas specifita: nenio pli :
    ##if fsid == '' or fsid == 'xxxx-xxx' :
    ##  return

    ### Se ĝi ne estas konektita al familysearch: nenio pli.
    ##if tree._FsSeanco == None or not tree._FsSeanco.logged:
    ##  return
    #
    PersonFS.FSID = self.FSID
    fsPerso = gedcomx.Person()
    if PersonFS.FSID != '' and PersonFS.fs_Tree :
      # ŝarĝante individuan "FamilySearch" :
      PersonFS.fs_Tree.add_persons([fsid])
      #fsPerso = gedcomx.Person._indekso.get(fsid) 
      fsPerso = PersonFS.fs_Tree._persons.get(fsid)
      # legas persona kaplinio
      mendo = "/platform/tree/persons/"+fsid
      r = tree._FsSeanco.head_url( mendo )
      if r and r.status_code == 301 and 'X-Entity-Forwarded-Id' in r.headers :
        fsid = r.headers['X-Entity-Forwarded-Id']
        PersonFS.FSID = fsid
        utila.ligi_gr_fs(self.dbstate.db, grPersono, fsid)
        mendo = "/platform/tree/persons/"+fsid
        r = tree._FsSeanco.head_url( mendo )
      if r :
        datemod = int(time.mktime(email.utils.parsedate(r.headers['Last-Modified'])))
        etag = r.headers['Etag']
      if not fsPerso :
        PersonFS.fs_Tree.add_persons([fsid])
        fsPerso = gedcomx.Person._indekso.get(fsid) or gedcomx.Person()
      if fsPerso and fsid != PersonFS.FSID :
        fsPerso.id=fsid

      if getfs == True :
        PersonFS.fs_Tree.add_spouses([fsid])
        PersonFS.fs_Tree.add_children([fsid])
    if getfs == True :
      kompRet = komparo.kompariFsGr(fsPerso, grPersono, self.dbstate.db, self.modelKomp,True)
    else:
      kompRet = komparo.kompariFsGr(fsPerso, grPersono, self.dbstate.db, self.modelKomp,False)
    for row in self.modelKomp.model :
      if row[0] == 'red' :
        self.propKomp.expand_row(row.path,1)
    
    if not PersonFS.fs_Tree:
      return

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
