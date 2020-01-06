# About

This container combines the [Xeus-Cling-CUDA](https://github.com/ComputationalRadiationPhysics/xeus-cling-cuda-container) software stack with the [Alpaka](https://github.com/ComputationalRadiationPhysics/alpaka) environment. It contains the following components:

* Ubuntu 16.04
* CUDA 8
* Cling
* Xeus-Cling
* Jupyter Notebook and Lab
* Boost
* OpenMP

# Create and Build Container

```bash
# create recipe
python recipe.py > recipe.def
# build container
singularity build --fakeroot cling-alpaka.sif recipe.def
```

# Running

```bash
# run a Jupyter Lab server on Port 8888
singularity run --nv cling-alpaka.sif jupyter-lab
```
