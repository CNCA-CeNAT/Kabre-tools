## modules.py - a miniclon of modules utility
## 	Copyright (C) 2017 Guillermo Cornejo Suárez gcornejo@cenat.ac.ct
##                         Centro Nacional de Alta Tecnología
##                         Colaboratorio Nacional de Computación Avanzada

##    This program is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 3 of the License, or
##    (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with this program.  If not, see <http://www.gnu.org/licenses/>.



###########################################################################
#--------------------------- Configuration -------------------------------#
modulerc = '/opt/modulerc'
###########################################################################


import os
import sys
import re
import numpy as np
import subprocess

loaded_modules_cache = []


# Start up routine. Currently it only checks if PBS_O_WORKDIR is defined, that means this is a PBS work and changes to the appropiate working directory.
def __init__():
    # is this a pbs work?
    if 'PBS_O_WORKDIR' in os.environ: 
        os.chdir(os.environ['PBS_O_WORKDIR'])

# Recursively explores a directory tree and appends all file names to module_files list
def _explore_module_hierarchy(name):
    module_files = []
    for element in os.listdir(name):
        path = os.path.join(name, element)
        if os.path.isfile(path):
            if 'modulerc' not in path:
                module_files.append(path)
        else:
            module_files += _explore_module_hierarchy(path)
    return module_files

# Reads conf file looking for MODULEPATH word, appends path to modules_dict directory, then it calls _explore_module_hierarchy() to discover related modules.
def _load_modules_name(conf):
    modules_dict = {}
    f = open(conf)
    for line in f:
        if '#' in line:
            continue
        if 'MODULEPATH' in line:
            modules_dict[line.split()[-1]] = []
    f.close()
    
    for k in modules_dict:
        modules_dict[k] = _explore_module_hierarchy(k)
    return modules_dict

# Every time regular expression \${\w*} appears, for example $i or $my_var, it expands the variable from local_vars dictionary. Returns the fully expanded variable, it means if
# T = 'asdf'
# G = $T hjkl
# then G expands to 'asdfhjkl'
def _expand_variables(variable, local_vars):
    m = re.search('\${\w*}', variable)
    if m is None:
        return variable
    else:
        i, j = m.span()
        var = variable[i+2:j-1]
        variable = variable[:i] + local_vars[var] + variable[j:]
        return _expand_variables(variable, local_vars)

# Adds a new environment variable
def _opt_prepend(path, new_path):
    if path in os.environ:
        os.environ[path] = new_path + ':' + os.environ[path]
    else:
        os.environ[path] = new_path

# Removes an environment variable
def _opt_pop(path, remove_path):
    p = os.environ[path]
    i = p.index(remove_path)
    os.environ[path] = p[:i] + p[i+len(remove_path):]
    os.environ[path] = os.environ[path].replace('::', ':')

# Returns a list of tuples with the key for os.environ and the new path to append
def _parse_module_file(mf):
    local_vars = {}
    paths = []

    for line in mf:
        line = line.split()
        if len(line) == 0:
            continue
        if line[0] == 'set':
            value = _expand_variables(line[2], local_vars)
            local_vars[line[1]] = value
        elif line[0] == 'prepend-path':
            new_path = _expand_variables(line[2], local_vars)
            paths.append((line[1], new_path))
    return paths

# Transforms a list to a printable string. 
def _printable_layout(l, line_len):
    printable = ''

    l = [str(s) for s in l]
    num_cols  = int(np.floor(line_len / max([len(s) for s in l])))
    col_width = int(np.ceil(line_len / num_cols))
    orig_size = len(l)

    l = np.array(l)
    l = np.resize(l, (int(num_cols), int(np.ceil(orig_size/num_cols))))
    l = l.T.flatten()[:orig_size]
    l = [str(s) for s in l]

    col = 0
    for name in l:
        printable += name
        if col == num_cols-1:
            printable += '\n'
            col = 0
        else:
            printable += (col_width - len(name)) * ' '
            col += 1
    if printable[-1] != '\n':
        printable += '\n'
    return printable


def avail(return_str=False):
    r_str = ''
    avail_modules = _load_modules_name(modulerc)
    line_len = os.get_terminal_size().columns
    for k,v in avail_modules.items():
        if len(v) == 0:
            continue
        dash_prefix = (line_len - len(k) - 2) // 2
        dash_sufix  = line_len - len(k) - 2 - dash_prefix 
        r_str += dash_prefix*'-' + ' ' + str(k) + ' ' + dash_sufix*'-' + '\n'
        module_names = [n[len(k)+1:] for n in v]
        module_names.sort()
        r_str += _printable_layout(module_names, line_len)
    if return_str:
        return r_str
    else:
        print(r_str)


def load(module_name):

    avail_modules = _load_modules_name(modulerc).values()
    avail_modules = [item for sublist in avail_modules for item in sublist]

    module = None
    for m in avail_modules:
        if module_name in m:
            module = m
            break
    if module is None:
        raise ValueError("Module %s not found, try running modules.avail()" % module_name)

    mf = open(module)
    paths = _parse_module_file(mf)
    for p in paths:
         _opt_prepend(p[0], p[1]) 
    mf.close()
    loaded_modules_cache.append((module_name, module))

def loaded(return_str=False):
    r_str = "Currently loaded modules:\n"
    modules_name = [i[0] for i in loaded_modules_cache]
    r_str += _printable_layout(modules_name, os.get_terminal_size().columns)
    if return_str:
        return r_str
    else:
        print(r_str)

def unload(module_name):
    module_path = None
    for m in loaded_modules_cache:
        if module_name == m[0]:
            module_path = m[1]
            break
    if module_path is None:
        raise ValueError('Module %s is not loaded' % module_name)

    mf = open(module_path)
    paths = _parse_module_file(mf)
    mf.close()

    for p in paths:
        _opt_pop(p[0], p[1])

    print('Module %s unloaded' % module_name)


def run(command, capture_output=False):
    if type(command) is not list:
        raise ValueError("Command must be a list, e.g.: [\"python\", \"my_script.py\", \"paramter1\", \"parameter2\"]")
    if capture_output:
        process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        return (process.returncode, process.stdout, process.stderr)
    else:
        process = subprocess.run(command, universal_newlines=True)
        return process.returncode
   
__init__()
