# Introduction #

This page provides generic instructions (i.e., they are independent of the system being evaluated) on how to run the Benchmark.

## Step 1: Topology generation ##

The first step for running the benchmark is the generation of the topologies over which the data processing tasks will operate over.

The `genTopologies.py` script generates network topologies, which takes as parameters _<networkSize,nodeLayout,nodeDensity,numInstances>_.  These are read from the `experiments.csv` file.

The first three parameters correspond to properties of the network.  The _numInstances_ parameter determines how many network topologies to generate using the first three parameters.  As a default, in the paper, we set _numInstances=10_.  This means that there are ten runs for each experiment scenario.

The scripts are designed to be easily extended, enabling network topology files to be created in the format required by each system being evaluated, and also the simulator used.  See the [AddingNewSystems](AddingNewSystems.md) page for more information on how to do this.

If a particular system has the ability to assign some of the nodes in the networks as sources, and others as relays, the topology generation script can also generate a file specifying this information on a per-system basis using the _proportionOfSources_ variable, and assigning random nodes to be sources for each topology instance.

## Step 2: Prepare the simulator jobs ##

In this step, for each combination of the variables specified in `experiments.csv`, we prepare jobs to be run by the simulator.  This involves preparing the inputs for each run of the simulator.   This may involve generating source files and compiling executables (as is the case with SNEE) or selecting the appropriate pre-compiled binaries (as is done for MHOSC), selecting the appropriate topology file generated in the first step, and generating parameter strings for the simulator.  We note that the requirements vary considerably depending on the system being evaluated.  We have a prepared generic script called `prepSimJobs.py` which invokes system specific libraries.  New systems can be incorporated by adding a new library and invoking the library from the script.

## Step 3: Run the simulations ##

The third step is to run the simulations.  In our case, we used the Avrora simulator.  You can run the simulator jobs on a local PC in a sequential manner using the `runAvrSim.py` script.

As we generated a considerable number of topology instances, we used [HTCondor](http://research.cs.wisc.edu/htcondor/), an open-source distributed high-throughput computing software framework developed at the University of Wisconsin-Madison that enables simulations to run in parallel on a computer cluster.  The `prepCondorJobs.py` script takes a collection of jobs from Step 2 and prepares them to be submitted to the HTCondor framework.  See the [UsingCondor](UsingCondor.md) page on instructions about using HTCondor.

We note that the use of HTCondor is an optional step, although it considerably improves performance when running the experiments.


## Step 4: Parse the simulator output ##

The next step is to parse and analyse the simulator output, to obtain the performance metrics for each run, using the `parseSimResults.py` script.

## Step 5: Visualize the results ##

We have prepared `gnuplot` scripts to enable users of the benchmark to view raw results (i.e., for each instance) and aggregated results (i.e., the average for all the instances of a particular run).