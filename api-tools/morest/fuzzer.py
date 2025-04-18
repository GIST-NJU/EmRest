import os
import sys

from prance import ResolvingParser

from build_graph import parse
from fuzzer.fuzzer import APIFuzzer
from utils.auth_util import get_token, SUT


def default_reclimit_handler(limit, parsed_url, recursions=()):
    """Raise prance.util.url.ResolutionError."""
    return {
        "type": "object",
        "name": "Recursive Dependency",
        "properties": {}
    }


def main():
    # testing arguments format: swagger address, server address, system under test's name, *args to obtain token
    test_args = [sys.argv[1], sys.argv[2], sys.argv[3]]
    if len(sys.argv) > 4:
        token = sys.argv[4]
    else:
        token = None
    parser = ResolvingParser(test_args[0],
                             recursion_limit_handler=default_reclimit_handler, backend='openapi-spec-validator', strict=False)
    apis, odg = parse(parser.specification)
    if test_args[1][-1] == '/':
        test_args[1] = test_args[1][:-1]
    odg.draw()
    if token is not None:
        pre_defined_headers = {"Authorization": f"Bearer {token}"}
    else:
        pre_defined_headers = {}
    # return
    # headers = get_token(SUT.SPREE, "http://192.168.74.135:3000")
    # api_fuzzer = APIFuzzer(apis, parser.specification, odg, 'https://demo.traccar.org/api/')
    # api_fuzzer = APIFuzzer(apis, parser.specification, odg, 'http://192.168.74.135:3000', pre_defined_headers=headers)
    # token = get_token(*test_args[2:])
    api_fuzzer = APIFuzzer(apis, parser.specification, odg, test_args[1], pre_defined_headers=pre_defined_headers,time_budget=int(sys.argv[3]))
    api_fuzzer.run()



if __name__ == '__main__':
    main()
