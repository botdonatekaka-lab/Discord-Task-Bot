import express, { type Express } from "express";
import cors from "cors";
import pinoHttp from "pino-http";
import path from "path";
import { fileURLToPath } from "url";
import router from "./routes";
import { logger } from "./lib/logger";

const app: Express = express();

app.use(
  pinoHttp({
    logger,
    serializers: {
      req(req) {
        return {
          id: req.id,
          method: req.method,
          url: req.url?.split("?")[0],
        };
      },
      res(res) {
        return {
          statusCode: res.statusCode,
        };
      },
    },
  }),
);

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Phục vụ dashboard static files (web/) tại root
// __dirname (injected by build banner) = artifacts/api-server/dist/
// → đi lên 3 cấp để đến workspace root, rồi vào web/
const __currentDir = path.dirname(fileURLToPath(import.meta.url));
const webDir = path.resolve(__currentDir, "../../../web");
app.use(express.static(webDir));

app.use("/api", router);

export default app;
