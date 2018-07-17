from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys

for project in sys.argv[1:]:
  print("Process {}".format(project))
  with open(project, "r") as f:
    content = f.read()

  content = content \
    .replace \
    ("<DebugInformationFormat>ProgramDatabase</DebugInformationFormat>",
     "<DebugInformationFormat></DebugInformationFormat>")

  with open(project, "w") as f:
    f.write(content)
