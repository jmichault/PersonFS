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

from collections import ChainMap

from fslib.dateformal import DateFormal

def all_annotations(cls) -> ChainMap:
    """Liveras vortar-similan ChainMap kiu inkluzivas komentadojn por ĉiuj
        atributoj difinitaj en klaso aŭ hereditaj de superklasoj."""
    return ChainMap(*(c.__annotations__ for c in cls.__mro__ if '__annotations__' in c.__dict__) )

def jsonigi(obj):
  """Liveras jsonigita version de obj.
  """
  if hasattr(obj, "jsonigi"):
    return obj.jsonigi()
  ko = obj.__class__.__name__
  if ( ko == 'bool' or ko == 'str' or ko == 'int' or ko == 'float') :
    return obj
  if ( ko == 'set' or ko == 'list'):
    if len(obj) == 0: return
    return [ jsonigi(o) for o in obj ]
  if ko == 'dict' :
    if len(obj) == 0: return
    x = dict()
    for k,v in obj.items() :
      json_k=jsonigi(k)
      json_v=jsonigi(v)
      x[json_k] = json_v
    return x
  ser = dict()
  for a in dir(obj):
    if not a.startswith('_') and not callable(getattr(obj, a)) :
      attr = getattr(obj,a)
      ka = attr.__class__.__name__
      if ka == 'NoneType' : continue
      if (ka == 'set' or ka == 'list') and len(attr)==0 : continue
      ser[a] = jsonigi(attr)
  return ser

def _aldKlaso(kl2,x):
  havasId = all_annotations(kl2).get("id")
  havasIndekso = all_annotations(kl2).get("_indekso")
  if ( havasId and havasIndekso
      and x.get("id") in kl2._indekso ) :
    obj=kl2._indekso[x.get("id")]
  else :
    obj = kl2()
  maljsonigi(obj,x)
  if ( havasId and havasIndekso):
    if( x.get("id") ) :
      kl2._indekso[x["id"]] = obj
  return obj

def maljsonigi(obj,d, nepre=False):
  if not nepre and hasattr(obj, "maljsonigi"):
    obj.maljsonigi(d)
    return
  if not d: return
  for k in d :
    #try:
    ann = all_annotations(obj.__class__).get(k)
    #except:
    #  from objbrowser import browse ;browse(locals())
    #  return:
    kn = str(ann)
    if (  kn == "<class 'bool'>" or kn == "<class 'str'>" or kn == "<class 'int'>" or kn == "<class 'float'>" or kn == "<class 'None'>") :
      setattr(obj,k, d[k])
    elif kn == "<class 'set'>":
      attr = getattr(obj,k, None) or set()
      attr.update(d[k])
      setattr(obj,k, attr)
    elif kn == "<class 'list'>":
      attr = getattr(obj,k, None) or list()
      attr.update(d[k])
      setattr(obj,k, attr)
    elif kn == "<class 'dict'>":
      attr = getattr(obj,k, None) or dict()
      attr.update(d[k])
      setattr(obj,k, attr)
    elif kn[:4] == 'set[' :
      kn2 = kn[4:len(kn)-1]
      if (  kn2 == "bool" or kn2 == "str" or kn2 == "int" or kn2 == "float" or kn2 == "None") :
        attr = getattr(obj,k, None) or set()
        attr.update(d[k])
        setattr(obj,k, attr)
      else :
        attr = getattr(obj,k, None) or set()
        kn2s = kn2.split('.')
        kl2 =globals()[kn2s[len(kn2s)-1]]
        for x in d[k] :
          nova = _aldKlaso(kl2,x)
          if nova : attr.add(nova)
        setattr(obj,k, attr)
    elif kn[:8] == "<class '" :
      kn2 = kn[8:len(kn)-2]
      kn2s = kn2.split('.')
      kl2 =globals()[kn2s[len(kn2s)-1]]
      nova = _aldKlaso(kl2,d[k])
      if nova: 
        setattr(obj,k, nova)
    elif kn[:9] == 'dict[str,' : # speciala kazo : dict[str,Link]
     if "Link" in kn:# speciala kazo : dict[str,Link]
      attr = getattr(obj,k, None) or dict()
      for k2,v in d[k].items() :
        nova = _aldKlaso(Link,v)
        if nova : attr[k2] =nova
      setattr(obj,k, attr)
     if ",set]" in kn:# speciala kazo : dict[str,set]
      attr = getattr(obj,k, None) or dict()
      for k2,v in d[k].items() :
        attr[k2] =v
      setattr(obj,k, attr)
    else:
      print("nekonata ero: "+obj.__class__.__name__+":"+k)
      #from objbrowser import browse ;browse(locals())

