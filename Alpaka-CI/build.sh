#!/bin/bash

# the variable change the container build folder
# check if environment variable is set
if [ -z ${ALPAKA_CI_BUILD_DIR+x} ]; then
    ALPAKA_CI_BUILD_DIR=""
fi

if [ -n "$ALPAKA_CI_BUILD_DIR" ]; then
    ALPAKA_CI_BUILD_DIR="--tmpdir $ALPAKA_CI_BUILD_DIR"
fi

if [ "$#" -gt 0 ]; then
    if [ $1 == "--help" ] || [ $1 == "-h" ]; then
	echo "usage: ./build.sh [docker|singularity]"
	exit 0
    fi
    if [ $1 == "docker" ]; then
        container="docker"
	recipe_extension=".Dockerfile"
	container_extension=""
    else
	if [ $1 == "singularity" ]; then
	    container="singularity"
	    recipe_extension=".def"
	    container_extension=".sif"
	else
	    echo "unknown argument: $1"
	    exit 1
	fi
    fi
else
    echo "usage: ./build.sh [docker|singularity]"
    exit 1
fi

# create a build cache
if [ ! -d ".cache" ]; then
    mkdir .cache
fi

# because every image is depend of his predecessor, all following images have to
# rebuild, if a image changed
break_chain=0

# grep all recipes
recipes=$(ls | grep "[0-9][0-9][a-z_]*.${recipe_extension}")
for recipe in $recipes ; do
    # there are 3 rules, which have to matched, that a image will not rebuild
    # 1. image chain is not broken -> means, if a image is rebuild, all
    #    following images have to rebuild
    # 2. a recipe of the current image have to be in .cache -> if a build of a
    #    image was successful, the script copy the recipe of it in .cache
    # 3. the recipe of the current image have to be equal like the version in
    #    .cache -> the recipe has change, rebuild
    cmp -s "$recipe" ".cache/${recipe}"
    cmp_ret=$?
    if [ $break_chain -eq 1 ] || [ ! -f ".cache/${recipe}" ] || [ $cmp_ret -ne 0 ]; then
	break_chain=1
	if [ $container == "docker" ]; then
	    echo "docker build -f $recipe . -t ${recipe%.*} |& tee d_${recipe%.*}.log"
	    docker build -f $recipe . -t ${recipe%.*} |& tee d_${recipe%.*}.log
	else
	    echo "singularity build --fakeroot -F ${ALPAKA_CI_BUILD_DIR} ${recipe%.*}${container_extension} $recipe |& tee s_${recipe%.*}.log"
	    singularity build --fakeroot -F ${ALPAKA_CI_BUILD_DIR} ${recipe%.*}${container_extension} $recipe |& tee s_${recipe%.*}.log
	fi
	if [ $? -eq 0 ]; then
	    # if the build was successful, copy the recipe to .cache
	    cp $recipe ".cache/${recipe}"
	else
	    exit 1
	fi
    fi
done
