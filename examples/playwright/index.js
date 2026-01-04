#!/usr/bin/env node
import { createServer } from "@playwright/mcp";

const server = createServer();
server.start();
