from rolling_test_base import *

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.test import Client as TestClient

from mds.api.v1.api import BINARY_TYPES_EXTENSIONS

import json

class RollingBinaryJsonTestCase(RollingTestCase):
    def test_get_checksums(self):
        post_data = {
            "procedure_guid": self.sp_guid,
            "element_id": self.br_element_id,
            "file_size": self.block_size * 10,
        }
        c = TestClient()
        response = c.post(reverse("sana-json-checksums-get"), post_data)
        resp_json = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("rolling" in resp_json)
        self.assertEqual(len(resp_json["rolling"]), 0)
        self.assertTrue("md5" in resp_json)
        self.assertEqual(len(resp_json["md5"]), 0)

    def test_post_binary_chunk(self):
        # Call this endpoint to create zero-filled data
        checksum_post_data = {
            "procedure_guid": self.sp_guid,
            "element_id": self.br_element_id,
            "file_size": self.block_size * 10,
        }
        c = TestClient()
        response = c.post(reverse("sana-json-checksums-get"), checksum_post_data)
        resp_json = json.loads(response.content)

        self.assertEqual(response.status_code, 200)

        chunk_index = 5
        rand_source = open("/dev/urandom", "rb")
        byte_data = rand_source.read(self.block_size)

        file_name = "test_file.tmp"
        with open(file_name, "wb") as f:
            f.write(byte_data)

        with open(file_name, "rb") as f:
            post_data = {
                "procedure_guid": self.sp_guid,
                "element_id": self.br_element_id,
                "element_type": BINARY_TYPES_EXTENSIONS["BINARYFILE"],
                "binary_guid": self.br_guid,
                "file_size": self.block_size * 10,
                "index": chunk_index,
                "byte_data": SimpleUploadedFile(file_name, f.read())
            }
            c = TestClient()
            response = c.post(reverse("sana-json-rolling-binarychunk-submit"), post_data)

        os.remove(file_name)

        resp_json = json.loads(response.content)
        self.assertEqual(resp_json["code"], 200)
        self._assert_binary_resource(chunk_index, byte_data)
