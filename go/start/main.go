package main

import (
	"cloud-poc/app"
	"context"
	"log"
	"os"

	"go.temporal.io/sdk/client"
)

func main() {
	namespace, certPath, certKeyPath, codecHexKey := os.Args[1], os.Args[2], os.Args[3], os.Args[4]
	c, err := app.CreateTemporalCloudClient(namespace, certPath, certKeyPath, codecHexKey)
	if err != nil {
		log.Fatalln("unable to create temporal client", err)
		return
	}
	defer c.Close()

	workflowInput := app.DummyWorkflowParam{
		A: 7,
		B: 10,
	}

	log.Printf("Executing dummy workflow w/ %+v", workflowInput)

	options := client.StartWorkflowOptions{
		ID:        "dummy-task-go-101",
		TaskQueue: app.TaskQueueName,
	}
	we, err := c.ExecuteWorkflow(context.Background(), options, app.DummyWorkflow, workflowInput)
	if err != nil {
		log.Fatalln("Unable to start the Workflow:", err)
		return
	}

	var result app.DummyWorkflowResult
	we.Get(context.Background(), &result)
	if err != nil {
		log.Fatalln("Unable to fetch workflow result:", err)
		return
	}
	log.Printf("Result of dummy workflow: %+v\n", result)
}
