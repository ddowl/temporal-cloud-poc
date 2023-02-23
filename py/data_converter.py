import os
import zlib
from typing import Iterable, List

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from temporalio.api.common.v1 import Payload
from temporalio.converter import PayloadCodec

default_key = b"test-key-test-key-test-key-test!"
default_key_id = "test-key-id"


class EncryptionCodec(PayloadCodec):
    def __init__(
        self, key_id: str = default_key_id, key: bytes = default_key, compress: bool = True
    ) -> None:
        super().__init__()
        self.key_id = key_id
        # We are using direct AESGCM to be compatible with samples from
        # TypeScript and Go. Pure Python samples may prefer the higher-level,
        # safer APIs.
        self.encryptor = AESGCM(key)
        self.compress = compress

    async def encode(self, payloads: Iterable[Payload]) -> List[Payload]:
        # We blindly encode all payloads with the key and set the metadata
        # saying which key we used

        def encode_payload(p: Payload) -> Payload:
            p_data = p.SerializeToString()
            if self.compress:
                p_data = zlib.compress(p_data)
            p_data = self.encrypt(p_data)

            return Payload(
                metadata={
                    "encoding": b"binary/encrypted",
                    "encryption-key-id": self.key_id.encode(),
                },
                data=p_data,
            )

        return [encode_payload(p) for p in payloads]

    async def decode(self, payloads: Iterable[Payload]) -> List[Payload]:
        def decode_payload(p: Payload) -> Payload:
            # Ignore ones w/out our expected encoding
            if p.metadata.get("encoding", b"").decode() != "binary/encrypted":
                return p

            # Confirm our key ID is the same
            key_id = p.metadata.get("encryption-key-id", b"").decode()
            if key_id != self.key_id:
                raise ValueError(f"Unrecognized key ID {key_id}. Current key ID is {self.key_id}.")

            # Decrypt and append
            p_data = p.data
            p_data = self.decrypt(p_data)
            if self.compress:
                p_data = zlib.decompress(p_data)
            return Payload.FromString(p_data)

        return [decode_payload(p) for p in payloads]

    def encrypt(self, data: bytes) -> bytes:
        nonce = os.urandom(12)
        return nonce + self.encryptor.encrypt(nonce, data, None)

    def decrypt(self, data: bytes) -> bytes:
        return self.encryptor.decrypt(data[:12], data[12:], None)
