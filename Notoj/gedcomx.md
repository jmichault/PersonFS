# sources
doc «officielle» : (mais pourtant pas à jour)
https://github.com/FamilySearch/gedcomx/blob/master/specifications/json-format-specification.md
https://github.com/FamilySearch/gedcomx/blob/master/specifications/conceptual-model-specification.md

un peu plus pratique, mais incomplète (quand je l'ai consultée, il manquait par exemple les classes Event et Document, qui sont pourtant des «toplevel» :
https://www.familysearch.org/developers/docs/api/gx_json
https://www.familysearch.org/developers/docs/api/fs_json

sans surprise familysearch ne suit pas sa propre norme, il rajoute des classes et des champs, et en ignore certains…

# traduire les types en type python :
boolean                 --> bool
string                  --> str
map of array of string  --> dict[str,set]   (identifiers)
map of Link             --> dict[str,Link]  (links)
array                   --> set
classe                  --> classe
array of classe         --> set[classe]

# liste des classes gedcomx :

## classe racine du fichier gedcomx :
* Gedcomx(HypermediaEnabledData)

## classes «toplevel» :
* Person(Subject)
* Relationship(Subject)
* SourceDescription(HypermediaEnabledData)
* Agent(HypermediaEnabledData)
* Event(Subject)
* PlaceDescription(Subject)
* Document(Conclusion)

## classes se résumant à une énumération de chaînes :
ConfidenceLevel
FactType
GenderType
NamePartType
NameType
RelationshipType
ResourceType

## classes qui n'héritent d'aucune autre :
* ExtensibleData	met en place id
* HasDateAndPlace (utilité ?)
* HasFacts (utilité ?)
* HasNotes (utilité ?)
* HasText (utilité ?)
* Link
* Qualifier
* ReferencesSources (utilité ?)
* ResourceReference   (mettre et gérer un index ?)
* TextValue
* VocabElement
* VocabElementList

## classes héritant d'une autre et dérivées par d'autres :
* HypermediaEnabledData(ExtensibleData)
* Conclusion(HypermediaEnabledData)
* Subject(Conclusion)

##  autres classes
* Address(ExtensibleData)
* Attribution(ExtensibleData)
* Coverage(HypermediaEnabledData)
* Date(ExtensibleData)
* DisplayProperties(ExtensibleData)
* EvidenceReference(HypermediaEnabledData)
* Fact(Conclusion)
* FamilyView(HypermediaEnabledData)
* Gender(Conclusion)
* Name(Conclusion)
* NameForm(ExtensibleData)
* NamePart(ExtensibleData)
* Note(HypermediaEnabledData)
* OnlineAccount(ExtensibleData)
* PlaceDisplayProperties(ExtensibleData)
* PlaceReference(ExtensibleData)
* SourceCitation(HypermediaEnabledData)
* SourceReference(HypermediaEnabledData)

##  ajouts FS :
* PersonInfo
* CitationField : pas documentée ???
