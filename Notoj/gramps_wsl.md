# utiliser gramps sous windows avec WSL

pré-requis : windows 10 >= 22H2, ou windows 11


## installer wsl
aller dans «Paramètres»
* --> Applications
* --> Fonctionnalités Facultatives
* --> Plus de fonctionnalités windows
* --> cocher «Sous-système windows pour Linux» et «Plateforme de machine virtuelle»
* --> OK, rebooter

## mettre à jour WSL vers la dernière version :
* lancer «microsoft store»
* chercher wsl, cliquer obtenir

## installer ubuntu
toujours dans «microsoft store» :
* chercher ubuntu 22.04, cliquer obtenir puis ouvrir
* rentrer un nom d’utilisateur, le mot de passe.
* installer le support du français :
```
sudo apt-get -y install language-pack-fr language-pack-fr-base language-pack-gnome-fr language-pack-gnome-fr-base
sudo locale-gen
sudo update-locale LANG=fr_FR.UTF-8
```

## installer gramps
dans la ligne de commande ubuntu :
```
sudo add-apt-repository universe
sudo apt install gramps python3-pip -y
gsettings set org.gnome.desktop.interface cursor-theme whiteglass
gramps
```

## facultatif : installer le driver vGPU

