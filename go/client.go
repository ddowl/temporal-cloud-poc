package app

import (
	"crypto/tls"
	"fmt"

	"go.temporal.io/sdk/client"
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
	})
	if err != nil {
		return nil, fmt.Errorf("error connecting to temporal cloud: %w", err)
	}
	return temporalClient, nil
}
