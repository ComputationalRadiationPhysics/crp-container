import json, sys, os
import shutil, subprocess
from typing import Dict

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import recipe as rc

def main():
    check_singularity()

    # generate recipe
    recipe = rc.recipe()

    # write recipe to file
    with open('recipe.def', 'w') as recipe_file:
        recipe_file.write(recipe)
        recipe_file.close()


    # build image
    process = subprocess.Popen(['singularity',
                                'build',
                                '--fakeroot',
                                'cling-alpaka.sif',
                                'recipe.def'],
                               stdout=subprocess.PIPE)
    output, error = process.communicate()
    if error is not None:
        print('"singularity build --fakeroot cling-alpaka.sif recipe.def" failed')
        exit(1)

    # write log
    with open('build.log', 'w') as build_log:
        build_log.write(output.decode('utf-8'))
        build_log.close()


def check_singularity():
    """Check if the singularity container software is available and runs 'singularity --version'

    """
    if not shutil.which('singularity'):
        print('could not find singularity')
        exit(1)

    process = subprocess.Popen(['singularity', '--version'], stdout=subprocess.PIPE)
    output, error = process.communicate()
    if error is not None:
        print('could not run "singularity --version"')
        exit(1)

    print(output.decode("utf-8"))


if __name__ == '__main__':
    main()
