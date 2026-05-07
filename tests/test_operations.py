# -*- coding: utf-8 -*-
# Copyright 2023 Google LLC
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

from contextlib import redirect_stderr
import io
import unittest

from google.generativeai import protos
from google.generativeai import client as client_lib
import google.protobuf.any_pb2

import google.generativeai.operations as genai_operation
from google.generativeai.types import model_types
import google.api_core.operation as core_operation

from absl.testing import absltest
from absl.testing import parameterized


class OperationsTests(parameterized.TestCase):
    metadata_type = (
        "type.googleapis.com/google.ai.generativelanguage.v1beta.CreateTunedModelMetadata"
    )
    result_type = "type.googleapis.com/google.ai.generativelanguage.v1beta.TunedModel"

    def test_end_to_end(self):
        name = "my-model"

        # Operation is defined here: https://github.com/googleapis/googleapis/blob/master/google/longrunning/operations.proto#L128
        # It uses `google.protobuf.Any` to encode the metadata and results
        # `Any` takes a type name and a serialized proto.
        metadata = google.protobuf.any_pb2.Any(
            type_url=self.metadata_type,
            value=protos.CreateTunedModelMetadata(tuned_model=name)._pb.SerializeToString(),
        )

        # Initially the `Operation` is not `done`, so it only gives a metadata.
        initial_pb = core_operation.operations_pb2.Operation(
            name=f"tunedModels/{name}/operations/urvodfipaft0",
            done=False,
            metadata=metadata,
        )

        # When the `Operation` is `done`, it returns a `response`
        final_pb = core_operation.operations_pb2.Operation(
            name=f"tunedModels/{name}/operations/urvodfipaft0",
            done=True,
            metadata=metadata,
            response=google.protobuf.any_pb2.Any(
                type_url=self.result_type,
                value=protos.TunedModel(name=name)._pb.SerializeToString(),
            ),
        )

        # Create the operation with the `initial_pb` but when it asks for an update
        # return the `final_pb`.
        def refresh(*_, **__):
            return final_pb

        # This is the base Operation class
        operation = core_operation.Operation(
            operation=initial_pb,
            refresh=refresh,
            cancel=lambda: print(f"cancel!"),
            result_type=protos.TunedModel,
            metadata_type=protos.CreateTunedModelMetadata,
        )

        # Use our wrapper instead.
        ctm_op = genai_operation.CreateTunedModelOperation.from_core_operation(operation)

        # Test that the metadata was decoded
        meta = ctm_op.metadata
        self.assertEqual(meta.tuned_model, name)

        # Update the status to get the `final_pb`
        result = ctm_op.result()

        # Check that the result was decoded.
        self.assertIsInstance(result, model_types.TunedModel)
        self.assertEqual(result.name, name)

    def test_wait_bar(self):
        name = "my-model"

        def gen_operations():
            """yield 10+done incremental operation statuses"""

            def make_metadata(completed_steps):
                return google.protobuf.any_pb2.Any(
                    type_url=self.metadata_type,
                    value=protos.CreateTunedModelMetadata(
                        tuned_model=name,
                        total_steps=total_steps,
                        completed_steps=completed_steps,
                    )._pb.SerializeToString(),
                )

            total_steps = 10
            for completed_steps in range(total_steps):
                metadata = make_metadata(completed_steps)

                yield core_operation.operations_pb2.Operation(
                    name=f"tunedModels/{name}/operations/urvodfipaft0",
                    done=False,
                    metadata=metadata,
                )

            op = core_operation.operations_pb2.Operation(
                name=f"tunedModels/{name}/operations/urvodfipaft0",
                done=True,
                metadata=make_metadata(total_steps),
                response=google.protobuf.any_pb2.Any(
                    type_url=self.result_type,
                    value=protos.TunedModel(name=name)._pb.SerializeToString(),
                ),
            )

            while True:
                yield op

        # pop the initial status
        ops = gen_operations()
        initial_pb = next(ops)

        def refresh(*_, **__):
            """get the next status on each refresh"""
            return next(ops)

        # This is the base Operation class
        operation = core_operation.Operation(
            operation=initial_pb,
            refresh=refresh,
            cancel=None,
            result_type=protos.TunedModel,
            metadata_type=protos.CreateTunedModelMetadata,
        )

        # Use our wrapper instead.
        ctm_op = genai_operation.CreateTunedModelOperation.from_core_operation(operation)

        # Capture the stderr so we can check the wait-bar.
        f = io.StringIO()
        with redirect_stderr(f):
            for status in ctm_op.wait_bar():
                pass

        s = f.getvalue()
        self.assertIn("100%|##########| 10/10", s)
        self.assertTrue(ctm_op.done())


class MockOperationsClient:
    """Mock client for operations testing."""

    def __init__(self):
        self.list_operations_calls = []
        self.get_operation_calls = []
        self.delete_operation_calls = []
        self._operations = []

    def list_operations(self, name, filter_):
        self.list_operations_calls.append((name, filter_))
        return iter(self._operations)

    def get_operation(self, name, **kwargs):
        self.get_operation_calls.append(name)
        if self._operations:
            return self._operations[0]
        raise KeyError(f"Operation {name} not found")

    def delete_operation(self, name):
        self.delete_operation_calls.append(name)

    def cancel_operation(self, name, **kwargs):
        pass


def _make_done_operation_pb(name, metadata_type, result_type):
    """Create a done Operation protobuf message."""
    metadata = google.protobuf.any_pb2.Any(
        type_url=metadata_type,
        value=protos.CreateTunedModelMetadata(
            tuned_model=name, total_steps=1, completed_steps=1
        )._pb.SerializeToString(),
    )
    return core_operation.operations_pb2.Operation(
        name=f"tunedModels/{name}/operations/op123",
        done=True,
        metadata=metadata,
        response=google.protobuf.any_pb2.Any(
            type_url=result_type,
            value=protos.TunedModel(name=name)._pb.SerializeToString(),
        ),
    )


class ListGetDeleteOperationsTests(parameterized.TestCase):
    metadata_type = (
        "type.googleapis.com/google.ai.generativelanguage.v1beta.CreateTunedModelMetadata"
    )
    result_type = "type.googleapis.com/google.ai.generativelanguage.v1beta.TunedModel"

    def setUp(self):
        self.mock_client = MockOperationsClient()
        client_lib._client_manager.clients["operations"] = self.mock_client

        op_pb = _make_done_operation_pb("my-model", self.metadata_type, self.result_type)
        self.mock_client._operations = [op_pb]

    def tearDown(self):
        client_lib._client_manager.clients.pop("operations", None)

    def test_list_operations(self):
        ops = list(genai_operation.list_operations(client=self.mock_client))
        self.assertLen(self.mock_client.list_operations_calls, 1)
        self.assertLen(ops, 1)
        self.assertIsInstance(ops[0], genai_operation.CreateTunedModelOperation)

    def test_list_operations_uses_default_client(self):
        ops = list(genai_operation.list_operations())
        self.assertLen(ops, 1)

    def test_get_operation(self):
        op = genai_operation.get_operation(
            "tunedModels/my-model/operations/op123", client=self.mock_client
        )
        self.assertIsInstance(op, genai_operation.CreateTunedModelOperation)
        self.assertLen(self.mock_client.get_operation_calls, 1)

    def test_get_operation_uses_default_client(self):
        op = genai_operation.get_operation("tunedModels/my-model/operations/op123")
        self.assertIsInstance(op, genai_operation.CreateTunedModelOperation)

    def test_delete_operation(self):
        genai_operation.delete_operation(
            "tunedModels/my-model/operations/op123", client=self.mock_client
        )
        self.assertLen(self.mock_client.delete_operation_calls, 1)
        self.assertEqual(
            self.mock_client.delete_operation_calls[0],
            "tunedModels/my-model/operations/op123",
        )

    def test_delete_operation_uses_default_client(self):
        genai_operation.delete_operation("tunedModels/my-model/operations/op123")
        self.assertLen(self.mock_client.delete_operation_calls, 1)

    def test_from_proto(self):
        op_pb = _make_done_operation_pb("my-model", self.metadata_type, self.result_type)
        op = genai_operation.CreateTunedModelOperation.from_proto(op_pb, self.mock_client)
        self.assertIsInstance(op, genai_operation.CreateTunedModelOperation)
        self.assertEqual(op.name, f"tunedModels/my-model/operations/op123")

    def test_name_property(self):
        op_pb = _make_done_operation_pb("my-model", self.metadata_type, self.result_type)
        op = genai_operation.CreateTunedModelOperation.from_proto(op_pb, self.mock_client)
        self.assertEqual(op.name, "tunedModels/my-model/operations/op123")

    def test_update_method(self):
        op_pb = _make_done_operation_pb("my-model", self.metadata_type, self.result_type)

        def refresh(*_, **__):
            return op_pb

        op = genai_operation.CreateTunedModelOperation(
            operation=op_pb,
            refresh=refresh,
            cancel=lambda: None,
            result_type=protos.TunedModel,
            metadata_type=protos.CreateTunedModelMetadata,
        )
        # Should not raise
        op.update()

    def test_from_gapic(self):
        op_pb = _make_done_operation_pb("my-model", self.metadata_type, self.result_type)
        op = genai_operation.from_gapic(
            cls=genai_operation.CreateTunedModelOperation,
            operation=op_pb,
            operations_client=self.mock_client,
            result_type=protos.TunedModel,
            metadata_type=protos.CreateTunedModelMetadata,
        )
        self.assertIsInstance(op, genai_operation.CreateTunedModelOperation)

    def test_from_core_operation_no_polling_no_retry(self):
        """Test from_core_operation when neither polling nor retry attribute exists."""
        op_pb = _make_done_operation_pb("my-model", self.metadata_type, self.result_type)

        def refresh(*_, **__):
            return op_pb

        base_op = core_operation.Operation(
            operation=op_pb,
            refresh=refresh,
            cancel=None,
            result_type=protos.TunedModel,
            metadata_type=protos.CreateTunedModelMetadata,
        )
        # Remove any polling/retry attrs to test the kwargs={} branch
        if hasattr(base_op, "_polling"):
            del base_op._polling
        if hasattr(base_op, "_retry"):
            del base_op._retry

        ctm_op = genai_operation.CreateTunedModelOperation.from_core_operation(base_op)
        self.assertIsInstance(ctm_op, genai_operation.CreateTunedModelOperation)


if __name__ == "__main__":
    absltest.main()
