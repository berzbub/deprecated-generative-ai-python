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

from typing import Optional

from absl.testing import absltest
from absl.testing import parameterized

from google.generativeai import protos
from google.generativeai import responder


def _add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


def _greet(name: str, greeting: Optional[str] = None) -> str:
    """Greet a person."""
    if greeting:
        return f"{greeting}, {name}!"
    return f"Hello, {name}!"


def _no_args() -> str:
    """A function with no arguments."""
    return "hello"


class ToTypeTests(parameterized.TestCase):
    @parameterized.named_parameters(
        ["string_str", "string", protos.Type.STRING],
        ["integer_int", "integer", protos.Type.INTEGER],
        ["number_int", "number", protos.Type.NUMBER],
        ["boolean_str", "boolean", protos.Type.BOOLEAN],
        ["array_str", "array", protos.Type.ARRAY],
        ["object_str", "object", protos.Type.OBJECT],
        ["int_1", 1, protos.Type.STRING],
        ["int_3", 3, protos.Type.INTEGER],
        ["enum_type", protos.Type.STRING, protos.Type.STRING],
    )
    def test_to_type(self, x, expected):
        result = responder.to_type(x)
        self.assertEqual(result, expected)


class GenerateSchemaTests(parameterized.TestCase):
    def test_generate_schema_basic(self):
        schema = responder._generate_schema(_add)
        self.assertEqual(schema["name"], "_add")
        self.assertEqual(schema["description"], "Add two integers.")
        self.assertIn("parameters", schema)
        params = schema["parameters"]
        self.assertIn("properties", params)
        self.assertIn("a", params["properties"])
        self.assertIn("b", params["properties"])

    def test_generate_schema_required_inferred(self):
        schema = responder._generate_schema(_add)
        self.assertIn("required", schema["parameters"])
        required = schema["parameters"]["required"]
        self.assertIn("a", required)
        self.assertIn("b", required)

    def test_generate_schema_optional_not_required(self):
        schema = responder._generate_schema(_greet)
        required = schema["parameters"].get("required", [])
        self.assertIn("name", required)
        self.assertNotIn("greeting", required)

    def test_generate_schema_custom_required(self):
        schema = responder._generate_schema(_add, required=["a"])
        self.assertEqual(schema["parameters"]["required"], ["a"])

    def test_generate_schema_with_descriptions(self):
        schema = responder._generate_schema(
            _add, descriptions={"a": "first number", "b": "second number"}
        )
        props = schema["parameters"]["properties"]
        self.assertIn("a", props)

    def test_generate_schema_no_args(self):
        schema = responder._generate_schema(_no_args)
        self.assertEqual(schema["name"], "_no_args")
        self.assertNotIn("parameters", schema)

    def test_generate_schema_empty_required(self):
        schema = responder._generate_schema(_greet, required=[])
        self.assertEqual(schema["parameters"]["required"], [])


class BuildSchemaTests(absltest.TestCase):
    def test_build_schema_simple(self):
        from typing import Any
        import pydantic

        fields = {"x": (int, pydantic.Field())}
        schema = responder._build_schema("test_fn", fields)
        self.assertIn("properties", schema)
        self.assertIn("x", schema["properties"])

    def test_build_schema_strips_title(self):
        from typing import Any
        import pydantic

        fields = {"x": (int, pydantic.Field())}
        schema = responder._build_schema("test_fn", fields)
        self.assertNotIn("title", schema)

    def test_build_schema_strips_additional_properties(self):
        from typing import Any
        import pydantic

        fields = {"x": (int, pydantic.Field())}
        schema = responder._build_schema("test_fn", fields)
        self.assertNotIn("additionalProperties", schema)


class UnpackDefsTests(absltest.TestCase):
    def test_unpack_defs_with_ref(self):
        defs = {"MyType": {"type": "object", "properties": {"val": {"type": "string"}}}}
        schema = {"properties": {"x": {"$ref": "#/$defs/MyType"}}}
        responder.unpack_defs(schema, defs)
        self.assertNotIn("$ref", schema["properties"]["x"])
        self.assertEqual(schema["properties"]["x"]["type"], "object")

    def test_unpack_defs_with_anyof_ref(self):
        defs = {"MyType": {"type": "string"}}
        schema = {"properties": {"x": {"anyOf": [{"$ref": "#/$defs/MyType"}, {"type": "null"}]}}}
        responder.unpack_defs(schema, defs)
        # The anyOf entry should have been replaced with the actual type
        self.assertEqual(schema["properties"]["x"]["anyOf"][0]["type"], "string")

    def test_unpack_defs_with_items_ref(self):
        defs = {"MyItem": {"type": "integer"}}
        schema = {"properties": {"x": {"items": {"$ref": "#/$defs/MyItem"}}}}
        responder.unpack_defs(schema, defs)
        self.assertEqual(schema["properties"]["x"]["items"]["type"], "integer")

    def test_unpack_defs_no_properties(self):
        defs = {}
        schema = {"type": "string"}
        responder.unpack_defs(schema, defs)  # Should not raise
        self.assertEqual(schema["type"], "string")


class StripTitlesTests(absltest.TestCase):
    def test_strip_titles_removes_title(self):
        schema = {"title": "MyTitle", "type": "object"}
        responder.strip_titles(schema)
        self.assertNotIn("title", schema)

    def test_strip_titles_nested(self):
        schema = {
            "title": "Top",
            "type": "object",
            "properties": {
                "x": {"title": "X", "type": "string"},
            },
        }
        responder.strip_titles(schema)
        self.assertNotIn("title", schema)
        self.assertNotIn("title", schema["properties"]["x"])

    def test_strip_titles_items(self):
        schema = {"type": "array", "items": {"title": "Item", "type": "string"}}
        responder.strip_titles(schema)
        self.assertNotIn("title", schema["items"])


class StripAdditionalPropertiesTests(absltest.TestCase):
    def test_strip_additional_properties(self):
        schema = {"type": "object", "additionalProperties": False}
        responder.strip_additional_properties(schema)
        self.assertNotIn("additionalProperties", schema)

    def test_strip_additional_properties_nested(self):
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "x": {"type": "object", "additionalProperties": True},
            },
        }
        responder.strip_additional_properties(schema)
        self.assertNotIn("additionalProperties", schema)
        self.assertNotIn("additionalProperties", schema["properties"]["x"])

    def test_strip_additional_properties_items(self):
        schema = {"type": "array", "items": {"additionalProperties": False}}
        responder.strip_additional_properties(schema)
        self.assertNotIn("additionalProperties", schema["items"])


class AddObjectTypeTests(absltest.TestCase):
    def test_add_object_type_for_schema_with_properties(self):
        schema = {"properties": {"x": {"type": "string"}}}
        responder.add_object_type(schema)
        self.assertEqual(schema["type"], "object")

    def test_add_object_type_removes_required(self):
        schema = {"properties": {"x": {"type": "string"}}, "required": ["x"]}
        responder.add_object_type(schema)
        self.assertNotIn("required", schema)

    def test_add_object_type_items(self):
        schema = {"type": "array", "items": {"properties": {"x": {"type": "string"}}}}
        responder.add_object_type(schema)
        self.assertEqual(schema["items"]["type"], "object")


class ConvertToNullableTests(absltest.TestCase):
    def test_convert_to_nullable_optional(self):
        schema = {"anyOf": [{"type": "string"}, {"type": "null"}]}
        responder.convert_to_nullable(schema)
        self.assertEqual(schema["type"], "string")
        self.assertTrue(schema["nullable"])
        self.assertNotIn("anyOf", schema)

    def test_convert_to_nullable_optional_null_first(self):
        schema = {"anyOf": [{"type": "null"}, {"type": "integer"}]}
        responder.convert_to_nullable(schema)
        self.assertEqual(schema["type"], "integer")
        self.assertTrue(schema["nullable"])

    def test_convert_to_nullable_invalid_union(self):
        schema = {"anyOf": [{"type": "string"}, {"type": "integer"}]}
        with self.assertRaises(ValueError):
            responder.convert_to_nullable(schema)

    def test_convert_to_nullable_wrong_size(self):
        schema = {"anyOf": [{"type": "string"}, {"type": "null"}, {"type": "integer"}]}
        with self.assertRaises(ValueError):
            responder.convert_to_nullable(schema)

    def test_convert_to_nullable_nested_properties(self):
        schema = {
            "type": "object",
            "properties": {
                "x": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            },
        }
        responder.convert_to_nullable(schema)
        self.assertTrue(schema["properties"]["x"]["nullable"])

    def test_convert_to_nullable_items(self):
        schema = {"type": "array", "items": {"anyOf": [{"type": "integer"}, {"type": "null"}]}}
        responder.convert_to_nullable(schema)
        self.assertTrue(schema["items"]["nullable"])


class RenameSchemaFieldsTests(absltest.TestCase):
    def test_rename_type_field(self):
        schema = {"type": "string"}
        result = responder._rename_schema_fields(schema)
        self.assertNotIn("type", result)
        self.assertIn("type_", result)
        self.assertEqual(result["type_"], protos.Type.STRING)

    def test_rename_format_field(self):
        schema = {"format": "float"}
        result = responder._rename_schema_fields(schema)
        self.assertNotIn("format", result)
        self.assertIn("format_", result)
        self.assertEqual(result["format_"], "float")

    def test_rename_items_recursively(self):
        schema = {"items": {"type": "integer"}}
        result = responder._rename_schema_fields(schema)
        # items key is kept; the nested schema is recursively processed
        self.assertIn("items", result)
        self.assertIn("type_", result["items"])

    def test_rename_properties_recursively(self):
        schema = {"properties": {"x": {"type": "string"}}}
        result = responder._rename_schema_fields(schema)
        self.assertIn("properties", result)
        self.assertIn("type_", result["properties"]["x"])

    def test_rename_schema_fields_none(self):
        result = responder._rename_schema_fields(None)
        self.assertIsNone(result)


class FunctionDeclarationTests(absltest.TestCase):
    def test_init(self):
        fd = responder.FunctionDeclaration(
            name="my_func",
            description="Does something",
            parameters={"type": "object", "properties": {"x": {"type": "string"}}},
        )
        self.assertEqual(fd.name, "my_func")
        self.assertEqual(fd.description, "Does something")

    def test_init_no_parameters(self):
        fd = responder.FunctionDeclaration(name="no_params", description="No params")
        self.assertEqual(fd.name, "no_params")

    def test_from_proto(self):
        proto = protos.FunctionDeclaration(name="proto_func", description="from proto")
        fd = responder.FunctionDeclaration.from_proto(proto)
        self.assertEqual(fd.name, "proto_func")

    def test_to_proto(self):
        fd = responder.FunctionDeclaration(name="my_func", description="test")
        proto = fd.to_proto()
        self.assertIsInstance(proto, protos.FunctionDeclaration)
        self.assertEqual(proto.name, "my_func")

    def test_from_function(self):
        fd = responder.FunctionDeclaration.from_function(_add)
        self.assertIsInstance(fd, responder.CallableFunctionDeclaration)
        self.assertEqual(fd.name, "_add")
        self.assertEqual(fd.description, "Add two integers.")

    def test_from_function_with_descriptions(self):
        fd = responder.FunctionDeclaration.from_function(
            _add, descriptions={"a": "first operand", "b": "second operand"}
        )
        self.assertIsInstance(fd, responder.CallableFunctionDeclaration)


class CallableFunctionDeclarationTests(absltest.TestCase):
    def test_call(self):
        cfd = responder.CallableFunctionDeclaration.from_function(_add)
        fc = protos.FunctionCall(name="_add", args={"a": 3, "b": 4})
        response = cfd(fc)
        self.assertIsInstance(response, protos.FunctionResponse)
        self.assertEqual(response.response["result"], 7)

    def test_call_dict_result(self):
        def returns_dict(x: int) -> dict:
            """Returns a dict."""
            return {"value": x * 2}

        cfd = responder.CallableFunctionDeclaration.from_function(returns_dict)
        fc = protos.FunctionCall(name="returns_dict", args={"x": 5})
        response = cfd(fc)
        self.assertEqual(response.response["value"], 10)


class MakeFunctionDeclarationTests(absltest.TestCase):
    def test_from_function_declaration(self):
        fd = responder.FunctionDeclaration(name="f", description="d")
        result = responder._make_function_declaration(fd)
        self.assertIs(result, fd)

    def test_from_protos_function_declaration(self):
        proto = protos.FunctionDeclaration(name="f", description="d")
        result = responder._make_function_declaration(proto)
        self.assertIs(result, proto)

    def test_from_dict_with_function(self):
        def fn(x: int) -> int:
            """test fn"""
            return x

        d = {
            "name": "fn",
            "description": "test fn",
            "function": fn,
        }
        result = responder._make_function_declaration(d)
        self.assertIsInstance(result, responder.CallableFunctionDeclaration)

    def test_from_dict_without_function(self):
        d = {"name": "fn", "description": "test fn"}
        result = responder._make_function_declaration(d)
        self.assertIsInstance(result, responder.FunctionDeclaration)

    def test_from_callable(self):
        result = responder._make_function_declaration(_add)
        self.assertIsInstance(result, responder.CallableFunctionDeclaration)

    def test_invalid_type_raises(self):
        with self.assertRaises(TypeError):
            responder._make_function_declaration(42)


class ToolTests(absltest.TestCase):
    def test_init(self):
        tool = responder.Tool(function_declarations=[_add])
        self.assertLen(tool.function_declarations, 1)

    def test_function_declarations_property(self):
        tool = responder.Tool(function_declarations=[_add, _greet])
        self.assertLen(tool.function_declarations, 2)

    def test_getitem_by_name(self):
        tool = responder.Tool(function_declarations=[_add])
        fd = tool["_add"]
        self.assertEqual(fd.name, "_add")

    def test_getitem_by_function_call(self):
        tool = responder.Tool(function_declarations=[_add])
        fc = protos.FunctionCall(name="_add", args={"a": 1, "b": 2})
        fd = tool[fc]
        self.assertEqual(fd.name, "_add")

    def test_call_callable_declaration(self):
        tool = responder.Tool(function_declarations=[_add])
        fc = protos.FunctionCall(name="_add", args={"a": 2, "b": 3})
        response = tool(fc)
        self.assertIsInstance(response, protos.FunctionResponse)
        self.assertEqual(response.response["result"], 5)

    def test_call_non_callable_declaration_returns_none(self):
        fd = responder.FunctionDeclaration(name="static_fn", description="static")
        tool = responder.Tool(function_declarations=[fd])
        fc = protos.FunctionCall(name="static_fn", args={})
        result = tool(fc)
        self.assertIsNone(result)

    def test_to_proto(self):
        tool = responder.Tool(function_declarations=[_add])
        proto = tool.to_proto()
        self.assertIsInstance(proto, protos.Tool)

    def test_duplicate_name_raises(self):
        fd1 = responder.FunctionDeclaration(name="fn", description="first")
        fd2 = responder.FunctionDeclaration(name="fn", description="second")
        with self.assertRaises(ValueError):
            responder.Tool(function_declarations=[fd1, fd2])


class FunctionLibraryTests(absltest.TestCase):
    def test_init_single_tool(self):
        lib = responder.FunctionLibrary(tools=[responder.Tool(function_declarations=[_add])])
        self.assertIsNotNone(lib)

    def test_getitem_by_name(self):
        lib = responder.FunctionLibrary(tools=[responder.Tool(function_declarations=[_add])])
        fd = lib["_add"]
        self.assertEqual(fd.name, "_add")

    def test_getitem_by_function_call(self):
        lib = responder.FunctionLibrary(tools=[responder.Tool(function_declarations=[_add])])
        fc = protos.FunctionCall(name="_add", args={"a": 1, "b": 2})
        fd = lib[fc]
        self.assertEqual(fd.name, "_add")

    def test_call_returns_part(self):
        lib = responder.FunctionLibrary(tools=[responder.Tool(function_declarations=[_add])])
        fc = protos.FunctionCall(name="_add", args={"a": 4, "b": 6})
        part = lib(fc)
        self.assertIsInstance(part, protos.Part)
        self.assertEqual(part.function_response.response["result"], 10)

    def test_call_non_callable_returns_none(self):
        fd = responder.FunctionDeclaration(name="static", description="no call")
        lib = responder.FunctionLibrary(tools=[responder.Tool(function_declarations=[fd])])
        fc = protos.FunctionCall(name="static", args={})
        result = lib(fc)
        self.assertIsNone(result)

    def test_to_proto(self):
        lib = responder.FunctionLibrary(tools=[responder.Tool(function_declarations=[_add])])
        protos_list = lib.to_proto()
        self.assertIsInstance(protos_list, list)
        self.assertLen(protos_list, 1)

    def test_duplicate_function_raises(self):
        tool1 = responder.Tool(function_declarations=[_add])
        tool2 = responder.Tool(function_declarations=[_add])
        with self.assertRaises(ValueError):
            responder.FunctionLibrary(tools=[tool1, tool2])


class MakeToolsTests(absltest.TestCase):
    def test_make_tool_from_tool(self):
        t = responder.Tool(function_declarations=[_add])
        result = responder._make_tool(t)
        self.assertIs(result, t)

    def test_make_tool_from_protos_tool(self):
        proto_tool = protos.Tool(
            function_declarations=[protos.FunctionDeclaration(name="f", description="d")]
        )
        result = responder._make_tool(proto_tool)
        self.assertIsInstance(result, responder.Tool)

    def test_make_tool_from_dict_with_function_declarations(self):
        d = {"function_declarations": [_add]}
        result = responder._make_tool(d)
        self.assertIsInstance(result, responder.Tool)

    def test_make_tool_from_callable(self):
        result = responder._make_tool(_add)
        self.assertIsInstance(result, responder.Tool)

    def test_make_tools_flattens_single_declaration_tools(self):
        tools = [_add, _greet]
        result = responder._make_tools(tools)
        # Multiple single-function tools should be merged into one tool
        self.assertLen(result, 1)
        self.assertLen(result[0].function_declarations, 2)

    def test_make_tools_from_single_tool(self):
        tool = responder.Tool(function_declarations=[_add, _greet])
        result = responder._make_tools(tool)
        self.assertLen(result, 1)


class ToFunctionLibraryTests(absltest.TestCase):
    def test_none_returns_none(self):
        result = responder.to_function_library(None)
        self.assertIsNone(result)

    def test_function_library_passthrough(self):
        lib = responder.FunctionLibrary(tools=[responder.Tool(function_declarations=[_add])])
        result = responder.to_function_library(lib)
        self.assertIs(result, lib)

    def test_creates_library_from_tools(self):
        result = responder.to_function_library([_add])
        self.assertIsInstance(result, responder.FunctionLibrary)


class ToFunctionCallingModeTests(parameterized.TestCase):
    FunctionCallingMode = protos.FunctionCallingConfig.Mode

    @parameterized.named_parameters(
        ["auto_str", "auto", protos.FunctionCallingConfig.Mode.AUTO],
        ["any_str", "any", protos.FunctionCallingConfig.Mode.ANY],
        ["none_str", "none", protos.FunctionCallingConfig.Mode.NONE],
        ["auto_int", 1, protos.FunctionCallingConfig.Mode.AUTO],
        ["any_int", 2, protos.FunctionCallingConfig.Mode.ANY],
        ["none_int", 3, protos.FunctionCallingConfig.Mode.NONE],
    )
    def test_to_function_calling_mode(self, x, expected):
        result = responder.to_function_calling_mode(x)
        self.assertEqual(result, expected)


class ToFunctionCallingConfigTests(absltest.TestCase):
    def test_from_proto(self):
        proto = protos.FunctionCallingConfig(mode="AUTO")
        result = responder.to_function_calling_config(proto)
        self.assertIs(result, proto)

    def test_from_string_mode(self):
        result = responder.to_function_calling_config("auto")
        self.assertIsInstance(result, protos.FunctionCallingConfig)
        self.assertEqual(result.mode, protos.FunctionCallingConfig.Mode.AUTO)

    def test_from_int_mode(self):
        result = responder.to_function_calling_config(1)
        self.assertIsInstance(result, protos.FunctionCallingConfig)
        self.assertEqual(result.mode, protos.FunctionCallingConfig.Mode.AUTO)

    def test_from_dict(self):
        result = responder.to_function_calling_config({"mode": "any"})
        self.assertIsInstance(result, protos.FunctionCallingConfig)
        self.assertEqual(result.mode, protos.FunctionCallingConfig.Mode.ANY)

    def test_invalid_type_raises(self):
        with self.assertRaises(TypeError):
            responder.to_function_calling_config(object())


class ToToolConfigTests(absltest.TestCase):
    def test_from_proto(self):
        proto = protos.ToolConfig(
            function_calling_config=protos.FunctionCallingConfig(mode="AUTO")
        )
        result = responder.to_tool_config(proto)
        self.assertIs(result, proto)

    def test_from_dict(self):
        d = {"function_calling_config": {"mode": "any"}}
        result = responder.to_tool_config(d)
        self.assertIsInstance(result, protos.ToolConfig)
        self.assertEqual(
            result.function_calling_config.mode, protos.FunctionCallingConfig.Mode.ANY
        )

    def test_invalid_type_raises(self):
        with self.assertRaises(TypeError):
            responder.to_tool_config("invalid")


if __name__ == "__main__":
    absltest.main()
