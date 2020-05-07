try:
    from .silvius_config import *
    print("Loaded config from local silvius_config.py")
except:
    print("Using default config, create silvius_config.py locally to override")
    from .default_silvius_config import *
