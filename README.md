Logentries agent
================

A command line utility for a convenient access to logentries logging
infrastructure.


How to use
----------

	usage: le COMMAND [ARGS]

	Where COMMAND is one of:
	init      Write local configuration file
	reinit    As init but does not reset undefined parameters
	register  Register this host
	--name=  name of the host
	--hostname=  hostname of the host
	whoami    Displays settings for this host
	monitor   Monitor this host
	follow <filename>  Follow the given log
	--name=  name of the log
	--type=  type of the log
	followed <filename>  Check if the file is followed
	clean     Removes configuration file
	ls        List internal filesystem and settings: <path>
	rm        Remove entity: <path>
	pull      Pull log file: <path> <when> <filter> <limit>

	Where ARGS are:
	--help            show usage help and exit
	--version         display version number and exit
	--account-key=    set account key and exit
	--host-key=       set local host key and exit, generate key if key is empty
	--no-timestamps   no timestamps in agent reportings
	--force           force given operation
	--datahub         send logs to the specified data hub address
			the format is address:port with port being optional
	--suppress-ssl    do not use SSL with API server
	--yes	            always respond yes


System metrics
--------------

The agent collects system metrics regarding CPU, memory, network, disk, and
processes. Example configuration may look like this:

	[Main]
	user-key = ...
	agent-key = ...
	metrics-interval = 5s
	metrics-token = ...
	metrics-cpu = system
	metrics-vcpu = core
	metrics-mem = system
	metrics-swap = system
	metrics-net = sum eth0
	metrics-disk = sum sda4 sda5
	metrics-space = /

	[cassandra]
	metrics-process = org.apache.cassandra.service.CassandraDaemon


Example output may look like this:

	<14>1 2015-01-28T23:42:03.668428Z myhost le - cpu - user=1.1 nice=0.0 system=0.2 load=1.3 idle=98.6 iowait=0.0 irq=0.0 softirq=0.1 steal=0.0 guest=0.0 guest_nice=0.0 vcpus=8
	<14>1 2015-01-28T23:42:03.668566Z myhost le - vcpu - vcpu=0 user=14.4 nice=0.0 system=0.0 load=14.4 idle=785.6 iowait=0.0 irq=0.0 softirq=0.0 steal=0.0 guest=0.0 guest_nice=0.0 vcpus=8
	<14>1 2015-01-28T23:42:03.668588Z myhost le - vcpu - vcpu=1 user=24.0 nice=0.0 system=1.6 load=25.6 idle=774.4 iowait=0.0 irq=0.0 softirq=0.0 steal=0.0 guest=0.0 guest_nice=0.0 vcpus=8
	<14>1 2015-01-28T23:42:03.668603Z myhost le - vcpu - vcpu=2 user=12.8 nice=0.0 system=1.6 load=14.4 idle=785.6 iowait=0.0 irq=0.0 softirq=0.0 steal=0.0 guest=0.0 guest_nice=0.0 vcpus=8
	<14>1 2015-01-28T23:42:03.668617Z myhost le - vcpu - vcpu=3 user=11.2 nice=0.0 system=1.6 load=12.8 idle=785.6 iowait=0.0 irq=0.0 softirq=1.6 steal=0.0 guest=0.0 guest_nice=0.0 vcpus=8
	<14>1 2015-01-28T23:42:03.668631Z myhost le - vcpu - vcpu=4 user=0.0 nice=0.0 system=0.0 load=0.0 idle=800.0 iowait=0.0 irq=0.0 softirq=0.0 steal=0.0 guest=0.0 guest_nice=0.0 vcpus=8
	<14>1 2015-01-28T23:42:03.668645Z myhost le - vcpu - vcpu=5 user=4.9 nice=0.0 system=4.9 load=9.9 idle=780.3 iowait=0.0 irq=0.0 softirq=9.9 steal=0.0 guest=0.0 guest_nice=0.0 vcpus=8
	<14>1 2015-01-28T23:42:03.668658Z myhost le - vcpu - vcpu=6 user=6.4 nice=0.0 system=1.6 load=8.0 idle=792.0 iowait=0.0 irq=0.0 softirq=0.0 steal=0.0 guest=0.0 guest_nice=0.0 vcpus=8
	<14>1 2015-01-28T23:42:03.668673Z myhost le - vcpu - vcpu=7 user=0.0 nice=0.0 system=0.0 load=0.0 idle=800.0 iowait=0.0 irq=0.0 softirq=0.0 steal=0.0 guest=0.0 guest_nice=0.0 vcpus=8
	<14>1 2015-01-28T23:42:03.668762Z myhost le - mem - total=16770625536 available=86.8 used=45.2 free=54.8 active=12.1 inactive=26.9 buffers=0.7 cached=31.2
	<14>1 2015-01-28T23:42:03.668853Z myhost le - swap - total=0 used=0.0 free=0.0 in=0 out=0
	<14>1 2015-01-28T23:42:03.668977Z myhost le - disk - device=sum reads=0 writes=0 bytes_read=0 bytes_write=0 time_read=0 time_write=0
	<14>1 2015-01-28T23:42:03.669071Z myhost le - disk - device=sda4 reads=0 writes=0 bytes_read=0 bytes_write=0 time_read=0 time_write=0
	<14>1 2015-01-28T23:44:29.185629Z myhost le - disk - device=sda5 reads=19 writes=2135 bytes_read=81920 bytes_write=1005879296 time_read=29 time_write=33004
	<14>1 2015-01-28T23:42:03.669123Z myhost le - space - path="/" size=638815010816 used=87.8 free=7.1
	<14>1 2015-01-28T23:42:03.669212Z myhost le - net - net=eth0 sent_bytes=36230 recv_bytes=1260226 sent_packets=481 recv_packets=848 err_in=0 err_out=0 drop_in=0 drop_out=0
	<14>1 2015-01-28T23:52:48.741521Z myhost le - cassandra - cpu_user=0.6 cpu_system=0.0 reads=250 writes=0 bytes_read=0 bytes_write=8192 fds=141 mem=4.4 total=16770625536 rss=734867456 vms=3441418240


CPU
---

Specify the `metrics-cpu` parameter to collect CPU metrics. Allowed values are
`system` which will normalize usage of all CPUs to 100%, or `core` which will
normalize usage to single CPU (typical for `top` command).

Example:

	metrics-cpu = core
	metrics-cpu = system

Example log entry:

	<14>1 2015-01-28T23:42:03.668428Z myhost le - cpu - user=1.1 nice=0.0 system=0.2 load=1.3 idle=98.6 iowait=0.0 irq=0.0 softirq=0.1 steal=0.0 guest=0.0 guest_nice=0.0 vcpus=8

Fields explained:

-  *user* time spent processing user level processes with normal or negative
   nice value (higher priority)
-  *nice* time spent processing user level processes with positive nice value
   (lower priority)
-  *system* time spent processing system level tasks
-  *usage* total time spent processing
-  *idle* time spent idle, with no outstandign tasks and no incomplete I/O
   operations
-  *iowait* time spent waiting for I/O operation to complete (idle)
-  *irq* time spent servicing/handling hardware interrupts
-  *softirq* time spent servicing/handling soft interrupts. Commonly servicing
   tasks scheduled independently of hardware interrupts.
-  *steal* time not available for the virtual machine, i.e. stolen by
   hypervisor in concurrent virtual environments
-  *guest* time spent running guest operating systems with normal nice value
-  *guest_nice* time spent running guest operating systems with positive nice
   value
-  *vcpus* total number of CPUs

VCPU
----

Specify the `metrics-vcpu` parameter to collect metrics for each individual CPU.
The only viable value is `core` which will normaliza usage to single CPU.

Example:

	metrics-vcpu = core

Example log entry:

	<14>1 2015-01-28T23:42:03.668566Z myhost le - vcpu - vcpu=0 user=14.4 nice=0.0 system=0.0 load=14.4 idle=785.6 iowait=0.0 irq=0.0 softirq=0.0 steal=0.0 guest=0.0 guest_nice=0.0 vcpus=8

Fields are similar to CPU section.

Memory
------

Specify the `metrics-mem` parameter to collect memory metrics. The only viable
value is `system`.

Example:

	metrics-mem = system

Example log entry:

	<14>1 2015-01-28T23:42:03.668762Z myhost le - mem - total=16770625536 available=86.8 used=45.2 free=54.8 active=12.1 inactive=26.9 buffers=0.7 cached=31.2

Fields explained:

-  *total* physical memory size in bytes
-  *available* amount of memory that is available for processes, typically
   free + buffers + cached
-  *used* memory used by OS (includes caches and buffers)
-  *free* memory not used by OS
-  *active* memory marked as recently used (dirty pages)
-  *inactive* memory marked as not used (old pages)
-  *buffers* memory reserved for temporary I/O storage
-  *cached* part of the memory used as disk cache, tmpfs, vms, and
   memory-mapped files

Swap
----

Specify the `metrics-swap` parameter to collect swap area metrics. The only
viable value is `system`.

Example:

	metrics-swap = system

Example log entry:

	<14>1 2015-01-28T23:42:03.668853Z myhost le - swap - total=0 used=0.0 free=0.0 in=0 out=0

Fields explained:

-  *total* size of all swap areas
-  *used* % of swap areas being used
-  *free* % of swap areas being unused
-  *in* input traffic in bytes
-  *out* output traffic in bytes

Network
-------

In the `metrics-net` configuration parameter specify network interfaces for
which the agent will collect metrics.

Special interfaces are `all` which instructs the agent to follow all interfaces
(including lo), `select` which will follow selected interfaces such as eth and
wlan, and `sum` which aggregates usage of all interfaces in the system.

Example:

	metrics-net = eth0
	metrics-net = sum select
	metrics-net = all

Example log entry:

	<14>1 2015-01-28T23:42:03.669212Z myhost le - net - net=eth0 sent_bytes=36230 recv_bytes=1260226 sent_packets=481 recv_packets=848 err_in=0 err_out=0 drop_in=0 drop_out=0

Fields explained:

-  *net* network interface
-  *bytes_sent* number of bytes sent since last record
-  *bytes_recv* number of bytes received since last record
-  *packets_sent* number of packets sent since last record
-  *packets_recv* number of packets received since last record
-  *err_in* number of errors while receiving
-  *err_out* number of errors while sending
-  *drop_in* number of incomming packets which were dropped
-  *drop_out* number of outgoing packets which were sropped

Disk IO
-------

In the `metrics-disk` configuration parameter specify devices for which will the agent
collect metrics.

Special device is `all` which instructs the agent to collect metrics for all devices.


Example:

	metrics-disk = sum sda4 sda5
	metrics-disk = all

Example log entry:

	<14>1 2015-01-28T23:44:29.185629Z myhost le - disk - device=sda5 reads=19 writes=2135 bytes_read=81920 bytes_write=1005879296 time_read=29 time_write=33004

Fields explained:

-  *device* device name
-  *reads* number of read operations since last record
-  *writes* number of write operations since last record
-  *bytes_read* number of bytes read since last record
-  *bytes_write* number of bytes written since last record
-  *time_read* time spent reading from device in milliseconds since last record
-  *time_write* time spent writing to device in milliseconds since last record

Disk space
----------

In the `metrics-space` configuration parameter specify mount points for which
will the agent collect usage metrics.

Example:

	metrics-space = /

Example log entry:

	<14>1 2015-01-28T23:42:03.669123Z myhost le - space - path="/" size=638815010816 used=87.8 free=7.1

Fields explained:

-  *path* disk mount point
-  *size* size of the disk in bytes
-  *used* % of disk space used
-  *free* % of disk space free

Note that used + free might not reach 100% in certain cases.

Processes
---------

To follow a particular process, specify a pattern matching process' command
argument in `metrics-process`. Specify this parameter in a separate section.

Example:

	[cassandra]
	metrics-process = org.apache.cassandra.service.CassandraDaemon

Example log entry:

	<14>1 2015-01-28T23:52:48.741521Z myhost le - cassandra - cpu_user=0.6 cpu_system=0.0 reads=250 writes=0 bytes_read=0 bytes_write=8192 fds=141 mem=4.4 total=16770625536 rss=734867456 vms=3441418240

Fields explained:

-  *cpu_user* the amount of time process spent in user mode
-  *cpu_system* the amount of time process spent in system mode
-  *reads* the number of read operations since last record
-  *writes* the number of write operations since last record
-  *bytes_read* the number of bytes read since last record
-  *bytes_write* the number of bytes writen since last record
-  *fds* the number of open file descriptors
-  *mem* % of memory used
-  *total* total amount of memory
-  *rss* resident set size - the amount of memory this process currently has in
   main memory
-  *vms* virtual memory size - the amount of virtual memory the process has
   allocated, including shared libraries
