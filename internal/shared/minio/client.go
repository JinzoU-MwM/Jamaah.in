package minio

import (
	"context"
	"fmt"
	"io"
	"time"

	"github.com/minio/minio-go/v7"
	"github.com/minio/minio-go/v7/pkg/credentials"
)

type Client struct {
	client *minio.Client
	bucket string
}

func New(endpoint, accessKey, secretKey, bucket string, useSSL bool) (*Client, error) {
	client, err := minio.New(endpoint, &minio.Options{
		Creds:  credentials.NewStaticV4(accessKey, secretKey, ""),
		Secure: useSSL,
	})
	if err != nil {
		return nil, fmt.Errorf("create minio client: %w", err)
	}

	ctx := context.Background()
	err = client.MakeBucket(ctx, bucket, minio.MakeBucketOptions{})
	if err != nil {
		exists, err2 := client.BucketExists(ctx, bucket)
		if err2 != nil || !exists {
			return nil, fmt.Errorf("ensure bucket %s: %w", bucket, err)
		}
	}

	return &Client{client: client, bucket: bucket}, nil
}

func (c *Client) Upload(ctx context.Context, objectName string, reader io.Reader, objectSize int64, contentType string) error {
	opts := minio.PutObjectOptions{
		ContentType: contentType,
	}
	_, err := c.client.PutObject(ctx, c.bucket, objectName, reader, objectSize, opts)
	if err != nil {
		return fmt.Errorf("upload object %s: %w", objectName, err)
	}
	return nil
}

func (c *Client) GetPresignedURL(ctx context.Context, objectName string, expiry time.Duration) (string, error) {
	url, err := c.client.PresignedGetObject(ctx, c.bucket, objectName, expiry, nil)
	if err != nil {
		return "", fmt.Errorf("get presigned url for %s: %w", objectName, err)
	}
	return url.String(), nil
}

func (c *Client) Delete(ctx context.Context, objectName string) error {
	err := c.client.RemoveObject(ctx, c.bucket, objectName, minio.RemoveObjectOptions{})
	if err != nil {
		return fmt.Errorf("delete object %s: %w", objectName, err)
	}
	return nil
}

func (c *Client) ObjectExists(ctx context.Context, objectName string) (bool, error) {
	_, err := c.client.StatObject(ctx, c.bucket, objectName, minio.StatObjectOptions{})
	if err != nil {
		return false, nil
	}
	return true, nil
}