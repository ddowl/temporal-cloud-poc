package app

import (
	"cloud-poc/codecserver/codec"
	"crypto/tls"
	"encoding/hex"
	"fmt"

	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/converter"
)

func CreateTemporalCloudClient(namespace string, certPath string, certKeyPath string, codecHexKey string) (client.Client, error) {
	cert, err := tls.LoadX509KeyPair(certPath, certKeyPath)
	if err != nil {
		return nil, fmt.Errorf("error loading cert: %w", err)
	}

	codecKey, err := hex.DecodeString(codecHexKey)
	if err != nil {
		return nil, fmt.Errorf("error decoding hex key: %w", err)
	}

	temporalClient, err := client.Dial(client.Options{
		HostPort:  fmt.Sprintf("%s.tmprl.cloud:7233", namespace),
		Namespace: namespace,
		ConnectionOptions: client.ConnectionOptions{
			TLS: &tls.Config{Certificates: []tls.Certificate{cert}},
		},
		DataConverter: codec.NewEncryptionDataConverter(
			converter.GetDefaultDataConverter(),
			codec.DataConverterOptions{KeyID: "default-key-id", Key: codecKey, Compress: false},
		),
	})
	if err != nil {
		return nil, fmt.Errorf("error connecting to temporal cloud: %w", err)
	}
	return temporalClient, nil
}
