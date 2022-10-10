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
from gramps.gen.config import config
from gramps.gen.const import GRAMPS_LOCALE as glocale
from gramps.gen.datehandler import get_date
from gramps.gen.display.name import displayer as name_displayer
from gramps.gen.errors import WindowActiveError
from gramps.gen.lib import StyledText, StyledTextTag, StyledTextTagType
from gramps.gen.plug import Gramplet
from gramps.gen.utils.db import get_birth_or_fallback, get_death_or_fallback

from gramps.gui.editors import EditPerson
from gramps.gui.listmodel import ListModel, NOSORT
from gramps.gui.widgets.styledtexteditor import StyledTextEditor

_ = glocale.translation.gettext

class PersonFS(Gramplet):
  """
  Gramplet to display ancestors of the active person.
  """
  def init(self):
    self.gui.WIDGET = self.krei_gui()
    self.gui.get_container_widget().remove(self.gui.textview)
    self.gui.get_container_widget().add_with_viewport(self.gui.WIDGET)
    self.gui.WIDGET.show_all()

  def krei_gui(self):
    """
    krei the GUI interface.
    """
    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    vbox.set_spacing(4)
    tags = [StyledTextTag(StyledTextTagType.LINK, 'https://familysearch.org', [(0, len('family search'))])]
    textelien = StyledText('family search', tags)
    self.label = StyledTextEditor()
    self.label.set_editable(False)
    self.label.set_text(textelien)
    self.label.set_halign(Gtk.Align.START)


    self.view = Gtk.TreeView()
    self.view.set_tooltip_column(3)
    titles = [(_('Name'), 0, 230),
                  (_('Birth'), 2, 100),
                  ('', NOSORT, 1),
                  ('', NOSORT, 1), # tooltip
                  ('', NOSORT, 100)] # handle
    self.model = ListModel(self.view, titles, list_mode="tree",
                               event_func=self.cb_double_click)
    vbox.pack_start(self.label, False, True, 0)
    vbox.pack_start(self.view, False, True, 0)
    return vbox

  def get_has_data(self, active_handle):
    """
    Return True if the gramplet has data, else return False.
    """
    if active_handle:
      person = self.dbstate.db.get_person_from_handle(active_handle)
      family_handle = person.get_main_parents_family_handle()
      if family_handle:
        family = self.dbstate.db.get_family_from_handle(family_handle)
        if family and (family.get_father_handle() or
                       family.get_mother_handle()):
          return True
    return False

  def cb_double_click(self, treeview):
    """
    Handle double click on treeview.
    """
    (model, iter_) = treeview.get_selection().get_selected()
    if not iter_:
      return

    try:
      handle = model.get_value(iter_, 4)
      person = self.dbstate.db.get_person_from_handle(handle)
      EditPerson(self.dbstate, self.uistate, [], person)
    except WindowActiveError:
      pass

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
    self.model.clear()
    if active_handle:
      self.add_to_tree(1, None, active_handle)
      self.view.expand_all()
      self.set_has_data(self.get_has_data(active_handle))
    else:
      self.set_has_data(False)

  def add_to_tree(self, depth, parent_id, person_handle):
    """
    Add a person to the tree.
    """
    if depth > config.get('behavior.generation-depth'):
      return

    person = self.dbstate.db.get_person_from_handle(person_handle)
    name = name_displayer.display(person)
    if parent_id is None:
      fsid = ''
      for attr in person.get_attribute_list():
        if attr.get_type() == '_FSFTID':
          fsid = attr.get_value()
      text = name + '';
      if fsid == '':
        lien = 'https://familysearch.org'
      else:
        lien = 'https://familysearch.org/tree/person/' + fsid
      tags = [StyledTextTag(StyledTextTagType.LINK, lien, [(0, len(text))])]
      textelien = StyledText(text, tags)
      self.label.set_text(textelien)

    birth = get_birth_or_fallback(self.dbstate.db, person)
    death = get_death_or_fallback(self.dbstate.db, person)

    birth_text = birth_date = birth_sort = ''
    if birth:
      birth_date = get_date(birth)
      birth_sort = '%012d' % birth.get_date_object().get_sort_value()
      birth_text = _('%(abbr)s %(date)s') % \
                         {'abbr': birth.type.get_abbreviation(),
                          'date': birth_date}

    death_date = death_sort = death_text = ''
    if death:
      death_date = get_date(death)
      death_sort = '%012d' % death.get_date_object().get_sort_value()
      death_text = _('%(abbr)s %(date)s') % \
                         {'abbr': death.type.get_abbreviation(),
                          'date': death_date}

    tooltip = name + '\n' + birth_text + '\n' + death_text

    label = _('%(depth)s. %(name)s') % {'depth': depth, 'name': name}
    item_id = self.model.add([label, birth_date, birth_sort,
                                  tooltip, person_handle], node=parent_id)

    family_handle = person.get_main_parents_family_handle()
    if family_handle:
      family = self.dbstate.db.get_family_from_handle(family_handle)
      if family:
        father_handle = family.get_father_handle()
        if father_handle:
          self.add_to_tree(depth + 1, item_id, father_handle)
        mother_handle = family.get_mother_handle()
        if mother_handle:
          self.add_to_tree(depth + 1, item_id, mother_handle)

    return item_id
