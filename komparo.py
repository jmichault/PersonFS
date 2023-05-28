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
from urllib.parse import unquote

from gramps.gen.plug.menu import FilterOption, TextOption, NumberOption, BooleanOption
from gramps.gen.db import DbTxn
from gramps.gen.display.name import displayer as name_displayer
from gramps.gen.display.place import displayer as _pd
from gramps.gen.filters import CustomFilters, GenericFilterFactory, rules
from gramps.gen.lib import Date, EventRoleType, EventType, Person

from gramps.gui.dialog import OkDialog, WarningDialog
from gramps.gui.plug import MenuToolOptions, PluginWindows
from gramps.gui.utils import ProgressMeter

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
import utila
from constants import GEDCOMX_GRAMPS_FAKTOJ

#from objbrowser import browse ;browse(locals())
class FSKomparoOpcionoj(MenuToolOptions):

  def __init__(self, name, person_id=None, dbstate=None):
    #print("KO.init")
    self.db = dbstate.get_database()
    MenuToolOptions.__init__(self, name, person_id, dbstate)

  def add_menu_options(self, menu):
    #print("KO.amo")
    self.__general_options(menu)

  def __general_options(self, menu):
    #print("KO.go")
    category_name = _("FamilySearch Komparo Opcionoj")
    self.__gui_tagoj = NumberOption(_("Nombro tagoj"), 0, 0, 99) 
    self.__gui_tagoj.set_help(_("Nombro da tagoj inter du komparoj"))
    menu.add_option(category_name, "gui_tagoj", self.__gui_tagoj)

    self.__gui_deviga = BooleanOption(_("Devigi komparo"), True) 
    self.__gui_deviga.set_help(_("Kompari sendepende de la nombro da tagoj."))
    menu.add_option(category_name, "gui_deviga", self.__gui_deviga)

    all_persons = rules.person.Everyone([])
    self.__gui_filter_name = FilterOption(_trans.gettext("Person Filter"), 0)
    menu.add_option(category_name,'Person', self.__gui_filter_name)
    # custom filter:
    filter_list = CustomFilters.get_filters('Person')
    # generic filter:
    GenericFilter = GenericFilterFactory('Person')
    all_filter = GenericFilter()
    all_filter.set_name(_trans.gettext("All %s") % (_trans.gettext("Persons")))
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
    #print("K.title")
    return _("FamilySearch Komparo")

  def initial_frame(self):
    #print("K.options")
    return _trans.gettext("Options")

  def run(self):
    #print("K.run")
    if not PersonFS.PersonFS.aki_sesio(self):
      WarningDialog(_('Ne konektita al FamilySearch'))
      return
    progress = ProgressMeter(_("FamilySearch : Komparo"), _trans.gettext('Starting'),
                   can_cancel=True, parent=self.uistate.window)
    self.uistate.set_busy_cursor(True)
    self.dbstate.db.disable_signals()
    if not PersonFS.PersonFS.fs_Tree:
      PersonFS.PersonFS.fs_Tree = tree.Tree()
      PersonFS.PersonFS.fs_Tree._getsources = False
    self.db = self.dbstate.get_database()
    # krei datumbazan tabelon
    fs_db.create_schema(self.db)
    fs_db.create_tags(self.dbstate.db)
    # krei la ordigitan liston de personoj por procesi
    filter_ = self.options.menu.get_option_by_name('Person').get_filter()
    tagoj = self.options.menu.get_option_by_name('gui_tagoj').get_value()
    devigi = self.options.menu.get_option_by_name('gui_deviga').get_value()
    maks_dato = int(time.time()) - tagoj*24*3600
    self.plist = set(filter_.apply(self.db, self.db.iter_person_handles()))
    pOrdList = list()
    progress.set_pass(_('Konstruante la ordigitan liston (1/2)'), len(self.plist))
    print("liste filtrée : "+str(len(self.plist)))
    for handle in self.plist:
      if progress.get_cancelled() :
        self.uistate.set_busy_cursor(False)
        progress.close()
        self.dbstate.db.enable_signals()
        self.dbstate.db.request_rebuild()
        return
      progress.step()
      person = self.db.get_person_from_handle(handle)
      fsid = utila.get_fsftid(person)
      if(fsid == ''): continue
      self.db.dbapi.execute("select stat_dato from personfs_stato where p_handle=?",[handle])
      datumoj = self.db.dbapi.fetchone()
      if datumoj and datumoj[0] :
        if devigi or datumoj[0] < maks_dato :
          pOrdList.append([datumoj[0],handle,fsid])
      else:
        pOrdList.append([0,handle,fsid])
    def akiUnua(ero):
      return ero[0]
    pOrdList.sort(key=akiUnua)
    # procesi
    progress.set_pass(_('Procesante la liston (2/2)'), len(pOrdList))
    print("liste triée : "+str(len(pOrdList)))
    kop_etik = PersonFS.PersonFS.fs_etikedado
    PersonFS.PersonFS.fs_etikedado = True
    import asyncio
    def kompari_paro_p1(paro):
      fsid = paro[2]
      fsPersono = None
      datemod = None
      etag = None
      if fsid in PersonFS.PersonFS.fs_Tree._persons:
        fsPersono = PersonFS.PersonFS.fs_Tree._persons.get(fsid)
      if not fsPersono or not hasattr(fsPersono,'_last_modified') or not fsPersono._last_modified :
        mendo = "/platform/tree/persons/"+fsid
        r = tree._FsSeanco.head_url( mendo )
        while r and r.status_code == 301 and 'X-Entity-Forwarded-Id' in r.headers :
          fsid = r.headers['X-Entity-Forwarded-Id']
          print('kompari_paro_p1 : %s --> %s' % (paro[2],fsid))
          paro[2]=fsid
          mendo = "/platform/tree/persons/"+fsid
          r = tree._FsSeanco.head_url( mendo )
        if r and 'Last-Modified' in r.headers :
          datemod = int(time.mktime(email.utils.parsedate(r.headers['Last-Modified'])))
        if r and 'Etag' in r.headers :
          etag = r.headers['Etag']
        PersonFS.PersonFS.fs_Tree.add_persono(fsid)
        fsPersono = PersonFS.PersonFS.fs_Tree._persons.get(fsid)
      if not fsPersono :
        print (_('FS ID %s ne trovita') % (fsid))
        return
      fsPersono._datemod = datemod
      fsPersono._etag = etag
    #async def kompari_paroj_p1(loop,paroj):
    #  farindajxoj = set()
    #  for paro in paroj :
    #    farindajxoj.add(loop.run_in_executor(None,kompari_paro_p1,paro))
    #  for farindajxo in farindajxoj :
    #    await farindajxo
    def kompari_paro_p2(paro):
      grPersono = self.db.get_person_from_handle(paro[1])
      fsid = paro[2]
      utila.ligi_gr_fs(self.dbstate.db, grPersono, fsid)
      print("traitement "+grPersono.gramps_id+' '+fsid)
      if fsid in PersonFS.PersonFS.fs_Tree._persons:
        fsPersono = PersonFS.PersonFS.fs_Tree._persons.get(fsid)
        kompariFsGr(fsPersono,grPersono,self.db,dupdok=True)
      else:
        print (' kompari_paro_p2 : '+_('FS ID %s ne trovita') % (fsid))
    #cnt=0
    #paroj=list()
    for paro in pOrdList:
      if progress.get_cancelled() :
        self.uistate.set_busy_cursor(False)
        progress.close()
        self.dbstate.db.enable_signals()
        self.dbstate.db.request_rebuild()
        PersonFS.PersonFS.fs_etikedado = kop_etik
        return
      progress.step()
      kompari_paro_p1(paro)
      kompari_paro_p2(paro)
      #paroj.append(paro)
      #cnt = cnt+1
      #if cnt >= 10 :
      #  loop = asyncio.get_event_loop()
      #  loop.run_until_complete( kompari_paroj_p1(loop,paroj))
      #  cnt=0
      #  for paro2 in paroj:
      #    kompari_paro_p2(paro2)
      #  paroj=list()
    #if cnt >0 :
    #  loop = asyncio.get_event_loop()
    #  loop.run_until_complete( kompari_paroj_p1(loop,paroj))
    #for paro2 in paroj:
    #  kompari_paro_p2(paro2)
    PersonFS.PersonFS.fs_etikedado = kop_etik
    self.uistate.set_busy_cursor(False)
    progress.close()
    self.dbstate.db.enable_signals()
    self.dbstate.db.request_rebuild()

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
  koloro = "red"
  if (grSekso == fsSekso) :
    koloro = "green"
  return ( koloro , _('Sekso:')
        , '', grSekso
        , '', fsSekso
        , None, 'sekso', None, None
        ) 

def FaktoKomp(db, person, fsPerso, grEvent , fsFact ) :
  grFakto = utila.get_grevent(db, person, EventType(grEvent))
  grFakto_handle = None
  titolo = str(EventType(grEvent))
  if grFakto != None :
    grFakto_handle = grFakto.handle
    grFaktoDato = utila.grdato_al_formal(grFakto.date)
    if grFakto.place and grFakto.place != None :
      place = db.get_place_from_handle(grFakto.place)
      #grFaktoLoko = place.name.value
      grFaktoLoko = _pd.display(db,place)
    else :
      grFaktoLoko = ''
  else :
    grFaktoDato = ''
    grFaktoLoko = ''
  # FARINDAĴO : norma loknomo

  fsFakto = utila.get_fsfact (fsPerso, fsFact )
  if fsFakto:
    fsFakto_id = fsFakto.id
  else :
    fsFakto_id = None
  fsFaktoDato = ''
  fsFaktoLoko = ''
  if fsFakto and fsFakto.date :
    fsFaktoDato = str(fsFakto.date)
  if fsFakto and fsFakto.place :
    fsFaktoLoko = fsFakto.place.original or ''
  if grEvent == EventType.BIRTH or grEvent == EventType.DEATH :
    koloro = "red"
  else:
    koloro = "orange"
  if (grFaktoDato == fsFaktoDato) :
    koloro = "green"
  if grFaktoDato == '' and grFaktoLoko == '' and fsFaktoDato == '' and fsFaktoLoko == '' :
    return None
  if fsFaktoDato == '' and grFaktoDato != '':
    koloro = "yellow"
  if grFaktoDato == '' and fsFaktoDato != '':
    koloro = "yellow3"
  return ( koloro , titolo
        , grFaktoDato , grFaktoLoko
        , fsFaktoDato , fsFaktoLoko
        , False, 'fakto', grFakto_handle, fsFakto_id
        )

def NomojKomp(grPersono, fsPerso ) :
    grNomo = grPersono.primary_name
    fsNomo = fsPerso.akPrefNomo()
    koloro = "red"
    if (grNomo.get_primary_surname().surname == fsNomo.akSurname()) and (grNomo.first_name == fsNomo.akGiven()) :
      koloro = "green"
    res = list()
    res.append ( ( koloro , _trans.gettext('Name')
        , '', grNomo.get_primary_surname().surname + ', ' + grNomo.first_name 
        , '', fsNomo.akSurname() +  ', ' + fsNomo.akGiven()
        , False, 'nomo1', str(grNomo), fsNomo.id, grNomo.get_primary_surname().surname, grNomo.first_name
        ))
    fsNomoj = fsPerso.names.copy()
    if fsNomo and fsNomo in fsNomoj: fsNomoj.remove(fsNomo)
    for grNomo in grPersono.alternate_names :
      fsNomo = gedcomx.Name()
      koloro = "yellow"
      for x in fsNomoj :
        if (grNomo.get_primary_surname().surname == x.akSurname()) and (grNomo.first_name == x.akGiven()) :
          fsNomo = x
          koloro = "green"
          fsNomoj.remove(x)
          break
      res.append (( koloro , '  ' + _trans.gettext('Name')
        , '', grNomo.get_primary_surname().surname + ', ' + grNomo.first_name 
        , '', fsNomo.akSurname() +  ', ' + fsNomo.akGiven()
        , False, 'nomo', str(grNomo), fsNomo.id, grNomo.get_primary_surname().surname, grNomo.first_name
        ))
    koloro = "yellow3"
    for fsN in fsNomoj :
      res.append (( koloro , '  ' + _trans.gettext('Name')
        , '', ''
        , '', fsN.akSurname() +  ', ' + fsN.akGiven()
        , False, 'nomo', None, fsN.id
        ))
    return res

def grperso_datoj (db, grPersono) :
  if not grPersono:
    return ''
  grBirth = utila.get_grevent(db, grPersono, EventType(EventType.BIRTH))
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
  grDeath = utila.get_grevent(db, grPersono, EventType(EventType.DEATH))
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
  fsFakto = utila.get_fsfact (fsPerso, 'http://gedcomx.org/Birth' )
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
  fsFakto = utila.get_fsfact (fsPerso, 'http://gedcomx.org/Death' )
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
  father_handle = None
  father_name = ''
  mother = None
  mother_handle = None
  mother_name = ''
  res = list()
  if family_handle:
    family = db.get_family_from_handle(family_handle)
    father_handle = family.get_father_handle()
    if father_handle:
      father = db.get_person_from_handle(father_handle)
      father_name = name_displayer.display(father)
    mother_handle = family.get_mother_handle()
    if mother_handle:
      mother = db.get_person_from_handle(mother_handle)
      mother_name = name_displayer.display(mother)

  # FARINDAĴO : uzi _gepatrojCP
  # FARINDAĴO : multoblaj gepatroj
  #if len(fsPersono._gepatrojCP) > 0 :
  if len(fsPersono._gepatroj) > 0 :
    parents_ids = set()
    for paro in fsPersono._gepatroj:
      parents_ids.add(paro.person1.resourceId)
      parents_ids.add(paro.person2.resourceId)
    parents_ids.remove(fsPersono.id)
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
  fatherFsid = utila.get_fsftid(father)
  motherFsid = utila.get_fsftid(mother)
  koloro = "orange"
  if (fatherFsid == fsfather_id) :
    koloro = "green"
  elif father and fsfather_id == '' :
    koloro = "yellow"
  elif father is None and fsfather_id != '':
    koloro = "yellow3"
  if father or fsFather :
    res.append ( ( koloro , _trans.gettext('Father')
        , grperso_datoj(db, father) , ' ' + father_name + ' [' + fatherFsid  + ']'
        , fsperso_datoj(db, fsFather) , fs_father_name + ' [' + fsfather_id + ']'
        , False, 'patro', father_handle ,fatherFsid
        ) )
  koloro = "orange"
  if (motherFsid == fsmother_id) :
    koloro = "green"
  elif mother and fsmother_id == '' :
    koloro = "yellow"
  elif mother is None and fsmother_id != '':
    koloro = "yellow3"
  if mother or fsMother :
    res.append( ( koloro , _trans.gettext('Mother')
        , grperso_datoj(db, mother) , ' ' + mother_name + ' [' + motherFsid + ']'
        , fsperso_datoj(db, fsMother) , fs_mother_name + ' [' + fsmother_id + ']'
        , False, 'patrino', mother_handle ,motherFsid
        ) )
  return res

def aldEdzKomp(db, grPersono, fsPerso) :
  """
  " aldonas edzan komparon
  """
  grFamilioj = grPersono.get_family_handle_list()
  fsEdzoj = fsPerso._paroj.copy()
  fsInfanoj = fsPerso._infanojCP.copy()
  fsid = fsPerso.id
  res = list()
  
  for family_handle in grPersono.get_family_handle_list():
    family = db.get_family_from_handle(family_handle)
    if family :
      edzo_handle = family.mother_handle
      if edzo_handle == grPersono.handle :
        edzo_handle = family.father_handle
      if edzo_handle :
        edzo = db.get_person_from_handle(edzo_handle)
      else :
        edzo = Person()
      edzoNomo = edzo.primary_name
      edzoFsid = utila.get_fsftid(edzo)
      fsEdzoId = ''
      fsEdzTrio = None
      fsParo = None
      fsParoId = None
      for paro in fsEdzoj :
        if ( (paro.person1 and paro.person1.resourceId == edzoFsid)
            or( (paro.person1==None or paro.person1.resourceId== '') and edzoFsid == '')) :
          fsEdzoId = edzoFsid
          fsParo = paro
          fsParoId = paro.id
          fsEdzoj.remove(paro)
          break
        elif ( (paro.person2 and paro.person2.resourceId == edzoFsid)
            or( (paro.person2==None or paro.person2.resourceId== '') and edzoFsid == '')) :
          fsEdzoId = edzoFsid
          fsParo = paro
          fsParoId = paro.id
          fsEdzoj.remove(paro)
          break
      
      koloro = "yellow"
      if edzoFsid and edzoFsid == fsEdzoId :
        koloro = "green"
      if edzo_handle == None and fsEdzoId == '' :
        koloro = "green"
      if PersonFS.PersonFS.fs_Tree :
        fsEdzo = PersonFS.PersonFS.fs_Tree._persons.get(fsEdzoId) or gedcomx.Person()
      else :
        fsEdzo = gedcomx.Person()
      fsNomo = fsEdzo.akPrefNomo()
      res.append( ( koloro , _trans.gettext('Spouse')
                , grperso_datoj(db, edzo) , edzoNomo.get_primary_surname().surname + ', ' + edzoNomo.first_name + ' [' + edzoFsid + ']'
          , fsperso_datoj(db, fsEdzo) , fsNomo.akSurname() +  ', ' + fsNomo.akGiven()  + ' [' + fsEdzoId  + ']'
          , False, 'edzo', edzo_handle ,fsEdzoId , family.handle, fsParoId
           ) )
      # familiaj eventoj (edziĝo, …)
      if fsParo :
        fsFaktoj = fsParo.facts.copy()
        fsParo_id = fsParo.id
      else :
        fsFaktoj = set()
        fsParo_id = None
      for eventref in family.get_event_ref_list() :
        event = db.get_event_from_handle(eventref.ref)
        titolo = str(EventType(event.type))
        grFaktoPriskribo = event.description or ''
        grFaktoDato = utila.grdato_al_formal(event.date)
        if event.place and event.place != None :
          place = db.get_place_from_handle(event.place)
          #grFaktoLoko = place.name.value
          grFaktoLoko = _pd.display(db,place)
        else :
          grFaktoLoko = ''
        # FARINDAĴO : norma loknomo
        if grFaktoLoko == '' :
          grValoro = grFaktoPriskribo
        else :
          grValoro = grFaktoPriskribo +' @ '+ grFaktoLoko
        koloro="yellow"
        fsFaktoDato = ''
        fsFaktoLoko = ''
        fsFaktoPriskribo = ''
        fsFakto_id = None
        for fsFakto in fsFaktoj :
          gedTag = GEDCOMX_GRAMPS_FAKTOJ.get(unquote(fsFakto.type))
          if not gedTag:
            if fsFakto.type[:6] == 'data:,':
              gedTag = unquote(fsFakto.type[6:])
            else:
              gedTag = fsFakto.type
          grTag = int(event.type) or event.type
          if gedTag != grTag :
            continue
          fsFaktoDato = str(fsFakto.date or '')
          if (fsFaktoDato == grFaktoDato) :
            koloro = "green"
          if fsFakto.place:
            fsFaktoLoko = fsFakto.place.original or ''
          fsFaktoPriskribo = fsFakto.value or ''
          fsFakto_id = fsFakto.id
          fsFaktoj.remove(fsFakto)
          break
        if fsFaktoLoko == '' :
          fsValoro = fsFaktoPriskribo
        else :
          fsValoro = fsFaktoPriskribo +' @ '+ fsFaktoLoko
        res.append( ( koloro , ' '+titolo
          , grFaktoDato , grValoro
          , fsFaktoDato , fsValoro
        , False, 'edzoFakto', eventref.ref ,fsFakto_id, family.handle, fsParo_id
            ) )
      # faktoj en FS, ne en GR :
      koloro = "yellow3"
      for fsFakto in fsFaktoj :
        evtType = GEDCOMX_GRAMPS_FAKTOJ.get(unquote(fsFakto.type))
        if evtType :
          titolo = str(EventType(evtType))
        elif fsFakto.type[:6] == 'data:,':
          titolo = unquote(fsFakto.type[6:])
        else :
          titolo = fsFakto.type
        fsFaktoDato = str(fsFakto.date or '')
        if fsFakto.place:
          fsFaktoLoko = fsFakto.place.original or ''
        else : fsFaktoLoko = '' 
        fsFaktoPriskribo = fsFakto.value or ''
        if fsFaktoLoko == '' :
          fsValoro = fsFaktoPriskribo
        else :
          fsValoro = fsFaktoPriskribo +' @ '+ fsFaktoLoko
        res.append( ( koloro , ' '+titolo
          , '' , ''
          , fsFaktoDato , fsValoro
          , False, 'edzoFakto', None ,fsFakto.id, family.handle, fsParo.id
         ) )
        
      for child_ref in family.get_child_ref_list():
        infano = db.get_person_from_handle(child_ref.ref)
        infanoNomo = infano.primary_name
        infanoFsid = utila.get_fsftid(infano)
        fsInfanoId = ''
        for triopo in fsInfanoj :
          if ( (   ((triopo.parent1 and triopo.parent1.resourceId == fsid)
                    and ( (triopo.parent2 and triopo.parent2.resourceId == fsEdzoId)
                       or (not triopo.parent2 and fsEdzoId=='')))
                 or((triopo.parent2 and triopo.parent2.resourceId == fsid)
                    and ( (triopo.parent1 and triopo.parent1.resourceId == fsEdzoId)
                       or (not triopo.parent1 and fsEdzoId==''))) )
              and triopo.child.resourceId == infanoFsid ) :
            fsInfanoId = infanoFsid
            fsInfanoj.remove(triopo)
            break
        koloro = "yellow"
        if fsInfanoId != '' and fsInfanoId == infanoFsid :
          koloro = "green"
        if PersonFS.PersonFS.fs_Tree :
          fsInfano = PersonFS.PersonFS.fs_Tree._persons.get(fsInfanoId) or gedcomx.Person()
        else :
          fsInfano = gedcomx.Person()
        fsNomo = fsInfano.akPrefNomo()
        res.append( ( koloro ,'    '+ _trans.gettext('Child')
                , grperso_datoj(db, infano) , infanoNomo.get_primary_surname().surname + ', ' + infanoNomo.first_name + ' [' + infanoFsid + ']'
                , fsperso_datoj(db, fsInfano), fsNomo.akSurname() +  ', ' + fsNomo.akGiven() + ' [' + fsInfanoId + ']'
          , False, 'infano', child_ref.ref  ,fsInfanoId
           ) )
      toRemove=set()
      for triopo in fsInfanoj :
        if ( (triopo.parent1 and triopo.parent2)
             and ( (triopo.parent1.resourceId == fsid and triopo.parent2.resourceId == fsEdzoId )
                    or  (triopo.parent2.resourceId == fsid and triopo.parent1.resourceId == fsEdzoId ))) :
            fsInfanoId = triopo.child.resourceId
            koloro = "yellow3"
            fsInfano = PersonFS.PersonFS.fs_Tree._persons.get(fsInfanoId)
            if fsInfano :
              fsNomo = fsInfano.akPrefNomo()
            else :
              fsNomo = gedcomx.Name()
            res.append( ( koloro ,'    '+ _trans.gettext('Child')
                , '', ''
                , fsperso_datoj(db, fsInfano), fsNomo.akSurname() +  ', ' + fsNomo.akGiven() + ' [' + fsInfanoId + ']'
                , False, 'infano', None  ,fsInfanoId
               ) )
            toRemove.add(triopo)
      for triopo in toRemove :
        fsInfanoj.remove(triopo)
  koloro = "yellow3"
  for paro in fsEdzoj :
    if paro.person1 and paro.person1.resourceId == fsid :
      fsEdzoId = paro.person2.resourceId
    elif paro.person1 :
      fsEdzoId = paro.person1.resourceId
    fsEdzo = PersonFS.PersonFS.fs_Tree._persons.get(fsEdzoId)
    if fsEdzo :
      fsNomo = fsEdzo.akPrefNomo()
    else :
      fsNomo = gedcomx.Name()
    res.append( ( koloro , _trans.gettext('Spouse')
                , '', ''
          , fsperso_datoj(db, fsEdzo) , fsNomo.akSurname() +  ', ' + fsNomo.akGiven()  + ' [' + fsEdzoId  + ']'
                , False, 'edzo', None  ,fsEdzoId , None, paro.id
           ) )
    toRemove=set()
    for triopo in fsInfanoj :
      if ( (triopo.parent1 and triopo.parent2)
             and ( (triopo.parent1.resourceId == fsid and triopo.parent2.resourceId == fsEdzoId )
                    or  (triopo.parent2.resourceId == fsid and triopo.parent1.resourceId == fsEdzoId ))) :
        fsInfanoId = triopo.child.resourceId
        fsInfano = PersonFS.PersonFS.fs_Tree._persons.get(fsInfanoId)
        if fsInfano :
          fsNomo = fsInfano.akPrefNomo()
        else :
          fsNomo = gedcomx.Name()
        res.append( ( koloro ,'    '+ _trans.gettext('Child')
                , '', ''
                , fsperso_datoj(db, fsInfano), fsNomo.akSurname() +  ', ' + fsNomo.akGiven() + ' [' + fsInfanoId + ']'
                , False, 'infano', None  ,fsInfanoId
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
    res.append( ( koloro ,_trans.gettext('Child')
                , '', ''
                , fsperso_datoj(db, fsInfano), fsNomo.akSurname() +  ', ' + fsNomo.akGiven() + ' [' + fsInfanoId + ']'
                , False, 'infano', None  ,fsInfanoId
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
    grFaktoDato = utila.grdato_al_formal(event.date)
    if event.place and event.place != None :
      place = db.get_place_from_handle(event.place)
      #grFaktoLoko = place.name.value
      grFaktoLoko = _pd.display(db,place)
    else :
      grFaktoLoko = ''
    # FARINDAĴO : norma loknomo
    if grFaktoLoko == '' :
      grValoro = grFaktoPriskribo
    else :
      grValoro = grFaktoPriskribo +' @ '+ grFaktoLoko
    koloro="yellow"
    fsFakto_id = None
    fsFaktoDato = ''
    fsFaktoLoko = ''
    fsFaktoPriskribo = ''
    for fsFakto in fsFaktoj :
      fsFakto_id = fsFakto.id
      gedTag = GEDCOMX_GRAMPS_FAKTOJ.get(unquote(fsFakto.type))
      if not gedTag:
        if fsFakto.type[:6] == 'data:,':
          gedTag = unquote(fsFakto.type[6:])
        else:
          gedTag = fsFakto.type
      if not gedTag :
        continue
      grTag = int(event.type) or event.type
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
      koloro = "green"
      fsFaktoj.remove(fsFakto)
      break
    if fsFaktoLoko == '' :
      fsValoro = fsFaktoPriskribo
    else :
      fsValoro = fsFaktoPriskribo +' @ '+ fsFaktoLoko
    res.append( [ koloro , titolo
        , grFaktoDato , grValoro
        , fsFaktoDato , fsValoro
        , False, 'fakto', grFakto.ref  ,fsFakto_id
        ] )
  koloro = "yellow3"
  for fsFakto in fsFaktoj :
    if fsFakto.type == "http://gedcomx.org/Birth" or fsFakto.type == "http://gedcomx.org/Baptism" or fsFakto.type == "http://gedcomx.org/Death" or fsFakto.type == "http://gedcomx.org/Burial" :
      continue
    gedTag = GEDCOMX_GRAMPS_FAKTOJ.get(unquote(fsFakto.type))
    if not gedTag:
      if fsFakto.type[:6] == 'data:,':
        gedTag = unquote(fsFakto.type[6:])
      else:
        gedTag = fsFakto.type
    if gedTag :
      titolo = str(EventType(gedTag))
    elif fsFakto.type[:6] == 'data:,':
      titolo = unquote(fsFakto.type[6:])
    else :
      titolo = fsFakto.type
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
    res.append( [ koloro , titolo
        , '' , ''
        , fsFaktoDato , fsValoro
        , False, 'fakto', None  ,fsFakto.id
        ] )
  return res

def kompariFsGr(fsPersono,grPersono,db,model=None,dupdok=False):
  dbPersono= fs_db.db_stato(db,grPersono.handle)
  dbPersono.get()
  if (model == None and hasattr(fsPersono,'_datmod')
      and dbPersono.stat_dato > fsPersono._datmod
      and dbPersono.stat_dato > grPersono.change):
    return
  if fsPersono.id :
    dbPersono.fsid = fsPersono.id
  FS_Familio=FS_Esenco=FS_Nomo=FS_Fakto=FS_Gepatro=FS_Dup=FS_Dok=False
  tag_fs_dok = db.get_tag_from_name('FS_Dok')
  if tag_fs_dok and tag_fs_dok.handle in grPersono.tag_list:
    FS_Dok = True
  tag_fs_dup = db.get_tag_from_name('FS_Dup')
  if tag_fs_dup and tag_fs_dup.handle in grPersono.tag_list:
    FS_Dup = True
  # Komparo de esenca eroj
  listres=list()
  res = SeksoKomp(grPersono, fsPersono)
  if res: listres.append(res)
  if res and res[0] != "green" : FS_Esenco = True
  resNomoj = NomojKomp(grPersono, fsPersono)
  if resNomoj :
    if resNomoj[0][0] != "green" : FS_Esenco = True
    listres.append(resNomoj.pop(0))
  res = FaktoKomp(db, grPersono, fsPersono, EventType.BIRTH , "http://gedcomx.org/Birth") 
  if res: listres.append(res)
  if res and res[0] != "green" : FS_Esenco = True
  res = FaktoKomp(db, grPersono, fsPersono, EventType.BAPTISM , "http://gedcomx.org/Baptism")
  if res: listres.append(res)
  if res and res[0] != "green" : FS_Esenco = True
  res = FaktoKomp(db, grPersono, fsPersono, EventType.DEATH , "http://gedcomx.org/Death") 
  if res: listres.append(res)
  if res and res[0] != "green" : FS_Esenco = True
  res = FaktoKomp(db, grPersono, fsPersono, EventType.BURIAL , "http://gedcomx.org/Burial")
  if res: listres.append(res)
  if res and res[0] != "green" : FS_Esenco = True

  if not PersonFS.PersonFS.fs_Tree:
    colFS = _('Ne konektita al FamilySearch')
  else :
    colFS = '===================='


  if(model and len(listres)) :
    if not PersonFS.PersonFS.fs_Tree:
      esenco_id = model.add(['white',_('Esenco'),'==========','============================','==========',colFS,False,'Esenco',None,None,None,None]  )
    elif FS_Esenco:
      esenco_id = model.add(['red',_('Esenco'),'==========','============================','==========',colFS,False,'Esenco',None,None,None,None]  )
    else:
      esenco_id = model.add(['green',_('Esenco'),'==========','============================','==========',colFS,False,'Esenco',None,None,None,None]  )
    for linio in listres:
      model.add( linio,node=esenco_id)

  # Komparo de aliaj nomoj
  if len(resNomoj)>0 :
    for linio in resNomoj:
      if linio[0] != "green" : FS_Nomo = True
    if model :
      if not PersonFS.PersonFS.fs_Tree:
        nomo_id = model.add(['white',_('Aliaj nomoj'),'==========','============================','==========',colFS,False,'Aliaj nomoj',None,None,None,None]  )
      elif FS_Nomo:
        nomo_id = model.add(['red',_('Aliaj nomoj'),'==========','============================','==========',colFS,False,'Aliaj nomoj',None,None,None,None]  )
      else:
        nomo_id = model.add(['green',_('Aliaj nomoj'),'==========','============================','==========',colFS,False,'Aliaj nomoj',None,None,None,None]  )
      for linio in resNomoj:
        model.add( linio,node=nomo_id)

  # Komparo de gepatroj
  res = aldGepKomp(db, grPersono, fsPersono)
  FS_Gepatro=False
  for linio in res:
    if linio[0] != "green" : FS_Gepatro = True
  if(model and len(res)) :
    if not PersonFS.PersonFS.fs_Tree:
      gepatro_id = model.add(['white',_('Gepatroj'),'==========','============================','==========',colFS,False,'Gepatroj',None,None,None,None]  )
    elif FS_Gepatro:
      gepatro_id = model.add(['red',_('Gepatroj'),'==========','============================','==========',colFS,False,'Gepatroj',None,None,None,None]  )
    else:
      gepatro_id = model.add(['green',_('Gepatroj'),'==========','============================','==========',colFS,False,'Gepatroj',None,None,None,None]  )
    for linio in res:
      model.add( linio,node=gepatro_id)

  # Komparo de familioj
  res = aldEdzKomp(db, grPersono, fsPersono)
  for linio in res:
    if linio[0] != "green" : FS_Familio = True
  if(model and len(res)) :
    if not PersonFS.PersonFS.fs_Tree:
      familio_id = model.add(['white',_('Familioj'),'==========','============================','==========',colFS,False,'Familioj',None,None,None,None]  )
    elif FS_Familio:
      familio_id = model.add(['red',_('Familioj'),'==========','============================','==========',colFS,False,'Familioj',None,None,None,None]  )
    else:
      familio_id = model.add(['green',_('Familioj'),'==========','============================','==========',colFS,False,'Familioj',None,None,None,None]  )
    for linio in res:
       model.add( linio,node=familio_id)

  # Komparo de aliaj faktoj
  res = aldAliajFaktojKomp(db, grPersono, fsPersono)
  for linio in res:
    if linio[0] != "green" : FS_Fakto = True
  if model and len(res):
    if not PersonFS.PersonFS.fs_Tree:
      fakto_id = model.add(['white',_('Faktoj'),'==========','============================','==========',colFS,False,'Faktoj',None,None,None,None]  )
    elif FS_Fakto:
      fakto_id = model.add(['red',_('Faktoj'),'==========','============================','==========',colFS,False,'Faktoj',None,None,None,None]  )
    else:
      fakto_id = model.add(['green',_('Faktoj'),'==========','============================','==========',colFS,False,'Faktoj',None,None,None,None]  )
    for linio in res:
      model.add( linio,node=fakto_id)

  if not PersonFS.PersonFS.fs_Tree:
    return

  if fsPersono.id and (not hasattr(fsPersono,'_last_modified') or not fsPersono._last_modified ) :
    mendo = "/platform/tree/persons/"+fsPersono.id
    r = tree._FsSeanco.head_url( mendo )
    while r.status_code == 301 and 'X-Entity-Forwarded-Id' in r.headers :
      fsid = r.headers['X-Entity-Forwarded-Id']
      utila.ligi_gr_fs(db, grPersono, fsid)
      fsPersono.id = fsid
      mendo = "/platform/tree/persons/"+fsPersono.id
      r = tree._FsSeanco.head_url( mendo )
    if 'Last-Modified' in r.headers :
      fsPersono._last_modified = int(time.mktime(email.utils.parsedate(r.headers['Last-Modified'])))
    if 'Etag' in r.headers :
      fsPersono._etag = r.headers['Etag']
  if not hasattr(fsPersono,'_last_modified') :
    fsPersono._last_modified = 0
  FS_Identa = not( FS_Familio or FS_Esenco or FS_Nomo or FS_Fakto or FS_Gepatro )
  # Serĉi ĉu FamilySearch ofertas duplonojn
  if fsPersono.id and dupdok:
    mendo = "/platform/tree/persons/"+fsPersono.id+"/matches"
    r = tree._FsSeanco.head_url(
                    mendo ,{"Accept": "application/x-gedcomx-atom+json"}
                )
    if r and r.status_code == 200 :
      FS_Dup = True
    if r and r.status_code != 200 :
      FS_Dup = False
    # Serĉi ĉu FamilySearch ofertas dokumentoj
    mendo = "/service/tree/tree-data/record-matches/"+fsPersono.id
    r = tree._FsSeanco.get_url( mendo ,{"Accept": "application/json,*/*"})
    if r and r.status_code == 200 :
      try:
        j = r.json()
        if ( 'data' in j
            and 'matches' in j['data'] 
            and len(j['data']['matches']) >= 1 ) :
          FS_Dok = True
        else:
          FS_Dok = False
      except Exception as e:
        self.write_log("WARNING: corrupted file from %s, error: %s" % (mendo, e))
        print(r.content)
  dbPersono.stat_dato = int(time.time())
  if ( FS_Identa 
       and ( not dbPersono.konf_dato 
          or (grPersono.change > dbPersono.konf_dato)
          or (fsPersono._last_modified > dbPersono.konf_dato))):
    dbPersono.konf_dato = dbPersono.stat_dato
  if dbPersono.konf_dato and grPersono.change > dbPersono.konf_dato :
    FS_Gramps = True
  else :
    FS_Gramps = False
  if dbPersono.konf_dato and fsPersono._last_modified > dbPersono.konf_dato :
    FS_FS = True
  else :
    FS_FS = False
  ret = list() 
  if PersonFS.PersonFS.fs_etikedado :
    if db.transaction :
      intr = True
      txn=db.transaction
    else :
      intr = False
      txn = DbTxn(_("FamilySearch etikedoj"), db)
    # «tags»
    for t in fs_db.stato_tags:
      val = locals().get(t[0])
      if val == None : continue
      tag_fs = db.get_tag_from_name(t[0])
      if val : ret.append(t[0])
      if not val and tag_fs.handle in grPersono.tag_list:
        grPersono.remove_tag(tag_fs.handle)
      if tag_fs and val and tag_fs.handle not in grPersono.tag_list:
        grPersono.add_tag(tag_fs.handle)
    db.commit_person(grPersono, txn, grPersono.change)
    dbPersono.gramps_datomod = grPersono.change
    if fsPersono.id :
      dbPersono.fs_datomod = fsPersono._last_modified
    dbPersono.konf_esenco = not FS_Esenco
    dbPersono.commit(txn)
    if not intr :
      db.transaction_commit(txn)
  return ret

  # FARINDAĴOJ : fontoj, notoj, memoroj, attributoj …

