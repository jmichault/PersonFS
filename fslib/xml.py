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
from fslib.json import maljsonigi, all_annotations, _aldKlaso

verb=True

class xmlero:
  def __init__(self):
    self._depth=0
    self._obj={ 1:self}
    self._eroj={ 1:'gedcomx'}
    self._klaso={ 1:self.__class__.__name__}
    self._isset={ 1:False}
    self._isdict={ 1:False}
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
    if verb: print("  start:"+str(kn)+" ; "+str(attrib))
    ann = all_annotations(patro.__class__).get(kn)
    if ann:
      if verb : print("  simple:"+str(ann))
      kl2 = ann
      obj = getattr(patro,kn, None) or kl2()
      if not obj:
        obj=kl2()
      maljsonigi(obj,attrib)
      setattr(patro,kn,obj)
      self._eroj[self._depth]=kn
      self._obj[self._depth]=obj
      self._klaso[self._depth]=ann
      self._isset[self._depth]=False
      self._isdict[self._depth]=False
      return
    kn=kn+"s"
    self._eroj[self._depth]=kn
    ann = all_annotations(patro.__class__).get(kn)
    if not ann:
      print("malxmligi-start:AVERTO: depth="+str(self._depth)+" xml-ne konata ero: "+patro.__class__.__name__+"."+tag+"-kn="+kn)
      return
    sann = str(ann)
    self._klaso[self._depth]=ann
    if sann[:4] == 'set[':
      self._isset[self._depth]=True
      kl2 = ann.__args__[0]
      print("   set[: "+sann+" ; attrib="+str(attrib))
      attr = getattr(patro,kn, None) or set()
      setattr(patro,kn, attr)
      #from objbrowser import browse ;browse(locals())
    elif sann[:9] == 'dict[str,' : # speciala kazo : dict[str,Link]
      self._isdict[self._depth]=True
      kl2 = ann.__args__[1]
      print("   dict[: "+sann+" ; attrib="+str(attrib))
      attr = getattr(patro,kn, None) or dict()
      setattr(patro,kn, attr)
    else:
      print("AVERTO: ne konata klaso: "+patro.__class__.__name__+":"+kn+" - "+sann)
    obj=kl2()
    self._obj[self._depth]=obj
    if "Link" in sann:# speciala kazo : dict[str,Link]
      rel = attrib['rel']
      attrib.pop('rel')
      maljsonigi(obj,attrib)
      attr[rel]=obj
    else:
      maljsonigi(obj,attrib)
  def end(self, tag):             # Vokita por ĉiu ferma etikedo.
    obj = self._obj.get(self._depth)
    kn = self._eroj.get(self._depth)
    isset = self._isset.get(self._depth)
    isdict = self._isdict.get(self._depth)
    if kn == 'changeMessage':
       print("  obj="+str(obj))
    self._depth -= 1
    patro = self._obj.get(self._depth)
    if verb: print("  end:"+str(kn)+" ; "+tag)
    if self._depth >= 1:
      if isset:
        attr = getattr(patro,kn, None) or set()
        attr.add(obj)
        setattr(patro,kn, attr)
      elif isdict:
        pass
        #attr = getattr(patro,kn, None) or dict()
        #attr.add(obj)
        #setattr(patro,kn, attr)
      else:
        if obj:
          setattr(patro,kn,obj)
      self._obj[self._depth+1] = None
      self._eroj[self._depth+1] = ''
      self._isset[self._depth+1]=False
      self._isdict[self._depth+1]=False
  def data(self, data):
    if data and not data.isspace() :
      obj = self._obj.get(self._depth)
      kn = self._eroj.get(self._depth)
      klaso = self._klaso.get(self._depth)
      isset = self._isset.get(self._depth)
      isdict = self._isdict.get(self._depth)
      if verb: print("    data:"+str(kn)+" ; "+data)
      if obj != None and klaso and (klaso.__name__ == 'str' or klaso.__name__ == 'bool' or klaso.__name__ == 'int'):
        self._obj[self._depth]=data
      elif obj != None and klaso and klaso.__name__ == 'DateFormal':
        maljsonigi(obj,data)
      elif obj != None and obj.__class__.__name__ == 'set':
        obj.add(data)
      elif obj != None and klaso and klaso.__name__ == 'set' and obj.__class__.__name__ == 'TextValue':
        obj.value = data
      else:
        print("malxmligi:AVERTO:   "+str(self._depth)+"-data: kn="+kn+" ;"+data+";klaso="+str(klaso)+" - "+str(obj))
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


def xmligi(obj):
  r = ET.Element(obj.__class__.__name__.lower())
  r.attrib['xmlns']='http://gedcomx.org/v1/'
  farixml(r,obj)
  return ET.ElementTree(r)

def farixml(r,obj):
  for a in dir(obj):
    if not a.startswith('_') and not callable(getattr(obj, a)) :
      attr = getattr(obj,a)
      ka = attr.__class__.__name__
      if ka == 'NoneType' : continue
      if (ka == 'set' or ka == 'list' or ka == 'str' or ka == 'dict') and len(attr)==0 : continue
      kn = str(ka)
      if (kn == 'str') or (kn == 'int') or (kn == 'bool'):
        r.attrib[a]=str(attr)
      elif (kn == 'set'):
        if a[len(a)-1]=='s':
          a = a[:len(a)-1]
        for x in attr:
         sub = ET.SubElement(r,a)
         farixml(sub,x)
      elif (kn == 'dict'):
        if a[len(a)-1]=='s':
          a = a[:len(a)-1]
        for k,v in attr.items():
         sub = ET.SubElement(r,a)
         if a == 'link':
           sub.attrib['rel']=k
         elif a =='identifier' :
           sub.attrib['type']=k
         else:
           sub.attrib['type']=k
           print('nekonata dict: '+a)
         farixml(sub,v)
      else :
        sub = ET.SubElement(r,a)
        farixml(sub,attr)
  

class xmlGedcomx(xmlero,Gedcomx):
  pass
