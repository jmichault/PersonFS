
Comment transférer au mieux les notes saisies dans gramps vers FS ?  
Et inversement ?

# Dans gramps :
* Une Note peut être référencée par :
  * un individu
  * une famille
  * un évènement
  * une référence d'évènement
  * un nom
  * …
* une même note peut être référencée à plusieurs endroits.
* une note se compose de :
  * un id
  * un type
  * un texte
  * des étiquettes

# Dans FS :
* Une Note peut être attachée à :
  * un individu
  * une famille
  * …
* on ne peut pas réutiliser une note.
* une note se compose de :
  * un id
  * un titre
  * un texte
  * une «attribution» (= auteur et date de dernière modification)
  * si c'est une note d'individu : un tag alerte (booléen) (une seule note d'individu peut être une note d'alerte)
* les «Explications» (= changeMessage) peuvent être considérées comme des notes. Elles peuvent être rattachées à :
  * un évènement/fait
  * un conjoint
  * un nom
  * …
* le «Bref récit biographique» pourrait être considéré comme une note, mais il est traité par FS comme un fait.

# traitement
* pour les notes individu et famille :
  * type gramps <--> titre FS
  * texte gramps <--> texte FS
  * on suppose que le type/titre est unique pour un individu ou une famille (mais c'est faux aussi bien dans gramps que FS…)
* pour les notes évènement/référence d'évènement, nom
  * concaténation des (type+texte) gramps, triés par type <--> changeMessage FS.
