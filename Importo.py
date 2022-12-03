#
# interfaco por familysearch
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
" «FamilySearch» importo.
"""
#import cProfile
import json


from gi.repository import Gtk

from gramps.gen.db import DbTxn
from gramps.gen.config import config
from gramps.gen.const import GRAMPS_LOCALE as glocale
from gramps.gen.lib import Attribute, ChildRef, Citation, Date, Event, EventRef, EventType, EventRoleType, Family, Media, Name, NameType, Note
from gramps.gen.lib import Person, Place, PlaceName, PlaceRef, PlaceType, Source, SrcAttribute, StyledText, StyledTextTag, StyledTextTagType
from gramps.gen.plug.menu import StringOption, PersonOption, BooleanOption, NumberOption, FilterOption, MediaOption
from gramps.gui.dialog import WarningDialog, QuestionDialog2
from gramps.gui.plug import MenuToolOptions, PluginWindows
from gramps.gui.utils import ProgressMeter
from gramps.plugins.lib.libgedcom import PERSONALCONSTANTEVENTS, FAMILYCONSTANTEVENTS, GED_TO_GRAMPS_EVENT, TOKENS

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

from PersonFS import PersonFS, CONFIG
from constants import FACT_TAGS
from tree import Tree

try:
    _trans = glocale.get_addon_translator(__file__)
except ValueError:
    _trans = glocale.translation
_ = _trans.gettext

# tutmondaj variabloj
vorteco = 0

#from objbrowser import browse ;browse(locals())

class FSImportoOpcionoj(MenuToolOptions):
  """
  " 
  """
  def __init__(self, name, person_id=None, dbstate=None):
    """
    " 
    """
    if vorteco >= 3:
      print(_("Kromprogramoj"))
    MenuToolOptions.__init__(self, name, person_id, dbstate)

  def add_menu_options(self, menu):
    """
    " 
    """
    category_name = _("FamilySearch Importo Opcionoj")
    self.__FS_ID = StringOption(_("FamilySearch ID"), 'XXXX-XXX')
    self.__FS_ID.set_help(_("identiga numero por esti prenita de FamilySearch retejo"))
    menu.add_option(category_name, "FS_ID", self.__FS_ID)
    self.__gui_asc = NumberOption(_("Nombro ascentontaj"), 0, 0, 99)
    self.__gui_asc.set_help(_("Nombro de generacioj por supreniri"))
    menu.add_option(category_name, "gui_asc", self.__gui_asc)
    self.__gui_desc = NumberOption(_("Nombro descendontaj"), 0, 0, 99)
    self.__gui_desc.set_help(_("Nombro de generacioj descendontaj"))
    menu.add_option(category_name, "gui_desc", self.__gui_desc)
    self.__gui_nereimporti = BooleanOption(_("Ne reimporti ekzistantajn personojn"), True)
    self.__gui_nereimporti.set_help(_("Importi nur neekzistantajn personojn"))
    menu.add_option(category_name, "gui_nereimporti", self.__gui_nereimporti)
    self.__gui_edz = BooleanOption(_("Aldoni geedzoj"), False)
    self.__gui_edz.set_help(_("Aldoni informojn pri geedzoj"))
    menu.add_option(category_name, "gui_edz", self.__gui_edz)
    self.__gui_vort = NumberOption(_("Vorteco"), 0, 0, 3)
    self.__gui_vort.set_help(_("Vorteca nivelo de 0 (minimuma) ĝis 3 (tre vorta)"))
    menu.add_option(category_name, "gui_vort", self.__gui_vort)

    if vorteco >= 3:
      print(_("Menuo Aldonita"))
  def load_previous_values(self):
    MenuToolOptions.load_previous_values(self)
    if PersonFS.FSID :
      self.handler.options_dict['FS_ID'] = PersonFS.FSID
    return

class FSImporto(PluginWindows.ToolManagedWindowBatch):
  """
  " 
  """
  fs_TreeImp = None
  fs_gr = None
  def __init__(self, dbstate, user, options_class, name, callback):
    """
    " 
    """
    self.uistate = user.uistate
    PluginWindows.ToolManagedWindowBatch.__init__(self, dbstate, user, options_class, name, callback)

  def get_title(self):
    """
    " 
    """
    return _("FamilySearch Import Tool")  # tool window title

  def initial_frame(self):
    """
    " 
    """
    return _("FamilySearch Importo Opcionoj")  # tab title

  #@profile
  def run(self):
  #  cProfile.runctx('self.run2()',globals(),locals())
  #def run2(self):
    """
    " 
    """
    self.__get_menu_options()
    print("import ID :"+self.FS_ID)
    # FARINDAĴO : Progresa stango
    progress = ProgressMeter(_("FamilySearch Importo"), _('Starting'),
                                      parent=self.uistate.window)
    self.uistate.set_busy_cursor(True)
    self.dbstate.db.disable_signals()
    cnt=0
    self.fs_gr = dict()
    # sercxi ĉi tiun numeron en «gramps».
    # kaj plenigas fs_gr vortaro.
    progress.set_pass(_('Konstrui FSID listo'), self.dbstate.db.get_number_of_people())
    for person_handle in self.dbstate.db.get_person_handles() :
      progress.step()
      person = self.dbstate.db.get_person_from_handle(person_handle)
      for attr in person.get_attribute_list():
        if attr.get_type() == '_FSFTID' and attr.get_value() ==self.FS_ID :
          print(_('«FamilySearch» ekzistanta ID'))
        if attr.get_type() == '_FSFTID':
          self.fs_gr[attr.get_value()] = person_handle
          break
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
          if self.vorteco >= 3:
            PersonFS.fs_Session = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, True, False, 2)
          else :
            PersonFS.fs_Session = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, False, False, 2)
        else :
          print("Vi devas enigi la ID kaj pasvorton")
      else:
        if self.vorteco >= 3:
          PersonFS.fs_Session = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, True, False, 2)
        else :
          PersonFS.fs_Session = gedcomx.FsSession(PersonFS.fs_sn, PersonFS.fs_pasvorto, False, False, 2)
    print("importo")
    print(PersonFS.fs_sn)
    print(PersonFS.fs_Session)
    if self.fs_TreeImp:
      del self.fs_TreeImp
    self.fs_TreeImp = Tree(PersonFS.fs_Session)
    # Legi la personojn en «FamilySearch».
    progress.set_pass(_('Elŝutante personojn…'), mode= ProgressMeter.MODE_ACTIVITY)
    print(_("Elŝutante personon…"))
    if self.FS_ID:
      self.fs_TreeImp.add_persons([self.FS_ID])
    else : return
    progress.set_pass(_('Elŝutante ascendantojn…'),self.asc)
    # ascendante
    todo = set(self.fs_TreeImp._persons.keys())
    done = set()
    for i in range(self.asc):
      progress.step()
      if not todo:
        break
      done |= todo
      print( _("Elŝutante %s generaciojn de ascendantojn…") % (i + 1))
      todo = self.fs_TreeImp.add_parents(todo) - done
    # descendante
    progress.set_pass(_('Elŝutante posteulojn…'),self.desc)
    todo = set(self.fs_TreeImp._persons.keys())
    done = set()
    for i in range(self.desc):
      progress.step()
      if not todo:
        break
      done |= todo
      print( _("Elŝutante %s generaciojn de posteulojn…") % (i + 1))
      todo = self.fs_TreeImp.add_children(todo) - done
    # edzoj
    if self.desc and not self.edz:
      print("posteuloj elŝutantaj : devigi elŝutanto de edzoj ")
      self.edz = True
    if self.edz :
      progress.set_pass(_('Elŝutante edzojn…'), mode= ProgressMeter.MODE_ACTIVITY)
      print(_("Elŝutante edzojn…"))
      todo = set(self.fs_TreeImp._persons.keys())
      self.fs_TreeImp.add_spouses(todo)
    # notoj
    progress.set_pass(_('Elŝutante notojn…'),len(self.fs_TreeImp.persons))
    print(_("Elŝutante notojn…"))
    for fsPersono in self.fs_TreeImp.persons :
      progress.step()
      datumoj = PersonFS.fs_Session.get_jsonurl("/platform/tree/persons/%s/notes" % fsPersono.id)
      gedcomx.maljsonigi(self.fs_TreeImp,datumoj)
      datumoj = PersonFS.fs_Session.get_jsonurl("/platform/tree/persons/%s/sources" % fsPersono.id)
      gedcomx.maljsonigi(self.fs_TreeImp,datumoj)
      datumoj = PersonFS.fs_Session.get_jsonurl("/platform/tree/persons/%s/memories" % fsPersono.id)
      gedcomx.maljsonigi(self.fs_TreeImp,datumoj)
    #for fsFam in self.fs_TreeImp._fam.values() :
    #  fsFam.get_notes()
    if self.vorteco >= 3:
      rezulto = gedcomx.jsonigi(self.fs_TreeImp)
      f = open('importo.out.json','w')
      json.dump(rezulto,f,indent=2)
      f.close()

    print(_("Importado…"))
    # FamilySearch ŝarĝo kompleta
    # Komenco de importo
    with DbTxn("FamilySearch import", self.dbstate.db) as txn:
      self.txn = txn
      # importi lokoj
      progress.set_pass(_('Importado de lokoj…'),len(self.fs_TreeImp.places))
      print(_("Importado de lokoj…"))
      for pl in self.fs_TreeImp.places :
        progress.step()
        self.aldLoko(pl)
      progress.set_pass(_('Importado de personoj…'),len(self.fs_TreeImp.persons))
      print(_("Importado de personoj…"))
      # importi personoj
      for fsPersono in self.fs_TreeImp.persons :
        progress.step()
        self.aldPersono(fsPersono)
      progress.set_pass(_('Importado de familioj…'),len(self.fs_TreeImp.relationships))
      print(_("Importado de familioj…"))
      # importi familioj
      for fsFam in self.fs_TreeImp.relationships :
        progress.step()
        if fsFam.type == 'http://gedcomx.org/Couple':
          self.aldFamilio(fsFam)
    print("import fini.")
    self.txn = None
    self.uistate.set_busy_cursor(False)
    progress.close()
    self.dbstate.db.enable_signals()
    self.dbstate.db.request_rebuild()

  def akiriLoko(self, nomo, parent):
    # sercxi por loko kun cî nomo
    for handle in self.db.get_place_handles():
      place = self.db.get_place_from_handle(handle)
      if place.name.value == nomo :
        return place
      for name in place.get_alternative_names():
        if name.value == nomo :
          return place
    return None

  def kreiLoko(self, nomo, parent):
    place = self.akiriLoko(nomo, parent)
    if place:
      return place
    place = Place()
    place_name = PlaceName()
    place_name.set_value( nomo )
    place.set_name(place_name)
    place.set_title(nomo)
    place_type = None
    if not parent:
      place_type = PlaceType(1)
    else:
      if parent.place_type == PlaceType(1):
        place_type = PlaceType(9)
      elif parent.place_type == PlaceType(9):
        place_type = PlaceType(10)
      elif parent.place_type == PlaceType(10):
        place_type = PlaceType(14)
      elif parent.place_type == PlaceType(14):
        place_type = PlaceType(20)
      placeref = PlaceRef()
      placeref.ref = parent.handle
      place.add_placeref(placeref)
    place.set_type(place_type)
    self.dbstate.db.add_place(place, self.txn)
    self.dbstate.db.commit_place(place, self.txn)
    return place



  def aldLoko(self, pl):
    # FARINDAĴO : Elekti nomo
    nomo = next(iter(pl.names))
    pl._handle = None
    # sercxi por loko kun cî nomo
    grLoko = self.akiriLoko(nomo, None)
    if grLoko:
      pl._handle = grLoko.handle
      return
    
    partoj = nomo.value.split(', ')
    if len(partoj) <1:
      return

    # FARINDAĴOJ : administri naciajn apartaĵojn, aŭ uzi geonames ?
    lando = partoj.pop(len(partoj)-1)
    grLando = self.kreiLoko(lando, None)
    if grLando:
      pl._handle = grLando.handle
    if len(partoj) <1:
      return

    regiono = partoj.pop(len(partoj)-1)
    grRegiono = self.kreiLoko(regiono, grLando)
    if grRegiono:
      pl._handle = grRegiono.handle
    if len(partoj) <1:
      return

    fako = partoj.pop(len(partoj)-1)
    grFako = self.kreiLoko(fako, grRegiono)
    if grFako:
      pl._handle = grFako.handle
    if len(partoj) <1:
      return

    municipo = partoj.pop(len(partoj)-1)
    grMunicipo = self.kreiLoko(municipo, grFako)
    if grMunicipo:
      pl._handle = grMunicipo.handle
    if len(partoj) <1:
      pn = PlaceName()
      pn.set_value(nomo)
      grMunicipo.add_alternative_name(pn)
      self.dbstate.db.commit_place(grMunicipo, self.txn)
      return

    lokloko = ", ".join(partoj)
    grLoko = self.kreiLoko(lokloko, grMunicipo)
    pl_handle = grLoko.handle
    pn = PlaceName()
    pn.set_value(nomo)
    grLoko.add_alternative_name(pn)
    self.dbstate.db.commit_place(grLoko, self.txn)


  def aldFamilio(self,fsFam):
    familio = None
    grPatroHandle = self.fs_gr.get(fsFam.person1.resourceId)
    grPatrinoHandle = self.fs_gr.get(fsFam.person2.resourceId) 
    if grPatroHandle :
      grPatro = self.dbstate.db.get_person_from_handle(grPatroHandle)
      if grPatrinoHandle :
        grPatrino = self.dbstate.db.get_person_from_handle(grPatrinoHandle)
      else :
        grPatrino = None
      for family_handle in grPatro.get_family_handle_list():
        if not family_handle: continue
        f = self.dbstate.db.get_family_from_handle(family_handle)
        if f.get_mother_handle() == grPatrinoHandle :
          familio = f
          break
    elif grPatrinoHandle :
      grPatro = None
      grPatrino = self.dbstate.db.get_person_from_handle(grPatrinoHandle)
      for family_handle in grPatrino.get_family_handle_list():
        if not family_handle: continue
        f = self.dbstate.db.get_family_from_handle(family_handle)
        if f.get_father_handle() == None :
          familio = f
          break
    else:
      print(_('sengepatra familio ???'))
      return
    if not grPatro and fsFam.person1.resourceId: return
    if not grPatrino and fsFam.person2.resourceId: return
    if not familio :
      familio = Family()
      familio.set_father_handle(grPatroHandle)
      familio.set_mother_handle(grPatrinoHandle)
      attr = Attribute()
      attr.set_type('_FSFTID')
      attr.set_value(fsFam.id)
      familio.add_attribute(attr)
      self.dbstate.db.add_family(familio, self.txn)
      self.dbstate.db.commit_family(familio, self.txn)
      if grPatro:
        grPatro.add_family_handle(familio.get_handle())
        self.dbstate.db.commit_person(grPatro, self.txn)
      if grPatrino:
        grPatrino.add_family_handle(familio.get_handle())
        self.dbstate.db.commit_person(grPatrino, self.txn)
    # familiaj faktoj
    for fsFakto in fsFam.facts:
      event = self.aldFakto(fsFakto,familio)
      found = False
      for er in familio.get_event_ref_list():
        if er.ref == event.handle:
          found = True
          break
      if not found:
        er = EventRef()
        er.set_role(EventRoleType.FAMILY)
        er.set_reference_handle(event.get_handle())
        self.dbstate.db.commit_event(event, self.txn)
        familio.add_event_ref(er)
      
    self.dbstate.db.commit_family(familio,self.txn)

    for cp in self.fs_TreeImp.childAndParentsRelationships :
      if not cp.parent1 and fsFam.person1 : continue
      if not cp.parent2 and fsFam.person2 : continue
      if cp.parent1 and (not fsFam.person1 or cp.parent1.resourceId != fsFam.person1.resourceId) : continue
      if cp.parent2 and (not fsFam.person2 or cp.parent2.resourceId != fsFam.person2.resourceId) : continue
      infanoHandle = self.fs_gr.get(cp.child.resourceId)
      if not infanoHandle: continue
      found = False
      for cr in familio.get_child_ref_list() :
        if cr.get_reference_handle() == infanoHandle:
          found = True
          break
      if not found :
        childref = ChildRef()
        childref.set_reference_handle(infanoHandle)
        familio.add_child_ref(childref)
        self.dbstate.db.commit_family(familio, self.txn)
        infano = self.dbstate.db.get_person_from_handle(infanoHandle)
        infano.add_parent_family_handle(familio.get_handle())
        self.dbstate.db.commit_person(infano, self.txn)
    # notoj
    for fsNoto in fsFam.notes :
      noto = self.aldNoto(fsNoto,familio.note_list)
      familio.add_note(noto.handle)
    # fontoj
    for fsFonto in fsFam.sources :
      c = self.aldFonto(fsFonto,familio,familio.citation_list)
      #familio.add_citation(c.handle)
    # FARINDAĴOJ : FS ID
    self.dbstate.db.commit_family(familio,self.txn)
    return

  def aldFonto(self, fsFonto, obj, EkzCit):
    # akiri SourceDescription
    sourceDescription = gedcomx.SourceDescription._indekso[fsFonto.descriptionId]
    # sercxi ekzistantan
    trovita = False
    print("aldFonto sercxi : "+sourceDescription.id)
    #for s in self.dbstate.db.iter_sources():
    for sh in self.dbstate.db.get_source_handles() :
      s = self.dbstate.db.get_source_from_handle(sh)
      if s.abbrev == "FamilySearch " + sourceDescription.id :
        trovita = True
        break
      for attr in s.get_attribute_list():
        if attr.get_type() == '_FSFTID' and attr.get_value() == sourceDescription.id :
          trovita = True
      if trovita: break
    if not trovita :
      print("aldFonto : "+sourceDescription.id)
      s = Source()
      if len(sourceDescription.descriptions):
        description = next(iter(sourceDescription.descriptions))
        if description and description.value:
          s.set_description(description.value)
      if len(sourceDescription.titles):
        title = next(iter(sourceDescription.titles))
        if title and title.value:
          s.set_title(title.value)
      # FARINDAĴO : Elekti aŭtoro de SourceDescriptionId
      if len(sourceDescription.authors):
        s.set_author(next(iter(sourceDescription.authors)))
      #if len(sourceDescription.links) and 'source-reference' in sourceDescription.links:
      #  link = sourceDescription.links['source-reference']
      #  s.set_publication_info(link.href)
      if sourceDescription.about:
        s.set_publication_info(sourceDescription.about)
      # FS ID
      s.abbrev = "FamilySearch " + sourceDescription.id
      attr = SrcAttribute()
      attr.set_type('_FSFTID')
      attr.set_value(sourceDescription.id)
      s.add_attribute(attr)
      self.dbstate.db.add_source(s,self.txn)
      self.dbstate.db.commit_source(s,self.txn)
    # sercxi ekzistantan citaĵon
    for ch in obj.citation_list :
      c = self.dbstate.db.get_citation_from_handle(ch)
      if c.get_reference_handle() == s.handle :
        return c
    citation = Citation()
    citation.set_reference_handle(s.get_handle())
    self.dbstate.db.add_citation(citation,self.txn)
    self.dbstate.db.commit_citation(citation,self.txn)
    obj.add_citation(citation.handle)
    
    return citation

  def aldPersono(self,fsPersono):
    fsid = fsPersono.id
    grPersonoHandle = self.fs_gr.get(fsid)
    if not grPersonoHandle:
      grPerson = Person()
      self.aldNomoj( fsPersono, grPerson)
      if fsPersono.gender.type == "http://gedcomx.org/Male" :
        grPerson.set_gender(Person.MALE)
      elif fsPersono.gender.type == "http://gedcomx.org/Female" :
        grPerson.set_gender(Person.FEMALE)
      else :
        grPerson.set_gender(Person.UNKNOWN)
      attr = Attribute()
      attr.set_type('_FSFTID')
      attr.set_value(fsid)
      grPerson.add_attribute(attr)

      self.dbstate.db.add_person(grPerson,self.txn)
      self.dbstate.db.commit_person(grPerson,self.txn)
      self.fs_gr[fsid] = grPerson.handle
    else :
      if self.nereimporti :
        return
      grPerson = self.dbstate.db.get_person_from_handle(grPersonoHandle)

    # faktoj
    for fsFakto in fsPersono.facts:
      event = self.aldFakto(fsFakto,grPerson)
      found = False
      for er in grPerson.get_event_ref_list():
        if er.ref == event.handle:
          found = True
          break
      if not found:
        er = EventRef()
        er.set_role(EventRoleType.PRIMARY)
        er.set_reference_handle(event.get_handle())
        self.dbstate.db.commit_event(event, self.txn)
        grPerson.add_event_ref(er)
      if event.type == EventType.BIRTH :
        grPerson.set_birth_ref(er)
      elif event.type == EventType.DEATH :
        grPerson.set_death_ref(er)
      self.dbstate.db.commit_person(grPerson,self.txn)
    # notoj
    for fsNoto in fsPersono.notes :
      noto = self.aldNoto(fsNoto,grPerson.note_list)
      grPerson.add_note(noto.handle)
    # fontoj
    for fsFonto in fsPersono.sources :
      c = self.aldFonto(fsFonto,grPerson,grPerson.citation_list)
      self.dbstate.db.commit_person(grPerson,self.txn)
    # FARINDAĴOJ : memoroj
    #for fsMemoro in fsPersono.memories :
      #print("memorie :")
      #print(fsMemoro)
      #m = Media()
      #m.path = fsMemoro.url
      #m.desc = fsMemoro.description
      #self.dbstate.db.add_media(m, self.txn)
      #self.dbstate.db.commit_media(m, self.txn)
      #citation = Citation()
      #citation.set_reference_handle(m.get_handle())
      #self.dbstate.db.add_citation(citation,self.txn)
      #self.dbstate.db.commit_citation(citation,self.txn)
      #grPerson.add_citation(citation.handle)
      #continue
      
    self.dbstate.db.commit_person(grPerson,self.txn)

  def aldNomoj(self, fsPersono, grPerson):
    for fsNomo in fsPersono.names :
      nomo = Name()
      if fsNomo.type == 'http://gedcomx.org/MarriedName' :
        nomo.set_type(NameType(NameType.MARRIED))
      elif fsNomo.type == 'http://gedcomx.org/AlsoKnownAs' :
        nomo.set_type(NameType(NameType.AKA))
      elif fsNomo.type == 'http://gedcomx.org/BirthName' :
        nomo.set_type(NameType(NameType.BIRTH))
      #elif fsNomo.type == 'http://gedcomx.org/NickName' :
      #elif fsNomo.type == 'http://gedcomx.org/AdoptiveName' :
      #elif fsNomo.type == 'http://gedcomx.org/FormalName' :
      #elif fsNomo.type == 'http://gedcomx.org/ReligiousName' :
      else :
        # FARINDAĴO : administri moknomojn ĝuste
        nomo.set_type(NameType(NameType.CUSTOM))
      nomo.set_first_name(fsNomo.akGiven())
      s = nomo.get_primary_surname()
      s.set_surname(fsNomo.akSurname())
      for fsNoto in fsNomo.notes :
        noto = self.aldNoto(fsNoto,nomo.note_list)
        nomo.add_note(noto.handle)
      if fsNomo.preferred :
        grPerson.set_primary_name(nomo)
      else:
        grPerson.add_alternate_name(nomo)

  def aldNoto(self,fsNoto,EkzNotoj):
    # sercxi ekzistantan
    for nh in EkzNotoj:
      n = self.dbstate.db.get_note_from_handle(nh)
      for t in n.text.get_tags():
        if t.name == "fs_sn" :
          titolo = n.get()[t.ranges[0][0]:t.ranges[0][1]]
          if titolo == fsNoto.subject:
            return n
    note = Note()
    tags = [  StyledTextTag("fs_sn", fsNoto.id,[(0, len(fsNoto.subject))])
            , StyledTextTag(StyledTextTagType.BOLD, True,[(0, len(fsNoto.subject))])
            , StyledTextTag(StyledTextTagType.FONTSIZE, 16,[(0, len(fsNoto.subject))])  ]
    titolo = StyledText(fsNoto.subject, tags)
    note.set_format(Note.FORMATTED)
    note.set_styledtext(titolo)
    note.append("\n\n"+(fsNoto.text or ''))
    #note_type = NoteType()
    #note_type.set((note_type, note_cust))
    self.dbstate.db.add_note(note, self.txn)
    self.dbstate.db.commit_note(note, self.txn)
    return note
    
  def aldFakto(self, fsFakto, obj):
    if fsFakto.type[:6] == 'data:,':
      gedTag = FACT_TAGS.get(fsFakto.type[6:]) or fsFakto.type[6:]
    else:
      gedTag = FACT_TAGS.get(fsFakto.type) or fsFakto.type
    evtType = GED_TO_GRAMPS_EVENT.get(gedTag) or gedTag
    fsFaktoLoko = fsFakto.place or ''
    grLokoHandle = None
    fsFaktoPriskribo = fsFakto.value or ''
    fsFaktoDato = fsFakto.date or ''
    if fsFakto.date:
      grDate = Date()
      grDate.set_calendar(Date.CAL_GREGORIAN)
      if fsFakto.date.formal :
        if fsFakto.date.formal.proksimuma :
          grDate.set_modifier(Date.MOD_ABOUT)
        if fsFakto.date.formal.gamo :
          if fsFakto.date.formal.finalaDato :
            grDate.set_modifier(Date.MOD_BEFORE)
          elif fsFakto.date.formal.finalaDato :
            grDate.set_modifier(Date.MOD_AFTER)
        if fsFakto.date.formal.unuaDato:
          jaro = fsFakto.date.formal.unuaDato.jaro
          monato = fsFakto.date.formal.unuaDato.monato
          tago = fsFakto.date.formal.unuaDato.tago
        else :
          jaro = fsFakto.date.formal.finalaDato.jaro
          monato = fsFakto.date.formal.finalaDato.monato
          tago = fsFakto.date.formal.finalaDato.tago
        # FARINDAĴO : kompleksaj datoj, dato gamo
        #if tago and monato and jaro :
        #  grDate.set_yr_mon_day(jaro, monato, tago)
        #else :
        #  grDate.set(value=(tago, monato, jaro, 0),text=fsFakto.date.original)
      grDate.set(value=(tago, monato, jaro, 0),text=fsFakto.date.original or '',newyear=Date.NEWYEAR_JAN1)
    else : grDate = None

    # serĉi ekzistanta
    for fakto in obj.event_ref_list :
      e = self.dbstate.db.get_event_from_handle(fakto.ref)
      if ( e.type.value == evtType or e.type.string == gedTag) :
        if ( e.get_date_object() == grDate ):
          return e
        elif ( ( e.get_date_object().is_empty() and not grDate)
             and ( e.get_place_handle() == grLokoHandle or (not e.get_place_handle() and not grLokoHandle))
             and ( e.description == fsFaktoPriskribo or (not e.description and not fsFaktoPriskribo))
           ) :
          return e
    event = Event()
    event.set_type( evtType )
    if grLokoHandle:
      event.set_place_handle( grLokoHandle )
    if grDate :
      event.set_date_object( grDate )
    event.set_description(fsFaktoPriskribo)
    # noto
    for fsNoto in fsFakto.notes:
      noto = self.aldNoto(fsNoto,event.note_list)
      event.add_note(noto.handle)
    self.dbstate.db.add_event(event, self.txn)
    self.dbstate.db.commit_event(event, self.txn)
    return event

  def __get_menu_options(self):
    menu = self.options.menu
    self.FS_ID = menu.get_option_by_name('FS_ID').get_value()
    self.asc = menu.get_option_by_name('gui_asc').get_value()
    self.desc = menu.get_option_by_name('gui_desc').get_value()
    self.edz = menu.get_option_by_name('gui_edz').get_value()
    self.nereimporti = menu.get_option_by_name('gui_nereimporti').get_value()
    self.vorteco = menu.get_option_by_name('gui_vort').get_value()

