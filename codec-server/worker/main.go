package main

import (
	"log"

	"cloud-poc/codecserver"
	"cloud-poc/codecserver/codec"

	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/converter"
	"go.temporal.io/sdk/worker"
)

func main() {
	c, err := client.Dial(client.Options{
		// Set DataConverter here so that workflow and activity inputs/results will
		// be encoded as required.
		DataConverter: codec.NewEncryptionDataConverter(
			converter.GetDefaultDataConverter(),
			codec.DataConverterOptions{KeyID: "test", Compress: true},
		),
	})
	if err != nil {
		log.Fatalln("Unable to create client", err)
	}
	defer c.Close()

	w := worker.New(c, "codecserver", worker.Options{})

	w.RegisterWorkflow(codecserver.Workflow)
	w.RegisterActivity(codecserver.Activity)

	err = w.Run(worker.InterruptCh())
	if err != nil {
		log.Fatalln("Unable to start worker", err)
	}
}
