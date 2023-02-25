package main

import (
	"cloud-poc/app"
	"log"
	"os"

	"go.temporal.io/sdk/worker"
)

func main() {
	namespace, certPath, certKeyPath, codecHexKey := os.Args[1], os.Args[2], os.Args[3], os.Args[4]
	c, err := app.CreateTemporalCloudClient(namespace, certPath, certKeyPath, codecHexKey)
	if err != nil {
		log.Fatalln("unable to create temporal client", err)
		return
	}
	defer c.Close()

	w := worker.New(c, app.TaskQueueName, worker.Options{})
	w.RegisterWorkflow(app.DummyWorkflow)
	w.RegisterActivity(app.ExpensiveActivity)
	w.RegisterActivity(app.UnreliableActivity)
	err = w.Run(worker.InterruptCh())
	if err != nil {
		log.Fatalln("unable to start Worker", err)
	}
}
