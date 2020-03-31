# About
The scripts creates recipes and build a container for the Alpaka CI. The container contains different versions of `gcc`, `clang`, `cuda` and `boost` installed via `spack`. The scripts an incremental container build, because a complete build takes a long time and a single error can crash the whole build waste all work.

# requirements

* [docker](https://www.docker.com/) or [singularity](https://sylabs.io/guides/3.5/user-guide/)
* Python > 3.6
* [hpccm](https://github.com/NVIDIA/hpc-container-maker)

# Usage

``` bash
# run `python recipe.py --help` to see more options
python recipe.py
cd build
# if you want to change the container build folder, because /tmp has not enough space
# export ALPAKA_CI_BUILD_DIR=/path/to/new/build/folder
./build singularity
```

# Technical Background

The Python script generates some docker or singularity container recipes and store it in the `build` directory. The recipes depend on each other. The recipe `00_<name>.[Dockerfile|.sif]` pull a image from Dockerhub and build the baseimage. All following images are depend of it's predecessor. That means `01_<name>.[Dockerfile|.sif]` use `00_<name>.[Dockerfile|.sif]` as baseimage, `02_<name>.[Dockerfile|.sif]` use `01_<name>.[Dockerfile|.sif]` as baseimage and so one. The script `build.sh` run the container build command for each recipe in the right order. It also implements a build cache. If a image failed, you can run the script again and it automatically continues after the last successful built image. It also handle it, if a recipe for a image is changed.

# Modify the recipe

The python function `incremental_stage` in recipe.py is responsible to install spack packages.

``` python
# ...

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

# ...

final_stage()

# ...
```

Each `incremental_stage` function call generates a recipe. The order of the calls describes the dependency between the recipes. It is also possible to split the install of a package in two recipes:

``` python
# install the current gcc version an the dependencies
incremental_stage(stage_name='gcc_image',
                  spack_package='gcc',
				  versions=[''])
# install additional gcc versions
incremental_stage(stage_name='gcc_image',
                  spack_package='gcc',
				  versions=['5.5.0',
							'6.4.0',
							'7.3.0',
							'8.1.0',
							'9.1.0'])

```
