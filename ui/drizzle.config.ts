// drizzle.config.ts
// 用于 bun run drizzle-kit studio 启动可视化界面
import { defineConfig } from "drizzle-kit";
export default defineConfig({
  dialect: "postgresql",
  dbCredentials: {
    // psql --username noeticai --host localhost --port 5432 --password
    url: "postgresql://noeticai:noeticai@localhost:5432/langchain_demo"
  },
});