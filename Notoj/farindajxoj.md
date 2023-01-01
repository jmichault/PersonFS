
* note : fsid fusionné : GZKW-DLY,GJ7P-84L;
        ; fsid George Washington : KNDX-MKG
	; fsid avec parents multiples : 9CSJ-L2D

# à faire pour version 1.2

## prioritaires
* gramplet : empêcher de cocher ce qui n'est pas traité.
## facultatifs
* comparaison : gérer le drapeau «vivant» sur familysearch.
* bogue gramplet : rafraichir ne supprime pas les évènements supprimés dans familysearch.
* bogue import : la liste des filtres est celle du démarrage de gramps.
* gestion des relevés (= «records» FS)
* gedcomx : attributs inconnus :
  * Person:fields
  * Person:Principal, ex. : LR2N-SRM
* exécution de la synchro en arrière-plan ?
* que faire si une personne a deux attributs \_FSFTID ?
* import :
  * gérer une liaison auto des parents, conjoints et enfants s'ils existent déjà, plutôt que créer en double.
  * cocher par défaut «Ne pas réimporter les personnes existantes»
  * option pour ne pas importer les notes
  * option pour ne pas importer les sources
  * pb. : faut-il importer la famille si on n'a pas le conjoint ?
          mais on a besoin de la famille si on a les enfants…
            --> forcer l'option conjoint si on charge les descendants.
          --> on n'importe pas si l'un des conjoints manque.
          ou mettre à jour les familles quand ré-import ?
* gramplet :
  * rafraichir : ne recharger la personne que si elle a été modifiée.
  * copie des noms, sexe, conjoints, enfants
  * comparer les lieux.
  * création dans FS : lier aux parents et aux enfants qui existent dans FS
  * faire des listes déroulantes.
  * gestion des sources
  * gestion des notes
* recherche :
  * bouton d'import sur la recherche ?
  * cacher ou désactiver le bouton «Aldoni» si l'attribut \_FSFTID est renseigné
	ou afficher un avertissement.
  * plus de critères (au moins décès : lieu de décès, lieu général)
  * recherche accessible depuis le menu ?
  * recherche : charger les suivants
  * dates : supprimer le A et les autres caractères non gérés dans la date.
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

# à faire pour version 2

* gestion pointue des lieux dans l'import , dans le gramplet, dans gedcomx-v1 ?
* gestion des «memories»
* module de liaison automatique.
* module de détection de doublons dans gramps d'après le FSID
* gramplet :
  * lier un enfant ou conjoint gramps avec un enfant ou conjoint FS
  * gestion des sources
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


