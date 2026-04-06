import os
import subprocess
import sys

# subprocess.check_call([sys.executable, "-m", "pip", "install", "mujoco"])

import mujoco
from mujoco import viewer


model = mujoco.load_model_from_path("C:/Users/Lance/Documents/GitHub/ar4/ar4_mujoco_sim/package.xml")

viewer.launch()