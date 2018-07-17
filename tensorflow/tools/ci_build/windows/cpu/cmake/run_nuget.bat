:: This script assumes the standard setup on tensorflow Jenkins windows machines.
:: It is NOT guaranteed to work on any other machine. Use at your own risk!
::
:: REQUIREMENTS:
:: * All installed in standard locations:
::   - JDK8, and JAVA_HOME set.
::   - Microsoft Visual Studio 2015 Community Edition
::   - Msys2
::   - Anaconda3
::   - CMake

:: Record the directory we are in. Script should be invoked from the root of the repository.
SET REPO_ROOT=%cd%

:: Make sure we have a clean directory to build things in.
SET BUILD_DIR=cmake_build
RMDIR %BUILD_DIR% /S /Q
MKDIR %BUILD_DIR%


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: Install external dependencies
:: TODO: remove this after we moved to Windows docker container

IF DEFINED TF_BUILD_PYTHON_VERSION (ECHO TF_BUILD_PYTHON_VERSION is set to %TF_BUILD_PYTHON_VERSION%) ELSE (SET TF_BUILD_PYTHON_VERSION="Python3.5")
SET PYTHON_VERSION_NUMBER=%TF_BUILD_PYTHON_VERSION:python=%
SET PYTHON_VERSION_NUMBER_NO_DOT=%PYTHON_VERSION_NUMBER:.=%

%BUILD_BINARIESDIRECTORY%\packages\drop.app.16.127.27318-rc4951956\lib\net45\drop get -d %BUILD_BINARIESDIRECTORY%\packages\miniconda --recurse infinite -n miniconda3/4.3.21 -s https://aiinfra.artifacts.visualstudio.com/DefaultCollection --patAuth %SYSTEM_ACCESSTOKEN%
if %errorlevel% neq 0 exit /b %errorlevel%

cmd /c start /wait %BUILD_BINARIESDIRECTORY%\packages\miniconda\Miniconda3-4.3.21-Windows-x86_64.exe /S /NoRegistry=1 /AddToPath=0 /RegisterPython=0 /D=%BUILD_BINARIESDIRECTORY%\packages\python
if %errorlevel% neq 0 exit /b %errorlevel%

%BUILD_BINARIESDIRECTORY%\packages\python\scripts\conda install -q -y python=%PYTHON_VERSION_NUMBER%
if %errorlevel% neq 0 exit /b %errorlevel%



SET CMAKE_EXE="%BUILD_BINARIESDIRECTORY%\packages\cmake.x64.3.10.0\bin\cmake.exe"
SET CTEST_EXE="%BUILD_BINARIESDIRECTORY%\packages\cmake.x64.3.10.0\bin\ctest.exe"
SET SWIG_EXE="%BUILD_BINARIESDIRECTORY%\packages\swigwin.3.0.9\tools\swigwin-3.0.9\swig.exe"
SET PY_EXE="%BUILD_BINARIESDIRECTORY%\packages\python\python.exe"
SET PY_LIB="%BUILD_BINARIESDIRECTORY%\packages\python\libs\python%PYTHON_VERSION_NUMBER_NO_DOT%.lib"
SET PIP_EXE="%BUILD_BINARIESDIRECTORY%\packages\python\Scripts\pip.exe"
SET PATH=%BUILD_BINARIESDIRECTORY%\packages\python;%BUILD_BINARIESDIRECTORY%\packages\python\scripts;%PATH%


:: numpy and protobuf are required by build
:: Use same version in tensorflow/tools/ci_build/install/install_python3.x_pip_packages.sh
%PIP_EXE% install numpy==1.12.0 protobuf==3.3.0
if %errorlevel% neq 0 exit /b %errorlevel%

:: Install absl-py.
%PIP_EXE% install --upgrade absl-py
if %errorlevel% neq 0 exit /b %errorlevel%

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::



:: Set which tests to build
IF DEFINED BUILD_CC_TESTS (ECHO BUILD_CC_TESTS is set to %BUILD_CC_TESTS%) ELSE (SET BUILD_CC_TESTS=OFF)
IF DEFINED BUILD_PYTHON_TESTS (ECHO BUILD_PYTHON_TESTS is set to %BUILD_PYTHON_TESTS%) ELSE (SET BUILD_PYTHON_TESTS=ON)

:: Set if this build is a nightly
IF DEFINED TF_NIGHTLY (ECHO TF_NIGHTLY is set to %TF_NIGHTLY%) ELSE (SET TF_NIGHTLY=OFF)

:: Set pip binary location. Do not override if it is set already.
IF DEFINED PIP_EXE (ECHO PIP_EXE is set to %PIP_EXE%) ELSE (SET PIP_EXE="C:\Program Files\Anaconda3\Scripts\pip.exe")

:: Set ctest binary location.
IF DEFINED CTEST_EXE (ECHO CTEST_EXE is set to %CTEST_EXE%) ELSE (SET CTEST_EXE="C:\Program Files\cmake\bin\ctest.exe")

IF DEFINED NUMBER_OF_PROCESSORS (ECHO NUMBER_OF_PROCESSORS is set to %NUMBER_OF_PROCESSORS%) ELSE (SET NUMBER_OF_PROCESSORS="32")



:: Create nuget package
%PY_EXE% %REPO_ROOT%\tensorflow\tools\ci_build\windows\nuget\collect_components_license.py
