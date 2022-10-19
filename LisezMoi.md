


Ceci est un [_gramplet_](https://www.gramps-project.org/wiki/index.php/Gramplets) pour interfacer _gramps_ avec _familysearch.com_.

Dans l'état actuel il est très limité, il permet de comparer la fiche de votre personne gramps avec celle de familysearch pour les informations suivantes :  
* nom/prénom principal
* date et lieu de naissance
* date et lieu de baptême
* date et lieu de décès
* date et lieu de d'inhumation
* nom/prénom principal du père et de la mére

le lien avec _familysearch_ se fait grâce à un attribut de clé _«\_FSFTID»_ et ayant pour valeur le N° d'identification _familysearch_.  
Note : le script python [_GetMyAncestors_]() renseigne cet attribut.

Les dates sont affichés chaque fois que c'est possible en utilisant le format [_«formal»_](https://github.com/FamilySearch/gedcomx/blob/master/specifications/date-format-specification.md) de _familysearch_.

Pour pouvoir utiliser le gramplet il vous faut un compte _familysearch_, celui-ci est à renseigner dans les préférences, ainsi que le mot de passe associé.
