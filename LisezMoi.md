

Ceci est un module pour interfacer _gramps_ avec _familysearch.com_.
il se compose de :
* un [_gramplet_](https://www.gramps-project.org/wiki/index.php/Gramplets) permettant de comparer votre individu avec celui de _FamilySearch_.
* un module d'import accessible par le menu «Outils» --> «Modification de l'arbre familial» --> «Import de données FamilySearch»

Pour pouvoir utiliser le gramplet il vous faut un compte _familysearch_, celui-ci sera demandé au lancement du gramplet, ainsi que le mot de passe associé.

# installation
## prérequis
Les module python «requests» et «gedcomx-v1» doivent être installés.
De ce fait ce plugin ne peut pas être utilisé avec la distribution AIO de gramps.

## en chargeant le zip
Sur la [page d'accueil du projet](https://github.com/jmichault/PersonFS), cliquez «Releases» (à droite), et dans «Assets» choisissez le fichier PersonFS.zip).  
Puis extrayez le zip dans le dossier des plugins de Gramps (~/.gramps/gramps51/plugins pour la version 5.1 de gramps)

## avec git
Dans un terminal, exécutez les commandes suivantes :

```
cd ~/.gramps/gramps51/plugins
git clone https://github.com/jmichault/PersonFS.git
```
(note : à adapter si gramps n'est pas en version 5.1)
# le gramplet
## activation
En étant positionné sur le panneau des Individus, cliquez sur le menu déroulant à droite des onglets (petit bouton «v») et choisissez «Ajouter un Gramplet», puis «FS».  
Une fois ceci fait un nouvel onglet «FS» est ajouté.

## utilisation
L'extension comporte 3 modules :
* un module d'import
* un gramplet de comparaison individu gramps vs individu FamilySearch. Il permet aussi de faire des recherches sur familysearch et de consulter les doublons potentiels trouvés par FamilySearch.
* un outil de comparaison, qui va parcourir tous les individus et positionner les étiquettes suivantes : (en cours de développement)
  * FS\_Identa : tout les éléments comparés sont synchrones
  * FS\_Esenco : il y a une information essentielle à synchroniser (nom/prénom principal, dates de naissance et décès).
  * FS\_Nomo : il y a un nom (autre que le principal) à synchroniser.
  * FS\_Gepatro : il y a un parent à synchroniser.
  * FS\_Familio : il y a un conjoint ou un enfant à synchroniser.
  * FS\_Fakto : il y a un évènement à synchoniser (autre que naissance ou décès).
  * FS\_Dup : doublon potentiel détecté par FS
  * FS\_Gramps : changé dans gramps depuis la dernière fois que l'étiquette FS\_Konf a été positionné, ou que tout était conforme (étiquette FS\_Identa et aucun autre)
  * FS\_FS : changé dans FamilySearch depuis la dernière fois que l'étiquette FS\_Konf a été positionné, ou que tout était conforme (étiquette FS\_Identa et aucun autre)
  * FS\_Konf : dans le gramplet : synchro pas parfaite mais marquée conforme


Le gramplet permet de comparer la fiche de votre personne gramps avec celle de familysearch pour les informations suivantes :  
* nom/prénom principal
* date et lieu de naissance
* date et lieu de baptême
* date et lieu de décès
* date et lieu de d'inhumation
* les parents (nom/prénom principal, années de naissance et de décès)
* les conjoints
* les enfants
* les autres évènements

La première colonne permet de visualiser rapidement quelles données ne sont pas en phase :
* vert = en phase (attention : pour les personnes seuls les identifiants familysearch sont vérifiés, pour les dates/lieux, seules les dates sont vérifiées)
* orange : présent des deux côtés, mais pas en phase.
* jaune : présent d'un seul côté.

Note : le lien avec _familysearch_ se fait grâce à un attribut de clé _«\_FSFTID»_ et ayant pour valeur le N° d'identification _familysearch_.  

Note : pour limiter le temps de chargement, au lancement les données détaillées des conjoints et enfants ne sont pas chargées. Vous pouvez les charger en cliquant sur le bouton «Charger conjoints et enfants».

Les dates sont affichés chaque fois que c'est possible en utilisant le format [_«formal»_](https://github.com/FamilySearch/gedcomx/blob/master/specifications/date-format-specification.md) de _familysearch_.

Depuis le gramplet, vous pouvez aussi :
* Accéder à la fiche FamilySearch complète en cliquant sur le N° d'identification (à droite de l'écran), ce qui lance votre navigateur internet.
* Lancer une recherche sur FamilySearch, qui vous permet aussi d'associer votre fiche à une fiche familysearch existante, ou de copier votre fiche vers FamilySearch si vous ne trouvez pas de correspondance.
* Consulter les doublons potentiels proposés par FamilySearch, et de là vous pouvez accéder à la fiche FamilySearch complète du doublon potentiel, ou accéder à l'écran de fusion FamilySearch.
* lancer le module d'import pour importer les données FamilySearch de votre individu, et éventuellement les ancêtres et descendants.

# le module d'import
Vous pouvez le lancer soit depuis le menu, soit depuis le gramplet.  
Vous avez juste à renseigner :
* l'identifiant FamilySearch de départ
* le nombre de générations d'ascendants à charger.
* le nombre de générations descendantes.
* décochez «Ne pas réimporter les personnes existantes» si vous voulez protéger vos individus existants.
* cochez «Ajouter les conjoints» si vous voulez charger aussi les conjoints de toutes les personnes.
  (note : si vous chargez des générations descendantes, les conjoints seront chargés)

Puis cliquez sur le bouton «Importer»

# méthode de travail suggérée.

## Créez des filtres
1. créez un filtre : «ascendants»
2. créez un filtre : «ascendants avec parent non synchronisé».
3. créez un filtre : «ascendants avec parent non synchronisé».

## démarrage
1. activez le gramplet sur la vue Individus
2. allez sur votre individu souche, et liez-le :
  * avec le bouton chercher, essayez de le trouver dans familysearch
  * si vous le trouvez : utilisez le bouton Lier.
  * si vous ne le trouvez pas : utilisez le bouton Ajouter.
3. faites de même avec ses parents, puis les parents de ses parents …

## régulièrement
1. filtrez les «ascendants avec parent non synchronisé»
  * synchronisez les parents
