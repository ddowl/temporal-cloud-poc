import dataclasses
from temporalio import converter
from temporalio.client import Client
from temporalio.service import TLSConfig

from data_converter import EncryptionCodec


async def create_temporal_client(
    namespace: str, cert_path: str, cert_key_path: str, codec_hex: str
) -> Client:
    cert_text = open(cert_path, "rb").read()
    private_cert_key_text = open(cert_key_path, "rb").read()

    return await Client.connect(
        f"{namespace}.tmprl.cloud:7233",
        namespace=namespace,
        tls=TLSConfig(client_cert=cert_text, client_private_key=private_cert_key_text),
        data_converter=dataclasses.replace(
            converter.default(), payload_codec=EncryptionCodec(key=bytes.fromhex(codec_hex)),
        ),
    )
