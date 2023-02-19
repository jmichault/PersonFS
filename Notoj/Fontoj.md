
# sources intéressantes
* code officiel java : https://github.com/FamilySearch/gedcomx-java
* code officiel php : https://github.com/FamilySearch/gedcomx-php
* https://github.com/dekoza/pyGedcomX
  * peu avancé : pas d\'import, pas d\'export
* spécifications gedcom 7 : https://gedcom.io/specifications/FamilySearchGEDCOMv7.html
  * le plus utile, notamment : https://gedcom.io/specifications/FamilySearchGEDCOMv7.html#records

# Exemple 1 : acte saisi dans FS : AD42 2NUM9_117_2 vue 6/78, double mariage
## Dans gramps :
* dépôt R0007 =
  propriétés :
  * nom = «France, Loire : archives départementales.»
  * type = archives
  * adresses : 
  * urls : site=«https://…»
  * notes :
* source S07216 
  proriétés :
  * titre : «Juré.- Baptêmes, mariages, sépultures - 1720 - 1745»
  * auteur :
  * pub. info. :
  * abbréviation : AD42, 2NUM9_117_2
  * notes : 
  * galerie :
  * attributs :
  * dépôts : R0007
  * !!! pas d'url ??? (==> à mettre en note ou en attribut )
* citation C15667
  propriétés :
  * source=S07216
  * date=1721-11-21
  * volume/page=vue 6/78
  * niveau de confiance=«très haut»
  * notes :
    * citation=«note : deux mariages en …»
    * transcription=«…»
  * galerie :
  * attributs :
  * !!! pas d'url ??? (==> à mettre en note ou en attribut )
     en note : le lien est cliquable, mais pas géré par l'export gedcomforgeneanet.
     en attribut : le lien n'est pas cliquable, mais géré par l'export.
* attachements
  --> la citation peut être liée aux 2 mariages, aux 2 familles, aux 4 époux, aux 4 liens parent-enfants, aux évènements naissance des époux…
  propriétés de l'attachement : aucune ?
## dans FS :
* source = https://www.familysearch.org/tree/sources/viewedit/Q318-NX7
  propriétés :
  * date=1721-11-21
  * titre=«Claude Dumas x Marie Barjat et Jean Dumas x Bénigne Meunier. France, Loire, Juré.»
  * url=«https://archives.loire.fr/ark:/51302/vta54d46fa1795267c1/daogrp/0/6»
  * référence=«France, Loire : archives départementales.\ncôte : 2NUM9_117_2 - Juré.- Baptêmes, mariages, sépultures - 1720 - 1745\nvue 6/78.»
  * note=«note : deux mariages en …»
  * date de modification
  * raison de la modification
* attachements : les deux liens conjuguaux, les 4 époux.
  propriétés :
  * signets
  * raison de l'ajout.
## correspondances
* gr-dépôt + gr-source + gr-citation.volume-page ~= fs-source.référence
* gr-citation.date = fs-source.date
* attachement gramps ~= attachement FS


# Exemple 2 : acte trouvé dans FS.
