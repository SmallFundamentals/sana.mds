from django.test import TestCase

from mds.mrs.models import BinaryResource, Client, SavedProcedure

import os
from shutil import rmtree
import uuid

class RollingTestCase(TestCase):
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

    def _assert_binary_resource(self, chunk_index, byte_data):
        saved_br = BinaryResource.objects.get(element_id=self.br_element_id)
        with open(saved_br.data.path, "r") as dest:
            # Jump to 5th block
            dest.seek(chunk_index * self.block_size)
            written_byte = dest.read(self.block_size)
            self.assertEqual(byte_data, written_byte)

            # This must be 6th block
            zero_filled_byte = dest.read(self.block_size)
            self.assertNotEqual(byte_data, zero_filled_byte)


