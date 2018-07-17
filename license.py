#!/usr/bin/python
import os, sys
import shutil



def find_and_copy_file(dst_path, src_path, file_name):
    
    found = False
    
    for dir_path, dirs, files in os.walk(src_path):
        for file_obj in files:
            if file_obj.upper().startswith(file_name) and not file_obj.endswith(".py"):
                shutil.copyfile(os.path.join(dir_path, file_obj), os.path.join(dst_path, file_obj))
                found = True
                
    return found
    
    
    
########get used components list
required_components_list = [  
                              "zlib", "gif", "png", "jpeg", "eigen", "gemmlowp", "jsoncpp", "farmhash", "fft2d", 
                              "highwayhash", "nsync", "protobuf", "re2", "cub"
                           ] #lmdb is disabled for OACR warning, so not included here
                             #double_conversion, sqlite are processed specially
                             

optional_components_list = []
#add optional components according to build configuration
options_list = [
                    "BUILD_CC_TESTS", "ENABLE_SSL_SUPPORT", "ENABLE_GRPC_SUPPORT", "ENABLE_JEMALLOC_SUPPORT", 
                    "ENABLE_SNAPPY_SUPPORT", "ENABLE_MKL_SUPPORT", "ENABLE_MKLDNN_SUPPORT"
               ]
optional_components_name = [
                                "googletest", "boringssl", "grpc", "jemalloc", 
                                "snappy", "mkl", "mkldnn"
                           ]
for index, option in enumerate(options_list):
    if os.environ.get(option) == "ON":
        optional_components_list.append(optional_components_name[index])
        
used_components_list = [*required_components_list, *optional_components_list]

########copy components license files
path_prefix = os.path.join(os.environ.get("BUILD_SOURCESDIRECTORY"),r"cmake_build\debug")
for component_name in used_components_list:

    dst_path = os.path.join(os.environ.get("BUILD_ARTIFACTSTAGINGDIRECTORY"), "license", component_name,)
    os.makedirs(dst_path, exist_ok=True)
    src_path = os.path.join(path_prefix, component_name)
    
    ##name of license file may be "license", "copyxx" or in "readme"
    if not find_and_copy_file(dst_path, src_path, "LICENSE"):
        if not find_and_copy_file(dst_path, src_path, "COPYING"):
            if not find_and_copy_file(dst_path, src_path, "README"):
                print("not found " + component_name + "'s license file")

########copy "tensorflow" license
shutil.copyfile(os.path.join(os.environ.get("BUILD_SOURCESDIRECTORY"), "LICENSE"), os.path.join(os.environ.get("BUILD_ARTIFACTSTAGINGDIRECTORY"), "tensorflow"))
########process components whose license file can not be found at cmake_build
special_components = ["double_conversion", "sqlite"]
for component in special_components:
    dst_dir = os.path.join(os.environ.get("BUILD_ARTIFACTSTAGINGDIRECTORY"), "license", component)
    os.mkdir(dst_dir)
    shutil.copyfile(os.path.join(os.environ.get("BUILD_SOURCESDIRECTORY"), "manual_collected_license", component+".txt"), os.path.join(dst_dir, "LICENSE"))

