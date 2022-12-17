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
from gramps.gen.db import DbTxn
from gramps.gen.config import config
from gramps.gen.const import GRAMPS_LOCALE as glocale
from gramps.gen.datehandler import get_date
from gramps.gen.display.name import displayer as name_displayer
from gramps.gen.display.place import displayer as _pd
from gramps.gen.errors import WindowActiveError
from gramps.gen.lib import Date, EventType, EventRoleType, Person, StyledText, StyledTextTag, StyledTextTagType, Tag
from gramps.gen.plug import Gramplet, PluginRegister
from gramps.gen.utils.db import get_birth_or_fallback, get_death_or_fallback

from gramps.gui.dialog import OptionDialog, OkDialog
from gramps.gui.editors import EditPerson
from gramps.gui.listmodel import ListModel, NOSORT, COLOR
from gramps.gui.viewmanager import run_plugin
from gramps.gui.widgets.buttons import IconButton
from gramps.gui.widgets.styledtexteditor import StyledTextEditor

from gramps.plugins.lib.libgedcom import PERSONALCONSTANTEVENTS, FAMILYCONSTANTEVENTS, GED_TO_GRAMPS_EVENT

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
from constants import FACT_TAGS, FACT_TYPES
import fs_db
import komparo
import tree
import utila
from utila import getfsid, get_grevent, get_fsfact, grdato_al_formal

import sys
import os
import time

try:
    _trans = glocale.get_addon_translator(__file__)
except ValueError:
    _trans = glocale.translation
_ = _trans.gettext


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
        self.top = Gtk.Builder()
        self.top.set_translation_domain("addon")
        base = os.path.dirname(__file__)
        locale.bindtextdomain("addon", base + "/locale")
        glade_file = base + os.sep + "PersonFS.glade"
        self.top.add_from_file(glade_file)
        top = self.top.get_object("PersonFSPrefDialogo")
        top.set_transient_for(self.uistate.window)
        parent_modal = self.uistate.window.get_modal()
        if parent_modal:
          self.uistate.window.set_modal(False)
        fsid = self.top.get_object("fsid_eniro")
        fsid.set_text(PersonFS.fs_sn)
        fspv = self.top.get_object("fspv_eniro")
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
          #  tree._FsSeanco = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, True, False, 2)
          #else :
          tree._FsSeanco = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, False, False, 2)
        else :
          print("Vi devas enigi la ID kaj pasvorton")
      else:
        #if self.vorteco >= 3:
        #  tree._FsSeanco = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, True, False, 2)
        #else :
        tree._FsSeanco = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, False, False, 2)
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
      print("konekti")
      tree._FsSeanco = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, True, False, 2)
      #tree._FsSeanco = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, False, False, 2)
    if not tree._FsSeanco.logged :
      return
    if not PersonFS.fs_Tree:
      PersonFS.fs_Tree = tree.Tree()
      PersonFS.fs_Tree._getsources = False

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
                (_('Coloro'), 1, 20,COLOR),
		( _('Propreco'), 2, 100),
		( _('Dato'), 3, 120),
                (_('Gramps Valoro'), 4, 200),
                (_('FS Dato'), 5, 120),
                (_('FS Valoro'), 6, 200),
             ]
    self.modelKomp = ListModel(self.propKomp, titles)
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

  def ButBaskKonf_toggled(self, dummy):
   with DbTxn(_("FamilySearch tags"), self.dbstate.db) as txn:
    val = self.top.get_object("ButBaskKonf").get_active()
    print ("checkbox active : "+str(val))
    tag_fs = self.dbstate.db.get_tag_from_name('FS_Konf')
    active_handle = self.get_active('Person')
    grPersono = self.dbstate.db.get_person_from_handle(active_handle)
    dbPersono= fs_db.db_stato(self.dbstate.db,grPersono.handle)
    dbPersono.get()
    dbPersono.konf = val
    dbPersono.commit(txn)
    if not val and tag_fs.handle in grPersono.tag_list:
      grPersono.remove_tag(tag_fs.handle)
    if tag_fs and val and tag_fs.handle not in grPersono.tag_list:
      grPersono.add_tag(tag_fs.handle)
    self.dbstate.db.commit_person(grPersono, txn, grPersono.change)

  def ButRefresxigi_clicked(self, dummy):
    rezulto = gedcomx.jsonigi(PersonFS.fs_Tree)
    f = open('arbo1.out.json','w')
    json.dump(rezulto,f,indent=2)
    f.close()
    if self.FSID :
      try:
        PersonFS.fs_Tree._persons.pop(self.FSID)
      except:
        pass
      PersonFS.fs_Tree.add_persons([self.FSID])
    rezulto = gedcomx.jsonigi(PersonFS.fs_Tree)
    f = open('arbo2.out.json','w')
    json.dump(rezulto,f,indent=2)
    f.close()

    active_handle = self.get_active('Person')
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
    #  fsFakto.type = FACT_TYPES.get(grTag)
    #  fsFakto.place = grFaktoLoko
    #  fsFakto.value = grFaktoPriskribo
    #  fsPerso.facts.add(fsFakto)
    # FARINDAĴOJ : fontoj, …
    peto = {'persons' : [gedcomx.jsonigi(fsPerso)]}
    jsonpeto = json.dumps(peto)
    print(jsonpeto)
    res = tree._FsSeanco.post_url( "/platform/tree/persons", jsonpeto )
    if res.status_code==201 and res.headers and "X-Entity-Id" in res.headers :
      fsid = res.headers['X-Entity-Id']
      utila.ligi_gr_fs(self.dbstate.db, person, fsid)
      self.FSID = fsid
      self.ButRefresxigi_clicked(self,None)
    else :
      print (res.headers)
      #from objbrowser import browse ;browse(locals())
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
      ButRefresxigi_clicked(self,None)
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
            #print(" ajout place : "+place["id"])
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
          #print("   person:"+person["id"])
          if "ascendancyNumber" in person["display"] and person["display"]["ascendancyNumber"] == 1 :
            #print("   asc")
            if person["gender"]["type"] == "http://gedcomx.org/Female" :
              #print("     mother")
              motherId=person["id"]
              mother=self.fs_TreeSercxo._persons[person["id"]]
            elif person["gender"]["type"] == "http://gedcomx.org/Male" :
              #print("     father")
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
            #print("   ParentChild;p1="+person1Id+";p2="+person2Id)
            if person2Id == fsId :
              person1=self.fs_TreeSercxo._persons[person1Id]
              if not father and person1.gender.type == "http://gedcomx.org/Male" :
                father = person1
              elif not mother and person1.gender.type == "http://gedcomx.org/Female" :
                mother = person1
              
      fsNomo = fsPerso.akPrefNomo()
      fsBirth = get_fsfact (fsPerso, 'http://gedcomx.org/Birth' ) or gedcomx.Fact()
      fsBirthLoko = fsBirth.place 
      #from objbrowser import browse ;browse(locals())
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
      #from objbrowser import browse ;browse(locals())
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
    self.FSID = None
    grPersono = self.dbstate.db.get_person_from_handle(person_handle)
    tag_fs = self.dbstate.db.get_tag_from_name('FS_Konf')
    if tag_fs.handle in grPersono.tag_list :
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
    fsPerso = gedcomx.Person._indekso.get(fsid) 
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
    
    fs_db.create_schema(db)
    komparo.kompariFsGr(fsPerso, grPersono, self.dbstate.db, self.modelKomp)


    return

  # FARINDAĴOJ : kopii, redundoj, esploro, …
