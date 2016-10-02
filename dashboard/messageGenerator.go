package main

import (
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/garyburd/redigo/redis"
)

type bandwidth struct {
	Upload   float64 `json:"upload"`
	Download float64 `json:"download"`
}

func getBWData(c redis.Conn) (string, error) {

	keys, _ := redis.Values(c.Do("KEYS", fmt.Sprintf("*download_%s", time.Now().Format("2006-01"))))
	allBWData := make(map[string]bandwidth)

	for _, key := range keys {
		mac := strings.Split(fmt.Sprintf("%s", key), "_")[0]
		deviceName, _ := redis.String(c.Do("GET", mac))

		download, _ := redis.Float64(c.Do("GET", fmt.Sprintf("%s_download_%s", mac, time.Now().Format("2006-01"))))
		upload, _ := redis.Float64(c.Do("GET", fmt.Sprintf("%s_upload_%s", mac, time.Now().Format("2006-01"))))

		allBWData[fmt.Sprintf("%s - %s", deviceName, mac)] = bandwidth{Upload: upload, Download: download}
	}

	json, _ := json.Marshal(allBWData)
	return string(json), nil
}

func getPushMessage(redisConn redis.Conn) (string, error) {
	// bwData := getBWData(redisConn)
	msg, _ := getBWData(redisConn)
	// msg := `{"mac1": { "upload": 123, "download": 456},"mac2": {"upload": 123, "download": 456}}`
	return msg, nil
}

func sendBandwidthData(b *Broker, redisConn redis.Conn) {
	for i := 0; ; i++ {

		// Create a little message to send to clients,
		msg, err := getPushMessage(redisConn)
		if err != nil {
			fmt.Println("Error generating message")
		}
		b.messages <- msg

		// Print a nice log message and sleep for 5s.
		time.Sleep(1 * 1e9)

	}

}
