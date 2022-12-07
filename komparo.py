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

from gramps.gui.plug import MenuToolOptions, PluginWindows
from gramps.gen.plug.menu import FilterOption, TextOption, NumberOption, BooleanOption
from gramps.gen.db import DbTxn
from gramps.gui.dialog import OkDialog, WarningDialog
from gramps.gen.filters import CustomFilters, GenericFilterFactory, rules
from gramps.gen.lib import EventType


from gramps.gen.const import GRAMPS_LOCALE as glocale
try:
    _trans = glocale.get_addon_translator(__file__)
except ValueError:
    _trans = glocale.translation
_ = _trans.gettext

from tree import Tree
from PersonFS import getfsid, PersonFS, SeksoKomp, NomojKomp, FaktoKomp, db_create_schema

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
    if not PersonFS.aki_sesio():
      WarningDialog(_('Ne konektita al FamilySearch'))
      return
    if not PersonFS.fs_Tree:
      PersonFS.fs_Tree = Tree(PersonFS.fs_Session)
      PersonFS.fs_Tree._getsources = False
    self.db = self.dbstate.get_database()
    db_create_schema(self.db)
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
      PersonFS.fs_Tree.add_persons([fsid])
      fsPersono = PersonFS.fs_Tree._persons.get(fsid)
      if not fsPersono :
        print (_('FS ID %s ne trovita') % (fsid))
        continue
      grPersono = self.db.get_person_from_handle(paro[1])
      konfEsenco = True
      res = SeksoKomp(grPersono, fsPersono)
      if res and res[0] != "green" : konfEsenco = False
      res = NomojKomp(grPersono, fsPersono)
      if res and res[0][0] != "green" : konfEsenco = False
      res = FaktoKomp(self.db, grPersono, fsPersono, EventType.BIRTH , "http://gedcomx.org/Birth") 
      if res and res[0] != "green" : konfEsenco = False
      res = FaktoKomp(self.db, grPersono, fsPersono, EventType.DEATH , "http://gedcomx.org/Death") 
      if res and res[0] != "green" : konfEsenco = False
      print (konfEsenco)
      with DbTxn(_("FamilySearch tags"), self.db) as txn:
        tag_esenco = self.db.get_tag_from_name('FS_Esenco')
        if not konfEsenco and tag_esenco in grPersono.tag_list:
          grPersono.remove_tag(tag_esenco)
        if tag_esenco and konfEsenco and tag_esenco not in grPersono.tag_list:
          grPersono.add_tag(tag_esenco)
        self.db.commit_person(grPersono, txn)
      



