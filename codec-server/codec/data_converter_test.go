package codec

import (
	"testing"

	"github.com/stretchr/testify/require"
	"go.temporal.io/sdk/converter"
)

func Test_DataConverter(t *testing.T) {
	defaultDc := converter.GetDefaultDataConverter()

	cryptDc := NewEncryptionDataConverter(
		converter.GetDefaultDataConverter(),
		DataConverterOptions{KeyID: "test", Compress: true},
	)

	payload := "Testing"

	defaultPayloads, err := defaultDc.ToPayloads(payload)
	require.NoError(t, err)

	encryptedPayloads, err := cryptDc.ToPayloads(payload)
	require.NoError(t, err)

	require.NotEqual(t, defaultPayloads.Payloads[0].GetData(), encryptedPayloads.Payloads[0].GetData())

	var decrypted string
	err = cryptDc.FromPayloads(encryptedPayloads, &decrypted)
	require.NoError(t, err)

	require.Equal(t, payload, decrypted)
}
