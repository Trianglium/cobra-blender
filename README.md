## Cobra™ Tools for Blender

"~~Life~~ Modding finds a way."

A toolset for blender allowing the import and export of models, textures and animations from **Planet Zoo**® and **Jurassic World Evolution**™.


### Installation
- Supported Blender versions: [**2.81+**](https://www.blender.org/download/)
- Get the latest release of the plugin [here](https://github.com/OpenNaja/cobra-blender/releases).
- To install the plugin with the addon installer in Blender, click `Edit` > `Preferences` > `Add-ons` > `Install...` and select the ZIP you just downloaded.
- `pyffi 2.2.4.dev3` must be installed to blender's bundled python directory. Open a cmd with admin rights and do the following steps:
```cmd
C:\Windows\system32>cd C:\Program Files\Blender Foundation\Blender 2.81\2.81\python\bin

C:\Program Files\Blender Foundation\Blender 2.81\2.81\python\bin>python.exe -m pip install PyFFI==2.2.4.dev3
```
Alternatively, you can copy the `pyffi` folder from your system's python into the appropriate spot in blender's python folder.

### How To Use

#### Importing Models
- `File` > `Import` > `Cobra Model (.MDL2)`.

#### Exporting Models
- `File` > `Export` > `Cobra Model (.MDL2)`.
- Select the source model, the exported model will be created in a subfolder called `export`.
- Model names are crucial; object naming convention has to be enforced. The object name suffix `_modelX` (with `X` being an integral number) determines which MDL2 model is targeted.

### Known Limitations
- Same model & LOD count.
- Fur shader fin generation is not functional for custom models, but stock fins can be edited.
- No shader or material edits with blender.
- No armature edits.
- No animation export. Animation import is limited to Banis files and only works on some files.

### Disclaimer
Not all model files are supported at this time. Some may crash on import or export. Even if they (seemingly) import and export fine, the result is not guaranteed to work ingame.

### Legal Notice
This software is developed under 'fair use' by enthusiasts and is not affiliated with Universal© or Frontier® in any form.

By downloading and using this software, you agree to the following conditions:
- **Use this software at your own risk.** It may cause damage to you, your equipment or your data. The authors are not responsible for your actions.
- **Do not use this software to circumvent copy protections.** Especially, do not try to unlock downloadable content for free, share official artwork or intellectual property or engage in so-called data mining to announce game content before an official announcement.
- **Do not seek monetary compensation for mods made with this software.** Do not charge money or ask for donations in order to download the mods. Do not accept payment in exchange for exclusive rights (even if temporary) to commissioners of mods.
- **Secure permission to use other parties' work in your mods.** This includes but is not limited to using IP, artwork, skin designs and 3D models (eg. porting models from another game). If you don't have the approval of the copyright holder(s), be prepared to face the consequences.

### Credits
- Planet Zoo, Cobra, Frontier and the Frontier Developments logo are trademarks or registered trademarks of Frontier Developments, plc.
- Jurassic World, Jurassic World Fallen Kingdom, Jurassic World Evolution and their respective logos are trademarks of Universal Studios and Amblin Entertainment, Inc.
- Daemon1, DennisNedry1993 and Inaki for initial modding attempts and documentation.
