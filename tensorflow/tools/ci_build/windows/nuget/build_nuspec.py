from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import argparse
import os
import sys
import shutil


def copy_file(src, dest):

  if not os.path.exists(src):
      sys.exit(-1)
  
  dir_name = os.path.dirname(dest)
  create_directory(dir_name)
  shutil.copyfile(src, dest)


def create_directory(path):
  if not os.path.isdir(path):
    os.makedirs(path, exist_ok=True)  # pylint: disable=unexpected-keyword-arg


def delete_directory(path):
  if os.path.isdir(path):
    shutil.rmtree(path)


def recreate_directory(path):
  delete_directory(path)
  create_directory(path)


def get_environment_variable(key, default=None):
  return os.environ.get(key, default)


def get_argument(value, default=None):
  if value:
    return value
  return default


def read_all_text(path):
  with open(path, "r") as fs:
    return fs.read()


parser = argparse.ArgumentParser()
parser.add_argument("--repo-root")
parser.add_argument("--build-root")
parser.add_argument("--package-dir")
parser.add_argument("--build-id")
parser.add_argument("--enable-gpu", default=False, action="store_true")
parser.add_argument("--include-pdb", nargs='?', const="all")

(args, unknown) = parser.parse_known_args()
repo_root = args.repo_root
build_root = args.build_root
package_dir = args.package_dir
build_id = args.build_id
enable_gpu = args.enable_gpu
include_pdb = args.include_pdb

current_dir = os.path.dirname(os.path.abspath(__file__))
build_types = ["release"]
is_vsts = "BUILD_BUILDID" in os.environ

if is_vsts:
  repo_root = get_argument(repo_root, os.environ["BUILD_REPOSITORY_LOCALPATH"])
  package_dir = get_argument(package_dir,
                             os.environ["BUILD_ARTIFACTSTAGINGDIRECTORY"])
  build_id = get_argument(build_id, os.environ["BUILD_BUILDID"])
  include_pdb = get_argument(include_pdb, os.environ.get("NUGET_INCLUDE_PDB"))

if not repo_root or not os.path.isdir(repo_root):
  raise RuntimeError("Invalid repo root: {}".format(repo_root))

build_root = get_argument(build_root, os.path.join(repo_root, "cmake_build"))
if not build_root or not os.path.isdir(build_root):
  raise RuntimeError("Invalid build root: {}".format(build_root))

package_dir = get_argument(package_dir, os.path.join(build_root, "nuget"))
include_pdb = get_argument(include_pdb, "").lower()
print("include_pdb={0}".format(include_pdb))

recreate_directory(package_dir)

nuspec_template = read_all_text(os.path.join(current_dir, "nuspec.template"))
targets_template = read_all_text(os.path.join(current_dir, "targets.template"))

package_name = "tensorflow" if not enable_gpu else "tensorflow-gpu"
target_file_name = "{}.targets".format(package_name)
print("package_name={0}".format(package_name))

tf_version = None
pip_setup_py_path = os.path.join(repo_root,
                                 r"tensorflow\tools\pip_package\setup.py")
with open(pip_setup_py_path, "r") as f:
  for line in f:
    if line.startswith("_VERSION"):
      tf_version = line.split('=')[-1].strip().strip("'")
      break

if not tf_version:
  raise RuntimeError("Failed to parse tf_version")
print("tf_version={0}".format(tf_version))

package_version = tf_version
if build_id:
  package_version += ("." + build_id)
print("package_version={0}".format(package_version))

release_notes = ""
if is_vsts:
  base_url = ""
  release_notes = r"""
    Branch: {branch}
    Commit: {source_version}
    Build: https://aiinfra.visualstudio.com/tensorflow/_build/index?buildId={build_id}""" \
    .format(branch=os.environ["BUILD_SOURCEBRANCH"].replace("refs/heads/", ""),
            source_version=os.environ["BUILD_SOURCEVERSION"],
            build_id=build_id)

package_files = []
additional_include_directories = ["$(MSBuildThisFileDirectory)include"]
additional_dependencies = dict()
after_build_copy_files = dict()


def add_package_file(src, target):
  package_files.append \
    ('<file src="{src}" target="{target}"/>'.format(src=src, target=target))


package_build_native_dir = r"build\native"
add_package_file(target_file_name, package_build_native_dir)

tf_shared_lib_cmake_path = \
  os.path.join(repo_root, r"tensorflow\contrib\cmake\tf_shared_lib.cmake")
print("Parse {}".format(tf_shared_lib_cmake_path))

matches = re.findall \
  ("install\(DIRECTORY +(\S+)\s+DESTINATION "
   "+(\S+)(?:\s+FILES_MATCHING +PATTERN +(\S+))?\)",
   read_all_text(tf_shared_lib_cmake_path)
   , re.MULTILINE | re.I)
print("Found {} install DIRECTORY commands".format(len(matches)))

for match in matches:
  src_dir = match[0].lower().replace('/', '\\')
  dest_dir = match[1].replace('/', '\\')
  pattern = match[2].strip('"')

  src_dir = src_dir.replace("${tensorflow_source_dir}", repo_root) \
    .replace("${CMAKE_CURRENT_BINARY_DIR}".lower(),
             os.path.join(build_root, "release"))
  if not pattern:
    src_dir = os.path.join(src_dir, "**", "*")
  else:
    src_dir = os.path.join(src_dir, "**", pattern)
  add_package_file(src_dir, os.path.join(package_build_native_dir, dest_dir))

matches = re.findall \
  ("\s*(\$<INSTALL_INTERFACE:(\S+)>)+",
   read_all_text(tf_shared_lib_cmake_path)
   , re.MULTILINE | re.I)
print("Found {} target_include_directories".format(len(matches)))

for match in matches:
  dest_dir = match[1].strip().strip('/').replace('/', '\\')
  include_dir = "$(MSBuildThisFileDirectory)" + dest_dir
  if not include_dir in additional_include_directories:
    additional_include_directories.append(include_dir)

for build_type in build_types:
  build_dir = os.path.join(build_root, build_type, build_type)
  package_lib_dir = os.path.join(r"lib\native", build_type)
  local_lib_dir = os.path.join(package_dir, package_lib_dir)

  additional_dependencies[build_type] = []
  after_build_copy_files[build_type] = []

  files = ["tensorflow.dll", "tensorflow.lib"]

  pdb_file = "tensorflow.pdb"
  if include_pdb == "all" or include_pdb == build_type.lower():
    files.append(pdb_file)
  elif include_pdb == "optional":
    if os.path.isfile(os.path.join(build_dir, pdb_file)):
      files.append(pdb_file)

  for file_name in files:
    raw_src = os.path.join(build_dir, file_name)
    if not os.path.isfile(raw_src):
      raise RuntimeError("{} is missing".format(raw_src))

    src = os.path.join(local_lib_dir, file_name)
    copy_file(raw_src, src)
    target = os.path.join(package_lib_dir, file_name)
    add_package_file(src, target)

    extension = os.path.splitext(file_name)[-1].lower()
    if extension == ".lib":
      additional_dependencies[build_type] \
        .append("$(MSBuildThisFileDirectory)..\\..\\" + target)
    elif extension in [".dll", ".pdb"]:
      after_build_copy_files[build_type] \
        .append(r"$(MSBuildThisFileDirectory)..\..\lib\native\{}\{}"
                .format(build_type, file_name))

##package components' license into package, so add releated contents into nuspec description file
##all needed components' license is put in BUILD_ARTIFACTSTAGINGDIRECTORY
license_dir = os.path.join(os.environ["BUILD_ARTIFACTSTAGINGDIRECTORY"], "license")
add_package_file(src=license_dir+r"\**\*", target="third_party_license")
print("xzj debug")
print(package_files)
nuspec = nuspec_template.format(id=package_name,
                                version=package_version,
                                release_notes=release_notes,
                                files="\r    ".join(package_files))

nuspec_path = os.path.join(package_dir, "tensorflow.nuspec")
with open(nuspec_path, "w") as f:
  f.write(nuspec)

targets = targets_template.format \
  (additional_include_directories=";".join(additional_include_directories),
   additional_dependencies_debug=";".join(additional_dependencies["debug"]),
   additional_dependencies_release=";".join(additional_dependencies["release"]),
   after_build_copy_files_debug=";".join(after_build_copy_files["debug"]),
   after_build_copy_files_release=";".join(after_build_copy_files["release"]))

targets_path = os.path.join(package_dir, target_file_name)
with open(targets_path, "w") as f:
  f.write(targets)
