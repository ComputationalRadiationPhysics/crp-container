# About

The container provides an environment to build and run [Alpaka](https://github.com/ComputationalRadiationPhysics/alpaka) application. The Alpaka library is not part of the container.

The following backends are supported:
- AccCpuSerial
- AccGpuCudaRt (if baseimage has CUDA)
- AccCpuThreads
- AccCpuOmp2Threads
- AccCpuOmp2Blocks
- AccCpuOmp4

# Create Recipe

Run `python recipe.py --help` to see all parameter. The recipe is printed on the stdout.

# Build Container
## Singularity

```bash
singularity shell --fakeroot container.sif recipe.def
```

## Docker

```bash
docker build . -f Dockerfile -t image:tag
```

# Run Shell
## Singularity

```bash
# --nv only for cuda support necessary
singularity shell --nv container.sif
```

## Docker

```bash
# --runtime=nvidia only for cuda support necessary
# -v $HOME:$HOME mount home directory in the container
docker run --runtime=nvidia -v $HOME:$HOME -it image:tag
```
