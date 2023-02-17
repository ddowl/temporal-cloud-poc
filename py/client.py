from temporalio.client import Client
from temporalio.service import TLSConfig


async def create_temporal_client(namespace: str, cert_path: str, key_path: str) -> Client:
    cert_text = open(cert_path, "rb").read()
    private_key_text = open(key_path, "rb").read()

    return await Client.connect(
        f"{namespace}.tmprl.cloud:7233",
        namespace=namespace,
        tls=TLSConfig(client_cert=cert_text, client_private_key=private_key_text),
    )