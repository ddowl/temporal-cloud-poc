package app

import (
	"cloud-poc/codecserver/codec"
	"crypto/tls"
	"fmt"

	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/converter"
)

func CreateTemporalCloudClient(namespace string, certPath string, keyPath string) (client.Client, error) {
	cert, err := tls.LoadX509KeyPair(certPath, keyPath)
	if err != nil {
		return nil, fmt.Errorf("error loading cert: %w", err)
	}

	temporalClient, err := client.Dial(client.Options{
		HostPort:  fmt.Sprintf("%s.tmprl.cloud:7233", namespace),
		Namespace: namespace,
		ConnectionOptions: client.ConnectionOptions{
			TLS: &tls.Config{Certificates: []tls.Certificate{cert}},
		},
		DataConverter: codec.NewEncryptionDataConverter(
			converter.GetDefaultDataConverter(),
			codec.DataConverterOptions{KeyID: "test", Compress: false},
		),
	})
	if err != nil {
		return nil, fmt.Errorf("error connecting to temporal cloud: %w", err)
	}
	return temporalClient, nil
}
