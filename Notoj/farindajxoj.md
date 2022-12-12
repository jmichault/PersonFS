
* note : menus contextuels sur grid : voir gramplet descendants

# gedcomx
* gestion des «attribution»
* gestion pointue des lieux dans l'import , dans le gramplet, dans gedcomx-v1 ?
* gestion des «memories»
* chargement du portrait FS vers gramps
* chargement des images FS vers gramps

# à faire pour version 1.1

## prioritaires
* gestion de la synchronisation
  * outil de mise à jour de l'état de synchro
    * doit être interruptible.
    * ne doit pas changer la date de dernière modification de l'individu.
  * étiquettes à renseigner :
    * FS\_Identa : informations essentielles conformes (nom/prénom principal, dates de naissance et décès).
    * FS\_Esenco : il y a une information essentielle à synchroniser (nom/prénom principal, dates de naissance et décès).
    * FS\_Nomo : il y a un nom à synchroniser (autre que le principal).
    * FS\_Gepatro : il y a un parent à synchroniser.
    * FS\_Infano : il y a un enfant à synchroniser.
    * FS\_Familio : il y a un conjoint à synchroniser.
    * FS\_Fakto : il y a un évènement à synchoniser (autre que naissance ou décès).
    * FS\_Konf : dans le gramplet : synchro pas parfaite mais marquée conforme
    * FS\_Dup : doublon potentiel détecté par FS
    * FS\_Gramps : changé dans gramps depuis la dernière fois que l'étiquette FS\_Konf a été positionné, ou que tout était conforme (étiquette FS\_Identa et aucun autre)
    * FS\_FS : changé dans FamilySearch depuis la dernière fois que l'étiquette FS\_Konf a été positionné, ou que tout était conforme (étiquette FS\_Identa et aucun autre)
    * source à joindre.
    * note à joindre.
  * affichage de l'état dans le gramplet
    * 1e ligne = état des renseignements essentiels (nom, prénom, sexe, naissance, décès)
    * 2e ligne = état des liens familiaux (parents, conjoints, enfants)
    * 3e ligne = état des évènements
    * 4e ligne = état des sources et notes
    * 5e ligne ? état des autres renseignements (portrait, médias, …)
* doublons :
  * bouton vers la fiche familysearch du doublon
  * bouton vers fusion dans familysearch
* gramplet
  * bug : parents multiples pas bien gérés
  * gérer le changement de FSID à la suite d'une fusion dans FamilySearch
  * bien définir la signification des couleurs, ex. :
    * vert foncé : tout bon
    * vert clair : essentiel bon, différences non essentielles
    * orange : présent des 2 cotés, mais discordance sur l'essentiel
    * jaune vif : présent que dans gramps
    * jaune sombre : présent que dans FS.
  * mettre la bonne couleur partout
* import :
  * gérer une liaison auto des parents, conjoints et enfants s'ils existent déjà.
## facultatifs
* que se passe t'il si une personne a deux attributs \_FSFTID ?
* partout :
  * création dans FS : lier aux parents et aux enfants qui existent dans FS
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
  * faire des listes déroulantes.
  * rafraichir : supprimer aussi les mariages avant de recharger.
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

# à faire pour version 1.2

* mise à jour de données FS dans le gramplet
* gestion des relevés (= «records» FS)

# à faire pour version 2

* module de liaison automatique.
* dans la recherche :
  * lien vers écran de fusion
* dans le gramplet :
  * lier un enfant ou conjoint gramps avec un enfant ou conjoint FS
* dans l'import :
  * gestion des «attribution»
  * charger les ID des familles
* gestion pointue des lieux dans l'import , dans le gramplet, dans fslib
* gestion des nicknames à voir
* gestion des «memories»
* gestion des sources dans le gramplet
* chargement du portrait FS vers gramps
* chargement des images FS vers gramps
* chargement des images gramps vers FS
* barres de progression
* détection de doublons dans gramps d'après le FSID
* création de personne FS : gérer tous les noms, les sources, …
* copies de données FS vers gramps dans le gramplet
* copies de données gramps vers FS dans le gramplet
* effacement de données FS dans le gramplet
* effacement de données gramps dans le gramplet

