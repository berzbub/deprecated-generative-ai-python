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
from __future__ import annotations

from google.generativeai.types import file_types

import collections
import datetime
import io
import os
from typing import Iterable, Sequence
import pathlib

import google

import google.generativeai as genai
from google.generativeai import client as client_lib
from google.generativeai import protos
from absl.testing import parameterized


class FileServiceClient(client_lib.FileServiceClient):
    def __init__(self, test):
        self.test = test
        self.observed_requests = []
        self.responses = collections.defaultdict(list)

    def create_file(
        self,
        path: str | io.IOBase | os.PathLike,
        *,
        mime_type: str | None = None,
        name: str | None = None,
        display_name: str | None = None,
        resumable: bool = True,
        metadata: Sequence[tuple[str, str]] = (),
    ) -> protos.File:
        self.observed_requests.append(
            dict(
                path=path,
                mime_type=mime_type,
                name=name,
                display_name=display_name,
                resumable=resumable,
            )
        )
        return self.responses["create_file"].pop(0)

    def get_file(
        self,
        request: protos.GetFileRequest | None = None,
        *,
        name: str | None = None,
        **kwargs,
    ) -> protos.File:
        if request is None and name is not None:
            request = protos.GetFileRequest(name=name)
        self.observed_requests.append(request)
        return self.responses["get_file"].pop(0)

    def list_files(
        self,
        request: protos.ListFilesRequest,
        **kwargs,
    ) -> Iterable[protos.File]:
        self.observed_requests.append(request)
        for f in self.responses["list_files"].pop(0):
            yield f

    def delete_file(
        self,
        request: protos.DeleteFileRequest,
        **kwargs,
    ):
        self.observed_requests.append(request)
        return


class UnitTests(parameterized.TestCase):
    def setUp(self):
        self.client = FileServiceClient(self)

        client_lib._client_manager.clients["file"] = self.client

    @property
    def observed_requests(self):
        return self.client.observed_requests

    @property
    def responses(self):
        return self.client.responses

    def test_video_metadata(self):
        self.responses["create_file"].append(
            protos.File(
                uri="https://test",
                state="ACTIVE",
                mime_type="video/quicktime",
                video_metadata=dict(video_duration=datetime.timedelta(seconds=30)),
                error=dict(code=7, message="ok?"),
            )
        )

        f = genai.upload_file(path="dummy.mov")
        self.assertEqual(google.rpc.status_pb2.Status(code=7, message="ok?"), f.error)
        self.assertEqual(
            protos.VideoMetadata(dict(video_duration=datetime.timedelta(seconds=30))),
            f.video_metadata,
        )

    @parameterized.named_parameters(
        [
            dict(
                testcase_name="FileDataDict",
                file_data=dict(file_uri="https://test_uri"),
            ),
            dict(
                testcase_name="FileDict",
                file_data=dict(uri="https://test_uri"),
            ),
            dict(
                testcase_name="FileData",
                file_data=protos.FileData(file_uri="https://test_uri"),
            ),
            dict(
                testcase_name="protos.File",
                file_data=protos.File(uri="https://test_uri"),
            ),
            dict(
                testcase_name="file_types.File",
                file_data=file_types.File(dict(uri="https://test_uri")),
            ),
        ]
    )
    def test_to_file_data(self, file_data):
        file_data = file_types.to_file_data(file_data)
        self.assertEqual(protos.FileData(file_uri="https://test_uri"), file_data)

    def test_webp_mimetype(self):
        self.responses["create_file"].append(protos.File())

        response = genai.upload_file("test.webp")

        self.assertEqual("image/webp", self.observed_requests[0]["mime_type"])

    def test_upload_file_iobase_without_mime_type_raises(self):
        import io

        buf = io.BytesIO(b"some data")
        with self.assertRaises(ValueError) as ctx:
            genai.upload_file(path=buf)
        self.assertIn("mime_type", str(ctx.exception))

    def test_upload_file_iobase_with_mime_type(self):
        import io

        self.responses["create_file"].append(protos.File(uri="https://test", name="files/abc"))
        buf = io.BytesIO(b"some data")
        result = genai.upload_file(path=buf, mime_type="application/octet-stream")
        self.assertIsInstance(result, file_types.File)
        self.assertEqual(self.observed_requests[0]["mime_type"], "application/octet-stream")

    def test_upload_file_unknown_extension_raises(self):
        with self.assertRaises(ValueError) as ctx:
            genai.upload_file(path="mystery.unknownxyz")
        self.assertIn("mime_type", str(ctx.exception))

    def test_upload_file_name_without_slash_prefixed(self):
        self.responses["create_file"].append(protos.File(uri="https://test", name="files/myname"))
        genai.upload_file("test.webp", name="myname")
        self.assertEqual(self.observed_requests[0]["name"], "files/myname")

    def test_upload_file_name_with_slash_unchanged(self):
        self.responses["create_file"].append(protos.File(uri="https://test", name="files/myname"))
        genai.upload_file("test.webp", name="files/myname")
        self.assertEqual(self.observed_requests[0]["name"], "files/myname")

    def test_list_files(self):
        self.responses["list_files"].append(
            [
                protos.File(name="files/abc", uri="https://a"),
                protos.File(name="files/def", uri="https://b"),
            ]
        )
        result = list(genai.list_files())
        self.assertLen(result, 2)
        self.assertIsInstance(result[0], file_types.File)
        self.assertIsInstance(result[1], file_types.File)
        self.assertEqual(result[0].name, "files/abc")

    def test_get_file_with_slash(self):
        self.responses["get_file"].append(protos.File(name="files/abc", uri="https://test"))
        result = genai.get_file("files/abc")
        self.assertIsInstance(result, file_types.File)
        req = self.observed_requests[0]
        self.assertEqual(req.name, "files/abc")

    def test_get_file_without_slash_prefixed(self):
        self.responses["get_file"].append(protos.File(name="files/abc", uri="https://test"))
        result = genai.get_file("abc")
        self.assertIsInstance(result, file_types.File)
        req = self.observed_requests[0]
        self.assertEqual(req.name, "files/abc")

    def test_delete_file_by_string_name(self):
        genai.delete_file("files/abc")
        req = self.observed_requests[0]
        self.assertIsInstance(req, protos.DeleteFileRequest)
        self.assertEqual(req.name, "files/abc")

    def test_delete_file_by_string_without_slash(self):
        genai.delete_file("abc")
        req = self.observed_requests[0]
        self.assertEqual(req.name, "files/abc")

    def test_delete_file_by_file_types_file(self):
        f = file_types.File(dict(name="files/abc"))
        genai.delete_file(f)
        req = self.observed_requests[0]
        self.assertEqual(req.name, "files/abc")

    def test_delete_file_by_protos_file(self):
        f = protos.File(name="files/abc")
        genai.delete_file(f)
        req = self.observed_requests[0]
        self.assertEqual(req.name, "files/abc")
