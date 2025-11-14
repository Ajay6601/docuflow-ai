import { useEffect, useRef, useState } from 'react'
import { WebSocketMessage } from '../types/document'

const WS_URL = 'ws://localhost:8000/api/v1/ws'

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false)
  const [messages, setMessages] = useState<WebSocketMessage[]>([])
  const ws = useRef<WebSocket | null>(null)
  const reconnectTimeout = useRef<NodeJS.Timeout>()

  const connect = () => {
    try {
      ws.current = new WebSocket(WS_URL)

      ws.current.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
      }

      ws.current.onmessage = (event) => {
        const message = JSON.parse(event.data) as WebSocketMessage
        console.log('WebSocket message:', message)
        setMessages((prev) => [...prev, message])
      }

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

      ws.current.onclose = () => {
        console.log('WebSocket disconnected')
        setIsConnected(false)
        
        // Attempt to reconnect after 3 seconds
        reconnectTimeout.current = setTimeout(() => {
          console.log('Attempting to reconnect...')
          connect()
        }, 3000)
      }
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error)
    }
  }

  const disconnect = () => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current)
    }
    if (ws.current) {
      ws.current.close()
      ws.current = null
    }
  }

  const subscribe = (documentId: number) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: 'subscribe',
        document_id: documentId
      }))
    }
  }

  const clearMessages = () => {
    setMessages([])
  }

  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [])

  return {
    isConnected,
    messages,
    subscribe,
    clearMessages
  }
}