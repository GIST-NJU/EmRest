# INSTALL PICT ON CentOS 7

## Install CMAKE

1. Download cmake (version > 3.13) `cmake-3.28.0-linux-x86_64.sh`
2. Install it to `/usr/local`, using the command `sh cmake-3.28.0-linux-x86_64.sh --prefix=/usr/local --exclude-subdir`
3. Verify the installation with `cmake -version`

## Install PICT

1. Clone the PICT repository `git clone git@github.com:microsoft/pict.git`
2. Prepare for building `cd pict/ & mkdir build & cp CMakeLists.txt build/`
3. Build with `cmake -DCMAKE_BUILD_TYPE=Release -S . -B build`
4. Compile with `cmake --build build` (If this step fails, upgrade gcc and start again from step 3, see https://github.com/microsoft/pict/issues/94)
5. The pict binary will be located at `pict/build/cli/pict`

## Upgrade GCC (https://www.cnblogs.com/jixiaohua/p/11732225.html)

The GCC version on the server is outdated, upgrade it to version 10.

1. Install the CentOS Software Collections `sudo yum install centos-release-scl`
2. Install the desired devtoolset (version > 9). To install a specific version, use devtoolset-7-gcc*, and so on. For example: `sudo yum install devtoolset-8-gcc*`
3. Activate the corresponding devtoolset. You can install multiple versions and switch between them as needed using this command: `scl enable devtoolset-8 bash`
4. Done! Check the GCC version with `gcc -v`

[Optional]
Note: The activation command only applies to the current session, and the GCC version will revert to the original 4.8.5 after restarting the session. To switch versions persistently:
The installed devtoolset is located under the `/opt/rh` directory, where each version has an `enable` file. To enable a specific version, run `source ./enable`.
You can write a shell script to switch between versions or set it to automatically start at boot.
