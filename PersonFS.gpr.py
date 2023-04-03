#
# Gramplet - fs (familysearch)
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

#------------------------------------------------------------------------
#
# FS Gramplet
#
#------------------------------------------------------------------------

register(GRAMPLET,
         id = "FS Gramplet",
         name = _("PersonFS"),
         description = _("interfaco por FamilySearch"),
         status = STABLE,
         fname="PersonFS.py",
         height=100,
         expand=True,
         gramplet = 'PersonFS',
         gramplet_title=_("FS"),
         detached_width = 500,
         detached_height = 500,
         version="1.3.2",
         gramps_target_version= '5.1',
         navtypes=["Person"],
         )

register(TOOL,
    id    = 'Importo de FamilySearch',
    name  = _("Importo de FamilySearch datoj"),
    description =  _("FamilySearch."),
    version = '1.3.2',
    gramps_target_version = '5.1',
    status = STABLE,
    fname = 'Importo.py',
    category = TOOL_DBPROC,
    toolclass = 'FSImporto',
    optionclass = 'FSImportoOpcionoj',
    tool_modes = [TOOL_MODE_GUI],
)

register(TOOL,
    id    = 'FamilySearch komparo',
    name  = _("FamilySearch : kompari"),
    description =  _("FamilySearch : kompari gramps personojn kun FS personojn."),
    version = '1.3.2',
    gramps_target_version = '5.1',
    status = STABLE,
    fname = 'komparo.py',
    category = TOOL_DBPROC,
    toolclass = 'FSKomparo',
    optionclass = 'FSKomparoOpcionoj',
    tool_modes = [TOOL_MODE_GUI],
)
