import os
from typing import Iterable, List

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from temporalio.api.common.v1 import Payload
from temporalio.converter import PayloadCodec

default_key_id = "default-key-id"


class EncryptionCodec(PayloadCodec):
    def __init__(self, key: bytes) -> None:
        super().__init__()
        self.key_id = default_key_id
        # We are using direct AESGCM to be compatible with samples from
        # TypeScript and Go.
        self.encryptor = AESGCM(key)

    async def encode(self, payloads: Iterable[Payload]) -> List[Payload]:
        # We blindly encode all payloads with the key and set the metadata
        # saying which key we used
        return [
            Payload(
                metadata={
                    "encoding": b"binary/encrypted",
                    "encryption-key-id": self.key_id.encode(),
                },
                data=self.encrypt(p.SerializeToString()),
            )
            for p in payloads
        ]

    async def decode(self, payloads: Iterable[Payload]) -> List[Payload]:
        def decode_payload(p: Payload) -> Payload:
            # Ignore ones w/out our expected encoding
            if p.metadata.get("encoding", b"").decode() != "binary/encrypted":
                return p
            # Confirm our key ID is the same
            key_id = p.metadata.get("encryption-key-id", b"").decode()
            if key_id != self.key_id:
                raise ValueError(f"Unrecognized key ID {key_id}. Current key ID is {self.key_id}.")

            # Decrypt
            return Payload.FromString(self.decrypt(p.data))

        return [decode_payload(p) for p in payloads]

    def encrypt(self, data: bytes) -> bytes:
        nonce = os.urandom(12)
        return nonce + self.encryptor.encrypt(nonce, data, None)

    def decrypt(self, data: bytes) -> bytes:
        return self.encryptor.decrypt(data[:12], data[12:], None)
