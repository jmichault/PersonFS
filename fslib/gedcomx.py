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

from fslib.dateformal import DateFormal

def jsonigi(obj):
  if hasattr(obj, "jsonigi"):
    return obj.jsonigi()
  ko = obj.__class__.__name__
  if ( ko == 'bool' or ko == 'str' or ko == 'int') :
    return obj
  elif ( ko == 'set' or ko == 'list'):
    if len(obj) == 0: return
    return [ jsonigi(o) for o in obj ]
  elif ko == 'dict' :
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

def maljsonigi(obj,d):
  if hasattr(obj, "maljsonigi"):
    obj.maljsonigi(d)
    return
  if not d: return
  for k in d:
    attr = getattr(obj,k, None)
    ann = obj.__annotations__.get(k)
    kn = str(ann)
    if kn != 'None' :
      if (  kn == "<class 'bool'>" or kn == "<class 'str'>" or kn == "<class 'int'>" or kn == "<class 'None'>") :
        setattr(obj,k, d[k])
      elif kn == "<class 'dict'>":
        setattr(obj,k, d[k])
      elif kn[:4] == 'set[' :
        kn2 = kn[4:len(kn)-1]
        #from objbrowser import browse ;browse(globals())
        if kn2:
          if (  kn2 == "bool" or kn2 == "str" or kn2 == "int" or kn2 == "None") :
            setattr(obj,k, d[k])
          else:
            kn2s = kn2.split('.')
            kl2 =globals()[kn2s[len(kn2s)-1]]
            for x in d[k] :
              novo = kl2()
              maljsonigi(novo,x)
              attr.add(novo)
        else :
          print("ne kognita : "+k)
      elif kn[:8] == "<class '" :
        kn2 = kn[8:len(kn)-2]
        if kn2:
          kn2s = kn2.split('.')
          kl2 =globals()[kn2s[len(kn2s)-1]]
          novo = kl2()
          maljsonigi(novo,d[k])
          setattr(obj,k, novo)
        else:
          print(_("farindaĵo : ")+kn)
          print(attr)
          print(ann)
      else :
        if kn != 'NoneType' :
          print(_("klaso ne json-igita(2) : ")+kn)
          print(attr)
          print(ann)

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
    qualifiers: set[Qualifier] = set()

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
    id: str
    lang: str
    sources: set[SourceReference] = set()
    analysis: str
    notes: set[Note] = set()
    confidence: str
    attribution: Attribution

class PlaceReference:
    original: str = ''
    descriptionRef: str = ''


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
  type: str
  date: Date
  place: PlaceReference
  value: str
  qualifiers: Qualifier

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
    parts: set[NamePart] = set()

class Name(Conclusion):
    """GEDCOM Name class
    """
    type: str
    nameForms: set[NameForm]=set()
    date: Date
    preferred: bool = False

class Identifier:
    value: str
    type: str

class EvidenceReference:
    resource: str
    attribution: Attribution

class Subject(Conclusion):
    extracted: bool = False
    evidence: set[EvidenceReference] = set()
    media: set[SourceReference] = set()
    identifiers: set[Identifier] = set()

class Gender(Conclusion):
    type: str

class Person(Subject):
    """GEDCOM individual class
    """
    private: bool
    gender: Gender
    names: set[Name] = set()
    facts: set[Fact] = set()
    attribution: Attribution
    links: dict

    id: str = None
    living: bool = True
    names: set[Name] = set()
    identifiers: set[int] = set()


class Relationship(Subject):
    type: str
    person1: str
    person2: str
    facts: set[Fact] = set()

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
  description: dict = dict()

class SourceDescription:
    id: str
    links: dict
    resourceType: str
    citations: set[SourceCitation] = set()
    mediaType: str
    about: str
    mediator: str
    publisher: str
    authors: set[str] = set()
    sources: set[SourceReference] = set()
    analysis: str
    componentOf: SourceReference
    titles: set[TextValue] = set()
    notes: set[Note] = set()
    attribution: Attribution
    rights: set[str] = set()
    coverage: set[Coverage] = set()
    descriptions: set[TextValue] = set()
    identifiers: dict = dict()
    created: int
    modified: int
    published: int
    repository: str

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
    id: str
    identifiers: set[Identifier] = set()
    names: set[TextValue] = set()
    homepage: str
    openid: str
    accounts: OnlineAccount
    emails: set[str] = set()
    phones: set[str] = set()
    addresses: set[Address] = set()
    person: str

class EventRole(Conclusion):
    person: str
    type: str

class Event(Subject):
    type: str
    date: Date
    place: PlaceReference
    roles: set[EventRole] = set()

class Document(Conclusion):
    type: str
    extracted: bool = False
    textType: str
    text: str
    attribution: Attribution

class GroupRole(Conclusion):
    person: str
    type: str
    date: Date
    details: str

class Group(Subject):
    names: set[TextValue] = set()
    date: Date
    place: PlaceReference
    roles: GroupRole

class PlaceDescription(Subject):
    names: set[TextValue] = set()
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
    id: str
    lang: str
    attribution: Attribution
    persons: set[Person] = set()
    relationships: set[Relationship] = set()
    sourceDescriptions: set[SourceDescription] = set()
    agents: set[Agent] = set()
    events: set[Event] = set()
    documents: set[Document] = set()
    places: set[PlaceReference] = set()
    groups: set[Group] = set()
    description: str  # URI must resolve to SourceDescription

    placeDescriptions: set[PlaceDescription] = set()
    notes: Note
    sourceReferences: set[SourceReference] = set()
    genders: set[Gender] = set()
    names: set[Name] = set()
    facts: set[Fact] = set()

