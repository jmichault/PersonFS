
* note : menus contextuels sur grid : voir gramplet descendants
* note : fsid fusionné : GZKW-DLY,GJ7P-84L, fsid avec doublons : G4Y1-1NV
        fsid George Washington : KNDX-MKG

# à faire pour version 1.1

## prioritaires
* gestion de la synchronisation
  * prendre en compte le forçage.
  * étiquettes à renseigner :
    * FS\_Gramps : changé dans gramps depuis la dernière fois que l'étiquette FS\_Konf a été positionnée, ou que tout était conforme (étiquette FS\_Identa et aucune autre)
    * FS\_FS : changé dans FamilySearch depuis la dernière fois que l'étiquette FS\_Konf a été positionnée, ou que tout était conforme (étiquette FS\_Identa et aucune autre)
    * FS\_Konf : effacer si discordance et modification depuis la dernière fois que l'étiquette FS\_Konf a été positionnée.
* gramplet
  * affichage de l'état, exemple :
    * 1e ligne = état des renseignements essentiels (nom, prénom, sexe, naissance, décès)
    * 2e ligne = état des liens familiaux (parents, conjoints, enfants)
    * 3e ligne = état des évènements
    * 4e ligne = état des sources et notes
    * 5e ligne ? état des autres renseignements (portrait, médias, …)
  * bug : parents multiples pas bien gérés
  * bien définir la signification des couleurs, ex. :
    * vert : tout bon
    * vert jaune : essentiel bon, différences non essentielles
    * rouge : renseignement essentiel présent des 2 cotés, mais discordance sur l'essentiel
    * orange : présent des 2 cotés, mais discordance sur l'essentiel
    * jaune : présent que dans gramps
    * jaune 3 : présent que dans FS.
  * mettre la bonne couleur partout
* import :
  * gérer une liaison auto des parents, conjoints et enfants s'ils existent déjà, plutôt que créer en double.
* traduction en français.
## facultatifs
* priorité sur les tags ?
* exécution de la synchro en arrière-plan ?
* que faire si une personne a deux attributs \_FSFTID ?
* import :
  * cocher par défaut «Ne pas réimporter les personnes existantes»
  * option pour ne pas importer les notes
  * option pour ne pas importer les sources
  * pb. : faut-il importer la famille si on n'a pas le conjoint ?
          mais on a besoin de la famille si on a les enfants…
            --> forcer l'option conjoint si on charge les descendants.
          --> on n'importe pas si l'un des conjoints manque.
          ou mettre à jour les familles quand ré-import ?
* gramplet :
  * création dans FS : lier aux parents et aux enfants qui existent dans FS
  * faire des listes déroulantes.
  * rafraichir : supprimer aussi les mariages dans l'arbre FS avant de recharger.
  * double clic sur la ligne d'une personne --> aller dessus
  * gestion des sources
  * gestion des notes
* recherche :
  * cacher ou désactiver le bouton «Aldoni» si l'attribut \_FSFTID est renseigné
  * double clic sur une ligne --> ouverture familysearch ?
  * bouton d'import sur la recherche ?
  * cacher ou désactiver le bouton «Aldoni» si l'attribut \_FSFTID est renseigné
  * plus de critères (au moins décès : lieu de décès, lieu général)
  * recherche accessible depuis le menu
  * recherche : charger les suivants
  * dates : supprimer le + et les autres caractères incorrects
* gérer les langues
* identifier et gérer les pré-requis (requests, gedcomx-v1)
* synchro :
  * accélérer le traitement :
    * lancement en multi-thread (async ?)
  * étiquettes à renseigner :
    * source à joindre.
    * note à joindre.

# à faire pour version 1.2

* gramplet :
  * copie de données gramps vers FS 
  * copie de données FS vers gramps 
* gestion des relevés (= «records» FS)

# à faire pour version 2

* gestion pointue des lieux dans l'import , dans le gramplet, dans gedcomx-v1 ?
* gestion des «memories»
* module de liaison automatique.
* modulede détection de doublons dans gramps d'après le FSID
* dans la recherche :
  * lien vers écran de fusion
* dans le gramplet :
  * lier un enfant ou conjoint gramps avec un enfant ou conjoint FS
* dans l'import :
  * gestion des «attribution»
  * charger les ID des familles
* gestion des nicknames à voir
* gestion des sources dans le gramplet
* chargement du portrait FS vers gramps
* chargement des images FS vers gramps
* chargement des images gramps vers FS
* barres de progression
* création de personne FS : gérer tous les noms, les sources, …
* copies de données FS vers gramps dans le gramplet
* copies de données gramps vers FS dans le gramplet
* effacement de données FS dans le gramplet
* effacement de données gramps dans le gramplet

