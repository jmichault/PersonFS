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


from gramps.gen.db import DbTxn
from gramps.gen.config import config
from gramps.gen.const import GRAMPS_LOCALE as glocale
from gramps.gen.lib import Attribute, Date, EventType, EventRoleType, Person, Name, NameType
from gramps.gen.plug.menu import StringOption, PersonOption, BooleanOption, NumberOption, FilterOption, MediaOption
from gramps.gui.dialog import OkDialog, WarningDialog, ErrorDialog
from gramps.gui.plug import MenuToolOptions, PluginWindows


from PersonFS import PersonFS
from getmyancestors.classes.tree import Tree, Name as fsName, Indi, Fact

try:
    _trans = glocale.get_addon_translator(__file__)
except ValueError:
    _trans = glocale.translation
_ = _trans.gettext

# tutmondaj variabloj
vorteco = 0

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
    self.__gui_edz = BooleanOption(_("Aldonu geedzoj"), False)
    self.__gui_edz.set_help(_("Aldonu informojn pri geedzoj kaj paro"))
    menu.add_option(category_name, "gui_edz", self.__gui_edz)
    self.__gui_vort = NumberOption(_("Vorteco"), 0, 0, 3)
    self.__gui_vort.set_help(_("Vorteca nivelo de 0 (minimuma) ĝis 3 (tre vorta)"))
    menu.add_option(category_name, "gui_vort", self.__gui_vort)

    if vorteco >= 3:
      print(_("Menuo Aldonita"))

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
    PluginWindows.ToolManagedWindowBatch.__init__(self, dbstate, user, options_class, name, callback)

  def get_title(self):
    """
    " 
    """
    print(_("Plugin get_title"))
    return _("FamilySearch Import Tool")  # tool window title

  def initial_frame(self):
    """
    " 
    """
    print(_("Plugin initial_frame"))
    return _("FamilySearch Importo Opcionoj")  # tab title

  def run(self):
    """
    " 
    """
    print(_("Plugin run"))
    self.__get_menu_options()
    print("import ID "+self.FS_ID)
    self.fs_gr = dict()
    # sercxi ĉi tiun numeron en «gramps».
    for person_handle in self.dbstate.db.get_person_handles() :
      person = self.dbstate.db.get_person_from_handle(person_handle)
      for attr in person.get_attribute_list():
        if attr.get_type() == '_FSFTID' and attr.get_value() ==self.FS_ID :
          print("ID trouvé !")
          WarningDialog(  _('«FamilySearch» ekzistanta ID')
			, _('«FamilySearch» ID uzata per %s. Importo interrompita') % {person.gramps_id}
			, self.window)
          return
        if attr.get_type() == '_FSFTID':
          self.fs_gr[attr.get_value()] = person_handle
          break
    if not self.fs_TreeImp :
      self.fs_TreeImp = Tree(PersonFS.fs_Session)
    else:
      self.fs_TreeImp.__init__()
    # Legi la personojn en «FamilySearch».
    self.fs_TreeImp.add_indis([self.FS_ID])
    # asc
    todo = set(self.fs_TreeImp.indi.keys())
    done = set()
    for i in range(self.asc):
      if not todo:
        break
      done |= todo
      print( _("Downloading %s. of generations of ancestors...") % (i + 1))
      todo = self.fs_TreeImp.add_parents(todo) - done
    # desc
    todo = set(self.fs_TreeImp.indi.keys())
    done = set()
    for i in range(self.desc):
      if not todo:
        break
      done |= todo
      print( _("Downloading %s. of generations of descendants...") % (i + 1))
      todo = self.fs_TreeImp.add_children(todo) - done
    # edzoj
    if self.edz :
      print(_("Downloading spouses and marriage information..."))
      todo = set(self.fs_TreeImp.indi.keys())
      self.fs_TreeImp.add_spouses(todo)

    # importi personoj
    for id in self.fs_TreeImp.indi.keys() :
      self.aldPersono(id)
    # importi edzoj/familioj

    print("import fini.")


  def aldPersono(self,fsid):
    if self.fs_gr.get(fsid) :
      return
    fsPerso = self.fs_TreeImp.indi.get(fsid)
    if not fsPerso :
      print("ID introuvable.")
      return
    grPerson = Person()
    nomo = Name()
    nomo.set_type(NameType(NameType.BIRTH))
    nomo.set_first_name(fsPerso.name.given)
    s = nomo.get_primary_surname()
    s.set_surname(fsPerso.name.surname)
    grPerson.set_primary_name(nomo)
    if fsPerso.gender == "M" :
      grPerson.set_gender(Person.MALE)
    elif fsPerso.gender == "F" :
      grPerson.set_gender(Person.FEMALE)
    attr = Attribute()
    attr.set_type('_FSFTID')
    attr.set_value(fsid)
    grPerson.add_attribute(attr)

    with DbTxn("FamilySearch import", self.dbstate.db) as trans:
      self.dbstate.db.add_person(grPerson,trans)
      self.dbstate.db.commit_person(grPerson,trans)

  def __get_menu_options(self):
    print(_("Plugin __get_menu_options"))
    menu = self.options.menu
    self.FS_ID = self.options.menu.get_option_by_name('FS_ID').get_value()
    self.asc = self.options.menu.get_option_by_name('gui_asc').get_value()
    self.desc = self.options.menu.get_option_by_name('gui_desc').get_value()
    self.edz = self.options.menu.get_option_by_name('gui_edz').get_value()

