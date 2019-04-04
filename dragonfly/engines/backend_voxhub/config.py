try:
    from voxhub_config import *
    print("Loaded config from local voxhub_config.py")
except:
    print("Using default config, create voxhub_config.py locally to override")
    from default_voxhub_config import *
