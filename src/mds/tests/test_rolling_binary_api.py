from django.test import TestCase

from mds.api.v1.api import BINARY_TYPES_EXTENSIONS, get_binary_checksum, register_rolling_binary_chunk
from mds.mrs.models import BinaryResource, Client, SavedProcedure

import os
from shutil import rmtree
import uuid

class RollingBinaryApiTestCase(TestCase):
    def setUp(self):
        self.block_size = 1024

        # Create required objects
        client = Client.objects.create()
        self.sp_guid = uuid.uuid4()
        sp = SavedProcedure.objects.create(client=client, guid=self.sp_guid)

        self.br_element_id = uuid.uuid4()
        self.br_guid = uuid.uuid4()
        br = BinaryResource.objects.create(
            procedure=sp,
            element_id=self.br_element_id,
            guid=self.br_guid,
        )
        br.upload_progress = 0
        br.total_size = 0
        br.data = br.data.field.generate_filename(br, ('%s' % br.pk))
        self.path, _ = os.path.split(br.data.path)
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        open(br.data.path, 'w').close()
        br.save()

    def tearDown(self):
        rmtree(self.path)

    def test_get_checksums_with_invalid_procedure(self):
        checksums = get_binary_checksum("1", "1", 0)
        self.assertIsNone(checksums)

    def test_get_checksums(self):
        file_size = self.block_size * 10
        checksums = get_binary_checksum(self.sp_guid, self.br_element_id, file_size)
        self.assertEqual(len(checksums), 2)

        saved_br = BinaryResource.objects.get(element_id=self.br_element_id)
        self.assertEqual(saved_br.total_size, file_size)

    def test_register_binary_chunk(self):
        file_size = self.block_size * 10
        # Call this API to create zero-filled data
        get_binary_checksum(self.sp_guid, self.br_element_id, file_size)

        element_type = BINARY_TYPES_EXTENSIONS['BINARYFILE']
        chunk_index = 5
        rand_source = open("/dev/urandom", "rb")
        byte_data = rand_source.read(self.block_size)

        # Write random bytes at 5th block
        result, _ = register_rolling_binary_chunk(
                self.sp_guid,
                self.br_element_id,
                element_type,
                self.br_guid,
                file_size,
                chunk_index,
                byte_data,
        )
        self.assertTrue(result)

        # Read binary data again and do assertion
        saved_br = BinaryResource.objects.get(element_id=self.br_element_id)
        with open(saved_br.data.path, "r") as dest:
            # Jump to 5th block
            dest.seek(chunk_index * self.block_size)
            written_byte = dest.read(self.block_size)
            self.assertEqual(byte_data, written_byte)

            # This must be 6th block
            zero_filled_byte = dest.read(self.block_size)
            self.assertNotEqual(byte_data, zero_filled_byte)
