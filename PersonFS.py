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
from gramps.gen.lib import Attribute, Date, EventType, EventRoleType, Person, StyledText, StyledTextTag, StyledTextTagType
from gramps.gen.lib.date import gregorian
from gramps.gen.plug import Gramplet, PluginRegister
from gramps.gen.utils.db import get_birth_or_fallback, get_death_or_fallback

from gramps.gui.dialog import OptionDialog
from gramps.gui.editors import EditPerson
from gramps.gui.listmodel import ListModel, NOSORT, COLOR
from gramps.gui.viewmanager import run_plugin
from gramps.gui.widgets.buttons import IconButton
from gramps.gui.widgets.styledtexteditor import StyledTextEditor

from gramps.plugins.lib.libgedcom import PERSONALCONSTANTEVENTS, FAMILYCONSTANTEVENTS, GED_TO_GRAMPS_EVENT

# lokaloj 
from fslib.session import Session
from fslib.constants import FACT_TAGS, FACT_TYPES
from fslib.tree import Tree, Name as fsName, Indi, Fact, jsonigi


import sys
import os
import time



try:
    _trans = glocale.get_addon_translator(__file__)
except ValueError:
    _trans = glocale.translation
_ = _trans.gettext
#_ = glocale.translation.gettext


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



def grdato_al_formal( dato) :
  """
  " konvertas gramps-daton al «formal» dato
  "   «formal» dato : <https://github.com/FamilySearch/gedcomx/blob/master/specifications/date-format-specification.md>
  """
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
  # FARINDAĴOJ : range ?  estimate ? calculate ? heure ?
  
  return res

def getfsid(person) :
  if not person :
    return ''
  for attr in person.get_attribute_list():
    if attr.get_type() == '_FSFTID':
      return attr.get_value()
  return ''

class PersonFS(Gramplet):
  """
  " Interfaco kun familySearch
  """
  fs_sn = CONFIG.get("preferences.fs_sn")
  fs_pasvorto = ''
  fs_pasvorto = CONFIG.get("preferences.fs_pasvorto") #
  fs_Session = None
  fs_Tree = None
  fs_TreeSercxo = None
  Sercxi = None
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

  def _db_create_schema(self):
    # krei datumbazan tabelon
    if not self.dbstate.db.dbapi.table_exists("personfs_stato"):
      with DbTxn(_("FamilySearch krei"), self.dbstate.db) as txn:
        self.dbstate.db.dbapi.execute('CREATE TABLE personfs_stato '
                           '('
                           'p_handle VARCHAR(50) PRIMARY KEY NOT NULL, '
                           'fsid CHAR(8), '
                           'estas_radiko CHAR(1), '
                           'stat_dato integer, '
                           'konf_dato integer, '
                           'gramps_datomod integer, '
                           'fs_datomod integer,'
                           'konf_esenco CHAR(1),'
                           'konf CHAR(1) '
                           ')')

  def _db_commit(self,person_handle):
    with DbTxn(_("FamilySearch commit"), self.dbstate.db) as txn:
      if self.db_handle :
        sql = "UPDATE personfs_stato set fsid=?, estas_radiko=? , stat_dato=?, konf_dato=?, gramps_datomod=?, fs_datomod=?, konf_esenco=?, konf=? where p_handle=? "
        self.dbstate.db.dbapi.execute(sql, [ self.db_fsid, self.db_estas_radiko or 'F', self.db_stat_dato, self.db_konf_dato, self.db_gramps_datomod, self.db_fs_datomod, self.db_konf_esenco or 'F', self.db_konf or 'F', self.db_handle] )
      else :
        self.db_handle = person_handle
        sql = "INSERT INTO personfs_stato(p_handle,fsid,estas_radiko,stat_dato,konf_dato,gramps_datomod,fs_datomod,konf_esenco,konf) VALUES (?,?,?,?,?,?,?,?,?)"
        self.dbstate.db.dbapi.execute(sql, [ self.db_handle, self.db_fsid, self.db_estas_radiko or 'F', self.db_stat_dato, self.db_konf_dato, self.db_gramps_datomod, self.db_fs_datomod, self.db_konf_esenco or 'F', self.db_konf or 'F' ] )

  def _db_get(self,person_handle):
    self.dbstate.db.dbapi.execute("select p_handle,fsid,estas_radiko,stat_dato,konf_dato,gramps_datomod,fs_datomod,konf_esenco,konf from personfs_stato where p_handle=?",[person_handle])
    datumoj = self.dbstate.db.dbapi.fetchone()
    if datumoj:
      self.db_handle = datumoj[0]
      self.db_fsid = datumoj[1]
      self.db_estas_radiko = datumoj[2]
      self.db_stat_dato = datumoj[3]
      self.db_konf_dato = datumoj[4]
      self.db_gramps_datomod = datumoj[5]
      self.db_fs_datomod = datumoj[6]
      self.db_konf_esenco = datumoj[7]
      self.db_konf = datumoj[8]

  def init(self):
    """
    " kreas GUI kaj konektas al FamilySearch
    """
    # FARINDAĴO : uzi PersonFS.lingvo

    # krei datumbazan tabelon
    self._db_create_schema()

    self.gui.WIDGET = self.krei_gui()
    self.gui.get_container_widget().remove(self.gui.textview)
    self.gui.get_container_widget().add_with_viewport(self.gui.WIDGET)
    self.gui.WIDGET.show_all()

    if PersonFS.fs_sn == '' or PersonFS.fs_pasvorto == '':
      self.pref_clicked(None)
    else:
      self.konekti_FS()
    self.db_handle= self.db_fsid= self.db_estas_radiko= self.db_stat_dato= self.db_konf_dato= self.db_gramps_datomod= self.db_fs_datomod = None
    self.db_konf_esenco = self.db_konf = None

  def konekti_FS(self):
    if not PersonFS.fs_Session:
      #PersonFS.fs_Session = Session(PersonFS.fs_sn, PersonFS.fs_pasvorto, True, False, 2)
      PersonFS.fs_Session = Session(PersonFS.fs_sn, PersonFS.fs_pasvorto, False, False, 2)
    if not PersonFS.fs_Session.logged:
      return
    if not PersonFS.fs_Tree:
      PersonFS.fs_Tree = Tree(PersonFS.fs_Session)
      PersonFS.fs_Tree.getsources = False

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
            "on_ButLancxi_clicked"      : self.ButLancxi_clicked,
            "on_ButAldoni_clicked"      : self.ButAldoni_clicked,
            "on_ButLigi_clicked"      : self.ButLigi_clicked,
            "on_ButRefresxigi_clicked"      : self.ButRefresxigi_clicked,
            "on_ButImporti_clicked"      : self.ButImporti_clicked,
	})

    return self.res

  def ButRefresxigi_clicked(self, dummy):
    if self.FSID :
      try:
        PersonFS.fs_Tree.indi.pop(self.FSID)
      except:
        pass
      PersonFS.fs_Tree.add_indis([self.FSID])
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
    fsPerso = Indi(None,self.fs_Tree)
    fsPerso.living = False
    if person.get_gender() == Person.MALE :
      fsPerso.gender = "http://gedcomx.org/Male"
    elif person.get_gender() == Person.FEMALE :
      fsPerso.gender = "http://gedcomx.org/Female"
    else:
      fsPerso.gender = "http://gedcomx.org/Unknown"
    grNomo = person.primary_name
    nomo = fsName()
    nomo.given = grNomo.first_name
    if grNomo.type == 3 :
      nomo.type = 'http://gedcomx.org/MarriedName'
    elif grNomo.type == 1 :
      nomo.type = 'http://gedcomx.org/AlsoKnownAs'
    else :
      nomo.type = 'http://gedcomx.org/BirthName'
    nomo.surname = grNomo.get_primary_surname().surname
    nomo.preferred = True
    fsPerso.names.add(nomo)
    # FARINDAĴO : aliaj nomoj
    grFaktoj = person.event_ref_list
    for grFakto in grFaktoj :
      if int(grFakto.get_role()) != EventRoleType.PRIMARY:
        continue
      event = self.dbstate.db.get_event_from_handle(grFakto.ref)
      titolo = str(EventType(event.type))
      grFaktoPriskribo = event.description or ''
      grFaktoDato = grdato_al_formal(event.date)
      if event.place and event.place != None :
        place = self.dbstate.db.get_place_from_handle(event.place)
        grFaktoLoko = place.name.value
      else :
        grFaktoLoko = ''
      # FARINDAĴO : norma loknomo
      if grFaktoLoko == '' :
        grValoro = grFaktoPriskribo
      else :
        grValoro = grFaktoPriskribo +' @ '+ grFaktoLoko
      grTag = PERSONALCONSTANTEVENTS.get(int(event.type), "").strip() or event.type
      fsFakto = Fact()
      fsFakto.date = grFaktoDato
      fsFakto.type = FACT_TYPES.get(grTag)
      fsFakto.place = grFaktoLoko
      fsFakto.value = grFaktoPriskribo
      fsPerso.facts.add(fsFakto)
    # FARINDAĴOJ : fontoj, …
    peto = {'persons' : [jsonigi(fsPerso)]}
    jsonpeto = json.dumps(peto)
    res = self.fs_Tree.fs.post_url( "/platform/tree/persons", jsonpeto )
    if res.status_code==201 and res.headers and "X-Entity-Id" in res.headers :
      with DbTxn(_("Aldoni FamilySearch ID"), self.dbstate.db) as txn:
        fsid = res.headers['X-Entity-Id']
        attr = Attribute()
        attr.set_type('_FSFTID')
        attr.set_value(fsid)
        person.add_attribute(attr)
        self.dbstate.db.commit_person(person,txn)
        self.FSID = fsid
        self.ButRefresxigi_clicked(self,None)
    #else :
    #  FARINDAĴO 
    
    return

  def ButLigi_clicked(self, dummy):
    model, iter_ = self.top.get_object("PersonFSResRes").get_selection().get_selected()
    if iter_ :
      fsid = model.get_value(iter_, 1)
      #print(fsid)
      active_handle = self.get_active('Person')
      person = self.dbstate.db.get_person_from_handle(active_handle)
      attr = None
      with DbTxn(_("Aldoni FamilySearch ID"), self.dbstate.db) as txn:
        for attr in person.get_attribute_list():
          if attr.get_type() == '_FSFTID':
            attr.set_value(fsid)
            # FARINDAĴO : mesaĝo
            # ou lancement du lien vers la fusion dans familysearch ?
            break
        if not attr :
          attr = Attribute()
          attr.set_type('_FSFTID')
          attr.set_value(fsid)
          person.add_attribute(attr)
        self.dbstate.db.commit_person(person,txn)
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
    grBirth = self.get_grevent(person, EventType(EventType.BIRTH))
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
      PersonFS.fs_TreeSercxo = Tree(PersonFS.fs_Session)
      PersonFS.fs_TreeSercxo.getsources = False
    self.modelRes.clear()
    mendo = "/platform/tree/search?"
    grNomo = self.top.get_object("fs_nomo_eniro").get_text()
    if grNomo :
      mendo = mendo + "q.surname=\"%s\"&" % grNomo
    grANomo = self.top.get_object("fs_anomo_eniro").get_text()
    if grANomo :
      mendo = mendo + "q.givenName=\"%s\"&" % grANomo
    sekso = self.top.get_object("fs_sekso_eniro").get_text()
    if sekso :
      mendo = mendo + "q.sex=%s&" % sekso
    birdo = self.top.get_object("fs_birdo_eniro").get_text()
    if birdo :
      mendo = mendo + "q.birthLikeDate=%s&" % birdo
    loko = self.top.get_object("fs_loko_eniro").get_text()
    if loko :
      mendo = mendo + "q.anyPlace=\"%s\"&" % loko
    mendo = mendo + "offset=0&count=10"
    datumoj = self.fs_TreeSercxo.fs.get_url(
                    mendo ,{"Accept": "application/x-gedcomx-atom+json", "Accept-Language": "fr"}
                )
    if not datumoj :
      return
    tot = datumoj["results"]
    #print ("nb résultats = "+str(tot))
    for entry in datumoj["entries"] :
      #print (entry.get("id")+ ";  score = "+str(entry.get("score")))
      fsId = entry.get("id")
      data=entry["content"]["gedcomx"]
      if "places" in data:
        for place in data["places"]:
          if place["id"] not in self.fs_TreeSercxo.places:
            #print(" ajout place : "+place["id"])
            self.fs_TreeSercxo.places[place["id"]] = (
                                str(place["latitude"]),
                                str(place["longitude"]),
                            )
      father = None
      mother = None
      if "persons" in data:
        for person in data["persons"]:
          #from objbrowser import browse ;browse(locals())
          self.fs_TreeSercxo.indi[person["id"]] = Indi(person["id"], self.fs_TreeSercxo)
          self.fs_TreeSercxo.indi[person["id"]].add_data(person)
          #print("   person:"+person["id"])
          if "ascendancyNumber" in person["display"] and person["display"]["ascendancyNumber"] == 1 :
            #print("   asc")
            if person["gender"]["type"] == "http://gedcomx.org/Female" :
              #print("     mother")
              mother=self.fs_TreeSercxo.indi[person["id"]]
            elif person["gender"]["type"] == "http://gedcomx.org/Male" :
              #print("     father")
              father=self.fs_TreeSercxo.indi[person["id"]]
      fsPerso = PersonFS.fs_TreeSercxo.indi.get(fsId) or Indi()
      if "relationships" in data:
        for rel in data["relationships"]:
          if rel["type"] == "http://gedcomx.org/Couple":
            person1Id = rel["person1"]["resourceId"]
            person2Id = rel["person2"]["resourceId"]
            relfid = rel.get("id")
            if person1Id in PersonFS.fs_TreeSercxo.indi:
              PersonFS.fs_TreeSercxo.indi[person1Id].spouses.add(
                 (person1Id, person2Id, relfid)
                )
            if person2Id in PersonFS.fs_TreeSercxo.indi:
              PersonFS.fs_TreeSercxo.indi[person2Id].spouses.add(
                 (person1Id, person2Id, relfid)
                )
            self.fs_TreeSercxo.add_fam(person1Id, person2Id)
            family = self.fs_TreeSercxo.fam[(person1Id, person2Id)]
            if relfid:
              family.add_marriage(relfid)
          elif rel["type"] == "http://gedcomx.org/ParentChild":
            person1Id = rel["person1"]["resourceId"]
            person2Id = rel["person2"]["resourceId"]
            #print("   ParentChild;p1="+person1Id+";p2="+person2Id)
            if person2Id == fsId :
              person1=self.fs_TreeSercxo.indi[person1Id]
              if not father and person1.gender == "http://gedcomx.org/Male" :
                father = person1
              elif not mother and person1.gender == "http://gedcomx.org/Female" :
                mother = person1
              
      fsNomo = fsPerso.name or fsName()
      fsBirth = self.get_fsfact (fsPerso, 'http://gedcomx.org/Birth' ) or Fact()
      fsBirthLoko = fsBirth.place 
      if fsBirthLoko :
        fsBirth = fsBirth.date or '' + ' \n@ ' +fsBirthLoko
      else :
        fsBirth = fsBirth.date or ''
      fsDeath = self.get_fsfact (fsPerso, 'http://gedcomx.org/Death' ) or Fact()
      fsDeathLoko = fsDeath.place 
      if fsDeathLoko :
        fsDeath = fsDeath.date or '' + ' \n@ ' +fsDeathLoko
      else :
        fsDeath = fsDeath.date or ''
      #from objbrowser import browse ;browse(locals())
      if father and father.name :
        fsPatroNomo = father.name
      else:
        fsPatroNomo = fsName()
      if mother and mother.name :
        fsPatrinoNomo = mother.name
      else:
        fsPatrinoNomo = fsName()
      edzoj = ''
      for fsEdzTrio in fsPerso.spouses :
        if fsEdzTrio[0] == fsId:
          edzoId = fsEdzTrio[1]
        elif fsEdzTrio[1] == fsId:
          edzoId = fsEdzTrio[0]
        else: continue
        fsEdzo = PersonFS.fs_TreeSercxo.indi.get(edzoId) or Indi()
        fsEdzoNomo = fsEdzo.name or fsName()
        if edzoj != '': edzoj = edzoj + "\n"
        edzoj = edzoj + fsEdzoNomo.surname +  ', ' + fsEdzoNomo.given
      self.modelRes.add( ( 
		  str(entry.get("score"))
		, fsId
		, fsNomo.surname +  ', ' + fsNomo.given
		, fsBirth
		, fsDeath
                , fsPatroNomo.surname +  ', ' + fsPatroNomo.given
                   + '\n'+fsPatrinoNomo.surname +  ', ' + fsPatrinoNomo.given
		, edzoj
		) )
    self.Sercxi.show()

      
    
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

  def get_grevent(self, person, event_type):
    """
    " Liveras la unuan gramps eventon de la donita tipo.
    """
    if not person:
      return None
    for event_ref in person.get_event_ref_list():
      if int(event_ref.get_role()) == EventRoleType.PRIMARY:
        event = self.dbstate.db.get_event_from_handle(event_ref.ref)
        if event.get_type() == event_type:
          return event
    return None

  def grperso_datoj (self, person) :
    if not person:
      return ''
    grBirth = self.get_grevent(person, EventType(EventType.BIRTH))
    if grBirth :
      if grBirth.date.modifier == Date.MOD_ABOUT :
        res = '~'
      elif grBirth.date.modifier == Date.MOD_BEFORE:
        res = '/'
      else :
        res = ' '
      val = "%04d" % ( grBirth.date.dateval[Date._POS_YR] )
      if val == '0000' :
        val = '....'
      if grBirth.date.modifier == Date.MOD_AFTER:
        res = res + val + '/-'
      else :
        res = res + val + '-'
    else :
      res = ' ....-'
    grDeath = self.get_grevent(person, EventType(EventType.DEATH))
    if grDeath :
      if grDeath.date.modifier == Date.MOD_ABOUT :
        res = res + '~'
      elif grDeath.date.modifier == Date.MOD_BEFORE:
        res = res + '/'
      val = "%04d" % ( grDeath.date.dateval[Date._POS_YR] )
      if val == '0000' :
        val = '....'
      if grDeath.date.modifier == Date.MOD_AFTER:
        res = res + val + '/'
      else :
        res = res + val 
    else :
      res = res + '....'
    return res

  def fsperso_datoj (self, fsPerso) :
    if not fsPerso:
      return ''
    fsFakto = self.get_fsfact (fsPerso, 'http://gedcomx.org/Birth' )
    if fsFakto and fsFakto.date :
      if fsFakto.date[0] == 'A' :
        res ='~'
      elif fsFakto.date[0] == '/' :
        res ='/'
      else :
        res = ' '
      posSigno = fsFakto.date.find('+')
      posMinus = fsFakto.date.find('-')
      if posMinus >= 0 and (posSigno <0 or posSigno > posMinus) :
        posSigno = posMinus
      if len(fsFakto.date) >= posSigno+5 :
        res = res + fsFakto.date[posSigno+1:posSigno+5]
      else :
        res = res+'....'
      if len(fsFakto.date) >= posSigno+6 and fsFakto.date[posSigno+6] == '/' :
        res = res + '/'
      res = res+'-'
    else :
      res = ' ....-'
    fsFakto = self.get_fsfact (fsPerso, 'http://gedcomx.org/Death' )
    if fsFakto and fsFakto.date :
      if fsFakto.date[0] == 'A' :
        res = res + '~'
      elif fsFakto.date[0] == '/' :
        res = res + '/'
      posSigno = fsFakto.date.find('+')
      posMinus = fsFakto.date.find('-')
      if posMinus >= 0 and (posSigno <0 or posSigno > posMinus) :
        posSigno = posMinus
      if len(fsFakto.date) >= posSigno+6 :
        res = res + fsFakto.date[posSigno+1:posSigno+5]
      else :
        res = res+'....'
      if len(fsFakto.date) >= posSigno+7 and fsFakto.date[posSigno+6] == '/' :
        res = res + '/'
    else :
      res = res + '....'
    return res

  def get_fsfact(self, person, fact_tipo):
    """
    " Liveras la unuan familysearch fakton de la donita tipo.
    """
    for fact in person.facts :
      if fact.type == fact_tipo :
        return fact
    return None

  def aldSeksoKomp(self, person, fsPerso ) :
    if person.get_gender() == Person.MALE :
      grSekso = _trans.gettext("male")
    elif person.get_gender() == Person.FEMALE :
      grSekso = _trans.gettext("female")
    else :
      grSekso = _trans.gettext("unknown")
    if fsPerso.gender == "http://gedcomx.org/Male" :
      fsSekso = _trans.gettext("male")
    elif fsPerso.gender == "http://gedcomx.org/Female" :
      fsSekso = _trans.gettext("female")
    else :
      fsSekso = _trans.gettext("unknown")
    coloro = "orange"
    fsPerso.konf_sekso = False
    if (grSekso == fsSekso) :
      coloro = "green"
      fsPerso.konf_sekso = True
    self.modelKomp.add( ( coloro , _('Sekso:')
		, '', grSekso
		, '', fsSekso
		) )
    return

  def aldNomojKomp(self, person, fsPerso ) :
    grNomo = person.primary_name
    fsNomo = fsPerso.name or fsName()
    coloro = "orange"
    fsPerso.konf_nomo = False
    if (grNomo.get_primary_surname().surname == fsNomo.surname) and (grNomo.first_name == fsNomo.given) :
      coloro = "green"
      fsPerso.konf_nomo = True
    self.modelKomp.add( ( coloro , _trans.gettext('Name')
		, '', grNomo.get_primary_surname().surname + ', ' + grNomo.first_name 
		, '', fsNomo.surname +  ', ' + fsNomo.given
		) )
    res = fsPerso.konf_nomo
    fsNomoj = fsPerso.nicknames.union(fsPerso.birthnames)
    #fsNomoj = fsPerso.nicknames.union(fsPerso.birthnames).union(fsPerso.aka)
    for grNomo in person.alternate_names :
      fsNomo = fsName()
      coloro = "yellow"
      for x in fsNomoj :
        if (grNomo.get_primary_surname().surname == x.surname) and (grNomo.first_name == x.given) :
          fsNomo = x
          coloro = "green"
          fsNomoj.remove(x)
          break
      if coloro != "green" : res = False
      self.modelKomp.add( ( coloro , '  ' + _trans.gettext('Name')
		, '', grNomo.get_primary_surname().surname + ', ' + grNomo.first_name 
		, '', fsNomo.surname +  ', ' + fsNomo.given
		) )
    coloro = "yellow"
    for fsNomo in fsNomoj :
      res = False
      self.modelKomp.add( ( coloro , '  ' + _trans.gettext('Name')
		, '', ''
		, '', fsNomo.surname +  ', ' + fsNomo.given
		) )
    return res

  def aldFaktoKomp(self, person, fsPerso, grEvent , fsFact ) :
    grFakto = self.get_grevent(person, EventType(grEvent))
    titolo = str(EventType(grEvent))
    if grFakto != None :
      grFaktoDato = grdato_al_formal(grFakto.date)
      if grFakto.place and grFakto.place != None :
        place = self.dbstate.db.get_place_from_handle(grFakto.place)
        grFaktoLoko = place.name.value
      else :
        grFaktoLoko = ''
    else :
      grFaktoDato = ''
      grFaktoLoko = ''
    # FARINDAĴO : norma loknomo

    fsFakto = self.get_fsfact (fsPerso, fsFact )
    fsFaktoDato = ''
    fsFaktoLoko = ''
    if fsFakto != None :
      if fsFakto.date :
        fsFaktoDato = fsFakto.date
      if fsFakto.place :
        fsFaktoLoko = fsFakto.place
    coloro = "orange"
    if (grFaktoDato == fsFaktoDato) :
      coloro = "green"
    if grFaktoDato == '' and grFaktoLoko == '' and fsFaktoDato == '' and fsFaktoLoko == '' :
      return
    self.modelKomp.add( ( coloro , titolo
		, grFaktoDato , grFaktoLoko
		, fsFaktoDato , fsFaktoLoko
		) )
    return (coloro == "green")

  def aldAliajFaktojKomp(self, person, fsPerso ) :
    grFaktoj = person.event_ref_list
    fsFaktoj = fsPerso.facts.copy()
    for grFakto in grFaktoj :
      if int(grFakto.get_role()) != EventRoleType.PRIMARY:
        continue
      event = self.dbstate.db.get_event_from_handle(grFakto.ref)
      if event.type == EventType.BIRTH or event.type == EventType.DEATH or event.type == EventType.BAPTISM or event.type == EventType.BURIAL :
        continue
      titolo = str(EventType(event.type))
      grFaktoPriskribo = event.description or ''
      grFaktoDato = grdato_al_formal(event.date)
      if event.place and event.place != None :
        place = self.dbstate.db.get_place_from_handle(event.place)
        grFaktoLoko = place.name.value
      else :
        grFaktoLoko = ''
      # FARINDAĴO : norma loknomo
      if grFaktoLoko == '' :
        grValoro = grFaktoPriskribo
      else :
        grValoro = grFaktoPriskribo +' @ '+ grFaktoLoko
      coloro="orange"
      fsFaktoDato = ''
      fsFaktoLoko = ''
      fsFaktoPriskribo = ''
      for fsFakto in fsFaktoj :
        gedTag = FACT_TAGS.get(fsFakto.type) or fsFakto.type
        if not gedTag :
          continue
        grTag = PERSONALCONSTANTEVENTS.get(int(event.type), "").strip() or event.type
        if gedTag != grTag :
          continue
        fsFaktoDato = fsFakto.date or ''
        if (fsFaktoDato != grFaktoDato) :
          fsFaktoDato = ''
          continue
        fsFaktoLoko = fsFakto.place or ''
        fsFaktoPriskribo = fsFakto.value or ''
        coloro = "green"
        fsFaktoj.remove(fsFakto)
        break
      if fsFaktoLoko == '' :
        fsValoro = fsFaktoPriskribo
      else :
        fsValoro = fsFaktoPriskribo +' @ '+ fsFaktoLoko
      self.modelKomp.add( ( coloro , titolo
		, grFaktoDato , grValoro
		, fsFaktoDato , fsValoro
		) )
    coloro = "yellow"
    for fsFakto in fsFaktoj :
      if fsFakto.type == "http://gedcomx.org/Birth" or fsFakto.type == "http://gedcomx.org/Baptism" or fsFakto.type == "http://gedcomx.org/Death" or fsFakto.type == "http://gedcomx.org/Burial" :
        continue
      gedTag = FACT_TAGS.get(fsFakto.type) or fsFakto.type
      evtType = GED_TO_GRAMPS_EVENT.get(gedTag) 
      if evtType :
        titolo = str(EventType(evtType))
      else :
        titolo = gedTag
      fsFaktoDato = fsFakto.date or ''
      fsFaktoLoko = fsFakto.place or ''
      fsFaktoPriskribo = fsFakto.value or ''
      if fsFaktoLoko == '' :
        fsValoro = fsFaktoPriskribo
      else :
        fsValoro = fsFaktoPriskribo +' @ '+ fsFaktoLoko
      self.modelKomp.add( ( coloro , titolo
		, '' , ''
		, fsFaktoDato , fsValoro
		) )
    return

  def aldGepKomp(self, person, fsPerso ) :
    """
    " aldonas gepatran komparon
    """
    family_handle = person.get_main_parents_family_handle()
    father = None
    father_name = ''
    mother = None
    mother_name = ''
    if family_handle:
      family = self.dbstate.db.get_family_from_handle(family_handle)
      handle = family.get_father_handle()
      if handle:
        father = self.dbstate.db.get_person_from_handle(handle)
        father_name = name_displayer.display(father)
      handle = family.get_mother_handle()
      if handle:
        mother = self.dbstate.db.get_person_from_handle(handle)
        mother_name = name_displayer.display(mother)

    if len(fsPerso.parents) > 0 :
      fs_parents = next(iter(fsPerso.parents))
      fsfather_id = fs_parents[0] or ''
      fsmother_id = fs_parents[1] or ''
      PersonFS.fs_Tree.add_indis([fsfather_id,fsmother_id])
      fsFather = PersonFS.fs_Tree.indi.get(fsfather_id)
      if fsFather and fsFather.name :
        fs_father_name = fsFather.name.surname + ', ' + fsFather.name.given
      else :
        fs_father_name = ''
      fsMother = PersonFS.fs_Tree.indi.get(fsmother_id)
      if fsMother and fsMother.name :
        fs_mother_name = fsMother.name.surname + ', ' + fsMother.name.given
      else :
        fs_mother_name = ''
    else :
      fsfather_id = ''
      fsmother_id = ''
      fsFather = None
      fsMother = None
      fs_father_name = ''
      fs_mother_name = ''
    fatherFsid = getfsid(father)
    motherFsid = getfsid(mother)
    coloro = "orange"
    if (fatherFsid == fsfather_id) :
      coloro = "green"
    self.modelKomp.add( ( coloro , _trans.gettext('Father')
		, self.grperso_datoj(father) , ' ' + father_name + ' [' + fatherFsid  + ']'
		, self.fsperso_datoj(fsFather) , fs_father_name + ' [' + fsfather_id + ']'
		) )
    coloro = "orange"
    if (motherFsid == fsmother_id) :
      coloro = "green"
    self.modelKomp.add( ( coloro , _trans.gettext('Mother')
		, self.grperso_datoj(mother) , ' ' + mother_name + ' [' + motherFsid + ']'
		, self.fsperso_datoj(fsMother) , fs_mother_name + ' [' + fsmother_id + ']'
		) )
    return

  def aldEdzKomp(self, person, fsPerso, fsid) :
    """
    " aldonas edzan komparon
    """
    grFamilioj = person.get_family_handle_list()
    fsEdzoj = fsPerso.spouses.copy()
    fsInfanoj = fsPerso.children.copy()
    
    for family_handle in person.get_family_handle_list():
      family = self.dbstate.db.get_family_from_handle(family_handle)
      if family :
        edzo_handle = family.mother_handle
        if edzo_handle == self.get_active('Person') :
          edzo_handle = family.father_handle
        if edzo_handle :
          edzo = self.dbstate.db.get_person_from_handle(edzo_handle)
        else :
          edzo = Person()
        edzoNomo = edzo.primary_name
        edzoFsid = getfsid(edzo)
        fsEdzoId = ''
        for fsEdzTrio in fsEdzoj :
          if fsEdzTrio[0] == edzoFsid :
            fsEdzoId = fsEdzTrio[0]
            fsEdzoj.remove(fsEdzTrio)
            break
          elif fsEdzTrio[1] == edzoFsid :
            fsEdzoId = fsEdzTrio[1]
            fsEdzoj.remove(fsEdzTrio)
            break
        
        coloro = "orange"
        if fsEdzoId != '' and edzoFsid == fsEdzoId :
          coloro = "green"
        fsEdzo = PersonFS.fs_Tree.indi.get(fsEdzoId)
        if fsEdzo :
          fsNomo = fsEdzo.name
        else :
          fsNomo = fsName()
        self.modelKomp.add( ( coloro , _trans.gettext('Spouse')
                  , self.grperso_datoj(edzo) , edzoNomo.get_primary_surname().surname + ', ' + edzoNomo.first_name + ' [' + edzoFsid + ']'
		  , self.fsperso_datoj(fsEdzo) , fsNomo.surname +  ', ' + fsNomo.given  + ' [' + fsEdzoId  + ']'
             ) )
        # familiaj eventoj (edziĝo, …)
        if fsEdzTrio :
          fsFamilio = self.fs_Tree.fam[(fsEdzTrio[0], fsEdzTrio[1])]
          fsFaktoj = fsFamilio.facts.copy()
          for eventref in family.get_event_ref_list() :
            event = self.dbstate.db.get_event_from_handle(eventref.ref)
            titolo = str(EventType(event.type))
            grFaktoPriskribo = event.description or ''
            grFaktoDato = grdato_al_formal(event.date)
            if event.place and event.place != None :
              place = self.dbstate.db.get_place_from_handle(event.place)
              grFaktoLoko = place.name.value
            else :
              grFaktoLoko = ''
            # FARINDAĴO : norma loknomo
            if grFaktoLoko == '' :
              grValoro = grFaktoPriskribo
            else :
              grValoro = grFaktoPriskribo +' @ '+ grFaktoLoko
            coloro="orange"
            fsFaktoDato = ''
            fsFaktoLoko = ''
            fsFaktoPriskribo = ''
            for fsFakto in fsFaktoj :
              gedTag = FACT_TAGS.get(fsFakto.type) or fsFakto.type
              grTag = FAMILYCONSTANTEVENTS.get(int(event.type), "").strip() or event.type
              if gedTag != grTag :
                continue
              fsFaktoDato = fsFakto.date or ''
              if (fsFaktoDato == grFaktoDato) :
                coloro = "green"
              fsFaktoLoko = fsFakto.place or ''
              fsFaktoPriskribo = fsFakto.value or ''
              fsFaktoj.remove(fsFakto)
              break
            if fsFaktoLoko == '' :
              fsValoro = fsFaktoPriskribo
            else :
              fsValoro = fsFaktoPriskribo +' @ '+ fsFaktoLoko
            self.modelKomp.add( ( coloro , ' '+titolo
    		  , grFaktoDato , grValoro
    		  , fsFaktoDato , fsValoro
    		  ) )
        coloro = "yellow"
        for fsFakto in fsFaktoj :
          gedTag = FACT_TAGS.get(fsFakto.type) or fsFakto.type
          evtType = GED_TO_GRAMPS_EVENT.get(gedTag) 
          if evtType :
            titolo = str(EventType(evtType))
          else :
            titolo = gedTag
          fsFaktoDato = fsFakto.date or ''
          fsFaktoLoko = fsFakto.place or ''
          fsFaktoPriskribo = fsFakto.value or ''
          if fsFaktoLoko == '' :
            fsValoro = fsFaktoPriskribo
          else :
            fsValoro = fsFaktoPriskribo +' @ '+ fsFaktoLoko
          self.modelKomp.add( ( coloro , ' '+titolo
		, '' , ''
		, fsFaktoDato , fsValoro
		) )
          
        for child_ref in family.get_child_ref_list():
          infano = self.dbstate.db.get_person_from_handle(child_ref.ref)
          infanoNomo = infano.primary_name
          infanoFsid = getfsid(infano)
          fsInfanoId = ''
          for fsTrio in fsInfanoj :
            if (  (fsTrio[0] == fsid and fsTrio[1] == fsEdzoId and fsTrio[2] == infanoFsid)
                or (fsTrio[0] == fsEdzoId and fsTrio[1] == fsid and fsTrio[2] == infanoFsid)) :
              fsInfanoId = fsTrio[2]
              fsInfanoj.remove(fsTrio)
              break
          coloro = "orange"
          if fsInfanoId != '' and fsInfanoId == infanoFsid :
            coloro = "green"
          fsInfano = PersonFS.fs_Tree.indi.get(fsInfanoId)
          if fsInfano :
            fsNomo = fsInfano.name
          else :
            fsNomo = fsName()
          self.modelKomp.add( ( coloro ,'    '+ _trans.gettext('Child')
                  , self.grperso_datoj(infano) , infanoNomo.get_primary_surname().surname + ', ' + infanoNomo.first_name + ' [' + infanoFsid + ']'
                  , self.fsperso_datoj(fsInfano), fsNomo.surname +  ', ' + fsNomo.given + ' [' + fsInfanoId + ']'
             ) )
        toRemove=set()
        for fsTrio in fsInfanoj :
          if (  (fsTrio[0] == fsid and fsTrio[1] == fsEdzoId )
                or (fsTrio[0] == fsEdzoId and fsTrio[1] == fsid )) :
              fsInfanoId = fsTrio[2]
              coloro = "orange"
              fsInfano = PersonFS.fs_Tree.indi.get(fsInfanoId)
              if fsInfano :
                fsNomo = fsInfano.name
              else :
                fsNomo = fsName()
              self.modelKomp.add( ( coloro ,'    '+ _trans.gettext('Child')
                  , '', ''
                  , self.fsperso_datoj(fsInfano), fsNomo.surname +  ', ' + fsNomo.given + ' [' + fsInfanoId + ']'
                 ) )
              toRemove.add(fsTrio)
        for fsTrio in toRemove :
          fsInfanoj.remove(fsTrio)
    coloro = "orange"
    for fsEdzTrio in fsEdzoj :
      if fsEdzTrio[0] == fsid :
        fsEdzoId = fsEdzTrio[1]
      else :
        fsEdzoId = fsEdzTrio[0]
      fsEdzo = PersonFS.fs_Tree.indi.get(fsEdzoId)
      if fsEdzo :
        fsNomo = fsEdzo.name
      else :
        fsNomo = fsName()
      self.modelKomp.add( ( coloro , _trans.gettext('Spouse')
                  , '', ''
		  , self.fsperso_datoj(fsEdzo) , fsNomo.surname +  ', ' + fsNomo.given  + ' [' + fsEdzoId  + ']'
             ) )
      toRemove=set()
      for fsTrio in fsInfanoj :
        if (  (fsTrio[0] == fsid and fsTrio[1] == fsEdzoId )
                or (fsTrio[0] == fsEdzoId and fsTrio[1] == fsid )) :
              fsInfanoId = fsTrio[2]
              fsInfano = PersonFS.fs_Tree.indi.get(fsInfanoId)
              if fsInfano :
                fsNomo = fsInfano.name
              else :
                fsNomo = fsName()
              self.modelKomp.add( ( coloro ,'    '+ _trans.gettext('Child')
                  , '', ''
                  , self.fsperso_datoj(fsInfano), fsNomo.surname +  ', ' + fsNomo.given + ' [' + fsInfanoId + ']'
                ) )
              toRemove.add(fsTrio)
      for fsTrio in toRemove :
        fsInfanoj.remove(fsTrio)
    for fsTrio in fsInfanoj :
      fsInfanoId = fsTrio[2]
      fsInfano = PersonFS.fs_Tree.indi.get(fsInfanoId)
      if fsInfano :
        fsNomo = fsInfano.name
      else :
        fsNomo = fsName()
      self.modelKomp.add( ( coloro ,_trans.gettext('Child')
                  , '', ''
                  , self.fsperso_datoj(fsInfano), fsNomo.surname +  ', ' + fsNomo.given + ' [' + fsInfanoId + ']'
             ) )
    return

  def kompariFs(self, person_handle, getfs):
    """
    " Komparas gramps kaj FamilySearch
    """
    self._db_create_schema()
    self.FSID = None
    person = self.dbstate.db.get_person_from_handle(person_handle)
    fsid = getfsid(person)
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
    if PersonFS.fs_Session == None or not PersonFS.fs_Session.logged:
      return
    #
    self._db_get(person_handle)
    self.db_fsid = fsid
    PersonFS.FSID = fsid
    # ŝarĝante individuan "FamilySearch" :
    PersonFS.fs_Tree.add_indis([fsid])
    fsPerso = PersonFS.fs_Tree.indi.get(fsid) or Indi()
    if getfs == True :
      PersonFS.fs_Tree.add_spouses([fsid])
      PersonFS.fs_Tree.add_children([fsid])


    fsPerso.konf = self.aldNomojKomp( person, fsPerso)
    self.aldSeksoKomp( person, fsPerso)

    fsPerso.konf_birdo =  self.aldFaktoKomp( person, fsPerso, EventType.BIRTH , "http://gedcomx.org/Birth") 
    fsPerso.konf = (self.aldFaktoKomp( person, fsPerso, EventType.BAPTISM , "http://gedcomx.org/Baptism") and fsPerso.konf)
    fsPerso.konf_morto = self.aldFaktoKomp( person, fsPerso, EventType.DEATH , "http://gedcomx.org/Death")
    fsPerso.konf = (self.aldFaktoKomp( person, fsPerso, EventType.BURIAL , "http://gedcomx.org/Burial") and fsPerso.konf)
    fsPerso.konf = (fsPerso.konf and fsPerso.konf_esenco)

    fsPerso.konf = (self.aldGepKomp( person, fsPerso) and fsPerso.konf)

    fsPerso.konf = (self.aldEdzKomp( person, fsPerso, fsid) and fsPerso.konf)

    fsPerso.konf = (self.aldAliajFaktojKomp( person, fsPerso) and fsPerso.konf)

    self.db_konf_esenco = (fsPerso.konf_sekso and fsPerso.konf_birdo and fsPerso.konf_morto) 
    self.db_konf = fsPerso.konf
    self.db_gramps_datomod = person.change

    # FARINDAĴOJ : db_datoj : db_…

    # FARINDAĴOJ : «tags»

    # FARINDAĴOJ : fontoj, notoj, memoroj, attributoj …

    self._db_commit(person_handle)
    return

  # FARINDAĴOJ : kopii, redundoj, esploro, …
