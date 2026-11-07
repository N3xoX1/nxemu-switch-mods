# NXEmu Switch mods

Code patches and cheats for Nintendo Switch games. Set up so NXEmu can ship them as its bundled mods.

## Layout

```
<Game name> [<title id>]/
    <Mod name>/
        mod.json
        LICENSE                  (when the mod has a license)
        README.md                (optional)
        exefs/<name>.nxpatch | <name>.pchtxt | <name>.ips
        cheats/<build id>.txt
```

- `<title id>`: the game's 16-digit hex title id, in upper case.
- One mod folder holds the patches for every game version: each patch names the build id it applies to
  (`@nsobid-`), and NXEmu applies only the one that matches the installed version. `game_versions` in
  `mod.json` lists them.
- Names must be valid on Windows: none of `< > : " / \ | ? *`, and no trailing space or dot.
- Plain files only: no archives, and nothing taken from a game (romfs, ExeFS files) or derived from one.

## mod.json

```json
{
    "name": "Shown in the game's add-ons list",
    "description": "What the mod does",
    "game_versions": ["1.4.3"],
    "enabled_by_default": true,
    "requires": ["frame_step"],
    "license": "MIT",
    "permission": "...",
    "credits": [
        {"name": "Author", "work": "What they made", "url": "https://...", "license": "MIT", "permission": "..."}
    ]
}
```

- `enabled_by_default`: `false` keeps the mod off until the user turns it on.
- `requires`: NXEmu features the mod needs; a build without one keeps the mod off.
  `frame_step`: NXEmu writes the measured frame time to the patch page (`.nxpatch` `@page`).
- `license`: the license the mod's authors gave it, with its text and copyright lines in the mod's `LICENSE`, or
  `null` when they gave none.
- `permission`: needed when `license` is `null`: who allowed the mod to be here, and when.
- `credits`: everyone whose work the mod uses, each with the `license` of their work or the `permission` they gave.

## Formats

- `.nxpatch`: NXEmu patch sets. Sets of instruction sites, each checked against its original instruction and
  applied whole; a site of several words runs in a cave NXEmu places after the module. Described in
  NXEmu's `src/nxemu-loader/core/file_sys/patch_sets.h`.
- `.pchtxt`: IPSwitch text patches.
- `.ips`: IPS binary patches, named by build id.
- `cheats/*.txt`: Atmosphère cheat files, named by build id.

## Checks

`python tools/check_mods.py` checks the layout, names, `mod.json` and file types; CI runs it on every push and
pull request.

## License

There is no license for the repository as a whole: each mod is under its own terms, set by its authors, in its
`mod.json` and `LICENSE`. A mod with no license may be used only as its `permission` says, which may not cover
copying it elsewhere. The tools are under the MIT license in `tools/LICENSE`.
