from rolling_test_base import *

from mds.api.v1.api import BINARY_TYPES_EXTENSIONS, get_binary_checksum, register_rolling_binary_chunk

class RollingBinaryApiTestCase(RollingTestCase):
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
        self._assertSingleChunkData(chunk_index, byte_data)
