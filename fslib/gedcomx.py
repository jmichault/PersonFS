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

# gedcomx klasoj
class ExtensibleData:
  id: str
  _indekso: dict = dict()

class HasText:
  text: str

class Link:
  href: str
  template: str
  title: str
  type: str
  accept: str
  allow: str
  hreflang: str
  count: int
  offset: int
  results: int

class Qualifier:
  name: str
  value: str

class HypermediaEnabledData(ExtensibleData):
  links: dict[str,Link]

class ResourceReference:
  resourceId: str
  resource: str

class Attribution(ExtensibleData):
  contributor: str
  modified: int
  changeMessage: str
  changeMessageResource: str
  creator: 	ResourceReference
  created: int

class SourceReference(HypermediaEnabledData):
  description: str
  descriptionId: str
  attribution: Attribution
  qualifiers: set[Qualifier]

class ReferencesSources:
  sources: set[SourceReference]

class TextValue:
  lang: str
  value: str

class VocabElement:
  id: str
  uri: str
  subclass: str
  type: str
  sortName: str
  labels: set[TextValue]
  descriptions: set[TextValue]
  sublist: str
  position: int

class VocabElementList:
  id: str
  title: str
  description: str
  uri: str
  elements: set[VocabElement]

class FamilyView(HypermediaEnabledData):
  parent1: ResourceReference
  parent2: ResourceReference
  children: set[ResourceReference]

class Date(ExtensibleData):
  """
  " original: str
  " formal: DateFormal
  """
  original: str
  formal: DateFormal
  normalized: set[TextValue]
  confidence: str

  def __str__(self):
   if self.formal :
      return str(self.formal)
   elif self.original :
      return self.original
   else : return ''
    
class DisplayProperties(ExtensibleData):
  name: str
  gender: str
  lifespan: str
  birthDate: str
  birthPlace: str
  deathDate: str
  deathPlace: str
  marriageDate: str
  marriagePlace: str
  ascendancyNumber: str
  descendancyNumber: str
  relationshipDescription: str
  familiesAsParent: set[FamilyView]
  familiesAsChild: set[FamilyView]
  role: str

class Note(HypermediaEnabledData):
  subject: str
  text: str
  attribution: Attribution
  lang: str

class HasNotes:
  notes: set[Note]

class Conclusion(HypermediaEnabledData):
  attribution: Attribution
  sources: set[SourceReference]
  analysis: ResourceReference
  notes: set[Note]
  lang: str
  confidence: str
  sortKey: str

class CitationField:
  # FARINDAĴO : ne dokumenta klaso ???
  pass

class SourceCitation(TextValue,HypermediaEnabledData):
  citationTemplate: ResourceReference
  fields: set[CitationField]

class PlaceReference(ExtensibleData):
  original: str
  normalized: set[TextValue]
  description: str
  confidence: str
  latitude: float # family search !
  longitude: float # family search !
  names: set[TextValue] # family search !

class HasDateAndPlace:
  date: Date
  place: PlaceReference

class Fact(Conclusion):
  date: Date
  place: PlaceReference
  value: str
  qualifiers: set[Qualifier]
  type: str

class HasFacts:
  facts: set[Fact]

class Qualifier:
  name: str
  value: str

class NamePart(ExtensibleData):
  type: str
  value: str
  qualifiers: set[Qualifier]

class NameForm(ExtensibleData):
  lang: str
  parts: set[NamePart]
  fullText: str
  nameFormInfo: str  # family search !

class Name(Conclusion):
  preferred: bool
  date: Date
  nameForms: set[NameForm]
  type: str

class EvidenceReference(HypermediaEnabledData):
  resource: str
  resourceId: str
  attribution: Attribution

class Subject(Conclusion):
  evidence: set[EvidenceReference]
  media: set[SourceReference]
  identifiers: dict[str,set]
  extracted: bool

class Gender(Conclusion):
  type: str

class PersonInfo:
  canUserEdit: bool
  privateSpaceRestricted: bool
  readOnly: bool
  visibleToAll: bool

class Person(Subject):
  private: bool
  living: bool
  gender: Gender
  names: set[Name]
  facts: set[Fact]
  display: DisplayProperties
  personInfo: set[PersonInfo]  # family search !

class Relationship(Subject):
  person1: str
  person2: str
  facts: set[Fact]
  type: str


class Coverage(HypermediaEnabledData):
  spatial: PlaceReference
  temporal: Date

class SourceDescription(HypermediaEnabledData):
  citations: set[SourceCitation]
  mediator: ResourceReference
  publisher: ResourceReference
  authors: set[str]
  sources: set[SourceReference]
  analysis: ResourceReference
  componentOf: SourceReference
  titles: set[TextValue]
  notes: set[Note]
  attribution: Attribution
  identifiers: dict[str,set]
  rights: set[str]
  replacedBy: str
  replaces: set[str]
  statuses: set[str]
  lang: str
  about: str
  version: str
  resourceType: str
  mediaType: str

  mediator: str
  coverage: set[Coverage]
  descriptions: set[TextValue]
  created: int
  modified: int
  published: int
  repository: str

class OnlineAccount(ExtensibleData):
  serviceHomepage: ResourceReference
  accountName: str

class Address(ExtensibleData):
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
  value: str

class Agent(HypermediaEnabledData):
  identifiers: dict[str,set]
  names: set[TextValue]
  homepage: ResourceReference
  openid: ResourceReference
  accounts: set[OnlineAccount]
  emails: set[ResourceReference]
  phones: set[ResourceReference]
  addresses: set[Address]
  person: ResourceReference

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
  extracted: bool
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

class PlaceDisplayProperties(ExtensibleData):
  name: str
  fullName: str
  type: str

class PlaceDescription(Subject):
  names: set[TextValue]
  temporalDescription: Date
  latitude: float
  longitude: float
  spatialDescription: ResourceReference
  place: ResourceReference
  jurisdiction: ResourceReference
  display: PlaceDisplayProperties
  type: str

class Gender(Conclusion):
  type: str

class ChildAndParentsRelationship(Subject):
  # https://www.familysearch.org/developers/docs/api/types/json_ChildAndParentsRelationship
  parent1: ResourceReference
  parent2: ResourceReference
  child: ResourceReference
  parent1Facts: set[Fact]
  parent2Facts: set[Fact]

class Gedcomx(HypermediaEnabledData):
  # de https://github.com/FamilySearch/gedcomx/blob/master/specifications/xml-format-specification.md#gedcomx-type
  attribution: Attribution
  persons: set[Person]
  relationships: set[Relationship]
  sourceDescriptions: set[SourceDescription]
  agents: set[Agent]
  events: set[Event]
  places: set[PlaceDescription]
  documents: set[Document]
  groups: set[Group]
  lang: str
  description: str  # URI must resolve to SourceDescription
  # ne en specifo
  notes: Note
  childAndParentsRelationships: set[ChildAndParentsRelationship]
  sourceReferences: set[SourceReference]
  genders: set[Gender]
  names: set[Name]
  facts: set[Fact]

