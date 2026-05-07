# -*- coding: utf-8 -*-
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for google.generativeai.responder module."""

from typing import Any, Optional, Union

from absl.testing import absltest
from absl.testing import parameterized

from google.generativeai import protos
from google.generativeai import responder


# ---------------------------------------------------------------------------
# Helper functions used across tests
# ---------------------------------------------------------------------------

def _simple_fn(a: int, b: str) -> str:
    """A simple test function."""
    return f"{a} {b}"


def _no_args_fn():
    """A function with no arguments."""
    pass


def _optional_fn(a: int, b: Optional[str] = None) -> str:
    """A function with an optional argument."""
    return str(a)


def _list_fn(items: list[int]) -> list[int]:
    """A function returning a list."""
    return items


def _dict_fn(data: dict) -> dict:
    """A function with a dict argument."""
    return data


# ---------------------------------------------------------------------------
# to_type
# ---------------------------------------------------------------------------

class ToTypeTests(parameterized.TestCase):

    @parameterized.named_parameters(
        ["string_str", "string", protos.Type.STRING],
        ["string_int", 1, protos.Type.STRING],
        ["number_str", "number", protos.Type.NUMBER],
        ["number_int", 2, protos.Type.NUMBER],
        ["integer_str", "integer", protos.Type.INTEGER],
        ["integer_int", 3, protos.Type.INTEGER],
        ["boolean_str", "boolean", protos.Type.BOOLEAN],
        ["array_str", "array", protos.Type.ARRAY],
        ["array_int", 5, protos.Type.ARRAY],
        ["object_str", "object", protos.Type.OBJECT],
        ["object_int", 6, protos.Type.OBJECT],
        ["unspecified_str", "unspecified", protos.Type.TYPE_UNSPECIFIED],
        ["unspecified_int", 0, protos.Type.TYPE_UNSPECIFIED],
    )
    def test_to_type(self, x, expected):
        result = responder.to_type(x)
        self.assertEqual(result, expected)

    def test_to_type_enum(self):
        result = responder.to_type(protos.Type.STRING)
        self.assertEqual(result, protos.Type.STRING)


# ---------------------------------------------------------------------------
# _generate_schema
# ---------------------------------------------------------------------------

class GenerateSchemaTests(parameterized.TestCase):

    def test_simple_function(self):
        schema = responder._generate_schema(_simple_fn)
        self.assertEqual(schema["name"], "_simple_fn")
        self.assertIn("parameters", schema)
        params = schema["parameters"]
        self.assertIn("a", params["properties"])
        self.assertIn("b", params["properties"])

    def test_no_args_function(self):
        schema = responder._generate_schema(_no_args_fn)
        self.assertEqual(schema["name"], "_no_args_fn")
        # no parameters key when there are no properties
        self.assertNotIn("parameters", schema)

    def test_required_fields_inferred(self):
        schema = responder._generate_schema(_simple_fn)
        self.assertIn("required", schema["parameters"])
        self.assertIn("a", schema["parameters"]["required"])
        self.assertIn("b", schema["parameters"]["required"])

    def test_required_fields_override(self):
        schema = responder._generate_schema(_simple_fn, required=["a"])
        self.assertEqual(schema["parameters"]["required"], ["a"])

    def test_descriptions_provided(self):
        schema = responder._generate_schema(
            _simple_fn, descriptions={"a": "the integer", "b": "the string"}
        )
        # descriptions become part of schema generation; just check it works
        self.assertIn("parameters", schema)

    def test_list_type(self):
        schema = responder._generate_schema(_list_fn)
        self.assertIn("parameters", schema)

    def test_dict_type(self):
        schema = responder._generate_schema(_dict_fn)
        self.assertIn("parameters", schema)


# ---------------------------------------------------------------------------
# _build_schema
# ---------------------------------------------------------------------------

class BuildSchemaTests(absltest.TestCase):

    def test_simple(self):
        fields = {"x": (int, ...)}
        result = responder._build_schema("test", fields)
        self.assertIn("properties", result)
        self.assertIn("x", result["properties"])

    def test_nullable_field(self):
        import pydantic

        fields = {"x": (Optional[int], pydantic.Field())}
        result = responder._build_schema("test", fields)
        # nullable optional should survive processing
        self.assertIn("properties", result)


# ---------------------------------------------------------------------------
# unpack_defs
# ---------------------------------------------------------------------------

class UnpackDefsTests(absltest.TestCase):

    def test_no_properties(self):
        schema = {"type": "string"}
        # Should not raise
        responder.unpack_defs(schema, {})

    def test_with_ref(self):
        defs = {
            "MyType": {"type": "object", "properties": {"a": {"type": "integer"}}}
        }
        schema = {"properties": {"x": {"$ref": "#/$defs/MyType"}}}
        responder.unpack_defs(schema, defs)
        self.assertEqual(schema["properties"]["x"]["type"], "object")

    def test_with_anyof_ref(self):
        defs = {"MyType": {"type": "object", "properties": {}}}
        schema = {
            "properties": {
                "x": {"anyOf": [{"$ref": "#/$defs/MyType"}, {"type": "null"}]}
            }
        }
        responder.unpack_defs(schema, defs)
        # Should not raise; anyOf refs are replaced with actual schema

    def test_with_items_ref(self):
        defs = {"MyType": {"type": "object", "properties": {"a": {"type": "integer"}}}}
        schema = {"properties": {"x": {"items": {"$ref": "#/$defs/MyType"}}}}
        responder.unpack_defs(schema, defs)
        self.assertEqual(schema["properties"]["x"]["items"]["type"], "object")


# ---------------------------------------------------------------------------
# strip_titles
# ---------------------------------------------------------------------------

class StripTitlesTests(absltest.TestCase):

    def test_removes_top_level_title(self):
        schema = {"title": "MyModel", "type": "object", "properties": {}}
        responder.strip_titles(schema)
        self.assertNotIn("title", schema)

    def test_removes_nested_title(self):
        schema = {
            "properties": {
                "a": {"title": "A", "type": "integer"}
            }
        }
        responder.strip_titles(schema)
        self.assertNotIn("title", schema["properties"]["a"])

    def test_removes_items_title(self):
        schema = {"items": {"title": "Item", "type": "string"}}
        responder.strip_titles(schema)
        self.assertNotIn("title", schema["items"])


# ---------------------------------------------------------------------------
# strip_additional_properties
# ---------------------------------------------------------------------------

class StripAdditionalPropertiesTests(absltest.TestCase):

    def test_removes_top_level(self):
        schema = {"type": "object", "additionalProperties": False}
        responder.strip_additional_properties(schema)
        self.assertNotIn("additionalProperties", schema)

    def test_removes_nested(self):
        schema = {
            "properties": {
                "a": {"type": "object", "additionalProperties": False}
            }
        }
        responder.strip_additional_properties(schema)
        self.assertNotIn("additionalProperties", schema["properties"]["a"])

    def test_removes_items(self):
        schema = {"items": {"type": "object", "additionalProperties": True}}
        responder.strip_additional_properties(schema)
        self.assertNotIn("additionalProperties", schema["items"])


# ---------------------------------------------------------------------------
# add_object_type
# ---------------------------------------------------------------------------

class AddObjectTypeTests(absltest.TestCase):

    def test_adds_object_type(self):
        schema = {"properties": {"a": {"type": "integer"}}}
        responder.add_object_type(schema)
        self.assertEqual(schema["type"], "object")

    def test_no_properties_no_change(self):
        schema = {"type": "string"}
        responder.add_object_type(schema)
        self.assertEqual(schema["type"], "string")

    def test_recurses_into_items(self):
        schema = {"items": {"properties": {"a": {"type": "integer"}}}}
        responder.add_object_type(schema)
        self.assertEqual(schema["items"]["type"], "object")


# ---------------------------------------------------------------------------
# convert_to_nullable
# ---------------------------------------------------------------------------

class ConvertToNullableTests(absltest.TestCase):

    def test_optional_null_first(self):
        schema = {"anyOf": [{"type": "null"}, {"type": "string"}]}
        responder.convert_to_nullable(schema)
        self.assertEqual(schema.get("type"), "string")
        self.assertTrue(schema.get("nullable"))

    def test_optional_null_second(self):
        schema = {"anyOf": [{"type": "integer"}, {"type": "null"}]}
        responder.convert_to_nullable(schema)
        self.assertEqual(schema.get("type"), "integer")
        self.assertTrue(schema.get("nullable"))

    def test_invalid_union_raises(self):
        schema = {"anyOf": [{"type": "string"}, {"type": "integer"}, {"type": "null"}]}
        with self.assertRaises(ValueError):
            responder.convert_to_nullable(schema)

    def test_invalid_non_null_union_raises(self):
        schema = {"anyOf": [{"type": "string"}, {"type": "integer"}]}
        with self.assertRaises(ValueError):
            responder.convert_to_nullable(schema)

    def test_recurses_into_properties(self):
        schema = {
            "properties": {
                "a": {"anyOf": [{"type": "integer"}, {"type": "null"}]}
            }
        }
        responder.convert_to_nullable(schema)
        self.assertTrue(schema["properties"]["a"].get("nullable"))

    def test_recurses_into_items(self):
        schema = {"items": {"anyOf": [{"type": "string"}, {"type": "null"}]}}
        responder.convert_to_nullable(schema)
        self.assertTrue(schema["items"].get("nullable"))


# ---------------------------------------------------------------------------
# _rename_schema_fields
# ---------------------------------------------------------------------------

class RenameSchemaFieldsTests(absltest.TestCase):

    def test_renames_type(self):
        schema = {"type": "string"}
        result = responder._rename_schema_fields(schema)
        self.assertIn("type_", result)
        self.assertNotIn("type", result)
        self.assertEqual(result["type_"], protos.Type.STRING)

    def test_renames_format(self):
        schema = {"format": "int32", "type": "integer"}
        result = responder._rename_schema_fields(schema)
        self.assertIn("format_", result)
        self.assertNotIn("format", result)

    def test_renames_items(self):
        schema = {"type": "array", "items": {"type": "string"}}
        result = responder._rename_schema_fields(schema)
        self.assertIn("items", result)
        self.assertIn("type_", result["items"])

    def test_renames_properties(self):
        schema = {"type": "object", "properties": {"a": {"type": "integer"}}}
        result = responder._rename_schema_fields(schema)
        self.assertIn("properties", result)
        self.assertIn("type_", result["properties"]["a"])

    def test_none_returns_none(self):
        result = responder._rename_schema_fields(None)
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# FunctionDeclaration
# ---------------------------------------------------------------------------

class FunctionDeclarationTests(absltest.TestCase):

    def test_basic_creation(self):
        fd = responder.FunctionDeclaration(
            name="my_func",
            description="A test function",
            parameters={
                "type": "object",
                "properties": {"x": {"type": "integer"}},
            },
        )
        self.assertEqual(fd.name, "my_func")
        self.assertEqual(fd.description, "A test function")
        self.assertIsInstance(fd.parameters, protos.Schema)

    def test_no_parameters(self):
        fd = responder.FunctionDeclaration(
            name="my_func",
            description="A test function",
        )
        self.assertEqual(fd.name, "my_func")

    def test_to_proto(self):
        fd = responder.FunctionDeclaration(
            name="add",
            description="Adds two numbers",
            parameters={
                "type": "object",
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"type": "integer"},
                },
            },
        )
        proto = fd.to_proto()
        self.assertIsInstance(proto, protos.FunctionDeclaration)
        self.assertEqual(proto.name, "add")

    def test_from_proto(self):
        proto = protos.FunctionDeclaration(name="greet", description="Greets user")
        fd = responder.FunctionDeclaration.from_proto(proto)
        self.assertIsInstance(fd, responder.FunctionDeclaration)
        self.assertEqual(fd.name, "greet")

    def test_from_function(self):
        def add(a: int, b: int) -> int:
            """Adds two integers."""
            return a + b

        fd = responder.FunctionDeclaration.from_function(add)
        self.assertIsInstance(fd, responder.CallableFunctionDeclaration)
        self.assertEqual(fd.name, "add")
        self.assertEqual(fd.description, "Adds two integers.")

    def test_from_function_with_descriptions(self):
        def multiply(a: int, b: int) -> int:
            """Multiplies two integers."""
            return a * b

        fd = responder.FunctionDeclaration.from_function(
            multiply, descriptions={"a": "first operand", "b": "second operand"}
        )
        self.assertEqual(fd.name, "multiply")


# ---------------------------------------------------------------------------
# CallableFunctionDeclaration
# ---------------------------------------------------------------------------

class CallableFunctionDeclarationTests(absltest.TestCase):

    def test_call_returns_function_response(self):
        def add(a: int, b: int) -> int:
            """Adds two integers."""
            return a + b

        cfd = responder.CallableFunctionDeclaration.from_function(add)
        fc = protos.FunctionCall(name="add", args={"a": 3, "b": 5})
        result = cfd(fc)
        self.assertIsInstance(result, protos.FunctionResponse)
        self.assertEqual(result.response["result"], 8)

    def test_call_dict_result(self):
        def info(name: str) -> dict:
            """Returns info about name."""
            return {"name": name, "length": len(name)}

        cfd = responder.CallableFunctionDeclaration.from_function(info)
        fc = protos.FunctionCall(name="info", args={"name": "hello"})
        result = cfd(fc)
        self.assertEqual(result.response["name"], "hello")
        self.assertEqual(result.response["length"], 5)


# ---------------------------------------------------------------------------
# _make_function_declaration
# ---------------------------------------------------------------------------

class MakeFunctionDeclarationTests(absltest.TestCase):

    def test_from_function_declaration(self):
        fd = responder.FunctionDeclaration(name="f", description="d")
        result = responder._make_function_declaration(fd)
        self.assertIs(result, fd)

    def test_from_proto_function_declaration(self):
        proto = protos.FunctionDeclaration(name="f", description="d")
        result = responder._make_function_declaration(proto)
        self.assertIs(result, proto)

    def test_from_dict_with_function_key(self):
        def f(x: int) -> int:
            """A function."""
            return x

        d = {
            "name": "f",
            "description": "A function",
            "parameters": None,
            "function": f,
        }
        result = responder._make_function_declaration(d)
        self.assertIsInstance(result, responder.CallableFunctionDeclaration)

    def test_from_dict_without_function_key(self):
        d = {"name": "f", "description": "d"}
        result = responder._make_function_declaration(d)
        self.assertIsInstance(result, responder.FunctionDeclaration)

    def test_from_callable(self):
        def f(x: int) -> int:
            """A function."""
            return x

        result = responder._make_function_declaration(f)
        self.assertIsInstance(result, responder.CallableFunctionDeclaration)

    def test_invalid_type_raises(self):
        with self.assertRaises(TypeError):
            responder._make_function_declaration(42)


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------

class ToolTests(absltest.TestCase):

    def test_basic_tool(self):
        def f(x: int) -> int:
            """Doubles x."""
            return x * 2

        tool = responder.Tool(function_declarations=[f])
        self.assertLen(tool.function_declarations, 1)
        proto = tool.to_proto()
        self.assertIsInstance(proto, protos.Tool)

    def test_tool_getitem_by_name(self):
        def f(x: int) -> int:
            """Doubles x."""
            return x * 2

        tool = responder.Tool(function_declarations=[f])
        fd = tool["f"]
        self.assertEqual(fd.name, "f")

    def test_tool_getitem_by_function_call(self):
        def f(x: int) -> int:
            """Doubles x."""
            return x * 2

        tool = responder.Tool(function_declarations=[f])
        fc = protos.FunctionCall(name="f", args={"x": 3})
        fd = tool[fc]
        self.assertEqual(fd.name, "f")

    def test_tool_call_callable(self):
        def f(x: int) -> int:
            """Doubles x."""
            return x * 2

        tool = responder.Tool(function_declarations=[f])
        fc = protos.FunctionCall(name="f", args={"x": 4})
        result = tool(fc)
        self.assertIsInstance(result, protos.FunctionResponse)
        self.assertEqual(result.response["result"], 8)

    def test_tool_call_non_callable_returns_none(self):
        proto_fd = protos.FunctionDeclaration(name="g", description="d")
        tool = responder.Tool(function_declarations=[proto_fd])
        fc = protos.FunctionCall(name="g", args={})
        result = tool(fc)
        self.assertIsNone(result)

    def test_duplicate_function_name_raises(self):
        def f(x: int) -> int:
            """First."""
            return x

        def f2(x: int) -> int:
            """Second."""
            return x

        proto1 = protos.FunctionDeclaration(name="same", description="first")
        proto2 = protos.FunctionDeclaration(name="same", description="second")
        with self.assertRaises(ValueError):
            responder.Tool(function_declarations=[proto1, proto2])


# ---------------------------------------------------------------------------
# FunctionLibrary
# ---------------------------------------------------------------------------

class FunctionLibraryTests(absltest.TestCase):

    def test_basic_library(self):
        def add(a: int, b: int) -> int:
            """Adds numbers."""
            return a + b

        lib = responder.FunctionLibrary(tools=[add])
        protos_list = lib.to_proto()
        self.assertLen(protos_list, 1)

    def test_library_getitem(self):
        def add(a: int, b: int) -> int:
            """Adds numbers."""
            return a + b

        lib = responder.FunctionLibrary(tools=[add])
        fd = lib["add"]
        self.assertEqual(fd.name, "add")

    def test_library_getitem_by_function_call(self):
        def add(a: int, b: int) -> int:
            """Adds numbers."""
            return a + b

        lib = responder.FunctionLibrary(tools=[add])
        fc = protos.FunctionCall(name="add", args={"a": 1, "b": 2})
        fd = lib[fc]
        self.assertEqual(fd.name, "add")

    def test_library_call_returns_part(self):
        def add(a: int, b: int) -> int:
            """Adds numbers."""
            return a + b

        lib = responder.FunctionLibrary(tools=[add])
        fc = protos.FunctionCall(name="add", args={"a": 2, "b": 3})
        result = lib(fc)
        self.assertIsInstance(result, protos.Part)
        self.assertEqual(result.function_response.response["result"], 5)

    def test_library_call_non_callable_returns_none(self):
        proto_fd = protos.FunctionDeclaration(name="g", description="d")
        lib = responder.FunctionLibrary(tools=[proto_fd])
        fc = protos.FunctionCall(name="g", args={})
        result = lib(fc)
        self.assertIsNone(result)

    def test_duplicate_name_across_tools_raises(self):
        def f(x: int) -> int:
            """A function."""
            return x

        proto_fd = protos.FunctionDeclaration(name="f", description="duplicate")
        with self.assertRaises(ValueError):
            responder.FunctionLibrary(tools=[f, proto_fd])


# ---------------------------------------------------------------------------
# _make_tool
# ---------------------------------------------------------------------------

class MakeToolTests(absltest.TestCase):

    def test_from_tool(self):
        def f(x: int) -> int:
            """A function."""
            return x

        tool = responder.Tool(function_declarations=[f])
        result = responder._make_tool(tool)
        self.assertIs(result, tool)

    def test_from_proto_tool(self):
        proto_tool = protos.Tool(
            function_declarations=[protos.FunctionDeclaration(name="f", description="d")]
        )
        result = responder._make_tool(proto_tool)
        self.assertIsInstance(result, responder.Tool)

    def test_from_dict_with_function_declarations(self):
        proto_fd = protos.FunctionDeclaration(name="f", description="d")
        result = responder._make_tool({"function_declarations": [proto_fd]})
        self.assertIsInstance(result, responder.Tool)

    def test_from_dict_single_fd(self):
        result = responder._make_tool({"name": "f", "description": "d"})
        self.assertIsInstance(result, responder.Tool)

    def test_from_iterable(self):
        def f(x: int) -> int:
            """A function."""
            return x

        result = responder._make_tool([f])
        self.assertIsInstance(result, responder.Tool)

    def test_from_callable(self):
        def f(x: int) -> int:
            """A function."""
            return x

        result = responder._make_tool(f)
        self.assertIsInstance(result, responder.Tool)


# ---------------------------------------------------------------------------
# _make_tools and to_function_library
# ---------------------------------------------------------------------------

class MakeToolsTests(absltest.TestCase):

    def test_multiple_single_fn_tools_flattened(self):
        def a(x: int) -> int:
            """a."""
            return x

        def b(x: int) -> int:
            """b."""
            return x

        tools = responder._make_tools([a, b])
        # Two single-fn tools should be merged into one
        self.assertLen(tools, 1)
        self.assertLen(tools[0].function_declarations, 2)

    def test_single_tool_not_flattened(self):
        def f(x: int) -> int:
            """f."""
            return x

        tools = responder._make_tools([f])
        self.assertLen(tools, 1)

    def test_non_iterable_tool(self):
        def f(x: int) -> int:
            """f."""
            return x

        tools = responder._make_tools(f)
        self.assertLen(tools, 1)


class ToFunctionLibraryTests(absltest.TestCase):

    def test_none_returns_none(self):
        result = responder.to_function_library(None)
        self.assertIsNone(result)

    def test_function_library_returned_as_is(self):
        def f(x: int) -> int:
            """f."""
            return x

        lib = responder.FunctionLibrary(tools=[f])
        result = responder.to_function_library(lib)
        self.assertIs(result, lib)

    def test_creates_library_from_callable(self):
        def f(x: int) -> int:
            """f."""
            return x

        result = responder.to_function_library(f)
        self.assertIsInstance(result, responder.FunctionLibrary)


# ---------------------------------------------------------------------------
# to_function_calling_mode
# ---------------------------------------------------------------------------

class ToFunctionCallingModeTests(parameterized.TestCase):

    @parameterized.named_parameters(
        ["auto_str", "auto", responder.FunctionCallingMode.AUTO],
        ["any_str", "any", responder.FunctionCallingMode.ANY],
        ["none_str", "none", responder.FunctionCallingMode.NONE],
        ["auto_int", 1, responder.FunctionCallingMode.AUTO],
        ["any_int", 2, responder.FunctionCallingMode.ANY],
        ["none_int", 3, responder.FunctionCallingMode.NONE],
    )
    def test_to_function_calling_mode(self, x, expected):
        result = responder.to_function_calling_mode(x)
        self.assertEqual(result, expected)


# ---------------------------------------------------------------------------
# to_function_calling_config
# ---------------------------------------------------------------------------

class ToFunctionCallingConfigTests(absltest.TestCase):

    def test_from_proto(self):
        cfg = protos.FunctionCallingConfig(mode=responder.FunctionCallingMode.AUTO)
        result = responder.to_function_calling_config(cfg)
        self.assertIs(result, cfg)

    def test_from_string_mode(self):
        result = responder.to_function_calling_config("auto")
        self.assertIsInstance(result, protos.FunctionCallingConfig)
        self.assertEqual(result.mode, responder.FunctionCallingMode.AUTO)

    def test_from_int_mode(self):
        result = responder.to_function_calling_config(1)
        self.assertEqual(result.mode, responder.FunctionCallingMode.AUTO)

    def test_from_dict(self):
        result = responder.to_function_calling_config(
            {"mode": "any", "allowed_function_names": ["f"]}
        )
        self.assertEqual(result.mode, responder.FunctionCallingMode.ANY)

    def test_invalid_type_raises(self):
        with self.assertRaises(TypeError):
            responder.to_function_calling_config([1, 2])


# ---------------------------------------------------------------------------
# to_tool_config
# ---------------------------------------------------------------------------

class ToToolConfigTests(absltest.TestCase):

    def test_from_proto(self):
        cfg = protos.ToolConfig(
            function_calling_config=protos.FunctionCallingConfig(
                mode=responder.FunctionCallingMode.AUTO
            )
        )
        result = responder.to_tool_config(cfg)
        self.assertIs(result, cfg)

    def test_from_dict(self):
        result = responder.to_tool_config({"function_calling_config": "auto"})
        self.assertIsInstance(result, protos.ToolConfig)
        self.assertEqual(
            result.function_calling_config.mode, responder.FunctionCallingMode.AUTO
        )

    def test_invalid_type_raises(self):
        with self.assertRaises(TypeError):
            responder.to_tool_config("not_a_dict_or_proto")


if __name__ == "__main__":
    absltest.main()
