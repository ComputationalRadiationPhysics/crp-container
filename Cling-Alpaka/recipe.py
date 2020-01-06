import sys, os, json

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Alpaka'))
import generator as ap_gn

import hpccm
from hpccm.primitives import raw, baseimage, shell

def main():
    hpccm.config.set_container_format('singularity')
    hpccm.config.set_singularity_version('3.3')
    stage = hpccm.Stage()

    # the baseimage of xeus-cling-cuda is Ubuntu 16.04 with CUDA 8
    if not ap_gn.add_alpaka_dep_layer(stage, '16.04', True, []):
        print('adding the alpaka dependencies layer failed', file=sys.stderr)
        exit(1)

    build_jupyter_kernel(stage)

    # baseimage support nothing  else than dockerhub
    # so, manually add the baseimage command to the recipe
    recipe = stage.__str__()
    recipe = 'Bootstrap: library\nFrom: sehrig/default/xeus-cling-cuda-cxx:2.2\n\n' + recipe

    print(recipe)

def build_jupyter_kernel(stage):
    """Add the different Alpaka kernel versions to Jupyter Notebook.

    :param stage: the hpccm stage
    :type stage: hpccm.Stage

    """
    kernel_register = []
    kernel_register.append('mkdir -p /opt/miniconda3/share/jupyter/kernels/')
    kernel_register.append('cd /opt/miniconda3/share/jupyter/kernels/')
    for std in [11, 14, 17]:
        # without and with CUDA mode
        for acc in ['', '-cuda']:
            kernel_path = 'alpaka-cpp' + str(std) + acc
            kernel_register.append('mkdir -p ' + kernel_path)
            kernel_register.append("echo '" +
                                   gen_jupyter_kernel(std, acc) +
                                   "' > " + kernel_path + "/kernel.json")

    kernel_register.append('cd -')
    stage += shell(commands=kernel_register)

def gen_jupyter_kernel(std, acc):
    """Create the different Alpaka kernel json's.

    :param std: C++ Standard: 11, 14 or 17
    :type std: str
    :param acc: If CUDA mode or not: "" or "-cuda"
    :type acc: str

    """
    display_name = 'Alpaka-C++' + str(std) + acc.upper()
    argv = ['/opt/miniconda3/bin/xcpp',
            '-f',
            '{connection_file}',
            '-std=c++'+str(std),
            "-I/usr/local/include/c++/v1",
            "-fopenmp"
            ]
    if 'cuda' in acc:
        argv.append('-xcuda')

    return json.dumps({
            'display_name': display_name,
            'argv': argv,
            'language': 'C++'
    }
    )


if __name__ == '__main__':
    main()
