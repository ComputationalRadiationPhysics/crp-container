import argparse, os
from typing import Tuple, List, Dict, Union

import hpccm
from hpccm.primitives import baseimage, shell, environment
from hpccm.building_blocks.packages import packages
from hpccm.templates.git import git

images = {'ubuntu16.04' : 'ubuntu:xenial',
          'ubuntu18.04' : 'ubuntu:bionic'}

spack_install='/opt/spack/bin/spack install -y -n {0} target=x86_64'

# save all stages of the container build
# each element has the Shape List[str, stage]
# str contains the stage name
image_stack=[]
# can be docker or singularity
container_typ=''

def parse_args() -> argparse.Namespace:
    """Parse the input arguments and returns a argparse.Namespace object.

    :returns: argparse.Namespace object
    :rtype: argparse.Namespace

    """
    parser = argparse.ArgumentParser(
        description='Script to generate a container receipt for Alpaka CI',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--container', type=str, default='singularity',
                        choices=['docker', 'singularity'],
                        help='generate receipt for docker or singularity (default: singularity)')
    parser.add_argument('-i',  type=str, default='ubuntu18.04',
                        choices=images.keys(),
                        help='Choice the base image. (default: ubuntu18.04)')
    args = parser.parse_args()
    return args

def prefix_image(image_name : str) -> str:
    """Prefix the image name with a continues increasing number to get a unique name.

    :param image_name: the name of the image
    :type image_name: str
    :returns: the name of the image with a unique prefix number
    :rtype: str

    """
    return (str(len(image_stack)).zfill(2) + '_' + image_name)

def get_previos_image() -> hpccm.Stage:
    """Return a new stage object which has as baseimage the previous image in the image_stack.

    :returns: Stage object with baseimage
    :rtype: hpccm.Stage

    """
    stage = hpccm.Stage()
    image_name = image_stack[-1][0]
    if container_typ == 'singularity':
        image_name += '.sif'
    stage += baseimage(_bootstrap='localimage', _distro='ubuntu', image=image_name)
    return stage

def base_stage(image_name : str):
    """Create the Baseimage of the image stack. Pull a container from Docker, install
Packages via apt and install Spack. The stage will be append to image_stack.

    :param image_name: Name of the Docker Image (see images)
    :type image_name: str

    """
    stage = hpccm.Stage()
    stage += baseimage(_bootstrap='docker', image=images[image_name])

    package_manager =['apt-transport-https', 'autoconf', 'build-essential',
                      'bzip2', 'ca-certificates', 'coreutils', 'curl',
                      'environment-modules', 'gdb', 'git', 'g++', 'gzip',
                      'less', 'libc6-dev', 'libomp-dev', 'libssl-dev',
                      'locales', 'locales-all', 'make', 'nano', 'patch',
                      'pkg-config', 'software-properties-common', 'tar', 'tcl',
                      'unzip', 'wget', 'zlib1g']

    if '16.04' in image_name:
        package_manager.append('gnupg-agent')
    if '18.04' in image_name:
        package_manager.append('gpg-agent')

    stage += packages(ospackages=package_manager)

    stage += shell(commands=['locale-gen en_US.UTF-8',
                              'update-locale LANG=en_US.UTF-8'])

    # Setup and install Spack
    stage += shell(commands=[
        git().clone_step(repository='https://github.com/spack/spack',
                         branch='master', path='/opt'),
        '/opt/spack/bin/spack bootstrap',
        'ln -s /opt/spack/share/spack/setup-env.sh /etc/profile.d/spack.sh',
        'ln -s /opt/spack/share/spack/spack-completion.bash /etc/profile.d'])
    stage += environment(variables={'PATH': '/opt/spack/bin:$PATH',
                                    'FORCE_UNSAFE_CONFIGURE': '1'})

    image_stack.append([prefix_image('base_image'), stage])

def incremental_stage(stage_name : str, spack_package : str, versions : List[str]):
    """Add a new stage to image_stack. The stage use as baseimage the last
image of image_stack. The stage runs spack install commands. Each stage
generates recipe file.


    :param stage_name: Name of the recipe. Does not need to be unique.
    :type stage_name: str
    :param spack_package: Name of the spack package.
    :type spack_package: str
    :param versions: List of package versions. '' means install default version
    :type versions: List[str]


    """
    stage = get_previos_image()
    stage += environment(variables={'PATH': '/opt/spack/bin:$PATH',
                                    'FORCE_UNSAFE_CONFIGURE': '1'})

    spack_packages = []
    for v in versions:
        # if install a specific version, add a @ -> e.g. llvm@9.0
        spack_packages.append(spack_install.format(spack_package + ("@" if v != "" else "")  + v))

    stage += shell(commands=spack_packages)

    image_stack.append((prefix_image(stage_name), stage))

def finale_stage():
    """Add a new stage to image_stack. The stage use as baseimage the last
image of image_stack. The stage do some cleanups and set the environment.

    """
    stage = get_previos_image()
    stage += environment(variables={'PATH': '/opt/spack/bin:$PATH',
                                    'FORCE_UNSAFE_CONFIGURE': '1'})
    stage += shell(commands=['rm -rf /usr/local/cuda',
                             'spack clean --all'])

    image_stack.append((prefix_image('final_image'), stage))

def main(args):
    global container_typ
    container_typ=args.container
    hpccm.config.set_container_format(container_typ)
    if container_typ == 'singularity':
        hpccm.config.set_singularity_version('3.3')

    base_stage(args.i)
    incremental_stage(stage_name='cmake_image',
                      spack_package='cmake',
                      versions=['3.16.5'])
    incremental_stage(stage_name='gcc_image',
                      spack_package='gcc',
                      versions=['', # install latest version
                                '5.5.0',
                                '6.4.0',
                                '7.3.0',
                                '8.1.0',
                                '9.1.0'])
    incremental_stage(stage_name='llvm_image',
                      spack_package='llvm',
                      versions=['',
                                '5.0.2',
                                '6.0.1',
                                '7.1.0',
                                '8.0.0',
                                '9.0.1'])
    incremental_stage(stage_name='cuda_image',
                      spack_package='cuda',
                      versions=['',
                                '9.0.176',
                                '9.1.85',
                                '9.2.88',
                                '10.0.130',
                                '10.1.243'])
    incremental_stage(stage_name='boost_image',
                      spack_package='boost',
                      versions=['',
                                '1.67.0',
                                '1.69.0',
                                '1.71.0'])
    finale_stage()

    if not os.path.exists('./build'):
        os.makedirs('./build')
        os.symlink(os.getcwd() + '/build.sh', os.getcwd() + '/build/build.sh')

    file_suffix = '.def' if container_typ == 'singularity' else 'Dockerfile'

    for image in image_stack:
        with open('./build/' + image[0] + file_suffix, 'w') as filehandle:
            filehandle.write(image[1].__str__())

if __name__ == "__main__":
    args = parse_args()
    main(args)
