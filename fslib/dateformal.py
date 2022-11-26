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

import sys


# datetime ne akceptas negativajn valuojn, do ni devas krei nian propran klason
class SimplaDato:
  """
  " jaro: int
  " monato: int
  " tago: int
  " horo: int
  " minuto: int
  " sekundo: int
  " zono: str
  """
  def __init__(self,datumoj: str=None):
    #±YYYY[-MM[-DD[Thh:[mm[:ss]][±hh[:mm]|Z]]]]
    self.jaro = self.monato = self.tago = self.horo = self.minuto = self.sekundo = 0
    self.zono='Z'
    if not datumoj:
      return
    if len(datumoj) <5:
      print("nekorekta formala dato: "+datumoj)
      return
    posZ = datumoj.find('Z')
    if posZ >0:
      datumoj = datumoj[:posZ]
      self.zono='Z'
    splitT = datumoj.split('T')
    dato=splitT[0]
    if len(dato) <5:
      print("nekorekta formala dato: "+datumoj)
      return
    self.jaro=int(dato[:5])
    x = dato[6:].split('-')
    if len(x)>0 and x[0] != '' : self.monato=int(x[0])
    if len(x)>1 : self.tago=int(x[1])
    if len(splitT)>1:
      pHoro=splitT[1] # hora parto : hh:[mm[:ss]]
      posSigno = pHoro.find('+')
      if not posSigno: posSigno = pHoro.find('-')
      if posSigno >=0:
        self.zono = pHoro[posSigno:]
        pHoro = pHoro[:posSigno]
      x = pHoro.split(':')
      self.horo=int(x[0])
      if len(x)>1 : self.minuto=int(x[1])
      if len(x)>2 : self.sekundo=int(x[2])
  def __str__(self):
    #±YYYY[-MM[-DD[Thh:[mm[:ss]][±hh[:mm]|Z]]]]
    if self.jaro ==0 : return ''
    if self.jaro >= 0 : res='+'
    res += "%04d" %(self.jaro)
    if self.monato:
      res += "-%02d" %(self.monato)
      if self.tago:
        res += "-%02d" %(self.tago)
    if self.horo:
      res += "T%02d" %(self.horo)
      if self.minuto:
        res += ":%02d" %(self.minuto)
        if self.sekundo:
          res += ":%02d" %(self.sekundo)
      res += self.zono
    return res



class DateFormal:
  """
  " proksimuma: bool
  " gamo: bool
  " okazoj: int
  " unuaDato: SimplaDato
  " finalaDato: SimplaDato
  " dauxro : str #  PnnnnYnnMnnDTnnHnnMnnS
  """
  def __init__(self,src=None):
    self.proksimuma = self.gamo = False
    self.okazoj=0
    self.unuaDato = SimplaDato()
    self.finalaDato = SimplaDato()
    self.dauxro = None
    self.maljsonigi(src)

  def maljsonigi(self,src):
    if not src or len(src)<5: return
    if src[0] == 'A':
      self.proksimuma = True
      src = src[1:]
    if src[0] == 'R':
      src = src[1:]
      partoj = src.split('/',1)
      self.okazoj = int(partoj[0]) or 1
      src = partoj[1]
    partoj = src.split('/')
    self.unuaDato = SimplaDato(partoj[0])
    if len(partoj)>1: self.gamo = True
    if len(partoj)>1 and len(partoj[1])>1 :
      if partoj[1] == 'P':
        self.dauxro = partoj[1]
      else:
        self.finalaDato = SimplaDato(partoj[1])
    
  def jsonigi(self):
    return str(self)


  def __str__(self):
    if self.proksimuma: res='A'
    else: res=''
    if self.okazoj >0:
      res += 'R'+str(self.okazoj)+'/'
    res += str(self.unuaDato)
    if self.gamo:
      res += '/'
      if self.finalaDato :
        res += str(self.finalaDato)
      elif self.dauxro :
        res += self.dauxro
    return res
