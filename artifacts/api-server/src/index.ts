import http from "http";
import { Server as SocketIO } from "socket.io";
import app from "./app";
import { logger } from "./lib/logger";
import { setupBotControl } from "./routes/botControl";

const rawPort = process.env["PORT"];

if (!rawPort) {
  throw new Error(
    "PORT environment variable is required but was not provided.",
  );
}

const port = Number(rawPort);

if (Number.isNaN(port) || port <= 0) {
  throw new Error(`Invalid PORT value: "${rawPort}"`);
}

// Bọc Express trong http.Server để Socket.IO có thể dùng chung
const server = http.createServer(app);
const io = new SocketIO(server, { cors: { origin: "*" } });

// Gắn bot control routes + socket events
setupBotControl(app, io);

server.listen(port, (err?: Error) => {
  if (err) {
    logger.error({ err }, "Error listening on port");
    process.exit(1);
  }
  logger.info({ port }, "Server listening");
});
