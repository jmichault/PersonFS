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

import email.utils
import time

from gramps.gui.plug import MenuToolOptions, PluginWindows
from gramps.gen.plug.menu import FilterOption, TextOption, NumberOption, BooleanOption
from gramps.gen.db import DbTxn
from gramps.gui.dialog import OkDialog, WarningDialog
from gramps.gen.filters import CustomFilters, GenericFilterFactory, rules
from gramps.gen.lib import EventRoleType, EventType, Person

from gramps.plugins.lib.libgedcom import PERSONALCONSTANTEVENTS, FAMILYCONSTANTEVENTS, GED_TO_GRAMPS_EVENT

from gramps.gen.const import GRAMPS_LOCALE as glocale
try:
    _trans = glocale.get_addon_translator(__file__)
except ValueError:
    _trans = glocale.translation
_ = _trans.gettext

import gedcomx

import PersonFS
import fs_db
import tree
from constants import FACT_TAGS, FACT_TYPES
from utila import getfsid, get_grevent, get_fsfact, grdato_al_formal

class FSKomparoOpcionoj(MenuToolOptions):

  def __init__(self, name, person_id=None, dbstate=None):
    self.db = dbstate.get_database()
    MenuToolOptions.__init__(self, name, person_id, dbstate)

  def add_menu_options(self, menu):
    self.__general_options(menu)

  def __general_options(self, menu):
    category_name = _("FamilySearch Komparo Opcionoj")
    self.__gui_tagoj = NumberOption(_("Nombro tagoj"), 0, 0, 99) 
    self.__gui_tagoj.set_help(_("Nombro da tagoj inter du komparoj"))
    menu.add_option(category_name, "gui_tagoj", self.__gui_tagoj)

    self.__gui_deviga = BooleanOption(_("Devigi komparo"), True) 
    self.__gui_deviga.set_help(_("Kompari sendepende de la nombro da tagoj."))
    menu.add_option(category_name, "gui_deviga", self.__gui_deviga)

    all_persons = rules.person.Everyone([])
    self.__gui_filter_name = FilterOption(_("Person Filter"), 0)
    menu.add_option(category_name,'Person', self.__gui_filter_name)
    # custom filter:
    filter_list = CustomFilters.get_filters('Person')
    # generic filter:
    GenericFilter = GenericFilterFactory('Person')
    all_filter = GenericFilter()
    all_filter.set_name(_("All %s") % (_("Persons")))
    all_filter.add_rule(all_persons)
    # only add the generic filter if it isn't already in the menu
    all_filter_in_list = False
    for fltr in filter_list:
        if fltr.get_name() == all_filter.get_name():
            all_filter_in_list = True
    if not all_filter_in_list:
        filter_list.insert(0, all_filter)
    self.__gui_filter_name.set_filters(filter_list)

class FSKomparo(PluginWindows.ToolManagedWindowBatch):

  def get_title(self):
    return _("FamilySearch Komparo")

  def initial_frame(self):
    return _("Options")

  def run(self):
    if not PersonFS.PersonFS.aki_sesio():
      WarningDialog(_('Ne konektita al FamilySearch'))
      return
    if not PersonFS.PersonFS.fs_Tree:
      PersonFS.PersonFS.fs_Tree = tree.Tree()
      PersonFS.PersonFS.fs_Tree._getsources = False
    self.db = self.dbstate.get_database()
    # krei datumbazan tabelon
    fs_db.create_schema(self.db)
    filter_ = self.options.menu.get_option_by_name('Person').get_filter()
    self.plist = set(filter_.apply(self.db, self.db.iter_person_handles()))
    pOrdList = list()
    for handle in self.plist:
      person = self.db.get_person_from_handle(handle)
      fsid = getfsid(person)
      if(fsid == ''): continue
      self.db.dbapi.execute("select stat_dato from personfs_stato where p_handle=?",[handle])
      datumoj = self.db.dbapi.fetchone()
      if datumoj and datumoj[0]:
        pOrdList.append([datumoj[0],handle,fsid])
      else:
        pOrdList.append([0,handle,fsid])
    def akiUnua(ero):
      return ero[0]
    pOrdList.sort(key=akiUnua)
    for paro in pOrdList:
      print (paro)
      fsid = paro[2]
      fsPersono = None
      datemod = None
      etag = None
      if fsid in PersonFS.PersonFS.fs_Tree._persons:
        fsPersono = PersonFS.PersonFS.fs_Tree._persons.get(fsid)
      if not fsPersono or not hasattr(fsPersono,'_last_modified') or not fsPersono._last_modified :
        mendo = "/platform/tree/persons/"+fsid
        r = tree._FsSeanco.head_url(
                    mendo 
                )
        datemod = int(time.mktime(email.utils.parsedate(r.headers['Last-Modified'])))
        etag = r.headers['Etag']
        PersonFS.PersonFS.fs_Tree.add_persons([fsid])
      fsPersono = PersonFS.PersonFS.fs_Tree._persons.get(fsid)
      if not fsPersono :
        print (_('FS ID %s ne trovita') % (fsid))
        continue
      fsPersono._datemod = datemod
      fsPersono._etag = etag
      grPersono = self.db.get_person_from_handle(paro[1])
      kompariFsGr(fsPersono,grPersono,self.db)

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
  if (grSekso == fsSekso) :
    coloro = "green"
  return ( coloro , _('Sekso:')
		, '', grSekso
		, '', fsSekso
		) 

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
    return None
  return ( coloro , titolo
		, grFaktoDato , grFaktoLoko
		, fsFaktoDato , fsFaktoLoko
		)

def NomojKomp(person, fsPerso ) :
    grNomo = person.primary_name
    fsNomo = fsPerso.akPrefNomo()
    coloro = "orange"
    if (grNomo.get_primary_surname().surname == fsNomo.akSurname()) and (grNomo.first_name == fsNomo.akGiven()) :
      coloro = "green"
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

def grperso_datoj (db, person) :
  if not person:
    return ''
  grBirth = get_grevent(db, person, EventType(EventType.BIRTH))
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
  grDeath = get_grevent(db, person, EventType(EventType.DEATH))
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

def fsperso_datoj (db, fsPerso) :
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

def aldGepKomp(db, grPersono, fsPersono ) :
  """
  " aldonas gepatran komparon
  """
  family_handle = grPersono.get_main_parents_family_handle()
  father = None
  father_name = ''
  mother = None
  mother_name = ''
  res = list()
  if family_handle:
    family = db.get_family_from_handle(family_handle)
    handle = family.get_father_handle()
    if handle:
      father = db.get_person_from_handle(handle)
      father_name = name_displayer.display(father)
    handle = family.get_mother_handle()
    if handle:
      mother = db.get_person_from_handle(handle)
      mother_name = name_displayer.display(mother)

  if len(fsPersono._gepatroj) > 0 :
    parents_ids = set()
    for paro in fsPersono._gepatroj:
      parents_ids.add(paro.person1.resourceId)
      parents_ids.add(paro.person2.resourceId)
    PersonFS.PersonFS.fs_Tree.add_persons(parents_ids)
    fsfather_id = ''
    fsFather = None
    fsmother_id = ''
    fsMother = None
    for fsid in parents_ids :
      fs2 = gedcomx.Person._indekso.get(fsid) or gedcomx.Person()
      if fs2.gender and fs2.gender.type == "http://gedcomx.org/Male" :
        fsfather_id = fsid
        fsFather = fs2
      elif fs2.gender and fs2.gender.type == "http://gedcomx.org/Female" :
        fsmother_id = fsid
        fsMother = fs2
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
  res.append ( ( coloro , _trans.gettext('Father')
		, grperso_datoj(db, father) , ' ' + father_name + ' [' + fatherFsid  + ']'
		, fsperso_datoj(db, fsFather) , fs_father_name + ' [' + fsfather_id + ']'
		) )
  coloro = "orange"
  if (motherFsid == fsmother_id) :
    coloro = "green"
  res.append( ( coloro , _trans.gettext('Mother')
		, grperso_datoj(db, mother) , ' ' + mother_name + ' [' + motherFsid + ']'
		, fsperso_datoj(db, fsMother) , fs_mother_name + ' [' + fsmother_id + ']'
		) )
  return res

def aldEdzKomp(db, person, fsPerso) :
  """
  " aldonas edzan komparon
  """
  grFamilioj = person.get_family_handle_list()
  fsEdzoj = fsPerso._paroj.copy()
  fsInfanoj = fsPerso._infanojCP.copy()
  fsid = fsPerso.id
  res = list()
  
  for family_handle in person.get_family_handle_list():
    family = db.get_family_from_handle(family_handle)
    if family :
      edzo_handle = family.mother_handle
      if edzo_handle == person.handle :
        edzo_handle = family.father_handle
      if edzo_handle :
        edzo = db.get_person_from_handle(edzo_handle)
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
      fsEdzo = PersonFS.PersonFS.fs_Tree._persons.get(fsEdzoId) or gedcomx.Person()
      fsNomo = fsEdzo.akPrefNomo()
      res.append( ( coloro , _trans.gettext('Spouse')
                , grperso_datoj(db, edzo) , edzoNomo.get_primary_surname().surname + ', ' + edzoNomo.first_name + ' [' + edzoFsid + ']'
		  , fsperso_datoj(db, fsEdzo) , fsNomo.akSurname() +  ', ' + fsNomo.akGiven()  + ' [' + fsEdzoId  + ']'
           ) )
      # familiaj eventoj (edziĝo, …)
      fsFamilio = None
      fsFaktoj = set()
      if fsEdzTrio :
        fsFamilio = self.fs_Tree._fam[(fsEdzTrio[0], fsEdzTrio[1])]
        fsFaktoj = fsFamilio.facts.copy()
        for eventref in family.get_event_ref_list() :
          event = db.get_event_from_handle(eventref.ref)
          titolo = str(EventType(event.type))
          grFaktoPriskribo = event.description or ''
          grFaktoDato = grdato_al_formal(event.date)
          if event.place and event.place != None :
            place = db.get_place_from_handle(event.place)
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
          res.append( ( coloro , ' '+titolo
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
        res.append( ( coloro , ' '+titolo
		, '' , ''
		, fsFaktoDato , fsValoro
		) )
        
      for child_ref in family.get_child_ref_list():
        infano = db.get_person_from_handle(child_ref.ref)
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
        fsInfano = PersonFS.PersonFS.fs_Tree._persons.get(fsInfanoId) or gedcomx.Person()
        fsNomo = fsInfano.akPrefNomo()
        res.append( ( coloro ,'    '+ _trans.gettext('Child')
                , grperso_datoj(db, infano) , infanoNomo.get_primary_surname().surname + ', ' + infanoNomo.first_name + ' [' + infanoFsid + ']'
                , fsperso_datoj(db, fsInfano), fsNomo.akSurname() +  ', ' + fsNomo.akGiven() + ' [' + fsInfanoId + ']'
           ) )
      toRemove=set()
      for triopo in fsInfanoj :
        if (  (triopo.parent1.resourceId == fsid and triopo.parent2.resourceId == fsEdzoId )
              or  (triopo.parent2.resourceId == fsid and triopo.parent1.resourceId == fsEdzoId )) :
            fsInfanoId = triopo.child.resourceId
            coloro = "orange"
            fsInfano = PersonFS.PersonFS.fs_Tree._persons.get(fsInfanoId)
            if fsInfano :
              fsNomo = fsInfano.akPrefNomo()
            else :
              fsNomo = gedcomx.Name()
            res.append( ( coloro ,'    '+ _trans.gettext('Child')
                , '', ''
                , fsperso_datoj(db, fsInfano), fsNomo.akSurname() +  ', ' + fsNomo.akGiven() + ' [' + fsInfanoId + ']'
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
    fsEdzo = PersonFS.PersonFS.fs_Tree._persons.get(fsEdzoId)
    if fsEdzo :
      fsNomo = fsEdzo.akPrefNomo()
    else :
      fsNomo = gedcomx.Name()
    res.append( ( coloro , _trans.gettext('Spouse')
                , '', ''
		  , fsperso_datoj(db, fsEdzo) , fsNomo.akSurname() +  ', ' + fsNomo.akGiven()  + ' [' + fsEdzoId  + ']'
           ) )
    toRemove=set()
    for triopo in fsInfanoj :
      if (  (triopo.parent1.resourceId == fsid and triopo.parent2.resourceId == fsEdzoId )
              or  (triopo.parent2.resourceId == fsid and triopo.parent1.resourceId == fsEdzoId )) :
        fsInfanoId = triopo.child.resourceId
        fsInfano = PersonFS.PersonFS.fs_Tree._persons.get(fsInfanoId)
        if fsInfano :
          fsNomo = fsInfano.akPrefNomo()
        else :
          fsNomo = gedcomx.Name()
        res.append( ( coloro ,'    '+ _trans.gettext('Child')
                , '', ''
                , fsperso_datoj(db, fsInfano), fsNomo.akSurname() +  ', ' + fsNomo.akGiven() + ' [' + fsInfanoId + ']'
              ) )
        toRemove.add(triopo)
    for triopo in toRemove :
      fsInfanoj.remove(triopo)
  for triopo in fsInfanoj :
    fsInfanoId = triopo.child.resourceId
    fsInfano = PersonFS.PersonFS.fs_Tree._persons.get(fsInfanoId)
    if fsInfano :
      fsNomo = fsInfano.akPrefNomo()
    else :
      fsNomo = gedcomx.Name()
    res.append( ( coloro ,_trans.gettext('Child')
                , '', ''
                , fsperso_datoj(db, fsInfano), fsNomo.akSurname() +  ', ' + fsNomo.akGiven() + ' [' + fsInfanoId + ']'
           ) )
  return res

def aldAliajFaktojKomp(db, person, fsPerso ) :
  grFaktoj = person.event_ref_list
  fsFaktoj = fsPerso.facts.copy()
  res = list()
  for grFakto in grFaktoj :
    if int(grFakto.get_role()) != EventRoleType.PRIMARY:
      continue
    event = db.get_event_from_handle(grFakto.ref)
    if event.type == EventType.BIRTH or event.type == EventType.DEATH or event.type == EventType.BAPTISM or event.type == EventType.BURIAL :
      continue
    titolo = str(EventType(event.type))
    grFaktoPriskribo = event.description or ''
    grFaktoDato = grdato_al_formal(event.date)
    if event.place and event.place != None :
      place = db.get_place_from_handle(event.place)
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
    res.append( ( coloro , titolo
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
    res.append( ( coloro , titolo
		, '' , ''
		, fsFaktoDato , fsValoro
		) )
  return res

def kompariFsGr(fsPersono,grPersono,db,model=None):
  fs_db.create_schema(db)
  dbPersono= fs_db.db_stato(db,grPersono.handle)
  dbPersono.get()
  if (model == None and hasattr(fsPersono,'_datmod')
      and dbPersono.stat_dato > fsPersono._datmod
      and dbPersono.stat_dato > grPersono.change):
    return
  dbPersono.fsid = fsPersono.id
  FS_Familio=FS_Esenco=FS_Nomo=FS_Fakto=FS_Gepatro=False
  res = SeksoKomp(grPersono, fsPersono)
  if(model) :  model.add( res )
  if res and res[0] != "green" : FS_Esenco = True
  res = NomojKomp(grPersono, fsPersono)
  for linio in res:
    if linio[0] != "green" : FS_Nomo = True
    if model:
       model.add( linio)
  if res and res[0][0] != "green" : FS_Esenco = True

  res = FaktoKomp(db, grPersono, fsPersono, EventType.BIRTH , "http://gedcomx.org/Birth") 
  if res and res[0] != "green" : FS_Esenco = True
  res = FaktoKomp(db, grPersono, fsPersono, EventType.BAPTISM , "http://gedcomx.org/Baptism")
  if res and res[0][0] != "green" : FS_Fakto = True
  if model and res: model.add(res)
  res = FaktoKomp(db, grPersono, fsPersono, EventType.DEATH , "http://gedcomx.org/Death") 
  if res and res[0] != "green" : FS_Esenco = True
  res = FaktoKomp(db, grPersono, fsPersono, EventType.BURIAL , "http://gedcomx.org/Burial")
  if res and res[0][0] != "green" : FS_Fakto = True
  if model and res: model.add(res)

  res = aldGepKomp(db, grPersono, fsPersono)
  FS_Gepatro=False
  for linio in res:
    if linio[0] != "green" : FS_Gepatro = True
    if model:
       model.add( linio)

  res = aldEdzKomp(db, grPersono, fsPersono)
  for linio in res:
    if linio[0] != "green" : FS_Familio = True
    if model:
       model.add( linio)
  res = aldAliajFaktojKomp(db, grPersono, fsPersono)
  for linio in res:
    if linio[0] != "green" : FS_Fakto = True
    if model:
       model.add( linio)

  if not hasattr(fsPersono,'_last_modified') or not fsPersono._last_modified :
    mendo = "/platform/tree/persons/"+fsPersono.id
    r = tree._FsSeanco.head_url(
                    mendo 
                )
    fsPersono._last_modified = int(time.mktime(email.utils.parsedate(r.headers['Last-Modified'])))
    fsPersono._etag = r.headers['Etag']
  FS_Identa = not( FS_Familio or FS_Esenco or FS_Nomo or FS_Fakto or FS_Gepatro )
  with DbTxn(_("FamilySearch tags"), db) as txn:
    # «tags»
    for t in fs_db.stato_tags:
      val = locals().get(t[0])
      if val == None : continue
      print("tag "+t[0]+" ; val="+str(val))
      tag_fs = db.get_tag_from_name(t[0])
      if not val and tag_fs.handle in grPersono.tag_list:
        grPersono.remove_tag(tag_fs.handle)
      if tag_fs and val and tag_fs.handle not in grPersono.tag_list:
        grPersono.add_tag(tag_fs.handle)
    db.commit_person(grPersono, txn)
    dbPersono.stat_dato = int(time.time())
    if FS_Identa:
      dbPersono.konf_dato = dbPersono.stat_dato
    dbPersono.gramps_datomod = grPersono.change
    dbPersono.fs_datomod = fsPersono._last_modified
    dbPersono.konf_esenco = not FS_Esenco
    dbPersono.commit(txn)

  # FARINDAĴOJ : fontoj, notoj, memoroj, attributoj …

