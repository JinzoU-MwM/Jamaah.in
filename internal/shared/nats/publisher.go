package nats

import (
	"fmt"
	"log"
	"time"

	"github.com/nats-io/nats.go"
)

type Publisher struct {
	nc *nats.Conn
	js nats.JetStreamContext
}

func NewPublisher(addr string) (*Publisher, error) {
	nc, err := nats.Connect(addr,
		nats.Name("jamaah-in-publisher"),
		nats.ReconnectWait(2*time.Second),
		nats.MaxReconnects(10),
	)
	if err != nil {
		return nil, fmt.Errorf("connect to nats: %w", err)
	}

	js, err := nc.JetStream()
	if err != nil {
		return nil, fmt.Errorf("get jetstream context: %w", err)
	}

	p := &Publisher{nc: nc, js: js}
	p.ensureStreams()
	return p, nil
}

func (p *Publisher) ensureStreams() {
	streams := []struct {
		name     string
		subjects []string
	}{
		{"JAMAAH", []string{"jamaah.>"}},
		{"INVOICE", []string{"invoice.>"}},
		{"PACKAGE", []string{"package.>"}},
		{"FINANCE", []string{"finance.>"}},
		{"AIOCR", []string{"aiocr.>"}},
		{"NOTIFY", []string{"notify.>"}},
	}

	for _, s := range streams {
		_, err := p.js.StreamInfo(s.name)
		if err == nats.ErrStreamNotFound {
			_, err = p.js.AddStream(&nats.StreamConfig{
				Name:     s.name,
				Subjects: s.subjects,
				Replicas: 1,
				Retention: nats.LimitsPolicy,
				MaxAge:   72 * time.Hour,
			})
			if err != nil {
				log.Printf("create stream %s: %v", s.name, err)
			}
		}
	}
}

func (p *Publisher) Publish(subject string, data []byte) error {
	_, err := p.js.Publish(subject, data)
	if err != nil {
		return fmt.Errorf("publish to %s: %w", subject, err)
	}
	return nil
}

func (p *Publisher) Close() {
	if p.nc != nil {
		p.nc.Close()
	}
}