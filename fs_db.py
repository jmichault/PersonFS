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


# table  personfs_stato :
#      'p_handle VARCHAR(50) PRIMARY KEY NOT NULL, '	# handle gramps de la personne
#      'fsid CHAR(8), '					                # fsid de la personne
#      ? 'estas_radiko CHAR(1), '			            # vrai si c'est l'une de nos racines
#      'stat_dato integer, '				            # date de la dernière comparaison
#      'konf_dato integer, '				            # date à laquelle on a marqué la fiche conforme
#      'gramps_datomod integer, '			            # date de dernière modification dans gramps lors de la comparaison
#      'fs_datomod integer,'				            # date de dernière modification dans gramps lors de la comparaison
#      'konf_esenco CHAR(1),'				            # conforme sur les données essentielles
#      'konf CHAR(1) '					                # marqué conforme

from gramps.gen.db import DbTxn
from gramps.gen.lib import Tag

from gramps.gen.const import GRAMPS_LOCALE as glocale
try:
    _trans = glocale.get_addon_translator(__file__)
except ValueError:
    _trans = glocale.translation
_ = _trans.gettext

stato_tags = (
('FS_Identa', 'green'),
('FS_Konf', 'green'),
('FS_Esenco', 'red'),
('FS_Nomo', 'red'),
('FS_Gepatro', 'red'),
('FS_Familio', 'red'),
('FS_Fakto', 'red'),
('FS_Dup', 'red'),
('FS_Dok', 'red'),
('FS_Gramps', 'yellow'),
('FS_FS', 'yellow'),
)

def create_tags(db):
  if db.transaction :
    intr = True
    txn = db.transaction
  else :
    intr = False
    txn = None
  for t in stato_tags:
    if not db.get_tag_from_name(t[0]):
      if txn == None :
        txn = DbTxn(_("FamilySearch : krei etikadojn"), db) 
      tag = Tag()
      tag.set_name(t[0])
      tag.set_color(t[1])
      db.add_tag(tag, txn)
      db.commit_tag(tag, txn)
  if txn != None and not intr :
    db.transaction_commit(txn)
    del txn

def create_schema(db):
  # krei datumbazan tabelon
  if db.transaction :
    intr = True
    txn = db.transaction
  else :
    intr = False
    txn = None
  if not db.dbapi.table_exists("personfs_stato"):
    db.dbapi.execute('CREATE TABLE personfs_stato '
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
  if txn != None and not intr :
    db.transaction_commit(txn)
    del txn

class db_stato:
  def __init__(self, db, p_handle=None):
    self.db=db
    self.p_handle=p_handle
    self.fsid=None
    self.estas_radiko=None
    self.stat_dato=None
    self.konf_dato=None
    self.gramps_datomod=None
    self.fs_datomod=None
    self.konf_esenco=None
    self.konf=None

  def commit(self,txn):
    if not self.p_handle:
      print("eraro : ne p_handle !")
      return
    self.db.dbapi.execute("SELECT 1 FROM personfs_stato where p_handle=?",[self.p_handle])
    row = self.db.dbapi.fetchone()
    if row :
      sql = "UPDATE personfs_stato set fsid=?, estas_radiko=? , stat_dato=?, konf_dato=?, gramps_datomod=?, fs_datomod=?, konf_esenco=?, konf=? where p_handle=? "
      self.db.dbapi.execute(sql, [ self.fsid, int(self.estas_radiko or 0), self.stat_dato, self.konf_dato, self.gramps_datomod, self.fs_datomod, int(self.konf_esenco or 0), int(self.konf or 0), self.p_handle] )
    else :
      sql = "INSERT INTO personfs_stato(p_handle,fsid,estas_radiko,stat_dato,konf_dato,gramps_datomod,fs_datomod,konf_esenco,konf) VALUES (?,?,?,?,?,?,?,?,?)"
      self.db.dbapi.execute(sql, [ self.p_handle, self.fsid, int(self.estas_radiko or 0), self.stat_dato, self.konf_dato, self.gramps_datomod, self.fs_datomod, int(self.konf_esenco or 0), int(self.konf or 0) ] )

  def get(self,person_handle=None):
    if not person_handle : person_handle = self.p_handle
    if not person_handle :
      print("ne person_handle")
      return
    self.db.dbapi.execute("select p_handle,fsid,estas_radiko,stat_dato,konf_dato,gramps_datomod,fs_datomod,konf_esenco,konf from personfs_stato where p_handle=?",[person_handle])
    datumoj = self.db.dbapi.fetchone()
    if datumoj:
      self.p_handle = datumoj[0]
      self.fsid = datumoj[1]
      self.estas_radiko = datumoj[2]
      self.stat_dato = datumoj[3]
      self.konf_dato = datumoj[4]
      self.gramps_datomod = datumoj[5]
      self.fs_datomod = datumoj[6]
      self.konf_esenco = datumoj[7]
      self.konf = datumoj[8]
    else:
      self.p_handle = person_handle
      self.fsid = None
      self.estas_radiko = None
      self.stat_dato = None
      self.konf_dato = None
      self.gramps_datomod = None
      self.fs_datomod = None
      self.konf_esenco = None
      self.konf = None

