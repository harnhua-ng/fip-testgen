import os
from re import match
from sys import argv, exit

def gpll_cfg_upd():
    status = 0
    windows_os = 1 if(os.name == 'nt') else 0

    insPath  = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),".."))
    scrName  = os.path.basename(os.path.realpath(__file__))

    ip_inst_name    = os.path.basename(os.path.realpath(insPath))
    ip_gen_cfg_file = os.path.realpath(os.path.join(insPath,ip_inst_name+'.cfg'))
    gpll_cfg_file   = os.path.realpath(os.path.join(insPath,ip_inst_name+'_cfg_file.cfg'))
    rename_ip_gen_cfg_file = os.path.realpath(os.path.join(insPath,'ip_gen_cfg_file.cfg'))

    if(os.path.isfile(rename_ip_gen_cfg_file)):
        os.remove(rename_ip_gen_cfg_file)

    print("DEBUG: renaming file {} -> {}".format(ip_gen_cfg_file,rename_ip_gen_cfg_file))
    if(windows_os):
        os.system('copy /y "{}" "{}"'.format(ip_gen_cfg_file,rename_ip_gen_cfg_file))
    else:
        os.system('cp -f "{}" "{}"'.format(ip_gen_cfg_file,rename_ip_gen_cfg_file))

    if(os.path.isfile(gpll_cfg_file)):
        print("DEBUG: renaming file {} -> {}".format(gpll_cfg_file,ip_gen_cfg_file))
        if(windows_os):
            os.system('copy /y "{}" "{}"'.format(gpll_cfg_file,ip_gen_cfg_file))
        else:
            os.system('cp -f "{}" "{}"'.format(gpll_cfg_file,ip_gen_cfg_file))
        os.remove(gpll_cfg_file)

    return status

gpll_cfg_upd()
print("Clean up script : ",os.path.realpath(argv[0]))
os.remove(os.path.realpath(argv[0]))
exit(0)
