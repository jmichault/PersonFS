
* note : fsid fusionné : GZKW-DLY,GJ7P-84L;
        ; fsid George Washington : KNDX-MKG
	; fsid avec parents multiples : 9CSJ-L2D

# à faire pour version 1.2
* bogue : lieux en double avec même url fs.
	cause = lieux fusionnés. exemple : 7345333 fusionné avec 10735890


# à faire pour version 1.3
## prioritaires
* bogues :
 * gramplet : rafraichir ne supprime pas les évènements supprimés dans familysearch.
 * import : la liste des filtres est celle du démarrage de gramps.
* gramplet :
  * copie des noms, sexe, conjoints, enfants
  * comparer les lieux.
* recherche :
  * dates : supprimer le A et les autres caractères non gérés dans la date.
  * création dans FS : lier aux parents et aux enfants qui existent dans FS
  * plus de critères (au moins décès : lieu de décès, lieu général)
* import :
  * gérer une liaison auto des parents, conjoints et enfants s'ils existent déjà, plutôt que créer en double.
  * cocher par défaut «Ne pas réimporter les personnes existantes»
## facultatifs
* gestion des relevés (= «records» FS)
* gedcomx : attributs inconnus :
  * Person:fields
  * Person:Principal, ex. : LR2N-SRM
  * PlaceDescription:placeDescriptionInfo
* exécution de la synchro en arrière-plan ?
* que faire si une personne a deux attributs \_FSFTID ?
* gramplet :
  * comparaison : gérer le drapeau «vivant» sur familysearch.
  * rafraichir : ne recharger la personne que si elle a été modifiée.
  * faire des listes déroulantes.
* recherche :
  * bouton d'import sur la recherche ?
  * cacher ou désactiver le bouton «Aldoni» si l'attribut \_FSFTID est renseigné
	ou afficher un avertissement.
  * recherche accessible depuis le menu ?
  * recherche : charger les suivants
* gérer les langues
* identifier et gérer les pré-requis (requests, gedcomx-v1)
* synchro :
  * accélérer le traitement :
    * lancement en multi-thread (async ?)
  * étiquettes à renseigner :
    * source à joindre.
    * note à joindre.
* ne pas se connecter à FamilySearch avant l'ouverture de la BD
* éviter la double comparaison à l'ouverture de gramps
* import :
  * éviter de créer de nouveaux lieux quand un lieu identique existe déjà
  * accélérer l'import des lieux.
  * accélérer le chargement des notes et sources.

# à faire pour version 2

* gestion pointue des lieux dans l'import , dans le gramplet, dans gedcomx-v1 ?
* gestion des «memories»
* module de liaison automatique.
* module de détection de doublons dans gramps d'après le FSID
* gramplet :
  * lier un enfant ou conjoint gramps avec un enfant ou conjoint FS
  * gestion des sources
  * gestion des notes
* dans l'import :
  * gestion des «attribution» ?
  * charger les ID des lieux , sources , Relationship,ChildAndParentsRelationship ?
* gestion des nicknames à voir
* chargement du portrait FS vers gramps
* chargement des images FS vers gramps
* chargement des images gramps vers FS
* création de personne FS : gérer tous les noms, les sources, …
* effacement de données FS dans le gramplet
* effacement de données gramps dans le gramplet


