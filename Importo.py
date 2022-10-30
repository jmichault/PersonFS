
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
#_ = glocale.translation.gettext

# tutmondaj variabloj
vorteco = 0

CONFIG_NAME = "FSImporto"
CONFIG = config.register_manager(CONFIG_NAME)
CONFIG.register("pref.vorteco", vorteco)
CONFIG.load()

def save_config():
    CONFIG.set("pref.vorteco", vorteco)
    CONFIG.save()

save_config()


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
    if vorteco >= 3:
      print(_("Antaŭe VORT"))
    gui_vort = CONFIG.get('pref.vorteco')
    if vorteco >= 3:
      print(_("VORT:"), gui_vort)
    self.__gui_vort = NumberOption(_("Vorteco"), gui_vort, 0, 3)
    self.__gui_vort.set_help(_("Vorteca nivelo de 0 (minimuma) ĝis 3 (tre vorta)"))
    menu.add_option(category_name, "gui_vort", self.__gui_vort)

    if vorteco >= 3:
      print(_("Menuo Aldonita"))

class FSImporto(PluginWindows.ToolManagedWindowBatch):
  """
  " 
  """
  fs_TreeImp = None
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
    db = self.dbstate.db
    self.__get_menu_options()
    print("import ID "+self.FS_ID)
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
      

    # Legi la personon en «FamilySearch».
    if not self.fs_TreeImp :
      self.fs_TreeImp = Tree(PersonFS.fs_Session)
    self.fs_TreeImp.add_indis([self.FS_ID])
    fsPerso = self.fs_TreeImp.indi.get(self.FS_ID)
    if not fsPerso :
      print("ID introuvable.")
      return
    else :
      print("ID chargé.")
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
    attr.set_value(self.FS_ID)
    grPerson.add_attribute(attr)

    with DbTxn("FamilySearch import", db) as trans:
      db.add_person(grPerson,trans)
      self.dbstate.db.commit_person(person,trans)
    
    
    print("import fini.")

  def __get_menu_options(self):
    print(_("Plugin __get_menu_options"))
    menu = self.options.menu
    self.FS_ID = self.options.menu.get_option_by_name('FS_ID').get_value()

