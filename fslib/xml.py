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
" NE UZI ! LABORO EN PROGRESO !!!
"""

import fslib.gedcomx

from fslib.gedcomx import Gedcomx
from fslib.json import maljsonigi, all_annotations

class xmlero:
  def __init__(self):
    self._depth=0
    self._obj={ 1:self}
    self._eroj={ 1:'gedcomx'}
    self._klaso={ 1:self.__class__.__name__}
    self._isset={ 1:False}
  def start(self, tag, attrib):   # Vokita por ĉiu malferma etikedo.
    patro=self._obj.get(self._depth)
    self._depth += 1
    if self._depth == 1:
      maljsonigi(self,attrib)
      return
    if tag[:24] != '{http://gedcomx.org/v1/}':
      print("AVERTO: ne konata tag: "+tag)
      return
    kn=tag[24:]
    ann = all_annotations(patro.__class__).get(kn)
    if ann:
      if self._depth == 2:
        print("  simple:"+str(ann))
      kl2 = ann
      obj = getattr(patro,kn, None)
      if not obj:
        obj=kl2()
        setattr(patro,kn,obj)
      self._eroj[self._depth]=kn
      self._obj[self._depth]=obj
      self._klaso[self._depth]=ann
      self._isset[self._depth]=False
      return
    kn=kn+"s"
    ann = all_annotations(patro.__class__).get(kn)
    if not ann:
      print("AVERTO: xml-ne konata ero: "+tag+"-sann="+str(sann))
      return
    sann = str(ann)
    self._eroj[self._depth]=kn
    self._klaso[self._depth]=ann
    if sann[:4] == 'set[':
      print("set[")
      print(ann.__args__[0])
    elif sann[:9] == 'dict[str,' : # speciala kazo : dict[str,Link]
      if "Link" in sann:# speciala kazo : dict[str,Link]
        attr = getattr(patro,kn, None) or dict()
        rel = attrib['rel']
        attrib.pop('rel')
        l = fslib.gedcomx.Link()
        maljsonigi(l,attrib)
        attr[rel]=l
        setattr(patro,kn, attr)
      elif ",set]" in sann:# speciala kazo : dict[str,set]
        attr = getattr(patron,k, None) or dict()
        #for k2,v in d[k].items() :
        #  attr[k2] =v
        setattr(patro,kn, attr)
      else:
        print("AVERTO: ne konata dict: "+tag+"-sann="+sann)
    else:
      print("AVERTO: ne konata klaso: "+patro.__class__.__name__+":"+kn+" - "+sann)
    kl2 = ann.__args__[0]
    obj=kl2()
    self._obj[self._depth]=obj
    maljsonigi(obj,attrib)
    self._isset[self._depth]=True
  def end(self, tag):             # Vokita por ĉiu ferma etikedo.
    obj = self._obj.get(self._depth)
    kn = self._eroj.get(self._depth)
    isset = self._isset.get(self._depth)
    if kn == 'changeMessage':
       print("  obj="+str(obj))
    self._depth -= 1
    patro = self._obj.get(self._depth)
    if self._depth == 1:
      print("  end:"+kn)
    if self._depth >= 1:
      #print("  end:"+kn)
      if isset:
        attr = getattr(patro,kn, None) or set()
        #from objbrowser import browse ;browse(locals())
        if obj:
          attr.add(obj)
        if patro:
          setattr(patro,kn, attr)
      else:
        setattr(patro,kn,obj)
      self._obj[self._depth+1] = None
      self._eroj[self._depth+1] = ''
      self._isset[self._depth+1]=False
  def data(self, data):
    if data and not data.isspace() :
      obj = self._obj.get(self._depth)
      kn = self._eroj.get(self._depth)
      klaso = self._klaso.get(self._depth)
      isset = self._isset.get(self._depth)
      if klaso.__name__ != obj.__class__.__name__:
        print("AVERTO:   ??"+str(self._depth)+"-data: kn="+kn+" ;"+data+";klaso="+klaso.__name__+" - "+obj.__class__.__name__)
      if klaso.__name__ == 'str' or klaso.__name__ == 'bool' or klaso.__name__ == 'int':
        self._obj[self._depth]=data
      elif klaso.__name__ == 'DateFormal':
        maljsonigi(obj,data)
      elif obj.__class__.__name__ == 'set':
        obj.add(data)
      elif klaso.__name__ == 'set' and obj.__class__.__name__ == 'TextValue':
        obj.value = data
      else:
        print("AVERTO:   "+str(self._depth)+"-data: kn="+kn+" ;"+data+";klaso="+klaso.__name__+" - "+obj.__class__.__name__)
      #if obj and not isset:
      #  print(str(self._depth)+"data: kn="+kn+" ;"+data+".")
      #if obj:
      #  print(str(self._depth)+"data: kn="+kn+" ;"+data+".")
      #  #maljsonigi(obj,data)
  def close(self):    
    pass

import xml.etree.ElementTree as ET
def malxmligi(obj,d, nepre=False):
  parser=ET.XMLParser(target=obj)
  parser.feed(d)
  parser.close()
  

class xmlGedcomx(xmlero,Gedcomx):
  pass
