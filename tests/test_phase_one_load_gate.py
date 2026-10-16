import io
import unittest

from scripts.load_test_phase_one import percentile
from services.object_storage import ObjectStorage


class PhaseOneLoadAndStatelessTests(unittest.TestCase):
    def test_percentile_is_deterministic_for_capacity_gates(self):
        samples = [100, 10, 50, 20, 40, 30]
        self.assertEqual(percentile(samples, 0.50), 30)
        self.assertEqual(percentile(samples, 0.95), 100)
        self.assertEqual(percentile([], 0.95), 0)

    def test_two_instances_use_the_same_external_object_namespace(self):
        class SharedS3:
            def __init__(self):
                self.objects = {}

            def upload_fileobj(self, stream, bucket, key, ExtraArgs):
                self.objects[(bucket, key)] = stream.read()

            def generate_presigned_url(self, operation, Params, ExpiresIn):
                key = (Params["Bucket"], Params["Key"])
                if key not in self.objects:
                    raise AssertionError("object was not shared between instances")
                return f"https://objects.example/{Params['Key']}?ttl={ExpiresIn}"

        shared_s3 = SharedS3()

        def instance():
            storage = ObjectStorage.__new__(ObjectStorage)
            storage.backend = "s3"
            storage.bucket = "beacon-evidence"
            storage.prefix = "beacon"
            storage.kms_key_id = "test-key"
            storage.expected_owner = "123456789012"
            storage._s3 = shared_s3
            return storage

        first_instance = instance()
        second_instance = instance()
        key = "beacon/agency-42/evidence/shared.bin"
        first_instance.put(io.BytesIO(b"shared evidence"), key, "application/octet-stream")

        signed_url = second_instance.signed_url(key, "shared.bin")
        self.assertIn(key, signed_url)

    def test_production_configuration_forbids_durable_local_upload_state(self):
        from config import settings

        source = open(settings.__file__, encoding="utf-8").read()
        self.assertIn("OBJECT_STORAGE_BACKEND must be 's3' in production", source)
