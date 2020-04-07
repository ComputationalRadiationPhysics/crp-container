# About
The scripts creates recipes and build containers for the Alpaka CI. The containers contains different versions of `gcc`, `clang`, `cuda` and `boost` installed via `spack`. The recipes are  designed as incremental build. Every stage is build as own image. This decrease the error-proneness, allows to reuse build stages and allows to distribute the build on different CI instances. The current architecture of the stages are shown in the diagram. Every container has a baseimage, a `cmake` stage and a `boost` stage with different versions.

```
baseimage ---> boost ---> gcc
                     |
                     ---> clang
                     |
                     ---> cuda -
                               |
                               ---> clang
```

The stages of a container are managed via json configuration file:

``` json
{
    "image" : "ubuntu18.04-cuda10.2",
    "build_dir" : "./build_gcc",
	"final_stage_name" : "alpaka_gcc",
    "packages" : [
	{"stage_name" : "cmake",
	 "package_name" : "cmake",
	 "versions" : ["3.16.5"]
	},
	{"stage_name" : "boost",
	 "package_name" : "boost",
	 "versions" : ["",
                       "1.67.0",
                       "1.69.0",
                       "1.71.0"]
	},
	{"stage_name" : "gcc",
	 "package_name" : "gcc",
	 "versions" : ["",
                       "5.5.0",
                       "6.4.0",
                       "7.3.0",
                       "8.1.0",
                       "9.1.0"]
	}
    ]
}
```

# requirements

* [docker](https://www.docker.com/) or [singularity](https://sylabs.io/guides/3.5/user-guide/)
* Python > 3.6
* [hpccm](https://github.com/NVIDIA/hpc-container-maker)

# Usage

``` bash
# run `python recipe.py --help` to see more options
python recipe.py --json /path/to/config.json [--container <docker|singularity>]
# folder name depends on the json config
cd build
# if you want to change the container build folder, because /tmp has not enough space
# export ALPAKA_CI_BUILD_DIR=/path/to/new/build/folder
./build <docker|singularity>
```

# Technical Background

The Python script generates some docker or singularity container recipes and store it in the build directory. The recipes depend on each other. The recipe `00_<name>.[Dockerfile|.sif]` pull a image from Dockerhub and build the baseimage. All following images are depend of it's predecessor. That means `01_<name>.[Dockerfile|.sif]` use `00_<name>.[Dockerfile|.sif]` as baseimage, `02_<name>.[Dockerfile|.sif]` use `01_<name>.[Dockerfile|.sif]` as baseimage and so one. The script `build.sh` run the container build command for each recipe in the right order. It also implements a build cache. If a image failed, you can run the script again and it automatically continues after the last successful built image. It also handle it, if a recipe for a image is changed.

# Create a config.json

The minimum json configuration is:

``` json
{
    "image" : "ubuntu18.04-cuda10.2",
    "build_dir" : "./build",
    "packages" : [
	{"stage_name" : "cmake",
	"package_name" : "cmake",
	 "versions" : [""]
	}
    ]
}
```

* **image:** Name of the Docker baseimage (supported are: `ubuntu16.04`, `ubuntu18.04`, `ubuntu18.04-cuda10.2`)
* **build_dir:** Folder, where the recipes are stored
* **final_stage_name:** It is a optional attribute. If it is set, the last image of the image stack is renamed to the attribute value.
* **stage_name:** Name of the recipe for the stage
* **package_name:** Name of a Spack package
* **versions:** Versions, which should installed (empty string means default build)

In the folder `productive-config` are configurations, which are designed for the Alpaka CI. The folder `test-config` contains configurations for test container, which can be build fast.

# Test

All tests are done with the configurations in `productive-config`, `CMake 3.16.5`, `Boost 1.71.0` and Alpaka develop branch at commit:

```
commit cb87c59bb4f27eed43bc643693eb3c1055b73985
Author: René Widera <r.widera@hzdr.de>
Date:   Mon Mar 30 12:49:04 2020 +0200

    CMake search rocrand and hiprand (#948)

    search for rocrand and hiprand

    Co-authored-by: Matthias Werner <Matthias.Werner1@tu-dresden.de>

    Co-authored-by: Matthias Werner <Matthias.Werner1@tu-dresden.de>

```

|     |  Container  | Recpie name        | Compiler version                             | CMake Arguments                                                               | Notes |
|-----|-------------|--------------------|----------------------------------------------|-------------------------------------------------------------------------------|-------|
| [x] |    Docker   | t1_gcc.json        | GCC 8.1.0                                    | -DALPAKA_ACC_GPU_CUDA_ENABLE=OFF                                              |       |
| [x] | Singularity | t1_gcc.json        | GCC 8.1.0                                    | -DALPAKA_ACC_GPU_CUDA_ENABLE=OFF                                              |       |
| [x] |    Docker   | t2_clang.json      | Clang 8.0.0                                  | -DALPAKA_ACC_GPU_CUDA_ENABLE=OFF                                              |       |
| [x] | Singularity | t2_clang.json      | Clang 8.0.0                                  | -DALPAKA_ACC_GPU_CUDA_ENABLE=OFF                                              |       |
| [x] |    Docker   | t3_cuda.json       | CUDA 10.1.243                                |                                                                               |       |
| [x] | Singularity | t3_cuda.json       | CUDA 10.1.243                                | -DCMAKE_LIBRARY_PATH=/usr/local/cuda/lib64/stubs                              |       |
| [ ] |    Docker   | t4_cuda-clang.json | Clang 8.0.0 as CUDA-Compiler (CUDA 10.0.130) | -DCMAKE_LIBRARY_PATH=/usr/local/cuda/lib64/stubs -DALPAKA_CUDA_COMPILER=clang | [1]   |
| [ ] | Singularity | t4_cuda-clang.json | Clang 8.0.0 as CUDA-Compiler (CUDA 10.0.130) | -DCMAKE_LIBRARY_PATH=/usr/local/cuda/lib64/stubs -DALPAKA_CUDA_COMPILER=clang | [2]   |

[1]

* build failed with
  alpaka/include/alpaka/mem/buf/BufUniformCudaHipRt.hpp:404:50: error: implicit conversion changes signedness: 'const int' to 'std::size_t' (aka 'unsigned long') [-Werror,-Wsign-conversion]: std::size_t pitchBytes = widthBytes;
* if fixed, `memView` failed

[2]

* same problems like docker version, just `queue` also failed
