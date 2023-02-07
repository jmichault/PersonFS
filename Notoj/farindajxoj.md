
* note : fsid fusionné : GZKW-DLY,GJ7P-84L;
        ; fsid George Washington : KNDX-MKG
	; fsid avec parents multiples : 9CSJ-L2D
	; fsid avec lieu non standardisé : LR24-CQK

# à faire pour version 1.3
## prioritaires
* bogues :
  * comparaison : la liste des filtres est celle du premier lancement.
* gramplet :
  * si coche d'un parent, enfant ou conjoint :
    * si absent de FS mais a un FSTID : accepter.
    * si absent de FS et pas de FSTID : suggérer d'aller sur la fiche.
    * si absent de gramps : chercher le FSID dans gramps.
      * si absent : suggérer l'import.
      * si présent : associer.
  * si coche de sexe : suggérer de faire la correction manuellement.
  * comparer les lieux.
* recherche :
  * création dans FS : lier aux parents et aux enfants qui existent dans FS
  * plus de critères (au moins décès : date + lieu de décès, et lieu général)
* import :
  * normaliser les noms/prénoms ?
  * importer/mettre à jour l'ID des objets : évènement, famille, source, citation.
  * gérer une liaison auto des parents, conjoints et enfants s'ils existent déjà, plutôt que créer en double.
  * cocher systématiquement par défaut «Ne pas réimporter les personnes existantes»
* traduction en français
* mise à jour doc
## facultatifs
* gérer le «LifeSketch»
* maintenir un dictionnaire personne.fsid-handle.
* maintenir un dictionnaire lieu.fsid-handle.
* gestion des relevés (= «records» FS)
* gedcomx : attributs inconnus :
  * Person:fields (dans les recherches ?)
  * Person:Principal, ex. : LR2N-SRM
  * PlaceDescription:placeDescriptionInfo
* exécution de la synchro en arrière-plan ?
* que faire si une personne a deux attributs \_FSFTID ?
* gramplet :
  * rafraichissement sans relecture de FS après saisie dans gramps ?
  * copie des noms vers FS : positionner preferred correctement.
	attention : il doit toujours rester un nom préféré sur FS.
  * comparaison : gérer le drapeau «vivant» sur familysearch.
  * rafraichir : ne recharger la personne que si elle a été modifiée.
  * faire des listes déroulantes.
  * copie d'individus FS manquants dans gramps. (pour l'inverse, on va plutôt se déplacer sur la fiche gramps, faire une recherche et créer si pas trouvé)
  * liaison de conjoints FS vers gramps (le conjoint doit exister dans gramps, sinon : message).
  * suppression d'évènements familysearch.
  * copie d'un contrat de mariage vers FS : ne marche pas car FS n'accepte que les évènements suivants sur un mariage : «Mariage», «Annulation»,«Divorce»,«Mariage de droit coutumier»,«A vécu maritalement», «Aucun enfant».
    * --> lier les autres évènements aux conjoints ?
    * --> transformer les autres évènements en note (pb : pas de date sur les notes, il faut la rajouter dans le texte)?
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
  * gestion de l'évènement StillBirth (= enfant mort-né) ?
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
  * gestion des images et du portrait
* dans l'import :
  * gestion des «attribution» ?
  * charger les ID des lieux , sources , Relationship, ChildAndParentsRelationship ?
* gestion des nicknames à voir
* chargement du portrait FS vers gramps
* chargement des images FS vers gramps
* chargement des images gramps vers FS
* création de personne FS : gérer tous les noms, les sources, …
* effacement de données FS dans le gramplet
* effacement de données gramps dans le gramplet


