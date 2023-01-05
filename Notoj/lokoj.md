	; fsid avec lieu non standardisé : LR24-CQK

# les lieux dans familysearch :

recherche : <https://www.familysearch.org/research/places/>

peuvent être de deux classes :
* PlaceDescription : attribut «places» de la classe gedcomx.
	décrit les lieux normalisés.
  * l'id permet de récupérer la description complète sur <https://api.familysearch.org/platform/places/description/ID>
    * de là, on peut récupérer le lien vers la place familysearch : <https://api.familysearch.org/platforme/places/ID2>
  * names : noms localisés.
* PlaceReference : partout ailleurs. Par exemple attribut place de la classe Fact.
	attributs importants :
  * description : contient l'id du lieu normalisé sous la forme #ID (si le lieu est normalisé)
  * original : le texte saisi
  * normalized : le nom normalisé (attention à la langue), pour la France il est généralement (mais pas toujours) de la forme «commune, département, région, pays»
  * names : noms localisés.

Les lieux normalisés n'ont en général qu'une précision limitée à la commune. Pour rentrer un lieu plus précis, on faut utiliser le champ «original». Par exemple, si on utilise la forme recommandée par geneanet pour les lieux français, on va mettre dans original : «[lieu-dit ou précision] - commune, code_insee, département, région, pays».
 À vérifier : On va mettre dans description «#ID».
 On peut aussi créer un lieu depuis <https://www.familysearch.org/research/places/>
 On ne peut créer que les types suivants :
 * 115 : Établissement scolaire 
 *  20 : Cimetière
 * 308 : Quartier
 *  38 : Ferme
 *  23 : Lieu de culte ( à l'exception des temples de l’Église de Jésus-Christ !!! )
 * 391 : Village = plus petit que 376, dispose d'un magasin.
 * 376 : Town = A local division of human settlement often incorporated administratively, larger than a village but smaller than a city. An official designation for township in several of the United States including New England and parts of the midwest.
 * 201 : Commune
 * 186 : Ville = Installation artificielle plus ou moins étendue et pérenne dotée de systèmes élaborés d’exploitation des sols, d’habitations, de transport et d’organisation gouvernementale.
 * 266 : Hameau
 * 378 : Canton (Township)
 * 142 : Hôpital
Les types suivants ne peuvent être créés que par FamilySearch :
 * Comté
 * Pays
 * Province
 * Région
 * État

liste des types de lieux : <https://www.familysearch.org/platform/places/types> .
Certaines descriptions ne sont pas traduites en français. voir <https://www.familysearch.org/platform/places/types?lang=en> pour la description en américain.  
Quelques-uns des types pertinents en France :
 * type 580 = Pays
 * type 337 = Région
 * type 209 = Comté (avant la révolution)
 * type 215 = Département

 * type 172 = Canton
 * type 201 = Commune
 * type 186 = Ville
 * type 171 = Arrondissement municipal
 * type 140 = Endroits peuplés
 * 115 : Établissement scolaire 
 *  20 : Cimetière
 * 308 : Quartier
 *  38 : Ferme
 *  23 : Lieu de culte ( à l'exception des temples de l’Église de Jésus-Christ !!! )
 * 391 : Village = plus petit que 376, dispose d'un magasin.
 * 266 : Hameau
 * 142 : Hôpital


Attention : il y a deux types d'ID :
 * l' ID place-description = celui utilisé pour  https://api.familysearch.org/platforme/places/description/ID. C'est celui utilisé dans les classes «Gedcomx» et «Fact»
 * l' ID place = celui utilisé pour https://api.familysearch.org/platforme/places/ID
   * plusieurs ID place-description peuvent pointer vers le même ID place.
   * sur <https://api.familysearch.org/platforme/places/ID>, on récupère la liste des «place-description», qui peuvent nottament être des variantes temporelles.


Un lieu peut avoir des doublons. Exemple pour Angoulême, on a :
 * ID = 10978745 (Commune, certifié); type=201 ; fullname = «Angoulême, Charente, Nouvelle-Aquitaine, France»
 * ID = 5953317 (Commune, accepté) ; type=201 ; fullname = «Angoulême, Charente, Nouvelle-Aquitaine, France»
   a des enfants de type canton ??? : 
   * 9517845 ; type = 172 ; fullname = «Aubeterre-sur-Dronne, Angoulême, Charente, Nouvelle-Aquitaine, France»
   * 9517842 ; type = 172 ; fullname = «Blanzac-Porcheresse, Angoulême, Charente, Nouvelle-Aquitaine, France»
 * ID = 10905243 (Commune, accepté) ; type=201 ; fullname = «Angoulême, Charente, Poitou-Charentes, France»
 * ID = 6824318 (Endroits peuplés, accepté)
 * ID = 10743639 (Ville, certifié) ; type=186
   * partie de 10709047 ; type=209 ; name = «Angoumois»

Question : à quoi ressemblent les lieux non normalisés ?


# correspondance avec gramps
## Problème 1 : il faut stocker quelque part la correspondance ID gramps <--> ID familysearch.
 * solution choisie = utiliser les liens internet : créer un lien, type="FamilySearch", addr = https://api.familysearch.org/platform/places/description/ID . Un lieu peut avoir plusieurs liens.

## Problème 2 : lieux avec une propriété «original» plus précise que «normalized»
Il faudrait créer un lieu enfant du lieu normalisé, mais seulement quand «original» est vraiment plus précis que «normalized».  
À voir plus tard. Pour l'instant on en reste au lieu normalisé.


## équivalence entre les types familysearch et gramps
| code        | nom français     | code FS | obs. |
| ----------- | ---------------- | --------| ---- |
|COUNTRY      | Pays             | 580     | État souverain
|STATE        | Province (Région)| 362     | État fédéral
|COUNTY       | Comté (Départ.)  | 209,521 | 209 = dirigé par un comte, 521=comté anglais,suédois, roumain
|CITY         | Ville            | 186     |
|PARISH       | Paroisse         | 312     |
|LOCALITY     | Lieu-dit         |         |
|STREET       | Rue              |         |
|PROVINCE     | Province         | 323     |
|REGION       | Région           | 337     |
|DEPARTMENT   | Département      | 215     |
|NEIGHBORHOOD | Quartier         | 308     | 
|DISTRICT     | District (Arr.)  | 221     | District américain, Arrondissement départemental
|BOROUGH      | Borough (Arr.)   | 171     | Arrondissement municipal
|MUNICIPALITY | Municipalité     | 201     | = Commune en france
|TOWN         | Bourg            | 376     |
|VILLAGE      | Village          | 391     |
|HAMLET       | Hameau           | 266     |
|FARM         | Ferme            | 38      |
|BUILDING     | Immeuble         |         | 23, 61, 115, 142
|NUMBER       | Numéro           |         |

types FS usuels sans correspondance claire :  
 * 172 = Canton
 * 140 = Endroits peuplés
 *  20 : Cimetière



# correspondance avec les codes insee
api adresse : https://adresse.data.gouv.fr/api-doc/adresse
api cog : https://www.data.gouv.fr/fr/datasets/code-officiel-geographique-cog/
  note : les anciennes communes n'y sont pas.
fichiers cog : https://www.insee.fr/fr/information/2560452

types de divisions :  
* pays = COUNTRY = 580
* région = REGION = 337
* département = DEPARTMENT = 215
	, partie d'une région
* collectivité territoriale
	, partie d'une région
    ex. : conseils départementaux 
* arrondissement ~ DISTRICT ~ 221
	, partie d'un département
* canton, partie d'un département
* commune = MUNICIPALITY = 201

# correspondance avec geonames

