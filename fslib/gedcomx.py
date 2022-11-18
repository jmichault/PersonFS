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
  if ( ko == 'bool' or ko == 'str' or ko == 'int') :
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
      if ka == 'set' and len(attr)==0 : continue
      ser[a] = jsonigi(attr)
  return ser

def _aldKlaso(kl2,x):
  if ( hasattr(kl2, "id") and hasattr(kl2, "_indekso")
      and x.get("id") in kl2._indekso ) :
    # FARINDAĴO : aŭ kompleti aktualan 
    return None
  nova = kl2()
  maljsonigi(nova,x)
  if ( hasattr(kl2, "id") and hasattr(kl2, "_indekso")):
    if( hasattr(kl2, "_indekso")) :
      kl2._indekso[x["id"]] = nova
  return nova

def maljsonigi(obj,d, nepre=False):
  if not nepre and hasattr(obj, "maljsonigi"):
    obj.maljsonigi(d)
    return
  if not d: return
  for k in d :
    ann = all_annotations(obj.__class__).get(k)
    kn = str(ann)
    if (  kn == "<class 'bool'>" or kn == "<class 'str'>" or kn == "<class 'int'>" or kn == "<class 'None'>") :
      setattr(obj,k, d[k])
    elif kn == "<class 'dict'>":
      attr = getattr(obj,k, None) or dict()
      attr.update(d[k])
      setattr(obj,k, attr)
      #from objbrowser import browse ;browse(locals())
    elif kn[:4] == 'set[' :
      kn2 = kn[4:len(kn)-1]
      if (  kn2 == "bool" or kn2 == "str" or kn2 == "int" or kn2 == "None") :
        attr = getattr(obj,k, None) or set()
        attr.update(d[k])
        setattr(obj,k, attr)
        #from objbrowser import browse ;browse(locals())
        #setattr(obj,k, d[k])
      else :
        attr = getattr(obj,k, None) or set()
        #if k == 'parts':
        #  from objbrowser import browse ;browse(locals())
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
    else:
      print("clé inconnue: "+obj.__class__.__name__+":"+k)

# gedcomx classes and functions
class Qualifier:
  name: str
  value: str

class Attribution:
  contributor: str
  modified: int
  changeMessage: str
  creator: str
  created: int

class SourceReference:
  description: str
  descriptionId: str
  attribution: Attribution
  qualifiers: set[Qualifier]

class Date():
  """
  " original: str
  " formal: DateFormal
  """
  original: str = None
  formal: DateFormal = None

  def __str__(self):
   if self.formal :
      return str(self.formal)
   elif self.original :
      return self.original
   else : return ''
    

class Note:
  """GEDCOM Note class
  """
  lang: str
  subject: str
  text: str
  attribution: Attribution

class Conclusion:
  id: str = None
  lang: str
  sources: set[SourceReference]
  analysis: str
  notes: set[Note]
  confidence: str
  attribution: Attribution
  links: dict

class PlaceReference:
  original: str = None
  descriptionRef: str = None
  normalized: str = None


class Fact(Conclusion):
  """
  " GEDCOMx Fact class
  "   type: FactType
  "   date: Date
  "   place: str ... PlaceReference
  "   value: str
  "   qualifiers: Qualifier
  "  :param data: FS Fact data
  "  :param tree: a tree object
  """
  id: str = None
  type: str
  date: Date
  place: PlaceReference
  value: str
  qualifiers: Qualifier

  _indekso = dict()

class Qualifier:
  name: str
  value: str

class NamePart:
  type: str
  value: str
  qualifiers: Qualifier

class NameForm:
  lang: str
  fullText: str
  parts: set[NamePart]

class Name(Conclusion):
  """GEDCOM Name class
  """
  id: str = None
  type: str
  nameForms: set[NameForm]=set()
  date: Date
  preferred: bool = None

  _indekso = dict()

class EvidenceReference:
  resource: str
  attribution: Attribution

class Subject(Conclusion):
  extracted: bool = None
  evidence: set[EvidenceReference]
  media: set[SourceReference]
  identifiers: dict

class Gender(Conclusion):
    type: str

class Person(Subject):
  """GEDCOM individual class
  """
  id: str = None
  private: bool
  gender: Gender
  names: set[Name]
  facts: set[Fact]
  living: bool = False
  names: set[Name]
  display: dict

  _indekso = dict()

class Relationship(Subject):
  type: str
  person1: str
  person2: str
  facts: set[Fact]

  """GEDCOM Relationship class
  """

class LangValue:
  lang: str
  value: str

class SourceCitation(LangValue):
  pass

class TextValue(LangValue):
  pass

class Coverage:
  spatial: PlaceReference
  temporal: Date

class Link:
  accept: str
  href: str

class HypermediaEnabledData:
  description: dict

class SourceDescription:
  id: str = None
  resourceType: str
  citations: set[SourceCitation]
  mediaType: str
  about: str
  mediator: str
  publisher: str
  authors: set[str]
  sources: set[SourceReference]
  analysis: str
  componentOf: SourceReference
  titles: set[TextValue]
  notes: set[Note]
  attribution: Attribution
  links: dict
  rights: set[str]
  coverage: set[Coverage]
  descriptions: set[TextValue]
  identifiers: dict
  created: int
  modified: int
  published: int
  repository: str

  _indekso = dict()

class OnlineAccount:
  serviceHomepage: str
  accountName: str

class Address:
  value: str
  city: str
  country: str
  postalCode: str
  stateOrProvince: str
  street: str
  street2: str
  street3: str
  street4: str
  street5: str
  street6: str

class Agent:
  id: str = None
  identifiers: dict
  names: set[TextValue]
  homepage: str
  openid: str
  accounts: OnlineAccount
  emails: set[str]
  phones: set[str]
  addresses: set[Address]
  person: str

  _indekso = dict()

class EventRole(Conclusion):
  person: str
  type: str

class Event(Subject):
  type: str
  date: Date
  place: PlaceReference
  roles: set[EventRole]

class Document(Conclusion):
  type: str
  extracted: bool = None
  textType: str
  text: str
  attribution: Attribution

class GroupRole(Conclusion):
  person: str
  type: str
  date: Date
  details: str

class Group(Subject):
  names: set[TextValue]
  date: Date
  place: PlaceReference
  roles: GroupRole

class PlaceDescription(Subject):
  names: set[TextValue]
  type: str
  place: str
  jurisdiction: str
  latitude: float
  longitude: float
  temporalDescription: Date
  spatialDescription: str

class Gender(Conclusion):
  type: str

class Tree:
  """ gedcomx tree class
  """
  id: str = None
  lang: str
  attribution: Attribution
  persons: set[Person]
  relationships: set[Relationship]
  sourceDescriptions: set[SourceDescription]
  agents: set[Agent]
  events: set[Event]
  documents: set[Document]
  places: set[PlaceReference]
  groups: set[Group]
  description: str  # URI must resolve to SourceDescription

  placeDescriptions: set[PlaceDescription]
  notes: Note
  sourceReferences: set[SourceReference]
  genders: set[Gender]
  names: set[Name]
  facts: set[Fact]

  _indekso = dict()

