package main

import (
	"context"
	"log"

	"cloud-poc/codecserver"
	"cloud-poc/codecserver/codec"

	"go.temporal.io/sdk/client"
	"go.temporal.io/sdk/converter"
)

func main() {
	c, err := client.Dial(client.Options{
		// Set DataConverter here so that workflow and activity inputs/results will
		// be encoded as required.
		DataConverter: codec.NewEncryptionDataConverter(
			converter.GetDefaultDataConverter(),
			codec.DataConverterOptions{KeyID: "default-key-id", Compress: false},
		),
	})
	if err != nil {
		log.Fatalln("Unable to create client", err)
	}
	defer c.Close()

	workflowOptions := client.StartWorkflowOptions{
		ID:        "codecserver_workflowID",
		TaskQueue: "codecserver",
	}

	we, err := c.ExecuteWorkflow(
		context.Background(),
		workflowOptions,
		codecserver.Workflow,
		"Plain text input",
	)
	if err != nil {
		log.Fatalln("Unable to execute workflow", err)
	}

	log.Println("Started workflow", "WorkflowID", we.GetID(), "RunID", we.GetRunID())

	var result string
	err = we.Get(context.Background(), &result)
	if err != nil {
		log.Fatalln("Unable get workflow result", err)
	}
	log.Println("Workflow result:", result)
}
