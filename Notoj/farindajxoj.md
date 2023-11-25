
* note : fsid fusionné : GZKW-DLY,GJ7P-84L;
        ; fsid George Washington : KNDX-MKG
	; fsid avec parents multiples : 9CSJ-L2D (lacour-pijardière : père officiel et père réel)
	; fsid avec lieu non standardisé : LR24-CQK
	; fsid avec date intervalle : LTY2-RSM
	; fsid avec date avant :  KZCP-RPL (Meints, Roelof)
	; fsid avec «Bref récit biographique» : LRVF-9YS
    ; fsid avec note d'individu : LRVF-HBK
# fait :
  * copie d'un contrat de mariage vers FS : ne marche pas car FS n'accepte que les évènements suivants sur un mariage : «Mariage», «Annulation»,«Divorce»,«Mariage de droit coutumier»,«A vécu maritalement», «Aucun enfant».
    * --> créer un évènement mariage avec une explication qui dit que c'est un contrat ?  
	  c'est la solution choisie : on met en explication :"http://gedcomx.org/MarriageContract\nContrat de mariage."
    * --> lier ces autres évènements aux conjoints ? (c'est ce que fait familysearch)
    * --> transformer les autres évènements en note (pb : pas de date sur les notes, il faut la rajouter dans le texte)?
  * idem pour : fiançailles
  * copie des notes personnepersonne et famillee de gramps vers FS.

# à faire pour version 1.5
## prioritaires
* bogues :
  * il faut rafraichir après transfert d'un enfant vers FS.
  * affichage court des annèes : transformer les dates républicaines (voir Libaros, Jean : son fils Frix affiché 0005-1882 au lieu de 1797-1882)
  * si connexion FS perdue : reconnecter correctement (actuellement, il faut rafraîchir une deuxième fois).
  * comparaison : fsid G6M3-79W : le conjoint n'apparaît pas car il n'y a pas de lien conjugal dans FS.
  * comparaison : la comparaison des mariages n'utilise pas le fsftid
  * mise à jour d'un événement avec changement de lieu : le lieu est parfois effacé ? Si le lieu est nouveau ?
  * import d'une date A/+1736 (pas prévu dans gramps).
  * comparaison : la liste des filtres est celle du premier lancement.
  * import 1 clic : quelquefois les enfants ne sont pas tous importés.
  * naissance sans date dans gramps n'apparait pas ?
  * transfert d'une date «vers xxxx» devient «abt xxxx-00-00» au lieu de "abt xxxx»
  * positionner la langue lors des transferts vers FS. Notamment pour les noms.
* gramplet :
  * lors de la création dans FS : une fois la personne créée, faire le transfert de ses évènements.
  * renseigner le FSFTID des évènements lors de la comparaison s'il n'y est pas.
  * transfert d'un enfant de gramps vers FS.
  * possibilité de renseigner manuellement le \_FSFTID d'une personnes
  * si coche d'une ligne de regroupement : cocher tout le groupe.
  * si coche d'un parent, enfant ou conjoint :
    * si absent de FS mais a un FSFTID : accepter.
    * si absent de FS et pas de FSFTID : suggérer d'aller sur la fiche et demander confirmation.
    * si absent de gramps : chercher le FSFTID dans gramps.
      * si absent : suggérer l'import.
      * si présent : accepter.
  * si coche de sexe : suggérer de faire la correction manuellement.
  * comparer les lieux.
  * si erreur dans la copie : afficher un message.
* recherche :
  * création dans FS :
    * lier aux parents et aux enfants qui existent dans FS
    * après création : transférer aussi les faits et noms.
  * plus de critères (au moins décès : date + lieu de décès, et lieu général)
* import :
  * ne pas lancer si pas de fsid.
  * normaliser les noms/prénoms (majuscules et minuscules).
  * importer/mettre à jour l'ID des objets : évènement, famille, source, citation.
  * gérer une liaison auto des parents, conjoints et enfants s'ils existent déjà, plutôt que créer en double.
  * cocher systématiquement par défaut «Ne pas réimporter les personnes existantes»
* traduction en français
* mise à jour doc
## facultatifs
* maintenir un dictionnaire personne.fsid-handle.
* maintenir un dictionnaire lieu.fsid-handle.
* gedcomx : attributs inconnus :
  * Person:Principal, ex. : LR2N-SRM
  * Tag:conclusionId G8FW-VTJ
* exécution de la synchro en arrière-plan ?
* que faire si une personne a deux attributs \_FSFTID ?
	il faudrait supprimer ceux qui ont été supprimés dans FS.
* gramplet :
  * rafraichissement sans relecture de FS après saisie dans gramps ?
  * copie des noms vers FS : positionner preferred correctement.
	attention : il doit toujours rester un nom préféré sur FS.
  * comparaison : gérer le drapeau «vivant» sur familysearch.
  * rafraichir : ne recharger la personne que si elle a été modifiée.
  * liaison de conjoints FS vers gramps (le conjoint doit exister dans gramps, sinon : message).
* recherche :
  * bouton d'import sur la recherche ?
  * cacher ou désactiver le bouton «Aldoni» si l'attribut \_FSFTID est renseigné
	ou afficher un avertissement.
  * recherche accessible depuis le menu ?
  * recherche : charger les suivants
* identifier et gérer les pré-requis (requests, gedcomx-v1)
* synchro :
  * accélérer le traitement :
    * lancement en multi-thread (async ?)
  * étiquettes à renseigner :
    * source à joindre.
    * note à joindre.
* ne pas se connecter à FamilySearch avant l'ouverture de la BD
* import :
  * gestion de l'évènement StillBirth (= enfant mort-né) ?
  * accélérer le chargement des notes et sources.

# à faire pour version 2

* rafraîchir quand on change de régime.
* bogue gramps si case à cocher dans un treeview : sudo sed -i 's/int(path)/path/' /usr/lib/python3/dist-packages/gramps/gui/listmodel.py
	--> doit être corrigé par gramps-project : https://github.com/gramps-project/gramps/pull/1426
	--> je pourrais alors supprimer mialistmodel.py
* gestion pointue des lieux dans l'import , dans le gramplet, dans gedcomx-v1 ?
  - attention, car une refonte en profondeur de la gestion des lieux est prévue pour gramps 2.0…
* gestion des «memories»
* module de liaison automatique.
* module de liaison manuelle, mais à la chaine.
* module de détection de doublons dans gramps d'après le FSID
* gramplet :
  * lier un enfant ou conjoint gramps avec un enfant ou conjoint FS
  * gestion des sources
    problème : comment transférer au mieux les sources saisies dans gramps vers FS ?
      - dans gramps, on a une hiérarchie dépôt --> source --> citation, rien de tel dans FS.
      - voir Notoj/fontoj.txt
  * gestion des notes
  * gestion des images et du portrait
* dans l'import :
  * gestion des «attribution» ?
  * charger les ID des lieux , sources , Relationship, ChildAndParentsRelationship ?
* gestion des nicknames à voir
* chargement du portrait FS vers gramps, et réciproquement.
* chargement des images FS vers gramps
* chargement des images gramps vers FS
* création de personne FS : gérer tous les noms, les sources, …
* effacement de données FS dans le gramplet ?
* effacement de données gramps dans le gramplet ?
* gestion des relevés (= «records» FS)


