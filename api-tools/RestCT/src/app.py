if __name__ == "__main__":
    import sys
    import os

    cur_path = os.path.abspath(os.path.dirname(__file__))
    root_path = os.path.split(cur_path)[0]
    sys.path.append(root_path)
    
    from src.config import *
    from src.algorithms import RestCT

    

    # parse the arguments
    args = parse_args(root_path)

    # check the configuration
    config = Config()
    config.check(args)

    # run the algorithm
    restCT = RestCT(config)
    restCT.run()
