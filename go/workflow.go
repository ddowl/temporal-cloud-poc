package app

import (
	"fmt"
	"time"

	"go.temporal.io/sdk/temporal"
	"go.temporal.io/sdk/workflow"
)

type DummyWorkflowParam struct {
	A int
	B int
}

type DummyWorkflowResult struct {
	Status string
	Res    int
}

func DummyWorkflow(ctx workflow.Context, param DummyWorkflowParam) (DummyWorkflowResult, error) {
	retrypolicy := &temporal.RetryPolicy{
		InitialInterval:    100 * time.Millisecond,
		BackoffCoefficient: 1.2,
		MaximumInterval:    100 * time.Second,
		MaximumAttempts:    10, // use `0` for unlimited retry attempts
	}

	options := workflow.ActivityOptions{
		StartToCloseTimeout: time.Minute,
		RetryPolicy:         retrypolicy,
	}

	ctx = workflow.WithActivityOptions(ctx, options)

	err := workflow.
		ExecuteActivity(ctx, UnreliableActivity, UnreliableActivityParam{Input: param.A}).
		Get(ctx, nil) // "Get" blocks until future is resolved
	if err != nil {
		return DummyWorkflowResult{}, fmt.Errorf("error executing unreliable activity: %w", err)
	}

	var expensiveResult ExpensiveActivityResult
	err = workflow.
		ExecuteActivity(ctx, ExpensiveActivity, ExpensiveActivityParam{Input: param.B}).
		Get(ctx, &expensiveResult)
	if err != nil {
		return DummyWorkflowResult{}, fmt.Errorf("error executing expensive activity: %w", err)
	}

	return DummyWorkflowResult{Status: "COMPLETE", Res: expensiveResult.Cost}, nil
}
