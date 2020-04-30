import argparse, sys
from typing import Tuple, List, Dict, Union

import generator as gn

import hpccm
from hpccm.primitives import baseimage, shell

images = {'ubuntu16.04' : 'ubuntu:xenial',
          'ubuntu18.04' : 'ubuntu:bionic',
          'cuda8' : 'nvidia/cuda:8.0-devel-ubuntu16.04',
          'cuda9' : 'nvidia/cuda:9.0-devel-ubuntu16.04',
          'cuda9.1' : 'nvidia/cuda:9.1-devel-ubuntu16.04',
          'cuda9.2' : 'nvidia/cuda:9.2-devel-ubuntu16.04',
          'cuda10.0' : 'nvidia/cuda:10.0-devel-ubuntu18.04',
          'cuda10.1' : 'nvidia/cuda:10.1-devel-ubuntu18.04',
          'cuda10.2' : 'nvidia/cuda:10.2-devel-ubuntu18.04'}

compilers = ['gcc', 'clang']

def main():
    parser = argparse.ArgumentParser(
        description='Script to generate a container receipt for Alpaka',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--container', type=str, default='singularity',
                        choices=['docker', 'singularity'],
                        help='generate receipt for docker or singularity (default: singularity)')
    parser.add_argument('-i',  type=str, default='ubuntu18.04',
                        choices=images.keys(),
                        help='Choice the base image. (default: ubuntu18.04)')
    parser.add_argument('-c',  metavar='', nargs='+', type=str,
                        help='Install extra compiler. Supported are GCC and Clang. '
                        'E.g -c gcc:8 clang:7.0 clang:8')
    parser.add_argument('--alpaka', action='store_true',
                        help='Install Alpaka to /usr/local')


    args = parser.parse_args()

    # verify distribution, CUDA support and extra compiler
    ubuntu_version = check_distribution(images[args.i])
    cuda_support = True if 'cuda' in args.i else False
    if args.c:
        check_compiler(args.c)

    # create baseimage
    hpccm.config.set_container_format(args.container)
    if args.i == 'singularity':
        hpccm.config.set_singularity_version('3.3')
    stage = hpccm.Stage()
    stage += baseimage(image=images[args.i])

    if not gn.add_alpaka_dep_layer(stage, ubuntu_version, cuda_support ,args.c, args.alpaka):
        print('add alpaka dependencies layer failed', file=sys.stderr)
        exit(1)

    install_ninja(stage)

    print(stage)

def check_distribution(image_name : str) -> str:
    """Check if distribution name is a valid Ubuntu version.

    :param image_name: distribution name
    :type image_name: str
    :returns: ubuntu version number: '16.04' or '18.04'
    :rtype: str

    """
    if 'xenial' in image_name or '16.04' in image_name:
        return '16.04'
    elif 'bionic' in image_name or '18.04' in image_name:
        return '18.04'
    else:
        print('unknown distribution', file=sys.stderr)
        exit(1)

def check_compiler(compiler_list : List[str]):
    """Check if extra compiler is supported

    :param check_list: list of compilers
    :type check_list: str
    """
    for ch in compiler_list:
        found = False
        for c in compilers:
            if ch.startswith(c + ':'):
                found = True
        if not found:
            print(ch + ' is not a supported compiler', file=sys.stderr)
            exit(1)

def install_ninja(stage : hpccm.Stage):
    """Install ninja build system

    :param stage: hpccm stage
    :type stage: hpccm.Stage

    """
    stage += shell(commands=['cd /opt',
                             'wget https://github.com/ninja-build/ninja/releases/download/v1.9.0/ninja-linux.zip',
                             'unzip ninja-linux.zip',
                             'mv ninja /usr/local/bin/',
                             'rm ninja-linux.zip',
                             'cd -'])

if __name__ == '__main__':
    main()
