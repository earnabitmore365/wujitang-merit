#!/usr/bin/env bun
import { Server } from '@modelcontextprotocol/sdk/server/index.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import { readFileSync } from 'fs'
import { join } from 'path'

// 端口从命令行参数读取（默认 8788）
const PORT = parseInt(process.argv[2] || '8788')
const NAME = PORT === 8788 ? 'taiji' : 'liangyi'

// 读取 token
const tokenPath = join(import.meta.dir, '.channel_token')
const TOKEN = readFileSync(tokenPath, 'utf-8').trim()

const mcp = new Server(
  { name: `channel-${NAME}`, version: '0.1.0' },
  {
    capabilities: {
      experimental: { 'claude/channel': {} },
    },
    instructions: `太极↔两仪通道（${NAME}端）。收到 <channel> 消息时读取内容并处理。`,
  },
)

await mcp.connect(new StdioServerTransport())

Bun.serve({
  port: PORT,
  hostname: '127.0.0.1',
  async fetch(req) {
    const auth = req.headers.get('Authorization')
    if (auth !== `Bearer ${TOKEN}`) {
      return new Response('Unauthorized', { status: 401 })
    }

    const body = await req.text()
    await mcp.notification({
      method: 'notifications/claude/channel',
      params: {
        content: body,
        meta: { source: `channel-${NAME}`, path: new URL(req.url).pathname },
      },
    })
    return new Response('ok')
  },
})
