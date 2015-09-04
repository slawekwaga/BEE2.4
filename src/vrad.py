import os
import os.path
import sys
import subprocess

from property_parser import Property
import utils

CONF = Property('Config')

def quote(txt):
    return '"' + txt + '"'


def load_config():
    global CONF
    utils.con_log('Loading Settings...')
    try:
        with open("bee2/vrad_config.cfg") as config:
            CONF = Property.parse(config, 'bee2/vrad_config.cfg').find_key(
                'Config', []
            )
    except FileNotFoundError:
        pass
    utils.con_log('Config Loaded!')


def pack_content(path):
    """Pack any custom content into the map."""
    utils.con_log("Running PakRat!")
    arg_bits = [
        quote(os.path.normpath(os.path.join(os.getcwd(), "bee2/pakrat.jar"))),
        "-auto",
        quote(os.path.normpath(
            os.path.join(
                os.path.dirname(os.getcwd()),
                'bee2/',
            )
        )),
        quote(path),
    ]
    arg = " ".join(arg_bits)
    utils.con_log(arg)
    subprocess.call(arg, stdout=None, stderr=subprocess.PIPE, shell=True)
    utils.con_log("Packing complete!")


def run_vrad(args):
    "Execute the original VRAD."

    if utils.MAC:
        os_suff = '_osx'
    elif utils.LINUX:
        os_suff = '_linux'
    else:
        os_suff = ''

    joined_args = (
        '"' + os.path.normpath(
            os.path.join(os.getcwd(), "vrad" + os_suff + "_original")
            ) +
        '" ' +
        " ".join(
            # put quotes around args which contain spaces
            (quote(x) if " " in x else x)
            for x in args
            )
        )
    utils.con_log("Calling original VRAD...")
    utils.con_log(joined_args)
    code = subprocess.call(
        joined_args,
        stdout=None,
        stderr=subprocess.PIPE,
        shell=True,
    )
    if code == 0:
        utils.con_log("Done!")
    else:
        utils.con_log("VRAD failed! (" + str(code) + ")")
        sys.exit(code)


def main(argv):
    utils.con_log('BEE2 VRAD hook started!')
    args = " ".join(argv)
    fast_args = argv[1:]
    full_args = argv[1:]

    path = argv[-1]  # The path is the last argument to vrad
    fast_args[-1] = os.path.normpath(path)

    utils.con_log("Map path is " + path)
    if path == "":
        raise Exception("No map passed!")

    load_config()

    for a in fast_args[:]:
        if a.casefold() in (
                "-both",
                "-final",
                "-staticproplighting",
                "-staticproppolys",
                "-textureshadows",
                ):
            # remove final parameters from the modified arguments
            fast_args.remove(a)
        elif a in ('-force_peti', '-force_hammer', '-no_pack'):
            # we need to strip these out, otherwise VBSP will get confused
            fast_args.remove(a)
            full_args.remove(a)

    fast_args = ['-bounce', '2', '-noextra'] + fast_args

    # Fast args: -bounce 2 -noextra -game $gamedir $path\$file
    # Final args: -both -final -staticproplighting -StaticPropPolys
    # -textureshadows  -game $gamedir $path\$file

    if not path.endswith(".bsp"):
        path += ".bsp"

    if '-force_peti' in args or '-force_hammer' in args:
        # we have override command!
        if '-force_peti' in args:
            utils.con_log('OVERRIDE: Applying cheap lighting!')
            is_peti = True
        else:
            utils.con_log('OVERRIDE: Preserving args!')
            is_peti = False
    else:
        # If we don't get the special -force args, check for the name
        # equalling preview to determine if we should convert
        # If that is false, check the config file to see what was
        # specified there.
        is_peti = (
            os.path.basename(path) == "preview.bsp" or
            utils.conv_bool(CONF['force_full'], False)
        )


    if is_peti:
        utils.con_log("Forcing Cheap Lighting!")
        run_vrad(fast_args)
    else:
        utils.con_log("Hammer map detected! Not forcing cheap lighting..")
        run_vrad(full_args)

    if '-no_pack' not in args:
        pack_content(path)
    else:
        utils.con_log("No items to pack!")
    utils.con_log("BEE2 VRAD hook finished!")

if __name__ == '__main__':
    main(sys.argv)