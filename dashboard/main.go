// Golang HTML5 Server Side Events Example
//
// Run this code like:
//  > go run server.go
//
// Then open up your browser to http://localhost:8000
// Your browser must support HTML5 SSE, of course.

package main

import (
	"log"
	"net/http"

	"github.com/garyburd/redigo/redis"
)

func main() {

	// Connect to Redis
	redisConn, err := redis.Dial("tcp", "192.168.1.2:6379")
	// redisConn, err := redis.Dial("tcp", ":6379")
	if err != nil {
		log.Panicf("Error connecting to Redis: %s", err)
	}

	// Make a new Broker instance
	b := &Broker{
		make(map[chan string]bool),
		make(chan (chan string)),
		make(chan (chan string)),
		make(chan string),
	}

	// Start processing events
	b.Start()

	// Make b the HTTP handler for "/events/".  It can do
	// this because it has a ServeHTTP method.  That method
	// is called in a separate goroutine for each
	// request to "/events/".
	http.Handle("/events/", b)

	// Generate a constant stream of events that get pushed
	// into the Broker's messages channel and are then broadcast
	// out to any clients that are attached.
	go sendBandwidthData(b, redisConn)

	// When we get a request at "/", call `MainPageHandler`
	// in a new goroutine.
	http.Handle("/", http.HandlerFunc(MainPageHandler))

	// Start the server and listen forever on port 8000.
	http.ListenAndServe(":8000", nil)
}
