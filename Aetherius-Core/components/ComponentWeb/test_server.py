#!/usr/bin/env python3
"""
简化的测试服务器
"""

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import asyncio
import json
from datetime import datetime

app = FastAPI(title="Test Server")

# CORS设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Test server is running", "time": datetime.now().isoformat()}

@app.get("/test", response_class=HTMLResponse)
async def test_page():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket测试</title>
        <meta charset="utf-8">
    </head>
    <body>
        <h1>WebSocket测试页面</h1>
        <div id="status">准备连接...</div>
        <div id="messages" style="border: 1px solid #ccc; height: 300px; overflow-y: scroll; padding: 10px; margin: 10px 0;"></div>
        <input type="text" id="messageInput" placeholder="输入消息..." style="width: 70%;">
        <button onclick="sendMessage()">发送</button>
        
        <script>
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = protocol + '//' + window.location.host + '/ws';
            console.log('连接到:', wsUrl);
            
            const ws = new WebSocket(wsUrl);
            const statusDiv = document.getElementById('status');
            const messagesDiv = document.getElementById('messages');
            
            ws.onopen = function() {
                statusDiv.textContent = '✅ 已连接';
                addMessage('系统', '连接已建立');
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                addMessage('服务器', JSON.stringify(data, null, 2));
            };
            
            ws.onclose = function() {
                statusDiv.textContent = '❌ 连接已关闭';
                addMessage('系统', '连接已关闭');
            };
            
            ws.onerror = function(error) {
                statusDiv.textContent = '❌ 连接错误';
                addMessage('错误', error.toString());
            };
            
            function addMessage(sender, message) {
                const div = document.createElement('div');
                div.innerHTML = '<strong>' + sender + ':</strong> <pre>' + message + '</pre>';
                messagesDiv.appendChild(div);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
            
            function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                if (message) {
                    const data = {
                        type: 'test',
                        message: message,
                        timestamp: new Date().toISOString()
                    };
                    ws.send(JSON.stringify(data));
                    addMessage('客户端', JSON.stringify(data, null, 2));
                    input.value = '';
                }
            }
            
            document.getElementById('messageInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        </script>
    </body>
    </html>
    '''

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection accepted")
    
    try:
        # 发送欢迎消息
        await websocket.send_json({
            "type": "welcome",
            "message": "WebSocket连接已建立",
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            data = await websocket.receive_json()
            print(f"Received: {data}")
            
            # 回显消息
            response = {
                "type": "echo",
                "original": data,
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_json(response)
            
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")

if __name__ == "__main__":
    print("启动测试服务器...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")