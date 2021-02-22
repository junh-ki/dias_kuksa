# JSON data structure file to create the in-vehicle GENIVI VSS server, `kuksa-val-server` [(Link)](https://github.com/eclipse/kuksa.val).

* Here, `modified.json` is the `make` result of `vehicle_signal_specification` [(Link)](https://github.com/GENIVI/vehicle_signal_specification) with the `spec/` folder. 

Please refer to [DIAS-KUKSA: KUKSA.val VSS Server Setup](https://dias-kuksa-doc.readthedocs.io/en/latest/contents/invehicle.html#kuksa-val-kuksa-val-vss-server-setup) for detailed information.

## Prerequisites

* Built `kuksa.val` infrastructure. [(Link)](https://github.com/eclipse/kuksa.val)

## Step 1: Recursively clone `vehicle_signal_specification`
~~~
$ git clone --recurse-submodules https://github.com/GENIVI/vehicle_signal_specification.git
~~~

## Step 2: Make changes on `vehicle_signal_specification/spec/` according to the data structure one wants to create.

In order to change the structure of `modified.json`, the `spec/` should be redesigned according to one's preference. Here, the default `modified.json` follows the structure intended for DIAS-KUKSA.

## Step 3: Make changes on `vehicle_signal_specification/Makefile` according to one's preferred file format.

In order to produce a JSON file only, make changes on `Makefile` as follow:
~~~
#
# Makefile to generate specifications
#

.PHONY: clean all json

all: clean json

DESTDIR?=/usr/local
TOOLSDIR?=./vss-tools
DEPLOYDIR?=./docs-gen/static/releases/nightly


json:
    ${TOOLSDIR}/vspec2json.py -i:spec/VehicleSignalSpecification.id -I ./spec ./spec/VehicleSignalSpecification.vspec vss_rel_$$(cat VERSION).json

clean:
    rm -f vss_rel_$$(cat VERSION).json
    (cd ${TOOLSDIR}/vspec2c/; make clean)

install:
    git submodule init
    git submodule update
    (cd ${TOOLSDIR}/; python3 setup.py install --install-scripts=${DESTDIR}/bin)
    $(MAKE) DESTDIR=${DESTDIR} -C ${TOOLSDIR}/vspec2c install
    install -d ${DESTDIR}/share/vss
    (cd spec; cp -r * ${DESTDIR}/share/vss)

deploy:
    if [ -d $(DEPLOYDIR) ]; then \
        rm -f ${DEPLOYDIR}/vss_rel_*;\
    else \
        mkdir -p ${DEPLOYDIR}; \
    fi;
        cp  vss_rel_* ${DEPLOYDIR}/
~~~

## Step 4: Navigate to `vehicle_signal_specification/` and execute `make`

~~~
$ make
~~~

## Step 5: Rename the result JSON file as `modified.json`

## Step 6: Place the JSON file to `kuksa.val/build/src`, the directory where `kuksa-val-server` is located

## Step 7: Navigate to `kuksa.val/build/src` and run `kuksa-val-server` with the JSON file

~~~
$ ./kuksa-val-server --vss modified.json --insecure --log-level ALL
~~~

By doing so, the VSS data structure defined in the JSON file can be realized in `kuksa-val-server`.
