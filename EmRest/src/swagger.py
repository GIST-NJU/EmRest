import json
from urllib.parse import urlparse, urlunparse

import prance
from logging import getLogger
from openapi_parser.parser import _create_parser
from openapi_parser.specification import *

from src.factor import *
from src.rest import *

_logger = getLogger(__name__)

def recursion_limit_handler(limit, parsed_url, recursions=()):
    """https://github.com/RonnyPfannschmidt/prance/blob/main/COMPATIBILITY.rst"""
    return None


class ParserV3:
    def __init__(self, swagger_path, server=None):
        # Set up prance to solve the problem of loop call
        _resolver = prance.ResolvingParser(url=swagger_path,
                                           strict=False,
                                           lazy=True,
                                           recursion_limit_handler=recursion_limit_handler)
        try:
            _logger.debug(f"Resolving specification file")
            _resolver.parse()
            specification = _resolver.specification
        except prance.ValidationError as error:
            raise ValueError(f"OpenAPI validation error: {error}")
        except Exception as error:
            raise ValueError(f"OpenAPI file parsing error: {error}")

        _parser = _create_parser(strict_enum=True)

        # parse swagger specification
        self._swagger: Specification = _parser.load_specification(specification)

        # There may be multiple servers, but only one is stored
        self._server: str = self._get_server(server)

    def _get_server(self, specified):
        """
        get bash path of url
        """
        server = self._swagger.servers[0]
        parsed = urlparse(server.url)
        if parsed.scheme == 0 or parsed.netloc == 0:
            raise ValueError(f"Invalid URI {server.url}: Scheme and netloc are required.")
        if specified is not None:
            specified = urlparse(specified)
            return urlunparse(
                (specified.scheme, specified.netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
        return parsed.geturl()

    def extract(self):
        operations = []
        for path in self._swagger.paths:
            path_parameters = path.parameters

            for operation in path.operations:
                rest_op = RestOp(self._server, path.url, operation.method.name)

                if operation.description is not None and len(operation.description):
                    rest_op.description = operation.description

                # handle with input parameters
                for param in operation.parameters:
                    rest_param = self._extract_param(param)
                    rest_op.parameters.append(rest_param)

                if len(path_parameters) > 0:
                    for param in path_parameters:
                        rest_param = self._extract_param(param)
                        rest_op.parameters.append(rest_param)

                # handle request body
                if operation.request_body is not None:
                    if not len(operation.request_body.content) == 0:
                        rest_op.parameters.append(self._extract_body_param(operation.request_body))

                for r in operation.responses:
                    if r.code is None:
                        continue
                    response = RestResponse(r.code, r.description)
                    if r.content is not None:
                        for c in r.content:
                            content_type = c.type
                            content = ParserV3._extract_factor("response", c.schema)
                            response.add_content(content, content_type.name)
                    rest_op.responses.append(response)

                uri_parts = path.url.strip('/').split('/')
                for f in rest_op.get_leaf_factors():
                    f.extract_meaningful_tokens(uri_parts)

                operations.append(rest_op)
        return operations

    @staticmethod
    def _extract_body_param(body: RequestBody):
        content = body.content
        if len(content) == 0:
            raise ValueError("no content is provided")

        content = content[0]

        factor: AbstractFactor = ParserV3._extract_factor("body", content.schema)
        if body.description is not None and len(body.description) != 0:
            factor.set_description(body.description)

        return BodyParam(factor, content.type.value)

    @staticmethod
    def _extract_param(param: Parameter):
        """
        extract factor from swagger
        """
        # factor info: AbstractFactor
        factor: AbstractFactor = ParserV3._extract_factor(param.name, param.schema)
        factor.required = param.required
        if param.location is ParameterLocation.QUERY:
            rest_param = QueryParam(factor)
        elif param.location is ParameterLocation.HEADER:
            rest_param = HeaderParam(factor)
        elif param.location is ParameterLocation.PATH:
            rest_param = PathParam(factor)
        else:
            raise ValueError(f"Unsupported factor location: {param.location}")
        return rest_param

    @staticmethod
    def _extract_factor(name: str, schema: Schema):
        if isinstance(schema, Null):
            raise ValueError(f"Parameter {name} has no schema")
        if len(schema.enum) > 0:
            factor = EnumFactor(name, schema.enum)
        elif isinstance(schema, Boolean):
            factor = BoolFactor(name)
        elif isinstance(schema, Integer):
            factor = ParserV3._build_integer_factor(name, schema)
        elif isinstance(schema, Number):
            factor = ParserV3._build_number_factor(name, schema)
        elif isinstance(schema, String):
            factor = ParserV3._build_string_factor(name, schema)
        elif isinstance(schema, Array):
            factor = ParserV3._build_array_factor(name, schema)
        elif isinstance(schema, Object):
            factor = ParserV3._build_object_factor(name, schema)
        elif isinstance(schema, (AnyOf, OneOf)):
            _schema = next(filter(lambda x: x.type is DataType.OBJECT, schema.schemas), None)
            if _schema is None:
                _schema = next(filter(lambda x: x.type is DataType.ARRAY, schema.schemas), None)
            if _schema is None:
                _schema = schema.schemas[0]
            factor = ParserV3._extract_factor(name, _schema)
        else:
            raise ValueError(f"{name} -> Unsupported schema: {schema}")

        if not isinstance(factor, (ObjectFactor, ArrayFactor)):
            if schema.example is not None:
                factor.set_example(schema.example)
            if schema.default is not None:
                factor.set_default(schema.default)
        if schema.description is not None:
            factor.set_description(schema.description)

        return factor

    @staticmethod
    def _build_object_factor(name: str, schema: Object):
        # todo: currently do not handle with anyOf and oneOf
        # todo: have never seen max_properties and min_properties, so I will not deal with them for now.
        object_factor = ObjectFactor(name)

        if len(schema.required) == 0:
            schema.required = [_.name for _ in schema.properties]

        for p in schema.properties:
            p_factor = ParserV3._extract_factor(p.name, p.schema)
            if p_factor.name not in schema.required:
                p_factor.required = False
            object_factor.add_property(p_factor)

        # object_factor.ref_name = get_ref_name(object_factor)

        return object_factor

    @staticmethod
    def _build_array_factor(name: str, schema: Array):
        min_items = schema.min_items if schema.min_items is not None else 1
        array = ArrayFactor(name)
        if schema.items is None:
            raise ValueError(f"Parameter {name} has no items")
        item_factor = ParserV3._extract_factor("_item", schema.items)
        array.set_item(item_factor)
        return array

    @staticmethod
    def _build_string_factor(name: str, schema: String):
        if schema.pattern is not None:
            return RegexFactor(name, schema.pattern)
        if schema.format is not None:
            if schema.format is StringFormat.DATE:
                return ParserV3._build_date_factor(name, schema)
            if schema.format is StringFormat.DATETIME:
                return ParserV3._build_datetime_factor(name, schema)
            if schema.format is StringFormat.BINARY:
                return ParserV3._build_binary_factor(name, schema)
            # todo: build factor based on format
            raise ValueError(f"Format {schema.format} is not supported")

        if "date" in name.lower() and "time" in name.lower():
            return DateTimeFactor(name)
        if "date" in name.lower():
            return DateFactor(name)
        if "time" in name.lower():
            return TimeFactor(name)

        return StringFactor(name,
                            min_length=schema.min_length if schema.min_length is not None else 1,
                            max_length=schema.max_length if schema.max_length is not None else 100)

    @staticmethod
    def _build_date_factor(name, schema: String):
        if schema.format is None or schema.format is not StringFormat.DATE:
            raise ValueError(f"Format {schema.format} is not date")

        return DateFactor(name)

    @staticmethod
    def _build_datetime_factor(name, schema: String):
        if schema.format is None or schema.format is not StringFormat.DATETIME:
            raise ValueError(f"Format {schema.format} is not datetime")

        return DateTimeFactor(name)

    @staticmethod
    def _build_binary_factor(name, schema: String):
        if schema.format is None or schema.format is not StringFormat.BINARY:
            raise ValueError("fFormat {schema.format} is not binary")

        return BinaryFactor(name, 1, 100)

    @staticmethod
    def _build_integer_factor(name: str, schema: Integer):
        factor = IntFactor(
            name=name,
            min_value=schema.minimum if schema.minimum is not None else -1000,
            max_value=schema.maximum if schema.maximum is not None else 1000,
        )

        # if schema.multiple_of is not None:
        #     factor.set_multiple_of(schema.multiple_of)
        return factor

    @staticmethod
    def _build_number_factor(name: str, schema: Number):
        factor = FloatFactor(
            name=name,
            min_value=schema.minimum if schema.minimum is not None else -1000,
            max_value=schema.maximum if schema.maximum is not None else 1000,
        )

        # if schema.multiple_of is not None:
        #     factor.set_multiple_of(schema.multiple_of)
        return factor


if __name__ == '__main__':
    data = {}
    # Query the total number and average number of input parameters
    spec_folder = "./specs"
    for spec in os.listdir(spec_folder):
        spec_path = os.path.join(spec_folder, spec)
        spec_name = os.path.split(spec)[-1].split(".")[0]
        try:
            parser = ParserV3(spec_path)
        except Exception as e:
            continue
        operations = parser.extract()
        data[spec_name] = {}
        for op in operations:
            print(f"{spec_name}:{op.id} {len([f for f in op.get_leaf_factors() if f.required])}")
            data[spec_name][op.id] = len(op.get_leaf_factors())
    json.dump(data, open("numberOfParamPerOp.json", "w"), indent=4)
