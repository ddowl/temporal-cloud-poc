package app

import (
	"context"
	"errors"
	"math/rand"
	"time"
)

type ExpensiveActivityParam struct {
	Input int
}

type ExpensiveActivityResult struct {
	Cost int
}

func ExpensiveActivity(ctx context.Context, param ExpensiveActivityParam) (ExpensiveActivityResult, error) {
	s := rand.Intn(param.Input)
	time.Sleep(50 * time.Millisecond * time.Duration(s))
	return ExpensiveActivityResult{Cost: s}, nil
}

type UnreliableActivityParam struct {
	Input int
}

func UnreliableActivity(ctx context.Context, param UnreliableActivityParam) error {
	s := rand.Intn(param.Input)
	if s < (3 * param.Input / 4) {
		return errors.New("unexpected error executing expensive activity")
	}
	return nil
}
