## Cobra™ Tools for Blender

"~~Life~~ Modding finds a way."

A toolset for blender allowing the import and export of models, textures and animations from **Planet Zoo**® and **Jurassic World Evolution**™.


### Installation
- Get the latest release [here](https://github.com/OpenNaja/cobra-blender/releases).
- To install with the addon installer in Blender, click `File` > `User Preferences` > `Add-ons` > `Install Add-ons from File` and select the ZIP you just downloaded.
- pyffi 2.2.4.dev3 must be installed to blender's bundled python directory. Open a cmd with admin rights and do the following steps:
```cmd
C:\Windows\system32>cd C:\Program Files\Blender Foundation\Blender 2.81\2.81\python\bin

C:\Program Files\Blender Foundation\Blender 2.81\2.81\python\bin>python.exe -m pip install PyFFI==2.2.4.dev3
```

### How To Use

#### Importing Models
- `File` > `Import` > `Cobra Model (.MDL2)`.
- n.b. using MDL2 normals will crash blender when importing stock models with a fur shader.

#### Exporting Models
- `File` > `Export` > `Cobra Model (.MDL2)`.
- Select the source model, the exported model will be created in a subfolder called `export`.
- Model names are crucial; object naming convention has to be enforced.

#### Brand New Models
When using new models instead of editing existing ones you must add some custom properties before exporting them. must use integers

![Imgur](https://i.imgur.com/4vmFAZy.png)

please set these two properties to match the settings of the stock mesh you are replacing.

If your model is intended to be furry for Planet Zoo then you must also set the mesh up to be a replacement for the shell mesh. make sure it has the same flag and shell count as a stock shell mesh. You will then need to create a Fur Length vertex group on your custom mesh and weight paint it. you only need to wieght paint with small values close to 0 like 0.01-0.05 for it to have reasonable fur length ingame. 

![Imgur](https://i.imgur.com/vHskqtP.png)

At this time the Fur method using the Fin meshes are not able to be created from scratch. One could remove most of the the fin mesh leaving a single polygon if the mesh interferes with your brand new mesh. 

If you are making edits to a stock model you can also edit the fin mesh to fit the edited geometry and that will work at this time. 

#### UV MAP Setup
Please ensure that if you add vertices to an edited stock mesh that you remove the UV1 through UV3 and then re-add them.


### Known Limitations
- Same model & LOD count.
- Fur shader fin generation is not functional for custom models, but stock fins can be edited.
- No shader edits.
- No armature edits.
- No animation export. Animation import is limited to Banis files and only works on some files.

### Disclaimer
Not all model files are supported at this time. Some may crash on import or export. Try loading the OVL and unpacking with reverse sets setting changed in the OVL tool if the import does not work the first time.

### Legal Notice
- This tool is developed under 'fair use' by enthusiasts and is not affiliated with Universal© or Frontier® in any form.
- Use at your own risk. This tool may cause damage to you, your equipment or your data.
- Do not use or modify these tools to circumvent copy protections; especially, do not try to unlock downloadable content for free or share official artwork or intellectual property or engage in so-called data mining to announce game content before an official announcement.
- Do not charge money or ask for donations for mods created with these tools.


### Credits
- Planet Zoo, Cobra, Frontier and the Frontier Developments logo are trademarks or registered trademarks of Frontier Developments, plc.
- Jurassic World, Jurassic World Fallen Kingdom, Jurassic World Evolution and their respective logos are trademarks of Universal Studios and Amblin Entertainment, Inc.
- Daemon1, DennisNedry1993 and Inaki for initial modding attempts and documentation.
