
PersonFS is a [gramplet](https://www.gramps-project.org/wiki/index.php/Gramplets) to interface gramps with familysearch.com.
warnings : 
* don't work with windows AIO release.
* you need to patch gramps with command ` sudo sed -i 's/int(path)/path/' /usr/lib/python3/dist-packages/gramps/gui/listmodel.py `
* you need to install python modules requests and gedcomx-v1 (>=1.0.8) with ` pip install --upgrade requests gedcomx-v1 `

Ceci est un [gramplet](https://www.gramps-project.org/wiki/index.php/Gramplets) pour interfacer gramps avec familysearch.com.
Plus d'informations dans [LisezMoi.md](LisezMoi.md)
Attention : ne marche pas avec la version windows AIO de gramps. Sous windows utilisez gramps avec WSL : voir [Notoj/gramps_wsl.md](Notoj/gramps_wsl.md)

Ĉi tio estas [gramplet](https://www.gramps-project.org/wiki/index.php/Gramplets) por interligi gramps kun familysearch.com.
Pliaj informoj en [LeguMin.md](LeguMin.md)
