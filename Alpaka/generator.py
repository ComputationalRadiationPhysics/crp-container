import sys
from typing import Tuple, List, Dict, Union

import hpccm
from hpccm.primitives import shell, environment
from hpccm.building_blocks.packages import packages
from hpccm.building_blocks.cmake import cmake
from hpccm.building_blocks.gnu import gnu
from hpccm.building_blocks.llvm import llvm
from hpccm.templates.git import git
from hpccm.templates.CMakeBuild import CMakeBuild

def add_alpaka_dep_layer(stage : hpccm.Stage, ubuntu_version : str,
                         cuda_support : bool, extra_compiler : List[str],
                         alpaka=False) -> bool:
    """Add all dependencies to an hpccm stage that are necessary to build and run Alpaka.

    :param stage: At least a baseimage
    :type stage: hpccm.Stage
    :param ubuntu_version: Ubuntu version number: '16.04' or '18.04'
    :type ubuntu_version: str
    :param cuda_support: Set True, if the Stage supports CUDA
    :type cuda_support: bool
    :param extra_compiler: List of compilers, which are installed additional to the system compiler. Supported are: gcc:[5-9], clang:[5.0-7.0, 8-9]
    :type extra_compiler: str
    :param alpaka: install alpaka in /usr/local
    :type alpaka: bool
    :returns: Returns True if function was successful
    :rtype: bool

    """
    if ubuntu_version != '16.04' and ubuntu_version != '18.04':
        print('not supported Ubuntu version: ' + ubuntu_version, file=sys.stderr)
        print('supported are: 16.04, 18.04', file=sys.stderr)
        return False

    apt_package_list = ['gcc', 'g++', 'make', 'software-properties-common',
                        'wget', 'libc6-dev', 'libomp-dev', 'unzip', 'git']

    if ubuntu_version == '16.04':
        apt_package_list.append('gnupg-agent')
    if ubuntu_version == '18.04':
        apt_package_list.append('gpg-agent')

    stage += packages(ospackages=apt_package_list)

    stage += cmake(eula=True, version='3.16.0')

    # install extra compiler
    if extra_compiler is not None:
        for com in extra_compiler:
            if com.startswith('gcc'):
                stage += gnu(extra_repository=True, version=com[len('gcc:'):])
            if com.startswith('clang'):
                add_clang(stage, ubuntu_version, version=com[len('clang:'):])

    #install boost
    stage += shell(commands=['add-apt-repository -y ppa:mhier/libboost-latest'])
    stage += packages(ospackages=['boost1.67'])

    if cuda_support:
        stage += environment(
            variables={'LD_LIBRARY_PATH': '$LD_LIBRARY_PATH:/usr/local/cuda/lib64'})
        # alpaka use a function direct from the cuda driver library
        # in the container, the cuda libraries are not at the default path
        stage += environment(
            variables={'LIBRARY_PATH': '$LIBRARY_PATH:/usr/local/cuda/lib64/stubs'})
        stage += environment(
            variables={'CMAKE_PREFIX_PATH': '/usr/local/cuda/lib64/stubs/'})

    if alpaka:
        git_alpaka = git()
        cmake_alpaka = CMakeBuild()
        alpaka_commands = []
        alpaka_commands.append(git_alpaka.clone_step(
            repository='https://github.com/alpaka-group/alpaka.git',
            path='/opt'))
        alpaka_commands.append(cmake_alpaka.configure_step(build_directory='build',
                                                           directory='/opt/alpaka',
                                                           opts=['-Dalpaka_BUILD_EXAMPLES=OFF',
                                                                 '-DBUILD_TESTING=OFF']))
        alpaka_commands.append(cmake_alpaka.build_step(target='install'))
        alpaka_commands.append('rm -rf /opt/alpaka')

        stage += shell(commands=alpaka_commands)

    return True

def add_clang(stage : hpccm.Stage, ubuntu_version : str, version : str):
    """Add commands to stage to install clang.

    :param stage: hpccm Stage
    :type stage: hpccm.Stage
    :param ubuntu_version: Ubuntu version number: '16.04' or '18.04'
    :type ubuntu_version: str
    :param version: Clang version: 5.0 - 7.0 or 8 - 9
    :type version: str

    """
    if ubuntu_version == '16.04':
        distro_name = 'xenial'
    elif ubuntu_version == '18.04':
        distro_name = 'bionic'
    else:
        print('clang error: unsupported Ubuntu version: ' + ubuntu_version, file=sys.stderr)
        print('supported Ubuntu version: 16.04, 18.04', file=sys.stderr)
        return

    # clang/llvm changed its name pattern and the ppa sources with clang 8
    # https://apt.llvm.org/
    ppa_version = '' if float(version) < 8.0 else '-' + str(version)

    stage += shell(commands=['wget http://llvm.org/apt/llvm-snapshot.gpg.key',
	                     'apt-key add llvm-snapshot.gpg.key',
	                     'rm llvm-snapshot.gpg.key',
	                     'echo "" >> /etc/apt/sources.list',
	                     'echo "deb http://apt.llvm.org/' + distro_name +
                             '/ llvm-toolchain-' + distro_name + ppa_version + ' main" >> /etc/apt/sources.list',
                             'echo "deb-src http://apt.llvm.org/' + distro_name +
                             '/ llvm-toolchain-' + distro_name + ppa_version + ' main" >> /etc/apt/sources.list'
    ])
    stage += llvm(version=str(version))
