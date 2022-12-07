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

# lokaloj 
from constants import FACT_TAGS, FACT_TYPES
from tree import Tree

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

def get_fsfact(self, person, fact_tipo):
  """
  " Liveras la unuan familysearch fakton de la donita tipo.
  """
  for fact in person.facts :
    if fact.type == fact_tipo :
      return fact
  return None

def get_grevent(db, person, event_type):
  """
  " Liveras la unuan gramps eventon de la donita tipo.
  """
  if not person:
    return None
  for event_ref in person.get_event_ref_list():
    if int(event_ref.get_role()) == EventRoleType.PRIMARY:
      event = db.get_event_from_handle(event_ref.ref)
      if event.get_type() == event_type:
        return event
  return None


def NomojKomp(person, fsPerso ) :
    grNomo = person.primary_name
    fsNomo = fsPerso.akPrefNomo()
    coloro = "orange"
    fsPerso.konf_nomo = False
    if (grNomo.get_primary_surname().surname == fsNomo.akSurname()) and (grNomo.first_name == fsNomo.akGiven()) :
      coloro = "green"
      fsPerso.konf_nomo = True
    res = list()
    res.append ( ( coloro , _trans.gettext('Name')
		, '', grNomo.get_primary_surname().surname + ', ' + grNomo.first_name 
		, '', fsNomo.akSurname() +  ', ' + fsNomo.akGiven()
		))
    fsNomoj = fsPerso.names.copy()
    fsNomoj.remove(fsNomo)
    for grNomo in person.alternate_names :
      fsNomo = gedcomx.Name()
      coloro = "yellow"
      for x in fsNomoj :
        if (grNomo.get_primary_surname().surname == x.akSurname()) and (grNomo.first_name == x.akGiven()) :
          fsNomo = x
          coloro = "green"
          fsNomoj.remove(x)
          break
      if coloro != "green" : res = False
      res.append (( coloro , '  ' + _trans.gettext('Name')
		, '', grNomo.get_primary_surname().surname + ', ' + grNomo.first_name 
		, '', fsNomo.akSurname() +  ', ' + fsNomo.akGiven()
		))
    coloro = "yellow"
    for fsNomo in fsNomoj :
      if fsNomo == fsNomo : continue
      res.append (( coloro , '  ' + _trans.gettext('Name')
		, '', ''
		, '', fsNomo.akSurname() +  ', ' + fsNomo.akGiven()
		))
    return res

def SeksoKomp(grPersono, fsPersono ) :
  if grPersono.get_gender() == Person.MALE :
    grSekso = _trans.gettext("male")
  elif grPersono.get_gender() == Person.FEMALE :
    grSekso = _trans.gettext("female")
  else :
    grSekso = _trans.gettext("unknown")
  if fsPersono.gender and fsPersono.gender.type == "http://gedcomx.org/Male" :
    fsSekso = _trans.gettext("male")
  elif fsPersono.gender and fsPersono.gender.type == "http://gedcomx.org/Female" :
    fsSekso = _trans.gettext("female")
  else :
    fsSekso = _trans.gettext("unknown")
  coloro = "orange"
  fsPersono._konf_sekso = False
  if (grSekso == fsSekso) :
    coloro = "green"
    fsPersono._konf_sekso = True
  return ( coloro , _('Sekso:')
		, '', grSekso
		, '', fsSekso
		) 
  return

def FaktoKomp(db, person, fsPerso, grEvent , fsFact ) :
  grFakto = get_grevent(db, person, EventType(grEvent))
  titolo = str(EventType(grEvent))
  if grFakto != None :
    grFaktoDato = grdato_al_formal(grFakto.date)
    if grFakto.place and grFakto.place != None :
      place = db.get_place_from_handle(grFakto.place)
      grFaktoLoko = place.name.value
    else :
      grFaktoLoko = ''
  else :
    grFaktoDato = ''
    grFaktoLoko = ''
  # FARINDAĴO : norma loknomo

  fsFakto = get_fsfact (fsPerso, fsFact )
  fsFaktoDato = ''
  fsFaktoLoko = ''
  if fsFakto and fsFakto.date :
    fsFaktoDato = str(fsFakto.date)
  if fsFakto and fsFakto.place :
    fsFaktoLoko = fsFakto.place.original or ''
  coloro = "orange"
  if (grFaktoDato == fsFaktoDato) :
    coloro = "green"
  if grFaktoDato == '' and grFaktoLoko == '' and fsFaktoDato == '' and fsFaktoLoko == '' :
    return
  return ( coloro , titolo
		, grFaktoDato , grFaktoLoko
		, fsFaktoDato , fsFaktoLoko
		)


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

def getfsid(grPersono) :
  if not grPersono :
    return ''
  for attr in grPersono.get_attribute_list():
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
    if not PersonFS.fs_Session:
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
          #  PersonFS.fs_Session = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, True, False, 2)
          #else :
          PersonFS.fs_Session = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, False, False, 2)
        else :
          print("Vi devas enigi la ID kaj pasvorton")
      else:
        #if self.vorteco >= 3:
        #  PersonFS.fs_Session = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, True, False, 2)
        #else :
        PersonFS.fs_Session = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, False, False, 2)
    return PersonFS.fs_Session

  def _db_create_schema(self):
    # krei datumbazan tabelon
    with DbTxn(_("FamilySearch krei"), self.dbstate.db) as txn:
    if not self.dbstate.db.dbapi.table_exists("personfs_stato"):
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
    if not self.dbstate.db.get_tag_from_name('FS_Esenco'):
      tag = Tag()
      tag.set_name('FS_Esenco')
      tag.set_color('green')

  def _db_commit(self,person_handle):
    with DbTxn(_("FamilySearch commit"), self.dbstate.db) as txn:
      if self.db_handle :
        sql = "UPDATE personfs_stato set fsid=?, estas_radiko=? , stat_dato=?, konf_dato=?, gramps_datomod=?, fs_datomod=?, konf_esenco=?, konf=? where p_handle=? "
        self.dbstate.db.dbapi.execute(sql, [ self.db_fsid, int(self.db_estas_radiko or 0), self.db_stat_dato, self.db_konf_dato, self.db_gramps_datomod, self.db_fs_datomod, int(self.db_konf_esenco or 0), int(self.db_konf or 0), self.db_handle] )
      else :
        self.db_handle = person_handle
        sql = "INSERT INTO personfs_stato(p_handle,fsid,estas_radiko,stat_dato,konf_dato,gramps_datomod,fs_datomod,konf_esenco,konf) VALUES (?,?,?,?,?,?,?,?,?)"
        self.dbstate.db.dbapi.execute(sql, [ self.db_handle, self.db_fsid, int(self.db_estas_radiko or 0), self.db_stat_dato, self.db_konf_dato, self.db_gramps_datomod, self.db_fs_datomod, int(self.db_konf_esenco or 0), int(self.db_konf or 0) ] )

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
      print("konekti")
      PersonFS.fs_Session = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, True, False, 2)
      #PersonFS.fs_Session = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, False, False, 2)
    if not PersonFS.fs_Session.logged:
      return
    if not PersonFS.fs_Tree:
      PersonFS.fs_Tree = Tree(PersonFS.fs_Session)
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
	})

    return self.res

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
    res = self.fs_Tree._fs.post_url( "/platform/tree/persons", jsonpeto )
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

  def SerDupCxangxo(self, dummy):
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

    self.ButLancxi_clicked(None)
    if not PersonFS.fs_TreeSercxo:
      PersonFS.fs_TreeSercxo = Tree(PersonFS.fs_Session)
      PersonFS.fs_TreeSercxo._getsources = False
    self.modelRes.clear()
    mendo = "/platform/tree/persons/"+self.FSID+"/matches"
    r = self.fs_TreeSercxo._fs.get_url(
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
      PersonFS.fs_TreeSercxo = Tree(PersonFS.fs_Session)
      PersonFS.fs_TreeSercxo._getsources = False
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
    datumoj = self.fs_TreeSercxo._fs.get_jsonurl(
                    mendo ,{"Accept": "application/x-gedcomx-atom+json", "Accept-Language": "fr"}
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

  def grperso_datoj (self, person) :
    if not person:
      return ''
    grBirth = get_grevent(self.dbstate.db, person, EventType(EventType.BIRTH))
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
    grDeath = get_grevent(self.dbstate.db, person, EventType(EventType.DEATH))
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
    fsFakto = get_fsfact (fsPerso, 'http://gedcomx.org/Birth' )
    if fsFakto and fsFakto.date and fsFakto.date.formal :
      if fsFakto.date.formal.proksimuma :
        res = '~'
      else :
        res = ' '
      if fsFakto.date.formal.unuaDato :
        res = res + str(fsFakto.date.formal.unuaDato.jaro)
      if fsFakto.date.formal.gamo :
        if fsFakto.date.formal.finalaDato :
          res = res +'/'+ str(fsFakto.date.formal.finalaDato.jaro)
      res = res+'-'
    else :
      res = ' ....-'
    fsFakto = get_fsfact (fsPerso, 'http://gedcomx.org/Death' )
    if fsFakto and fsFakto.date and fsFakto.date.formal:
      if fsFakto.date.formal.proksimuma:
        res = res + '~'
      else :
        res = res + ' '
      if fsFakto.date.formal.unuaDato :
        res = res + str(fsFakto.date.formal.unuaDato.jaro)
      if fsFakto.date.formal.gamo :
        if fsFakto.date.formal.finalaDato and fsFakto.date.formal.finalaDato.jaro:
          res = res +'/'+ str(fsFakto.date.formal.finalaDato.jaro)
        elif fsFakto.date.formal.unuaDato and fsFakto.date.formal.unuaDato.jaro:
          res = res +'/'+ str(fsFakto.date.formal.finalaDato.jaro)
    else :
      res = res + '....'
    return res

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
        if fsFakto.type[:6] == 'data:,':
          gedTag = FACT_TAGS.get(fsFakto.type[6:]) or fsFakto.type[6:]
        else:
          gedTag = FACT_TAGS.get(fsFakto.type) or fsFakto.type
        if not gedTag :
          continue
        grTag = PERSONALCONSTANTEVENTS.get(int(event.type), "").strip() or event.type
        if gedTag != grTag :
          continue
        if fsFakto and fsFakto.date :
          fsFaktoDato = str(fsFakto.date)
        if (fsFaktoDato != grFaktoDato) :
          fsFaktoDato = ''
          continue
        if fsFakto and fsFakto.place :
          fsFaktoLoko = fsFakto.place.original or ''
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
      if fsFakto.type[:6] == 'data:,':
        gedTag = FACT_TAGS.get(fsFakto.type[6:]) or fsFakto.type[6:]
      else:
        gedTag = FACT_TAGS.get(fsFakto.type) or fsFakto.type
      evtType = GED_TO_GRAMPS_EVENT.get(gedTag) 
      if evtType :
        titolo = str(EventType(evtType))
      else :
        titolo = gedTag
      if hasattr(fsFakto,"date"):
        fsFaktoDato = str(fsFakto.date or '')
      else : fsFaktoDato = ""
      if hasattr(fsFakto,"place") and fsFakto.place:
        fsFaktoLoko = fsFakto.place.original or ''
      else : fsFaktoLoko = ""
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

    if len(fsPerso._gepatroj) > 0 :
      parents_ids = set()
      for paro in fsPerso._gepatroj:
        parents_ids.add(paro.person1.resourceId)
      PersonFS.fs_Tree.add_persons(parents_ids)
      fsfather_id = ''
      fsFather = None
      fsMother = None
      fsmother_id = ''
      for fsid in parents_ids :
        fsPersono = gedcomx.Person._indekso.get(fsid) or gedcomx.Person()
        if fsPersono.gender and fsPersono.gender.type == "http://gedcomx.org/Male" :
          fsfather_id = fsid
          fsFather = fsPersono
        elif fsPersono.gender and fsPersono.gender.type == "http://gedcomx.org/Female" :
          fsmother_id = fsid
          fsMother = fsPersono
      if fsFather :
        nomo = fsFather.akPrefNomo()
        fs_father_name = nomo.akSurname() + ', ' + nomo.akGiven()
      else :
        fs_father_name = ''
      if fsMother :
        nomo = fsMother.akPrefNomo()
        fs_mother_name = nomo.akSurname() + ', ' + nomo.akGiven()
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
    fsEdzoj = fsPerso._paroj.copy()
    fsInfanoj = fsPerso._infanojCP.copy()
    
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
        fsEdzTrio = None
        for paro in fsEdzoj :
          if paro.person1.resourceId == edzoFsid :
            fsEdzoId = edzoFsid
            fsEdzoj.remove(paro)
            break
          elif paro.person2.resourceId == edzoFsid :
            fsEdzoId = edzoFsid
            fsEdzoj.remove(paro)
            break
        
        coloro = "orange"
        if fsEdzoId != '' and edzoFsid == fsEdzoId :
          coloro = "green"
        fsEdzo = PersonFS.fs_Tree._persons.get(fsEdzoId) or gedcomx.Person()
        fsNomo = fsEdzo.akPrefNomo()
        self.modelKomp.add( ( coloro , _trans.gettext('Spouse')
                  , self.grperso_datoj(edzo) , edzoNomo.get_primary_surname().surname + ', ' + edzoNomo.first_name + ' [' + edzoFsid + ']'
		  , self.fsperso_datoj(fsEdzo) , fsNomo.akSurname() +  ', ' + fsNomo.akGiven()  + ' [' + fsEdzoId  + ']'
             ) )
        # familiaj eventoj (edziĝo, …)
        fsFamilio = None
        fsFaktoj = set()
        if fsEdzTrio :
          fsFamilio = self.fs_Tree._fam[(fsEdzTrio[0], fsEdzTrio[1])]
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
              fsFaktoDato = str(fsFakto.date or '')
              if (fsFaktoDato == grFaktoDato) :
                coloro = "green"
              fsFaktoLoko = fsFakto.place.original or ''
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
          fsFaktoDato = str(fsFakto.date or '')
          fsFaktoLoko = fsFakto.place.original or ''
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
          for triopo in fsInfanoj :
            if (  (  (triopo.parent1.resourceId == fsid and triopo.parent2.resourceId == fsEdzoId )
                    or  (triopo.parent2.resourceId == fsid and triopo.parent1.resourceId == fsEdzoId ))
                 and triopo.child.resourceId == infanoFsid ) :
              fsInfanoId = infanoFsid
              fsInfanoj.remove(triopo)
              break
          coloro = "orange"
          if fsInfanoId != '' and fsInfanoId == infanoFsid :
            coloro = "green"
          fsInfano = PersonFS.fs_Tree._persons.get(fsInfanoId) or gedcomx.Person()
          fsNomo = fsInfano.akPrefNomo()
          self.modelKomp.add( ( coloro ,'    '+ _trans.gettext('Child')
                  , self.grperso_datoj(infano) , infanoNomo.get_primary_surname().surname + ', ' + infanoNomo.first_name + ' [' + infanoFsid + ']'
                  , self.fsperso_datoj(fsInfano), fsNomo.akSurname() +  ', ' + fsNomo.akGiven() + ' [' + fsInfanoId + ']'
             ) )
        toRemove=set()
        for triopo in fsInfanoj :
          if (  (triopo.parent1.resourceId == fsid and triopo.parent2.resourceId == fsEdzoId )
                or  (triopo.parent2.resourceId == fsid and triopo.parent1.resourceId == fsEdzoId )) :
              fsInfanoId = triopo.child.resourceId
              coloro = "orange"
              fsInfano = PersonFS.fs_Tree._persons.get(fsInfanoId)
              if fsInfano :
                fsNomo = fsInfano.akPrefNomo()
              else :
                fsNomo = gedcomx.Name()
              self.modelKomp.add( ( coloro ,'    '+ _trans.gettext('Child')
                  , '', ''
                  , self.fsperso_datoj(fsInfano), fsNomo.akSurname() +  ', ' + fsNomo.akGiven() + ' [' + fsInfanoId + ']'
                 ) )
              toRemove.add(triopo)
        for triopo in toRemove :
          fsInfanoj.remove(triopo)
    coloro = "orange"
    for paro in fsEdzoj :
      if paro.person1.resourceId == fsid :
        fsEdzoId = paro.person2.resourceId
      else :
        fsEdzoId = paro.person1.resourceId
      fsEdzo = PersonFS.fs_Tree._persons.get(fsEdzoId)
      if fsEdzo :
        fsNomo = fsEdzo.akPrefNomo()
      else :
        fsNomo = gedcomx.Name()
      self.modelKomp.add( ( coloro , _trans.gettext('Spouse')
                  , '', ''
		  , self.fsperso_datoj(fsEdzo) , fsNomo.akSurname() +  ', ' + fsNomo.akGiven()  + ' [' + fsEdzoId  + ']'
             ) )
      toRemove=set()
      for triopo in fsInfanoj :
        if (  (triopo.parent1.resourceId == fsid and triopo.parent2.resourceId == fsEdzoId )
                or  (triopo.parent2.resourceId == fsid and triopo.parent1.resourceId == fsEdzoId )) :
          fsInfanoId = triopo.child.resourceId
          fsInfano = PersonFS.fs_Tree._persons.get(fsInfanoId)
          if fsInfano :
            fsNomo = fsInfano.akPrefNomo()
          else :
            fsNomo = gedcomx.Name()
          self.modelKomp.add( ( coloro ,'    '+ _trans.gettext('Child')
                  , '', ''
                  , self.fsperso_datoj(fsInfano), fsNomo.akSurname() +  ', ' + fsNomo.akGiven() + ' [' + fsInfanoId + ']'
                ) )
          toRemove.add(triopo)
      for triopo in toRemove :
        fsInfanoj.remove(triopo)
    for triopo in fsInfanoj :
      fsInfanoId = triopo.child.resourceId
      fsInfano = PersonFS.fs_Tree._persons.get(fsInfanoId)
      if fsInfano :
        fsNomo = fsInfano.akPrefNomo()
      else :
        fsNomo = gedcomx.Name()
      self.modelKomp.add( ( coloro ,_trans.gettext('Child')
                  , '', ''
                  , self.fsperso_datoj(fsInfano), fsNomo.akSurname() +  ', ' + fsNomo.akGiven() + ' [' + fsInfanoId + ']'
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
    PersonFS.fs_Tree.add_persons([fsid])
    fsPerso = gedcomx.Person._indekso.get(fsid) or gedcomx.Person()
    if getfs == True :
      PersonFS.fs_Tree.add_spouses([fsid])
      PersonFS.fs_Tree.add_children([fsid])

    self.db_konf_esenco = True
    res = NomojKomp( person, fsPerso)
    if res[0][0] != "green" : self.db_konf_esenco = False
    for linio in res:
       self.modelKomp.add( linio)
    res = SeksoKomp( person, fsPerso)
    self.modelKomp.add( res )
    if res[0] != "green" : self.db_konf_esenco = False

    res = FaktoKomp(self.dbstate.db, person, fsPerso, EventType.BIRTH , "http://gedcomx.org/Birth")
    if res[0] != "green" : self.db_konf_esenco = False
    self.modelKomp.add(res)

    res = FaktoKomp(self.dbstate.db, person, fsPerso, EventType.BAPTISM , "http://gedcomx.org/Baptism")
    self.modelKomp.add(res)
    res = FaktoKomp(self.dbstate.db, person, fsPerso, EventType.DEATH , "http://gedcomx.org/Death")
    if res[0] != "green" : self.db_konf_esenco = False
    self.modelKomp.add(res)
    res = FaktoKomp(self.dbstate.db, person, fsPerso, EventType.BURIAL , "http://gedcomx.org/Burial")
    self.modelKomp.add(res)

    fsPerso.konf = (self.aldGepKomp( person, fsPerso) and fsPerso.konf)

    fsPerso.konf = (self.aldEdzKomp( person, fsPerso, fsid) and fsPerso.konf)

    fsPerso.konf = (self.aldAliajFaktojKomp( person, fsPerso) and fsPerso.konf)

    self.db_konf_esenco = (fsPerso._konf_sekso and fsPerso.konf_birdo and fsPerso.konf_morto) 
    self.db_konf = fsPerso.konf
    self.db_gramps_datomod = person.change

    # FARINDAĴOJ : db_datoj : db_…

    # FARINDAĴOJ : «tags»

    # FARINDAĴOJ : fontoj, notoj, memoroj, attributoj …

    self._db_commit(person_handle)
    return

  # FARINDAĴOJ : kopii, redundoj, esploro, …
